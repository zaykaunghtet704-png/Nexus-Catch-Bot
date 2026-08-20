import os

# Telegram Bot Credentials
BOT_TOKEN = os.getenv("BOT_TOKEN", "8823072889:AAHKIzIzYVm4CjRJzoJWCktJhI5ZYn4mn4Y")

# Multiple Owner IDs Support
OWNER_IDS = [7869852655, 7974865879]

# Encryption Key
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY", "32_BYTE_SECRET_KEY_FOR_AES_256!")

# Links
LINK_WAIFU = "https://t.me/example_waifu"
LINK_GROUP = "https://t.me/+00J7JktW8bJlZTY1"
LINK_CHANNEL = "https://t.me/+E6BxfAj0gaI2Y2Zl"

# 13 Rarity Tiers
RARITY_TIERS = {
    "1": {"name": "Common", "rate": 0.35},
    "2": {"name": "Uncommon", "rate": 0.20},
    "3": {"name": "Rare", "rate": 0.12},
    "4": {"name": "Super Rare", "rate": 0.08},
    "5": {"name": "Ultra Rare", "rate": 0.06},
    "6": {"name": "Epic", "rate": 0.05},
    "7": {"name": "Legendary", "rate": 0.04},
    "8": {"name": "Mythic", "rate": 0.03},
    "9": {"name": "Celestial", "rate": 0.02},
    "10": {"name": "Supreme", "rate": 0.015},
    "11": {"name": "Exalted", "rate": 0.010},
    "12": {"name": "Divine", "rate": 0.004},
    "13": {"name": "Premium Edition", "rate": 0.001}
}
