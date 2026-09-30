"""
modules/extra_commands.py - Missing Command Handlers
"""
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import CommandHandler, ContextTypes
from database import users_col, inventory_col, cards_col

async def profile_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_data = users_col.find_one({"user_id": user.id}) or {}
    
    balance = user_data.get("balance", 0)
    gems = user_data.get("gems", 0)
    cards_count = inventory_col.count_documents({"user_id": user.id})

    text = (
        f"👤 <b>{user.first_name}'s Profile</b>\n"
        f"─────────────────────────\n"
        f"🆔 <b>User ID:</b> <code>{user.id}</code>\n"
        f"💰 <b>Coins:</b> {balance:,}\n"
        f"💎 <b>Gems:</b> {gems:,}\n"
        f"🃏 <b>Total Cards:</b> {cards_count}\n"
    )
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)

async def balance_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_data = users_col.find_one({"user_id": user.id}) or {}
    balance = user_data.get("balance", 0)
    gems = user_data.get("gems", 0)

    text = (
        f"💰 <b>{user.first_name}'s Balance</b>\n"
        f"─────────────────────────\n"
        f"🪙 <b>Coins:</b> {balance:,}\n"
        f"💎 <b>Gems:</b> {gems:,}\n"
    )
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)

async def search_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❓ ရှာဖွေလိုသော Character အမည်ကို ထည့်ပေးပါ။\nဥပမာ - <code>/search Naruto</code>", parse_mode=ParseMode.HTML)
        return
        
    query = " ".join(context.args)
    results = list(cards_col.find({"name": {"$regex": query, "$options": "i"}}).limit(5))
    
    if not results:
        await update.message.reply_text("❌ မည်သည့် Character မျှ မတွေ့ရှိပါ။")
        return
        
    text = f"🔍 <b>'{query}' ရှာဖွေမှု ရလဒ်များ:</b>\n\n"
    for c in results:
        text += f"• <b>{c.get('name')}</b> (Anime: {c.get('anime', 'Unknown')})\n"
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)

async def top_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pipeline = [
        {"$group": {"_id": "$user_id", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 10}
    ]
    top_users = list(inventory_col.aggregate(pipeline))
    
    if not top_users:
        await update.message.reply_text("🏆 မည်သည့် Collector မျှ ကတ်မရှိသေးပါ။")
        return

    text = "🏆 <b>TOP 10 COLLECTORS</b>\n─────────────────────────\n"
    for idx, u in enumerate(top_users, 1):
        text += f"{idx}. User ID <code>{u['_id']}</code> — <b>{u['count']} Cards</b>\n"
        
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)

async def ctop_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pipeline = [
        {"$group": {"_id": "$card_name", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 10}
    ]
    top_cards = list(inventory_col.aggregate(pipeline))
    
    if not top_cards:
        await update.message.reply_text("📊 မည်သည့် ကတ်မျှ မဖမ်းရသေးပါ။")
        return

    text = "📊 <b>TOP MOST CAUGHT CHARACTERS</b>\n─────────────────────────\n"
    for idx, c in enumerate(top_cards, 1):
        text += f"{idx}. <b>{c['_id']}</b> — {c['count']} times caught\n"
        
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)

async def ranking_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    top_users = list(users_col.find().sort("balance", -1).limit(10))
    
    text = "🌐 <b>GLOBAL COIN RANKING</b>\n─────────────────────────\n"
    for idx, u in enumerate(top_users, 1):
        name = u.get("first_name", "User")
        bal = u.get("balance", 0)
        text += f"{idx}. <b>{name}</b> — 💰 {bal:,} Coins\n"
        
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)

async def gift_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🎁 <b>Gift Feature:</b>\nအခြားသူအား ကတ် သို့မဟုတ် Coins ပေးပို့ရန် Reply ရိုက်၍ <code>/gift &lt;amount/card_id&gt;</code> ဟု အသုံးပြုပါ၊", parse_mode=ParseMode.HTML)

async def check_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❓ စစ်ဆေးလိုသော Character / Card ID ကို ထည့်ပါ။\nဥပမာ - <code>/check Naruto</code>", parse_mode=ParseMode.HTML)
        return
        
    card_name = " ".join(context.args)
    card = cards_col.find_one({"name": {"$regex": card_name, "$options": "i"}})
    
    if not card:
        await update.message.reply_text("❌ Character မတွေ့ရှိပါ။")
        return
        
    text = (
        f"🔍 <b>CHARACTER INFO</b>\n"
        f"─────────────────────────\n"
        f"👤 <b>Name:</b> {card.get('name')}\n"
        f"📺 <b>Anime:</b> {card.get('anime', 'N/A')}\n"
        f"⭐ <b>Rarity:</b> {card.get('rarity', 'Common')}\n"
    )
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)

def get_extra_handlers():
    return [
        CommandHandler("profile", profile_command),
        CommandHandler("balance", balance_command),
        CommandHandler("search", search_command),
        CommandHandler("top", top_command),
        CommandHandler("ctop", ctop_command),
        CommandHandler("ranking", ranking_command),
        CommandHandler("gift", gift_command),
        CommandHandler("check", check_command),
    ]
