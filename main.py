"""
main.py - Main Entrypoint
"""
import os
import logging
from telegram.ext import Application, CallbackQueryHandler, CommandHandler
from modules.admin import admin_callback_handler, admin_panel_command, gban_command
from modules.game import catch_command, collection_command, leaderboard_command, profile_command
from modules.shop_trade import daily_command, shop_command
from modules.start import help_command, start_command

# Harem Module မှ Handler များကို တင်သွင်းခြင်း
from modules.harem import get_harem_handlers

# Master Owner Module မှ Handler များကို တင်သွင်းခြင်း
try:
    from modules.owner_god_master import get_master_owner_handlers
except ImportError:
    from owner_god_master import get_master_owner_handlers

# Logging Setup
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Bot Token ကို Environment Variable မှ ခေါ်ယူခြင်း
BOT_TOKEN = os.getenv("BOT_TOKEN")

def main():
    if not BOT_TOKEN:
        logger.error("❌ BOT_TOKEN environment variable မတွေ့ရှိပါ။ ကျေးဇူးပြု၍ Render/VPS တွင် Token ထည့်သွင်းပေးပါ။")
        return

    app = Application.builder().token(BOT_TOKEN).build()

    # 1. User & Game Handlers
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("profile", profile_command))
    app.add_handler(CommandHandler("catch", catch_command))
    app.add_handler(CommandHandler("roll", catch_command))
    app.add_handler(CommandHandler("collection", collection_command))
    app.add_handler(CommandHandler("leaderboard", leaderboard_command))
    app.add_handler(CommandHandler("daily", daily_command))
    app.add_handler(CommandHandler("shop", shop_command))

    # 2. Harem Modules Handlers (/harem, /chmode)
    for handler in get_harem_handlers():
        app.add_handler(handler)

    # 3. Admin Handlers
    app.add_handler(CommandHandler("admin", admin_panel_command))
    app.add_handler(CommandHandler("gban", gban_command))
    app.add_handler(CallbackQueryHandler(admin_callback_handler, pattern="^admin_"))

    # 4. Master Owner God-Mode Suite Handlers
    for handler in get_master_owner_handlers():
        app.add_handler(handler)

    logger.info("🤖 Nexus Catch Bot started successfully with Master Owner Suite & Harem Module...")
    print("🤖 Nexus Catch Bot started successfully...")
    
    app.run_polling()

if __name__ == "__main__":
    main()
