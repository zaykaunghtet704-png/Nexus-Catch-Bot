"""
NEXUS CARD BOT
Configuration File
Version 4

Myanmar 🇲🇲 + English 🇬🇧
"""

import os


# ============================================================
# BOT
# ============================================================

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()

if not BOT_TOKEN:
    raise RuntimeError(
        "BOT_TOKEN environment variable is not set."
    )


# ============================================================
# OWNER / ADMINS
# ============================================================

def _get_int_list(name):
    value = os.getenv(name, "").strip()

    if not value:
        return set()

    result = set()

    for item in value.split(","):
        item = item.strip()

        if not item:
            continue

        try:
            result.add(int(item))
        except ValueError:
            pass

    return result


OWNER_ID = int(
    os.getenv("OWNER_ID", "0")
)

# Multiple bot admins
ADMIN_IDS = _get_int_list(
    "ADMIN_IDS"
)

# Owner automatically becomes admin
if OWNER_ID:
    ADMIN_IDS.add(
        OWNER_ID
    )


# ============================================================
# OWNER ONLY COMMANDS
# ============================================================

OWNER_ONLY_COMMANDS = {
    "broadcast",
    "addcard",
    "editcard",
    "delcard",
    "givecard",
    "givecoins",
    "takecoins",
    "ban",
    "unban",
    "addadmin",
    "deladmin",
    "setprice",
    "setdrop",
    "changetime",
    "setclaim",
    "maintenance",
    "stats",
    "reload",
    "resetall",
}


# ============================================================
# ADMIN COMMANDS
# ============================================================

ADMIN_COMMANDS = {
    "addcard",
    "editcard",
    "delcard",
    "givecard",
    "givecoins",
    "takecoins",
    "ban",
    "unban",
    "mute",
    "unmute",
    "warn",
    "warnings",
    "setprice",
    "drop",
    "changetime",
    "stats",
    "users",
    "groups",
}


# ============================================================
# DATABASE
# ============================================================

DATABASE_PATH = os.getenv(
    "DATABASE_PATH",
    "nexus.db",
)


# ============================================================
# LANGUAGE
# ============================================================

DEFAULT_LANGUAGE = os.getenv(
    "DEFAULT_LANGUAGE",
    "my",
).lower()

SUPPORTED_LANGUAGES = {
    "my": "Myanmar 🇲🇲",
    "en": "English 🇬🇧",
}


# ============================================================
# CARD SYSTEM
# ============================================================

CARD_EDITIONS = [
    "Common",
    "Uncommon",
    "Rare",
    "Super Rare",
    "Epic",
    "Ultra",
    "Mythic",
    "Legendary",
    "Divine",
    "Immortal",
    "Secret",
    "Exclusive",
    "Premium",
]


# Highest → Lowest
EDITION_RANK = {
    "Premium": 13,
    "Exclusive": 12,
    "Secret": 11,
    "Immortal": 10,
    "Divine": 9,
    "Legendary": 8,
    "Mythic": 7,
    "Ultra": 6,
    "Epic": 5,
    "Super Rare": 4,
    "Rare": 3,
    "Uncommon": 2,
    "Common": 1,
}


# ============================================================
# PREMIUM PRICE
# ============================================================

PREMIUM_PRICE = 15000


# Default prices
EDITION_PRICES = {
    "Common": 500,
    "Uncommon": 1000,
    "Rare": 1800,
    "Super Rare": 2500,
    "Epic": 3500,
    "Ultra": 5000,
    "Mythic": 6500,
    "Legendary": 8000,
    "Divine": 9500,
    "Immortal": 11000,
    "Secret": 12000,
    "Exclusive": 13500,
    "Premium": PREMIUM_PRICE,
}


# ============================================================
# DAILY
# ============================================================

DAILY_REWARD = 500

DAILY_COOLDOWN = 24 * 60 * 60


# ============================================================
# CLAIM
# ============================================================

# User can claim twice in 24 hours
CLAIM_COOLDOWN = 12 * 60 * 60

CLAIMS_PER_24_HOURS = 2


# ============================================================
# DROP
# ============================================================

DROP_ENABLED = True

# Owner can change these later
DROP_DEFAULT_COUNT = 1

DROP_MIN_COUNT = 1
DROP_MAX_COUNT = 10


# ============================================================
# HAREM
# ============================================================

HAREM_PER_PAGE = 6

HMODE_DEFAULT = 10

HMODE_OPTIONS = [
    5,
    10,
    15,
    20,
    999999,
]


# ============================================================
# MARKET
# ============================================================

MARKET_ENABLED = True

MARKET_PAGE_SIZE = 6

MIN_SELL_PRICE = 1

MAX_SELL_PRICE = 1000000000


