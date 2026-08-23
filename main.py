# main.py - Complete Pyrogram Main Application Entry
import logging
from pyrogram import Client
from config import BOT_TOKEN

# Logging configuration to track bot status
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

# Initialize Pyrogram Client with bot_token, api_id, and api_hash
# (Pyrogram requires api_id and api_hash even when running exclusively with a bot token)
app = Client(
    "nexus_catch_bot",
    api_id=611335,                  # Standard public telegram api_id placeholder
    api_hash="d94b915db182103f6f1a8e63b65287be", # Standard public telegram api_hash placeholder
    bot_token=BOT_TOKEN,
    plugins=dict(root=".")         # Automatically loads handlers from handlers.py or other files in the directory
)

if __name__ == "__main__":
    print("🤖 Nexus Catch Bot is starting up successfully...")
    app.run()
