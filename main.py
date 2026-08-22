import logging
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters
from config import BOT_TOKEN
from database import init_db
from handlers import (
    start, help_command, harem, search_cards, profile, nexus_catch,
    daily, claim, balance, market, sell, buy, delist,
    trade, gift, duel, upgrade, fav, unfav, hmode, check_card, top_rankings, ctop,
    addcard, removecard, gcoin, user_cards, ban_user, unban_user, changetime,
    group_message_listener
)

logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)

def main():
    init_db()
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    
    # User Command Handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("harem", harem))
    app.add_handler(CommandHandler("search", search_cards))
    app.add_handler(CommandHandler("profile", profile))
    app.add_handler(CommandHandler("Nexus", nexus_catch))
    app.add_handler(CommandHandler("daily", daily))
    app.add_handler(CommandHandler("claim", claim))
    app.add_handler(CommandHandler("balance", balance))
    app.add_handler(CommandHandler("market", market))
    app.add_handler(CommandHandler("sell", sell))
    app.add_handler(CommandHandler("buy", buy))
    app.add_handler(CommandHandler("delist", delist))
    app.add_handler(CommandHandler("trade", trade))
    app.add_handler(CommandHandler("gift", gift))
    app.add_handler(CommandHandler("duel", duel))
    app.add_handler(CommandHandler("upgrade", upgrade))
    app.add_handler(CommandHandler("fav", fav))
    app.add_handler(CommandHandler("unfav", unfav))
    app.add_handler(CommandHandler("hmode", hmode))
    app.add_handler(CommandHandler("check", check_card))
    app.add_handler(CommandHandler("top", top_rankings))
    app.add_handler(CommandHandler("rankings", top_rankings))
    app.add_handler(CommandHandler("ctop", ctop))
    
    # Owner & Admin Command Handlers
    app.add_handler(CommandHandler("addcard", addcard))
    app.add_handler(CommandHandler("removecard", removecard))
    app.add_handler(CommandHandler("gcoin", gcoin))
    app.add_handler(CommandHandler("usercards", user_cards))
    app.add_handler(CommandHandler("ban", ban_user))
    app.add_handler(CommandHandler("unban", unban_user))
    app.add_handler(CommandHandler("changetime", changetime))
    
    # Message Listener for Group Card Spawning (Math Formula Drop)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, group_message_listener))
    
    print("🚀 Ultimate Card Bot is running successfully...")
    app.run_polling()

if __name__ == "__main__":
    main()
