import sys
import os
import asyncio
from threading import Thread

base_dir = os.path.dirname(os.path.abspath(__file__))
if base_dir not in sys.path:
    sys.path.insert(0, base_dir)

from flask import Flask
from telegram.ext import Application
from config import BOT_TOKEN
import handlers

web_app = Flask(__name__)

@web_app.route('/')
def home():
    return "Nexus Complete RPG Card Bot Engine Online!"

def run_flask():
    port = int(os.getenv("PORT", 8080))
    web_app.run(host="0.0.0.0", port=port)

async def run_bot():
    app = Application.builder().token(BOT_TOKEN).build()

    # Register handlers from handlers.py
    handlers.register_all_handlers(app)

    print("🚀 Complete Advanced Nexus Card Bot System Active!")
    
    async with app:
        await app.start()
        await app.updater.start_polling()
        await asyncio.Event().wait()

def main():
    Thread(target=run_flask, daemon=True).start()
    asyncio.run(run_bot())

if __name__ == "__main__":
    main()
