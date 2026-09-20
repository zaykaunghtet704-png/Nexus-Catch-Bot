"""
modules/economy.py — Daily coins, balance, and marketplace.
"""
import math
import time
from bson import ObjectId
from html import escape

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.ext import CallbackContext, CallbackQueryHandler, CommandHandler

from waifu import application, user_collection, market_collection
from waifu.config import Config

_DAILY_COOLDOWN = 86_400   # 24 hours in seconds
_PAGE = 8

# ── Helpers ───────────────────────────────────────────────────────────────────

def _fmt_time(secs: int) -> str:
    h, r = divmod(secs, 3600)
    m, s = divmod(r, 60)
    return f"{h}h {m}m {s}s" if h else (f"{m}m {s}s" if m else f"{s}s")


async def _ensure_user(user_id: int, u) -> dict:
    doc = await user_collection.find_one({"$or": [{"id": user_id}, {"user_id": user_id}]})
    if not doc:
        doc = {
            "id": user_id,
            "user_id": user_id,
            "username": u.username,
            "first_name": u.first_name,
            "characters": [],
            "coins": 0,
            "xp": 0,
            "wins": 0,
            "total_guesses": 0,
            "favorites": [],
        }
        await user_collection.insert_one(doc)
    return doc


# ── /balance ──────────────────────────────────────────────────────────────────

async def balance(update: Update, context: CallbackContext) -> None:
    u = update.effective_user
    doc = await _ensure_user(u.id, u)
    await update.message.reply_text(
        f"💰 <b>{escape(u.first_name)}'s Balance</b>\n\n"
        f"Coins: <b>{doc.get('coins', 0):,}</b> 🪙",
        parse_mode=ParseMode.HTML,
    )


# ── /daily ────────────────────────────────────────────────────────────────────

async def daily(update: Update, context: CallbackContext) -> None:
    u = update.effective_user
    doc = await _ensure_user(u.id, u)
    now = time.time()
    last = doc.get("last_daily", 0)

    if now - last < _DAILY_COOLDOWN:
        remaining = int(_DAILY_COOLDOWN - (now - last))
        await update.message.reply_text(
            f"⏳ Daily reward ကို ရယူပြီးဖြစ်ပါသည်!\n<b>{_fmt_time(remaining)}</b> ကြာမှ ပြန်လည်ရယူနိုင်ပါမည်။",
            parse_mode=ParseMode.HTML,
        )
        return

    reward = getattr(Config, "DAILY_COINS", 200)
    await user_collection.update_one(
        {"$or": [{"id": u.id}, {"user_id": u.id}]},
        {"$inc": {"coins": reward}, "$set": {"last_daily": now}},
    )
    await update.message.reply_text(
        f"🎁 <b>Daily Reward ရရှိပါပြီ!</b>\n\n"
        f"သင် <b>{reward:,} coins</b> 🪙 ရရှိခဲ့ပါသည်။\n"
        f"လက်ရှိ လက်ကျန်ငွေ: <b>{doc.get('coins', 0) + reward:,} coins</b>",
        parse_mode=ParseMode.HTML,
    )


# ── /sell ─────────────────────────────────────────────────────────────────────

