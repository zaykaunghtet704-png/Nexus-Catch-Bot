import random

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)

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
    get_random_card,
    get_card,
    create_drop,
    claim_drop,
    get_collection,
    daily_reward,
)


def owner_only(user_id):
    return user_id == OWNER_ID


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    create_user(
        user.id,
        user.username
    )

    text = (
        "✨━━━━━━━━━━━━━━━━━━✨\n"
        "       🃏 *CARD WORLD* 🃏\n"
        "✨━━━━━━━━━━━━━━━━━━✨\n\n"

        "🎴 Welcome to the Card World!\n\n"

        "🔥 Collect rare cards\n"
        "💎 Discover special editions\n"
        "🏆 Build your collection\n\n"

        "📌 *Commands*\n"
        "🎴 /draw — Draw a card\n"
        "📚 /collection — Your cards\n"
        "👤 /profile — Your profile\n"
        "🎁 /daily — Daily reward\n\n"

        "✨ Good luck, Collector! ✨"
    )

    await update.message.reply_text(
        text,
        parse_mode="Markdown"
    )


async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    create_user(
        user.id,
        user.username
    )

    data = get_user(user.id)

    if not data:
        return

    user_id, username, coins, xp, level = data

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


async def daily(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    create_user(
        user.id,
        user.username
    )

    if not daily_reward(user.id):
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
        "🔥 See you tomorrow, Collector!",
        parse_mode="Markdown"
    )


async def collection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    create_user(
        user.id,
        user.username
    )

    cards = get_collection(user.id)

    if not cards:
        await update.message.reply_text(
            "📚 *YOUR COLLECTION*\n\n"
            "🗃️ Collection အလွတ်ဖြစ်နေပါတယ်။\n\n"
            "🎴 /draw ကိုနှိပ်ပြီး Card စုလိုက်ပါ!",
            parse_mode="Markdown"
        )
        return

    lines = [
        "📚 *YOUR COLLECTION*",
        "━━━━━━━━━━━━━━━━━━",
        ""
    ]

    for name, edition, price, amount in cards:
        lines.append(
            f"🎴 *{name}*\n"
            f"💎 {edition}\n"
            f"💰 {price:,} 🪙\n"
            f"📦 ×{amount}\n"
        )

    await update.message.reply_text(
        "\n".join(lines),
        parse_mode="Markdown"
    )


async def draw(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    create_user(
        user.id,
        user.username
    )

    card = get_random_card()

    if not card:
        await update.message.reply_text(
            "⚠️ Card Database ထဲမှာ Card မရှိသေးပါ။"
        )
        return

    card_id, name, edition, price, image_type, file_id = card

    from database import add_card

    add_card(
        user.id,
        card_id
    )

    text = (
        "🎴✨ *CARD DRAW!* ✨🎴\n\n"
        f"🃏 *{name}*\n"
        f"💎 Edition: *{edition}*\n"
        f"💰 Value: *{price:,} 🪙*\n\n"
        "📚 Collection ထဲ ထည့်ပြီးပါပြီ!"
    )

    if image_type == "photo" and file_id:
        await update.message.reply_photo(
            photo=file_id,
            caption=text,
            parse_mode="Markdown"
        )

    elif image_type == "video" and file_id:
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


async def drop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    if not owner_only(user.id):
        await update.message.reply_text(
            "⛔ ဒီ Command ကို Owner ပဲ အသုံးပြုနိုင်ပါတယ်။"
        )
        return

    card = get_random_card()

    if not card:
        await update.message.reply_text(
            "⚠️ Drop လုပ်ဖို့ Card မရှိသေးပါ။"
        )
        return

    card_id, name, edition, price, image_type, file_id = card

    drop_id = create_drop(card_id)

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "🎴  GET CARD  🎴",
                callback_data=f"drop:{drop_id}"
            )
        ]
    ])

    text = (
        "✨━━━━━━━━━━━━━━━━━━✨\n"
        "       🎴 *CARD DROP!* 🎴\n"
        "✨━━━━━━━━━━━━━━━━━━✨\n\n"

        f"🃏 *{name}*\n"
        f"💎 *{edition}*\n"
        f"💰 Value: *{price:,} 🪙*\n\n"

        "🔥 *FIRST CLICK WINS!*\n"
        "⚡ Button ကို အရင်နှိပ်တဲ့သူက\n"
        "ဒီ Card ကို ရရှိမှာပါ!\n\n"

        "✨━━━━━━━━━━━━━━━━━━✨"
    )

    if image_type == "photo" and file_id:
        await update.message.reply_photo(
            photo=file_id,
            caption=text,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )

    elif image_type == "video" and file_id:
        await update.message.reply_video(
            video=file_id,
            caption=text,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )

    else:
        await update.message.reply_text(
            text,
            reply_markup=keyboard,
            parse_mode="Markdown"
        )


async def drop_button(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    query = update.callback_query

    await query.answer()

    user = query.from_user

    create_user(
        user.id,
        user.username
    )

    drop_id = int(
        query.data.split(":")[1]
    )

    success = claim_drop(
        drop_id,
        user.id
    )

    if not success:
        await query.answer(
            "❌ Too late! ဒီ Card ကို တစ်ယောက်က ယူပြီးပါပြီ!",
            show_alert=True
        )
        return

    card_id = __import__(
        "database"
    ).get_drop_card_id(drop_id)

    card = get_card(card_id)

    if not card:
        return

    _, name, edition, price, _, _ = card

    await query.answer(
        "🎉 Card ရပါပြီ!",
        show_alert=True
    )

    await query.message.reply_text(
        "🎉✨ *CARD CLAIMED!* ✨🎉\n\n"
        f"👑 Winner: {user.mention_markdown_v2()}\n"
        f"🎴 Card: *{name}*\n"
        f"💎 Edition: *{edition}*\n"
        f"💰 Value: *{price:,} 🪙*\n\n"
        "📚 Collection ထဲ ထည့်ပြီးပါပြီ!\n"
        "🔥 Congratulations, Collector!",
        parse_mode="Markdown"
    )


def main():
    if not BOT_TOKEN:
        raise RuntimeError(
            "BOT_TOKEN မတွေ့ပါ။ .env ကို စစ်ပါ။"
        )

    init_db()

    app = (
        Application
        .builder()
        .token(BOT_TOKEN)
        .build()
    )

    app.add_handler(
        CommandHandler("start", start)
    )

    app.add_handler(
        CommandHandler("profile", profile)
    )

    app.add_handler(
        CommandHandler("collection", collection)
    )

    app.add_handler(
        CommandHandler("daily", daily)
    )

    app.add_handler(
        CommandHandler("draw", draw)
    )

    app.add_handler(
        CommandHandler("drop", drop)
    )

    app.add_handler(
        CallbackQueryHandler(
            drop_button,
            pattern=r"^drop:\d+$"
        )
    )

    print("🃏 CARD BOT IS RUNNING...")

    app.run_polling()


if __name__ == "__main__":
    main()
