import logging
import random
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
    return "<h1>Nexus Ultimate Catch Engine Online 24/7!</h1>"

def run_web():
    app.run(host='0.0.0.0', port=PORT)

# --- ADVANCED CARD DATABASE (WITH RARITY WEIGHTS) ---
cards_db = [
    {
        "id": "1", "name": "Gojo Satoru", "anime": "Jujutsu Kaisen", 
        "rarity": "SSR 🌟", "power": 100, "weight": 5, 
        "image": "https://media.giphy.com/media/lsdd32H2EqjXGRh1m2/giphy.gif"
    },
    {
        "id": "2", "name": "Goku Ultra Instinct", "anime": "Dragon Ball Super", 
        "rarity": "Legendary 🔥", "power": 95, "weight": 10, 
        "image": "https://media.giphy.com/media/cb9aF9FZvXo4mNu4MK/giphy.gif"
    },
    {
        "id": "3", "name": "Naruto Uzumaki", "anime": "Naruto", 
        "rarity": "Rare ✨", "power": 80, "weight": 35, 
        "image": "https://media.giphy.com/media/2y9n1aB5r9pYI/giphy.gif"
    },
    {
        "id": "4", "name": "Kamisato Ayaka", "anime": "Genshin Impact", 
        "rarity": "Rare ✨", "power": 85, "weight": 30, 
        "image": "https://i.imgur.com/example.jpg"
    }
]

# State Storage
user_db = {}           
active_spawns = {}     
chat_message_counts = {}
CURRENT_SPAWN_THRESHOLD = SPAWN_THRESHOLD

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# --- UTILS ---
def get_user(user_id):
    if user_id not in user_db:
        user_db[user_id] = {"coins": 1000, "cards": [], "banned": False}
    return user_db[user_id]

def is_owner(user_id: int) -> bool:
    return user_id in OWNER_IDS

def get_random_card():
    weights = [c.get("weight", 20) for c in cards_db]
    return random.choices(cards_db, weights=weights, k=1)[0]

# --- PLAYER COMMANDS ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "<b>⚡ NEXUS ULTIMATE CATCH ENGINE ⚡</b>\n\n"
        "<b>🎮 Interactive Game Features:</b>\n"
        "• /collection - Inline Pagination ဖြင့် ကတ်များ ကြည့်ရန်\n"
        "• /grab - Group ထဲ ကျလာသော Card ကို ရယူရန်\n"
        "• /daily - နေ့စဉ် Daily Reward Coins ယူရန်\n"
        "• /profile - မိမိ၏ Stats & Coins ကြည့်ရန်\n"
        "• /duel - Card Power PVP Battle ဆော့ရန်\n"
        "• /evolve &lt;card_no&gt; - Card Level မြှင့်ရန်\n"
        "• /transfer &lt;user_id&gt; &lt;amount&gt; - Coin ပို့ရန်\n\n"
        "<b>👑 Admin Controls:</b>\n"
        "• /addcard | /delcard | /givecoins | /setspawn | /stats | /broadcast"
    )
    await update.message.reply_text(text, parse_mode="HTML")

async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    u = get_user(user.id)
    text = (
        f"👤 <b>PLAYER PROFILE: {user.first_name}</b>\n\n"
        f"🆔 <b>ID:</b> <code>{user.id}</code>\n"
        f"💰 <b>Coins:</b> {u['coins']} Coins\n"
        f"🎴 <b>Total Cards:</b> {len(u['cards'])}\n"
        f"🛡️ <b>Account Status:</b> {'Banned ❌' if u['banned'] else 'Active ✅'}"
    )
    await update.message.reply_text(text, parse_mode="HTML")