async def sell(update: Update, context: CallbackContext) -> None:
    u = update.effective_user
    if len(context.args) != 2:
        await update.message.reply_text(
            "<b>အသုံးပြုနည်း:</b> <code>/sell [char_id] [price]</code>", parse_mode=ParseMode.HTML
        )
        return

    char_id, price_str = context.args
    if not price_str.isdigit() or int(price_str) <= 0:
        await update.message.reply_text("❌ စေးနှုန်းသည် အပေါင်းကိန်း သီးသန့်ဖြစ်ရပါမည်။")
        return
    price = int(price_str)

    doc = await user_collection.find_one({"$or": [{"id": u.id}, {"user_id": u.id}]})
    if not doc:
        await update.message.reply_text("❌ သင့်ထံတွင် Character မရှိသေးပါ။")
        return

    char = next((c for c in doc.get("characters", []) if str(c.get("id")) == str(char_id)), None)
    if not char:
        await update.message.reply_text("❌ ထို Character သည် သင့် Harem ထဲတွင် မရှိပါ။")
        return

    # Escrow: remove from user's characters list while listed
    await user_collection.update_one(
        {"$or": [{"id": u.id}, {"user_id": u.id}]},
        {"$pull": {"characters": {"id": char["id"]}}},
    )
    listing = {
        "seller_id": u.id,
        "seller_name": u.first_name,
        "char_id": char["id"],
        "char": char,
        "price": price,
        "listed_at": time.time(),
    }
    result = await market_collection.insert_one(listing)

    await update.message.reply_text(
        f"🏪 <b>{escape(char['name'])}</b> ကို <b>{price:,} coins</b> ဖြင့် Market ပေါ် တင်ပြီးပါပြီ!\n"
        f"Listing ID: <code>{result.inserted_id}</code>",
        parse_mode=ParseMode.HTML,
    )


# ── /market ───────────────────────────────────────────────────────────────────

async def market(update: Update, context: CallbackContext, page: int = 0) -> None:
    args = context.args if hasattr(context, "args") and context.args else []
    if args and args[0].isdigit():
        page = int(args[0]) - 1

    total = await market_collection.count_documents({})
    if total == 0:
        await update.message.reply_text("🏪 စျေးကွက်ထဲတွင် ရောင်းရန် မရှိသေးပါ။")
        return

    total_pages = max(1, math.ceil(total / _PAGE))
    page = max(0, min(page, total_pages - 1))

    listings = await market_collection.find({}).sort("price", 1).skip(page * _PAGE).limit(_PAGE).to_list(_PAGE)

    lines = [f"🏪 <b>Marketplace</b>  (Page {page+1}/{total_pages})\n"]
    for lst in listings:
        char = lst["char"]
        lines.append(
            f"{char.get('rarity','🎴')}  <b>{escape(char['name'])}</b>  "
            f"— <b>{lst['price']:,} 🪙</b>\n"
            f"   Seller: {escape(lst['seller_name'])}  |  "
            f"<code>/buy {lst['_id']}</code>\n"
        )

    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton("⬅️", callback_data=f"market:{page-1}"))
    nav.append(InlineKeyboardButton(f"{page+1}/{total_pages}", callback_data="noop"))
    if page < total_pages - 1:
        nav.append(InlineKeyboardButton("➡️", callback_data=f"market:{page+1}"))

    kb = InlineKeyboardMarkup([nav] if nav else [])
    await update.message.reply_text(
        "\n".join(lines), parse_mode=ParseMode.HTML, reply_markup=kb
    )


async def market_page_cb(update: Update, context: CallbackContext) -> None:
    q = update.callback_query
    await q.answer()
    page = int(q.data.split(":")[1])

    total = await market_collection.count_documents({})
    total_pages = max(1, math.ceil(total / _PAGE))
    page = max(0, min(page, total_pages - 1))
    listings = await market_collection.find({}).sort("price", 1).skip(page * _PAGE).limit(_PAGE).to_list(_PAGE)

    lines = [f"🏪 <b>Marketplace</b>  (Page {page+1}/{total_pages})\n"]
    for lst in listings:
        char = lst["char"]
        lines.append(
            f"{char.get('rarity','🎴')}  <b>{escape(char['name'])}</b>  "
            f"— <b>{lst['price']:,} 🪙</b>\n"
            f"   Seller: {escape(lst['seller_name'])}  |  "
            f"<code>/buy {lst['_id']}</code>\n"
        )

    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton("⬅️", callback_data=f"market:{page-1}"))
    nav.append(InlineKeyboardButton(f"{page+1}/{total_pages}", callback_data="noop"))
    if page < total_pages - 1:
        nav.append(InlineKeyboardButton("➡️", callback_data=f"market:{page+1}"))
    kb = InlineKeyboardMarkup([nav])
    try:
        await q.edit_message_text("\n".join(lines), parse_mode=ParseMode.HTML, reply_markup=kb)
    except Exception:
        pass


