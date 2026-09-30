"""
NEXUS CATCH BOT
modules/handlers.py

User Commands:
- /profile
- /harem
- /search
- /top
- /market
"""

import re
import logging
from html import escape

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import (
    ContextTypes,
    CommandHandler,
)

from database import (
    users_col,
    cards_col,
    inventory_col,
    market_col,
)

logger = logging.getLogger(__name__)


# ==========================================
# HELPER FUNCTIONS
# ==========================================

def safe_int(value, default=0):
    """Convert value to integer safely."""
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def safe_text(value, default="Unknown"):
    """Escape HTML text safely."""
    return escape(str(value if value is not None else default))


def get_user_id(update: Update):
    """Get Telegram user ID."""
    user = update.effective_user

    if not user:
        return None

    return user.id


# ==========================================
# PROFILE COMMAND
# ==========================================

async def profile_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    message = update.effective_message
    user = update.effective_user

    if not message or not user:
        return

    try:
        user_data = users_col.find_one(
            {"user_id": user.id}
        ) or {}

        balance = safe_int(user_data.get("balance", 0))
        gems = safe_int(user_data.get("gems", 0))

        total_cards = inventory_col.count_documents(
            {"user_id": user.id}
        )

        name = safe_text(user.first_name)

        username = (
            f"@{safe_text(user.username)}"
            if user.username
            else "Not Set"
        )

        text = (
            "👤 <b>PLAYER PROFILE</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
            f"👤 Name: <b>{name}</b>\n"
            f"🔗 Username: {username}\n"
            f"🆔 ID: <code>{user.id}</code>\n\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "💰 <b>ECONOMY</b>\n\n"
            f"🪙 Coins: <b>{balance:,}</b>\n"
            f"💎 Gems: <b>{gems:,}</b>\n\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "🎴 <b>COLLECTION</b>\n\n"
            f"🃏 Total Cards: <b>{total_cards}</b>\n\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "💗 Keep Collecting!"
        )

        await message.reply_text(
            text,
            parse_mode=ParseMode.HTML,
        )

    except Exception:
        logger.exception("Profile command error")

        await message.reply_text(
            "❌ Profile ကို ဖွင့်မရပါ။ နောက်မှ ထပ်ကြိုးစားပါ။"
        )


# ==========================================
# HAREM COMMAND
# ==========================================

async def harem_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    message = update.effective_message
    user = update.effective_user

    if not message or not user:
        return

    try:
        total = inventory_col.count_documents(
            {"user_id": user.id}
        )

        if total == 0:
            await message.reply_text(
                "🏰 <b>YOUR HAREM</b>\n\n"
                "🧧 သင့်တွင် Card မရှိသေးပါ။\n\n"
                "🎴 /catch ဖြင့် Card ဖမ်းယူနိုင်ပါသည်။",
                parse_mode=ParseMode.HTML,
            )
            return

        user_cards = list(
            inventory_col.find(
                {"user_id": user.id}
            ).sort("_id", -1).limit(10)
        )

        name = safe_text(user.first_name)

        text = (
            f"🏰 <b>{name}'s HAREM</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            f"🃏 Total Cards: <b>{total}</b>\n\n"
        )

        for index, item in enumerate(user_cards, 1):

            card_name = safe_text(
                item.get("card_name")
                or item.get("name")
                or "Unknown Card"
            )

            rarity = safe_text(
                item.get("rarity", "Common")
            )

            edition = safe_text(
                item.get("edition", "Normal")
            )

            card_id = safe_text(
                item.get("card_id", item.get("_id", "N/A"))
            )

            text += (
                f"{index}. 🎴 <b>{card_name}</b>\n"
                f"   ✨ Rarity: {rarity}\n"
                f"   💠 Edition: {edition}\n"
                f"   🆔 ID: <code>{card_id}</code>\n\n"
            )

        if total > 10:
            text += (
                f"📄 Showing 10 / {total} Cards\n"
                "💡 Pagination will be available in the Harem module."
            )

        text += "\n━━━━━━━━━━━━━━━━━━━━"

        await message.reply_text(
            text,
            parse_mode=ParseMode.HTML,
        )

    except Exception:
        logger.exception("Harem command error")

        await message.reply_text(
            "❌ Harem ကို ဖွင့်မရပါ။"
        )


# ==========================================
# SEARCH COMMAND
# ==========================================

