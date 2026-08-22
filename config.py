import os

BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
OWNER_ID = 7974865879
OWNER_USERNAME = "May_Be_786"

GROUP_LINK = "https://t.me/+00J7JktW8bJlZTY1"
CHANNEL_LINK = "https://t.me/+E6BxfAj0gaI2Y2Zl"

# 13 Rarity Levels & Max Prices (Common to Premium Edition)
RARITY_LEVELS = [
    {"level": 1, "name": "Common ⚪", "rate": 35.0, "max_price": 500},
    {"level": 2, "name": "Uncommon 🟢", "rate": 20.0, "max_price": 1200},
    {"level": 3, "name": "Rare 🔵", "rate": 15.0, "max_price": 2500},
    {"level": 4, "name": "Super Rare 🔷", "rate": 10.0, "max_price": 4000},
    {"level": 5, "name": "Epic 🟣", "rate": 8.0, "max_price": 6000},
    {"level": 6, "name": "Mega Epic 🔮", "rate": 5.0, "max_price": 8000},
    {"level": 7, "name": "Legendary ⭐", "rate": 3.0, "max_price": 10000},
    {"level": 8, "name": "Mythic 🌟", "rate": 2.0, "max_price": 11500},
    {"level": 9, "name": "Divine 💫", "rate": 1.0, "max_price": 12500},
    {"level": 10, "name": "Immortal 🔥", "rate": 0.5, "max_price": 13500},
    {"level": 11, "name": "Celestial ✨", "rate": 0.3, "max_price": 14200},
    {"level": 12, "name": "Supreme 👑", "rate": 0.15, "max_price": 14700},
    {"level": 13, "name": "Premium Edition 💎", "rate": 0.05, "max_price": 15000},
]
