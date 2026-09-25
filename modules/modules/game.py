"""
modules/game.py - Game Logic, Catching & Collection
"""
import random
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes
from database import cards_col, inventory_col, users_col

async def profile_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    data = users_col.find_one({"user_id": user.id}) or {}
    total_cards = inventory_col.count_documents({"user_id": user.id})

    text = (
        f"👤 <b>PLAYER PROFILE</b>\n"
        f"─────────────────────────\n"
        f"🏷️ <b>Name:</b> {user.first_name}\n"
        f"👑 <b>Title:</b> {data.get('custom_title', 'Novice Collector')}\n"
        f"💰 <b>Coins:</b> {data.get('balance', 0):,}\n"
        f"💎 <b>Gems:</b> {data.get('gems', 0):,}\n"
        f"⚡ <b>XP:</b> {data.get('xp', 0):,}\n"
        f"🎴 <b>Total Cards:</b> {total_cards}\n"
        f"🌟 <b>VIP Status:</b> {'Active' if data.get('is_vip') else 'None'}"
    )
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)

async def catch_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    all_cards = list(cards_col.find({}))
    if not all_cards:
        await update.message.reply_text("⚠️ စနစ်ထဲတွင် ကတ်များ ထည့်သွင်းထားခြင်း မရှိသေးပါ။")
        return

    card = random.choice(all_cards)
    inventory_col.insert_one({
        "user_id": user.id,
        "card_id": card["card_id"],
        "name": card.get("name"),
        "rarity": card.get("rarity", "Common"),
        "anime": card.get("anime", "Unknown"),
        "image_url": card.get("image_url", "")
    })
    
    users_col.update_one({"user_id": user.id}, {"$inc": {"xp": 50, "balance": 100}})
    await update.message.reply_text(
        f"🎉 <b>{user.first_name}</b> က <b>{card.get('name')}</b> ({card.get('rarity')}) ကတ်ကို အောင်မြင်စွာ ဖမ်းဆီးရရှိလိုက်ပါပြီ! 🎴",
        parse_mode=ParseMode.HTML
    )

async def collection_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_cards = list(inventory_col.find({"user_id": user.id}).limit(10))
    if not user_cards:
        await update.message.reply_text("📭 သင့်တွင် ကတ်များ မရှိသေးပါ။ /catch ဖြင့် ကတ်များ ဖမ်းဆီးပါ။")
        return

    text = f"🎴 <b>YOUR RECENT CARDS COLLECTION</b>\n─────────────────────────\n"
    for idx, c in enumerate(user_cards, 1):
        text += f"{idx}. <b>{c.get('name')}</b> | [{c.get('rarity')}] - {c.get('anime')}\n"
    
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)

async def leaderboard_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    top_users = users_col.find().sort("balance", -1).limit(5)
    text = "🏆 <b>TOP COLLECTORS LEADERBOARD</b>\n─────────────────────────\n"
    for idx, u in enumerate(top_users, 1):
        text += f"{idx}. {u.get('first_name', 'User')} — 💰 {u.get('balance', 0):,} Coins\n"
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)
