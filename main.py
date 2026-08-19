import asyncio
import logging
import random
from threading import Thread
from config import BOT_TOKEN, OWNER_IDS, PORT, SPAWN_THRESHOLD
from flask import Flask
from models import CardBase, SessionLocal, User, UserCard
from telegram import Update
from telegram.error import RetryAfter
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

# --- WEB KEEP-ALIVE SERVER ---
app = Flask(__name__)


@app.route("/")
def home():
    return "<h1>Nexus 24/7 Engine Active</h1>"


def run_web():
    app.run(host="0.0.0.0", port=PORT)


# --- GLOBAL VARIABLES ---
active_spawns = {}
chat_counts = {}

# --- LANGUAGE DICTIONARY SYSTEM ---
LANGUAGES = {
    "en": {
        "lang_changed": "✅ Language changed to **English**!",
        "no_spawn": "❌ No character active to catch!",
        "caught": "🎉 **{name}** captured **{card}**!\n🏷️ **Print:** #{print_num}\n✨ **Quality:** {quality}%\n⭐ **Rarity:** {rarity}\n🆔 `{uuid}`",
        "profile": "👤 **PROFILE:** {name}\n💰 Coins: `{coins}` | 🪙 Tokens: `{tokens}`\n🎴 Cards Collected: `{cards_count}`\n🌐 Language: English",
        "banned": "🚫 You are banned from using this bot.",
    },
    "my": {
        "lang_changed": "✅ ဘာသာစကားကို **မြန်မာဘာသာ** သို့ ပြောင်းလဲလိုက်ပါပြီ!",
        "no_spawn": "❌ ဖမ်းယူရန် Character မရှိသေးပါ!",
        "caught": "🎉 **{name}** သည် **{card}** ကို ဖမ်းယူရရှိခဲ့သည်!\n🏷️ **Print:** #{print_num}\n✨ **Quality:** {quality}%\n⭐ **Rarity:** {rarity}\n🆔 `{uuid}`",
        "profile": "👤 **အသုံးပြုသူ ပရိုဖိုင်:** {name}\n💰 Coins: `{coins}` | 🪙 Tokens: `{tokens}`\n🎴 စုဆောင်းထားသော ကဒ်များ: `{cards_count}`\n🌐 ဘာသာစကား: မြန်မာ",
        "banned": "🚫 သင့်အား ဘော့အသုံးပြုခွင့် ပိတ်ပင်ထားပါသည်။",
    },
}


def get_msg(user_lang, key, **kwargs):
    lang = user_lang if user_lang in LANGUAGES else "en"
    text = LANGUAGES[lang].get(key, LANGUAGES["en"].get(key, ""))
    return text.format(**kwargs) if kwargs else text


def is_owner(user_id: int) -> bool:
    return user_id in OWNER_IDS


# ==========================================
# 🌐 1. USER COMMANDS (MULTI-LANGUAGE)
# ==========================================


async def set_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    session = SessionLocal()
    user = session.query(User).filter(User.id == user_id).first()

    if not user:
        user = User(id=user_id, name=update.effective_user.first_name)
        session.add(user)

    if not context.args or context.args[0].lower() not in ["en", "my"]:
        await update.message.reply_text(
            "🌐 Select Language / ဘာသာစကား ရွေးချယ်ပါ:\n\n• `/language en` - English\n• `/language my` - မြန်မာဘာသာ",
            parse_mode="Markdown",
        )
        session.close()
        return

    user.language = context.args[0].lower()
    session.commit()
    msg = get_msg(user.language, "lang_changed")
    session.close()
    await update.message.reply_text(msg, parse_mode="Markdown")


async def user_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    session = SessionLocal()
    user = session.query(User).filter(User.id == user_id).first()

    if not user:
        user = User(id=user_id, name=update.effective_user.first_name)
        session.add(user)
        session.commit()

    if user.is_banned:
        await update.message.reply_text(get_msg(user.language, "banned"))
        session.close()
        return

    cards_count = (
        session.query(UserCard).filter(UserCard.user_id == user_id).count()
    )
    msg = get_msg(
        user.language,
        "profile",
        name=user.name,
        coins=user.coins,
        tokens=user.tokens,
        cards_count=cards_count,
    )
    session.close()
    await update.message.reply_text(msg, parse_mode="Markdown")


