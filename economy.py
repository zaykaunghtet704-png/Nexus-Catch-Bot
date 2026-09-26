import math
import time
from bson import ObjectId
from html import escape

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler

# သင့်ကိုယ်ပိုင် database နှင့် config ဖိုင်များမှ Import လုပ်ခြင်း
from database import users_col, inventory_col, market_col
try:
    from config import DAILY_COINS
except ImportError:
    DAILY_COINS = 500

_DAILY_COOLDOWN = 86_400   # ၂၄ နာရီ (စက္ကန့်ဖြင့်)
_PAGE = 8

# ── Helpers ───────────────────────────────────────────────────────────────────

def _fmt_time(secs: int) -> str:
    h, r = divmod(secs, 3600)
    m, s = divmod(r, 60)
    return f"{h}နာရီ {m}မိနစ် {s}စက္ကန့်" if h else (f"{m}မိနစ် {s}စက္ကန့်" if m else f"{s}စက္ကန့်")

async def _ensure_user(user_id: int, u) -> dict:
    doc = await users_col.find_one({"user_id": user_id})
    if not doc:
        doc = {
            "user_id": user_id, 
            "username": u.username,
            "first_name": u.first_name, 
            "coins": 0, 
            "xp": 0, 
            "wins": 0,
            "total_guesses": 0, 
            "favorites": [],
            "last_daily": 0
        }
        await users_col.insert_one(doc)
    return doc

# ── /balance ──────────────────────────────────────────────────────────────────

async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    u   = update.effective_user
    doc = await _ensure_user(u.id, u)
    await update.message.reply_text(
        f"💰 <b>{escape(u.first_name)}'s Balance</b>\n\n"
        f"Coins: <b>{doc.get('coins', 0):,}</b> 🪙",
        parse_mode=ParseMode.HTML,
    )

# ── /daily ────────────────────────────────────────────────────────────────────

