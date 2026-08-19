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
    return "<h1>Nexus Character Engine Online!</h1>"

def run_web():
    app.run(host='0.0.0.0', port=PORT)

# --- DATABASE STORAGE ---
DATA_FILE = "nexus_data.json"

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {"users": {}, "cards": [], "promo_codes": {"NEXUS2026": 1000}}

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

# --- HANDLER FUNCTIONS ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "<b>⚡ Welcome to Nexus Character Bot! ⚡</b>\n\n"
        "<b>🇲🇲 မြန်မာ:</b> Character များကို စုဆောင်းပါ၊ မိတ်ဆွေများနှင့် လဲလှယ်ပါ၊ Mini-games များဆော့ပြီး Coins ရှာပါ။\n"
        "<b>🇬🇧 English:</b> Collect characters, trade with friends, play mini-games to earn coins!\n\n"
        "👉 Press <b>/guide</b> to see game details."
    )
    await update.message.reply_text(text, parse_mode="HTML")

async def guide(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "<b>📖 NEXUS GAME GUIDE / ကစားနည်းလမ်းညွှန်</b>\n\n"
        "1. Group ထဲ စာများများရိုက်ပြီး Character Spawn လာပါက <code>/nexus</code> သို့ <code>/catch</code> ဖြင့် ဖမ်းယူပါ။\n"
        "2. မိမိ Character များကို <code>/vault</code> တွင် ပြန်ကြည့်ပါ။\n"
        "3. နေ့စဉ် Coins များကို <code>/daily</code> သို့ <code>/weekly</code> ဖြင့် Claim ယူပါ။\n"
        "4. Coins များ တိုးပွားရန် <code>/spin</code> သို့မဟုတ် <code>/gambit</code> Mini-games များ ကစားပါ။"
    )
    await update.message.reply_text(text, parse_mode="HTML")

async def catch_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    u = get_user(user.id, user.first_name)
    chat_id = update.effective_chat.id

    if chat_id not in active_spawns or active_spawns[chat_id] is None:
        await update.message.reply_text("❌ ဖမ်းယူရန် Character မရှိသေးပါ (No spawned character right now)!")
        return
        
    card = active_spawns[chat_id]
    active_spawns[chat_id] = None
    u["cards"].append({"card": card, "level": 1, "quality": random.randint(75, 100)})
    save_data()
    
    await update.message.reply_text(f"🎉 <b>{user.first_name}</b> captured [{card['rarity']}] <b>{card['name']}</b>!", parse_mode="HTML")

