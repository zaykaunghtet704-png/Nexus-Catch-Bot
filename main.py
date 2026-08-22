import logging
from telegram.ext import ApplicationBuilder, CommandHandler
from config import BOT_TOKEN
from database import init_db
from handlers import start, help_command, profile_command

logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)

def main():
    # Initialize Database
    init_db()
    
    application = ApplicationBuilder().token(BOT_TOKEN).build()
    
    # Register Handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("profile", profile_command))
    
    print("🚀 Ultimate Card Bot is successfully running...")
    application.run_polling()

if __name__ == "__main__":
    main()
