from threading import Thread
from telegram.ext import (
    Application, CommandHandler, MessageHandler, filters
)

from config import BOT_TOKEN
from services import run_flask
from handlers import (
    start_cmd, help_cmd, harem_cmd, search_cmd, profile_cmd, top_cmd, ctop_cmd,
    daily_cmd, sellprice_cmd, claim_cmd, nexus_cmd, changetime_cmd, givecoin_cmd,
    on_bot_added_to_group, handle_group_messages
)

def main():
    # Flask Server Start for Render Ping
    Thread(target=run_flask, daemon=True).start()
    
    app = Application.builder().token(BOT_TOKEN).build()
    
    # Register All User Commands
    app.add_handler(CommandHandler(["start", "sratr"], start_cmd))
    app.add_handler(CommandHandler(["help", "Help"], help_cmd))
    app.add_handler(CommandHandler(["harem", "Hearm"], harem_cmd))
    app.add_handler(CommandHandler("search", search_cmd))
    app.add_handler(CommandHandler("profile", profile_cmd))
    app.add_handler(CommandHandler(["top", "rankings"], top_cmd))
    app.add_handler(CommandHandler("ctop", ctop_cmd))
    app.add_handler(CommandHandler("daily", daily_cmd))
    app.add_handler(CommandHandler("sellprice", sellprice_cmd))
    app.add_handler(CommandHandler("claim", claim_cmd))
    app.add_handler(CommandHandler("Nexus", nexus_cmd))
    
    # Register Owner/Admin Commands
    app.add_handler(CommandHandler("changetime", changetime_cmd))
    app.add_handler(CommandHandler("givecoin", givecoin_cmd))
    
    # Register Event Listeners
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, on_bot_added_to_group))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_group_messages))
    
    print("🚀 Nexus Bot Online!")
    app.run_polling()

if __name__ == "__main__":
    main()
