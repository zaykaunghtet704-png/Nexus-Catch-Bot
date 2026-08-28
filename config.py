# ============================================================
# NEXUS CATCH BOT - CONFIG
# Version 4
# Myanmar 🇲🇲 / English 🇬🇧
# ============================================================

import os


# ============================================================
# BOT
# ============================================================

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()

OWNER_ID = int(
    os.getenv("OWNER_ID", "0")
)

ADMIN_IDS = {
    int(x.strip())
    for x in os.getenv("ADMIN_IDS", "").split(",")
    if x.strip().isdigit()
}


BOT_NAME = "NEXUS CARD BOT"
BOT_VERSION = "V4"


# ============================================================
# LANGUAGE
# ============================================================

DEFAULT_LANGUAGE = os.getenv(
    "DEFAULT_LANGUAGE",
    "my"
).lower()

SUPPORTED_LANGUAGES = [
    "my",
    "en",
]


# ============================================================
# DATABASE
# ============================================================

DATABASE_PATH = os.getenv(
    "DATABASE_PATH",
    "nexus_catch.db"
)

DB_PATH = DATABASE_PATH


# ============================================================
# GROUP / CHANNEL LINKS
# ============================================================

GROUP_LINK = os.getenv(
    "GROUP_LINK",
    "https://t.me/+00J7JktW8bJlZTY1"
).strip()

CHANNEL_LINK = os.getenv(
    "CHANNEL_LINK",
    "https://t.me/+E6BxfAj0gaI2Y2Zl"
).strip()


# Compatibility names
REQUIRED_GROUP_LINK = GROUP_LINK
REQUIRED_CHANNEL_LINK = CHANNEL_LINK

START_GROUP_LINK = GROUP_LINK
START_CHANNEL_LINK = CHANNEL_LINK


# ============================================================
# TELEGRAM CHAT IDs
# ============================================================

# Put the real Telegram IDs in Render Environment Variables.
#
# Example:
# REQUIRED_GROUP_ID=-1001234567890
# REQUIRED_CHANNEL_ID=-1009876543210
#

REQUIRED_GROUP_ID = int(
    os.getenv("REQUIRED_GROUP_ID", "0")
)

REQUIRED_CHANNEL_ID = int(
    os.getenv("REQUIRED_CHANNEL_ID", "0")
)


# IMPORTANT:
# bot.py imports these exact names.

GROUP_ID = REQUIRED_GROUP_ID
CHANNEL_ID = REQUIRED_CHANNEL_ID


# ============================================================
# WAIFU BUTTON
# ============================================================

WAIFU_LINK = os.getenv(
    "WAIFU_LINK",
    "https://t.me/"
).strip()

# Compatibility
I_AM_WAIFU_LINK = WAIFU_LINK


START_BUTTON_WAIFU = "💗 I'm Waifu"
START_BUTTON_GROUP = "👥 Group"
START_BUTTON_CHANNEL = "📢 Channel"


# ============================================================
# GROUP ACCESS
# ============================================================

MIN_GROUP_MEMBERS = int(
    os.getenv(
        "MIN_GROUP_MEMBERS",
        "50"
    )
)

REQUIRE_BOT_ADMIN = (
    os.getenv(
        "REQUIRE_BOT_ADMIN",
        "true"
    ).lower()
    in (
        "true",
        "1",
        "yes",
        "on",
    )
)

REQUIRE_OWNER_APPROVAL = (
    os.getenv(
        "REQUIRE_OWNER_APPROVAL",
        "true"
    ).lower()
    in (
        "true",
        "1",
        "yes",
        "on",
    )
)


# Compatibility names
BOT_MUST_BE_ADMIN = REQUIRE_BOT_ADMIN

GROUP_OWNER_APPROVAL_REQUIRED = (
    REQUIRE_OWNER_APPROVAL
)


# ============================================================
# CARD EDITIONS
# ============================================================

EDITIONS = [
    "Common",
    "Uncommon",
    "Rare",
    "Super Rare",
    "Ultra Rare",
    "Epic",
    "Super Epic",
    "Legendary",
    "Mythic",
    "Divine",
    "Exclusive",
    "Limited",
    "Premium",
]


