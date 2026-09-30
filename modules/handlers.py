"""
modules/handlers.py - Harem, Market, Profile & Game Commands
"""
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes
from database import users_col, cards_col, inventory_col, market_col

async def profile_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_data = users_col.find_one({"user_id": user.id}) or {}
    
    balance = user_data.get("balance", 0)
    gems = user_data.get("gems", 0)
    cards_count = inventory_col.count_documents({"user_id": user.id})

    text = (
        f"👤 <b>{user.first_name}'s Profile</b>\n"
        f"─────────────────────────\n"
        f"💰 <b>Coins:</b> {balance:,}\n"
        f"💎 <b>Gems:</b> {gems:,}\n"
        f"🃏 <b>Total Cards:</b> {cards_count}\n"
    )
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)

async def harem_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_cards = list(inventory_col.find({"user_id": user.id}))
    
    if not user_cards:
        await update.message.reply_text("🧧 သင့်တွင် မည်သည့် ကတ်မျှ မရှိသေးပါ။ `/catch` ဖြင့် ဖမ်းယူပါ။")
        return
        
    text = f"🏰 <b>{user.first_name}'s Harem Collection ({len(user_cards)})</b>\n\n"
    for item in user_cards[:10]: # Top 10 ရေးပြခြင်း
        text += f"• {item.get('card_name', 'Unknown Card')} [Rarity: {item.get('rarity', 'Common')}]\n"
        
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)

async def search_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❓ ရှာဖွေလိုသော Character အမည်ကို ထည့်ပါ:\nဥပမာ - `/search Naruto`", parse_mode=ParseMode.HTML)
        return
        
    query = " ".join(context.args)
    results = list(cards_col.find({"name": {"$regex": query, "$options": "i"}}).limit(5))
    
    if not results:
        await update.message.reply_text("❌ ရှာဖွေမှု မတွေ့ရှိပါ။")
        return
        
    text = f"🔍 <b>Search Results for '{query}':</b>\n\n"
    for c in results:
        text += f"• <b>{c.get('name')}</b> (Anime: {c.get('anime', 'N/A')})\n"
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)

async def top_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pipeline = [
        {"$group": {"_id": "$user_id", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 10}
    ]
    top_users = list(inventory_col.aggregate(pipeline))
    
    text = "🏆 <b>TOP HAREM COLLECTORS</b>\n─────────────────────────\n"
    for idx, u in enumerate(top_users, 1):
        text += f"{idx}. User ID `{u['_id']}` — <b>{u['count']} Cards</b>\n"
        
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)

async def market_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    items = list(market_col.find().limit(10))
    if not items:
        await update.message.reply_text("🏪 လက်ရှိ Market တွင် မည်သည့် ကတ်မျှ မတင်ရောင်းသေးပါ။")
        return
        
    text = "🛒 <b>CHARACTER MARKETPLACE</b>\n─────────────────────────\n"
    for item in items:
        text += f"• <b>{item['card_name']}</b> - Price: {item['price']} Coins (ID: `{item['_id']}`)\n"
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)
