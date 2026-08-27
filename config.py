import os
from dotenv import load_dotenv

load_dotenv()

# ==============================
# Telegram Bot Configuration
# ==============================

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
OWNER_ID = int(os.getenv("OWNER_ID", "0"))

# Notification Channel
CHANNEL_ID = os.getenv("CHANNEL_ID", "")

# Required Group / Channel
GROUP_LINK = os.getenv(
    "GROUP_LINK",
    "https://t.me/+00J7JktW8bJlZTY1"
)

CHANNEL_LINK = os.getenv(
    "CHANNEL_LINK",
    "https://t.me/+E6BxfAj0gaI2Y2Zl"
)

# Your bot's main / waifu link
WAIFU_LINK = os.getenv(
    "WAIFU_LINK",
    "https://t.me/"
)

# ==============================
# Group Requirements
# ==============================

# Group ထဲမှာ အနည်းဆုံး လူ 50 ရှိရမယ်
MIN_GROUP_MEMBERS = 50

# Bot ကို Group Admin ပေးထားရမယ်
REQUIRE_BOT_ADMIN = True

# Owner approval မရသေးရင် Bot အသုံးပြုခွင့်မပေး
REQUIRE_OWNER_APPROVAL = True

# ==============================
# Economy
# ==============================

DAILY_COINS = 500

# Claim cooldown
CLAIM_COOLDOWN_HOURS = 12

# 24 နာရီအတွင်း Claim အများဆုံး
CLAIM_LIMIT_24H = 2

# ==============================
# Pagination
# ==============================

HAREM_PER_PAGE = 10
MARKET_PER_PAGE = 10
SEARCH_PER_PAGE = 10
TOP_LIMIT = 15

# hmode မှာ ရွေးချယ်စရာ
HMODE_LIMIT = 10

# ==============================
# Card Editions
# ==============================

EDITIONS = [
    "Common",
    "Uncommon",
    "Rare",
    "Super Rare",
    "Epic",
    "Legendary",
    "Mythic",
    "Divine",
    "Celestial",
    "Eternal",
    "Ultimate",
    "Exclusive",
    "Premium",
]

# Premium အမြင့်ဆုံးစျေး
PREMIUM_PRICE = 15000

# ==============================
# Languages
# ==============================

SUPPORTED_LANGUAGES = {
    "my": "Myanmar",
    "en": "English",
}

DEFAULT_LANGUAGE = "my"

# ==============================
# Database
# ==============================

DATABASE_PATH = os.getenv(
    "DATABASE_PATH",
    "nexus_card.db"
)

# ==============================
# Bot Information
# ==============================

BOT_NAME = os.getenv(
    "BOT_NAME",
    "Nexus Card"
)

BOT_VERSION = "V5"

# ==============================
# Security
# ==============================

# Owner ID မရှိရင် Admin commands မလုပ်နိုင်
OWNER_ONLY_COMMANDS = {
    "drop",
    "broadcast",
    "givecoin",
    "givecard",
    "deletecard",
    "setdrop",
    "setprice",
    "setadmin",
    "deladmin",
    "approve",
    "reject",
    "ban",
    "unban",
    "maintenance",