# Compatibility names
CARD_EDITIONS = EDITIONS

CARD_TOTAL_EDITIONS = 13

CARD_HIGHEST_EDITION = "Premium"

CARD_DEFAULT_CURRENCY = "Coins"


# ============================================================
# CARD PRICE
# ============================================================

PREMIUM_PRICE = 15000

PREMIUM_SELL_PRICE = PREMIUM_PRICE

MARKET_MIN_PRICE = 1

MARKET_MAX_PRICE = 15000


CARD_SELL_PRICES = {
    "Common": 300,
    "Uncommon": 500,
    "Rare": 800,
    "Super Rare": 1200,
    "Ultra Rare": 1700,
    "Epic": 2300,
    "Super Epic": 3000,
    "Legendary": 4000,
    "Mythic": 5500,
    "Divine": 7000,
    "Exclusive": 8500,
    "Limited": 11000,
    "Premium": 15000,
}


# ============================================================
# DROP SYSTEM
# ============================================================

DROP_ENABLED = True

AUTO_DROP_ENABLED = True

DROP_MIN_CARDS = 1

DROP_MAX_CARDS = 3

DROP_COOLDOWN_SECONDS = int(
    os.getenv(
        "DROP_COOLDOWN_SECONDS",
        "0"
    )
)

DEFAULT_DROP_COUNT = 85


# ============================================================
# CLAIM SYSTEM
# ============================================================

CLAIM_ENABLED = True

CLAIM_COOLDOWN_HOURS = 12

CLAIM_CARDS_PER_CLAIM = 1

# Exact name used by bot.py
CLAIM_LIMIT_24H = 2

# Compatibility
CLAIM_DAILY_LIMIT = CLAIM_LIMIT_24H


# ============================================================
# DAILY COINS
# ============================================================

DAILY_COINS = 500

DAILY_COOLDOWN_HOURS = 24


# ============================================================
# ECONOMY
# ============================================================

STARTING_COINS = 0

MAX_COINS = 2_000_000_000

TRADE_TAX_PERCENT = 0

MARKET_TAX_PERCENT = 0


# ============================================================
# HAREM
# ============================================================

HAREM_PER_PAGE = 10

HAREM_ITEMS_PER_PAGE = HAREM_PER_PAGE

HAREM_BUTTONS_PER_PAGE = 10

HAREM_DEFAULT_MODE = "all"


# ============================================================
# HMODE
# ============================================================

HMODE_LIMIT = 10

HMODE_CARD_COUNT = HMODE_LIMIT

HMODE_ENABLED = True


# ============================================================
# MARKET
# ============================================================

MARKET_PER_PAGE = 10

MARKET_ITEMS_PER_PAGE = MARKET_PER_PAGE


# ============================================================
# SEARCH
# ============================================================

SEARCH_LIMIT = 10

SEARCH_RESULTS_PER_PAGE = SEARCH_LIMIT

SEARCH_MAX_RESULTS = 100


# ============================================================
# TOP / RANKINGS
# ============================================================

TOP_LIMIT = 15

GLOBAL_RANKING_LIMIT = TOP_LIMIT

GROUP_RANKING_LIMIT = 15

TODAY_RANKING_LIMIT = 15


# ============================================================
# PROFILE
# ============================================================

PROFILE_SHOW_PHOTO = True

PROFILE_SHOW_CARD_COUNT = True

PROFILE_SHOW_COINS = True

PROFILE_SHOW_GLOBAL_RANK = True

PROFILE_SHOW_COLLECTION = True

PROFILE_SHOW_STATS = True


# ============================================================
# TRADE / GIFT / DUEL
# ============================================================

TRADE_ENABLED = True

GIFT_ENABLED = True

DUEL_ENABLED = True


# ============================================================
# DUEL
# ============================================================

DUEL_REWARD_MIN_COINS = 50

DUEL_REWARD_MAX_COINS = 500

DUEL_EXP_REWARD_MIN = 10

DUEL_EXP_REWARD_MAX = 100

DUEL_COOLDOWN_SECONDS = 60


# ============================================================
# CARD LEVEL / EXP
# ============================================================

CARD_LEVEL_ENABLED = True

CARD_MAX_LEVEL = 100

