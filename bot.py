from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

from config import BOT_TOKEN, OWNER_ID

from database import (
    init_db,
    create_user,
    get_user,
    create_card,
    get_card,
    get_all_cards,
    update_card,
    delete_card,
    get_random_card,
    create_drop,
    claim_drop,
    get_collection,
    claim_daily,
)

from cards import (
    EDITIONS,
    DEFAULT_PRICES,
    DROP_RATES,
    normalize_edition,
    choose_edition,
    get_edition_emoji,
)

from drops import (
    drop_keyboard,
    drop_caption,
)


# =====================================
# HELPERS
# =====================================

def is_owner(user_id: int):
    return user_id == OWNER_ID


def ensure_user(user):
    create_user(
        user.id,
        user.username
    )


# =====================================
# START
# =====================================

async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    user = update.effective_user

    ensure_user(user)

    text = (
        "✨━━━━━━━━━━━━━━━━━━✨\n"
        "       🃏 *CARD WORLD* 🃏\n"
        "✨━━━━━━━━━━━━━━━━━━✨\n\n"

        "🎴 Welcome, Collector!\n\n"

        "💎 Collect rare cards\n"
        "🔥 Catch limited drops\n"
        "🏆 Build your collection\n\n"

        "📌 *Commands*\n\n"
        "🎴 /draw — Draw Card\n"
        "📚 /collection — Collection\n"
        "👤 /profile — Profile\n"
        "🎁 /daily — Daily Reward\n"
        "ℹ️ /help — Help\n\n"

        "✨ Good luck! ✨"
    )

    await update.message.reply_text(
        text,
        parse_mode="Markdown"
    )


# =====================================
# HELP
# =====================================

async def help_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    text = (
        "📖 *CARD WORLD HELP*\n\n"

        "🎴 /draw\n"
        "Card တစ်ကဒ် ရယူရန်\n\n"

        "📚 /collection\n"
        "ကိုယ့် Card Collection ကြည့်ရန်\n\n"

        "👤 /profile\n"
        "Profile ကြည့်ရန်\n\n"

        "🎁 /daily\n"
        "Daily Reward ရယူရန်\n\n"

        "👑 *OWNER COMMANDS*\n\n"

        "➕ /addcard\n"
        "📋 /cards\n"
        "✏️ /editcard\n"
        "🗑️ /deletecard\n"
        "🎁 /drop\n"
    )

    await update.message.reply_text(
        text,
        parse_mode="Markdown"
    )


# =====================================
# PROFILE
# =====================================

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
        coins,
        xp,
        level,
        last_daily
    ) = data

    text = (
        "👤 *YOUR PROFILE*\n\n"
        f"🆔 ID: `{user_id}`\n"
        f"👤 Name: {username or user.first_name}\n\n"
        f"🪙 Coins: *{coins:,}*\n"
        f"⭐ XP: *{xp:,}*\n"
        f"🏆 Level: *{level}*"
    )

    await update.message.reply_text(
        text,
        parse_mode="Markdown"
    )


# =====================================
# DAILY
# =====================================

