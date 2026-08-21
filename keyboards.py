from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from config import REQUIRED_GROUP_LINK, REQUIRED_CHANNEL_LINK, WAIFU_LINK

# Common မှ Premium Edition အထိ အဆင့် (၁၃) ဆင့် အမည်များ
TIER_NAMES = [
    "Common", "Uncommon", "Rare", "Epic", "Legendary", 
    "Mythic", "Celestial", "Divine", "Immortal", "Supreme", 
    "Special Edition", "Limited Edition", "Premium Edition"
]

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
    for i in range(0, len(TIER_NAMES), 2):
        row = []
        for j in range(i, min(i+2, len(TIER_NAMES))):
            tier_num = j + 1
            tier_label = TIER_NAMES[j]
            row.append(InlineKeyboardButton(f"{tier_num}. {tier_label}", callback_data=f"hmode_{tier_num}"))
        buttons.append(row)
    buttons.append([InlineKeyboardButton("🔄 Reset Filter", callback_data="hmode_reset")])
    return InlineKeyboardMarkup(buttons)
