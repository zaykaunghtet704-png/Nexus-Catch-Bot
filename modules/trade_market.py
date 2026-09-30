from html import escape
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import CommandHandler, ContextTypes, CallbackQueryHandler

from database import inventory_col, market_col, users_col, db

wishlist_col = db["wishlist"]

# ── 1. Marketplace & Selling ──────────────────────────────────────────────────

async def sell_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/sell [Card ID] [Price in Coins]"""
    user_id = int(update.effective_user.id)

    if len(context.args) < 2 or not context.args[1].isdigit():
        await update.message.reply_text(
            "❌ <b>အသုံးပြုပုံ:</b> <code>/sell [Card ID] [Coins စျေးနှုန်း]</code>\nဥပမာ: <code>/sell 0001 5000</code>",
            parse_mode=ParseMode.HTML
        )
        return

    card_id = context.args[0]
    price = int(context.args[1])

    if price <= 0:
        await update.message.reply_text("❌ စျေးနှုန်းသည် 0 ထက် ကြီးရပါမည်။")
        return

    item = inventory_col.find_one({"user_id": user_id, "card_id": card_id})
    if not item:
        await update.message.reply_text("❌ သင့်ထံတွင် ထို ID ဖြင့် ကတ်မရှိပါ။")
        return

    # Delete from seller inventory and put into market
    inventory_col.delete_one({"_id": item["_id"]})
    market_listing = {
        "seller_id": user_id,
        "seller_name": update.effective_user.first_name,
        "card_id": item["card_id"],
        "name": item["name"],
        "anime": item["anime"],
        "rarity": item["rarity"],
        "img_url": item.get("img_url"),
        "price": price
    }
    res = market_col.insert_one(market_listing)

    await update.message.reply_text(
        f"🛒 <b>{item['name']}</b> ကို Market တွင် <b>{price:,} Coins</b> ဖြင့် ရောင်းချရန် တင်လိုက်ပါပြီ!\n"
        f"Market ID: <code>{res.inserted_id}</code>",
        parse_mode=ParseMode.HTML
    )

async def market_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/market - Global Marketplace ကြည့်ရန်"""
    listings = list(market_col.find().limit(10))

    if not listings:
        await update.message.reply_text("🛒 <b>Marketplace တွင် လက်ရှိ ရောင်းရန် တင်ထားသော ကတ်များ မရှိသေးပါ။</b>", parse_mode=ParseMode.HTML)
        return

    text = "🛒 <b>GLOBAL MARKETPLACE</b>\n⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n"
    for item in listings:
        text += (
            f"🎴 <b>{escape(item['name'])}</b> ({item['rarity']})\n"
            f"📺 {escape(item['anime'])}\n"
            f"💰 Price: <b>{item['price']:,} Coins</b> | Seller: {escape(item['seller_name'])}\n"
            f"🆔 Market ID: <code>{item['_id']}</code>\n\n"
        )
    text += "ဝယ်ယူရန် <code>/buy [Market ID]</code> ဟု ရိုက်ပါ။"
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)

async def buy_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/buy [Market ID]"""
    buyer_id = int(update.effective_user.id)
    if not context.args:
        await update.message.reply_text("❌ ဝယ်ယူလိုသော Market ID ကို ထည့်ပါ: <code>/buy [Market_ID]</code>", parse_mode=ParseMode.HTML)
        return

    from bson import ObjectId
    try:
        market_id = ObjectId(context.args[0])
        listing = market_col.find_one({"_id": market_id})
    except Exception:
        listing = None

    if not listing:
        await update.message.reply_text("❌ ထို Market ID ဖြင့် ပစ္စည်း ရှာမတွေ့ပါ။")
        return

    if listing["seller_id"] == buyer_id:
        await update.message.reply_text("❌ မိမိကိုယ်ပိုင် တင်ရောင်းထားသော ကတ်ကို ပြန်ဝယ်၍ မရပါ။")
        return

    buyer = users_col.find_one({"user_id": buyer_id}) or {"coins": 0}
    if buyer.get("coins", 0) < listing["price"]:
        await update.message.reply_text("❌ သင့်ထံတွင် ဝယ်ယူရန် Coins မလုံလောက်ပါ။")
        return

    # Transaction
    users_col.update_one({"user_id": buyer_id}, {"$inc": {"coins": -listing["price"]}})
    users_col.update_one({"user_id": listing["seller_id"]}, {"$inc": {"coins": listing["price"]}})

    # Add to Buyer Inventory & Remove from Market
    inventory_col.insert_one({
        "user_id": buyer_id,
        "card_id": listing["card_id"],
        "name": listing["name"],
        "anime": listing["anime"],
        "rarity": listing["rarity"],
        "img_url": listing.get("img_url")
    })
    market_col.delete_one({"_id": market_id})

    await update.message.reply_text(
        f"🎉 <b>{listing['name']}</b> အား <b>{listing['price']:,} Coins</b> ဖြင့် အောင်မြင်စွာ ဝယ်ယူလိုက်ပါပြီ!",
        parse_mode=ParseMode.HTML
    )

# ── 2. Favorite & Wishlist ─────────────────────────────────────────────────────

async def fav_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/fav [Card ID] - Profile တွင် ပြသမည့် Favourite Character သတ်မှတ်ရန်"""
    user_id = int(update.effective_user.id)
    if not context.args:
        await update.message.reply_text("❌ <code>/fav [Card ID]</code> ဟု ရိုက်ပါ", parse_mode=ParseMode.HTML)
        return

    card_id = context.args[0]
    item = inventory_col.find_one({"user_id": user_id, "card_id": card_id})
    if not item:
        await update.message.reply_text("❌ သင့် Inventory ထဲတွင် ထိုကတ် မရှိပါ။")
        return

    users_col.update_one({"user_id": user_id}, {"$set": {"favorite_card": item["name"]}}, upsert=True)
    await update.message.reply_text(f"🌟 <b>{item['name']}</b> အား သင့် Favourite Character အဖြစ် သတ်မှတ်လိုက်ပါပြီ!", parse_mode=ParseMode.HTML)

def get_trade_market_handlers():
    return [
        CommandHandler("sell", sell_command, block=False),
        CommandHandler("market", market_command, block=False),
        CommandHandler("buy", buy_command, block=False),
        CommandHandler("fav", fav_command, block=False)
    ]
