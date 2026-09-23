import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from database import users_col
from config import OWNER_ID, OWNER_USERNAME, GROUP_LINK, CHANNEL_LINK
from helpers import send_with_footer, check_forced_sub

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    
    # Check group member count if in a group
    if update.effective_chat.type in ["group", "supergroup"]:
        member_count = await context.bot.get_chat_member_count(update.effective_chat.id)
        if member_count < 50:
            keyboard = [[InlineKeyboardButton("👑 Contact Owner for Permission", url=f"https://t.me/{OWNER_USERNAME}")]]
            await update.message.reply_text(
                f"⚠️ **Group Error**: This group has only {member_count} members. A minimum of **50 members** is required to use this bot!\nPlease ask the owner for permission.",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown"
            )
            return

    existing_user = users_col.find_one({"user_id": user_id})
    if not existing_user:
        users_col.insert_one({"user_id": user_id, "username": user.username or user.first_name, "balance": 100, "xp": 0, "level": 1})
        msg = f"🌟 မင်္ဂလာပါ {user.first_name} ခင်ဗျာ။ Waifu Card Bot မှ ကြိုဆိုပါတယ်။ Coins 100 ရရှိထားပါသည်။\nWelcome to Waifu Card Bot!"
    else:
        msg = f"✨ WELCOME BACK, {user.first_name}!"

    await send_with_footer(update, msg)

def main():
    BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))

    print("🤖 Bot is running with Powered by maybe system...")
    app.run_polling()

if __name__ == '__main__':
    main()
