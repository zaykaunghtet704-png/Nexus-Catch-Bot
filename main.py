import logging
import random
from threading import Thread
from flask import Flask
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, 
    filters, ContextTypes
)
from config import BOT_TOKEN, OWNER_IDS, SPAWN_THRESHOLD, PORT

# --- WEB DASHBOARD FOR RENDER KEEP-ALIVE ---
app = Flask(__name__)

@app.route('/')
def home():
    return "<h1>Nexus Catch Advanced Control Engine Online!</h1>"

def run_web():
    app.run(host='0.0.0.0', port=PORT)

# --- SYSTEM DATABASES ---
cards_db = [
    {
        "id": "1", "name": "Gojo Satoru", "anime": "Jujutsu Kaisen", 
        "rarity": "SSR 🌟", "power": 100, 
        "image": "https://media.giphy.com/media/lsdd32H2EqjXGRh1m2/giphy.gif"
    }
]

user_db = {}           # {user_id: {"coins": 500, "cards": [], "banned": False, "level": 1}}
active_spawns = {}     # {chat_id: card_obj}
chat_message_counts = {}
CURRENT_SPAWN_THRESHOLD = SPAWN_THRESHOLD

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# --- UTILS & HELPERS ---
def get_user(user_id):
    if user_id not in user_db:
        user_db[user_id] = {"coins": 500, "cards": [], "banned": False, "level": 1}
    return user_db[user_id]

def is_owner(user_id: int) -> bool:
    return user_id in OWNER_IDS

# --- USER COMMANDS ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "<b>⚡ NEXUS CATCH — ADVANCED CONTROL ENGINE ⚡</b>\n\n"
        "<b>🎮 Player Commands:</b>\n"
        "• /profile - မိမိ၏ Profile & Coins စာရင်းကြည့်ရန်\n"
        "• /collection - မိမိ ရရှိထားသော Cards များကြည့်ရန်\n"
        "• /grab - Group ထဲ ကျလာသော ကတ်ကို ကောက်ယူရန်\n"
        "• /daily - နေ့စဉ် အခမဲ့ Coin 500 ရယူရန်\n"
        "• /transfer &lt;user_id&gt; &lt;amount&gt; - Coin လွှဲရန်\n"
        "• /duel - Card Battle တိုက်ခိုက်ရန်\n"
        "• /evolve &lt;card_no&gt; - Card Level မြှင့်ရန်\n\n"
        "<b>👑 Owner Controls:</b>\n"
        "• /addcard | /delcard | /givecoins\n"
        "• /setspawn | /banuser | /unbanuser\n"
        "• /stats | /broadcast"
    )
    await update.message.reply_text(text, parse_mode="HTML")

async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    u = get_user(user.id)
    text = (
        f"👤 <b>PLAYER PROFILE: {user.first_name}</b>\n\n"
        f"🆔 <b>User ID:</b> <code>{user.id}</code>\n"
        f"💰 <b>Coins Balance:</b> {u['coins']} Coins\n"
        f"🎴 <b>Total Cards Owned:</b> {len(u['cards'])}\n"
        f"🚫 <b>Status:</b> {'Banned ❌' if u['banned'] else 'Active ✅'}"
    )
    await update.message.reply_text(text, parse_mode="HTML")

async def daily(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = get_user(update.effective_user.id)
    u["coins"] += 500
    await update.message.reply_text(f"💰 <b>Daily Reward Received!</b>\nCoin 500 ရရှိပါသည်။ (လက်ရှိ Balance: {u['coins']})", parse_mode="HTML")

async def collection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = get_user(update.effective_user.id)
    if not u["cards"]:
        await update.message.reply_text("❌ သင့်ထံတွင် မည်သည့် Card မှ မရှိသေးပါ။")
        return
        
    text = f"🎴 <b>Your Collection</b> (Total: {len(u['cards'])} Cards):\n\n"
    for i, item in enumerate(u["cards"], 1):
        c = item["card"]
        quality = item.get("quality", 100)
        level = item.get("level", 1)
        power = c['power'] + (level * 10)
        text += f"{i}. [{c['rarity']}] <b>{c['name']}</b> (Lvl {level} | Quality: {quality}%) - Power: {power}\n"
    
    await update.message.reply_text(text, parse_mode="HTML")

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
        f"🎉 <b>Congratulations {user.first_name}!</b>\n\n"
        f"သင်သည် [{card['rarity']}] <b>{card['name']}</b> (Quality: {quality}%) အား ရရှိသွားပါပြီ။",
        parse_mode="HTML"
    )

