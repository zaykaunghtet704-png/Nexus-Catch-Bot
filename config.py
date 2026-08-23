# config.py - Complete Configuration File

# Telegram Bot Token
BOT_TOKEN = "8823072889:AAHIYPMd3Qon8oRrsoi9EPdNhWlIlBFeeGU"

# ရှားပါးမှုအဆင့်များနှင့် ဈေးနှုန်း/တန်ဖိုးများ
RARITIES = {
    "Common": {"emoji": "⚪", "value": 25},
    "Uncommon": {"emoji": "🔹", "value": 50},
    "Rare": {"emoji": "💎", "value": 100},
    "Legendary": {"emoji": "👑", "value": 250},
    "Mystical": {"emoji": "🔮", "value": 500},
    "Divine": {"emoji": "✨", "value": 1000},
    "CrossVerse": {"emoji": "🌌", "value": 2000},
    "Cataphract": {"emoji": "🛡️", "value": 5500},
    "Supreme": {"emoji": "🔥", "value": 8500},
    "Limited Edition": {"emoji": "🌟", "value": 10000},
    "Premium Edition": {"emoji": "✨👑", "value": 15000}
}

# Error မတက်စေရန် RARITY_TIERS ကို RARITIES နှင့် ချိတ်ဆက်ပေးခြင်း
RARITY_TIERS = RARITIES

# Force Join လုပ်ရမည့် ချန်နယ်နှင့် ဂရုလင့်ခ်များ
FORCE_JOIN_CHANNELS = [
    {"name": "Channel", "link": "https://t.me/+E6BxfAj0gaI2Y2Zl"},
    {"name": "Group", "link": "https://t.me/+00J7JktW8bJlZTY1"}
]

# ဘော့ပိုင်ရှင် (Owner) ၏ Telegram User IDs များ
OWNER_IDS = [7974865879]
