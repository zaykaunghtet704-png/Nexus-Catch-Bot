"""
NEXUS CATCH BOT
modules/trade_market.py

Commands:
- /sell
- /market
- /buy
- /fav
"""

import logging
from html import escape

from bson import ObjectId
from pymongo import ReturnDocument

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import (
    CommandHandler,
    ContextTypes,
)

from database import (
    inventory_col,
    market_col,
    users_col,
)

logger = logging.getLogger(__name__)


# ==========================================
# HELPERS
# ==========================================

def safe_text(value, default="Unknown"):
    if value is None:
        value = default
    return escape(str(value))


def safe_int(value, default=0):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


# ==========================================
# SELL COMMAND
# ==========================================

async def sell_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    message = update.effective_message
    user = update.effective_user

    if not message or not user:
        return

    if len(context.args) < 2:

        await message.reply_text(
            "🛒 <b>SELL CARD</b>\n\n"
            "အသုံးပြုပုံ:\n"
            "<code>/sell [Card ID] [Price]</code>\n\n"
            "ဥပမာ:\n"
            "<code>/sell 0001 5000</code>",
            parse_mode=ParseMode.HTML,
        )
        return

    card_id = context.args[0]

    try:
        price = int(context.args[1])
    except ValueError:
        await message.reply_text(
            "❌ စျေးနှုန်းသည် နံပါတ်ဖြစ်ရပါမည်။"
        )
        return

    if price <= 0:
        await message.reply_text(
            "❌ စျေးနှုန်းသည် 0 ထက် ကြီးရပါမည်။"
        )
        return

    try:

        item = inventory_col.find_one({
            "user_id": user.id,
            "card_id": card_id,
        })

        if not item:
            await message.reply_text(
                "❌ သင့် Inventory တွင် ထို Card မရှိပါ။"
            )
            return

        # Prevent duplicate listing of same inventory item
        existing = market_col.find_one({
            "seller_id": user.id,
            "inventory_id": item["_id"],
        })

        if existing:
            await message.reply_text(
                "❌ ဒီ Card ကို Market မှာ တင်ထားပြီးပါပြီ။"
            )
            return

        listing = {
            "seller_id": user.id,
            "seller_name": user.first_name or "Unknown",
            "inventory_id": item["_id"],
            "card_id": item.get("card_id"),
            "name": item.get(
                "name",
                item.get("card_name", "Unknown Card"),
            ),
            "anime": item.get("anime", "Unknown"),
            "rarity": item.get("rarity", "Common"),
            "edition": item.get("edition", "Normal"),
            "img_url": item.get("img_url"),
            "price": price,
        }

        # Insert listing first
        result = market_col.insert_one(listing)

        try:
            deleted = inventory_col.delete_one({
                "_id": item["_id"],
                "user_id": user.id,
            })

            if deleted.deleted_count == 0:
                market_col.delete_one({
                    "_id": result.inserted_id
                })

                await message.reply_text(
                    "❌ Card ပိုင်ဆိုင်မှုကို အတည်မပြုနိုင်ပါ။"
                )
                return

        except Exception:
            market_col.delete_one({
                "_id": result.inserted_id
            })
            raise

        await message.reply_text(
            "🛒 <b>CARD LISTED SUCCESSFULLY</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
            f"🎴 Card: <b>{safe_text(listing['name'])}</b>\n"
            f"✨ Rarity: {safe_text(listing['rarity'])}\n"
            f"💰 Price: <b>{price:,} Coins</b>\n"
            f"🆔 Market ID:\n"
            f"<code>{result.inserted_id}</code>\n\n"
            "━━━━━━━━━━━━━━━━━━━━",
            parse_mode=ParseMode.HTML,
        )

    except Exception:
        logger.exception("Sell command error")

        await message.reply_text(
            "❌ Card ရောင်းချရာတွင် Error ဖြစ်နေပါသည်။"
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

        listings = list(
            market_col.find().sort("_id", -1).limit(10)
        )

        if not listings:
            await message.reply_text(
                "🛒 <b>GLOBAL MARKETPLACE</b>\n"
                "━━━━━━━━━━━━━━━━━━━━\n\n"
                "📭 လက်ရှိ ရောင်းရန်တင်ထားသော Card မရှိသေးပါ။",
                parse_mode=ParseMode.HTML,
            )
            return

        text = (
            "🛒 <b>GLOBAL MARKETPLACE</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
        )

        for index, item in enumerate(listings, 1):

            name = safe_text(
                item.get("name", "Unknown Card")
            )

            anime = safe_text(
                item.get("anime", "Unknown")
            )

            rarity = safe_text(
                item.get("rarity", "Common")
            )

            seller = safe_text(
                item.get("seller_name", "Unknown")
            )

            price = safe_int(item.get("price", 0))

            market_id = safe_text(
                item.get("_id", "N/A")
            )

            text += (
                f"{index}. 🎴 <b>{name}</b>\n"
                f"📺 {anime}\n"
                f"✨ {rarity}\n"
                f"💰 Price: <b>{price:,} Coins</b>\n"
                f"👤 Seller: {seller}\n"
                f"🆔 ID: <code>{market_id}</code>\n\n"
            )

        text += (
            "━━━━━━━━━━━━━━━━━━━━\n"
            "💡 ဝယ်ယူရန်:\n"
            "<code>/buy [Market ID]</code>\n\n"
            "🎴 ရောင်းရန်:\n"
            "<code>/sell [Card ID] [Price]</code>"
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
# BUY COMMAND
# ==========================================

async def buy_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    message = update.effective_message
    user = update.effective_user

    if not message or not user:
        return

    if not context.args:
        await message.reply_text(
            "🛒 <b>BUY CARD</b>\n\n"
            "အသုံးပြုပုံ:\n"
            "<code>/buy [Market ID]</code>",
            parse_mode=ParseMode.HTML,
        )
        return

    try:
        market_id = ObjectId(context.args[0])
    except Exception:
        await message.reply_text(
            "❌ Market ID မှားယွင်းနေပါသည်။"
        )
        return

    try:

        # Atomically reserve the listing.
        # Only one buyer can successfully remove it.
        listing = market_col.find_one_and_delete({
            "_id": market_id,
            "seller_id": {"$ne": user.id},
        })

        if not listing:

            await message.reply_text(
                "❌ Market ID မရှိတော့ပါ သို့မဟုတ် "
                "မိမိ Card ကို ပြန်ဝယ်ရန် ကြိုးစားနေပါသည်။"
            )
            return

        price = safe_int(listing.get("price", 0))
        seller_id = listing.get("seller_id")

        if price <= 0:
            market_col.insert_one(listing)
            await message.reply_text(
                "❌ Listing စျေးနှုန်း မမှန်ပါ။"
            )
            return

        buyer = users_col.find_one({
            "user_id": user.id
        }) or {}

        # Support both existing balance and legacy coins
        balance = safe_int(
            buyer.get("balance", buyer.get("coins", 0))
        )

        if balance < price:

            market_col.insert_one(listing)

            await message.reply_text(
                "❌ Coins မလုံလောက်ပါ။\n"
                f"💰 လိုအပ်ချက်: {price:,}\n"
                f"💰 လက်ကျန်: {balance:,}"
            )
            return

        # Deduct using whichever field the account uses.
        balance_field = (
            "balance"
            if "balance" in buyer
            else "coins"
        )

        debit = users_col.update_one(
            {
                "user_id": user.id,
                balance_field: {"$gte": price},
            },
            {
                "$inc": {
                    balance_field: -price
                }
            },
        )

        if debit.modified_count != 1:

            market_col.insert_one(listing)

            await message.reply_text(
                "❌ Coins ဖြတ်တောက်မှု မအောင်မြင်ပါ။"
            )
            return

        # Credit seller
        seller = users_col.update_one(
            {"user_id": seller_id},
            {
                "$inc": {
                    balance_field: price
                }
            },
        )

        if seller.matched_count == 0:

            users_col.update_one(
                {"user_id": user.id},
                {"$inc": {balance_field: price}},
            )

            market_col.insert_one(listing)

            await message.reply_text(
                "❌ Seller Account မတွေ့ရှိပါ။ "
                "ငွေပြန်အမ်းပြီးပါပြီ။"
            )
            return

        # Transfer card to buyer
        card = {
            "user_id": user.id,
            "card_id": listing.get("card_id"),
            "name": listing.get("name"),
            "anime": listing.get("anime"),
            "rarity": listing.get("rarity"),
            "edition": listing.get("edition", "Normal"),
            "img_url": listing.get("img_url"),
        }

        try:
            inventory_col.insert_one(card)

        except Exception:

            # Refund buyer and seller
            users_col.update_one(
                {"user_id": user.id},
                {"$inc": {balance_field: price}},
            )

            users_col.update_one(
                {"user_id": seller_id},
                {"$inc": {balance_field: -price}},
            )

            market_col.insert_one(listing)

            raise

        await message.reply_text(
            "🎉 <b>PURCHASE SUCCESSFUL!</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
            f"🎴 Card: <b>{safe_text(listing.get('name'))}</b>\n"
            f"✨ Rarity: {safe_text(listing.get('rarity'))}\n"
            f"💰 Paid: <b>{price:,} Coins</b>\n\n"
            "🃏 Card ကို သင့် Inventory ထဲသို့ ထည့်သွင်းပြီးပါပြီ။\n"
            "━━━━━━━━━━━━━━━━━━━━",
            parse_mode=ParseMode.HTML,
        )

    except Exception:
        logger.exception("Buy command error")

        await message.reply_text(
            "❌ ဝယ်ယူရာတွင် Error ဖြစ်နေပါသည်။ "
            "Owner ထံ ဆက်သွယ်ပါ။"
        )


# ==========================================
# FAVORITE COMMAND
# ==========================================

async def fav_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    message = update.effective_message
    user = update.effective_user

    if not message or not user:
        return

    if not context.args:
        await message.reply_text(
            "🌟 အသုံးပြုပုံ:\n"
            "<code>/fav [Card ID]</code>",
            parse_mode=ParseMode.HTML,
        )
        return

    card_id = context.args[0]

    try:

        item = inventory_col.find_one({
            "user_id": user.id,
            "card_id": card_id,
        })

        if not item:
            await message.reply_text(
                "❌ သင့် Inventory ထဲတွင် ထို Card မရှိပါ။"
            )
            return

        card_name = item.get(
            "name",
            item.get("card_name", "Unknown Card"),
        )

        users_col.update_one(
            {"user_id": user.id},
            {
                "$set": {
                    "favorite_card": card_name,
                    "favorite_card_id": card_id,
                }
            },
            upsert=True,
        )

        await message.reply_text(
            "🌟 <b>FAVORITE UPDATED!</b>\n\n"
            f"🎴 Character: <b>{safe_text(card_name)}</b>\n"
            f"🆔 Card ID: <code>{safe_text(card_id)}</code>",
            parse_mode=ParseMode.HTML,
        )

    except Exception:
        logger.exception("Favorite command error")

        await message.reply_text(
            "❌ Favourite ပြောင်းလဲရာတွင် Error ဖြစ်နေပါသည်။"
        )


# ==========================================
# REGISTER HANDLERS
# ==========================================

def get_trade_market_handlers():

    return [
        CommandHandler("sell", sell_command, block=False),
        CommandHandler("market", market_command, block=False),
        CommandHandler("buy", buy_command, block=False),
        CommandHandler("fav", fav_command, block=False),
    ]
