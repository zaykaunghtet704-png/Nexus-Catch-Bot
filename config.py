import os

BOT_TOKEN = os.getenv("BOT_TOKEN", "8823072889:AAHKIzIzYVm4CjRJzoJWCktJhI5ZYn4mn4Y")
OWNER_IDS = [7869852655, 7974865879]
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY", "32_BYTE_SECRET_KEY_FOR_AES_256!")

# Required Force Join Links
LINK_WAIFU = "https://t.me/example_waifu"
LINK_GROUP = "https://t.me/+00J7JktW8bJlZTY1"
LINK_CHANNEL = "https://t.me/+E6BxfAj0gaI2Y2Zl"

# Log Channel ID for New Bot Add Events (Fill your log channel id, e.g. -100xxxxxxx)
LOG_CHANNEL_ID = os.getenv("LOG_CHANNEL_ID", "-1001234567890")

# 10 Main Rarity Tiers with Prices & Drop Rates
RARITY_TIERS = {
    "1": {"name": "Common", "chance": 35.0, "color": "#808080", "price": 500},
    "2": {"name": "Uncommon", "chance": 20.0, "color": "#00FF00", "price": 1000},
    "3": {"name": "Rare", "chance": 12.0, "color": "#0000FF", "price": 2000},
    "4": {"name": "Super Rare", "chance": 8.0, "color": "#4B0082", "price": 3500},
    "5": {"name": "Ultra Rare", "chance": 6.0, "color": "#800080", "price": 5000},
    "6": {"name": "Epic", "chance": 5.0, "color": "#FF00FF", "price": 7000},
    "7": {"name": "Legendary", "chance": 4.0, "color": "#FFA500", "price": 9000},
    "8": {"name": "Mythic", "chance": 3.0, "color": "#FF4500", "price": 11000},
    "9": {"name": "Celestial", "chance": 2.0, "color": "#00FFFF", "price": 13000},
    "10": {"name": "Premium Edition", "chance": 0.1, "color": "#FFD700", "price": 15000}
}

# Multilingual Text Support
STRINGS = {
    "MM": {
        "start": "✨ **{name}** မင်္ဂလာပါ!\nNexus RPG Card Bot မှ ကြိုဆိုပါသည်!",
        "force_join": "⚠️ Harem/Bot အသုံးပြုရန် အောက်ပါ Group နှင့် Channel ၂ ခုလုံးကို မဖြစ်မနေ Join ပေးရန် လိုအပ်ပါသည်-",
        "gp_not_approved": "⚠️ ဤ Group တွင် Bot အသုံးပြုခွင့် မဖွင့်ရသေးပါ။ အနိမ့်ဆုံး လူ ၅၀ ရှိရမည်ဖြစ်ပြီး Bot အား Admin ပေးထားရမည်။ Owner ထံ ဆက်သွယ်၍ ခွင့်ပြုချက်ယူပါ။",
        "claim_success": "🎉 ဂုဏ်ယူပါတယ်! ကဒ်သစ် ရရှိခဲ့ပါပြီ- `{card_name}` ({rarity})",
        "no_coins": "❌ Coin မလုံလောက်ပါ။"
    },
    "EN": {
        "start": "✨ Welcome **{name}**!\nWelcome to Nexus RPG Card Bot!",
        "force_join": "⚠️ To access Harem/Bot, you must join both of our channels below:",
        "gp_not_approved": "⚠️ This group is not approved. Requires at least 50 members and Bot Admin rights. Contact Owner to activate.",
        "claim_success": "🎉 Congratulations! You received: `{card_name}` ({rarity})",
        "no_coins": "❌ Insufficient coins."
    }
}
