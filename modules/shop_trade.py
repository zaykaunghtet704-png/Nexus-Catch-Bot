"""
modules/shop_trade.py - Shop & Daily Bonus Module
"""
from datetime import datetime, timedelta
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes
from database import users_col

async def daily_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    data = users_col.find_one({"user_id": user.id}) or {}
    last_claimed = data.get("last_daily")

    if last_claimed and datetime.utcnow() - last_claimed < timedelta(days=1):
        await update.message.reply_text("⏳ နေ့စဉ်ဆုလာဘ်ကို 24 နာရီမှ တစ်ကြိမ်သာ ရယူနိုင်ပါသည်။")
        return

    users_col.update_one(
        {"user_id": user.id},
        {"$inc": {"balance": 1000, "gems": 5}, "$set": {"last_daily": datetime.utcnow()}},
        upsert=True
    )
    await update.message.reply_text("🎁 <b>Daily Bonus Received!</b> +1,000 Coins နှင့် +5 Gems ရရှိသွားပါပြီ။", parse_mode=ParseMode.HTML)

async def shop_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "🛒 <b>NEXUS BOT SHOP</b>\n"
        "─────────────────────────\n"
        "1. <b>Card Pack (Standard):</b> 500 Coins (`/buy pack`)\n"
        "2. <b>VIP Pass (7 Days):</b> 50 Gems (`/buy vip`)\n\n"
        "ဝယ်ယူလိုပါက သက်ဆိုင်ရာ Command ကို အသုံးပြုပါ။"
    )
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)
