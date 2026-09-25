import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from database import users_col
from cards import seed_initial_cards
from drop import waifu_drop, guess_card
from harem import view_harem
from economy import balance, daily_reward, sell_card, view_market
from duel import start_duel
from trade import gift_card
from leaderboard import leaderboard
from profile import profile_command
from upload import upload_card, delete_card
from config import OWNER_ID, OWNER_USERNAME, GROUP_LINK, CHANNEL_LINK

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

async def send_with_footer(update: Update, text: str, reply_markup=None):
    footer = "\n\n✨ *Powered by maybe* 💫"
    full_text = text + footer
    await update.message.reply_text(full_text, reply_markup=reply_markup, parse_mode="Markdown")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    username = user.username or user.first_name

    # Check group member count if in a group
    if update.effective_chat.type in ["group", "supergroup"]:
        try:
            member_count = await context.bot.get_chat_member_count(update.effective_chat.id)
            if member_count < 50:
                keyboard = [[InlineKeyboardButton("👑 Contact Owner", url=f"https://t.me/{OWNER_USERNAME}")]]
                await update.message.reply_text(
                    f"⚠️ **Group Error**: This group has only {member_count} members. A minimum of **50 members** is required to use this bot!\nPlease ask the owner for permission.",
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode="Markdown"
                )
                return
        except Exception:
            pass

    existing_user = users_col.find_one({"user_id": user_id})
    if not existing_user:
        users_col.insert_one({
            "user_id": user_id,
            "username": username,
            "balance": 100,
            "xp": 0,
            "level": 1
        })
        welcome_message = f"မင်္ဂလာပါ {username} ခင်ဗျာ။ Waifu Card Bot မှ ကြိုဆိုပါတယ်။ Coins 100 ပေးအပ်လိုက်ပါပြီ။"
    else:
        welcome_message = f"WELCOME BACK! {username}၊ သင်၏ Waifu Harem စုဆောင်းမှုကို ဆက်လက်လုပ်ဆောင်နိုင်ပါပြီ။"

    await send_with_footer(update, welcome_message)

def main():
    # ဤနေရာတွင် BotFather ဆီမှ ရထားသော သင်၏ Telegram Bot Token ကို တိုက်ရိုက်ထည့်ပါ
    BOT_TOKEN = "8823072889:AAFHC43_m1GAq_jQO2qBxVn1pIeWWg2RHvs"
    
    if not BOT_TOKEN or BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        print("Error: BOT_TOKEN ကို ထည့်သွင်းထားခြင်း မရှိပါ။")
        return

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Handler များ အားလုံးကို ဤနေရာတွင် တိုက်ရိုက်ထည့်သွင်းခြင်း
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("drop", waifu_drop))
    app.add_handler(CommandHandler("guess", guess_card))
    app.add_handler(CommandHandler("harem", view_harem))
    app.add_handler(CommandHandler("balance", balance))
    app.add_handler(CommandHandler("daily", daily_reward))
    app.add_handler(CommandHandler("sell", sell_card))
    app.add_handler(CommandHandler("market", view_market))
    app.add_handler(CommandHandler("duel", start_duel))
    app.add_handler(CommandHandler("gift", gift_card))
    app.add_handler(CommandHandler("top", leaderboard))
    app.add_handler(CommandHandler("profile", profile_command))
    app.add_handler(CommandHandler("uploadchar", upload_card))
    app.add_handler(CommandHandler("deletecard", delete_card))
    app.add_handler(CommandHandler("fav", fav))
    app.add_handler(CommandHandler("unfav", unfav))
    app.add_handler(CommandHandler("search", search))
    app.add_handler(CommandHandler("check", check))
    app.add_handler(CommandHandler("todaytop", todaytop))

from cards import check, fav, search, unfav
from leaderboard import todaytop
from telegram.ext import Application, CommandHandler

    app.run_polling()

if __name__ == '__main__':
    main()
