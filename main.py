from threading import Thread
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, 
    MessageHandler, ChatMemberHandler, filters
)

from config import BOT_TOKEN
from services import run_flask
from handlers import (
    start_cmd, help_cmd, harem_cmd, claim_cmd, profile_cmd, daily_cmd, setlang_cmd,
    sellprice_cmd, approvegroup_cmd, givecoin_cmd, on_bot_added_to_group, handle_group_messages
)

def main():
    # Run Web Port Binding for Render Deployment
    Thread(target=run_flask, daemon=True).start()
    
    app = Application.builder().token(BOT_TOKEN).build()
    
    # User Commands
    app.add_handler(CommandHandler(["start", "sratr"], start_cmd))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("harem", harem_cmd))
    app.add_handler(CommandHandler("claim", claim_cmd))
    app.add_handler(CommandHandler("profile", profile_cmd))
    app.add_handler(CommandHandler("daily", daily_cmd))
    app.add_handler(CommandHandler("sellprice", sellprice_cmd))
    app.add_handler(CommandHandler("setlang", setlang_cmd))
    
    # Owner Commands
    app.add_handler(CommandHandler("approvegroup", approvegroup_cmd))
    app.add_handler(CommandHandler("givecoin", givecoin_cmd))
    
    # Group Events & Message Listeners
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, on_bot_added_to_group))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_group_messages))
    
    print("🚀 Nexus Multilingual Card Bot Started Successfully!")
    app.run_polling()

if __name__ == "__main__":
    main()