async def search_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    message = update.effective_message

    if not message:
        return

    if not context.args:

        await message.reply_text(
            "🔍 <b>CHARACTER SEARCH</b>\n\n"
            "ရှာဖွေလိုသော Character အမည်ကို ထည့်ပါ။\n\n"
            "ဥပမာ:\n"
            "<code>/search Naruto</code>\n"
            "<code>/search Mikasa</code>",
            parse_mode=ParseMode.HTML,
        )
        return

    query = " ".join(context.args).strip()

    if not query:
        await message.reply_text(
            "❌ ရှာဖွေလိုသော အမည်ထည့်ပါ။"
        )
        return

    try:
        regex_query = re.escape(query)

        results = list(
            cards_col.find(
                {
                    "name": {
                        "$regex": regex_query,
                        "$options": "i",
                    }
                }
            ).limit(10)
        )

        if not results:

            await message.reply_text(
                f"❌ <b>{safe_text(query)}</b> အတွက် "
                "Character မတွေ့ရှိပါ။",
                parse_mode=ParseMode.HTML,
            )
            return

        text = (
            "🔍 <b>SEARCH RESULTS</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            f"📝 Query: <b>{safe_text(query)}</b>\n\n"
        )

        for index, card in enumerate(results, 1):

            card_name = safe_text(
                card.get("name", "Unknown")
            )

            anime = safe_text(
                card.get("anime", "N/A")
            )

            rarity = safe_text(
                card.get("rarity", "Common")
            )

            edition = safe_text(
                card.get("edition", "Normal")
            )

            card_id = safe_text(
                card.get("card_id", card.get("_id", "N/A"))
            )

            text += (
                f"{index}. 🎴 <b>{card_name}</b>\n"
                f"   📺 Anime: {anime}\n"
                f"   ✨ Rarity: {rarity}\n"
                f"   💠 Edition: {edition}\n"
                f"   🆔 ID: <code>{card_id}</code>\n\n"
            )

        text += (
            "━━━━━━━━━━━━━━━━━━━━\n"
            "💗 Nexus Character Collection"
        )

        await message.reply_text(
            text,
            parse_mode=ParseMode.HTML,
        )

    except Exception:
        logger.exception("Search command error")

        await message.reply_text(
            "❌ Search ပြုလုပ်ရာတွင် Error ဖြစ်နေပါသည်။"
        )


# ==========================================
# TOP COLLECTORS COMMAND
# ==========================================

async def top_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    message = update.effective_message

    if not message:
        return

    try:
        pipeline = [
            {
                "$group": {
                    "_id": "$user_id",
                    "count": {"$sum": 1},
                }
            },
            {
                "$sort": {
                    "count": -1,
                }
            },
            {
                "$limit": 10,
            },
        ]

        top_users = list(
            inventory_col.aggregate(pipeline)
        )

        if not top_users:

            await message.reply_text(
                "🏆 Collector စာရင်း မရှိသေးပါ။"
            )
            return

        medals = ["🥇", "🥈", "🥉"]

        text = (
            "🏆 <b>TOP HAREM COLLECTORS</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
        )

        for index, item in enumerate(top_users, 1):

            user_id = item.get("_id", "Unknown")
            count = safe_int(item.get("count", 0))

            medal = (
                medals[index - 1]
                if index <= 3
                else f"{index}."
            )

            text += (
                f"{medal} <code>{safe_text(user_id)}</code>\n"
                f"   🃏 Cards: <b>{count}</b>\n\n"
            )

        text += (
            "━━━━━━━━━━━━━━━━━━━━\n"
            "🌍 Global Top Collectors"
        )

        await message.reply_text(
            text,
            parse_mode=ParseMode.HTML,
        )

    except Exception:
        logger.exception("Top command error")

        await message.reply_text(
            "❌ Ranking ကို ဖွင့်မရပါ။"
        )


# ==========================================
# MARKET COMMAND
# ==========================================

async def market_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    message = update.effective_message

    if not message:
        return

    try:
        items = list(
            market_col.find().sort("_id", -1).limit(10)
        )

        if not items:

            await message.reply_text(
                "🏪 <b>CHARACTER MARKETPLACE</b>\n"
                "━━━━━━━━━━━━━━━━━━━━\n\n"
                "📭 လက်ရှိ Market တွင် Card ရောင်းရန် "
                "တင်ထားခြင်း မရှိသေးပါ။\n\n"
                "💡 နောက်မှ ထပ်လာကြည့်ပါ။",
                parse_mode=ParseMode.HTML,
            )
            return

        text = (
            "🛒 <b>CHARACTER MARKETPLACE</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
        )

        for index, item in enumerate(items, 1):

            card_name = safe_text(
                item.get("card_name")
                or item.get("name")
                or "Unknown Card"
            )

            price = safe_int(
                item.get("price", 0)
            )

            listing_id = safe_text(
                item.get("listing_id", item.get("_id", "N/A"))
            )

            seller_id = safe_text(
                item.get("seller_id", item.get("user_id", "N/A"))
            )

            text += (
                f"{index}. 🎴 <b>{card_name}</b>\n"
                f"   💰 Price: <b>{price:,}</b> Coins\n"
                f"   🆔 Listing: <code>{listing_id}</code>\n"
                f"   👤 Seller: <code>{seller_id}</code>\n\n"
            )

        text += (
            "━━━━━━━━━━━━━━━━━━━━\n"
            "💡 Card ဝယ်ယူရန် /buy ကို အသုံးပြုပါ။"
        )

        await message.reply_text(
            text,
            parse_mode=ParseMode.HTML,
        )

    except Exception:
        logger.exception("Market command error")

        await message.reply_text(
            "❌ Market ကို ဖွင့်မရပါ။"
        )


# ==========================================
# REGISTER USER HANDLERS
# ==========================================

def get_user_handlers():

    return [
        CommandHandler("profile", profile_command),
        CommandHandler("harem", harem_command),
        CommandHandler("search", search_command),
        CommandHandler("top", top_command),
        CommandHandler("market", market_command),
    ]
