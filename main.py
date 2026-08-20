from threading import Thread
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, 
    MessageHandler, filters
)

from config import BOT_TOKEN
from services import run_flask
from handlers import (
    start_cmd, help_cmd, hmode_cmd, claim_cmd, botstats_cmd,
    hmode_callback, captcha_claim_callback, handle_group_messages
)

def main():
    # Run Web Server Thread for Render
    Thread(target=run_flask, daemon=True).start()
    
    # Initialize Bot Application
    app = Application.builder().token(BOT_TOKEN).build()
    
    # Register Commands
    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("hmode", hmode_cmd))
    app.add_handler(CommandHandler("claim", claim_cmd))
    app.add_handler(CommandHandler(["botstats", "suda"], botstats_cmd))
    
    # Register Callbacks
    app.add_handler(CallbackQueryHandler(hmode_callback, pattern="^hmode_"))
    app.add_handler(CallbackQueryHandler(captcha_claim_callback, pattern="^cap_claim_"))
    
    # Register Message Listener for Group Messages
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_group_messages))
    
    print("🚀 Bot Started with Configured Owners & Token!")
    app.run_polling()

if __name__ == "__main__":
    main()
