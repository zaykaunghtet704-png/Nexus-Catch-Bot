import os

BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
OWNER_IDS = [7974865879]  # သင်၏ Telegram User ID
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///nexus.db")
SPAWN_THRESHOLD = 15
PORT = int(os.environ.get("PORT", 8080))
