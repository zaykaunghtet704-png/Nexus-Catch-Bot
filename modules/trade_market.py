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
from datetime import datetime, timezone
from html import escape


from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import (
    CommandHandler,
    ContextTypes,
)

from database import (
    atomic, inventory_col,
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

        with atomic():
            item = inventory_col.find_one({
                "user_id": user.id,
                "$or": [{"card_id": card_id}, {"id": card_id}],
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
                "card_id": item.get("card_id") or item.get("id"),
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

        # Optional filters: /market rarity=Legendary anime=Naruto min=100 max=5000
        rarity_filter = None
        anime_filter = None
        min_price = None
        max_price = None
        for arg in context.args:
            key, sep, value = arg.partition("=")
            if not sep:
                rarity_filter = arg.strip().lower()
                continue
            key, value = key.lower(), value.strip()
            if key == "rarity":
                rarity_filter = value.lower()
            elif key == "anime":
                anime_filter = value.lower()
            elif key == "min":
                min_price = safe_int(value, -1)
            elif key == "max":
                max_price = safe_int(value, -1)

        all_listings = list(market_col.find().sort("_id", -1))
        listings = []
        for entry in all_listings:
            price_value = safe_int(entry.get("price", 0))
            if rarity_filter and rarity_filter not in str(entry.get("rarity", "")).lower():
                continue
            if anime_filter and anime_filter not in str(entry.get("anime", "")).lower():
                continue
            if min_price is not None and (min_price < 0 or price_value < min_price):
                continue
            if max_price is not None and (max_price < 0 or price_value > max_price):
                continue
            listings.append(entry)
            if len(listings) >= 10:
                break

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
            "🛒 <b>BUY CARD</b>\n\nအသုံးပြုပုံ: <code>/buy [Market ID]</code>",
            parse_mode=ParseMode.HTML,
        )
        return

    market_id = context.args[0].strip()
    class BuyAbort(Exception):
        pass

    try:
        with atomic():
            # Keep the original listing row locked until payment and transfer finish.
            listing = market_col.find_one_for_update({
                "_id": market_id,
                "seller_id": {"$ne": user.id},
            })
            if not listing:
                raise BuyAbort("❌ Market ID မရှိတော့ပါ သို့မဟုတ် မိမိ Card ကို ပြန်ဝယ်ရန် ကြိုးစားနေပါသည်။")

            price = safe_int(listing.get("price", 0), -1)
            if price <= 0:
                raise BuyAbort("❌ Listing စျေးနှုန်း မမှန်ပါ။")

            buyer = users_col.find_one({"user_id": user.id}) or {}
            buyer_field = "coins" if "coins" in buyer else "balance"
            balance = safe_int(buyer.get(buyer_field, 0))
            if balance < price:
                raise BuyAbort(
                    "❌ Coins မလုံလောက်ပါ။\n"
                    f"💰 လိုအပ်ချက်: {price:,}\n💰 လက်ကျန်: {balance:,}"
                )

            seller_id = listing.get("seller_id")
            seller_doc = users_col.find_one({"user_id": seller_id})
            if not seller_doc:
                raise BuyAbort("❌ Seller Account မတွေ့ပါ။ Owner ထံ အသိပေးပါ။")
            seller_field = "coins" if "coins" in seller_doc else "balance"

            debit = users_col.update_one(
                {"user_id": user.id, buyer_field: {"$gte": price}},
                {"$inc": {buyer_field: -price}},
            )
            if debit.modified_count != 1:
                raise BuyAbort("❌ Coins ဖြတ်တောက်မှု မအောင်မြင်ပါ။ ထပ်မံကြိုးစားပါ။")

            credit = users_col.update_one(
                {"user_id": seller_id},
                {"$inc": {seller_field: price}},
            )
            if credit.matched_count != 1:
                raise BuyAbort("❌ Seller ထံ ငွေလွှဲမရပါ။")

            card_id = listing.get("card_id") or listing.get("id")
            inventory_col.insert_one({
                "user_id": user.id,
                "card_id": card_id,
                "name": listing.get("name") or listing.get("card_name") or "Unknown Card",
                "anime": listing.get("anime", "Unknown"),
                "rarity": listing.get("rarity", "Common"),
                "edition": listing.get("edition", "Normal"),
                "img_url": listing.get("img_url") or listing.get("image"),
                "obtained_at": datetime.now(timezone.utc).isoformat(),
            })
            removed = market_col.delete_one({"_id": market_id})
            if removed.deleted_count != 1:
                raise BuyAbort("❌ Listing ကို အတည်ပြုမဖယ်ရှားနိုင်ပါ။")

    except BuyAbort as exc:
        await message.reply_text(str(exc))
        return
    except Exception:
        logger.exception("Buy command error")
        await message.reply_text("❌ ဝယ်ယူမှု မအောင်မြင်ပါ။ ငွေ/ကတ် ပြောင်းလဲမှုများကို Database Transaction ဖြင့် ပြန်လည်ကာကွယ်ထားပါသည်။")
        return

    await message.reply_text(
        "🎉 <b>PURCHASE SUCCESSFUL!</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        f"🎴 Card: <b>{safe_text(listing.get('name') or listing.get('card_name'))}</b>\n"
        f"✨ Rarity: {safe_text(listing.get('rarity'))}\n"
        f"💰 Paid: <b>{price:,} Coins</b>\n\n"
        "🃏 Card ကို သင့် Inventory ထဲသို့ ထည့်သွင်းပြီးပါပြီ။\n"
        "━━━━━━━━━━━━━━━━━━━━",
        parse_mode=ParseMode.HTML,
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
