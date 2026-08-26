from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

from config import (
    BOT_TOKEN,
    OWNER_ID,
)

from cards import (
    EDITIONS,
    DEFAULT_PRICES,
    DEFAULT_DROP_RATES,
    get_edition_emoji,
    normalize_edition,
    choose_weighted_card,
)

from database import (
    init_db,
    create_user,
    get_user,
    add_coins,
    add_xp,
    transfer_coins,
    claim_daily,

    create_card,
    get_card,
    get_all_cards,
    get_drop_cards,
    update_card,
    delete_card,

    add_card_to_collection,
    get_collection,

    create_drop,
    claim_drop,
)

from drops import (
    drop_keyboard,
    build_drop_text,
    build_winner_text,
)


# ==================================================
# HELPERS
# ==================================================

def is_owner(user_id: int):

    return user_id == OWNER_ID


def ensure_user(user):

    create_user(
        user.id,
        user.username or "",
        user.first_name or ""
    )


# ==================================================
# START
# ==================================================

async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    user = update.effective_user

    ensure_user(user)

    text = (
        "╭━━━━━━━━━━━━━━━━━━━━╮\n"
        "       🃏 *CARD WORLD* 🃏\n"
        "╰━━━━━━━━━━━━━━━━━━━━╯\n\n"

        "✨ Welcome, Collector!\n\n"

        "🎴 Collect rare cards\n"
        "💎 Discover Premium cards\n"
        "🔥 Catch limited drops\n"
        "🏆 Build your collection\n\n"

        "📌 *COMMANDS*\n\n"

        "🎴 /draw — Draw Card\n"
        "📚 /collection — Collection\n"
        "👤 /profile — Profile\n"
        "🪙 /balance — Balance\n"
        "🎁 /daily — Daily Reward\n"
        "💸 /transfer — Send Coins\n"
        "ℹ️ /help — Help\n\n"

        "✨ Good luck, Collector! ✨"
    )

    await update.message.reply_text(
        text,
        parse_mode="Markdown"
    )


# ==================================================
# HELP
# ==================================================

async def help_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    text = (
        "📖 *CARD WORLD HELP*\n\n"

        "🎴 `/draw`\n"
        "Random Card ရယူရန်\n\n"

        "📚 `/collection`\n"
        "ကိုယ့် Collection ကြည့်ရန်\n\n"

        "👤 `/profile`\n"
        "Profile ကြည့်ရန်\n\n"

        "🪙 `/balance`\n"
        "Coins ကြည့်ရန်\n\n"

        "🎁 `/daily`\n"
        "Daily Reward ရယူရန်\n\n"

        "💸 `/transfer USER_ID AMOUNT`\n"
        "Coins ပို့ရန်\n\n"

        "━━━━━━━━━━━━━━━━━━\n"
        "👑 *OWNER COMMANDS*\n"
        "━━━━━━━━━━━━━━━━━━\n\n"

        "➕ `/addcard`\n"
        "📋 `/cards`\n"
        "🗑️ `/deletecard ID`\n"
        "💰 `/setprice ID PRICE`\n"
        "🎯 `/setdrop ID RATE`\n"
        "💎 `/setedition ID EDITION`\n"
        "🎁 `/drop`\n"
        "🎴 `/givecard USER_ID CARD_ID`\n"
        "🪙 `/givecoin USER_ID AMOUNT`\n"
    )

    await update.message.reply_text(
        text,
        parse_mode="Markdown"
    )


# ==================================================
# PROFILE
# ==================================================

