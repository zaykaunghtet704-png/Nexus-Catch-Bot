from telegram import Update, ChatMember
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from config import BOT_TOKEN, LOG_CHANNEL_ID
import handlers as h

def main():
    app = Application.builder().token(BOT_TOKEN).build()

    # User Commands
    user_cmds = [
        ("start", h.start_cmd), ("help", h.help_cmd), ("ping", h.ping_cmd),
        ("profile", h.profile_cmd), ("harem", h.harem_cmd), ("hmode", h.hmode_cmd),
        ("view", h.view_card_cmd), ("daily", h.daily_cmd), ("claim", h.claim_cmd),
        ("nclaim", h.nclaim_cmd), ("fav", h.fav_cmd), ("favlist", h.favlist_cmd),
        ("sell", h.sell_cmd), ("sellprice", h.sellprice_cmd), ("gift", h.gift_cmd),
        ("pay", h.pay_cmd), ("top", h.top_cmd), ("rich", h.rich_cmd),
        ("search", h.search_cmd), ("rarity", h.rarity_cmd), ("shop", h.shop_cmd),
        ("buy", h.buy_cmd), ("dye", h.dye_cmd), ("duel", h.duel_cmd),
        ("guild", h.guild_cmd), ("gcreate", h.gcreate_cmd), ("gjoin", h.gjoin_cmd),
        ("pass", h.pass_cmd), ("lang", h.lang_cmd), ("frame", h.frame_cmd),
        ("font", h.font_cmd), ("trade", h.trade_cmd)
    ]

    # Owner & Sudo Commands
    sudo_cmds = [
        ("sudo", h.add_sudo_cmd), ("rmsudo", h.rmsudo_cmd), ("sudolist", h.sudolist_cmd),
        ("gcoin", h.gcoin_cmd), ("rmcoin", h.rmcoin_cmd), ("gcard", h.gcard_cmd),
        ("rmcard", h.rmcard_cmd), ("spawn", h.spawn_cmd), ("changetime", h.changetime_cmd),
        ("broadcast", h.broadcast_cmd), ("ban", h.ban_cmd), ("unban", h.unban_cmd),
        ("checkuser", h.checkuser_cmd), ("maintenance", h.maintenance_cmd),
        ("stats", h.stats_cmd), ("setpass", h.setpass_cmd), ("addcard", h.addcard_cmd),
        ("delcard", h.delcard_cmd), ("reload", h.reload_cmd), ("log", h.log_cmd)
    ]

    for cmd, handler in user_cmds + sudo_cmds:
        app.add_handler(CommandHandler(cmd, handler))

    print("NEXUS CATCH BOT RUNNING FULLY...")
    app.run_polling()

if __name__ == "__main__":
    main()
