import logging
import random
import asyncio
from threading import Thread
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from config import BOT_TOKEN, OWNER_IDS, SPAWN_THRESHOLD, PORT

# --- WEB DASHBOARD FOR RENDER & OWNER ANALYTICS ---
app = Flask(__name__)

@app.route('/')
def home():
    return "<h1>⚡ Nexus Catch Engine is Running Live 24/7 on Render!</h1>"

def run_web():
    app.run(host='0.0.0.0', port=PORT)

# --- DATABASE IN-MEMORY STORAGE ---
cards_db = [
    {
        "id": "1", "name": "Gojo Satoru", "anime": "Jujutsu Kaisen", 
        "rarity": "SSR 🌟", "power": 100, 
        "image": "https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExOHp1aWRid2J6eTJrbDZpNmFscXdrZHQ2Zmlxd3Z2MnBwaCZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/lsdd32H2EqjXGRh1m2/giphy.gif",
        "voice": "https://www.soundboard.com/handler/gettrack.ashx?id=184912"
    },
    {
        "id": "2", "name": "Goku Ultra Instinct", "anime": "Dragon Ball Super", 
        "rarity": "Legendary 🔥", "power": 95, 
        "image": "https://media.giphy.com/media/cb9aF9FZvXo4mNu4MK/giphy.gif"
    }
]

user_db = {}           # {user_id: {"coins": 1000, "cards": [], "banned": False, "spam_score": 0}}
active_spawns = {}     # {chat_id: card_obj}
chat_message_counts = {}
market_escrow = []     # List of cards in Escrow Auction Market

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# --- HELPER FUNCTIONS ---
def get_user(user_id):
    if user_id not in user_db:
        user_db[user_id] = {"coins": 500, "cards": [], "banned": False, "spam_score": 0}
    return user_db[user_id]

def is_owner(user_id: int) -> bool:
    return user_id in OWNER_IDS

# --- USER CORE COMMANDS ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "⚡ **NEXUS CATCH — NEXT-GEN GAME ENGINE** ⚡\n\n"
        "🎮 **Commands:**\n"
        "• /collection - မိမိရထားသော Animated Card များ ကြည့်ရန်\n"
        "• /grab - Group ထဲကျလာသော ကတ်ကို ကောက်ယူရန်\n"
        "• /daily - နေ့စဉ် အခမဲ့ Coin 500 ယူရန်\n"
        "• /duel - 3v3 Card Power တိုက်ပွဲဆော့ရန်\n"
        "• /evolve <card_no> - Card အား Evolution Art အဖြစ် အဆင့်မြှင့်ရန်\n"
        "• /market - Escrow Market တွင် ရောင်းရန်/ဝယ်ရန်\n"
    )
    await update.message.reply_text(text, parse_mode="Markdown")