async def profile(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    user = update.effective_user

    ensure_user(user)

    data = get_user(user.id)

    if not data:
        return

    (
        user_id,
        username,
        first_name,
        coins,
        xp,
        level,
        last_daily
    ) = data

    display_name = (
        f"@{username}"
        if username
        else first_name
    )

    text = (
        "╭━━━━━━━━━━━━━━━━━━━━╮\n"
        "          👤 *PROFILE*\n"
        "╰━━━━━━━━━━━━━━━━━━━━╯\n\n"

        f"🧑 Name: *{display_name}*\n"
        f"🆔 ID: `{user_id}`\n\n"

        f"🪙 Coins: *{coins:,}*\n"
        f"⭐ XP: *{xp:,}*\n"
        f"🏆 Level: *{level}*\n\n"

        "✨ Keep collecting!"
    )

    await update.message.reply_text(
        text,
        parse_mode="Markdown"
    )


# ==================================================
# BALANCE
# ==================================================

async def balance(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    user = update.effective_user

    ensure_user(user)

    data = get_user(user.id)

    if not data:
        return

    coins = data[3]

    await update.message.reply_text(
        "🪙 *YOUR BALANCE*\n\n"
        f"💰 Coins: *{coins:,} 🪙*",
        parse_mode="Markdown"
    )


# ==================================================
# DAILY
# ==================================================

async def daily(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    user = update.effective_user

    ensure_user(user)

    success = claim_daily(user.id)

    if not success:

        await update.message.reply_text(
            "⏳ *Daily Reward ရယူပြီးပါပြီ။*\n\n"
            "🌙 မနက်ဖြန် ပြန်လာခဲ့ပါ!",
            parse_mode="Markdown"
        )

        return

    await update.message.reply_text(
        "🎁━━━━━━━━━━━━━━━━━━🎁\n"
        "       ✨ *DAILY REWARD* ✨\n"
        "🎁━━━━━━━━━━━━━━━━━━🎁\n\n"

        "🪙 +100 Coins\n"
        "⭐ +20 XP\n\n"

        "🔥 Congratulations!\n"
        "🌙 Tomorrow, come back again!",
        parse_mode="Markdown"
    )


# ==================================================
# TRANSFER
# ==================================================

async def transfer(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    user = update.effective_user

    ensure_user(user)

    if len(context.args) != 2:

        await update.message.reply_text(
            "❌ အသုံးပြုပုံ:\n\n"
            "`/transfer USER_ID AMOUNT`",
            parse_mode="Markdown"
        )

        return

    try:

        target_id = int(
            context.args[0]
        )

        amount = int(
            context.args[1]
        )

    except ValueError:

        await update.message.reply_text(
            "❌ User ID / Amount မမှန်ပါ။"
        )

        return

    success, reason = transfer_coins(
        user.id,
        target_id,
        amount
    )

    if success:

        await update.message.reply_text(
            "✅ *TRANSFER SUCCESSFUL!*\n\n"
            f"👤 To: `{target_id}`\n"
            f"🪙 Amount: *{amount:,} Coins*",
            parse_mode="Markdown"
        )

    elif reason == "INSUFFICIENT":

        await update.message.reply_text(
            "❌ Coins မလုံလောက်ပါ။"
        )

    elif reason == "SELF_TRANSFER":

        await update.message.reply_text(
            "❌ ကိုယ့်ကိုယ်ကို Coins ပို့လို့မရပါ။"
        )

    elif reason == "RECEIVER_NOT_FOUND":

        await update.message.reply_text(
            "❌ အဲဒီ User က Bot ကို မစသေးပါ။"
        )

    else:

        await update.message.reply_text(
            "❌ Transfer မအောင်မြင်ပါ။"
        )


# ==================================================
# DRAW
# ==================================================

async def draw(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    user = update.effective_user

    ensure_user(user)

    cards = get_drop_cards()

    card = choose_weighted_card(cards)

    if not card:

        await update.message.reply_text(
            "⚠️ Card Database ထဲမှာ Card မရှိသေးပါ။"
        )

        return

    (
        card_id,
        name,
        edition,
        price,
        rate,
        description,
        media_type,
        file_id,
        limited
    ) = card

    add_card_to_collection(
        user.id,
        card_id
    )

    add_xp(
        user.id,
        5
    )

    emoji = get_edition_emoji(
        edition
    )

    text = (
        "🎴✨ *CARD DRAW!* ✨🎴\n\n"

        f"🃏 *{name}*\n"
        f"{emoji} *{edition}*\n"
        f"💰 Value: *{price:,} 🪙*\n\n"

        "📚 Collection ထဲ ထည့်ပြီးပါပြီ!\n"
        "⭐ +5 XP"
    )

    if media_type == "photo" and file_id:

        await update.message.reply_photo(
            photo=file_id,
            caption=text,
            parse_mode="Markdown"
        )

    elif media_type == "video" and file_id:

        await update.message.reply_video(
            video=file_id,
            caption=text,
            parse_mode="Markdown"
        )

    else:

        await update.message.reply_text(
            text,
            parse_mode="Markdown"
        )


# ==================================================
# COLLECTION
# ==================================================

async def collection(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    user = update.effective_user

    ensure_user(user)

    cards = get_collection(
        user.id
    )

    if not cards:

        await update.message.reply_text(
            "📚 *YOUR COLLECTION*\n\n"
            "🗃️ Collection အလွတ်ပါ။\n\n"
            "🎴 `/draw` နဲ့ Card စုလိုက်ပါ!",
            parse_mode="Markdown"
        )

        return

    lines = [
        "╭━━━━━━━━━━━━━━━━━━━━╮",
        "       📚 *COLLECTION*",
        "╰━━━━━━━━━━━━━━━━━━━━╯",
        ""
    ]

    for card in cards:

        (
            card_id,
            name,
            edition,
            price,
            media_type,
            amount
        ) = card

        emoji = get_edition_emoji(
            edition
        )

        lines.append(
            f"{emoji} *{name}*\n"
            f"💎 {edition}\n"
            f"💰 {price:,} 🪙\n"
            f"📦 ×{amount}\n"
        )

    await update.message.reply_text(
        "\n".join(lines),
        parse_mode="Markdown"
    )


# ==================================================
# OWNER CHECK
# ==================================================

async def owner_only(
    update: Update
):

    user = update.effective_user

    if not is_owner(user.id):

        await update.message.reply_text(
            "⛔ *OWNER ONLY*\n\n"
            "ဒီ command ကို Owner ပဲ အသုံးပြုနိုင်ပါတယ်။",
            parse_mode="Markdown"
        )

        return False

    return True


# ==================================================
# OWNER: ADD CARD TEXT
# ==================================================

async def addcard(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not await owner_only(update):
        return

    if not context.args:

        await update.message.reply_text(
            "❌ အသုံးပြုပုံ:\n\n"
            "`/addcard Card Name | Edition | Price`\n\n"
            "ဥပမာ:\n"
            "`/addcard Naruto | Premium Edition | 1000000`",
            parse_mode="Markdown"
        )

        return

    raw = " ".join(
        context.args
    )

    parts = [
        x.strip()
        for x in raw.split("|")
    ]

    if len(parts) < 2:

        await update.message.reply_text(
            "❌ Format မမှန်ပါ။"
        )

        return

    name = parts[0]

    edition = normalize_edition(
        parts[1]
    )

    if not edition:

        await update.message.reply_text(
            "❌ Edition မမှန်ပါ။\n\n"
            + "\n".join(
                f"• {x}"
                for x in EDITIONS
            )
        )

        return

    if len(parts) >= 3:

        try:
            price = int(parts[2])
        except ValueError:
            price = DEFAULT_PRICES[edition]

    else:

        price = DEFAULT_PRICES[edition]

    rate = DEFAULT_DROP_RATES[edition]

    card_id = create_card(
        name=name,
        edition=edition,
        price=price,
        drop_rate=rate
    )

    await update.message.reply_text(
        "✅ *CARD CREATED!*\n\n"
        f"🆔 ID: `{card_id}`\n"
        f"🃏 Name: *{name}*\n"
        f"💎 Edition: *{edition}*\n"
        f"💰 Price: *{price:,} 🪙*\n"
        f"🎯 Drop Rate: *{rate}%*\n\n"

        "📎 Media: မရှိသေးပါ\n\n"

        "💡 Photo/Video ချိတ်ရန်:\n"
        f"`/attach {card_id}`",
        parse_mode="Markdown"
    )


# ==================================================
# OWNER: MEDIA ATTACH
# ==================================================

async def attach(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not await owner_only(update):
        return

    if len(context.args) != 1:

        await update.message.reply_text(
            "အသုံးပြုပုံ:\n"
            "`/attach CARD_ID`\n\n"
            "ပြီးရင် Photo/Video ပို့ပါ။",
            parse_mode="Markdown"
        )

        return

    try:

        card_id = int(
            context.args[0]
        )

    except ValueError:

        await update.message.reply_text(
            "❌ Card ID မမှန်ပါ။"
        )

        return

    card = get_card(card_id)

    if not card:

        await update.message.reply_text(
            "❌ Card မတွေ့ပါ။"
        )

        return

    context.user_data["attach_card_id"] = card_id

    await update.message.reply_text(
        "📎 *MEDIA ATTACH MODE*\n\n"
        f"🎴 Card ID: `{card_id}`\n\n"
        "🖼️ Photo ဒါမှမဟုတ် 🎬 Video ကို\n"
        "အခု ပို့လိုက်ပါ။",
        parse_mode="Markdown"
    )


# ==================================================
# OWNER: MEDIA MESSAGE
# ==================================================

async def media_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not is_owner(
        update.effective_user.id
    ):
        return

    card_id = context.user_data.get(
        "attach_card_id"
    )

    if not card_id:
        return

    media_type = None
    file_id = None

    if update.message.photo:

        media_type = "photo"

        file_id = (
            update.message
            .photo[-1]
            .file_id
        )

    elif update.message.video:

        media_type = "video"

        file_id = (
            update.message
            .video
            .file_id
        )

    if not media_type:

        return

    success = update_card(
        card_id,
        media_type=media_type,
        file_id=file_id
    )

    context.user_data.pop(
        "attach_card_id",
        None
    )

    if not success:

        await update.message.reply_text(
            "❌ Card မတွေ့ပါ။"
        )

        return

    emoji = (
        "🖼️"
        if media_type == "photo"
        else "🎬"
    )

    await update.message.reply_text(
        f"✅ *MEDIA ATTACHED!*\n\n"
        f"🎴 Card ID: `{card_id}`\n"
        f"{emoji} Type: *{media_type}*",
        parse_mode="Markdown"
    )


# ==================================================
# OWNER: CARDS
# ==================================================

async def cards(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not await owner_only(update):
        return

    all_cards = get_all_cards()

    if not all_cards:

        await update.message.reply_text(
            "🗃️ Card Database အလွတ်ပါ။"
        )

        return

    lines = [
        "╭━━━━━━━━━━━━━━━━━━━━╮",
        "       🎴 *CARD DATABASE*",
        "╰━━━━━━━━━━━━━━━━━━━━╯",
        ""
    ]

    for card in all_cards:

        (
            card_id,
            name,
            edition,
            price,
            rate,
            description,
            media_type,
            file_id,
            limited
        ) = card

        emoji = get_edition_emoji(
            edition
        )

        media = (
            "🖼️ Photo"
            if media_type == "photo"
            else "🎬 Video"
            if media_type == "video"
            else "📭 None"
        )

        limited_text = (
            " 🔥 LIMITED"
            if limited
            else ""
        )

        lines.append(
            f"🆔 `{card_id}` — *{name}*\n"
            f"{emoji} {edition}{limited_text}\n"
            f"💰 {price:,} 🪙\n"
            f"🎯 {rate}%\n"
            f"📎 {media}\n"
        )

    await update.message.reply_text(
        "\n".join(lines),
        parse_mode="Markdown"
    )


# ==================================================
# OWNER: DELETE
# ==================================================

async def deletecard(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not await owner_only(update):
        return

    if len(context.args) != 1:

        await update.message.reply_text(
            "`/deletecard CARD_ID`",
            parse_mode="Markdown"
        )

        return

    try:

        card_id = int(
            context.args[0]
        )

    except ValueError:

        await update.message.reply_text(
            "❌ Card ID မမှန်ပါ။"
        )

        return

    if delete_card(card_id):

        await update.message.reply_text(
            "🗑️ *CARD DELETED!*",
            parse_mode="Markdown"
        )

    else:

        await update.message.reply_text(
            "❌ Card မတွေ့ပါ။"
        )


# ==================================================
# OWNER: SET PRICE
# ==================================================

async def setprice(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not await owner_only(update):
        return

    if len(context.args) != 2:

        await update.message.reply_text(
            "`/setprice CARD_ID PRICE`",
            parse_mode="Markdown"
        )

        return

    try:

        card_id = int(
            context.args[0]
        )

        price = int(
            context.args[1]
        )

    except ValueError:

        await update.message.reply_text(
            "❌ Number မမှန်ပါ။"
        )

        return

    if price < 0:

        await update.message.reply_text(
            "❌ Price က 0 ထက်ငယ်လို့မရပါ။"
        )

        return

    if not update_card(
        card_id,
        price=price
    ):

        await update.message.reply_text(
            "❌ Card မတွေ့ပါ။"
        )

        return

    await update.message.reply_text(
        f"✅ Card `{card_id}` Price → "
        f"*{price:,} 🪙*",
        parse_mode="Markdown"
    )


# ==================================================
# OWNER: SET DROP
# ==================================================

async def setdrop(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not await owner_only(update):
        return

    if len(context.args) != 2:

        await update.message.reply_text(
            "`/setdrop CARD_ID RATE`",
            parse_mode="Markdown"
        )

        return

    try:

        card_id = int(
            context.args[0]
        )

        rate = float(
            context.args[1]
        )

    except ValueError:

        await update.message.reply_text(
            "❌ Number မမှန်ပါ။"
        )

        return

    if rate < 0:

        await update.message.reply_text(
            "❌ Rate က 0 ထက်ငယ်လို့မရပါ။"
        )

        return

    if not update_card(
        card_id,
        drop_rate=rate
    ):

        await update.message.reply_text(
            "❌ Card မတွေ့ပါ။"
        )

        return

    await update.message.reply_text(
        f"🎯 Card `{card_id}` Drop Rate → "
        f"*{rate}%*",
        parse_mode="Markdown"
    )


# ==================================================
# OWNER: SET EDITION
# ==================================================

async def setedition(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not await owner_only(update):
        return

    if len(context.args) < 2:

        await update.message.reply_text(
            "`/setedition CARD_ID EDITION`",
            parse_mode="Markdown"
        )

        return

    try:

        card_id = int(
            context.args[0]
        )

    except ValueError:

        await update.message.reply_text(
            "❌ Card ID မမှန်ပါ။"
        )

        return

    edition = normalize_edition(
        " ".join(
            context.args[1:]
        )
    )

    if not edition:

        await update.message.reply_text(
            "❌ Edition မမှန်ပါ။"
        )

        return

    if not update_card(
        card_id,
        edition=edition
    ):

        await update.message.reply_text(
            "❌ Card မတွေ့ပါ။"
        )

        return

    await update.message.reply_text(
        f"💎 Card `{card_id}` → "
        f"*{edition}*",
        parse_mode="Markdown"
    )


# ==================================================
# OWNER: DROP
# ==================================================

async def drop(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not await owner_only(update):
        return

    cards = get_drop_cards()

    card = choose_weighted_card(
        cards
    )

    if not card:

        await update.message.reply_text(
            "⚠️ Drop လုပ်ဖို့ Card မရှိပါ။"
        )

        return

    (
        card_id,
        name,
        edition,
        price,
        rate,
        description,
        media_type,
        file_id,
        limited
    ) = card

    drop_id = create_drop(
        card_id
    )

    keyboard = drop_keyboard(
        drop_id
    )

    caption = build_drop_text(
        card
    )

    if media_type == "photo" and file_id:

        await update.message.reply_photo(
            photo=file_id,
            caption=caption,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )

    elif media_type == "video" and file_id:

        await update.message.reply_video(
            video=file_id,
            caption=caption,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )

    else:

        await update.message.reply_text(
            caption,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )


# ==================================================
# GET CARD BUTTON
# ==================================================

async def card_drop_button(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    user = query.from_user

    ensure_user(user)

    try:

        drop_id = int(
            query.data.split(":")[1]
        )

    except (IndexError, ValueError):

        await query.answer(
            "❌ Invalid Drop",
            show_alert=True
        )

        return

    card_id = claim_drop(
        drop_id,
        user.id
    )

    if card_id is None:

        await query.answer(
            "❌ TOO LATE!\n\n"
            "ဒီ Card ကို တစ်ယောက်က ရယူပြီးပါပြီ။",
            show_alert=True
        )

        return

    card = get_card(
        card_id
    )

    if not card:

        await query.answer(
            "⚠️ Card Data မတွေ့ပါ။",
            show_alert=True
        )

        return

    await query.answer(
        "🎉 CARD CLAIMED!",
        show_alert=True
    )

    text = build_winner_text(
        user,
        card
    )

    await query.message.reply_text(
        text,
        parse_mode="HTML"
    )


# ==================================================
# OWNER: GIVE COIN
# ==================================================

async def givecoin(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not await owner_only(update):
        return

    if len(context.args) != 2:

        await update.message.reply_text(
            "`/givecoin USER_ID AMOUNT`",
            parse_mode="Markdown"
        )

        return

    try:

        user_id = int(
            context.args[0]
        )

        amount = int(
            context.args[1]
        )

    except ValueError:

        await update.message.reply_text(
            "❌ Number မမှန်ပါ။"
        )

        return

    if amount <= 0:

        await update.message.reply_text(
            "❌ Amount မှန်အောင်ထည့်ပါ။"
        )

        return

    if not get_user(user_id):

        await update.message.reply_text(
            "❌ User မတွေ့ပါ။"
        )

        return

    add_coins(
        user_id,
        amount
    )

    await update.message.reply_text(
        "✅ *COINS GIVEN!*\n\n"
        f"👤 User: `{user_id}`\n"
        f"🪙 +{amount:,} Coins",
        parse_mode="Markdown"
    )


# ==================================================
# OWNER: GIVE CARD
# ==================================================

async def givecard(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not await owner_only(update):
        return

    if len(context.args) != 2:

        await update.message.reply_text(
            "`/givecard USER_ID CARD_ID`",
            parse_mode="Markdown"
        )

        return

    try:

        user_id = int(
            context.args[0]
        )

        card_id = int(
            context.args[1]
        )

    except ValueError:

        await update.message.reply_text(
            "❌ ID မမှန်ပါ။"
        )

        return

    if not get_user(user_id):

        await update.message.reply_text(
            "❌ User မတွေ့ပါ။"
        )

        return

    card = get_card(
        card_id
    )

    if not card:

        await update.message.reply_text(
            "❌ Card မတွေ့ပါ။"
        )

        return

    add_card_to_collection(
        user_id,
        card_id
    )

    await update.message.reply_text(
        "🎴 *CARD GIVEN!*\n\n"
        f"👤 User: `{user_id}`\n"
        f"🃏 Card: *{card[1]}*\n"
        f"💎 Edition: *{card[2]}*",
        parse_mode="Markdown"
    )


# ==================================================
# ERROR HANDLER
# ==================================================

async def error_handler(
    update: object,
    context: ContextTypes.DEFAULT_TYPE
):

    print(
        "BOT ERROR:",
        context.error
    )


# ==================================================
# MAIN
# ==================================================

def main():

    if not BOT_TOKEN:

        raise RuntimeError(
            "BOT_TOKEN မတွေ့ပါ။ Render Environment ကို စစ်ပါ။"
        )

    if OWNER_ID == 0:

        raise RuntimeError(
            "OWNER_ID မတွေ့ပါ။ Render Environment ကို စစ်ပါ။"
        )

    init_db()

    app = (
        Application
        .builder()
        .token(BOT_TOKEN)
        .build()
    )

    # --------------------------
    # USER COMMANDS
    # --------------------------

    app.add_handler(
        CommandHandler(
            "start",
            start
        )
    )

    app.add_handler(
        CommandHandler(
            "help",
            help_command
        )
    )

    app.add_handler(
        CommandHandler(
            "profile",
            profile
        )
    )

    app.add_handler(
        CommandHandler(
            "balance",
            balance
        )
    )

    app.add_handler(
        CommandHandler(
            "daily",
            daily
        )
    )

    app.add_handler(
        CommandHandler(
            "transfer",
            transfer
        )
    )

    app.add_handler(
        CommandHandler(
            "draw",
            draw
        )
    )

    app.add_handler(
        CommandHandler(
            "collection",
            collection
        )
    )

    # --------------------------
    # OWNER
    # --------------------------

    app.add_handler(
        CommandHandler(
            "addcard",
            addcard
        )
    )

    app.add_handler(
        CommandHandler(
            "attach",
            attach
        )
    )

    app.add_handler(
        CommandHandler(
            "cards",
            cards
        )
    )

    app.add_handler(
        CommandHandler(
            "deletecard",
            deletecard
        )
    )

    app.add_handler(
        CommandHandler(
            "setprice",
            setprice
        )
    )

    app.add_handler(
        CommandHandler(
            "setdrop",
            setdrop
        )
    )

    app.add_handler(
        CommandHandler(
            "setedition",
            setedition
        )
    )

    app.add_handler(
        CommandHandler(
            "drop",
            drop
        )
    )

    app.add_handler(
        CommandHandler(
            "givecoin",
            givecoin
        )
    )

    app.add_handler(
        CommandHandler(
            "givecard",
            givecard
        )
    )

    # --------------------------
    # PHOTO / VIDEO
    # --------------------------

    app.add_handler(
        MessageHandler(
            filters.PHOTO,
            media_message
        )
    )

    app.add_handler(
        MessageHandler(
            filters.VIDEO,
            media_message
        )
    )

    # --------------------------
    # GET CARD
    # --------------------------

    app.add_handler(
        CallbackQueryHandler(
            card_drop_button,
            pattern=r"^carddrop:\d+$"
        )
    )

    # --------------------------
    # ERROR
    # --------------------------

    app.add_error_handler(
        error_handler
    )

    print(
        "🃏 CARD WORLD V4 IS RUNNING..."
    )

    app.run_polling()


if __name__ == "__main__":
    main()
