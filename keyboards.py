from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from config import GROUP_LINK, CHANNEL_LINK, OWNER_USERNAME

def get_start_kb():
    kb = [
        [InlineKeyboardButton("🛒 Market", callback_data="market"), InlineKeyboardButton("🎒 Harem", callback_data="harem")],
        [InlineKeyboardButton("👥 Group Link", url=GROUP_LINK), InlineKeyboardButton("📢 Channel Link", url=CHANNEL_LINK)],
        [InlineKeyboardButton("👑 Owner Contact", url=f"https://t.me/{OWNER_USERNAME}")]
    ]
    return InlineKeyboardMarkup(kb)

def get_force_join_kb():
    kb = [
        [InlineKeyboardButton("🔗 Join Group", url=GROUP_LINK)],
        [InlineKeyboardButton("🔗 Join Channel", url=CHANNEL_LINK)],
        [InlineKeyboardButton("✅ Joined / ဝင်ပြီးပါပြီ", callback_data="check_join")]
    ]
    return InlineKeyboardMarkup(kb)

def get_owner_link_kb():
    return InlineKeyboardMarkup([[InlineKeyboardButton("👑 Contact Owner", url=f"https://t.me/{OWNER_USERNAME}")]])
