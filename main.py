from threading import Thread
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from Flask import Flask

from config import BOT_TOKEN
from handlers import (
    start_cmd, help_cmd, harem_cmd, profile_cmd, view_cmd, setlang_cmd,
    approvegroup_cmd, addcard_cmd, givecoin_cmd,
    on_bot_added_to_group, handle_group_messages
)

# Flask Ping Server for Cloud Deployment
web_app = Flask(__name__)

@web_app.route('/')
def home():
    return "Nexus RPG Card Bot Engine Online!"

def run_flask():
    web_app.run(host="0.0.0.0", port=8080)

def main():
    Thread(target=run_flask, daemon=True).start()

    app = Application.builder().token(BOT_TOKEN).build()

    # User Commands
    app.add_handler(CommandHandler(["start", "sratr"], start_cmd))
    app.add_handler(CommandHandler(["help", "Help"], help_cmd))
    app.add_handler(CommandHandler(["harem", "Hearm"], harem_cmd))
    app.add_handler(CommandHandler("profile", profile_cmd))
    app.add_handler(CommandHandler("view", view_cmd))
    app.add_handler(CommandHandler("setlang", setlang_cmd))

    # Admin/Owner Commands
    app.add_handler(CommandHandler("approvegroup", approvegroup_cmd))
    app.add_handler(CommandHandler("addcard", addcard_cmd))
    app.add_handler(CommandHandler("givecoin", givecoin_cmd))

    # Event Handlers
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, on_bot_added_to_group))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_group_messages))

    print("🚀 Nexus Card Bot Started Successfully!")
    app.run_polling()

if __name__ == "__main__":
    main()
