from telegram import InlineKeyboardButton, InlineKeyboardMarkup

TIER_NAMES = [
    "⚪ Common",           # 1
    "🟢 Uncommon",         # 2
    "🔵 Rare",             # 3
    "🟣 Epic",             # 4
    "🟡 Legendary",        # 5
    "🔴 Mythic",           # 6
    "🟠 Celestial",        # 7
    "🌸 Divine",           # 8
    "💎 Radiant",          # 9
    "⚡ Supreme",          # 10
    "🌟 Immortal",         # 11
    "👑 Exclusive",        # 12
    "✨ Premium Edition"   # 13
]

def get_start_keyboard():
    keyboard = [
        [
            InlineKeyboardButton("🔮 အကူအညီ (Help)", callback_data="help_p1"),
            InlineKeyboardButton("🛒 ဈေးကွက် (Market)", callback_data="market_main")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_help_keyboard():
    keyboard = [
        [
            InlineKeyboardButton("◀️ ရှေ့သို့", callback_data="help_p1"),
            InlineKeyboardButton("နောက်သို့ ▶️", callback_data="help_p2")
        ],
        [
            InlineKeyboardButton("🏠 ပင်မသို့", callback_data="help_home")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_harem_pagination_keyboard(page, total_pages):
    row = []
    if page > 1:
        row.append(InlineKeyboardButton("◀️ နောက်သို့", callback_data=f"harem_page_{page-1}"))
    if page < total_pages:
        row.append(InlineKeyboardButton("ရှေ့သို့ ▶️", callback_data=f"harem_page_{page+1}"))
    
    keyboard = [row, [InlineKeyboardButton("📂 ကဒ်အားလုံးကြည့်ရန်", callback_data="all_cards_list")]]
    return InlineKeyboardMarkup(keyboard)

def get_market_keyboard():
    keyboard = [
        [InlineKeyboardButton("🛒 ဈေးကွက်စာရင်းကြည့်ရန်", callback_data="market_list_view")],
        [InlineKeyboardButton("🔄 Refresh", callback_data="market_refresh")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_hmode_keyboard():
    keyboard = []
    row = []
    for i, name in enumerate(TIER_NAMES, 1):
        row.append(InlineKeyboardButton(f"✨ T{i}: {name}", callback_data=f"hmode_{i}"))
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    keyboard.append([InlineKeyboardButton("🔄 Reset Filter", callback_data="hmode_reset")])
    return InlineKeyboardMarkup(keyboard)
