import os
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from database import users_col
from cards import seed_initial_cards
from drop import waifu_drop, guess_card
from harem import view_harem
from economy import balance, daily_reward, sell_card, view_market
from duel import start_duel
from trade import gift_card
from leaderboard import leaderboard

from upload import upload_card, delete_card

# main() ফাংশন ထဲတွင် ထည့်ရန်:
app.add_handler(CommandHandler("uploadchar", upload_card))
app.add_handler(CommandHandler("deletecard", delete_card))

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    username = user.username or user.first_name

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

    await update.message.reply_text(welcome_message)

def main():
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    if not BOT_TOKEN:
        print("Error: BOT_TOKEN ကို ထည့်သွင်းထားခြင်း မရှိပါ။")
        return

    app = ApplicationBuilder().token(BOT_TOKEN).build()

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

    print("Bot စတင် အလုပ်လုပ်နေပါပြီ...")
    app.run_polling()

if __name__ == '__main__':
    main()
