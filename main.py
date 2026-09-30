"""
main.py - Main Entrypoint
Nexus Catch Bot
"""
import os
import logging
from telegram.ext import Application, CallbackQueryHandler, CommandHandler

# 1. Start Module
from modules.start import start_command, help_command

# 2. Game Module (/catch, /collection, /leaderboard, message counter for spawning)
from modules.game import get_game_handlers

# 3. Harem Module (/harem, /chmode, /hmode)
from modules.harem import get_harem_handlers

# 4. Shop & Economy Module (/daily, /shop)
from modules.shop_trade import daily_command, shop_command

# 5. Upload Module (/upload, /uploadchar, /update, /delete)
from modules.upload import get_upload_handlers

# 6. Trade & Market Module (/sell, /market, /buy, /fav)
from modules.trade_market import get_trade_market_handlers

# 7. Quests, Redeem & Recycle Module (/redeem, /recycle, /quest)
from modules.quests_redeem import get_quests_redeem_handlers

# 8. Spawn Settings Module (/setspawn, /changetime - Owner Only)
from modules.spawn_settings import get_spawn_settings_handlers

# 9. Admin Module (/admin, /gban)
from modules.admin import admin_panel_command, gban_command, admin_callback_handler

# 10. Master Owner God-Mode Module
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

# Environment Variable မှ Bot Token ခေါ်ယူခြင်း
BOT_TOKEN = os.getenv("BOT_TOKEN")

def main():
    if not BOT_TOKEN:
        logger.error("❌ BOT_TOKEN environment variable မတွေ့ရှိပါ။ ကျေးဇူးပြု၍ Render/VPS တွင် Token ထည့်သွင်းပေးပါ။")
        return

    app = Application.builder().token(BOT_TOKEN).build()

    # 1. Start & Help Handlers
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))

    # 2. Daily & Shop Handlers
    app.add_handler(CommandHandler("daily", daily_command))
    app.add_handler(CommandHandler("shop", shop_command))

    # 3. Game & Auto-Spawning Handlers (/catch, /collection, /leaderboard & Spawning Logic)
    for handler in get_game_handlers():
        app.add_handler(handler)

    # 4. Harem & Preference Handlers (/harem, /chmode, /hmode)
    for handler in get_harem_handlers():
        app.add_handler(handler)

    # 5. Character Upload Handlers (/upload, /uploadchar, /update, /delete)
    for handler in get_upload_handlers():
        app.add_handler(handler)

    # 6. Trade & Market Handlers (/sell, /market, /buy, /fav)
    for handler in get_trade_market_handlers():
        app.add_handler(handler)

    # 7. Quests, Redeem & Recycle Handlers (/redeem, /recycle, /quest)
    for handler in get_quests_redeem_handlers():
        app.add_handler(handler)

    # 8. Spawn Settings Handlers (/setspawn, /changetime - Owner Only)
    for handler in get_spawn_settings_handlers():
        app.add_handler(handler)

    # 9. Admin Handlers (/admin, /gban)
    app.add_handler(CommandHandler("admin", admin_panel_command))
    app.add_handler(CommandHandler("gban", gban_command))
    app.add_handler(CallbackQueryHandler(admin_callback_handler, pattern="^admin_"))

    # 10. Master Owner Suite Handlers
    for handler in get_master_owner_handlers():
        app.add_handler(handler)

    logger.info("🤖 Nexus Catch Bot started successfully with all features loaded...")
    print("🤖 Nexus Catch Bot started successfully...")
    
    app.run_polling()

if __name__ == "__main__":
    main()
