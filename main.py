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

# --- DYNAMIC MULTI-LANGUAGE DICTIONARY ---
LANGUAGES = {
    "en": {
        "start": "👋 **Welcome to Nexus Card Bot!**\nUse `/help` to see all commands or `/language` to change language.",
        "help": (
            "📜 **COMMANDS LIST**\n\n"
            "👤 **User Commands:**\n"
            "• `/start` - Start the bot\n"
            "• `/profile` - View your profile & balance\n"
            "• `/catch` or `/nexus` - Catch spawned character\n"
            "• `/language` - Change language (EN/MY)\n\n"
            "👑 **Owner Commands:**\n"
            "• `/addcard` - Create new card base\n"
            "• `/give` - Give coins/tokens to user\n"
            "• `/banuser` - Ban or Unban user\n"
            "• `/forcespawn` - Force spawn a card"
        ),
        "lang_select": "🌐 **Select your preferred language:**",
        "lang_changed": "✅ Language set to **English**!",
        "no_spawn": "❌ No character active to catch in this group!",
        "caught": "🎉 **{name}** captured **{card}**!\n🏷️ **Print:** #{print_num}\n✨ **Quality:** {quality}%\n⭐ **Rarity:** {rarity}\n🆔 `{uuid}`",
        "profile": "👤 **PROFILE:** {name}\n💰 Coins: `{coins}` | 🪙 Tokens: `{tokens}`\n🎴 Cards Collected: `{cards_count}`\n🌐 Language: English",
        "banned": "🚫 You are banned from using this bot.",
    },
    "my": {
        "start": "👋 **Nexus Card Bot မှ ကြိုဆိုပါသည်!**\nCommands များကိုကြည့်ရန် `/help` ကိုသုံးပါ။ ဘာသာစကားပြောင်းရန် `/language` ကိုနှိပ်ပါ။",
        "help": (
            "📜 **အသုံးပြုနိုင်သော Commands များ**\n\n"
            "👤 **အသုံးပြုသူ Commands များ:**\n"
            "• `/start` - ဘော့အား စတင်ရန်\n"
            "• `/profile` - မိမိ ပရိုဖိုင်နှင့် လက်ကျန်ငွေကြည့်ရန်\n"
            "• `/catch` သို့ `/nexus` - ထွက်လာသော ကဒ်ကို ဖမ်းရန်\n"
            "• `/language` - ဘာသာစကား ပြောင်းရန် (မြန်မာ/Eng)\n\n"
            "👑 **Owner Commands များ:**\n"
            "• `/addcard` - ကဒ်အသစ် ထည့်ရန်\n"
            "• `/give` - Coins/Tokens ပေးရန်\n"
            "• `/banuser` - User အား Ban/Unban လုပ်ရန်\n"
            "• `/forcespawn` - ကဒ် ချက်ချင်း Spawn ခေါ်ရန်"
        ),
        "lang_select": "🌐 **အသုံးပြုလိုသော ဘာသာစကားကို ရွေးချယ်ပါ:**",
        "lang_changed": "✅ ဘာသာစကားကို **မြန်မာဘာသာ** သို့ ပြောင်းလိုက်ပါပြီ!",
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
# 🌐 USER COMMANDS
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

    msg = get_msg(lang, "help")
    await update.message.reply_text(msg, parse_mode="Markdown")


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
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        get_msg(lang, "lang_select"),
        reply_markup=reply_markup,
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

    msg = get_msg(selected_lang, "lang_changed")
    session.close()

    await query.edit_message_text(msg, parse_mode="Markdown")


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
# 👑 OWNER COMMANDS
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
            f"✅ **[CARD CREATED]**\n👑 Name: {name} | ID: `{cid}`",
            parse_mode="Markdown",
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
    else:
        await update.message.reply_text(
            "❌ No cards found in DB. Use `/addcard` first."
        )
    session.close()


# ==========================================
# ⚙️ AUTO SPAWN & HANDLERS
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
                print(f"Spawn Error: {err}")
        session.close()


if __name__ == "__main__":
    Thread(target=run_web).start()
    bot = ApplicationBuilder().token(BOT_TOKEN).build()

    # Register User Commands
    bot.add_handler(CommandHandler("start", start_cmd))
    bot.add_handler(CommandHandler("help", help_cmd))
    bot.add_handler(CommandHandler("language", set_language))
    bot.add_handler(CommandHandler("profile", user_profile))
    bot.add_handler(CommandHandler("nexus", catch_card))
    bot.add_handler(CommandHandler("catch", catch_card))

    # Register Button Handler
    bot.add_handler(
        CallbackQueryHandler(language_button_callback, pattern="^lang_")
    )

    # Register Owner Commands
    bot.add_handler(CommandHandler("addcard", admin_add_card))
    bot.add_handler(CommandHandler("give", admin_give_currency))
    bot.add_handler(CommandHandler("banuser", admin_ban_user))
    bot.add_handler(CommandHandler("forcespawn", admin_force_spawn))

    # Register Spawn Listener
    bot.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_spawns)
    )

    print("Master Bot Engine 24/7 Fully Operational...")
    bot.run_polling()
