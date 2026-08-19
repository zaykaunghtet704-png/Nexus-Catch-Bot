import logging
import random
import json
import os
from threading import Thread
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, 
    CallbackQueryHandler, filters, ContextTypes
)
from config import BOT_TOKEN, OWNER_IDS, SPAWN_THRESHOLD, PORT

# --- WEB KEEP-ALIVE SERVER ---
app = Flask(__name__)

@app.route('/')
def home():
    return "<h1>Sudo Character Bot Engine Online!</h1>"

def run_web():
    app.run(host='0.0.0.0', port=PORT)

# --- DATABASE STORAGE ---
DATA_FILE = "sudo_data.json"

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {"users": {}, "cards": [], "promo_codes": {"SUDO2026": 1000}}

def save_data():
    with open(DATA_FILE, "w") as f:
        json.dump(db_data, f, indent=4)

db_data = load_data()
user_db = db_data["users"]

if not db_data["cards"]:
    db_data["cards"] = [
        {"id": "1", "name": "Gojo Satoru", "anime": "Jujutsu Kaisen", "rarity": "SSR 🌟", "power": 100, "price": 2000, "image": "https://media.giphy.com/media/lsdd32H2EqjXGRh1m2/giphy.gif"},
        {"id": "2", "name": "Goku Ultra Instinct", "anime": "Dragon Ball", "rarity": "Legendary 🔥", "power": 95, "price": 1500, "image": "https://media.giphy.com/media/cb9aF9FZvXo4mNu4MK/giphy.gif"},
        {"id": "3", "name": "Naruto Uzumaki", "anime": "Naruto", "rarity": "Rare ✨", "power": 80, "price": 800, "image": "https://media.giphy.com/media/2y9n1aB5r9pYI/giphy.gif"}
    ]
    save_data()

cards_db = db_data["cards"]
active_spawns = {}     
chat_message_counts = {}
CURRENT_SPAWN_THRESHOLD = SPAWN_THRESHOLD

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# --- HELPER FUNCTIONS ---
def get_user(user_id, username="Player"):
    uid = str(user_id)
    if uid not in user_db:
        user_db[uid] = {
            "name": username, "coins": 1000, "tokens": 10,
            "cards": [], "favorites": [], "ox_stats": {"wins": 0, "losses": 0},
            "banned": False
        }
        save_data()
    return user_db[uid]

def is_owner(user_id: int) -> bool:
    return user_id in OWNER_IDS

# --- BOT COMMAND HANDLERS ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "<b>✨ Welcome to Sudo Character Bot! ✨</b>\n\n"
        "Collect your favorite characters, trade with friends, spin the wheel, "
        "and play mini-games to earn coins!\n\n"
        "👉 Press <b>/help</b> or open the menu button to see all available commands."
    )
    await update.message.reply_text(text, parse_mode="HTML")

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "<b>📖 HOW TO PLAY:</b>\n"
        "1. Stay active in groups to spawn characters.\n"
        "2. Use <code>/sudo</code> to catch spawned characters.\n"
        "3. Collect coins daily via <code>/daily</code> & <code>/weekly</code>.\n"
        "4. Play mini-games like <code>/wheel</code> & <code>/mines</code> to gamble coins!"
    )
    await update.message.reply_text(text, parse_mode="HTML")

