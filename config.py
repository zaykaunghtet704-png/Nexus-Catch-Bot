import os

BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
OWNER_ID = int(os.getenv("OWNER_ID", "123456789"))
LOG_CHANNEL_ID = int(os.getenv("LOG_CHANNEL_ID", "-1001234567890"))

REQUIRED_GROUP_LINK = "https://t.me/+00J7JktW8bJlZTY1"
REQUIRED_CHANNEL_LINK = "https://t.me/+E6BxfAj0gaI2Y2Zl"
WAIFU_LINK = "https://t.me/YOUR_WAIFU_LINK"

REQUIRED_CHANNELS = [
    {"chat_id": "@your_channel_id", "link": REQUIRED_CHANNEL_LINK},
    {"chat_id": "@your_group_id", "link": REQUIRED_GROUP_LINK}
]

DEFAULT_START_PHOTO = "https://i.imgur.com/8Q9ZQ9R.jpg"
