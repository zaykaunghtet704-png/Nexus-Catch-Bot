from telegram import Update
from telegram.ext import ContextTypes
from database import users_col

async def leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    top_users = list(users_col.find().sort("balance", -1).limit(5))

    if not top_users:
        await update.message.reply_text("🏆 ဦးဆောင်သူစာရင်း အချက်အလက် မရှိသေးပါ။")
        return

    lb_text = "🏆 **Waifu Bot - Wealth Leaderboard (အချမ်းသာဆုံး ဦးဆောင်သူများ)** 🏆\n\n"
    
    for rank, u in enumerate(top_users, 1):
        name = u.get("username", "Unknown")
        balance = u.get("balance", 0)
        lb_text += f"{rank}. **{name}** — 💰 {balance} Coins\n"

    await update.message.reply_text(lb_text, parse_mode="Markdown")
