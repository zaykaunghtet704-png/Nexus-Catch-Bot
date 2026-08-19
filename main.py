import logging
import random
import json
import os
from threading import Thread
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, 
    CallbackQueryHandler, filters, ContextTypes
)
from config import BOT_TOKEN, OWNER_IDS, SPAWN_THRESHOLD, PORT

# --- WEB KEEP-ALIVE SERVER ---
app = Flask(__name__)

@app.route('/')
def home():
    return "<h1>Nexus Full-Featured Catch Engine Online!</h1>"

def run_web():
    app.run(host='0.0.0.0', port=PORT)

# --- DATABASE STORAGE (JSON AUTO-SAVE) ---
DATA_FILE = "data.json"

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {"users": {}, "cards": []}

def save_data():
    with open(DATA_FILE, "w") as f:
        json.dump(db_data, f, indent=4)

db_data = load_data()
user_db = db_data["users"]

# Default Master Cards if empty
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

# --- UTILS ---
def get_user(user_id, username="Player"):
    uid = str(user_id)
    if uid not in user_db:
        user_db[uid] = {"name": username, "coins": 1000, "cards": [], "banned": False}
        save_data()
    return user_db[uid]

def is_owner(user_id: int) -> bool:
    return user_id in OWNER_IDS

# --- GAME COMMANDS ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "<b>⚡ NEXUS ULTIMATE CARD GAME ENGINE ⚡</b>\n\n"
        "<b>🎮 Card Operations:</b>\n"
        "• /grab - ကျလာသော ကဒ်ကို ကောက်ယူရန်\n"
        "• /roll - Coins 300 သုံး၍ ကဒ်သစ် Gacha နှိုက်ရန်\n"
        "• /collection - မိမိပိုင်ဆိုင်သော ကဒ်များ ကြည့်ရန်\n"
        "• /shop & /buy &lt;card_id&gt; - ကဒ်ဆိုင်မှ ကဒ်ဝယ်ရန်\n"
        "• /burn &lt;card_index&gt; - မလိုချင်သော ကဒ်ကို Coins ပြန်ပြောင်းရန်\n\n"
        "<b>⚔️ Gameplay & Economy:</b>\n"
        "• /daily - နေ့စဉ် Daily Reward ယူရန်\n"
        "• /duel - PVP Power Battle ဆော့ရန်\n"
        "• /trade &lt;user_id&gt; &lt;my_card_no&gt; &lt;their_card_no&gt;\n"
        "• /top - Top Wealthy & Collection Leaderboard\n\n"
        "<b>👑 Owner Controls:</b>\n"
        "• /addcard | /delcard | /setspawn | /stats | /broadcast"
    )
    await update.message.reply_text(text, parse_mode="HTML")

async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    u = get_user(user.id, user.first_name)
    text = (
        f"👤 <b>PLAYER PROFILE: {user.first_name}</b>\n\n"
        f"🆔 <b>ID:</b> <code>{user.id}</code>\n"
        f"💰 <b>Coins Balance:</b> {u['coins']} Coins\n"
        f"🎴 <b>Cards Owned:</b> {len(u['cards'])}\n"
        f"🛡️ <b>Status:</b> {'Banned ❌' if u['banned'] else 'Active ✅'}"
    )
    await update.message.reply_text(text, parse_mode="HTML")

