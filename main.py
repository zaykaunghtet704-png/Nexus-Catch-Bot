import random
from threading import Thread
from admin_system import (
    addcard_cmd,
    admin_callback_handler,
    adminpanel_cmd,
    backup_cmd,
    decspawn_cmd,
    givecoins_cmd,
    incspawn_cmd,
    is_admin,
    setspawn_cmd,
)
from config import BOT_TOKEN, DEFAULT_SPAWN_THRESHOLD, PORT
from flask import Flask
from models import BotConfig, CardBase, ChatSettings, SessionLocal, User, UserCard
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)
from user_system import (
    daily_cmd,
    inventory_cmd,
    leaderboard_cmd,
    lock_cmd,
    profile_cmd,
    roll_cmd,
)

app = Flask(__name__)


@app.route("/")
def home():
    return "Bot Operational"


def run_web():
    app.run(host="0.0.0.0", port=PORT)


active_spawns = {}


async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "✨ **Bot System Online!**\nUse `/profile`, `/roll`, `/daily`, or `/adminpanel`",
        parse_mode="Markdown",
    )


async def handle_spawns(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if (
        not update.message
        or not update.message.text
        or update.message.text.startswith("/")
    ):
        return

    chat_id = str(update.effective_chat.id)
    session = SessionLocal()
    try:
        m = (
            session.query(BotConfig)
            .filter(BotConfig.key == "maintenance_mode")
            .first()
        )
        if m and m.value == "true" and not is_admin(update.effective_user.id):
            return

        setting = (
            session.query(ChatSettings)
            .filter(ChatSettings.chat_id == chat_id)
            .first()
        )
        if not setting:
            setting = ChatSettings(
                chat_id=chat_id,
                spawn_threshold=DEFAULT_SPAWN_THRESHOLD,
                current_msg_count=1,
            )
            session.add(setting)
        else:
            setting.current_msg_count += 1

        if setting.current_msg_count >= setting.spawn_threshold:
            setting.current_msg_count = 0
            cards = session.query(CardBase).all()
            if cards:
                selected = random.choice(cards)
                active_spawns[chat_id] = selected.name.lower()
                caption = f"⚡ **A WILD CHARACTER APPEARED!**\n\n🌟 Rarity: **{selected.rarity}**\n`/catch <name>` ဖြင့် ဖမ်းယူပါ!"
                await context.bot.send_photo(
                    chat_id=int(chat_id),
                    photo=selected.image_url,
                    caption=caption,
                    parse_mode="Markdown",
                )

        session.commit()
    except Exception as e:
        print(f"Spawn Error: {e}")
    finally:
        session.close()


async def catch_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    if chat_id not in active_spawns:
        await update.message.reply_text("❌ ဖမ်းယူရန် Card မရှိသေးပါ။")
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

            card = (
                session.query(CardBase)
                .filter(CardBase.name.ilike(correct_name))
                .first()
            )
            if card:
                card.total_prints += 1
                new_uc = UserCard(
                    user_id=uid,
                    card_id=card.id,
                    print_number=card.total_prints,
                )
                session.add(new_uc)
                session.commit()
                await update.message.reply_text(
                    f"🎉 **{update.effective_user.first_name}** မှ `{card.name}` (Print #{card.total_prints}) ကို ဖမ်းယူလိုက်ပါပြီ!",
                    parse_mode="Markdown",
                )
        finally:
            session.close()
    else:
        await update.message.reply_text(
            "❌ နာမည် မှားနေပါသည်။ ပြန်လည် ကြိုးစားပါ။"
        )


if __name__ == "__main__":
    Thread(target=run_web).start()
    bot = ApplicationBuilder().token(BOT_TOKEN).build()

    # User Commands
    bot.add_handler(CommandHandler("start", start_cmd))
    bot.add_handler(CommandHandler("profile", profile_cmd))
    bot.add_handler(CommandHandler("daily", daily_cmd))
    bot.add_handler(CommandHandler("inventory", inventory_cmd))
    bot.add_handler(CommandHandler("roll", roll_cmd))
    bot.add_handler(CommandHandler("lock", lock_cmd))
    bot.add_handler(CommandHandler("leaderboard", leaderboard_cmd))
    bot.add_handler(CommandHandler("catch", catch_cmd))

    # Admin Commands & Callbacks
    bot.add_handler(CommandHandler("adminpanel", adminpanel_cmd))
    bot.add_handler(
        CallbackQueryHandler(admin_callback_handler, pattern="^adm_")
    )
    bot.add_handler(CommandHandler("addcard", addcard_cmd))
    bot.add_handler(CommandHandler("givecoins", givecoins_cmd))
    bot.add_handler(CommandHandler("backup", backup_cmd))

    # Spawn Threshold Management Commands
    bot.add_handler(CommandHandler("setspawn", setspawn_cmd))
    bot.add_handler(CommandHandler("incspawn", incspawn_cmd))
    bot.add_handler(CommandHandler("decspawn", decspawn_cmd))

    # Group Spawn Handler
    bot.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_spawns)
    )

    print("⚡ Fixed Enterprise Bot Active!")
    bot.run_polling()