CARD_BASE_EXP = 100

CARD_EXP_MULTIPLIER = 1.25


# ============================================================
# FAVORITE
# ============================================================

FAV_ENABLED = True

MAX_FAVOURITES = 20


# ============================================================
# CHECK CARD
# ============================================================

CHECK_CARD_ENABLED = True


# ============================================================
# RESET
# ============================================================

RESET_ENABLED = True


# ============================================================
# CHANGE TIME
# ============================================================

CHANGE_TIME_ENABLED = True

OWNER_CAN_CHANGE_DROP_COUNT = True

OWNER_CAN_CHANGE_DROP_TIME = True


# ============================================================
# OWNER CARD MANAGEMENT
# ============================================================

OWNER_CAN_ADD_CARD = True

OWNER_CAN_REMOVE_CARD = True

OWNER_CAN_EDIT_CARD = True

OWNER_CAN_EDIT_PRICE = True


# ============================================================
# ADMIN PERMISSIONS
# ============================================================

ADMIN_CAN_MANAGE_CARDS = True

ADMIN_CAN_MANAGE_USERS = True

ADMIN_CAN_MANAGE_GROUPS = True

ADMIN_CAN_MANAGE_MARKET = True

ADMIN_CAN_MANAGE_ECONOMY = True


# ============================================================
# OWNER ONLY COMMANDS
# ============================================================

OWNER_ONLY_COMMANDS = {
    "drop",
    "addcard",
    "deletecard",
    "delcard",
    "editcard",
    "givecard",
    "takecard",
    "givecoin",
    "givecoins",
    "takecoins",
    "addcoins",
    "delcoins",
    "setprice",
    "setdrop",
    "setadmin",
    "deladmin",
    "approve",
    "reject",
    "broadcast",
    "stats",
    "maintenance",
    "changetime",
    "groups",
    "banuser",
    "unbanuser",
    "resetuser",
    "resetall",
}


# ============================================================
# ADMIN COMMANDS
# ============================================================

ADMIN_COMMANDS = {
    "drop",
    "addcard",
    "deletecard",
    "delcard",
    "editcard",
    "givecard",
    "takecard",
    "givecoin",
    "addcoins",
    "delcoins",
    "setprice",
    "setdrop",
    "approve",
    "reject",
    "groups",
}


# ============================================================
# USER COMMANDS
# ============================================================

USER_COMMANDS = {
    "start",
    "help",
    "harem",
    "search",
    "profile",
    "top",
    "ctop",
    "rankings",
    "daily",
    "balance",
    "sellprice",
    "market",
    "sell",
    "buy",
    "delist",
    "trade",
    "gift",
    "duel",
    "fav",
    "unfav",
    "todayNexusCatch",
    "check",
    "Nexus",
    "claim",
    "hmode",
    "reset",
    "upgrade",
}


# ============================================================
# COMMAND ALIASES
# ============================================================

COMMAND_ALIASES = {

    "start": ["/start"],

    "help": ["/help"],

    "harem": ["/harem"],

    "search": ["/search"],

    "profile": ["/profile"],

    "top": ["/top"],

    "ctop": ["/ctop"],

    "rankings": ["/rankings"],

    "daily": ["/daily"],

    "balance": ["/balance"],

    "sellprice": ["/sellprice"],

    "market": ["/market"],

    "sell": ["/sell"],

    "buy": ["/buy"],

    "delist": ["/delist"],

    "trade": ["/trade"],

    "gift": ["/gift"],

    "duel": ["/duel"],

    "fav": ["/fav"],

    "unfav": ["/unfav"],

    "todayNexusCatch": [
        "/todayNexusCatch"
    ],

    "check": ["/check"],

    "Nexus": ["/Nexus"],

    "claim": ["/claim"],

    "hmode": ["/hmode"],

    "reset": ["/reset"],

    "upgrade": ["/upgrade"],
}


# ============================================================
# START
# ============================================================

START_IMAGE_URL = os.getenv(
    "START_IMAGE_URL",
    ""
).strip()


# ============================================================
# LANGUAGE TEXT
# ============================================================

