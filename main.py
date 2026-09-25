import logging
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import Application, CommandHandler, ContextTypes

# Modules များ import လုပ်ခြင်း
from cards import check, fav, search, unfav
from economy import daily
from leaderboard import todaytop
from profile import profile
from config import BOT_TOKEN

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 မင်္ဂလာပါ! Nexus Catch Bot မှ ကြိုဆိုပါတယ်။ /help ဟု ရိုက်နှိပ်၍ အကူအညီယူပါ။")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "<b>Nexus Catch Bot - အကူအညီ</b>\n\n"
        "/profile - မိမိ Profile ကြည့်ရန်\n"
        "/daily - နေ့စဉ် ဘောနပ်စ်ယူရန်\n"
        "/fav - နှစ်သက်သော ကတ်သတ်မှတ်ရန်\n"
        "/unfav - Favorite ဖြုတ်ရန်\n"
        "/search - ကတ်ရှာရန်\n"
        "/check - ကတ်အချက်အလက် စစ်ရန်\n"
        "/todaytop - Top Leaderboard ကြည့်ရန်"
    )
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)


def main():
    app = Application.builder().token(BOT_TOKEN).build()

    # Application ထဲတွင် Handler များထည့်ခြင်း
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("profile", profile))
    app.add_handler(CommandHandler("daily", daily))
    app.add_handler(CommandHandler("fav", fav))
    app.add_handler(CommandHandler("unfav", unfav))
    app.add_handler(CommandHandler("search", search))
    app.add_handler(CommandHandler("check", check))
    app.add_handler(CommandHandler("todaytop", todaytop))

    app.run_polling()


if __name__ == "__main__":
    main()
