import os

# Credentials & Security
BOT_TOKEN = os.getenv("BOT_TOKEN", "8823072889:AAHKIzIzYVm4CjRJzoJWCktJhI5ZYn4mn4Y")
OWNER_IDS = [7869852655, 7974865879]
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY", "32_BYTE_SECRET_KEY_FOR_AES_256!")

# Bot Links
LINK_WAIFU = "https://t.me/example_waifu"
LINK_GROUP = "https://t.me/+00J7JktW8bJlZTY1"
LINK_CHANNEL = "https://t.me/+E6BxfAj0gaI2Y2Zl"

# Rarity 13 Tiers (Drop Chance & Hex Color Code for Dye Canvas)
RARITY_TIERS = {
    "1": {"name": "Common", "chance": 35.0, "color": "#808080"},
    "2": {"name": "Uncommon", "chance": 20.0, "color": "#00FF00"},
    "3": {"name": "Rare", "chance": 12.0, "color": "#0000FF"},
    "4": {"name": "Super Rare", "chance": 8.0, "color": "#4B0082"},
    "5": {"name": "Ultra Rare", "chance": 6.0, "color": "#800080"},
    "6": {"name": "Epic", "chance": 5.0, "color": "#FF00FF"},
    "7": {"name": "Legendary", "chance": 4.0, "color": "#FFA500"},
    "8": {"name": "Mythic", "chance": 3.0, "color": "#FF4500"},
    "9": {"name": "Celestial", "chance": 2.0, "color": "#00FFFF"},
    "10": {"name": "Supreme", "chance": 1.5, "color": "#DC143C"},
    "11": {"name": "Exalted", "chance": 1.0, "color": "#FFD700"},
    "12": {"name": "Divine", "chance": 0.4, "color": "#E6E6FA"},
    "13": {"name": "Premium Edition", "chance": 0.1, "color": "#RAINBOW"}
}
