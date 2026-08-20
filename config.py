import os

BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///bot_database.db")
PORT = int(os.getenv("PORT", 8080))

# Super Owner Telegram IDs
OWNER_IDS = [7974865879]

DEFAULT_SPAWN_THRESHOLD = 80
