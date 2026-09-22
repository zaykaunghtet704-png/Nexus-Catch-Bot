from telegram import Update
from telegram.ext import ContextTypes
from database import users_col, inventory_col, market_col
import datetime

async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_data = users_col.find_one({"user_id": user.id})
    
    if not user_data:
        coins = 0
    else:
        coins = user_data.get("balance", 0)
        
    await update.message.reply_text(f"💰 {user.first_name} ၏ လက်ကျန်ငွေ: **{coins} Coins**", parse_mode="Markdown")

async def daily_reward(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    
    user_data = users_col.find_one({"user_id": user_id})
    if not user_data:
        users_col.insert_one({"user_id": user_id, "username": user.username or user.first_name, "balance": 100})
        user_data = users_col.find_one({"user_id": user_id})

    last_claim = user_data.get("last_daily")
    now = datetime.datetime.utcnow()

    if last_claim and (now - last_claim).total_seconds() < 86400:
        remaining_hours = int((86400 - (now - last_claim).total_seconds()) / 3600)
        await update.message.reply_text(f"⏳ နေ့စဉ်ဆုလာဘ်ကို ထပ်ယူရန် နောက်ထပ် {remaining_hours} နာရီခန့် စောင့်ဆိုင်းပါဦး။")
        return

    reward = 200
    users_col.update_one(
        {"user_id": user_id},
        {
            "$inc": {"balance": reward},
            "$set": {"last_daily": now}
        }
    )
    
    await update.message.reply_text(f"🎁 {user.first_name} ရေ! နေ့စဉ်ဆုလာဘ်အဖြစ် **{reward} Coins** ကို ရရှိသွားပါပြီ။")

async def sell_card(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not context.args or len(context.args) < 2:
        await update.message.reply_text("⚠️ ကျေးဇူးပြု၍ ပုံစံမှန်ကန်စွာ ရေးပါ (ဥပမာ - `/sell [Card ID] [ဈေးနှုန်း]`)")
        return

    card_id = context.args[0]
    try:
        price = int(context.args[1])
    except ValueError:
        await update.message.reply_text("❌ ဈေးနှုန်းသည် နံပါတ်ဖြစ်ရပါမည်။")
        return

    card = inventory_col.find_one({"user_id": user.id, "card_id": card_id})
    if not card:
        await update.message.reply_text("❌ သင့်ထံတွင် ဤ Card ID ရှိသော ကတ် မရှိပါ။")
        return

    market_col.insert_one({
        "seller_id": user.id,
        "seller_name": user.first_name,
        "card_id": card_id,
        "name": card['name'],
        "anime": card['anime'],
        "rarity": card['rarity'],
        "price": price
    })

    inventory_col.delete_one({"_id": card["_id"]})

    await update.message.reply_text(f"🛍️ `{card['name']}` ကတ်ကို ဈေးကွက်ထဲသို့ **{price} Coins** ဖြင့် အောင်မြင်စွာ တင်လိုက်ပါပြီ။", parse_mode="Markdown")

async def view_market(update: Update, context: ContextTypes.DEFAULT_TYPE):
    market_items = list(market_col.find({}))
    if not market_items:
        await update.message.reply_text("🏷️ လက်ရှိ ဈေးကွက်အတွင်း အရောင်းတင်ထားသော ကတ်များ မရှိသေးပါ။")
        return

    market_text = "🛒 **Waifu Marketplace ဈေးကွက်စာရင်း** 🛒\n\n"
    for item in market_items:
        market_text += (
            f"🔹 **{item['name']}** ({item['anime']}) - `[{item['rarity']}]`\n"
            f"   💰 ဈေးနှုန်း: {item['price']} Coins\n"
            f"   🆔 ID: `{item['card_id']}` | ရောင်းသူ: {item['seller_name']}\n\n"
        )
    
    await update.message.reply_text(market_text, parse_mode="Markdown")
