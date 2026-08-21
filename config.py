import os

BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
OWNER_ID = int(os.getenv("OWNER_ID", "123456789"))
LOG_CHANNEL_ID = int(os.getenv("LOG_CHANNEL_ID", "-1001234567890"))

REQUIRED_GROUP_LINK = "https://t.me/+00J7JktW8bJlZTY1"
REQUIRED_CHANNEL_LINK = "https://t.me/+E6BxfAj0gaI2Y2Zl"
REQUIRED_CHANNEL_ID = -1002233445566

RARITY_STAGES = {
    1: {"name": "Common", "chance": 35.0, "color": "#808080", "price": 1000},
    2: {"name": "Uncommon", "chance": 20.0, "color": "#00FF00", "price": 1500},
    3: {"name": "Rare", "chance": 12.0, "color": "#0000FF", "price": 2500},
    4: {"name": "Super Rare", "chance": 8.0, "color": "#4B0082", "price": 3500},
    5: {"name": "Ultra Rare", "chance": 6.0, "color": "#800080", "price": 5000},
    6: {"name": "Epic", "chance": 5.0, "color": "#FF00FF", "price": 6500},
    7: {"name": "Legendary", "chance": 4.0, "color": "#FFA500", "price": 8000},
    8: {"name": "Mythic", "chance": 3.0, "color": "#FF4500", "price": 9500},
    9: {"name": "Celestial", "chance": 2.0, "color": "#00FFFF", "price": 11000},
    10: {"name": "Supreme", "chance": 1.5, "color": "#DC143C", "price": 12500},
    11: {"name": "Exalted", "chance": 1.0, "color": "#FFD700", "price": 13500},
    12: {"name": "Divine", "chance": 0.4, "color": "#E6E6FA", "price": 14200},
    13: {"name": "Premium Edition", "chance": 0.1, "color": "#GOLD", "price": 15000},
}
