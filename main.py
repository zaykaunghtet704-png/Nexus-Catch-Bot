import logging
from telegram.ext import ApplicationBuilder, CommandHandler
from config import BOT_TOKEN
from database import init_db
from handlers import (
    start_command, help_command, harem_command, search_command,
    profile_command, nexus_command, daily_command, claim_command,
    balance_command, market_command, sell_command, duel_command,
    upgrade_command, fav_command, addcard_command, removecard_command, gcoin_command
)

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

def main():
    init_db()
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Handlers Registration
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("harem", harem_command))
    app.add_handler(CommandHandler("search", search_command))
    app.add_handler(CommandHandler("profile", profile_command))
    app.add_handler(CommandHandler("Nexus", nexus_command))
    app.add_handler(CommandHandler("daily", daily_command))
    app.add_handler(CommandHandler("claim", claim_command))
    app.add_handler(CommandHandler("balance", balance_command))
    app.add_handler(CommandHandler("market", market_command))
    app.add_handler(CommandHandler("sell", sell_command))
    app.add_handler(CommandHandler("duel", duel_command))
    app.add_handler(CommandHandler("upgrade", upgrade_command))
    app.add_handler(CommandHandler("fav", fav_command))
    
    # Owner Commands
    app.add_handler(CommandHandler("addcard", addcard_command))
    app.add_handler(CommandHandler("removecard", removecard_command))
    app.add_handler(CommandHandler("gcoin", gcoin_command))

    print("🤖 Bot is running successfully...")
    app.run_polling()

if __name__ == '__main__':
    main()
