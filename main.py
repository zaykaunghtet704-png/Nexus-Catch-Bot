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

# ==========================================
# 🌐 KEEP-ALIVE SERVER
# ==========================================
app = Flask(__name__)


@app.route("/")
def home():
    return "<h1>Nexus Core Active</h1>"


def run_web():
    app.run(host="0.0.0.0", port=PORT)


active_spawns = {}
chat_counts = {}

# ==========================================
# 🌐 LANGUAGE DICTIONARY
# ==========================================
LANGUAGES = {
    "en": {
        "start": "👋 **Welcome to Nexus Card Bot!**\nUse `/help` for available commands.",
        "help_user": (
            "👤 **USER COMMANDS:**\n"
            "• `/profile` - View status\n"
            "• `/collection` - View collected cards\n"
            "• `/catch` - Catch spawned character\n"
            "• `/search` - Search cards with inline button\n"
            "• `/cardlist` - View database cards\n"
            "• `/gift <user_id> <card_uuid>` - Gift a card\n"
            "• `/language` - Switch language"
        ),
        "help_owner": (
            "👑 **OWNER COMMANDS:**\n"
            "• `/addcard ID | Name | Rarity | Power` (Reply image)\n"
            "• `/forcespawn` - Force spawn a card\n"
            "• `/give <user_id> <coins/tokens> <amount>`\n"
            "• `/banuser <user_id> <ban/unban>`"
        ),
        "no_spawn": "❌ No active character to catch right now!",
        "caught": "🎉 **{name}** caught **{card}**!\n🏷️ **Print:** #{print_num}\n✨ **Quality:** {quality}%\n⭐ **Rarity:** {rarity}\n🆔 `{uuid}`",
        "banned": "🚫 You are banned from using this bot.",
    },
    "my": {
        "start": "👋 **Nexus Card Bot မှ ကြိုဆိုပါသည်!**\nCommands များကိုကြည့်ရန် `/help` ကိုသုံးပါ။",
        "help_user": (
            "👤 **အသုံးပြုသူ COMMANDS:**\n"
            "• `/profile` - ပရိုဖိုင်နှင့် လက်ကျန်ငွေကြည့်ရန်\n"
            "• `/collection` - မိမိ ရရှိထားသော ကဒ်များ ကြည့်ရန်\n"
            "• `/catch` - ထွက်လာသော ကဒ်ကို ဖမ်းယူရန်\n"
            "• `/search` - Inline Button ဖြင့် ကဒ် ရှာရန်\n"
            "• `/cardlist` - Bot ထဲရှိ ကဒ်များ ကြည့်ရန်\n"
            "• `/gift <user_id> <card_uuid>` - ကဒ် လက်ဆောင်ပေးရန်\n"
            "• `/language` - ဘာသာစကား ပြောင်းရန်"
        ),
        "help_owner": (
            "👑 **ထိန်းချုပ်သူ COMMANDS:**\n"
            "• `/addcard ID | Name | Rarity | Power` (ပုံကို Reply ပြန်၍)\n"
            "• `/forcespawn` - ကဒ် ချက်ချင်း ချပေးရန်\n"
            "• `/give <user_id> <coins/tokens> <amount>`\n"
            "• `/banuser <user_id> <ban/unban>`"
        ),
        "no_spawn": "❌ ဖမ်းယူရန် ကဒ် မရှိသေးပါ!",
        "caught": "🎉 **{name}** သည် **{card}** ကို ဖမ်းယူရရှိခဲ့သည်!\n🏷️ **Print:** #{print_num}\n✨ **Quality:** {quality}%\n⭐ **Rarity:** {rarity}\n🆔 `{uuid}`",
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
# 🔍 1. SEARCH WITH INLINE BUTTON (ဓာတ်ပုံအတိုင်း)
# ==========================================


async def search_card(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # စာမပါဘဲ /search သီးသန့် ရိုက်လျှင် Inline Button ပြမည်
    if not context.args:
        bot_username = (await context.bot.get_me()).username
        keyboard = [
            [
                InlineKeyboardButton(
                    "🔧 SEARCH CHARACTERS",
                    switch_inline_query_current_chat="",
                )
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "🔘 **TO SEARCH CHARACTER CLICK ON BUTTON BELOW**",
            reply_markup=reply_markup,
            parse_mode="Markdown",
        )
        return

    # /search Naruto ဟု စာပါပါက တိုက်ရိုက် ရှာပေးမည်
    query_name = " ".join(context.args).strip()
    session = SessionLocal()
    cards = (
        session.query(CardBase)
        .filter(CardBase.name.ilike(f"%{query_name}%"))
        .all()
    )

    if not cards:
        await update.message.reply_text("❌ ရှာဖွေသော ကဒ် မတွေ့ပါ!")
        session.close()
        return

    for card in cards[:3]:
        caption = (
            f"🔍 **[CARD DETAILS]**\n\n"
            f"🆔 **ID:** `{card.id}`\n"
            f"👤 **Name:** {card.name}\n"
            f"⭐ **Rarity:** {card.rarity}\n"
            f"⚡ **Base Power:** {card.base_power}\n"
            f"🏷️ **Total Prints:** {card.total_prints}"
        )
        try:
            await update.message.reply_photo(
                photo=card.image_url, caption=caption, parse_mode="Markdown"
            )
        except Exception:
            await update.message.reply_text(caption, parse_mode="Markdown")

    session.close()


# ==========================================
# 🎲 2. RARITY BASED AUTO SPAWN ENGINE (ကဒ်အနိမ့်/အမြင့် ရာခိုင်နှုန်း)
# ==========================================


def select_card_by_rarity(cards):
    """
    Rarity ပေါ်မူတည်၍ ကျရောက်နိုင်ခြေ (Weight/Probability) သတ်မှတ်ခြင်း:
    Common (⚪): 50% | Rare (🔵): 25% | Epic (🟣): 15% | Legendary (🟡): 8% | Mythic/UR (🔴): 2%
    """
    weights = []
    for c in cards:
        r = c.rarity.lower() if c.rarity else ""
        if "common" in r:
            weights.append(50)
        elif "rare" in r:
            weights.append(25)
        elif "epic" in r:
            weights.append(15)
        elif "legendary" in r:
            weights.append(8)
        else:
            weights.append(2)  # Mythic, UR, or others

    selected_card = random.choices(cards, weights=weights, k=1)[0]
    return selected_card


async def handle_spawns(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if (
        not update.message
        or not update.message.text
        or update.message.text.startswith("/")
    ):
        return

    chat_id = update.effective_chat.id
    chat_counts[chat_id] = chat_counts.get(chat_id, 0) + 1

    if chat_counts[chat_id] >= 100:
        session = SessionLocal()
        cards = session.query(CardBase).all()

        if cards:
            chat_counts[chat_id] = 0
            # Rarity အလိုက် ကဒ် ရွေးချယ်ခြင်း
            selected_card = select_card_by_rarity(cards)
            active_spawns[chat_id] = selected_card.id

            caption = (
                f"⚡ **A WILD CHARACTER APPEARED!**\n\n"
                f"👤 Name: **{selected_card.name}**\n"
                f"⭐ Rarity: **{selected_card.rarity}**\n\n"
                f"Use `/nexus` or `/catch` to claim!"
            )

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
# 👑 3. FLEXIBLE ADD CARD (Rarity & Power ပါဝင်ခြင်း)
# ==========================================


async def admin_add_card(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id):
        await update.message.reply_text("⚠️ Owner မဟုတ်ပါက သုံးပိုင်ခွင့် မရှိပါ။")
        return

    try:
        raw = " ".join(context.args)
        image_url = None

        if update.message.reply_to_message and (
            update.message.reply_to_message.photo
            or update.message.reply_to_message.document
        ):
            photo = update.message.reply_to_message.photo[-1]
            image_url = photo.file_id
            parts = [x.strip() for x in raw.split("|")]
        else:
            parts = [x.strip() for x in raw.split("|")]
            image_url = parts[-1]
            parts = parts[:-1]

        cid = parts[0]
        name = parts[1]
        rarity = parts[2] if len(parts) > 2 else "Common ⚪"
        power = int(parts[3]) if len(parts) > 3 else 1000

        session = SessionLocal()
        new_card = CardBase(
            id=cid,
            name=name,
            anime="General",
            rarity=rarity,
            base_power=power,
            element="Neutral",
            image_url=image_url,
        )
        session.add(new_card)
        session.commit()
        session.close()

        await update.message.reply_text(
            f"✅ **[ကဒ် ထည့်ပြီးပါပြီ]**\n🆔 ID: `{cid}`\n👤 Name: **{name}**\n⭐ Rarity: **{rarity}**\n⚡ Power: `{power}`",
            parse_mode="Markdown",
        )
    except Exception:
        await update.message.reply_text(
            "❌ **သုံးနည်း ပုံစံ:**\n\n"
            "1️⃣ **ပုံကို Reply ပြန်၍ ထည့်ရန်:**\n`/addcard ID | Name | Rarity | Power`\n*(ဥပမာ: `/addcard 001 | Naruto | Legendary 🟡 | 5000`)*\n\n"
            "2️⃣ **Link ဖြင့် ထည့်ရန်:**\n`/addcard ID | Name | Rarity | Power | Image_URL`",
            parse_mode="Markdown",
        )


# ==========================================
# 👤 BASIC USER & ADMIN COMMANDS
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
    user_id = update.effective_user.id
    session = SessionLocal()
    user = session.query(User).filter(User.id == str(user_id)).first()
    lang = user.language if user else "en"
    session.close()

    text = get_msg(lang, "help_user")
    if is_owner(user_id):
        text += "\n\n" + get_msg(lang, "help_owner")

    await update.message.reply_text(text, parse_mode="Markdown")


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
    text = (
        f"👤 **PROFILE:** {user.name}\n"
        f"💰 Coins: `{user.coins}` | 🪙 Tokens: `{user.tokens}`\n"
        f"🎴 Cards Collected: `{cards_count}`"
    )
    session.close()
    await update.message.reply_text(text, parse_mode="Markdown")


async def set_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [
            InlineKeyboardButton("🇬🇧 English", callback_data="lang_en"),
            InlineKeyboardButton("🇲🇲 မြန်မာစာ", callback_data="lang_my"),
        ]
    ]
    await update.message.reply_text(
        "🌐 Language Choice / ဘာသာစကား ရွေးချယ်ပါ:",
        reply_markup=InlineKeyboardMarkup(keyboard),
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
        f"✅ Language set to **{selected_lang.upper()}**!", parse_mode="Markdown"
    )


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


async def view_collection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    session = SessionLocal()
    user_cards = (
        session.query(UserCard).filter(UserCard.user_id == user_id).all()
    )

    if not user_cards:
        await update.message.reply_text(
            "🎴 Thave no cards yet! Use `/catch` to catch spawned cards."
        )
        session.close()
        return

    text = f"🎴 **{update.effective_user.first_name} ရဲ့ COLLECTION ({len(user_cards)})**\n\n"
    for idx, uc in enumerate(user_cards, 1):
        card_base = (
            session.query(CardBase).filter(CardBase.id == uc.card_id).first()
        )
        cname = card_base.name if card_base else "Unknown Card"
        text += f"{idx}. **{cname}** | #{uc.print_number} | Q: `{uc.quality}%` | UUID: `{uc.uuid}`\n"

    session.close()
    await update.message.reply_text(text, parse_mode="Markdown")


async def list_all_cards(update: Update, context: ContextTypes.DEFAULT_TYPE):
    session = SessionLocal()
    cards = session.query(CardBase).all()

    if not cards:
        await update.message.reply_text("❌ DB ထဲတွင် ကဒ်များ မရှိသေးပါ။")
        session.close()
        return

    text = f"🌐 **BOT DATABASE CARDS ({len(cards)})**\n\n"
    for c in cards:
        text += f"• **ID:** `{c.id}` | **Name:** {c.name} | **Rarity:** {c.rarity}\n"

    session.close()
    await update.message.reply_text(text, parse_mode="Markdown")


async def gift_card(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if len(context.args) < 2:
        await update.message.reply_text(
            "❌ သုံးနည်း: `/gift <target_user_id> <card_uuid>`"
        )
        return

    target_id, card_uuid = str(context.args[0]), str(context.args[1])
    session = SessionLocal()
    ucard = (
        session.query(UserCard)
        .filter(UserCard.uuid == card_uuid, UserCard.user_id == user_id)
        .first()
    )

    if not ucard:
        await update.message.reply_text(
            "❌ ဒီ ကဒ် UUID ကို သင့် Collection ထဲမှာ မတွေ့ပါ။"
        )
        session.close()
        return

    ucard.user_id = target_id
    session.commit()
    session.close()
    await update.message.reply_text(
        f"🎁 ကဒ် UUID `{card_uuid}` ကို User `{target_id}` ထံ လွှဲပေးလိုက်ပါပြီ။"
    )


async def admin_force_spawn(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    if not is_owner(update.effective_user.id):
        await update.message.reply_text("⚠️ Owner မဟုတ်ပါက သုံးပိုင်ခွင့် မရှိပါ။")
        return

    chat_id = update.effective_chat.id
    session = SessionLocal()
    cards = session.query(CardBase).all()

    if cards:
        selected_card = select_card_by_rarity(cards)
        active_spawns[chat_id] = selected_card.id
        caption = f"⚡ **[ADMIN SPAWN] CHARACTER APPEARED!**\nName: **{selected_card.name}**\nRarity: **{selected_card.rarity}**\nUse `/nexus` or `/catch`!"
        await context.bot.send_photo(
            chat_id=chat_id,
            photo=selected_card.image_url,
            caption=caption,
            parse_mode="Markdown",
        )
    else:
        await update.message.reply_text("❌ DB ထဲမှာ ကဒ်မရှိပါ။ `/addcard` အရင်လုပ်ပါ။")
    session.close()


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


# ==========================================
# 🚀 MAIN APP LAUNCHER
# ==========================================

if __name__ == "__main__":
    Thread(target=run_web).start()

    bot = ApplicationBuilder().token(BOT_TOKEN).build()

    # User Handlers
    bot.add_handler(CommandHandler("start", start_cmd))
    bot.add_handler(CommandHandler("help", help_cmd))
    bot.add_handler(CommandHandler("profile", user_profile))
    bot.add_handler(CommandHandler("language", set_language))
    bot.add_handler(
        CallbackQueryHandler(language_button_callback, pattern="^lang_")
    )

    # Card & Search Handlers
    bot.add_handler(CommandHandler("search", search_card))
    bot.add_handler(CommandHandler("catch", catch_card))
    bot.add_handler(CommandHandler("nexus", catch_card))
    bot.add_handler(CommandHandler("collection", view_collection))
    bot.add_handler(CommandHandler("inv", view_collection))
    bot.add_handler(CommandHandler("cardlist", list_all_cards))
    bot.add_handler(CommandHandler("gift", gift_card))

    # Control Handlers
    bot.add_handler(CommandHandler("addcard", admin_add_card))
    bot.add_handler(CommandHandler("forcespawn", admin_force_spawn))
    bot.add_handler(CommandHandler("give", admin_give_currency))
    bot.add_handler(CommandHandler("banuser", admin_ban_user))

    # Auto Spawn Listener
    bot.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_spawns)
    )

    print("Master Bot Engine Fully Operational...")
    bot.run_polling()