async def daily(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    user = update.effective_user

    ensure_user(user)

    if not claim_daily(user.id):
        await update.message.reply_text(
            "⏳ *Daily Reward ရယူပြီးပါပြီ!*\n\n"
            "🌙 မနက်ဖြန် ပြန်လာခဲ့ပါ။",
            parse_mode="Markdown"
        )
        return

    await update.message.reply_text(
        "🎁✨ *DAILY REWARD!* ✨🎁\n\n"
        "🪙 +100 Coins\n"
        "⭐ +20 XP\n\n"
        "🔥 Congratulations, Collector!",
        parse_mode="Markdown"
    )


# =====================================
# DRAW
# =====================================

async def draw(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    user = update.effective_user

    ensure_user(user)

    card = get_random_card()

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
        drop_rate,
        description,
        media_type,
        file_id
    ) = card

    from database import add_card_to_collection

    add_card_to_collection(
        user.id,
        card_id
    )

    emoji = get_edition_emoji(
        edition
    )

    text = (
        "🎴✨ *CARD DRAW!* ✨🎴\n\n"
        f"🃏 *{name}*\n"
        f"{emoji} *{edition}*\n"
        f"💰 Value: *{price:,} 🪙*\n\n"
        "📚 Collection ထဲ ထည့်ပြီးပါပြီ!"
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


# =====================================
# COLLECTION
# =====================================

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
            "🗃️ Collection အလွတ်ဖြစ်နေပါတယ်။\n\n"
            "🎴 /draw နဲ့ Card စုလိုက်ပါ!",
            parse_mode="Markdown"
        )
        return

    lines = [
        "📚 *YOUR COLLECTION*",
        "━━━━━━━━━━━━━━━━━━",
        ""
    ]

    for (
        card_id,
        name,
        edition,
        price,
        amount
    ) in cards:

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


# =====================================
# OWNER: ADD CARD
# =====================================

async def addcard(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    user = update.effective_user

    if not is_owner(user.id):
        await update.message.reply_text(
            "⛔ Owner Only Command"
        )
        return

    if not context.args:
        await update.message.reply_text(
            "❌ အသုံးပြုပုံ:\n\n"
            "/addcard Card Name | Edition\n\n"
            "ဥပမာ:\n"
            "/addcard Naruto | Premium Edition"
        )
        return

    raw = " ".join(
        context.args
    )

    if "|" not in raw:
        await update.message.reply_text(
            "❌ `|` ထည့်ပေးပါ။\n\n"
            "ဥပမာ:\n"
            "/addcard Naruto | Premium Edition",
            parse_mode="Markdown"
        )
        return

    name, edition_raw = [
        x.strip()
        for x in raw.split(
            "|",
            1
        )
    ]

    edition = normalize_edition(
        edition_raw
    )

    if not edition:
        await update.message.reply_text(
            "❌ Edition မမှန်ပါ။"
        )
        return

    price = DEFAULT_PRICES[
        edition
    ]

    rate = DROP_RATES[
        edition
    ]

    card_id = create_card(
        name=name,
        edition=edition,
        price=price,
        drop_rate=rate
    )

    emoji = get_edition_emoji(
        edition
    )

    await update.message.reply_text(
        "✅✨ *CARD CREATED!* ✨\n\n"
        f"🆔 ID: `{card_id}`\n"
        f"🃏 Name: *{name}*\n"
        f"{emoji} Edition: *{edition}*\n"
        f"💰 Price: *{price:,} 🪙*\n"
        f"🎯 Drop Rate: *{rate}%*",
        parse_mode="Markdown"
    )


# =====================================
# OWNER: CARDS
# =====================================

async def cards(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    user = update.effective_user

    if not is_owner(user.id):
        await update.message.reply_text(
            "⛔ Owner Only Command"
        )
        return

    all_cards = get_all_cards()

    if not all_cards:
        await update.message.reply_text(
            "🗃️ Card Database အလွတ်ပါ။"
        )
        return

    lines = [
        "🎴 *CARD DATABASE*",
        "━━━━━━━━━━━━━━━━━━",
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
            file_id
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

        lines.append(
            f"🆔 `{card_id}` — *{name}*\n"
            f"{emoji} {edition}\n"
            f"💰 {price:,} 🪙 | 🎯 {rate}%\n"
            f"📎 {media}\n"
        )

    await update.message.reply_text(
        "\n".join(lines),
        parse_mode="Markdown"
    )


# =====================================
# OWNER: DELETE CARD
# =====================================

async def deletecard(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    user = update.effective_user

    if not is_owner(user.id):
        await update.message.reply_text(
            "⛔ Owner Only Command"
        )
        return

    if not context.args:
        await update.message.reply_text(
            "အသုံးပြုပုံ:\n"
            "/deletecard CARD_ID"
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
            "🗑️ Card ဖျက်ပြီးပါပြီ။"
        )
    else:
        await update.message.reply_text(
            "❌ Card မတွေ့ပါ။"
        )


# =====================================
# OWNER: SET PRICE
# =====================================

async def setprice(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    user = update.effective_user

    if not is_owner(user.id):
        await update.message.reply_text(
            "⛔ Owner Only Command"
        )
        return

    if len(context.args) != 2:
        await update.message.reply_text(
            "အသုံးပြုပုံ:\n"
            "/setprice CARD_ID PRICE"
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

    if not get_card(card_id):
        await update.message.reply_text(
            "❌ Card မတွေ့ပါ။"
        )
        return

    update_card(
        card_id,
        price=price
    )

    await update.message.reply_text(
        f"💰 Card `{card_id}` Price ကို\n"
        f"*{price:,} 🪙* သို့ ပြောင်းပြီးပါပြီ။",
        parse_mode="Markdown"
    )


# =====================================
# OWNER: SET EDITION
# =====================================

async def setedition(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    user = update.effective_user

    if not is_owner(user.id):
        await update.message.reply_text(
            "⛔ Owner Only Command"
        )
        return

    if len(context.args) < 2:
        await update.message.reply_text(
            "/setedition CARD_ID EDITION"
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

    edition_raw = " ".join(
        context.args[1:]
    )

    edition = normalize_edition(
        edition_raw
    )

    if not edition:
        await update.message.reply_text(
            "❌ Edition မမှန်ပါ။"
        )
        return

    if not get_card(card_id):
        await update.message.reply_text(
            "❌ Card မတွေ့ပါ။"
        )
        return

    update_card(
        card_id,
        edition=edition
    )

    await update.message.reply_text(
        f"💎 Card `{card_id}` ကို\n"
        f"*{edition}* သို့ ပြောင်းပြီးပါပြီ။",
        parse_mode="Markdown"
    )


# =====================================
# OWNER: SET DROP RATE
# =====================================

async def setdrop(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    user = update.effective_user

    if not is_owner(user.id):
        await update.message.reply_text(
            "⛔ Owner Only Command"
        )
        return

    if len(context.args) != 2:
        await update.message.reply_text(
            "/setdrop CARD_ID RATE"
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

    if not get_card(card_id):
        await update.message.reply_text(
            "❌ Card မတွေ့ပါ။"
        )
        return

    update_card(
        card_id,
        drop_rate=rate
    )

    await update.message.reply_text(
        f"🎯 Card `{card_id}` Drop Rate ကို\n"
        f"*{rate}%* သို့ ပြောင်းပြီးပါပြီ။",
        parse_mode="Markdown"
    )


# =====================================
# OWNER: DROP
# =====================================

async def drop(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    user = update.effective_user

    if not is_owner(user.id):
        await update.message.reply_text(
            "⛔ Owner Only Command"
        )
        return

    card = get_random_card()

    if not card:
        await update.message.reply_text(
            "⚠️ Drop လုပ်ဖို့ Card မရှိသေးပါ။"
        )
        return

    (
        card_id,
        name,
        edition,
        price,
        drop_rate,
        description,
        media_type,
        file_id
    ) = card

    drop_id = create_drop(
        card_id
    )

    keyboard = drop_keyboard(
        drop_id
    )

    caption = drop_caption(
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


# =====================================
# DROP BUTTON
# =====================================

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
            "❌ Too Late!\n"
            "ဒီ Card ကို တစ်ယောက်က ရယူပြီးပါပြီ။",
            show_alert=True
        )

        return

    card = get_card(
        card_id
    )

    if not card:
        await query.answer(
            "⚠️ Card data မတွေ့ပါ။",
            show_alert=True
        )
        return

    (
        _id,
        name,
        edition,
        price,
        rate,
        description,
        media_type,
        file_id
    ) = card

    emoji = get_edition_emoji(
        edition
    )

    await query.answer(
        "🎉 Card ရပါပြီ!",
        show_alert=True
    )

    winner = user.mention_html()

    text = (
        "🎉✨ <b>CARD CLAIMED!</b> ✨🎉\n\n"
        f"👑 Winner: {winner}\n"
        f"🎴 Card: <b>{name}</b>\n"
        f"{emoji} Edition: <b>{edition}</b>\n"
        f"💰 Value: <b>{price:,} 🪙</b>\n\n"
        "📚 Collection ထဲ ထည့်ပြီးပါပြီ!\n\n"
        "🔥 Congratulations, Collector!"
    )

    await query.message.reply_text(
        text,
        parse_mode="HTML"
    )


# =====================================
# MAIN
# =====================================

def main():

    if not BOT_TOKEN:
        raise RuntimeError(
            "BOT_TOKEN မတွေ့ပါ။ .env ကို စစ်ပါ။"
        )

    if OWNER_ID == 0:
        raise RuntimeError(
            "OWNER_ID မတွေ့ပါ။ .env ကို စစ်ပါ။"
        )

    init_db()

    app = (
        Application
        .builder()
        .token(BOT_TOKEN)
        .build()
    )

    # User commands
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
            "daily",
            daily
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

    # Owner commands
    app.add_handler(
        CommandHandler(
            "addcard",
            addcard
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
            "setedition",
            setedition
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
            "drop",
            drop
        )
    )

    # GET CARD button
    app.add_handler(
        CallbackQueryHandler(
            card_drop_button,
            pattern=r"^carddrop:\d+$"
        )
    )

    print(
        "🃏 CARD WORLD BOT IS RUNNING..."
    )

    app.run_polling()


if __name__ == "__main__":
    main()
