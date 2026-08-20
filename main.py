import random
from threading import Thread
from admin_system import (
    addadmin_cmd,
    addcard_cmd,
    allow_group_cmd,
    changetime_cmd,
    givecards_cmd,
    givecoins_cmd,
    track_group_addition,
    usercards_cmd,
    verify_group_eligibility,
)
from config import BOT_TOKEN, DEFAULT_SPAWN_THRESHOLD, PORT
from flask import Flask
from market_system import buy_cmd, delist_cmd, gift_cmd, market_cmd, sell_cmd, trade_cmd
from models import CardBase, ChatSettings, SessionLocal, User, UserCard
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CallbackQueryHandler,
    ChatMemberHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)
from user_system import (
    balance_cmd,
    check_cmd,
    check_force_join,
    claim_cmd,
    ctop_cmd,
    daily_cmd,
    duel_cmd,
    fav_cmd,
    harem_callback,
    harem_cmd,
    help_callback,
    help_cmd,
    profile_cmd,
    search_cmd,
    sellprice_cmd,
    setlang_cmd,
    start_cmd,
    today_nexus_catch_cmd,
    top_cmd,
    unfav_cmd,
    upgrade_cmd,
)

app = Flask(__name__)


@app.route("/")
def home():
    return "Bot Online"


def run_web():
    app.run(host="0.0.0.0", port=PORT)


active_spawns = {}


async def handle_spawns(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text or update.message.text.startswith("/"):
        return

    chat = update.effective_chat
    if chat.type == "private":
        return

    is_eligible, err_msg = await verify_group_eligibility(update, context)
    if not is_eligible:
        return

    chat_id = str(chat.id)
    session = SessionLocal()
    try:
        setting = session.query(ChatSettings).filter(ChatSettings.chat_id == chat_id).first()
        if not setting:
            setting = ChatSettings(chat_id=chat_id, spawn_threshold=DEFAULT_SPAWN_THRESHOLD, current_msg_count=1)
            session.add(setting)
        else:
            setting.current_msg_count += 1

        if setting.current_msg_count >= setting.spawn_threshold:
            setting.current_msg_count = 0
            cards = session.query(CardBase).all()
            if cards:
                selected = random.choice(cards)
                active_spawns[chat_id] = selected.name.lower()
                caption = f"⚡ **A WILD CARD SPAWNED!**\n\n🌟 Rarity: **{selected.rarity}**\n`/Nexus <Card_Name>` ဖြင့် ဖမ်းယူပါ!"
                await context.bot.send_photo(chat_id=int(chat_id), photo=selected.image_url, caption=caption, parse_mode="Markdown")

        session.commit()
    finally:
        session.close()


async def nexus_catch_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat

    if chat.type != "private":
        is_eligible, err_msg = await verify_group_eligibility(update, context)
        if not is_eligible:
            await update.message.reply_text(err_msg, parse_mode="Markdown")
            return

    chat_id = str(chat.id)
    if chat_id not in active_spawns:
        return

    guess = " ".join(context.args).strip().lower()
    correct_name = active_spawns[chat_id]

    if guess == correct_name:
        del active_spawns[chat_id]
        uid = str(update.effective_user.id)
        session = SessionLocal()
        try:
            user = session.query(User).filter(User.id == uid).first()
            if not user:
                user = User(id=uid, first_name=update.effective_user.first_name)
                session.add(user)

            card = session.query(CardBase).filter(CardBase.name.ilike(correct_name)).first()
            if card:
                card.total_prints += 1
                session.add(UserCard(user_id=uid, card_id=card.id, print_number=card.total_prints, chat_id=chat_id))
                session.commit()
                await update.message.reply_text(
                    f"🎉 **{update.effective_user.first_name}** မှ `{card.name}` (Print #{card.total_prints}) ကို ဖမ်းယူလိုက်ပါပြီ!",
                    parse_mode="Markdown",
                )
        finally:
            session.close()


async def join_check_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "check_join_harem":
        is_joined = await check_force_join(query.from_user.id, context)
        if is_joined:
            await query.message.edit_text("✅ Join လုပ်ဆောင်မှု အောင်မြင်ပါသည်။ `/harem` command ကို ပြန်လည် ရိုက်နှိပ်ပါ။")
        else:
            await query.answer("❌ Link 2 ခုလုံးကို Join ရန် လိုအပ်သေးသည်!", show_alert=True)


if __name__ == "__main__":
    Thread(target=run_web).start()
    bot = ApplicationBuilder().token(BOT_TOKEN).build()

    bot.add_handler(CallbackQueryHandler(join_check_callback, pattern="^check_join_harem$"))
    bot.add_handler(CallbackQueryHandler(harem_callback, pattern="^harem_"))
    bot.add_handler(CallbackQueryHandler(help_callback, pattern="^help_"))
    bot.add_handler(ChatMemberHandler(track_group_addition, ChatMemberHandler.MY_CHAT_MEMBER))

    # User Command Handlers
    bot.add_handler(CommandHandler("start", start_cmd))
    bot.add_handler(CommandHandler("help", help_cmd))
    bot.add_handler(CommandHandler("harem", harem_cmd))
    bot.add_handler(CommandHandler("search", search_cmd))
    bot.add_handler(CommandHandler("profile", profile_cmd))
    bot.add_handler(CommandHandler("top", top_cmd))
    bot.add_handler(CommandHandler("rankings", top_cmd))
    bot.add_handler(CommandHandler("ctop", ctop_cmd))
    bot.add_handler(CommandHandler("daily", daily_cmd))
    bot.add_handler(CommandHandler("balance", balance_cmd))
    bot.add_handler(CommandHandler("sellprice", sellprice_cmd))
    bot.add_handler(CommandHandler("claim", claim_cmd))
    bot.add_handler(CommandHandler("check", check_cmd))
    bot.add_handler(CommandHandler("fav", fav_cmd))
    bot.add_handler(CommandHandler("unfav", unfav_cmd))
    bot.add_handler(CommandHandler("todayNexusCatch", today_nexus_catch_cmd))
    bot.add_handler(CommandHandler("duel", duel_cmd))
    bot.add_handler(CommandHandler("upgrade", upgrade_cmd))
    bot.add_handler(CommandHandler("Nexus", nexus_catch_cmd))
    bot.add_handler(CommandHandler("setlang", setlang_cmd))

    # Market Handlers
    bot.add_handler(CommandHandler("market", market_cmd))
    bot.add_handler(CommandHandler("sell", sell_cmd))
    bot.add_handler(CommandHandler("buy", buy_cmd))
    bot.add_handler(CommandHandler("delist", delist_cmd))
    bot.add_handler(CommandHandler("trade", trade_cmd))
    bot.add_handler(CommandHandler("gift", gift_cmd))

    # Admin & Owner Handlers
    bot.add_handler(CommandHandler("addcard", addcard_cmd))
    bot.add_handler(CommandHandler("givecoins", givecoins_cmd))
    bot.add_handler(CommandHandler("givecards", givecards_cmd))
    bot.add_handler(CommandHandler("changetime", changetime_cmd))
    bot.add_handler(CommandHandler("addadmin", addadmin_cmd))
    bot.add_handler(CommandHandler("allow", allow_group_cmd))
    bot.add_handler(CommandHandler("usercards", usercards_cmd))

    # Message Handler
    bot.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_spawns))

    print("⚡ Bot Activated Successfully!")
    bot.run_polling()
