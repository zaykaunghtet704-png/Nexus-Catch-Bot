import os

BOT_TOKEN = os.getenv("BOT_TOKEN", "8823072889:AAHKIzIzYVm4CjRJzoJWCktJhI5ZYn4mn4Y")
OWNER_IDS = [7869852655, 7974865879]
LOG_CHANNEL_ID = os.getenv("LOG_CHANNEL_ID", "-1001234567890")

DB_FILE = "bot_database.json"

LINK_WAIFU = "https://t.me/example_waifu"
LINK_GROUP = "https://t.me/+00J7JktW8bJlZTY1"
LINK_CHANNEL = "https://t.me/+E6BxfAj0gaI2Y2Zl"

RARITY_STAGES = {
    1: {"name": "⚪ Common", "price": 500},
    2: {"name": "🟢 Uncommon", "price": 1000},
    3: {"name": "🔵 Rare", "price": 2000},
    4: {"name": "🟣 Super Rare", "price": 3500},
    5: {"name": "🟡 Ultra Rare", "price": 5000},
    6: {"name": "🟠 Epic", "price": 7000},
    7: {"name": "🔴 Legendary", "price": 9000},
    8: {"name": "💖 Mythic", "price": 11000},
    9: {"name": "🌌 Celestial", "price": 13000},
    10: {"name": "👑 Supreme", "price": 14000},
    11: {"name": "✨ Exalted", "price": 14500},
    12: {"name": "⚡ Divine", "price": 14800},
    13: {"name": "💎 Premium Edition", "price": 15000}
}
