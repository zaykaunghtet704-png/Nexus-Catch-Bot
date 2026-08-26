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


def drop_caption(card):
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

    return (
        "✨━━━━━━━━━━━━━━━━━━✨\n"
        "       🎴 *CARD DROP!* 🎴\n"
        "✨━━━━━━━━━━━━━━━━━━✨\n\n"

        f"🃏 *{name}*\n"
        f"💎 Edition: *{edition}*\n"
        f"💰 Value: *{price:,} 🪙*\n\n"

        "⚡ *FIRST CLICK WINS!*\n"
        "🔥 Button ကို အရင်နှိပ်တဲ့သူက\n"
        "ဒီ Card ကို ရရှိမှာပါ!\n\n"

        "✨━━━━━━━━━━━━━━━━━━✨"
    )