async def daily(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = get_user(update.effective_user.id)
    u["coins"] += 500
    await update.message.reply_text(f"💰 <b>Daily Bonus Claimed!</b> +500 Coins ရရှိပါသည်။ (စုစုပေါင်း: {u['coins']})", parse_mode="HTML")

# --- INTERACTIVE BUTTON COLLECTION (PAGINATION) ---
async def collection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    u = get_user(user_id)
    
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
    text += f"💰 Balance: {u['coins']} Coins\n\n"
    
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
    owner_id = int(data[1])
    target_page = int(data[2])
    
    if query.from_user.id != owner_id:
        await query.answer("❌ ဤ Collection စာမျက်နှာကို မင်း ထိန်းချုပ်၍ မရပါ။", show_alert=True)
        return
        
    await send_collection_page(update, context, owner_id, page=target_page)

async def grab(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    u = get_user(user.id)
    chat_id = update.effective_chat.id
    
    if u.get("banned", False):
        await update.message.reply_text("❌ သင့်အကောင့် Shadow Ban ခံထားရပါသဖြင့် ကတ်ယူ၍မရပါ။")
        return

    if chat_id not in active_spawns or active_spawns[chat_id] is None:
        await update.message.reply_text("❌ ယခုအချိန်တွင် ကောက်ယူရန် ကတ်မရှိသေးပါ။")
        return
        
    card = active_spawns[chat_id]
    active_spawns[chat_id] = None
    
    quality = random.randint(75, 100)
    u["cards"].append({"card": card, "level": 1, "quality": quality})
    
    await update.message.reply_text(
        f"🎉 <b>CONGRATULATIONS {user.first_name}!</b>\n\n"
        f"သင်သည် [{card['rarity']}] <b>{card['name']}</b> (Mint Quality: {quality}%) အား အောင်မြင်စွာ ကောက်ယူလိုက်ပါပြီ။",
        parse_mode="HTML"
    )

async def evolve(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = get_user(update.effective_user.id)
    try:
        idx = int(context.args[0]) - 1
        item = u["cards"][idx]
        cost = item["level"] * 300
        
        if u["coins"] < cost:
            await update.message.reply_text(f"❌ Level တင်ရန် Coin {cost} လိုအပ်ပါသည်။")
            return
            
        u["coins"] -= cost
        item["level"] += 1
        item["quality"] = min(100, item["quality"] + 5)
        
        await update.message.reply_text(f"✨ <b>{item['card']['name']}</b> သည် Level {item['level']} သို့ မြင့်တက်သွားပါပြီ!", parse_mode="HTML")
    except Exception:
        await update.message.reply_text("❌ Usage: <code>/evolve 1</code>", parse_mode="HTML")

async def duel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = get_user(update.effective_user.id)
    if not u["cards"]:
        await update.message.reply_text("❌ တိုက်ခိုက်ရန် သင့်ထံတွင် ကတ်မရှိပါ။")
        return
        
    my_item = max(u["cards"], key=lambda x: x["card"]["power"] + (x["level"] * 10))
    bot_card = random.choice(cards_db)
    
    my_power = my_item["card"]["power"] + (my_item["level"] * 10)
    enemy_power = bot_card["power"] + random.randint(1, 35)
    
    msg = "⚔️ <b>NEXUS ARENA DUEL</b> ⚔️\n\n"
    msg += f"👤 Your Fighter: <b>{my_item['card']['name']}</b> (Power: {my_power})\n"
    msg += f"👾 Boss: <b>{bot_card['name']}</b> (Power: {enemy_power})\n\n"
    
    if my_power >= enemy_power:
        u["coins"] += 500
        msg += "🏆 <b>VICTORY!</b> (+500 Coins)"
    else:
        msg += "💀 <b>DEFEAT!</b>"
        
    await update.message.reply_text(msg, parse_mode="HTML")

async def transfer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = get_user(update.effective_user.id)
    try:
        target_id = int(context.args[0])
        amount = int(context.args[1])
        
        if amount <= 0 or u["coins"] < amount:
            await update.message.reply_text("❌ Coins ပမာဏ မလုံလောက်ပါ။")
            return
            
        target_u = get_user(target_id)
        u["coins"] -= amount
        target_u["coins"] += amount
        
        await update.message.reply_text(f"✅ User <code>{target_id}</code> သို့ Coin {amount} လွှဲပြောင်းပြီးပါပြီ။", parse_mode="HTML")
    except Exception:
        await update.message.reply_text("❌ Usage: <code>/transfer <user_id> <amount></code>", parse_mode="HTML")

# --- OWNER CONTROLS ---
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

        cards_db.append({
            "id": card_id, "name": name, "anime": anime, 
            "rarity": rarity, "power": int(power), "weight": 20, "image": image_url
        })
        await update.message.reply_text(f"✅ Card <b>{name}</b> အား ထည့်သွင်းပြီးပါပြီ။", parse_mode="HTML")
    except Exception:
        await update.message.reply_text(
            "❌ <b>အသုံးပြုပုံ:</b>\n"
            "• <code>/addcard ID | Name | Anime | Rarity | Power | URL</code>\n"
            "• ပုံကို Reply ပြန်ပြီး: <code>/addcard ID | Name | Anime | Rarity | Power</code>",
            parse_mode="HTML"
        )

async def set_spawn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id):
        return
    try:
        global CURRENT_SPAWN_THRESHOLD
        CURRENT_SPAWN_THRESHOLD = int(context.args[0])
        await update.message.reply_text(f"✅ Spawn Rate ကို စာ <b>{CURRENT_SPAWN_THRESHOLD}</b> စောင်လျှင် ၁ ကတ်သို့ ပြောင်းလိုက်ပါပြီ။", parse_mode="HTML")
    except Exception:
        await update.message.reply_text("❌ Usage: <code>/setspawn <count></code>", parse_mode="HTML")

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id):
        return
    msg = (
        "<b>📊 ADVANCED BOT SYSTEM STATS</b>\n\n"
        f"• <b>Total Players:</b> {len(user_db)}\n"
        f"• <b>Active Groups:</b> {len(chat_message_counts)}\n"
        f"• <b>Total Cards:</b> {len(cards_db)}\n"
        f"• <b>Spawn Threshold:</b> {CURRENT_SPAWN_THRESHOLD} Messages"
    )
    await update.message.reply_text(msg, parse_mode="HTML")

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id):
        return
    msg = " ".join(context.args)
    if not msg:
        await update.message.reply_text("❌ Broadcast စာသား ထည့်ပါ။")
        return
        
    success = 0
    for cid in chat_message_counts.keys():
        try:
            await context.bot.send_message(chat_id=cid, text=f"📢 <b>GLOBAL ANNOUNCEMENT:</b>\n\n{msg}", parse_mode="HTML")
            success += 1
        except Exception:
            pass
    await update.message.reply_text(f"✅ Group ပေါင်း ({success}) ခုသို့ Broadcast စာ ပို့ပြီးပါပြီ။", parse_mode="HTML")

# --- AUTO SPAWN SYSTEM (PROBABILITY BASED) ---
async def handle_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return
        
    chat_id = update.effective_chat.id
    count = chat_message_counts.get(chat_id, 0) + 1
    chat_message_counts[chat_id] = count
    
    if count >= CURRENT_SPAWN_THRESHOLD and cards_db:
        chat_message_counts[chat_id] = 0
        card = get_random_card()
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
    app.add_handler(CommandHandler("collection", collection))
    app.add_handler(CommandHandler("grab", grab))
    app.add_handler(CommandHandler("evolve", evolve))
    app.add_handler(CommandHandler("duel", duel))
    app.add_handler(CommandHandler("transfer", transfer))
    
    # Callback Query for Pagination
    app.add_handler(CallbackQueryHandler(collection_callback, pattern="^col_"))

    # Owner Handlers
    app.add_handler(CommandHandler("addcard", add_card))
    app.add_handler(CommandHandler("setspawn", set_spawn))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("broadcast", broadcast))

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_messages))

    print("Nexus Ultimate Catch Engine Online...")
    app.run_polling()