# ============================================================
# TRADE
# ============================================================

TRADE_ENABLED = True

TRADE_TIMEOUT = 120


# ============================================================
# DUEL
# ============================================================

DUEL_ENABLED = True

DUEL_TIMEOUT = 60

DUEL_MIN_COINS = 0


# ============================================================
# GIFT
# ============================================================

GIFT_ENABLED = True


# ============================================================
# FAVORITES
# ============================================================

FAVORITES_ENABLED = True

MAX_FAVORITES = 50


# ============================================================
# RANKING
# ============================================================

GLOBAL_TOP_LIMIT = 15

GROUP_TOP_LIMIT = 15


# ============================================================
# TODAY NEXUS CATCH
# ============================================================

TODAY_TOP_LIMIT = 15


# ============================================================
# SEARCH
# ============================================================

SEARCH_PER_PAGE = 6


# ============================================================
# CARD CHECK
# ============================================================

CHECK_CARD_ENABLED = True


# ============================================================
# JOIN REQUIREMENT
# ============================================================

JOIN_REQUIREMENT_ENABLED = True


# Required Group
REQUIRED_GROUP_LINK = (
    "https://t.me/+00J7JktW8bJlZTY1"
)

# Required Channel
REQUIRED_CHANNEL_LINK = (
    "https://t.me/+E6BxfAj0gaI2Y2Zl"
)


# ============================================================
# GROUP REQUIREMENT
# ============================================================

# Group must have at least 50 members
MIN_GROUP_MEMBERS = 50

# Bot must be admin
BOT_MUST_BE_ADMIN = True

# Owner approval required
GROUP_OWNER_APPROVAL_REQUIRED = True


# ============================================================
# GROUP ACTIVATION
# ============================================================

GROUP_ACTIVATION_ENABLED = True


# Possible statuses:
#
# pending
# approved
# rejected
# disabled
#

GROUP_STATUS_PENDING = "pending"
GROUP_STATUS_APPROVED = "approved"
GROUP_STATUS_REJECTED = "rejected"
GROUP_STATUS_DISABLED = "disabled"


# ============================================================
# GROUP JOIN NOTIFICATION
# ============================================================

GROUP_JOIN_NOTIFICATION_ENABLED = True

CHANNEL_NOTIFICATION_ENABLED = True


# ============================================================
# GROUP INFORMATION
# ============================================================

GROUP_LOG_ENABLED = True

GROUP_LOG_CHAT_ID = int(
    os.getenv(
        "GROUP_LOG_CHAT_ID",
        "0",
    )
)


# ============================================================
# OWNER NOTIFICATION
# ============================================================

OWNER_NOTIFICATION_ENABLED = True

OWNER_LOG_CHAT_ID = int(
    os.getenv(
        "OWNER_LOG_CHAT_ID",
        "0",
    )
)


# ============================================================
# CARD DROP MESSAGE
# ============================================================

DROP_MESSAGE = (
    "🎴 <b>NEXUS CARD DROP</b>\n\n"
    "✨ A new card has appeared!\n"
    "⚡ Be the fastest one to claim it!\n\n"
    "🔗 Press the button below first."
)


# ============================================================
# CLAIM MESSAGE
# ============================================================

CLAIM_SUCCESS_MESSAGE = (
    "🎉 <b>CARD CLAIMED!</b>\n\n"
    "🎴 You successfully obtained:\n"
    "✨ <b>{card_name}</b>\n\n"
    "🆔 ID: <code>{char_id}</code>\n"
    "💎 Edition: <b>{edition}</b>\n"
    "💰 Price: <b>{price:,}</b>"
)


# ============================================================
# ERROR MESSAGES
# ============================================================

ERROR_NOT_OWNER = (
    "🚫 Owner only command."
)

ERROR_NOT_ADMIN = (
    "🚫 Admin permission required."
)

ERROR_NOT_GROUP = (
    "🚫 This command can only be used in a group."
)

ERROR_GROUP_TOO_SMALL = (
    "🚫 ဒီ Group မှာ Member အနည်းဆုံး "
    f"{MIN_GROUP_MEMBERS} ယောက်ရှိရပါမယ်။"
)

ERROR_BOT_NOT_ADMIN = (
    "🚫 Bot ကို Group Admin ပေးထားရပါမယ်။"
)

ERROR_GROUP_NOT_APPROVED = (
    "⏳ ဒီ Group ကို Owner က "
    "အတည်ပြုပေးရန် လိုအပ်ပါသည်။"
)

ERROR_JOIN_REQUIRED = (
    "🔒 ဆက်သုံးရန် အောက်ပါ Group နှင့် "
    "Channel ကို Join လုပ်ထားရပါမယ်။"
)