async def transfer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = get_user(update.effective_user.id)
    try:
        target_id = int(context.args[0])
        amount = int(context.args[1])
        
        if amount <= 0 or u["coins"] < amount:
            await update.message.reply_text("❌ Coin ပမာဏ မလုံလောက်ပါ သို့မဟုတ် ပမာဏ မှားယွင်းနေပါသည်။")
            return
            
        target_u = get_user(target_id)
        u["coins"] -= amount
        target_u["coins"] += amount
        
        await update.message.reply_text(f"✅ User <code>{target_id}</code> ဆီသို့ Coins {amount} လွှဲပြောင်းပြီးပါပြီ။", parse_mode="HTML")
    except Exception:
        await update.message.reply_text("❌ Syntax: <code>/transfer <user_id> <amount></code>", parse_mode="HTML")

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
        
        await update.message.reply_text(f"✨ <b>{item['card']['name']}</b> သည် Level {item['level']} ဖြစ်သွားပါပြီ!", parse_mode="HTML")
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
    
    msg = "⚔️ <b>NEXUS CARD DUEL ARENA</b> ⚔️\n\n"
    msg += f"👤 Your Card: <b>{my_item['card']['name']}</b> (Power: {my_power})\n"
    msg += f"👾 Boss: <b>{bot_card['name']}</b> (Power: {enemy_power})\n\n"
    
    if my_power >= enemy_power:
        u["coins"] += 450
        msg += "🏆 <b>VICTORY!</b> (+450 Coins)"
    else:
        msg += "💀 <b>DEFEAT!</b>"
        
    await update.message.reply_text(msg, parse_mode="HTML")

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

        cards_db.append({"id": card_id, "name": name, "anime": anime, "rarity": rarity, "power": int(power), "image": image_url})
        await update.message.reply_text(f"✅ Card <b>{name}</b> အား ထည့်သွင်းပြီးပါပြီ။", parse_mode="HTML")
    except Exception:
        await update.message.reply_text(
            "❌ <b>အသုံးပြုပုံ:</b>\n"
            "• <code>/addcard ID | Name | Anime | Rarity | Power | URL</code>\n"
            "• ပုံကို Reply ပြန်ပြီး: <code>/addcard ID | Name | Anime | Rarity | Power</code>",
            parse_mode="HTML"
        )

async def del_card(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id):
        return
    try:
        cid = context.args[0]
        global cards_db
        cards_db = [c for c in cards_db if c["id"] != cid]
        await update.message.reply_text(f"✅ Card ID <code>{cid}</code> အား ဖျက်ပြီးပါပြီ။", parse_mode="HTML")
    except Exception:
        await update.message.reply_text("❌ Usage: <code>/delcard <card_id></code>", parse_mode="HTML")

async def give_coins(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id):
        return
    try:
        tid = int(context.args[0])
        amt = int(context.args[1])
        u = get_user(tid)
        u["coins"] += amt
        await update.message.reply_text(f"✅ User <code>{tid}</code> သို့ Coin {amt} ထည့်ပေးလိုက်ပါပြီ။", parse_mode="HTML")
    except Exception:
        await update.message.reply_text("❌ Usage: <code>/givecoins <user_id> <amount></code>", parse_mode="HTML")

async def set_spawn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id):
        return
    try:
        global CURRENT_SPAWN_THRESHOLD
        CURRENT_SPAWN_THRESHOLD = int(context.args[0])
        await update.message.reply_text(f"✅ Spawn Threshold ကို စာ <b>{CURRENT_SPAWN_THRESHOLD}</b> စောင်လျှင် ၁ ကတ်သို့ ပြောင်းလိုက်ပါပြီ။", parse_mode="HTML")
    except Exception:
        await update.message.reply_text("❌ Usage: <code>/setspawn <count></code>", parse_mode="HTML")

async def ban_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id):
        return
    try:
        tid = int(context.args[0])
        get_user(tid)["banned"] = True
        await update.message.reply_text(f"✅ User <code>{tid}</code> ကို Ban လိုက်ပါပြီ။", parse_mode="HTML")
    except Exception:
        await update.message.reply_text("❌ Usage: <code>/banuser <user_id></code>", parse_mode="HTML")

async def unban_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id):
        return
    try:
        tid = int(context.args[0])
        get_user(tid)["banned"] = False
        await update.message.reply_text(f"✅ User <code>{tid}</code> ကို Unban ပေးလိုက်ပါပြီ။", parse_mode="HTML")
    except Exception:
        await update.message.reply_text("❌ Usage: <code>/unbanuser <user_id></code>", parse_mode="HTML")

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id):
        return
    msg = (
        "<b>📊 BOT SYSTEM ANALYTICS</b>\n\n"
        f"• <b>Total Registered Players:</b> {len(user_db)}\n"
        f"• <b>Active Groups:</b> {len(chat_message_counts)}\n"
        f"• <b>Total Cards in Database:</b> {len(cards_db)}\n"
        f"• <b>Current Spawn Threshold:</b> {CURRENT_SPAWN_THRESHOLD} Msgs"
    )
    await update.message.reply_text(msg, parse_mode="HTML")

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id):
        return
    msg = " ".join(context.args)
    if not msg:
        await update.message.reply_text("❌ Send announcement text.")
        return
        
    success = 0
    for cid in chat_message_counts.keys():
        try:
            await context.bot.send_message(chat_id=cid, text=f"📢 <b>ANNOUNCEMENT:</b>\n\n{msg}", parse_mode="HTML")
            success += 1
        except Exception:
            pass
    await update.message.reply_text(f"✅ Broadcast sent to {success} groups.", parse_mode="HTML")

# --- MESSAGE HANDLER & AUTO SPAWN ---
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

    # Players
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("profile", profile))
    app.add_handler(CommandHandler("daily", daily))
    app.add_handler(CommandHandler("collection", collection))
    app.add_handler(CommandHandler("grab", grab))
    app.add_handler(CommandHandler("transfer", transfer))
    app.add_handler(CommandHandler("evolve", evolve))
    app.add_handler(CommandHandler("duel", duel))
    
    # Owners
    app.add_handler(CommandHandler("addcard", add_card))
    app.add_handler(CommandHandler("delcard", del_card))
    app.add_handler(CommandHandler("givecoins", give_coins))
    app.add_handler(CommandHandler("setspawn", set_spawn))
    app.add_handler(CommandHandler("banuser", ban_user))
    app.add_handler(CommandHandler("unbanuser", unban_user))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("broadcast", broadcast))
    
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_messages))

    print("Nexus Catch Full Control Engine Online...")
    app.run_polling()
