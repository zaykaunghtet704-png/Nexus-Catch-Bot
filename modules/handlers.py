"""
NEXUS CATCH BOT
modules/handlers.py

User Commands:
- /profile
- /search
- /top

Harem Commands are handled separately by modules/harem.py
Market Commands are handled separately by modules/trade_market.py
"""

import re
import logging
from html import escape

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes, CommandHandler

from database import users_col, cards_col, inventory_col

logger = logging.getLogger(__name__)


def safe_int(value, default=0):
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def safe_text(value, default="Unknown"):
    if value is None:
        value = default
    return escape(str(value))


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
        user_data = users_col.find_one({"user_id": user.id}) or {}

        # coins ကို အဓိကသုံးပြီး balance အဟောင်းကို fallback ထားသည်
        coins = safe_int(
            user_data.get("coins", user_data.get("balance", 0))
        )
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
            f"🪙 Coins: <b>{coins:,}</b>\n"
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

    try:
        regex_query = re.escape(query)

        results = list(
            cards_col.find({
                "name": {
                    "$regex": regex_query,
                    "$options": "i",
                }
            }).limit(10)
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
            card_name = safe_text(card.get("name", "Unknown"))
            anime = safe_text(card.get("anime", "N/A"))
            rarity = safe_text(card.get("rarity", "Common"))
            edition = safe_text(card.get("edition", "Normal"))
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
            {"$sort": {"count": -1}},
            {"$limit": 10},
        ]

        top_users = list(inventory_col.aggregate(pipeline))

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
# REGISTER USER HANDLERS
# ==========================================

def get_user_handlers():
    return [
        CommandHandler("profile", profile_command),
        CommandHandler("search", search_command),
        CommandHandler("top", top_command),
    ]
