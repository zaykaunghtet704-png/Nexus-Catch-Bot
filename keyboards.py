from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from config import REQUIRED_GROUP_LINK, REQUIRED_CHANNEL_LINK, WAIFU_LINK

TIER_NAMES = [
    "Common", "Uncommon", "Rare", "Epic", "Legendary", 
    "Mythic", "Celestial", "Divine", "Immortal", "Supreme", 
    "Special Edition", "Limited Edition", "Premium Edition"
]

def get_start_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("👑 I'm Waifu ✨", url=WAIFU_LINK)],
        [
            InlineKeyboardButton("💬 Group 🚀", url=REQUIRED_GROUP_LINK),
            InlineKeyboardButton("📢 Channel 💎", url=REQUIRED_CHANNEL_LINK)
        ]
    ])

def get_join_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💬 Group Join မည် 🚀", url=REQUIRED_GROUP_LINK)],
        [InlineKeyboardButton("📢 Channel Join မည် 💎", url=REQUIRED_CHANNEL_LINK)]
    ])

def get_help_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📖 Page 1", callback_data="help_p1"),
            InlineKeyboardButton("📖 Page 2", callback_data="help_p2")
        ],
        [InlineKeyboardButton("🛡️ Admin Cmds", callback_data="help_admin")]
    ])

def get_hmode_keyboard():
    buttons = []
    row = []
    # ခလုတ်များ အလွန်အမင်း မရှည်စေရန် တစ်တန်းလျှင် ၃ ခုစီ စီစဉ်ထားပါသည်
    for j, tier_label in enumerate(TIER_NAMES):
        tier_num = j + 1
        row.append(InlineKeyboardButton(f"{tier_num}. {tier_label}", callback_data=f"hmode_{tier_num}"))
        if len(row) == 3:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    
    buttons.append([InlineKeyboardButton("🔄 Reset Filter", callback_data="hmode_reset")])
    return InlineKeyboardMarkup(buttons)
