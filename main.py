import logging
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ChatMemberHandler
from config import BOT_TOKEN
from handlers import (
    my_chat_member_handler, start_cmd, help_cmd, harem_cmd, search_cards_cmd,
    profile_cmd, nexus_cmd, daily_cmd, claim_cmd, balance_cmd, market_cmd,
    sell_cmd, buy_cmd, delist_cmd, trade_cmd, gift_cmd, duel_cmd, upgrade_cmd,
    fav_cmd, unfav_cmd, hmode_cmd, check_card_cmd, top_cmd, ctop_cmd,
    addcard_cmd, remove_card_cmd, givecoins_cmd, user_cards_cmd, broadcast_cmd,
    changetime_cmd, ban_cmd, unban_cmd, button_callback
)

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(ChatMemberHandler(my_chat_member_handler, ChatMemberHandler.MY_CHAT_MEMBER))
    app.add_handler(CallbackQueryHandler(button_callback))

    # User Commands
    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("harem", harem_cmd))
    app.add_handler(CommandHandler("search", search_cards_cmd))
    app.add_handler(CommandHandler("profile", profile_cmd))
    app.add_handler(CommandHandler("Nexus", nexus_cmd))
    app.add_handler(CommandHandler("daily", daily_cmd))
    app.add_handler(CommandHandler("claim", claim_cmd))
    app.add_handler(CommandHandler("balance", balance_cmd))
    app.add_handler(CommandHandler("market", market_cmd))
    app.add_handler(CommandHandler("sell", sell_cmd))
    app.add_handler(CommandHandler("buy", buy_cmd))
    app.add_handler(CommandHandler("delist", delist_cmd))
    app.add_handler(CommandHandler("trade", trade_cmd))
    app.add_handler(CommandHandler("gift", gift_cmd))
    app.add_handler(CommandHandler("duel", duel_cmd))
    app.add_handler(CommandHandler("upgrade", upgrade_cmd))
    app.add_handler(CommandHandler("fav", fav_cmd))
    app.add_handler(CommandHandler("unfav", unfav_cmd))
    app.add_handler(CommandHandler("hmode", hmode_cmd))
    app.add_handler(CommandHandler("check", check_card_cmd))
    app.add_handler(CommandHandler("top", top_cmd))
    app.add_handler(CommandHandler("rankings", top_cmd))
    app.add_handler(CommandHandler("ctop", ctop_cmd))

    # Admin & Owner Commands
    app.add_handler(CommandHandler("addcard", addcard_cmd))
    app.add_handler(CommandHandler("removecard", remove_card_cmd))
    app.add_handler(CommandHandler("gcoin", givecoins_cmd))
    app.add_handler(CommandHandler("usercards", user_cards_cmd))
    app.add_handler(CommandHandler("broadcast", broadcast_cmd))
    app.add_handler(CommandHandler("changetime", changetime_cmd))
    app.add_handler(CommandHandler("ban", ban_cmd))
    app.add_handler(CommandHandler("unban", unban_cmd))

    print("🤖 Bot is starting successfully with all advanced features...")
    app.run_polling()

if __name__ == "__main__":
    main()
