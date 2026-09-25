"""
main.py - Main Entrypoint
"""
import os
from telegram.ext import Application, CallbackQueryHandler, CommandHandler
from modules.admin import admin_callback_handler, admin_panel_command, gban_command
from modules.game import catch_command, collection_command, leaderboard_command, profile_command
from modules.shop_trade import daily_command, shop_command
from modules.start import help_command, start_command

BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")

def main():
    app = Application.builder().token(BOT_TOKEN).build()

    # User & Game Handlers
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("profile", profile_command))
    app.add_handler(CommandHandler("catch", catch_command))
    app.add_handler(CommandHandler("roll", catch_command))
    app.add_handler(CommandHandler("collection", collection_command))
    app.add_handler(CommandHandler("leaderboard", leaderboard_command))
    app.add_handler(CommandHandler("daily", daily_command))
    app.add_handler(CommandHandler("shop", shop_command))

    # Admin Handlers
    app.add_handler(CommandHandler("admin", admin_panel_command))
    app.add_handler(CommandHandler("gban", gban_command))
    app.add_handler(CallbackQueryHandler(admin_callback_handler, pattern="^admin_"))

    print("🤖 Nexus Catch Bot started successfully...")
    app.run_polling()

if __name__ == "__main__":
    main()
