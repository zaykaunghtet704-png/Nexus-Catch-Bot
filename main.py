import os
import sys
import logging
from telegram import BotCommand
from telegram.ext import Application, CallbackQueryHandler, CommandHandler

# Current Working Directory နှင့် modules folder အား Python Path ထဲသို့ ထည့်သွင်းခြင်း
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "modules"))

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

# Missing Command များအတွက် extra_commands module မှ Import လုပ်ခြင်း
try:
    from modules.extra_commands import get_extra_handlers
except ImportError:
    try:
        from extra_commands import get_extra_handlers
    except ImportError:
        def get_extra_handlers(): return []

# Inline Gallery Search Module Import ပြုလုပ်ခြင်း
try:
    from modules.inline_search import get_inline_search_handlers
except ImportError:
    try:
        from inline_search import get_inline_search_handlers
    except ImportError:
        def get_inline_search_handlers(): return []

# Logging Setup
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")

# Telegram Bot Menu စာရင်း အလိုအလျောက် သတ်မှတ်ခြင်း
async def post_init(application: Application):
    commands = [
        BotCommand("start", "Bot ကို စတင်ရန်"),
        BotCommand("help", "အကူအညီနှင့် Command များကြည့်ရန်"),
        BotCommand("harem", "မိမိ၏ Character ကတ်များကြည့်ရန်"),
        BotCommand("profile", "မိမိ Profile နှင့် Stats ကြည့်ရန်"),
        BotCommand("catch", "ကတ်ဖမ်းရန်"),
        BotCommand("daily", "နေ့စဉ် ဆုလာဘ်ယူရန်"),
        BotCommand("balance", "လက်ကျန် Coins/Gems ကြည့်ရန်"),
        BotCommand("shop", "Item ဆိုင်ကြည့်ရန်"),
        BotCommand("market", "ကတ် အရောင်းအဝယ်ဈေးကွက်"),
        BotCommand("top", "Top Collectors စာရင်း"),
        BotCommand("ctop", "Top Characters စာရင်း"),
        BotCommand("ranking", "Global Ranking ကြည့်ရန်"),
        BotCommand("search", "Character ရှာဖွေရန်"),
        BotCommand("gift", "အခြားသူထံ ကတ်လက်ဆောင်ပေးရန်"),
        BotCommand("check", "Character အချက်အလက် စစ်ရန်"),
    ]
    await application.bot.set_my_commands(commands)
    logger.info("✅ Bot Menu Commands set successfully!")

def main():
    if not BOT_TOKEN:
        logger.error("❌ BOT_TOKEN environment variable မတွေ့ရှိပါ။")
        return

    # Application Builder နှင့် post_init တပ်ဆင်ခြင်း
    app = Application.builder().token(BOT_TOKEN).post_init(post_init).build()

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

    # Extra Commands (/profile, /balance, /top, /ctop, /ranking, /gift, /check)
    for handler in get_extra_handlers():
        app.add_handler(handler)

    # Inline Card Gallery Search (/search & Inline Query)
    for handler in get_inline_search_handlers():
        app.add_handler(handler)

    app.add_handler(CommandHandler("admin", admin_panel_command))
    app.add_handler(CommandHandler("gban", gban_command))
    app.add_handler(CallbackQueryHandler(admin_callback_handler, pattern="^admin_"))

    for handler in get_master_owner_handlers():
        app.add_handler(handler)

    logger.info("🤖 Bot started successfully...")
    
    # drop_pending_updates=True ထည့်သွင်းပေးခြင်းဖြင့် 409 Conflict သို့မဟုတ် Queue ငြိသည့် အမှားများ ကာကွယ်ပေးသည်
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
