from threading import Thread
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, 
    MessageHandler, filters
)

from config import BOT_TOKEN
from services import run_flask
from handlers import (
    start_cmd, help_cmd, claim_cmd, hmode_cmd, view_cmd, upgrade_cmd,
    botstats_cmd, suda_cmd, add_sudo_cmd, broadcast_cmd,
    hmode_callback, captcha_claim_callback, handle_group_messages
)

def main():
    # Render Web Port Binding
    Thread(target=run_flask, daemon=True).start()
    
    app = Application.builder().token(BOT_TOKEN).build()
    
    # User Handlers
    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("claim", claim_cmd))
    app.add_handler(CommandHandler("hmode", hmode_cmd))
    app.add_handler(CommandHandler("view", view_cmd))
    app.add_handler(CommandHandler("upgrade", upgrade_cmd))
    
    # System & Admin Handlers
    app.add_handler(CommandHandler(["botstats", "suda"], botstats_cmd))
    app.add_handler(CommandHandler("sudlist", suda_cmd))
    app.add_handler(CommandHandler("addsudo", add_sudo_cmd))
    app.add_handler(CommandHandler("broadcast", broadcast_cmd))
    
    # Callbacks & Group Listener
    app.add_handler(CallbackQueryHandler(hmode_callback, pattern="^hmode_"))
    app.add_handler(CallbackQueryHandler(captcha_claim_callback, pattern="^cap_claim_"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_group_messages))
    
    print("🚀 Nexus Fully Decoratable Card Bot Online!")
    app.run_polling()

if __name__ == "__main__":
    main()
