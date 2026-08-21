from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from config import LINK_WAIFU, LINK_GROUP, LINK_CHANNEL, RARITY_TIERS

def get_start_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💖 My Waifu", url=LINK_WAIFU)],
        [InlineKeyboardButton("🌐 Group Link", url=LINK_GROUP), InlineKeyboardButton("📢 Update Channel", url=LINK_CHANNEL)]
    ])

def get_force_join_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🌐 Join Group", url=LINK_GROUP)],
        [InlineKeyboardButton("📢 Join Channel", url=LINK_CHANNEL)],
        [InlineKeyboardButton("✅ Verify / Check Again", callback_data="check_force_join")]
    ])

def get_hmode_keyboard():
    keyboard = []
    row = []
    for k, v in RARITY_TIERS.items():
        row.append(InlineKeyboardButton(f"{v['name']}", callback_data=f"hmode_{k}"))
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    keyboard.append([InlineKeyboardButton("🔄 Show ALL (Reset)", callback_data="hmode_ALL")])
    return InlineKeyboardMarkup(keyboard)

def get_page_keyboard(prefix: str, current_page: int, total_pages: int):
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("⬅️ Prev", callback_data=f"{prefix}_page_{current_page - 1}"),
        InlineKeyboardButton(f"📄 {current_page}/{total_pages}", callback_data="noop"),
        InlineKeyboardButton("Next ➡️", callback_data=f"{prefix}_page_{current_page + 1}")
    ]])
