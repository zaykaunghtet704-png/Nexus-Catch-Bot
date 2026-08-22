from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from config import GROUP_LINK, CHANNEL_LINK, OWNER_USERNAME

def get_start_keyboard():
    keyboard = [
        [InlineKeyboardButton("💎 Market", callback_data="market"), InlineKeyboardButton("🎒 Harem", callback_data="harem")],
        [InlineKeyboardButton("👥 Group", url=GROUP_LINK), InlineKeyboardButton("📢 Channel", url=CHANNEL_LINK)],
        [InlineKeyboardButton("👑 Contact Owner", url=f"https://t.me/{OWNER_USERNAME}")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_force_join_keyboard():
    keyboard = [
        [InlineKeyboardButton("🔗 Join Group", url=GROUP_LINK)],
        [InlineKeyboardButton("🔗 Join Channel", url=CHANNEL_LINK)],
        [InlineKeyboardButton("✅ Checked", callback_data="check_join")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_owner_approval_keyboard():
    keyboard = [
        [InlineKeyboardButton("👑 Contact Owner for Approval", url=f"https://t.me/{OWNER_USERNAME}")]
    ]
    return InlineKeyboardMarkup(keyboard)