async def vault(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = get_user(update.effective_user.id, update.effective_user.first_name)
    if not u["cards"]:
        await update.message.reply_text("❌ သင့် Vault ထဲတွင် Character မရှိသေးပါ။ (Your vault is empty!)")
        return
    text = f"🌸 <b>{update.effective_user.first_name}'s Nexus Vault ({len(u['cards'])}):</b>\n\n"
    for i, c in enumerate(u["cards"][:10], 1):
        text += f"{i}. [{c['card']['rarity']}] <b>{c['card']['name']}</b>\n"
    await update.message.reply_text(text, parse_mode="HTML")

async def filter_vault(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🎭 Vault Filter Active! Use `/vault` with rarity tag.")

async def inspect(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❌ Usage: `/inspect <character_name_or_id>`")
        return
    query = context.args[0].lower()
    card = next((c for c in cards_db if query in c["name"].lower() or c["id"] == query), None)
    if card:
        text = f"🔍 <b>Character Specs:</b>\nName: {card['name']}\nAnime: {card['anime']}\nRarity: {card['rarity']}\nPower: {card['power']}"
        await update.message.reply_text(text, parse_mode="HTML")
    else:
        await update.message.reply_text("❌ Character မတွေ့ရှိပါ။")

async def fav(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = get_user(update.effective_user.id, update.effective_user.first_name)
    if context.args:
        u["favorites"].append(context.args[0])
        save_data()
        await update.message.reply_text("❤️ Favorites ထဲသို့ ထည့်သွင်းလိုက်ပါပြီ!")
    else:
        await update.message.reply_text("❌ Usage: `/fav <character_id>`")

async def gift(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🎁 Gift: User ၏ စာကို Reply ပြန်ပြီး `/gift <card_no>` ဟု ရိုက်ပေးပို့ပါ။")

async def trade(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🤝 Trade System: `/trade <user_id> <your_card_no> <their_card_no>`")

async def search_char(update: Update, context: ContextTypes.DEFAULT_TYPE):
    c = random.choice(cards_db)
    await update.message.reply_text(f"🔍 <b>Nexus Database Discovery:</b> [{c['rarity']}] <b>{c['name']}</b> ({c['anime']})", parse_mode="HTML")

async def daily(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = get_user(update.effective_user.id, update.effective_user.first_name)
    u["coins"] += 500
    save_data()
    await update.message.reply_text(f"💰 Claimed Daily Bonus: +500 Coins! (Balance: {u['coins']})")

async def weekly(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = get_user(update.effective_user.id, update.effective_user.first_name)
    u["coins"] += 2500
    save_data()
    await update.message.reply_text(f"🎁 Claimed Weekly Drop: +2500 Coins! (Balance: {u['coins']})")

async def wallet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = get_user(update.effective_user.id, update.effective_user.first_name)
    await update.message.reply_text(f"🏦 <b>{update.effective_user.first_name}'s Nexus Wallet:</b>\n💰 Coins: {u['coins']}\n🪙 Tokens: {u['tokens']}", parse_mode="HTML")

async def send_coins(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        target_id, amount = context.args[0], int(context.args[1])
        u = get_user(update.effective_user.id)
        if u["coins"] >= amount:
            u["coins"] -= amount
            target = get_user(target_id)
            target["coins"] += amount
            save_data()
            await update.message.reply_text(f"💸 Coins {amount} အား User {target_id} သို့ ပို့ပြီးပါပြီ။")
        else:
            await update.message.reply_text("❌ Coins မလုံလောက်ပါ။")
    except Exception:
        await update.message.reply_text("❌ Usage: `/send <user_id> <amount>`")

async def emporium(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = "🛒 <b>NEXUS EMPORIUM (SHOP):</b>\n"
    for c in cards_db:
        text += f"• ID: <code>{c['id']}</code> - {c['name']} ({c['price']} Coins)\n"
    await update.message.reply_text(text, parse_mode="HTML")

async def spin_wheel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = get_user(update.effective_user.id, update.effective_user.first_name)
    if u["coins"] < 200:
        await update.message.reply_text("❌ Spin လှည့်ရန် Coin 200 လိုအပ်ပါသည်။")
        return
    u["coins"] -= 200
    reward = random.choice([0, 100, 300, 500, 1000])
    u["coins"] += reward
    save_data()
    await update.message.reply_text(f"🎡 <b>Nexus Wheel Spin!</b> Won {reward} Coins! (Balance: {u['coins']})", parse_mode="HTML")

async def gambit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = get_user(update.effective_user.id, update.effective_user.first_name)
    won = random.choice([True, False])
    if won:
        u["coins"] += 300
        msg = "💣 Gambit Success! Won +300 Coins!"
    else:
        u["coins"] = max(0, u["coins"] - 100)
        msg = "💥 Gambit Failed! Lost 100 Coins."
    save_data()
    await update.message.reply_text(msg)

async def tictactoe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("⚔️ Tic Tac Toe Challenge initiated! Reply to player to start `/ttt`.")

async def leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sorted_users = sorted(user_db.items(), key=lambda x: x[1]['coins'], reverse=True)[:5]
    text = "🥇 <b>NEXUS GLOBAL LEADERBOARD:</b>\n"
    for i, (uid, udata) in enumerate(sorted_users, 1):
        text += f"{i}. {udata.get('name', 'Player')} - {udata['coins']} Coins\n"
    await update.message.reply_text(text, parse_mode="HTML")

async def poster(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = get_user(update.effective_user.id, update.effective_user.first_name)
    await update.message.reply_text(f"🏴‍☠️ <b>NEXUS WANTED POSTER</b>\nName: {update.effective_user.first_name}\nBounty Value: 💰 {u['coins'] * 10} Coins", parse_mode="HTML")

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
        await update.message.reply_text(f"🎉 Promo Code အောင်မြင်ပါသည်။ +{reward} Coins ရရှိလိုက်ပါပြီ။")
    else:
        await update.message.reply_text("❌ Promo Code မမှန်ပါ။")

async def staff_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id): return
    await update.message.reply_text("🛡️ <b>Nexus Staff Panel Opened.</b>")

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
        caption = f"⚡ <b>A NEXUS CHARACTER APPEARED!</b> ⚡\n\nName: <b>{card['name']}</b>\nRarity: {card['rarity']}\nUse <code>/nexus</code> or <code>/catch</code> to capture!"
        await context.bot.send_photo(chat_id=chat_id, photo=card['image'], caption=caption, parse_mode="HTML")

# --- BILINGUAL MENU CONFIGURATION ---
async def post_init(application):
    # 🇬🇧 English Commands
    en_commands = [
        BotCommand("start", "Start Nexus bot & main menu"),
        BotCommand("guide", "Learn how to play"),
        BotCommand("nexus", "Capture spawned character"),
        BotCommand("catch", "Alternative command to catch character"),
        BotCommand("vault", "View your character collection"),
        BotCommand("filter", "Filter vault by rarity"),
        BotCommand("inspect", "View character details"),
        BotCommand("fav", "Add character to favorites"),
        BotCommand("gift", "Send a character to a friend"),
        BotCommand("trade", "Trade characters with users"),
        BotCommand("search", "Search character database"),
        BotCommand("daily", "Claim daily free coins"),
        BotCommand("weekly", "Claim weekly massive coins"),
        BotCommand("wallet", "Check coins & tokens balance"),
        BotCommand("send", "Transfer coins to user"),
        BotCommand("emporium", "Nexus shop & market"),
        BotCommand("spin", "Spin lucky wheel for coins"),
        BotCommand("gambit", "Play minefield mini-game"),
        BotCommand("ttt", "Host Tic Tac Toe betting match"),
        BotCommand("top", "Global top wealth leaderboard"),
        BotCommand("poster", "Generate custom Wanted Poster"),
        BotCommand("redeem", "Redeem secret promo code"),
        BotCommand("staff", "Open Nexus Staff Panel"),
    ]

    # 🇲🇲 Burmese (မြန်မာ) Commands
    my_commands = [
        BotCommand("start", "ဘော့စတင်ရန်နှင့် Menu ကြည့်ရန်"),
        BotCommand("guide", "ကစားနည်း လမ်းညွှန် ကြည့်ရန်"),
        BotCommand("nexus", "ကျလာသော Character ကို ဖမ်းယူရန်"),
        BotCommand("catch", "Character ကောက်ယူရန် (အပို)"),
        BotCommand("vault", "မိမိ Character Collection ကြည့်ရန်"),
        BotCommand("filter", "Collection အား Rarity အလိုက် စစ်ထုတ်ရန်"),
        BotCommand("inspect", "Character အသေးစိတ် အချက်အလက် ကြည့်ရန်"),
        BotCommand("fav", "Favorites ထဲသို့ Character ထည့်ရန်"),
        BotCommand("gift", "သူငယ်ချင်းထံ Character လက်ဆောင်ပေးရန်"),
        BotCommand("trade", "User အချင်းချင်း Character လဲလှယ်ရန်"),
        BotCommand("search", "Character များကို ရှာဖွေရန်"),
        BotCommand("daily", "နေ့စဉ် အခမဲ့ Coins ရယူရန်"),
        BotCommand("weekly", "အပတ်စဉ် ကံစမ်း Coins ရယူရန်"),
        BotCommand("wallet", "မိမိ၏ Coin & Token လက်ကျန် ကြည့်ရန်"),
        BotCommand("send", "အခြားသူထံ Coins လွှဲပြောင်းရန်"),
        BotCommand("emporium", "Character ဆိုင်သို့ သွားရန်"),
        BotCommand("spin", "Lucky Wheel စက်လှည့်ရန်"),
        BotCommand("gambit", "Minesweeper Mini-game ကစားရန်"),
        BotCommand("ttt", "Tic Tac Toe လောင်းကြေးပွဲ စတင်ရန်"),
        BotCommand("top", "ထိပ်တန်း Top Players ဇယား ကြည့်ရန်"),
        BotCommand("poster", "မိမိ၏ Wanted Poster ဖန်တီးရန်"),
        BotCommand("redeem", "Promo Code ထည့်သွင်း အသုံးပြုရန်"),
        BotCommand("staff", "Staff Panel ဖွင့်ရန် (Admin Only)"),
    ]

    await application.bot.set_my_commands(en_commands)
    await application.bot.set_my_commands(my_commands, language_code="my")

# --- LAUNCH ENGINE ---
if __name__ == "__main__":
    Thread(target=run_web).start()

    app = ApplicationBuilder().token(BOT_TOKEN).post_init(post_init).build()

    # Handlers Registration
    handlers = [
        CommandHandler("start", start), CommandHandler("guide", guide),
        CommandHandler("nexus", catch_cmd), CommandHandler("catch", catch_cmd),
        CommandHandler("vault", vault), CommandHandler("filter", filter_vault),
        CommandHandler("inspect", inspect), CommandHandler("fav", fav),
        CommandHandler("gift", gift), CommandHandler("trade", trade),
        CommandHandler("search", search_char), CommandHandler("daily", daily),
        CommandHandler("weekly", weekly), CommandHandler("wallet", wallet),
        CommandHandler("send", send_coins), CommandHandler("emporium", emporium),
        CommandHandler("spin", spin_wheel), CommandHandler("gambit", gambit),
        CommandHandler("ttt", tictactoe), CommandHandler("top", leaderboard),
        CommandHandler("poster", poster), CommandHandler("redeem", redeem),
        CommandHandler("staff", staff_panel)
    ]
    
    for h in handlers:
        app.add_handler(h)

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_messages))

    print("Nexus Unique Bilingual Engine Running...")
    app.run_polling()