# ============================================================
# SUCCESS MESSAGES
# ============================================================

SUCCESS_APPROVED = (
    "✅ Group approved successfully."
)

SUCCESS_REJECTED = (
    "❌ Group rejected."
)

SUCCESS_CARD_ADDED = (
    "🎴 Card added successfully."
)

SUCCESS_CARD_DELETED = (
    "🗑️ Card deleted successfully."
)

SUCCESS_COINS_GIVEN = (
    "🪙 Coins added successfully."
)


# ============================================================
# COMMAND NAMES
# ============================================================

COMMANDS = {
    "start": "start",
    "help": "help",
    "harem": "harem",
    "search": "search",
    "profile": "profile",
    "top": "top",
    "ctop": "ctop",
    "rankings": "rankings",
    "daily": "daily",
    "balance": "balance",
    "sellprice": "sellprice",
    "market": "market",
    "sell": "sell",
    "buy": "buy",
    "delist": "delist",
    "trade": "trade",
    "gift": "gift",
    "duel": "duel",
    "fav": "fav",
    "unfav": "unfav",
    "todayNexusCatch": "todayNexusCatch",
    "check": "check",
    "changetime": "changetime",
    "Nexus": "Nexus",
    "claim": "claim",
    "hmode": "hmode",
    "reset": "reset",
    "upgrade": "upgrade",
}


# ============================================================
# OWNER COMMANDS
# ============================================================

OWNER_COMMANDS = {
    "broadcast",
    "addcard",
    "editcard",
    "delcard",
    "givecard",
    "takecard",
    "givecoins",
    "takecoins",
    "addadmin",
    "deladmin",
    "ban",
    "unban",
    "maintenance",
    "setdrop",
    "setprice",
    "changetime",
    "setclaim",
    "approve",
    "reject",
    "groups",
    "users",
    "stats",
    "reload",
    "resetall",
}


# ============================================================
# CARD DROP BUTTON
# ============================================================

DROP_BUTTON_TEXT = (
    "🎴 Claim Card"
)


# ============================================================
# BOT INFORMATION
# ============================================================

BOT_NAME = (
    "NEXUS CARD BOT"
)

BOT_VERSION = (
    "V4"
)


# ============================================================
# SUPPORT / LINKS
# ============================================================

WAIFU_LINK = os.getenv(
    "WAIFU_LINK",
    "https://t.me/",
)

GROUP_LINK = os.getenv(
    "GROUP_LINK",
    REQUIRED_GROUP_LINK,
)

CHANNEL_LINK = os.getenv(
    "CHANNEL_LINK",
    REQUIRED_CHANNEL_LINK,
)


# ============================================================
# LOGGING
# ============================================================

LOG_LEVEL = os.getenv(
    "LOG_LEVEL",
    "INFO",
)


# ============================================================
# TIMEZONE
# ============================================================

TIMEZONE = os.getenv(
    "TIMEZONE",
    "Asia/Yangon",
)


# ============================================================
# SAFETY
# ============================================================

MAX_MESSAGE_LENGTH = 4096

MAX_CALLBACK_LENGTH = 64


# ============================================================
# FEATURE FLAGS
# ============================================================

FEATURES = {
    "harem": True,
    "search": True,
    "profile": True,
    "top": True,
    "ctop": True,
    "rankings": True,
    "daily": True,
    "market": True,
    "trade": True,
    "gift": True,
    "duel": True,
    "favorites": True,
    "today_catch": True,
    "claim": True,
    "hmode": True,
    "upgrade": True,
}


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def is_owner(user_id):
    """
    Check whether a Telegram user is the bot owner.
    """

    try:
        return int(user_id) == OWNER_ID
    except (TypeError, ValueError):
        return False


def is_admin(user_id):
    """
    Check whether a Telegram user is an admin.
    """

    try:
        return (
            int(user_id) in ADMIN_IDS
        )
    except (TypeError, ValueError):
        return False


def is_owner_or_admin(user_id):
    """
    Owner or admin.
    """

    return (
        is_owner(user_id)
        or is_admin(user_id)
    )


def get_edition_price(
    edition,
):
    """
    Get default selling price for an edition.
    """

    return EDITION_PRICES.get(
        str(edition),
        500,
    )


def get_edition_rank(
    edition,
):
    """
    Get edition rank.
    """

    return EDITION_RANK.get(
        str(edition),
        1,
    )


def feature_enabled(
    feature,
):
    """
    Check feature status.
    """

    return FEATURES.get(
        feature,
        False,
    )


# ============================================================
# STARTUP INFO
# ============================================================

print(
    f"🚀 {BOT_NAME} {BOT_VERSION} configuration loaded."
)