async def daily(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = get_user(update.effective_user.id, update.effective_user.first_name)
    u["coins"] += 500
    save_data()
    await update.message.reply_text(f"💰 <b>Daily Reward!</b> +500 Coins ရရှိပါပြီ။ (Balance: {u['coins']})", parse_mode="HTML")

# --- GACHA ROLL SYSTEM ---
async def roll(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = get_user(update.effective_user.id, update.effective_user.first_name)
    cost = 300
    
    if u["coins"] < cost:
        await update.message.reply_text(f"❌ Gacha Roll ရန် Coin {cost} လိုအပ်ပါသည်။ (သင့် Coins: {u['coins']})")
        return
        
    u["coins"] -= cost
    card = random.choice(cards_db)
    quality = random.randint(70, 100)
    u["cards"].append({"card": card, "level": 1, "quality": quality})
    save_data()
    
    caption = (
        f"🎰 <b>GACHA ROLL SUCCESS!</b> 🎰\n\n"
        f"<b>Card:</b> [{card['rarity']}] <b>{card['name']}</b>\n"
        f"<b>Anime:</b> {card['anime']}\n"
        f"<b>Quality:</b> {quality}%\n"
        f"<b>Power:</b> {card['power']}\n\n"
        f"💰 ကျန် Coins: {u['coins']}"
    )
    if card['image'].endswith('.gif'):
        await update.message.reply_animation(animation=card['image'], caption=caption, parse_mode="HTML")
    else:
        await update.message.reply_photo(photo=card['image'], caption=caption, parse_mode="HTML")

# --- CARD SHOP & BUY SYSTEM ---
async def shop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = "<b>🛒 NEXUS CARD SHOP</b>\n\n"
    for c in cards_db:
        text += f"• <b>ID: {c['id']}</b> | [{c['rarity']}] <b>{c['name']}</b> — Price: <b>{c.get('price', 1000)} Coins</b>\n"
    text += "\nဝယ်ယူရန်: <code>/buy &lt;card_id&gt;</code> ဟု ရိုက်ပါ။"
    await update.message.reply_text(text, parse_mode="HTML")

async def buy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = get_user(update.effective_user.id, update.effective_user.first_name)
    try:
        cid = context.args[0]
        card = next((c for c in cards_db if c["id"] == cid), None)
        
        if not card:
            await update.message.reply_text("❌ မရှိသော Card ID ဖြစ်နေပါသည်။")
            return
            
        price = card.get("price", 1000)
        if u["coins"] < price:
            await update.message.reply_text(f"❌ ဒီကဒ်ဝယ်ရန် Coin {price} လိုအပ်ပါသည်။")
            return
            
        u["coins"] -= price
        u["cards"].append({"card": card, "level": 1, "quality": 100})
        save_data()
        
        await update.message.reply_text(f"✅ [{card['rarity']}] <b>{card['name']}</b> ကို Coin {price} ဖြင့် အောင်မြင်စွာ ဝယ်ယူလိုက်ပါပြီ။", parse_mode="HTML")
    except Exception:
        await update.message.reply_text("❌ Usage: <code>/buy <card_id></code>", parse_mode="HTML")

# --- CARD BURN (RECYCLE) ---
async def burn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = get_user(update.effective_user.id, update.effective_user.first_name)
    try:
        idx = int(context.args[0]) - 1
        burned_item = u["cards"].pop(idx)
        refund_coins = int(burned_item["card"]["power"] * 3)
        u["coins"] += refund_coins
        save_data()
        
        await update.message.reply_text(
            f"🔥 <b>{burned_item['card']['name']}</b> အား ဖျက်ဆီးလိုက်ပြီး "
            f"Coins +{refund_coins} ပြန်လည် ရရှိလိုက်ပါပြီ!",
            parse_mode="HTML"
        )
    except Exception:
        await update.message.reply_text("❌ Usage: <code>/burn <card_number_from_collection></code>", parse_mode="HTML")

# --- COLLECTION PAGINATION ---
async def collection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    u = get_user(user_id, update.effective_user.first_name)
    
    if not u["cards"]:
        await update.message.reply_text("❌ သင့်ထံတွင် မည်သည့် Card မှ မရှိသေးပါ။")
        return
        
    await send_collection_page(update, context, user_id, page=0)

async def send_collection_page(update, context, user_id, page=0):
    u = get_user(user_id)
    cards_per_page = 5
    total_cards = len(u["cards"])
    max_page = (total_cards - 1) // cards_per_page
    
    start_idx = page * cards_per_page
    end_idx = start_idx + cards_per_page
    page_cards = u["cards"][start_idx:end_idx]
    
    text = f"🎴 <b>YOUR COLLECTION</b> (Page {page + 1}/{max_page + 1})\n"
    text += f"💰 Balance: {u['coins']} Coins | Total: {total_cards} Cards\n\n"
    
    for i, item in enumerate(page_cards, start_idx + 1):
        c = item["card"]
        quality = item.get("quality", 100)
        level = item.get("level", 1)
        power = c['power'] + (level * 10)
        text += f"<b>{i}. [{c['rarity']}] {c['name']}</b>\n   └ Lvl {level} | Quality: {quality}% | Power: {power}\n"
        
    buttons = []
    if page > 0:
        buttons.append(InlineKeyboardButton("⬅️ Prev", callback_data=f"col_{user_id}_{page - 1}"))
    if page < max_page:
        buttons.append(InlineKeyboardButton("Next ➡️", callback_data=f"col_{user_id}_{page + 1}"))
        
    reply_markup = InlineKeyboardMarkup([buttons]) if buttons else None
    
    if update.callback_query:
        await update.callback_query.edit_message_text(text, parse_mode="HTML", reply_markup=reply_markup)
    else:
        await update.message.reply_text(text, parse_mode="HTML", reply_markup=reply_markup)

async def collection_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    data = query.data.split("_")
    owner_id = data[1]
    target_page = int(data[2])
    
    if str(query.from_user.id) != owner_id:
        await query.answer("❌ ဤ Collection စာမျက်နှာကို မင်း ထိန်းချုပ်၍ မရပါ။", show_alert=True)
        return
        
    await send_collection_page(update, context, owner_id, page=target_page)

# --- LEADERBOARD ---
async def top(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sorted_users = sorted(user_db.items(), key=lambda x: x[1]['coins'], reverse=True)[:10]
    
    text = "<b>🏆 NEXUS TOP 10 WEALTHIEST PLAYERS</b>\n\n"
    for i, (uid, udata) in enumerate(sorted_users, 1):
        text += f"<b>{i}. {udata.get('name', 'Player')}</b> — {udata['coins']} Coins ({len(udata['cards'])} Cards)\n"
        
    await update.message.reply_text(text, parse_mode="HTML")

# --- GRAB & SPAWN ---
async def grab(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    u = get_user(user.id, user.first_name)
    chat_id = update.effective_chat.id

    if chat_id not in active_spawns or active_spawns[chat_id] is None:
        await update.message.reply_text("❌ ယခုအချိန်တွင် ကောက်ယူရန် ကတ်မရှိသေးပါ။")
        return
        
    card = active_spawns[chat_id]
    active_spawns[chat_id] = None
    
    quality = random.randint(75, 100)
    u["cards"].append({"card": card, "level": 1, "quality": quality})
    save_data()
    
    await update.message.reply_text(
        f"🎉 <b>CONGRATULATIONS {user.first_name}!</b>\n\n"
        f"သင်သည် [{card['rarity']}] <b>{card['name']}</b> (Mint: {quality}%) အား ရရှိသွားပါပြီ။",
        parse_mode="HTML"
    )

# --- OWNER COMMANDS ---
async def add_card(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id):
        return
    try:
        raw_text = " ".join(context.args)
        parts = [x.strip() for x in raw_text.split("|")]
        
        image_url = ""
        if update.message.reply_to_message and update.message.reply_to_message.photo:
            photo_file = await update.message.reply_to_message.photo[-1].get_file()
            image_url = photo_file.file_path
            
        if len(parts) == 6:
            card_id, name, anime, rarity, power, image_url = parts
        elif len(parts) == 5 and image_url:
            card_id, name, anime, rarity, power = parts
        else:
            raise ValueError()

        new_c = {"id": card_id, "name": name, "anime": anime, "rarity": rarity, "power": int(power), "price": int(power)*10, "image": image_url}
        cards_db.append(new_c)
        save_data()
        
        await update.message.reply_text(f"✅ Card <b>{name}</b> အား Database ထဲသို့ ထည့်ပြီးပါပြီ။", parse_mode="HTML")
    except Exception:
        await update.message.reply_text("❌ Usage: <code>/addcard ID | Name | Anime | Rarity | Power | Image_URL</code>", parse_mode="HTML")

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id):
        return
    msg = (
        "<b>📊 ADVANCED SYSTEM STATS</b>\n\n"
        f"• <b>Total Players:</b> {len(user_db)}\n"
        f"• <b>Total Cards:</b> {len(cards_db)}\n"
        f"• <b>Current Spawn Threshold:</b> {CURRENT_SPAWN_THRESHOLD} Messages"
    )
    await update.message.reply_text(msg, parse_mode="HTML")

# --- AUTO SPAWN ---
async def handle_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return
        
    chat_id = update.effective_chat.id
    count = chat_message_counts.get(chat_id, 0) + 1
    chat_message_counts[chat_id] = count
    
    if count >= CURRENT_SPAWN_THRESHOLD and cards_db:
        chat_message_counts[chat_id] = 0
        card = random.choice(cards_db)
        active_spawns[chat_id] = card
        
        caption = (
            f"⚡ <b>A WILD CHARACTER APPEARED!</b> ⚡\n\n"
            f"<b>Name:</b> {card['name']}\n"
            f"<b>Rarity:</b> {card['rarity']}\n"
            f"<b>Anime:</b> {card['anime']}\n"
            f"<b>Power:</b> {card['power']}\n\n"
            f"ကတ်ကို ရယူရန် <code>/grab</code> ဟု ရိုက်ပါ။"
        )
        if card['image'].endswith('.gif'):
            await context.bot.send_animation(chat_id=chat_id, animation=card['image'], caption=caption, parse_mode="HTML")
        else:
            await context.bot.send_photo(chat_id=chat_id, photo=card['image'], caption=caption, parse_mode="HTML")

# --- ENGINE LAUNCH ---
if __name__ == "__main__":
    Thread(target=run_web).start()

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # User Handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("profile", profile))
    app.add_handler(CommandHandler("daily", daily))
    app.add_handler(CommandHandler("roll", roll))
    app.add_handler(CommandHandler("shop", shop))
    app.add_handler(CommandHandler("buy", buy))
    app.add_handler(CommandHandler("burn", burn))
    app.add_handler(CommandHandler("collection", collection))
    app.add_handler(CommandHandler("top", top))
    app.add_handler(CommandHandler("grab", grab))
    
    app.add_handler(CallbackQueryHandler(collection_callback, pattern="^col_"))

    # Admin Handlers
    app.add_handler(CommandHandler("addcard", add_card))
    app.add_handler(CommandHandler("stats", stats))

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_messages))

    print("Nexus Complete Full Card Game Engine Online...")
    app.run_polling()
