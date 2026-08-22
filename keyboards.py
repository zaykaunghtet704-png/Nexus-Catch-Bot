from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from config import CHANNEL_LINK, GROUP_LINK, OWNER_USERNAME

TIER_NAMES = [
    "⚪ Common", "🟢 Uncommon", "🔵 Rare", "🟣 Epic", "🟡 Legendary", 
    "🔴 Mythic", "🟠 Celestial", "🌸 Divine", "💎 Radiant", "⚡ Supreme", 
    "🌟 Immortal", "👑 Exclusive", "✨ Premium Edition"
]

def get_start_keyboard(lang="my"):
    if lang == "en":
        kb = [
            [InlineKeyboardButton("🔮 Help", callback_data="help_p1"), InlineKeyboardButton("🛒 Market", callback_data="market_main")],
            [InlineKeyboardButton("🎴 Harem", callback_data="harem_home"), InlineKeyboardButton("🔍 Search", callback_data="search_all")],
            [InlineKeyboardButton("📢 Channel", url=CHANNEL_LINK), InlineKeyboardButton("👥 Group", url=GROUP_LINK)],
            [InlineKeyboardButton("🌐 Change Language (မြန်မာ)", callback_data="lang_my")]
        ]
    else:
        kb = [
            [InlineKeyboardButton("🔮 အကူအညီ (Help)", callback_data="help_p1"), InlineKeyboardButton("🛒 ဈေးကွက် (Market)", callback_data="market_main")],
            [InlineKeyboardButton("🎴 ကိုယ်ပိုင်ကဒ်များ (Harem)", callback_data="harem_home"), InlineKeyboardButton("🔍 ကဒ်ရှာရန် (Search)", callback_data="search_all")],
            [InlineKeyboardButton("📢 Channel Join", url=CHANNEL_LINK), InlineKeyboardButton("👥 Group Join", url=GROUP_LINK)],
            [InlineKeyboardButton("🌐 Change Language (English)", callback_data="lang_en")]
        ]
    return InlineKeyboardMarkup(kb)

def get_harem_pagination_keyboard(page, total_pages):
    row = []
    if page > 1:
        row.append(InlineKeyboardButton("◀️ Prev", callback_data=f"harem_page_{page-1}"))
    if page < total_pages:
        row.append(InlineKeyboardButton("Next ▶️", callback_data=f"harem_page_{page+1}"))
    
    keyboard = [
        row, 
        [InlineKeyboardButton("📂 ပုံအားလုံးနှင့် ကဒ်စာရင်းကြည့်ရန် (All Cards)", callback_data="all_cards_list")],
        [InlineKeyboardButton("🏠 ပင်မသို့ (Home)", callback_data="help_home")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_market_keyboard():
    keyboard = [
        [InlineKeyboardButton("🛒 ဈေးကွက်စာရင်းကြည့်ရန်", callback_data="market_list_view")],
        [InlineKeyboardButton("🔄 Refresh", callback_data="market_refresh")],
        [InlineKeyboardButton("🏠 ပင်မသို့", callback_data="help_home")]
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
    keyboard.append([InlineKeyboardButton("🏠 ပင်မသို့", callback_data="help_home")])
    return InlineKeyboardMarkup(keyboard)
