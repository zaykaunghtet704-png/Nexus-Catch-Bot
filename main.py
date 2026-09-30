import os
import sys

# Current Working Directory နှင့် modules folder အား Python Path ထဲသို့ အတင်းထည့်ခြင်း
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "modules"))

import logging
from telegram.ext import Application, CallbackQueryHandler, CommandHandler

# Modules များ Import ပြုလုပ်ခြင်း (Safe Loading)
try:
    from modules.start import start_command, help_command
except ImportError:
    from start import start_command, help_command

try:
    from modules.game import get_game_handlers
except ImportError:
    from game import get_game_handlers

try:
    from modules.harem import get_harem_handlers
except ImportError:
    from harem import get_harem_handlers

try:
    from modules.shop_trade import daily_command, shop_command
except ImportError:
    from shop_trade import daily_command, shop_command

try:
    from modules.upload import get_upload_handlers
except ImportError:
    from upload import get_upload_handlers

try:
    from modules.trade_market import get_trade_market_handlers
except ImportError:
    from trade_market import get_trade_market_handlers

try:
    from modules.quests_redeem import get_quests_redeem_handlers
except ImportError:
    from quests_redeem import get_quests_redeem_handlers

try:
    from modules.spawn_settings import get_spawn_settings_handlers
except ImportError:
    from spawn_settings import get_spawn_settings_handlers

try:
    from modules.admin import admin_panel_command, gban_command, admin_callback_handler
except ImportError:
    from admin import admin_panel_command, gban_command, admin_callback_handler

try:
    from modules.owner_god_master import get_master_owner_handlers
except ImportError:
    try:
        from owner_god_master import get_master_owner_handlers
    except ImportError:
        def get_master_owner_handlers(): return []

# Logging Setup
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")

def main():
    if not BOT_TOKEN:
        logger.error("❌ BOT_TOKEN environment variable မတွေ့ရှိပါ။")
        return

    app = Application.builder().token(BOT_TOKEN).build()

    # Handlers Registrar
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("daily", daily_command))
    app.add_handler(CommandHandler("shop", shop_command))

    for handler in get_game_handlers():
        app.add_handler(handler)

    for handler in get_harem_handlers():
        app.add_handler(handler)

    for handler in get_upload_handlers():
        app.add_handler(handler)

    for handler in get_trade_market_handlers():
        app.add_handler(handler)

    for handler in get_quests_redeem_handlers():
        app.add_handler(handler)

    for handler in get_spawn_settings_handlers():
        app.add_handler(handler)

    app.add_handler(CommandHandler("admin", admin_panel_command))
    app.add_handler(CommandHandler("gban", gban_command))
    app.add_handler(CallbackQueryHandler(admin_callback_handler, pattern="^admin_"))

    for handler in get_master_owner_handlers():
        app.add_handler(handler)

    logger.info("🤖 Bot started successfully...")
    app.run_polling()

if __name__ == "__main__":
    main()
