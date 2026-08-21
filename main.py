import sys
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler
from config import BOT_TOKEN
import handlers as h

def main():
    app = Application.builder().token(BOT_TOKEN).build()

    # User Commands Register
    user_cmds = [
        ("start", h.start_cmd), ("help", h.help_cmd), ("ping", h.ping_cmd),
        ("profile", h.profile_cmd), ("harem", h.harem_cmd), ("hmode", h.hmode_cmd),
        ("view", h.view_card_cmd), ("daily", h.daily_cmd), ("claim", h.claim_cmd),
        ("nclaim", h.nclaim_cmd), ("fav", h.fav_cmd), ("favlist", h.favlist_cmd),
        ("sell", h.sell_cmd), ("sellprice", h.sellprice_cmd), ("gift", h.gift_cmd),
        ("pay", h.pay_cmd), ("top", h.top_cmd), ("rich", h.rich_cmd),
        ("search", h.search_cmd), ("rarity", h.rarity_cmd), ("dye", h.dye_cmd)
    ]

    # Sudo/Admin Commands Register
    sudo_cmds = [
        ("sudo", h.add_sudo_cmd), ("rmsudo", h.rmsudo_cmd), ("sudolist", h.sudolist_cmd),
        ("gcoin", h.gcoin_cmd), ("rmcoin", h.rmcoin_cmd), ("gcard", h.gcard_cmd),
        ("rmcard", h.rmcard_cmd), ("addcard", h.addcard_cmd), ("delcard", h.delcard_cmd),
        ("broadcast", h.broadcast_cmd), ("ban", h.ban_cmd), ("unban", h.unban_cmd),
        ("stats", h.stats_cmd)
    ]

    for cmd, handler in user_cmds + sudo_cmds:
        app.add_handler(CommandHandler(cmd, handler))

    print("NEXUS CATCH BOT IS RUNNING...")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
