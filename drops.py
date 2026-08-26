from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)


def drop_keyboard(drop_id: int):

    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "🎴  GET CARD  🎴",
                callback_data=f"carddrop:{drop_id}"
            )
        ]
    ])


def build_drop_text(card):

    (
        card_id,
        name,
        edition,
        price,
        drop_rate,
        description,
        media_type,
        file_id,
        limited
    ) = card

    limited_text = ""

    if limited:
        limited_text = "🔥 *LIMITED CARD*\n\n"

    description_text = ""

    if description:
        description_text = (
            f"📝 {description}\n\n"
        )

    return (
        "╭━━━━━━━━━━━━━━━━━━━━╮\n"
        "          🎴 *CARD DROP* 🎴\n"
        "╰━━━━━━━━━━━━━━━━━━━━╯\n\n"

        f"{limited_text}"

        f"🃏 *{name}*\n"
        f"💎 Edition: *{edition}*\n"
        f"💰 Value: *{price:,} 🪙*\n\n"

        f"{description_text}"

        "⚡ *FIRST CLICK WINS!*\n"
        "🔥 အရင်ဆုံး Button နှိပ်တဲ့သူက\n"
        "ဒီ Card ကို ရရှိမှာပါ!\n\n"

        "╰━━━━━━━━━━━━━━━━━━━━╯"
    )


def build_winner_text(
    user,
    card
):

    (
        card_id,
        name,
        edition,
        price,
        drop_rate,
        description,
        media_type,
        file_id,
        limited
    ) = card

    username = user.mention_html()

    return (
        "🎉━━━━━━━━━━━━━━━━━━🎉\n"
        "        🏆 *CARD CLAIMED!*\n"
        "🎉━━━━━━━━━━━━━━━━━━🎉\n\n"

        f"👑 Winner: {username}\n\n"

        f"🎴 Card: <b>{name}</b>\n"
        f"💎 Edition: <b>{edition}</b>\n"
        f"💰 Value: <b>{price:,} 🪙</b>\n\n"

        "📚 Collection ထဲ ထည့်ပြီးပါပြီ!\n"
        "⭐ +10 XP\n\n"

        "🔥 Congratulations, Collector!\n\n"

        "🎉━━━━━━━━━━━━━━━━━━🎉"
    )
