import os

BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///bot_database.db")
PORT = int(os.getenv("PORT", 8080))

# Owner User IDs (သင့် Telegram ID ပြောင်းပါ)
OWNER_IDS = [7974865879]
DEFAULT_SPAWN_THRESHOLD = 85

# Group Verification & Requirements
MIN_GROUP_MEMBERS = 50

# Force Join Settings
REQUIRED_GROUP_URL = "https://t.me/+00J7JktW8bJlZTY1"
REQUIRED_CHANNEL_URL = "https://t.me/+E6BxfAj0gaI2Y2Zl"
REQUIRED_GROUP_ID = "-1001234567890"    # သင့် Group ID ပြောင်းပါ
REQUIRED_CHANNEL_ID = "-1000987654321"  # သင့် Channel ID ပြောင်းပါ

# Admin Logging Channel
LOG_CHANNEL_ID = "-1001234567890"  # Bot Add သည့် Notification ဝင်မည့် Channel ID

MY_WAIFU_URL = "https://t.me/NexusCatchBot?start=harem"
START_IMAGE_URL = "https://picsum.photos/800/400"