async def daily(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    u   = update.effective_user
    doc = await _ensure_user(u.id, u)
    now = time.time()
    last = doc.get("last_daily", 0)

    if now - last < _DAILY_COOLDOWN:
        remaining = int(_DAILY_COOLDOWN - (now - last))
        await update.message.reply_text(
            f"⏳ Daily reward ရယူပြီးပါပြီ!\nနောက်ထပ် <b>{_fmt_time(remaining)}</b> ကြာမှ ပြန်လည်ရယူနိုင်ပါမည်။",
            parse_mode=ParseMode.HTML,
        )
        return

    reward = DAILY_COINS
    await users_col.update_one(
        {"user_id": u.id},
        {"$inc": {"coins": reward}, "$set": {"last_daily": now}},
    )
    current_coins = doc.get('coins', 0) + reward
    await update.message.reply_text(
        f"🎁 <b>Daily reward ရရှိပါသည်။</b>\n\n"
        f"သင် <b>{reward:,} coins</b> 🪙 ရရှိခဲ့သည်။\n"
        f"လက်ရှိ လက်ကျန်ငွေ: <b>{current_coins:,}</b> Coins",
        parse_mode=ParseMode.HTML,
    )

# ── /sell ─────────────────────────────────────────────────────────────────────

async def sell(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    u = update.effective_user
    if len(context.args) != 2:
        await update.message.reply_text(
            "အသုံးပြုပုံ: <code>/sell [card_id] [price]</code>", parse_mode=ParseMode.HTML)
        return

    char_id, price_str = context.args
    if not price_str.isdigit() or int(price_str) <= 0:
        await update.message.reply_text("❌ စျေးနှုန်းသည် အပေါင်းကိန်း သီးသန့်ဖြစ်ရပါမည်။")
        return
    price = int(price_str)

    # User Inventory ထဲတွင် ထို ကတ်ရှိမရှိ ရှာဖွေခြင်း
    item = await inventory_col.find_one({
        "user_id": u.id,
        "$or": [{"card_id": char_id}, {"id": char_id}]
    })

    if not item:
        await update.message.reply_text("❌ ထို ကတ်သည် သင့် Harem/Collection ထဲတွင် မရှိပါ။")
        return

    # User Inventory မှ ကတ်ကို ခေတ္တဖယ်ရှားခြင်း (Escrow)
    await inventory_col.delete_one({"_id": item["_id"]})

    listing = {
        "seller_id":   u.id,
        "seller_name": u.first_name,
        "card_id":     char_id,
        "char":        item,
        "price":       price,
        "listed_at":   time.time(),
    }
    result = await market_col.insert_one(listing)

    char_name = item.get("name", "Character")
    await update.message.reply_text(
        f"🏪 <b>{escape(char_name)}</b> ကို <b>{price:,} coins</b> ဖြင့် Market တွင် စာရင်းတင်လိုက်ပါပြီ!\n"
        f"Listing ID: <code>{result.inserted_id}</code>",
        parse_mode=ParseMode.HTML,
    )

# ── /market ───────────────────────────────────────────────────────────────────

async def market(update: Update, context: ContextTypes.DEFAULT_TYPE, page: int = 0) -> None:
    args  = context.args if hasattr(context, "args") and context.args else []
    if args and args[0].isdigit():
        page = int(args[0]) - 1

    total   = await market_col.count_documents({})
    if total == 0:
        await update.message.reply_text("🏪 လက်ရှိ Market ထဲတွင် ရောင်းရန် ကတ်များ မရှိသေးပါ။")
        return

    total_pages = max(1, math.ceil(total / _PAGE))
    page = max(0, min(page, total_pages - 1))

    listings = await market_col.find({}).sort("price", 1).skip(page * _PAGE).limit(_PAGE).to_list(_PAGE)

    lines = [f"🏪 <b>Marketplace</b>  (Page {page+1}/{total_pages})\n"]
    for lst in listings:
        char = lst["char"]
        rarity = char.get("rarity", "🎴")
        lines.append(
            f"{rarity}  <b>{escape(char.get('name', 'Card'))}</b>  "
            f"— <b>{lst['price']:,} 🪙</b>\n"
            f"   Seller: {escape(lst['seller_name'])}  |  "
            f"<code>/buy {lst['_id']}</code>"
        )

    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton("⬅️ Back", callback_data=f"market:{page-1}"))
    nav.append(InlineKeyboardButton(f"📖 {page+1}/{total_pages}", callback_data="noop"))
    if page < total_pages - 1:
        nav.append(InlineKeyboardButton("Next ➡️", callback_data=f"market:{page+1}"))

    kb = InlineKeyboardMarkup([nav] if nav else [])
    await update.message.reply_text("\n".join(lines), parse_mode=ParseMode.HTML, reply_markup=kb)

async def market_page_cb(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    q = update.callback_query
    await q.answer()
    page = int(q.data.split(":")[1])

    total       = await market_col.count_documents({})
    total_pages = max(1, math.ceil(total / _PAGE))
    page        = max(0, min(page, total_pages - 1))
    listings    = await market_col.find({}).sort("price", 1).skip(page * _PAGE).limit(_PAGE).to_list(_PAGE)

    lines = [f"🏪 <b>Marketplace</b>  (Page {page+1}/{total_pages})\n"]
    for lst in listings:
        char = lst["char"]
        rarity = char.get("rarity", "🎴")
        lines.append(
            f"{rarity}  <b>{escape(char.get('name', 'Card'))}</b>  "
            f"— <b>{lst['price']:,} 🪙</b>\n"
            f"   Seller: {escape(lst['seller_name'])}  |  "
            f"<code>/buy {lst['_id']}</code>"
        )

    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton("⬅️ Back", callback_data=f"market:{page-1}"))
    nav.append(InlineKeyboardButton(f"📖 {page+1}/{total_pages}", callback_data="noop"))
    if page < total_pages - 1:
        nav.append(InlineKeyboardButton("Next ➡️", callback_data=f"market:{page+1}"))
    kb = InlineKeyboardMarkup([nav] if nav else [])
    try:
        await q.edit_message_text("\n".join(lines), parse_mode=ParseMode.HTML, reply_markup=kb)
    except Exception:
        pass

# ── /buy ──────────────────────────────────────────────────────────────────────

async def buy(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    u = update.effective_user
    if not context.args:
        await update.message.reply_text("အသုံးပြုပုံ: <code>/buy [listing_id]</code>", parse_mode=ParseMode.HTML)
        return

    try:
        oid = ObjectId(context.args[0])
    except Exception:
        await update.message.reply_text("❌ Listing ID မှားယွင်းနေပါသည်။")
        return

    listing = await market_col.find_one({"_id": oid})
    if not listing:
        await update.message.reply_text("❌ ထို ကတ်ကို ရှာမတွေ့ပါ (သို့) ဝယ်ယူသွားပြီးဖြစ်ပါသည်။")
        return

    if listing["seller_id"] == u.id:
        await update.message.reply_text("❌ မိမိကိုယ်ပိုင် ရောင်းရန်တင်ထားသော ကတ်ကို ပြန်ဝယ်၍ မရပါ။")
        return

    buyer = await _ensure_user(u.id, u)
    if buyer.get("coins", 0) < listing["price"]:
        await update.message.reply_text(
            f"❌ Coin မလုံလောက်ပါ။ လိုအပ်သော ပမာဏ: <b>{listing['price']:,}</b> Coins.",
            parse_mode=ParseMode.HTML,
        )
        return

    # Atomic Transaction (Coins လွှဲပြောင်းခြင်း နှင့် Inventory ထဲ ကတ်ထည့်ပေးခြင်း)
    await users_col.update_one({"user_id": u.id}, {"$inc": {"coins": -listing["price"]}})
    await users_col.update_one({"user_id": listing["seller_id"]}, {"$inc": {"coins": listing["price"]}})

    # ဝယ်ယူသူ၏ Inventory ထဲသို့ ကတ်သစ်အဖြစ် ထည့်သွင်းခြင်း
    new_item = listing["char"]
    new_item["user_id"] = u.id
    if "_id" in new_item:
        del new_item["_id"]  # ID အသစ်ထုတ်ပေးနိုင်ရန် _id ကို ဖျက်သည်

    await inventory_col.insert_one(new_item)
    await market_col.delete_one({"_id": oid})

    char_name = new_item.get("name", "Character")
    await update.message.reply_text(
        f"✅ <b>{escape(char_name)}</b> ကို <b>{listing['price']:,} 🪙</b> ဖြင့် အောင်မြင်စွာ ဝယ်ယူလိုက်ပါပြီ!",
        parse_mode=ParseMode.HTML,
    )

# ── /delist ───────────────────────────────────────────────────────────────────

async def delist(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    u = update.effective_user
    if not context.args:
        await update.message.reply_text("အသုံးပြုပုံ: <code>/delist [listing_id]</code>", parse_mode=ParseMode.HTML)
        return

    try:
        oid = ObjectId(context.args[0])
    except Exception:
        await update.message.reply_text("❌ Listing ID မှားယွင်းနေပါသည်။")
        return

    listing = await market_col.find_one({"_id": oid})
    if not listing:
        await update.message.reply_text("❌ Listing ရှာမတွေ့ပါ။")
        return
        
    if listing["seller_id"] != u.id:
        await update.message.reply_text("❌ ဤ Listing သည် သင့်ပိုင်ဆိုင်မှု မဟုတ်ပါ။")
        return

    # Market မှ ဖျက်ပြီး Inventory ထဲ ပြန်ထည့်ပေးခြင်း
    restored_item = listing["char"]
    restored_item["user_id"] = u.id
    if "_id" in restored_item:
        del restored_item["_id"]

    await market_col.delete_one({"_id": oid})
    await inventory_col.insert_one(restored_item)

    await update.message.reply_text("✅ Market စာရင်းမှ ပယ်ဖျက်လိုက်ပါပြီ။ ကတ်ကို သင့် Harem ထဲသို့ ပြန်လည်ထည့်သွင်းပေးထားပါသည်။")

# ── Handlers များကို Main File သို့ လှမ်းပေးရန် ────────────────────────────────
def get_economy_handlers():
    return [
        CommandHandler("balance", balance, block=False),
        CommandHandler("daily",   daily,   block=False),
        CommandHandler("sell",    sell,    block=False),
        CommandHandler("market",  market,  block=False),
        CommandHandler("buy",     buy,     block=False),
        CommandHandler("delist",  delist,  block=False),
        CallbackQueryHandler(market_page_cb, pattern=r"^market:\d+$", block=False)
    ]
