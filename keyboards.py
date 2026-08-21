from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from config import LINK_WAIFU, LINK_GROUP, LINK_CHANNEL

def get_start_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💖 My Waifu", url=LINK_WAIFU)],
        [InlineKeyboardButton("🌐 Official Group", url=LINK_GROUP), InlineKeyboardButton("📢 Channel", url=LINK_CHANNEL)]
    ])

def get_trade_keyboard(trade_id: str):
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Confirm Trade", callback_data=f"tr_conf_{trade_id}"),
            InlineKeyboardButton("❌ Cancel", callback_data=f"tr_canc_{trade_id}")
        ]
    ])
