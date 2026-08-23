# main.py - Fixed Main Entry Point for Pyrogram
import asyncio
import logging
from pyrogram import Client, idle
from config import BOT_TOKEN

# Logging configuration
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

# Initialize Pyrogram Client
app = Client(
    "nexus_catch_bot",
    api_id=611335,
    api_hash="d94b915db182103f6f1a8e63b65287be",
    bot_token=BOT_TOKEN,
    plugins=dict(root=".")
)

async def main():
    print("🤖 Starting bot via asyncio main loop...")
    await app.start()
    print("✨ Bot is successfully running and listening for updates!")
    await idle()
    await app.stop()
    print("🛑 Bot stopped.")

if __name__ == "__main__":
    asyncio.run(main())