# ── /buy ──────────────────────────────────────────────────────────────────────

async def buy(update: Update, context: CallbackContext) -> None:
    u = update.effective_user
    if not context.args:
        await update.message.reply_text("<b>အသုံးပြုနည်း:</b> <code>/buy [listing_id]</code>", parse_mode=ParseMode.HTML)
        return

    try:
        oid = ObjectId(context.args[0])
    except Exception:
        await update.message.reply_text("❌ Listing ID မမှန်ကန်ပါ။")
        return

    listing = await market_collection.find_one({"_id": oid})
    if not listing:
        await update.message.reply_text("❌ စျေးကွက်ထဲတွင် မရှိတော့ပါ။ (သို့) ရောင်းထွက်သွားပါပြီ။")
        return
    if listing["seller_id"] == u.id:
        await update.message.reply_text("❌ မိမိကိုယ်တိုင် တင်ထားသော ပစ္စည်းကို ပြန်ဝယ်၍ မရပါ။")
        return

    buyer = await _ensure_user(u.id, u)
    if buyer.get("coins", 0) < listing["price"]:
        await update.message.reply_text(
            f"❌ Coins မလုံလောက်ပါ။ လိုအပ်သော ငွေပမာဏ: <b>{listing['price']:,} 🪙</b>",
            parse_mode=ParseMode.HTML,
        )
        return

    # Atomic exchange
    await user_collection.update_one(
        {"$or": [{"id": u.id}, {"user_id": u.id}]},
        {"$inc": {"coins": -listing["price"]}, "$push": {"characters": listing["char"]}},
    )
    await user_collection.update_one(
        {"$or": [{"id": listing["seller_id"]}, {"user_id": listing["seller_id"]}]},
        {"$inc": {"coins": listing["price"]}},
    )
    await market_collection.delete_one({"_id": oid})

    char = listing["char"]
    await update.message.reply_text(
        f"✅ <b>{escape(char['name'])}</b> ကို <b>{listing['price']:,} 🪙</b> ဖြင့် အောင်မြင်စွာ ဝယ်ယူလိုက်ပါပြီ!",
        parse_mode=ParseMode.HTML,
    )


# ── /delist ───────────────────────────────────────────────────────────────────

async def delist(update: Update, context: CallbackContext) -> None:
    u = update.effective_user
    if not context.args:
        await update.message.reply_text("<b>အသုံးပြုနည်း:</b> <code>/delist [listing_id]</code>", parse_mode=ParseMode.HTML)
        return

    try:
        oid = ObjectId(context.args[0])
    except Exception:
        await update.message.reply_text("❌ Listing ID မမှန်ကန်ပါ။")
        return

    listing = await market_collection.find_one({"_id": oid})
    if not listing:
        await update.message.reply_text("❌ Listing မတွေ့ရှိပါ။")
        return
    if listing["seller_id"] != u.id:
        await update.message.reply_text("❌ သင့်ပစ္စည်း မဟုတ်ပါ။")
        return

    await market_collection.delete_one({"_id": oid})
    await user_collection.update_one(
        {"$or": [{"id": u.id}, {"user_id": u.id}]},
        {"$push": {"characters": listing["char"]}},
    )
    await update.message.reply_text("✅ Market ပေါ်မှ ပြန်ဖြုတ်ပြီး Character ကို သင့် Harem သို့ ပြန်ထည့်ပေးလိုက်ပါပြီ။")


application.add_handler(CommandHandler(["balance", "bal"], balance, block=False))
application.add_handler(CommandHandler("daily", daily, block=False))
application.add_handler(CommandHandler("sell", sell, block=False))
application.add_handler(CommandHandler(["market", "m"], market, block=False))
application.add_handler(CommandHandler("buy", buy, block=False))
application.add_handler(CommandHandler("delist", delist, block=False))
application.add_handler(CallbackQueryHandler(market_page_cb, pattern=r"^market:\d+$", block=False))
