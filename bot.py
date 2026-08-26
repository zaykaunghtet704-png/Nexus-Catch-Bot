import random

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
)

from config import BOT_TOKEN, ADMIN_IDS
from database import (
    init_db,
    create_user,
    get_user,
    add_card_to_user,
    get_collection,
    claim_daily,
    connect,
)


RARITY_WEIGHT = {
    "Common": 60,
    "Rare": 25,
    "Epic": 10,
    "Legendary": 5,
}


def choose_rarity():
    rarities = list(RARITY_WEIGHT.keys())
    weights = list(RARITY_WEIGHT.values())

    return random.choices(
        rarities,
        weights=weights,
        k=1
    )[0]


def get_random_card(rarity):
    db = connect()
    cur = db.cursor()

    cur.execute(
        """
        SELECT id, name, rarity, image_url
        FROM cards
        WHERE rarity = ?
        """,
        (rarity,)
    )

    cards = cur.fetchall()
    db.close()

    if not cards:
        return None

    return random.choice(cards)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    create_user(user.id, user.username)

    text = (
        "🃏 *Card Bot မှ ကြိုဆိုပါတယ်!*\n\n"
        "🎴 Card စုဆောင်းနိုင်ပါတယ်။\n"
        "🎁 Daily reward ရယူနိုင်ပါတယ်။\n\n"
        "အသုံးပြုနိုင်တဲ့ Commands:\n"
        "🎴 /draw - Card ဆွဲရန်\n"
        "📚 /collection - Card Collection\n"
        "👤 /profile - Profile\n"
        "🎁 /daily - Daily Reward\n"
        "ℹ️ /help - Help"
    )

    await update.message.reply_text(
        text,
        parse_mode="Markdown"
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "🃏 *Card Bot Help*\n\n"
        "/start - Bot စတင်ရန်\n"
        "/draw - Card ဆွဲရန်\n"
        "/collection - Collection ကြည့်ရန်\n"
        "/profile - Profile ကြည့်ရန်\n"
        "/daily - Daily Reward\n"
        "/help - Help"
    )

    await update.message.reply_text(
        text,
        parse_mode="Markdown"
    )


async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    create_user(user.id, user.username)

    data = get_user(user.id)

    if not data:
        return

    _, username, coins, xp, level, last_daily = data

    text = (
        "👤 *Profile*\n\n"
        f"🆔 ID: `{user.id}`\n"
        f"👤 Name: {username or user.first_name}\n"
        f"💰 Coins: {coins}\n"
        f"⭐ XP: {xp}\n"
        f"🏆 Level: {level}"
    )

    await update.message.reply_text(
        text,
        parse_mode="Markdown"
    )


async def daily(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    create_user(user.id, user.username)

    success = claim_daily(user.id)

    if not success:
        await update.message.reply_text(
            "⏳ ဒီနေ့ Daily Reward ယူပြီးပါပြီ။"
        )
        return

    await update.message.reply_text(
        "🎁 Daily Reward ရပါပြီ!\n\n"
        "💰 +100 Coins\n"
        "⭐ +20 XP"
    )


async def draw(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    create_user(user.id, user.username)

    rarity = choose_rarity()
    card = get_random_card(rarity)

    if not card:
        await update.message.reply_text(
            "❌ ဒီ Rarity အတွက် Card မရှိသေးပါ။"
        )
        return

    card_id, name, card_rarity, image_url = card

    add_card_to_user(user.id, card_id)

    text = (
        "🎴 *NEW CARD!*\n\n"
        f"🃏 {name}\n"
        f"💎 Rarity: *{card_rarity}*\n\n"
        "📚 Collection ထဲ ထည့်ပြီးပါပြီ!"
    )

    if image_url:
        await update.message.reply_photo(
            photo=image_url,
            caption=text,
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text(
            text,
            parse_mode="Markdown"
        )


async def collection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    create_user(user.id, user.username)

    cards = get_collection(user.id)

    if not cards:
        await update.message.reply_text(
            "📚 Collection က အလွတ်ပါ။\n"
            "🎴 /draw နဲ့ Card စဆွဲပါ။"
        )
        return

    lines = ["📚 *Your Collection*\n"]

    for name, rarity, amount in cards:
        lines.append(
            f"🃏 {name} — {rarity} ×{amount}"
        )

    await update.message.reply_text(
        "\n".join(lines),
        parse_mode="Markdown"
    )


def main():
    if not BOT_TOKEN:
        raise RuntimeError(
            "BOT_TOKEN မတွေ့ပါ။ .env ဖိုင်ကို စစ်ပါ။"
        )

    init_db()

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("profile", profile))
    app.add_handler(CommandHandler("daily", daily))
    app.add_handler(CommandHandler("draw", draw))
    app.add_handler(CommandHandler("collection", collection))

    print("🃏 Card Bot is running...")

    app.run_polling()


if __name__ == "__main__":
    main()
