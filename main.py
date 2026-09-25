import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# Modules များမှ Function များ import လုပ်ခြင်း
from cards import check, fav, search, unfav
from database import cards_col
from economy import daily
from leaderboard import todaytop
from profile import profile

# Logging setup လုပ်ခြင်း
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)


def seed_initial_cards():
    """Initial cards Database ထဲသို့ ထည့်သွင်းခြင်း"""
    if cards_col.count_documents({}) == 0:
        sample_cards = [
            {
                "card_id": "c001",
                "name": "Rem",
                "anime": "Re:Zero",
                "rarity": "SR",
                "image_url": "https://i.imgur.com/example1.jpg",
            },
            {
                "card_id": "c002",
                "name": "Zero Two",
                "anime": "Darling in the Franxx",
                "rarity": "SSR",
                "image_url": "https://i.imgur.com/example2.jpg",
            },
            {
                "card_id": "c003",
                "name": "Nezuko Kamado",
                "anime": "Demon Slayer",
                "rarity": "R",
                "image_url": "https://i.imgur.com/example3.jpg",
            },
        ]
        cards_col.insert_many(sample_cards)
        print("နမူနာ ကတ်များ ထည့်သွင်းပြီးပါပြီ။")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/start command အတွက် function"""
    await update.message.reply_text(
        "👋 မင်္ဂလာပါ! Nexus Catch Bot မှ ကြိုဆိုပါတယ်။\n"
        "အကူအညီရယူရန် /help ဟု ရိုက်နှိပ်ပါ။"
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/help command အတွက် function"""
    text = (
        "<b>Nexus Catch Bot - အကူအညီ</b>\n\n"
        "/profile - မိမိ Profile နှင့် Stats များကြည့်ရန်\n"
        "/daily - နေ့စဉ် ဘောနပ်စ်ယူရန်\n"
        "/fav <id> - နှစ်သက်သော ကတ်သတ်မှတ်ရန်\n"
        "/unfav - Favorite ဖြုတ်ရန်\n"
        "/search <name> - ကတ်ရှာရန်\n"
        "/check <id> - ကတ်အချက်အလက် စစ်ရန်\n"
        "/todaytop - ယနေ့ Top Leaderboard ကြည့်ရန်"
    )
    await update.message.reply_text(text, parse_mode="HTML")


def main():
    """Bot စတင်ပွင့်မည့် Main Function"""
    seed_initial_cards()

    # သင့် Bot Token ကို ဒီနေရာမှာ ထည့်ပါ
    BOT_TOKEN = "8823072889:AAFHC43_m1GAq_jQO2qBxVn1pIeWWg2RHvs"

    app = Application.builder().token(BOT_TOKEN).build()

    # Command Handlers များ Register လုပ်ခြင်း
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
