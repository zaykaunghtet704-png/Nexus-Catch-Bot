from telegram.ext import Application, CommandHandler, ChatMemberHandler, CallbackQueryHandler
from config import BOT_TOKEN
import handlers as h

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    
    # 1. Callback နှင့် Chat Member Handler များကို အပေါ်ဆုံးတွင် ထားပါ
    app.add_handler(CallbackQueryHandler(h.button_callback))
    app.add_handler(ChatMemberHandler(h.my_chat_member_handler, ChatMemberHandler.MY_CHAT_MEMBER))

    # 2. Command Handlers အားလုံးကို ချိတ်ဆက်ခြင်း
    cmds = [
        ("start", h.start_cmd), 
        ("help", h.help_cmd), 
        ("harem", h.harem_cmd),
        ("profile", h.profile_cmd), 
        ("Nexus", h.nexus_cmd), 
        ("claim", h.claim_cmd),
        ("daily", h.daily_cmd), 
        ("balance", h.balance_cmd), 
        ("market", h.market_cmd),
        ("sell", h.sell_cmd), 
        ("buy", h.buy_cmd), 
        ("delist", h.delist_cmd),
        ("trade", h.trade_cmd), 
        ("gift", h.gift_cmd), 
        ("duel", h.duel_cmd),
        ("upgrade", h.upgrade_cmd), 
        ("fav", h.fav_cmd), 
        ("unfav", h.unfav_cmd),
        ("top", h.top_cmd), 
        ("rankings", h.ranking_cmd), 
        ("ctop", h.ctop_cmd),
        ("hmode", h.hmode_cmd), 
        ("search", h.search_cards_cmd),
        ("check", h.check_card_cmd),
        ("sellprice", h.sellprice_cmd),
        ("todaytop", h.todaytop_cmd),
        ("changetime", h.changetime_cmd),
        ("reset", h.reset_cmd),
        ("addcard", h.addcard_cmd), 
        ("removecard", h.remove_card_cmd),
        ("approve", h.approve_cmd), 
        ("gcoin", h.givecoins_cmd),
        ("ban", h.ban_cmd), 
        ("broadcast", h.broadcast_cmd)
    ]

    for c, func in cmds:
        app.add_handler(CommandHandler(c, func))

    print("🚀 NEXUS CATCH BOT RUNNING FULLY...")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
