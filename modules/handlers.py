"""
modules/handlers.py
Harem, Market, Profile & User Commands
"""

import re
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


# =====================================
# PROFILE COMMAND
# =====================================

async def profile_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    user = update.effective_user
    message = update.effective_message

    if not user or not message:
        return

    user_data = users_col.find_one(
        {"user_id": user.id}
    ) or {}

    balance = user_data.get("balance", 0)
    gems = user_data.get("gems", 0)

    cards_count = inventory_col.count_documents(
        {"user_id": user.id}
    )

    name = escape(user.first_name or "Player")

    text = (
        f"👤 <b>{name}'s Profile</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"🆔 <code>{user.id}</code>\n"
        f"💰 <b>Coins:</b> {balance:,}\n"
        f"💎 <b>Gems:</b> {gems:,}\n"
        f"🃏 <b>Total Cards:</b> {cards_count}\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "💗 Keep collecting!"
    )

    await message.reply_text(
        text,
        parse_mode=ParseMode.HTML,
    )


# =====================================
# HAREM COMMAND
# =====================================

async def harem_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    user = update.effective_user
    message = update.effective_message

    if not user or not message:
        return

    user_cards = list(
        inventory_col.find(
            {"user_id": user.id}
        ).limit(10)
    )

    total = inventory_col.count_documents(
        {"user_id": user.id}
    )

    if not user_cards:
        await message.reply_text(
            "🧧 သင့်တွင် Card မရှိသေးပါ။\n"
            "🎴 /catch ဖြင့် Card ဖမ်းယူနိုင်ပါသည်။"
        )
        return

    name = escape(user.first_name or "Player")

    text = (
        f"🏰 <b>{name}'s Harem</b>\n"
        f"🃏 Total Cards: <b>{total}</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
    )

    for index, item in enumerate(user_cards, 1):

        card_name = escape(
            str(item.get("card_name", "Unknown Card"))
        )

        rarity = escape(
            str(item.get("rarity", "Common"))
        )

        text += (
            f"{index}. 🎴 <b>{card_name}</b>\n"
            f"   ✨ Rarity: {rarity}\n\n"
        )

    if total > 10:
        text += (
            f"📄 Showing 10 of {total} cards.\n"
            "Pagination ကို နောက်ပိုင်း ထပ်ချိတ်နိုင်ပါတယ်။"
        )

    await message.reply_text(
        text,
        parse_mode=ParseMode.HTML,
    )


# =====================================
# SEARCH COMMAND
# =====================================

async def search_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    message = update.effective_message

    if not message:
        return

    if not context.args:

        await message.reply_text(
            "🔍 ရှာဖွေလိုသော Character အမည်ကို ထည့်ပါ။\n\n"
            "ဥပမာ - /search Naruto"
        )
        return

    query = " ".join(context.args).strip()

    safe_query = re.escape(query)

    results = list(
        cards_col.find(
            {
                "name": {
                    "$regex": safe_query,
                    "$options": "i",
                }
            }
        ).limit(10)
    )

    if not results:

        await message.reply_text(
            f"❌ '{query}' အတွက် Character မတွေ့ရှိပါ။"
        )
        return

    text = (
        f"🔍 <b>Search Results</b>\n"
        f"📝 Query: {escape(query)}\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
    )

    for index, card in enumerate(results, 1):

        name = escape(
            str(card.get("name", "Unknown"))
        )

        anime = escape(
            str(card.get("anime", "N/A"))
        )

        rarity = escape(
            str(card.get("rarity", "Common"))
        )

        text += (
            f"{index}. 🎴 <b>{name}</b>\n"
            f"   📺 Anime: {anime}\n"
            f"   ✨ Rarity: {rarity}\n\n"
        )

    text += "━━━━━━━━━━━━━━━━━━━━"

    await message.reply_text(
        text,
        parse_mode=ParseMode.HTML,
    )


# =====================================
# TOP COLLECTORS COMMAND
# =====================================

async def top_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    message = update.effective_message

    if not message:
        return

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
            "🏆 လက်ရှိ Collector စာရင်း မရှိသေးပါ။"
        )
        return

    text = (
        "🏆 <b>TOP HAREM COLLECTORS</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
    )

    medals = ["🥇", "🥈", "🥉"]

    for index, item in enumerate(top_users, 1):

        user_id = item.get("_id", 0)
        count = item.get("count", 0)

        medal = (
            medals[index - 1]
            if index <= 3
            else f"{index}."
        )

        text += (
            f"{medal} <code>{user_id}</code>\n"
            f"   🃏 <b>{count}</b> Cards\n\n"
        )

    text += "━━━━━━━━━━━━━━━━━━━━"

    await message.reply_text(
        text,
        parse_mode=ParseMode.HTML,
    )


# =====================================
# MARKET COMMAND
# =====================================

async def market_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    message = update.effective_message

    if not message:
        return

    items = list(
        market_col.find().limit(10)
    )

    if not items:

        await message.reply_text(
            "🏪 <b>CHARACTER MARKETPLACE</b>\n\n"
            "📭 လက်ရှိ Market တွင် Card ရောင်းရန် "
            "တင်ထားခြင်း မရှိသေးပါ။",
            parse_mode=ParseMode.HTML,
        )
        return

    text = (
        "🛒 <b>CHARACTER MARKETPLACE</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
    )

    for index, item in enumerate(items, 1):

        card_name = escape(
            str(item.get("card_name", "Unknown Card"))
        )

        price = item.get("price", 0)

        listing_id = escape(
            str(item.get("_id", "N/A"))
        )

        text += (
            f"{index}. 🎴 <b>{card_name}</b>\n"
            f"   💰 Price: <b>{price:,}</b> Coins\n"
            f"   🆔 ID: <code>{listing_id}</code>\n\n"
        )

    text += (
        "━━━━━━━━━━━━━━━━━━━━\n"
        "💡 Card ဝယ်ယူရန် /buy ကို အသုံးပြုပါ။"
    )

    await message.reply_text(
        text,
        parse_mode=ParseMode.HTML,
    )


# =====================================
# REGISTER HANDLERS
# =====================================

def get_user_handlers():

    return [
        CommandHandler("profile", profile_command),
        CommandHandler("search", search_command),
        CommandHandler("top", top_command),
        CommandHandler("market", market_command),
    ]