MY_TEXT = {

    "bot_name":
        "🎴 NEXUS CARD BOT",

    "welcome":
        "🎴 NEXUS Card Bot မှ ကြိုဆိုပါတယ်။",

    "owner_approval":
        "🔐 Owner Approval လိုအပ်ပါတယ်။",

    "bot_admin":
        "🤖 Bot ကို Group Admin ပေးထားရပါမယ်။",

    "minimum_members":
        "👥 Group မှာ Member အနည်းဆုံး 50 ယောက်ရှိရပါမယ်။",

    "join_required":
        "🔗 Group နှင့် Channel ကို Join လုပ်ပြီးမှ အသုံးပြုနိုင်ပါတယ်။",

    "not_found":
        "❌ မတွေ့ပါ။",

    "no_cards":
        "🎴 ကဒ်မရှိသေးပါ။",

    "insufficient_coins":
        "🪙 Coin မလုံလောက်ပါ။",

    "success":
        "✅ အောင်မြင်ပါပြီ။",

    "error":
        "⚠️ တစ်ခုခုမှားယွင်းနေပါတယ်။",
}


EN_TEXT = {

    "bot_name":
        "🎴 NEXUS CARD BOT",

    "welcome":
        "🎴 Welcome to NEXUS Card Bot.",

    "owner_approval":
        "🔐 Owner approval is required.",

    "bot_admin":
        "🤖 The bot must be an administrator.",

    "minimum_members":
        "👥 The group must have at least 50 members.",

    "join_required":
        "🔗 Please join the required group and channel.",

    "not_found":
        "❌ Not found.",

    "no_cards":
        "🎴 No cards found.",

    "insufficient_coins":
        "🪙 Not enough coins.",

    "success":
        "✅ Successfully completed.",

    "error":
        "⚠️ Something went wrong.",
}


# ============================================================
# HELP / PAGINATION
# ============================================================

HELP_PAGES = 6

HELP_ITEMS_PER_PAGE = 8

PAGINATION_ENABLED = True

PAGINATION_BUTTONS = True


# ============================================================
# LOGGING
# ============================================================

LOG_LEVEL = os.getenv(
    "LOG_LEVEL",
    "INFO"
)

LOG_COMMANDS = True

LOG_ERRORS = True

LOG_GROUP_INSTALLS = True

LOG_TRADES = True

LOG_MARKET = True


# ============================================================
# LOG CHANNELS
# ============================================================

GROUP_LOG_CHAT_ID = int(
    os.getenv(
        "GROUP_LOG_CHAT_ID",
        "0"
    )
)

OWNER_LOG_CHAT_ID = int(
    os.getenv(
        "OWNER_LOG_CHAT_ID",
        "0"
    )
)


# ============================================================
# BROADCAST
# ============================================================

BROADCAST_ENABLED = True

BROADCAST_DELAY = 0.05


# ============================================================
# MAINTENANCE
# ============================================================

MAINTENANCE_MODE = (
    os.getenv(
        "MAINTENANCE_MODE",
        "false"
    ).lower()
    in (
        "true",
        "1",
        "yes",
        "on",
    )
)


# ============================================================
# TELEGRAM
# ============================================================

PARSE_MODE = "HTML"

DISABLE_WEB_PAGE_PREVIEW = True

PROTECT_CONTENT = False


# ============================================================
# RENDER
# ============================================================

HOST = os.getenv(
    "HOST",
    "0.0.0.0"
)

PORT = int(
    os.getenv(
        "PORT",
        "10000"
    )
)


# ============================================================
# SECURITY
# ============================================================

ALLOW_PRIVATE_CHAT = True

ALLOW_GROUP_CHAT = True

ALLOW_CHANNEL_CHAT = False


# ============================================================
# DEVELOPMENT
# ============================================================

DEBUG = (
    os.getenv(
        "DEBUG",
        "false"
    ).lower()
    in (
        "true",
        "1",
        "yes",
        "on",
    )
)


# ============================================================
# VALIDATION
# ============================================================

if not BOT_TOKEN:
    print(
        "⚠️ WARNING: BOT_TOKEN is not configured."
    )

if not OWNER_ID:
    print(
        "⚠️ WARNING: OWNER_ID is not configured."
    )

print(
    "✅ NEXUS CARD BOT configuration loaded."
)
