from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from config import REQUIRED_GROUP_LINK, REQUIRED_CHANNEL_LINK, WAIFU_LINK

def get_start_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("👸 I'm Waifu", url=WAIFU_LINK)],
        [
            InlineKeyboardButton("👥 Group", url=REQUIRED_GROUP_LINK),
            InlineKeyboardButton("📢 Channel", url=REQUIRED_CHANNEL_LINK)
        ]
    ])

def get_join_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💬 Group Join မည်", url=REQUIRED_GROUP_LINK)],
        [InlineKeyboardButton("📢 Channel Join မည်", url=REQUIRED_CHANNEL_LINK)]
    ])

def get_help_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📖 Page 1", callback_data="help_p1"),
            InlineKeyboardButton("📖 Page 2", callback_data="help_p2")
        ],
        [InlineKeyboardButton("👑 Admin Cmds", callback_data="help_admin")]
    ])

def get_hmode_keyboard():
    buttons = []
    for i in range(1, 11, 2):
        row = [InlineKeyboardButton(f"Tier {j}", callback_data=f"hmode_{j}") for j in range(i, min(i+2, 11))]
        buttons.append(row)
    buttons.append([InlineKeyboardButton("🔄 Reset Filter", callback_data="hmode_reset")])
    return InlineKeyboardMarkup(buttons)
