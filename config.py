import os

BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///bot_database.db")
PORT = int(os.getenv("PORT", 8080))

# Owner IDs (သင့် Telegram User ID ပြောင်းပါ)
OWNER_IDS = [7974865879]
DEFAULT_SPAWN_THRESHOLD = 85

# Force Join Links
FORCE_GROUP_URL = "https://t.me/+00J7JktW8bJlZTY1"
FORCE_CHANNEL_URL = "https://t.me/+E6BxfAj0gaI2Y2Zl"

# Bot မှ Force Join စစ်ဆေးရန် ID များ (-100xxxxxxxxxx Format)
REQUIRED_GROUP_ID = "-1001234567890"   
REQUIRED_CHANNEL_ID = "-1000987654321" 

# Bot ကို Group ထဲ Add လျှင် Notification တက်မည့် Log Channel ID
LOG_CHANNEL_ID = "-1001234567890"

# Bot Username ပြောင်းပါ (PM ထဲတွင် /harem ကို တိုက်ရိုက် ပွင့်စေရန်)
MY_WAIFU_URL = "https://t.me/NexusCatchBot?start=harem"
START_IMAGE_URL = "https://picsum.photos/800/400"