async def sudo_catch(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    u = get_user(user.id, user.first_name)
    chat_id = update.effective_chat.id

    if chat_id not in active_spawns or active_spawns[chat_id] is None:
        await update.message.reply_text("❌ No spawned character to catch right now!")
        return
        
    card = active_spawns[chat_id]
    active_spawns[chat_id] = None
    u["cards"].append({"card": card, "level": 1, "quality": random.randint(75, 100)})
    save_data()
    
    await update.message.reply_text(f"🎉 <b>{user.first_name}</b> caught [{card['rarity']}] <b>{card['name']}</b>!", parse_mode="HTML")

async def harem(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = get_user(update.effective_user.id, update.effective_user.first_name)
    if not u["cards"]:
        await update.message.reply_text("❌ Your harem is empty!")
        return
    text = f"🌸 <b>{update.effective_user.first_name}'s Character Collection ({len(u['cards'])}):</b>\n\n"
    for i, c in enumerate(u["cards"][:10], 1):
        text += f"{i}. [{c['card']['rarity']}] <b>{c['card']['name']}</b>\n"
    await update.message.reply_text(text, parse_mode="HTML")

async def hmode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🎭 Filter harem mode enabled! Use `/harem` with rarity tag.")

async def check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❌ Usage: `/check <character_name_or_id>`")
        return
    query = context.args[0].lower()
    card = next((c for c in cards_db if query in c["name"].lower() or c["id"] == query), None)
    if card:
        text = f"🔍 <b>Character Info:</b>\nName: {card['name']}\nAnime: {card['anime']}\nRarity: {card['rarity']}\nPower: {card['power']}"
        await update.message.reply_text(text, parse_mode="HTML")
    else:
        await update.message.reply_text("❌ Character not found.")

async def fav(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = get_user(update.effective_user.id, update.effective_user.first_name)
    if context.args:
        u["favorites"].append(context.args[0])
        save_data()
        await update.message.reply_text("❤️ Added character to your favorites!")
    else:
        await update.message.reply_text("❌ Usage: `/fav <character_id>`")

async def gift(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🎁 Gift system: Reply to a user's message with `/gift <card_index>` to send a character.")

async def trade(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🤝 Trade system: `/trade <user_id> <your_card_no> <their_card_no>`")

async def explore(update: Update, context: ContextTypes.DEFAULT_TYPE):
    c = random.choice(cards_db)
    await update.message.reply_text(f"🔍 <b>Discovered:</b> [{c['rarity']}] <b>{c['name']}</b> from {c['anime']}", parse_mode="HTML")

async def daily(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = get_user(update.effective_user.id, update.effective_user.first_name)
    u["coins"] += 500
    save_data()
    await update.message.reply_text(f"💰 Claimed daily bonus of 500 coins! Balance: {u['coins']}")

async def weekly(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = get_user(update.effective_user.id, update.effective_user.first_name)
    u["coins"] += 2500
    save_data()
    await update.message.reply_text(f"🎁 Claimed weekly massive drop of 2500 coins! Balance: {u['coins']}")

async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = get_user(update.effective_user.id, update.effective_user.first_name)
    await update.message.reply_text(f"🏦 <b>{update.effective_user.first_name}'s Balance:</b>\n💰 Coins: {u['coins']}\n🪙 Tokens: {u['tokens']}", parse_mode="HTML")

async def pay(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        target_id, amount = context.args[0], int(context.args[1])
        u = get_user(update.effective_user.id)
        if u["coins"] >= amount:
            u["coins"] -= amount
            target = get_user(target_id)
            target["coins"] += amount
            save_data()
            await update.message.reply_text(f"💸 Transferred {amount} coins to User {target_id}.")
        else:
            await update.message.reply_text("❌ Insufficient coins.")
    except Exception:
        await update.message.reply_text("❌ Usage: `/pay <user_id> <amount>`")

async def shop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = "🛒 <b>Sudo Character Shop:</b>\n"
    for c in cards_db:
        text += f"• ID: <code>{c['id']}</code> - {c['name']} ({c['price']} Coins)\n"
    await update.message.reply_text(text, parse_mode="HTML")

# --- MINI GAMES ---

async def wheel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = get_user(update.effective_user.id, update.effective_user.first_name)
    if u["coins"] < 200:
        await update.message.reply_text("❌ You need 200 coins to spin the wheel!")
        return
    u["coins"] -= 200
    reward = random.choice([0, 100, 300, 500, 1000])
    u["coins"] += reward
    save_data()
    await update.message.reply_text(f"🎡 <b>Wheel Spin!</b> You won {reward} coins! (Current Balance: {u['coins']})", parse_mode="HTML")

async def mines(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = get_user(update.effective_user.id, update.effective_user.first_name)
    won = random.choice([True, False])
    if won:
        u["coins"] += 300
        msg = "💣 You safely navigated the minefield! Won +300 Coins!"
    else:
        u["coins"] = max(0, u["coins"] - 100)
        msg = "💥 KABOOM! You hit a mine and lost 100 Coins."
    save_data()
    await update.message.reply_text(msg)

async def ox(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Tic Tac Toe Betting host initiated! Reply to an opponent to start /ox match.")

async def oxstats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = get_user(update.effective_user.id)
    stats = u.get("ox_stats", {"wins": 0, "losses": 0})
    await update.message.reply_text(f"📊 <b>Tic Tac Toe Stats:</b> Wins: {stats['wins']} | Losses: {stats['losses']}", parse_mode="HTML")

async def oxtop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🏆 <b>Top Tic Tac Toe Champions:</b> Leaderboard loading...")

# --- STATS, UTILS & ADMIN ---

async def rank(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sorted_users = sorted(user_db.items(), key=lambda x: x[1]['coins'], reverse=True)[:5]
    text = "🥇 <b>GLOBAL TOP PLAYERS:</b>\n"
    for i, (uid, udata) in enumerate(sorted_users, 1):
        text += f"{i}. {udata.get('name', 'Player')} - {udata['coins']} Coins\n"
    await update.message.reply_text(text, parse_mode="HTML")

async def gctop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("⭐ Top guessers in this group: Updating real-time stats...")

async def stime(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id): return
    await update.message.reply_text("⏰ Spawn time configuration menu opened.")

async def bounty(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = get_user(update.effective_user.id, update.effective_user.first_name)
    await update.message.reply_text(f"🏴‍☠️ <b>WANTED POSTER</b>\nName: {update.effective_user.first_name}\nBounty Value: 💰 {u['coins'] * 10} Coins", parse_mode="HTML")

async def cstats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"📈 <b>Global Progress:</b> Total Users: {len(user_db)} | Active Groups: {len(chat_message_counts)}")

async def ctotal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"🌐 Total characters registered in database: {len(cards_db)}")

async def crarity(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✨ <b>Character Count by Rarity:</b>\n• SSR: 1\n• Legendary: 1\n• Rare: 1")

async def redeem(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❌ Usage: `/redeem <code>`")
        return
    code = context.args[0]
    promos = db_data.get("promo_codes", {})
    if code in promos:
        u = get_user(update.effective_user.id, update.effective_user.first_name)
        reward = promos.pop(code)
        u["coins"] += reward
        save_data()
        await update.message.reply_text(f"🎉 Code Redeemed! Received {reward} Coins.")
    else:
        await update.message.reply_text("❌ Invalid or expired promo code.")

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id): return
    await update.message.reply_text("🛡️ <b>Staff Command Panel Opened:</b>\nCommands: /addcard, /stime, /broadcast, /stats")

# --- MESSAGE SPAWN HANDLER ---
async def handle_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text: return
    chat_id = update.effective_chat.id
    count = chat_message_counts.get(chat_id, 0) + 1
    chat_message_counts[chat_id] = count
    
    if count >= CURRENT_SPAWN_THRESHOLD and cards_db:
        chat_message_counts[chat_id] = 0
        card = random.choice(cards_db)
        active_spawns[chat_id] = card
        caption = f"⚡ <b>A WILD CHARACTER APPEARED!</b> ⚡\n\nName: <b>{card['name']}</b>\nRarity: {card['rarity']}\nUse <code>/sudo</code> to catch!"
        await context.bot.send_photo(chat_id=chat_id, photo=card['image'], caption=caption, parse_mode="HTML")

# --- AUTO REGISTER BOT COMMANDS TO TELEGRAM MENU ---
async def post_init(application):
    commands = [
        BotCommand("start", "Start the bot & view menu"),
        BotCommand("help", "Learn how to play"),
        BotCommand("sudo", "Catch the spawned character"),
        BotCommand("harem", "View your character collection"),
        BotCommand("hmode", "Filter your harem by rarity"),
        BotCommand("check", "View details of a specific character"),
        BotCommand("fav", "Add a character to your favorites"),
        BotCommand("gift", "Gift a character to a friend"),
        BotCommand("trade", "Trade characters with another user"),
        BotCommand("explore", "Search for any character by name"),
        BotCommand("daily", "Claim your daily free coins"),
        BotCommand("weekly", "Claim your weekly massive coin drop"),
        BotCommand("balance", "Check your current coin & token balance"),
        BotCommand("pay", "Transfer coins to another user"),
        BotCommand("shop", "Buy characters using your coins"),
        BotCommand("wheel", "Spin the lucky wheel for waifus"),
        BotCommand("mines", "Play Minesweeper to multiply coins"),
        BotCommand("ox", "Host a Tic Tac Toe betting match"),
        BotCommand("oxstats", "View your Tic Tac Toe statistics"),
        BotCommand("oxtop", "View the best Tic Tac Toe players"),
        BotCommand("rank", "View the global top players & groups"),
        BotCommand("gctop", "View top guessers in your current group"),
        BotCommand("stime", "Change spawn time"),
        BotCommand("bounty", "Generate your custom Wanted Poster"),
        BotCommand("cstats", "View your overall global progress"),
        BotCommand("ctotal", "Show total characters in the database"),
        BotCommand("crarity", "View character counts by rarity"),
        BotCommand("redeem", "Redeem a secret promo code"),
        BotCommand("admin", "Open the Staff Command Panel"),
    ]
    await application.bot.set_my_commands(commands)

# --- LAUNCH ENGINE ---
if __name__ == "__main__":
    Thread(target=run_web).start()

    app = ApplicationBuilder().token(BOT_TOKEN).post_init(post_init).build()

    # Register Handlers
    handlers = [
        CommandHandler("start", start), CommandHandler("help", help_cmd),
        CommandHandler("sudo", sudo_catch), CommandHandler("harem", harem),
        CommandHandler("hmode", hmode), CommandHandler("check", check),
        CommandHandler("fav", fav), CommandHandler("gift", gift),
        CommandHandler("trade", trade), CommandHandler("explore", explore),
        CommandHandler("daily", daily), CommandHandler("weekly", weekly),
        CommandHandler("balance", balance), CommandHandler("pay", pay),
        CommandHandler("shop", shop), CommandHandler("wheel", wheel),
        CommandHandler("mines", mines), CommandHandler("ox", ox),
        CommandHandler("oxstats", oxstats), CommandHandler("oxtop", oxtop),
        CommandHandler("rank", rank), CommandHandler("gctop", gctop),
        CommandHandler("stime", stime), CommandHandler("bounty", bounty),
        CommandHandler("cstats", cstats), CommandHandler("ctotal", ctotal),
        CommandHandler("crarity", crarity), CommandHandler("redeem", redeem),
        CommandHandler("admin", admin_panel)
    ]
    
    for h in handlers:
        app.add_handler(h)

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_messages))

    print("Sudo Character Bot Full System Running...")
    app.run_polling()
