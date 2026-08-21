from telegram.inlinekeyboardbuilder import InlineKeyboardBuilder

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
    builder = InlineKeyboardBuilder()
    builder.button(text="🔮 အကူအညီ (Help)", callback_data="help_p1")
    builder.button(text="🛒 ဈေးကွက် (Market)", callback_data="market_main")
    builder.adjust(2)
    return builder.as_markup()

def get_help_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="◀️ ရှေ့သို့", callback_data="help_p1")
    builder.button(text="နောက်သို့ ▶️", callback_data="help_p2")
    builder.button(text="🏠 ပင်မသို့", callback_data="help_home")
    builder.adjust(2, 1)
    return builder.as_markup()

def get_harem_pagination_keyboard(page, total_pages):
    builder = InlineKeyboardBuilder()
    if page > 1:
        builder.button(text="◀️ နောက်သို့", callback_data=f"harem_page_{page-1}")
    if page < total_pages:
        builder.button(text="ရှေ့သို့ ▶️", callback_data=f"harem_page_{page+1}")
    builder.button(text="📂 ကဒ်အားလုံးကြည့်ရန်", callback_data="all_cards_list")
    builder.adjust(2, 1)
    return builder.as_markup()

def get_market_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="🛒 ဈေးကွက်စာရင်းကြည့်ရန်", callback_data="market_list_view")
    builder.button(text="🔄 Refresh", callback_data="market_refresh")
    builder.adjust(1)
    return builder.as_markup()

def get_hmode_keyboard():
    builder = InlineKeyboardBuilder()
    for i, name in enumerate(TIER_NAMES, 1):
        builder.button(text=f"✨ T{i}: {name}", callback_data=f"hmode_{i}")
    builder.button(text="🔄 Reset Filter", callback_data="hmode_reset")
    builder.adjust(2, 2, 2, 2, 2, 2, 1, 1)
    return builder.as_markup()
