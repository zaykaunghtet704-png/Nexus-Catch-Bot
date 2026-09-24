from database import users_col  # သို့မဟုတ် leaderboard အတွက် သုံးသော Collection
from telegram import Update
from telegram.ext import ContextTypes


async def todaytop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Coins/Balance အများဆုံး Top 10 ယူခြင်း
    top_users = list(users_col.find().sort("coins", -1).limit(10))

    if not top_users:
        await update.message.reply_text("🏆 ယနေ့ ထိပ်တန်း ကစားသမား စာရင်း မရှိသေးပါ။")
        return

    text = "🏆 <b>ယနေ့ ထိပ်တန်း ကစားသမားများ</b>\n\n"
    for idx, u in enumerate(top_users, 1):
        name = u.get("first_name", "User")
        coins = u.get("coins", 0)
        text += f"{idx}. <b>{name}</b> - 💰 {coins} Coins\n"

    await update.message.reply_text(text, parse_mode="HTML")
