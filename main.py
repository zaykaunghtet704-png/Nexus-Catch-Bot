import asyncio
import random
from threading import Thread
from config import BOT_TOKEN, OWNER_IDS, PORT, SPAWN_THRESHOLD
from flask import Flask
from models import CardBase, SessionLocal, User, UserCard
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.error import RetryAfter
from telegram.ext import (
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

# --- WEB KEEP-ALIVE SERVER ---
app = Flask(__name__)


@app.route("/")
def home():
    return "<h1>Nexus Engine Active</h1>"


def run_web():
    app.run(host="0.0.0.0", port=PORT)


active_spawns = {}
chat_counts = {}

# --- MULTI-LANGUAGE DICTIONARY ---
LANGUAGES = {
    "en": {
        "start": "👋 **Welcome to Nexus Card Bot!**\nUse `/help` for commands.",
        "help": (
            "📜 **COMMANDS LIST**\n\n"
            "👤 **User Commands:**\n"
            "• `/start` - Start bot\n"
            "• `/profile` - View profile\n"
            "• `/catch` or `/nexus` - Catch card\n"
            "• `/language` - Change language\n\n"
            "👑 **Owner Commands:**\n"
            "• Reply photo with `/addcard ID | Name` - Quick Add Card\n"
            "• `/addcard ID | Name | Image_URL` - Add Card with Link\n"
            "• `/give` - Give coins/tokens\n"
            "• `/forcespawn` - Force spawn in group"
        ),
        "lang_select": "🌐 **Select your language:**",
        "lang_changed": "✅ Language set to **English**!",
        "no_spawn": "❌ No character active to catch!",
        "caught": "🎉 **{name}** captured **{card}**!\n🏷️ **Print:** #{print_num}\n✨ **Quality:** {quality}%\n⭐ **Rarity:** {rarity}\n🆔 `{uuid}`",
        "profile": "👤 **PROFILE:** {name}\n💰 Coins: `{coins}` | 🪙 Tokens: `{tokens}`\n🎴 Cards: `{cards_count}`",
        "banned": "🚫 You are banned.",
    },
    "my": {
        "start": "👋 **Nexus Card Bot မှ ကြိုဆိုပါသည်!**\nCommands များကြည့်ရန် `/help` ကိုသုံးပါ။",
        "help": (
            "📜 **COMMANDS စာရင်း**\n\n"
            "👤 **အသုံးပြုသူ Commands:**\n"
            "• `/start` - စတင်ရန်\n"
            "• `/profile` - ပရိုဖိုင်ကြည့်ရန်\n"
            "• `/catch` သို့ `/nexus` - ကဒ်ဖမ်းရန်\n"
            "• `/language` - ဘာသာစကားပြောင်းရန်\n\n"
            "👑 **Owner Commands:**\n"
            "• ပုံကို Reply ပြန်၍ `/addcard ID | Name` - အလွယ်ကဒ်ထည့်ရန်\n"
            "• `/addcard ID | Name | Image_URL` - Link ဖြင့် ကဒ်ထည့်ရန်\n"
            "• `/give` - Coins/Tokens ပေးရန်\n"
            "• `/forcespawn` - ကဒ် ချက်ချင်း ချပေးရန်"
        ),
        "lang_select": "🌐 **ဘာသာစကား ရွေးချယ်ပါ:**",
        "lang_changed": "✅ ဘာသာစကားကို **မြန်မာစာ** သို့ ပြောင်းလိုက်ပါပြီ!",
        "no_spawn": "❌ ဖမ်းယူရန် ကဒ်မရှိသေးပါ!",
        "caught": "🎉 **{name}** သည် **{card}** ကို ဖမ်းယူရရှိခဲ့သည်!\n🏷️ **Print:** #{print_num}\n✨ **Quality:** {quality}%\n⭐ **Rarity:** {rarity}\n🆔 `{uuid}`",
        "profile": "👤 **အသုံးပြုသူ ပရိုဖိုင်:** {name}\n💰 Coins: `{coins}` | 🪙 Tokens: `{tokens}`\n🎴 စုဆောင်းထားသော ကဒ်များ: `{cards_count}`",
        "banned": "🚫 သင့်အား ပိတ်ပင်ထားပါသည်။",
    },
}


def get_msg(user_lang, key, **kwargs):
    lang = user_lang if user_lang in LANGUAGES else "en"
    text = LANGUAGES[lang].get(key, LANGUAGES["en"].get(key, ""))
    return text.format(**kwargs) if kwargs else text


def is_owner(user_id: int) -> bool:
    return user_id in OWNER_IDS


# ==========================================
# 🖼️ 1. SMART PHOTO REPLY ADD CARD (အလွယ်ဆုံး ကဒ်ထည့်နည်း)
# ==========================================


async def admin_add_card(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id):
        return

    try:
        raw = " ".join(context.args)
        image_url = None

        # ၁။ ပုံကို Reply ပြန်ပြီး /addcard ID | Name ရိုက်သည့်စနစ်
        if update.message.reply_to_message and (
            update.message.reply_to_message.photo
            or update.message.reply_to_message.document
        ):
            photo = update.message.reply_to_message.photo[-1]
            image_url = photo.file_id  # Telegram File ID ကို တိုက်ရိုက်ယူမည်
            cid, name = [x.strip() for x in raw.split("|")]

        # ၂။ Normal Link ဖြင့် /addcard ID | Name | Image_URL ထည့်သည့်စနစ်
        else:
            cid, name, image_url = [x.strip() for x in raw.split("|")]

        session = SessionLocal()
        new_card = CardBase(
            id=cid,
            name=name,
            anime="General",
            rarity="UR 👑",
            base_power=5000,
            element="Neutral",
            image_url=image_url,
        )
        session.add(new_card)
        session.commit()
        session.close()

        await update.message.reply_text(
            f"✅ **[ကဒ်အသစ် အောင်မြင်စွာ ထည့်ပြီးပါပြီ]**\n🆔 ID: `{cid}`\n👤 အမည်: **{name}**",
            parse_mode="Markdown",
        )
    except Exception:
        await update.message.reply_text(
            "❌ **ကဒ်ထည့်နည်း ပုံစံ (၂) မျိုး:**\n\n"
            "1️⃣ **ပုံကို Reply ပြန်၍ ရိုက်ရန်:**\n`/addcard ID | Name`\n\n"
            "2️⃣ **Link ဖြင့် တိုက်ရိုက် ရိုက်ရန်:**\n`/addcard ID | Name | Image_URL`",
            parse_mode="Markdown",
        )


# ==========================================
# 💬 2. AUTO SPAWN ENGINE (စာအကြောင်းရေ ၁၀၀ ပြည့်မှ ကဒ်ချပေးမည့်စနစ်)
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

    # စာအကြောင်းရေ ၁၀၀ ပြည့်/မပြည့် စစ်ဆေးခြင်း
    if chat_counts[chat_id] >= 100:
        session = SessionLocal()
        cards = session.query(CardBase).all()

        if cards:
            chat_counts[chat_id] = 0  # Counter ကို ပြန် 0 လုပ်မည်
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
                print(f"Spawn Error: {err}")
        session.close()


# ==========================================
# 🌐 3. USER & OWNER COMMANDS
# ==========================================


async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    session = SessionLocal()
    user = session.query(User).filter(User.id == user_id).first()
    if not user:
        user = User(id=user_id, name=update.effective_user.first_name)
        session.add(user)
        session.commit()

    msg = get_msg(user.language, "start")
    session.close()
    await update.message.reply_text(msg, parse_mode="Markdown")


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    session = SessionLocal()
    user = session.query(User).filter(User.id == user_id).first()
    lang = user.language if user else "en"
    session.close()
    await update.message.reply_text(
        get_msg(lang, "help"), parse_mode="Markdown"
    )


async def set_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    session = SessionLocal()
    user = session.query(User).filter(User.id == user_id).first()
    lang = user.language if user else "en"
    session.close()

    keyboard = [
        [
            InlineKeyboardButton("🇬🇧 English", callback_data="lang_en"),
            InlineKeyboardButton("🇲🇲 မြန်မာစာ", callback_data="lang_my"),
        ]
    ]
    await update.message.reply_text(
        get_msg(lang, "lang_select"),
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown",
    )


async def language_button_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    query = update.callback_query
    await query.answer()

    user_id = str(query.from_user.id)
    selected_lang = "en" if query.data == "lang_en" else "my"

    session = SessionLocal()
    user = session.query(User).filter(User.id == user_id).first()
    if not user:
        user = User(id=user_id, name=query.from_user.first_name)
        session.add(user)

    user.language = selected_lang
    session.commit()
    session.close()

    await query.edit_message_text(
        get_msg(selected_lang, "lang_changed"), parse_mode="Markdown"
    )


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
    else:
        await update.message.reply_text(
            "❌ No cards found in DB. Use `/addcard` first."
        )
    session.close()


if __name__ == "__main__":
    Thread(target=run_web).start()
    bot = ApplicationBuilder().token(BOT_TOKEN).build()

    bot.add_handler(CommandHandler("start", start_cmd))
    bot.add_handler(CommandHandler("help", help_cmd))
    bot.add_handler(CommandHandler("language", set_language))
    bot.add_handler(CommandHandler("profile", user_profile))
    bot.add_handler(CommandHandler("nexus", catch_card))
    bot.add_handler(CommandHandler("catch", catch_card))
    bot.add_handler(
        CallbackQueryHandler(language_button_callback, pattern="^lang_")
    )

    bot.add_handler(CommandHandler("addcard", admin_add_card))
    bot.add_handler(CommandHandler("give", admin_give_currency))
    bot.add_handler(CommandHandler("forcespawn", admin_force_spawn))
    bot.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_spawns)
    )

    print("Master Bot Engine 24/7 Fully Operational...")
    bot.run_polling()