async def daily(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = get_user(update.effective_user.id)
    u["coins"] += 500
    await update.message.reply_text(f"💰 Daily Bonus Coin 500 ရရှိပါသည်။ လက်ရှိ Coin: {u['coins']}")

async def collection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = get_user(update.effective_user.id)
    if not u["cards"]:
        await update.message.reply_text("သင့်ထံတွင် မည်သည့် Card မှ မရှိသေးပါ။")
        return
        
    text = f"🎴 **Your Nexus Collection** (Coins: {u['coins']}):\n\n"
    for i, item in enumerate(u["cards"], 1):
        c = item["card"]
        quality = item.get("quality", 100)
        level = item.get("level", 1)
        power = c['power'] + (level * 10)
        text += f"{i}. [{c['rarity']}] **{c['name']}** (Lvl {level} | Quality: {quality}%) - Power: {power}\n"
    await update.message.reply_text(text, parse_mode="Markdown")

async def grab(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    u = get_user(user.id)
    chat_id = update.effective_chat.id
    
    # AI Anti-Bot Shadow Ban Logic
    if u["banned"]:
        await update.message.reply_text("❌ သင့်အကောင့်သည် Auto-Script/Userbot သုံးစွဲမှုကြောင့် Ban ခံထားရပါသည်။")
        return

    if chat_id not in active_spawns or active_spawns[chat_id] is None:
        await update.message.reply_text("ယခုအချိန်တွင် ကောက်ယူရန် ကတ်မရှိသေးပါ။")
        return
        
    card = active_spawns[chat_id]
    active_spawns[chat_id] = None
    
    quality = random.randint(70, 100) # Dynamic Quality Percentage
    u["cards"].append({"card": card, "level": 1, "quality": quality})
    
    await update.message.reply_text(
        f"🎉 **Congratulations {user.mention_markdown()}!\n\n"
        f"သင်သည် [{card['rarity']}] ** (Quality: {quality}%) ကို အောင်မြင်စွာ ကောက်ယူလိုက်ပါပြီ။",
        parse_mode="Markdown"
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
        await update.message.reply_text(f"✨ **{item['card']['name']}** သည် Level {item['level']} အဖြစ် Evolution အောင်မြင်သွားပါပြီ!")
    except Exception:
        await update.message.reply_text("❌ Usage: `/evolve <card_number>`", parse_mode="Markdown")

async def duel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = get_user(update.effective_user.id)
    if not u["cards"]:
        await update.message.reply_text("တိုက်ခိုက်ရန် သင့်ထံတွင် ကတ်မရှိပါ။")
        return
        
    my_card = max(u["cards"], key=lambda x: x["card"]["power"] + (x["level"]*10))
    bot_card = random.choice(cards_db)
    
    my_power = my_card["card"]["power"] + (my_card["level"] * 10)
    enemy_power = bot_card["power"] + random.randint(1, 30)
    
    msg = f"⚔️ **3v3 NEXUS CARD DUEL** ⚔️\n\n"
    msg += f"👤 Your Fighter: **{my_card['card']['name']}** (Power: {my_power})\n"
    msg += f"👾 Boss Fighter: **{bot_card['name']}** (Power: {enemy_power})\n\n"
    
    if my_power >= enemy_power:
        u["coins"] += 400
        msg += "🏆 **VICTORY!** (+400 Coins)"
    else:
        msg += "💀 **DEFEAT!**"
        
    await update.message.reply_text(msg, parse_mode="Markdown")

# --- AUTO SPAWN SYSTEM ---
async def handle_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return
        
    chat_id = update.effective_chat.id
    count = chat_message_counts.get(chat_id, 0) + 1
    chat_message_counts[chat_id] = count
    
    if count >= SPAWN_THRESHOLD and cards_db:
        chat_message_counts[chat_id] = 0
        card = random.choice(cards_db)
        active_spawns[chat_id] = card
        
        caption = (
            f"⚡ **A WILD CHARACTER APPEARED!** ⚡\n\n"
            f"Name:\n"
            f"Rarity:\n"
            f"Anime:\n\n"
            f"ကတ်ကို ရယူရန် `/grab` ဟု ရိုက်ပါ။"
        )
        if card['image'].endswith('.gif'):
            await context.bot.send_animation(chat_id=chat_id, animation=card['image'], caption=caption, parse_mode="Markdown")
        else:
            await context.bot.send_photo(chat_id=chat_id, photo=card['image'], caption=caption, parse_mode="Markdown")

# --- ADMIN OWNER CONTROL ---
async def add_card(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id):
        return
    try:
        raw_text = " ".join(context.args)
        card_id, name, anime, rarity, power, image = [x.strip() for x in raw_text.split("|")]
        new_card = {"id": card_id, "name": name, "anime": anime, "rarity": rarity, "power": int(power), "image": image}
        cards_db.append(new_card)
        await update.message.reply_text(f"✅ Card **{name}** အား Database ထဲသို့ အောင်မြင်စွာ ထည့်ပြီးပါပြီ။", parse_mode="Markdown")
    except Exception:
        await update.message.reply_text("❌ Syntax: `/addcard ID | Name | Anime | Rarity | Power | Image_URL`", parse_mode="Markdown")

async def ban_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id):
        return
    try:
        target_id = int(context.args[0])
        u = get_user(target_id)
        u["banned"] = True
        await update.message.reply_text(f"✅ User `{target_id}` ကို Shadow Ban ပိတ်လိုက်ပါပြီ။", parse_mode="Markdown")
    except Exception:
        await update.message.reply_text("❌ Usage: `/banuser <user_id>`")

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id):
        return
    msg = " ".join(context.args)
    for cid in chat_message_counts.keys():
        try:
            await context.bot.send_message(chat_id=cid, text=f"📢 **ANNOUNCEMENT:**\n\n{msg}", parse_mode="Markdown")
        except Exception:
            pass
    await update.message.reply_text("✅ Announcement စာ ပို့ပြီးပါပြီ။")

# --- ENGINE LAUNCH ---
if __name__ == "__main__":
    # Start Flask Web Dashboard Thread for Render
    Thread(target=run_web).start()

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("daily", daily))
    app.add_handler(CommandHandler("collection", collection))
    app.add_handler(CommandHandler("grab", grab))
    app.add_handler(CommandHandler("evolve", evolve))
    app.add_handler(CommandHandler("duel", duel))
    
    app.add_handler(CommandHandler("addcard", add_card))
    app.add_handler(CommandHandler("banuser", ban_user))
    app.add_handler(CommandHandler("broadcast", broadcast))
    
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_messages))

    print("Nexus Catch Engine is Running Live...")
    app.run_polling()
