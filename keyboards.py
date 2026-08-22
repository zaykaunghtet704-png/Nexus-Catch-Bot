from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from config import GROUP_LINK, CHANNEL_LINK, OWNER_USERNAME

def get_start_keyboard(lang="my"):
    if lang == "my":
        keyboard = [
            [InlineKeyboardButton("💎 ဝယ်ယူရန်/မားကတ်", callback_data="market"), InlineKeyboardButton("🎒 ဟာရမ် (Harem)", callback_data="harem")],
            [InlineKeyboardButton("👥 ပင်မအုပ်စု", url=GROUP_LINK), InlineKeyboardButton("📢 ချန်နယ်", url=CHANNEL_LINK)],
            [InlineKeyboardButton("👑 အုံနာကို ဆက်သွယ်ရန်", url=f"https://t.me/{OWNER_USERNAME}")]
        ]
    else:
        keyboard = [
            [InlineKeyboardButton("💎 Market", callback_data="market"), InlineKeyboardButton("🎒 Harem", callback_data="harem")],
            [InlineKeyboardButton("👥 Main Group", url=GROUP_LINK), InlineKeyboardButton("📢 Channel", url=CHANNEL_LINK)],
            [InlineKeyboardButton("👑 Contact Owner", url=f"https://t.me/{OWNER_USERNAME}")]
        ]
    return InlineKeyboardMarkup(keyboard)

def get_force_join_keyboard():
    keyboard = [
        [InlineKeyboardButton("🔗 Join Group ဝင်ရန်", url=GROUP_LINK)],
        [InlineKeyboardButton("🔗 Join Channel ဝင်ရန်", url=CHANNEL_LINK)],
        [InlineKeyboardButton("✅ ဂျွိုင်းပြီးပါပြီ (Check)", callback_data="check_join")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_owner_approval_keyboard():
    keyboard = [
        [InlineKeyboardButton("👑 အုံနာထံ ခွင့်တောင်းရန် (Contact Owner)", url=f"https://t.me/{OWNER_USERNAME}")]
    ]
    return InlineKeyboardMarkup(keyboard)
