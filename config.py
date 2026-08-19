import os

BOT_TOKEN = os.getenv("BOT_TOKEN")
OWNER_IDS = [7974865879, 7869852655]  # ထည့်သွင်းပေးထားသော Owner IDs များ
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///nexus.db")
SPAWN_THRESHOLD = 15
PORT = int(os.environ.get("PORT", 8080))
