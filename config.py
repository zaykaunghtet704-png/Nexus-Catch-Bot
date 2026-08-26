import os

from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()

OWNER_ID = int(
    os.getenv("OWNER_ID", "0").strip()
)
