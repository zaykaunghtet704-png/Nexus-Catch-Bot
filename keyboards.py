from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from config import GROUP_LINK, CHANNEL_LINK, OWNER_USERNAME

def get_start_kb(lang='my'):
    kb = [
        [InlineKeyboardButton("🛒 Market", callback_data="market_view"), InlineKeyboardButton("🎒 Harem", callback_data="harem_view")],
        [InlineKeyboardButton("👥 Group Link", url=GROUP_LINK), InlineKeyboardButton("📢 Channel Link", url=CHANNEL_LINK)],
        [InlineKeyboardButton("🌐 Language / ဘာသာစကား", callback_data="toggle_lang")],
        [InlineKeyboardButton("👑 Owner Contact", url=f"https://t.me/{OWNER_USERNAME}")]
    ]
    return InlineKeyboardMarkup(kb)

def get_force_join_kb():
    kb = [
        [InlineKeyboardButton("🔗 Join Group", url=GROUP_LINK)],
        [InlineKeyboardButton("🔗 Join Channel", url=CHANNEL_LINK)],
        [InlineKeyboardButton("✅ Check Joined / စစ်ဆေးမည်", callback_data="verify_join")]
    ]
    return InlineKeyboardMarkup(kb)

def get_owner_link_kb():
    return InlineKeyboardMarkup([[InlineKeyboardButton("👑 Contact Owner", url=f"https://t.me/{OWNER_USERNAME}")]])
