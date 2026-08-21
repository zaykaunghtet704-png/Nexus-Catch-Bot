from telegram import Update
from telegram.ext import Application, CommandHandler, ChatMemberHandler, CallbackQueryHandler, ContextTypes
from config import BOT_TOKEN, LOG_CHANNEL_ID
import handlers as h

async def my_chat_member_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    result = update.my_chat_member
    if result.new_chat_member.status in ["member", "administrator"]:
        chat = result.chat
        user = result.from_user
        count = await chat.get_member_count()
        log_text = f"📥 **BOT ADDED TO GROUP**\n\n👥 Group: {chat.title}\n🆔 ID: `{chat.id}`\n👤 By: {user.first_name}\n📊 Members: `{count}`"
        try:
            await context.bot.send_message(chat_id=LOG_CHANNEL_ID, text=log_text, parse_mode="Markdown")
        except Exception:
            pass

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(ChatMemberHandler(my_chat_member_handler, ChatMemberHandler.MY_CHAT_MEMBER))
    app.add_handler(CallbackQueryHandler(h.button_callback))

    cmds = [
        ("start", h.start_cmd), ("help", h.help_cmd), ("harem", h.harem_cmd),
        ("profile", h.profile_cmd), ("Nexus", h.nexus_cmd), ("claim", h.claim_cmd),
        ("daily", h.daily_cmd), ("balance", h.balance_cmd), ("market", h.market_cmd),
        ("sell", h.sell_cmd), ("buy", h.buy_cmd), ("delist", h.delist_cmd),
        ("trade", h.trade_cmd), ("gift", h.gift_cmd),
        ("duel", h.duel_cmd), ("upgrade", h.upgrade_cmd), ("fav", h.fav_cmd),
        ("unfav", h.unfav_cmd), ("top", h.top_cmd), ("rankings", h.top_cmd),
        ("ranking", h.ranking_cmd), ("sellprice", h.sellprice_cmd),
        ("todaytop", h.todaytop_cmd), ("changetime", h.changetime_cmd),
        ("ctop", h.ctop_cmd), ("hmode", h.hmode_cmd), ("reset", h.reset_cmd),
        ("search", h.search_cards_cmd), ("check", h.check_card_cmd),
        ("addcard", h.addcard_cmd), ("removecard", h.remove_card_cmd),
        ("approve", h.approve_cmd), ("gcoin", h.givecoins_cmd),
        ("ban", h.ban_cmd), ("broadcast", h.broadcast_cmd)
    ]

    for c, func in cmds:
        app.add_handler(CommandHandler(c, func))

    print("🚀 NEXUS CATCH BOT RUNNING FULLY...")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
