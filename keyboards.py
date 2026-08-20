from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from config import LINK_WAIFU, LINK_GROUP, LINK_CHANNEL, RARITY_TIERS

def get_start_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💖 User Waifu", url=LINK_WAIFU)],
        [InlineKeyboardButton("🌐 Group Link", url=LINK_GROUP), InlineKeyboardButton("📢 Update Channel", url=LINK_CHANNEL)]
    ])

def get_hmode_keyboard():
    keyboard = []
    row = []
    for k, v in RARITY_TIERS.items():
        row.append(InlineKeyboardButton(f"{v['name']}", callback_data=f"hmode_{k}"))
        if len(row) == 3:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    keyboard.append([InlineKeyboardButton("🔄 Show ALL (Reset)", callback_data="hmode_ALL")])
    return InlineKeyboardMarkup(keyboard)
