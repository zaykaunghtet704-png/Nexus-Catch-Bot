import os

BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
OWNER_ID = 7974865879
OWNER_USERNAME = "May_Be_786"

GROUP_LINK = "https://t.me/+00J7JktW8bJlZTY1"
CHANNEL_LINK = "https://t.me/+E6BxfAj0gaI2Y2Zl"

# 13 Rarity Levels with Percentage Rates & Max Price (15,000)
RARITY_LEVELS = {
    1: {"name": "Common ⚪", "rate": 35.0, "max_price": 500},
    2: {"name": "Uncommon 🟢", "rate": 20.0, "max_price": 1200},
    3: {"name": "Rare 🔵", "rate": 15.0, "max_price": 2500},
    4: {"name": "Super Rare 🔷", "rate": 10.0, "max_price": 4000},
    5: {"name": "Epic 🟣", "rate": 8.0, "max_price": 6000},
    6: {"name": "Mega Epic 🔮", "rate": 5.0, "max_price": 8000},
    7: {"name": "Legendary ⭐", "rate": 3.0, "max_price": 10000},
    8: {"name": "Mythic 🌟", "rate": 2.0, "max_price": 11500},
    9: {"name": "Divine 💫", "rate": 1.0, "max_price": 12500},
    10: {"name": "Immortal 🔥", "rate": 0.5, "max_price": 13500},
    11: {"name": "Celestial ✨", "rate": 0.3, "max_price": 14200},
    12: {"name": "Supreme 👑", "rate": 0.15, "max_price": 14700},
    13: {"name": "Premium Edition 💎", "rate": 0.05, "max_price": 15000},
}
RARITIES = RARITY_LEVELS
