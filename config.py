import os

BOT_TOKEN = os.getenv("BOT_TOKEN", "8823072889:AAHKIzIzYVm4CjRJzoJWCktJhI5ZYn4mn4Y")
OWNER_IDS = [7869852655, 7974865879]
LOG_CHANNEL_ID = os.getenv("LOG_CHANNEL_ID", "-1001234567890")

LINK_WAIFU = "https://t.me/example_waifu"
LINK_GROUP = "https://t.me/+00J7JktW8bJlZTY1"
LINK_CHANNEL = "https://t.me/+E6BxfAj0gaI2Y2Zl"

# Rarity 13 Stages Configuration
RARITY_STAGES = {
    1: {"name": "Common", "chance": 35.0, "price": 500, "color": "#808080"},
    2: {"name": "Uncommon", "chance": 20.0, "price": 1000, "color": "#00FF00"},
    3: {"name": "Rare", "chance": 12.0, "price": 2000, "color": "#0000FF"},
    4: {"name": "Super Rare", "chance": 8.0, "price": 3500, "color": "#4B0082"},
    5: {"name": "Ultra Rare", "chance": 6.0, "price": 5000, "color": "#800080"},
    6: {"name": "Epic", "chance": 5.0, "price": 7000, "color": "#FF00FF"},
    7: {"name": "Legendary", "chance": 4.0, "price": 9000, "color": "#FFA500"},
    8: {"name": "Mythic", "chance": 3.0, "price": 11000, "color": "#FF4500"},
    9: {"name": "Celestial", "chance": 2.0, "price": 13000, "color": "#00FFFF"},
    10: {"name": "Supreme", "chance": 1.5, "price": 14000, "color": "#DC143C"},
    11: {"name": "Exalted", "chance": 1.0, "price": 14500, "color": "#FFD700"},
    12: {"name": "Divine", "chance": 0.4, "price": 14800, "color": "#E6E6FA"},
    13: {"name": "Premium Edition", "chance": 0.1, "price": 15000, "color": "#RAINBOW"}
}

LANGUAGES = {
    "MM": {
        "WELCOME": "✨ **{name}** မင်္ဂလာပါ!\nNexus RPG Card Bot မှ ကြိုဆိုပါသည်!",
        "NOT_APPROVED": "⚠️ ဤ Group သည် အသုံးပြုခွင့် မရသေးပါ။ Owner Approve ပြုလုပ်ပေးရန် စောင့်ဆိုင်းပါ။",
        "NOT_ENOUGH_MEMBERS": "⚠️ ဤ Group တွင် လူ ၅၀ အနည်းဆုံး မရှိသေးပါ။ (လက်ရှိ: {count} ယောက်)",
        "NEED_JOIN": "❌ မင်္ဂလာပါ! ဘော့ကို စတင်အသုံးပြုရန် အောက်ပါ Channel နှင့် Group များကို မဖြစ်မနေ Join ပေးပါရန်လိုအပ်ပါသည်။"
    },
    "EN": {
        "WELCOME": "✨ Welcome **{name}** to Nexus RPG Card Bot!",
        "NOT_APPROVED": "⚠️ This group is not approved yet. Please wait for owner approval.",
        "NOT_ENOUGH_MEMBERS": "⚠️ This group requires at least 50 members. (Current: {count})",
        "NEED_JOIN": "❌ Please join our group and channel first to use this bot!"
    }
}