async def catch_card(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_id = str(update.effective_user.id)

    session = SessionLocal()
    user = session.query(User).filter(User.id == user_id).first()
    if not user:
        user = User(id=user_id, name=update.effective_user.first_name)
        session.add(user)

    if user.is_banned:
        await update.message.reply_text(get_msg(user.language, "banned"))
        session.close()
        return

    if chat_id not in active_spawns or not active_spawns[chat_id]:
        await update.message.reply_text(get_msg(user.language, "no_spawn"))
        session.close()
        return

    card_base_id = active_spawns[chat_id]
    active_spawns[chat_id] = None

    card_base = (
        session.query(CardBase).filter(CardBase.id == card_base_id).first()
    )
    card_base.total_prints += 1

    quality = round(random.uniform(10.00, 100.00), 2)
    new_card = UserCard(
        user_id=user.id,
        card_id=card_base.id,
        print_number=card_base.total_prints,
        quality=quality,
    )
    session.add(new_card)
    session.commit()

    msg = get_msg(
        user.language,
        "caught",
        name=user.name,
        card=card_base.name,
        print_num=card_base.total_prints,
        quality=quality,
        rarity=card_base.rarity,
        uuid=new_card.uuid,
    )
    session.close()
    await update.message.reply_text(msg, parse_mode="Markdown")


# ==========================================
# 👑 2. FULL OWNER CONTROL PANEL
# ==========================================


async def admin_add_card(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id):
        return
    try:
        raw = " ".join(context.args)
        cid, name, anime, rarity, power, element, img = [
            x.strip() for x in raw.split("|")
        ]
        session = SessionLocal()
        new_card = CardBase(
            id=cid,
            name=name,
            anime=anime,
            rarity=rarity,
            base_power=int(power),
            element=element,
            image_url=img,
        )
        session.add(new_card)
        session.commit()
        session.close()
        await update.message.reply_text(
            f"✅ **[CARD CREATED]**\n👑 Name: {name} | ID: `{cid}`"
        )
    except Exception as e:
        await update.message.reply_text(
            f"❌ Format: `/addcard ID | Name | Anime | Rarity | Power | Element | Image_URL`\nError: `{e}`"
        )


async def admin_give_currency(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    if not is_owner(update.effective_user.id):
        return
    try:
        target_id, currency, amount = (
            str(context.args[0]),
            context.args[1].lower(),
            int(context.args[2]),
        )
        session = SessionLocal()
        user = session.query(User).filter(User.id == target_id).first()
        if user:
            if currency == "coins":
                user.coins += amount
            elif currency == "tokens":
                user.tokens += amount
            session.commit()
            await update.message.reply_text(
                f"✅ Added {amount} {currency} to User `{target_id}`."
            )
        session.close()
    except Exception:
        await update.message.reply_text(
            "❌ Format: `/give <user_id> <coins/tokens> <amount>`"
        )


async def admin_ban_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id):
        return
    try:
        target_id, action = str(context.args[0]), context.args[1].lower()
        session = SessionLocal()
        user = session.query(User).filter(User.id == target_id).first()
        if user:
            user.is_banned = True if action == "ban" else False
            session.commit()
            await update.message.reply_text(
                f"👤 User `{target_id}` {action.upper()}ED successfully."
            )
        session.close()
    except Exception:
        await update.message.reply_text(
            "❌ Format: `/banuser <user_id> <ban/unban>`"
        )


async def admin_force_spawn(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    if not is_owner(update.effective_user.id):
        return
    chat_id = update.effective_chat.id
    session = SessionLocal()
    cards = session.query(CardBase).all()
    if cards:
        selected_card = random.choice(cards)
        active_spawns[chat_id] = selected_card.id
        caption = f"⚡ **[ADMIN SPAWN] CHARACTER APPEARED!**\nName: **{selected_card.name}**\nUse `/nexus` or `/catch`!"
        await context.bot.send_photo(
            chat_id=chat_id,
            photo=selected_card.image_url,
            caption=caption,
            parse_mode="Markdown",
        )
    session.close()


# ==========================================
# ⚙️ 3. SAFE AUTO-SPAWN & FLOOD ENGINE
# ==========================================


async def handle_spawns(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if (
        not update.message
        or not update.message.text
        or update.message.text.startswith("/")
    ):
        return

    chat_id = update.effective_chat.id
    chat_counts[chat_id] = chat_counts.get(chat_id, 0) + 1

    if chat_counts[chat_id] >= SPAWN_THRESHOLD:
        session = SessionLocal()
        cards = session.query(CardBase).all()

        if cards:
            chat_counts[chat_id] = 0
            selected_card = random.choice(cards)
            active_spawns[chat_id] = selected_card.id
            caption = f"⚡ **A WILD CHARACTER APPEARED!**\nName: **{selected_card.name}**\nRarity: {selected_card.rarity}\nUse `/nexus` or `/catch`!"

            try:
                await context.bot.send_photo(
                    chat_id=chat_id,
                    photo=selected_card.image_url,
                    caption=caption,
                    parse_mode="Markdown",
                )
            except RetryAfter as e:
                await asyncio.sleep(e.retry_after)
                await context.bot.send_photo(
                    chat_id=chat_id,
                    photo=selected_card.image_url,
                    caption=caption,
                    parse_mode="Markdown",
                )
            except Exception as err:
                print(f"Spawn Engine Error: {err}")
        session.close()


# ==========================================
# 🚀 4. ENGINE LAUNCHER
# ==========================================

if __name__ == "__main__":
    Thread(target=run_web).start()
    bot = ApplicationBuilder().token(BOT_TOKEN).build()

    # User Handlers
    bot.add_handler(CommandHandler("language", set_language))
    bot.add_handler(CommandHandler("profile", user_profile))
    bot.add_handler(CommandHandler("nexus", catch_card))
    bot.add_handler(CommandHandler("catch", catch_card))

    # Owner Handlers
    bot.add_handler(CommandHandler("addcard", admin_add_card))
    bot.add_handler(CommandHandler("give", admin_give_currency))
    bot.add_handler(CommandHandler("banuser", admin_ban_user))
    bot.add_handler(CommandHandler("forcespawn", admin_force_spawn))

    # Message Handler
    bot.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_spawns)
    )

    print("Master Bot Engine 24/7 Fully Operational...")
    bot.run_polling()
