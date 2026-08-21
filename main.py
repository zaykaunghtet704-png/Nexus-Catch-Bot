import sys
import os
import time
import json
import random
import io
import asyncio
from threading import Thread

# Render/Linux Environment Auto-Path Resolver
base_dir = os.path.dirname(os.path.abspath(__file__))
venv_paths = [
    os.path.join(base_dir, ".venv", "lib", f"python3.{sys.version_info.minor}", "site-packages"),
    os.path.join(base_dir, "venv", "lib", f"python3.{sys.version_info.minor}", "site-packages")
]
for p in venv_paths:
    if os.path.exists(p) and p not in sys.path:
        sys.path.insert(0, p)

from flask import Flask
from PIL import Image, ImageDraw
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# ================= CONFIGURATIONS =================
BOT_TOKEN = os.getenv("BOT_TOKEN", "8823072889:AAHKIzIzYVm4CjRJzoJWCktJhI5ZYn4mn4Y")
OWNER_IDS = [7869852655, 7974865879]
LOG_CHANNEL_ID = os.getenv("LOG_CHANNEL_ID", "-1001234567890")

LINK_WAIFU = "https://t.me/example_waifu"
LINK_GROUP = "https://t.me/+00J7JktW8bJlZTY1"
LINK_CHANNEL = "https://t.me/+E6BxfAj0gaI2Y2Zl"

DB_FILE = "bot_database.json"

RARITY_STAGES = {
    1: {"name": "Common", "chance": 35.0, "price": 500, "color": "#808080"},
    2: {"name": "Uncommon", "chance": 20.0, "price": 1000, "color": "#00FF00"},
    3: {"name": "Rare", "chance": 12.0, "price": 2000, "color": "#0000FF"},
    4: {"name": "Super Rare", "chance": 8.0, "price": 3500, "color": "#4B0082"},
    5: {"name": "Ultra Rare", "chance": 6.0, "price": 5000, "color": "#800080"},
    6: {"name": "Epic", "chance": 5.0, "price": 7000, "color": "#FF00FF"},
    7: {"name": "Legendary", "chance": 4.0, "price": 9000, "color": "#FFA500"},
    8: {"name": "Mythic", "chance": 3.0, "price": 11000, "color": "#FF4500"},
    9: {"name": "Celestial", "chance": 2.0, "price": 13000, "color": "#00FFFF"},
    10: {"name": "Supreme", "chance": 1.5, "price": 14000, "color": "#DC143C"},
    11: {"name": "Exalted", "chance": 1.0, "price": 14500, "color": "#FFD700"},
    12: {"name": "Divine", "chance": 0.4, "price": 14800, "color": "#E6E6FA"},
    13: {"name": "Premium Edition", "chance": 0.1, "price": 15000, "color": "#RAINBOW"}
}

LANGUAGES = {
    "MM": {
        "WELCOME": "✨ **{name}** မင်္ဂလာပါ!\nNexus RPG Card Bot မှ ကြိုဆိုပါသည်!",
        "NOT_APPROVED": "⚠️ ဤ Group သည် အသုံးပြုခွင့် မရသေးပါ။ Owner Approve ပြုလုပ်ပေးရန် စောင့်ဆိုင်းပါ။",
        "NOT_ENOUGH_MEMBERS": "⚠️ ဤ Group တွင် လူ ၅၀ အနည်းဆုံး မရှိသေးပါ။ (လက်ရှိ: {count} ယောက်)",
        "NEED_JOIN": "❌ မင်္ဂလာပါ! ဘော့ကို စတင်အသုံးပြုရန် အောက်ပါ Channel နှင့် Group များကို မဖြစ်မနေ Join ပေးပါရန်လိုအပ်ပါသည်။"
    },
    "EN": {
        "WELCOME": "✨ Welcome **{name}** to Nexus RPG Card Bot!",
        "NOT_APPROVED": "⚠️ This group is not approved yet. Please wait for owner approval.",
        "NOT_ENOUGH_MEMBERS": "⚠️ This group requires at least 50 members. (Current: {count})",
        "NEED_JOIN": "❌ Please join our group and channel first to use this bot!"
    }
}

# ================= DATABASE ENGINE =================
class DatabaseManager:
    def __init__(self):
        self.data = {
            "users": {},
            "groups": {},
            "market": {},
            "sudos": [],
            "cards_master": {
                "0021": {"name": "Astraea Celestial Guardian", "rarity": 13, "atk": 950, "def": 880, "hp": 2400},
                "0022": {"name": "Luna Cosmic Librarian", "rarity": 9, "atk": 450, "def": 500, "hp": 1800}
            }
        }
        self.load_db()

    def load_db(self):
        if os.path.exists(DB_FILE):
            try:
                with open(DB_FILE, "r", encoding="utf-8") as f:
                    self.data = json.load(f)
            except Exception:
                pass

    def save_db(self):
        with open(DB_FILE, "w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=4, ensure_ascii=False)

    def get_user(self, uid: int, name: str = "User"):
        uid_str = str(uid)
        if uid_str not in self.data["users"]:
            self.data["users"][uid_str] = {
                "name": name,
                "lang": "MM",
                "coins": 5000,
                "cards": [
                    {"id": "0021", "print": 1, "mint": 100, "level": 1, "frame": "Gold", "dye": "#FF0055", "font": "Gothic"}
                ],
                "favorites": [],
                "hmode": "ALL",
                "last_claim": 0,
                "today_catches": 0
            }
            self.save_db()
        return self.data["users"][uid_str]

    def get_group(self, chat_id: int):
        cid_str = str(chat_id)
        if cid_str not in self.data["groups"]:
            self.data["groups"][cid_str] = {
                "spawn_rate": 85,
                "msg_count": 0,
                "approved": False,
                "spawned_card": None
            }
            self.save_db()
        return self.data["groups"][cid_str]

    def is_admin_or_owner(self, uid: int):
        return (uid in OWNER_IDS) or (str(uid) in self.data["sudos"])

db = DatabaseManager()

# ================= CANVAS ENGINE =================
def generate_custom_card(card_title, rarity_name, print_no, atk, def_val, hp, dye_hex="#FF0055", frame_style="Gold"):
    width, height = 400, 600
    image = Image.new("RGB", (width, height), color=(15, 15, 25))
    draw = ImageDraw.Draw(image)

    frame_color = (255, 215, 0) if frame_style == "Gold" else (0, 255, 255)

    draw.rectangle([10, 10, width - 10, height - 10], outline=frame_color, width=6)
    draw.rectangle([18, 18, width - 18, height - 18], outline=(50, 50, 70), width=2)

    draw.text((25, 25), f"[{rarity_name.upper()}]", fill=frame_color)
    draw.text((width - 120, 25), f"Print #{print_no:04d}", fill=(200, 200, 200))

    draw.rectangle([30, 60, width - 30, 380], outline=(100, 100, 150), fill=(30, 30, 45))
    draw.text((120, 200), "[ CHARACTER VISUAL ]", fill=(150, 150, 180))

    draw.text((30, 400), f"Character: {card_title}", fill=(255, 255, 255))
    draw.text((30, 430), f"Frame: {frame_style} | Dye: {dye_hex}", fill=dye_hex)
    draw.text((30, 460), f"Condition: Mint 100%", fill=(0, 255, 150))
    
    stats_text = f"HP: {hp:,} | ATK: {atk:,} | DEF: {def_val:,}"
    draw.text((30, 500), stats_text, fill=(255, 215, 0))

    bio = io.BytesIO()
    bio.name = 'card.png'
    image.save(bio, 'PNG')
    bio.seek(0)
    return bio

# ================= TELEGRAM BOT HANDLERS =================
async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    u = db.get_user(user.id, user.first_name)
    lang = u.get("lang", "MM")

    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton(" My Waifu", url=LINK_WAIFU)],
        [InlineKeyboardButton("🌐 Group Link", url=LINK_GROUP), InlineKeyboardButton("📢 Update Channel", url=LINK_CHANNEL)]
    ])
    
    msg = LANGUAGES[lang]["WELCOME"].format(name=user.first_name)
    await update.message.reply_photo(
        photo="https://picsum.photos/400/300",
        caption=msg,
        reply_markup=buttons,
        parse_mode="Markdown"
    )

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "📖 **Nexus RPG Bot Help Directory**\n\n"
        "**User Commands:**\n"
        "• `/harem` - မိမိ ပိုင်ဆိုင်သော ကဒ်များ ကြည့်ရန်\n"
        "• `/search` - Database အတွင်းရှိ ကဒ်များ ရှာရန်\n"
        "• `/profile` - Profile နှင့် Stats များ ကြည့်ရန်\n"
        "• `/claim` - ၁၂ နာရီ ၁ ကြိမ် အခမဲ့ ကဒ် ရယူရန်\n"
        "• `/daily` - နေ့စဉ် Coin 500 ယူရန်\n"
        "• `/balance` - လက်ကျန် Coin စစ်ရန်\n"
        "• `/sellprice` - Rarity အလိုက် ဈေးနှုန်းများ ကြည့်ရန်\n"
        "• `/market` / `/sell` / `/buy` - ဈေးကွက် အရောင်းအဝယ် ပြုလုပ်ရန်\n"
        "• `/view <card_id>` - ကဒ်အသေးစိတ် ပုံရိပ်ကြည့်ရန်\n"
        "• `/setlang` - Myanmar/English ဘာသာစကား ပြောင်းရန်"
    )
    await update.message.reply_text(text, parse_mode="Markdown")

async def harem_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    u = db.get_user(user.id, user.first_name)
    
    cards = u["cards"]
    text = f"🎴 **{user.first_name}'s Collection ({len(cards)} Cards):**\n\n"
    for idx, c in enumerate(cards, 1):
        m_card = db.data["cards_master"].get(c["id"], {"name": "Unknown"})
        text += f"{idx}. ID: `{c['id']}` | **{m_card['name']}** | Mint: {c.get('mint', 100)}%\n"

    await update.message.reply_text(text, parse_mode="Markdown")

async def profile_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    u = db.get_user(user.id, user.first_name)
    
    photos = await user.get_profile_photos(limit=1)
    caption = (
        f"👤 **{user.first_name}'s Profile**\n\n"
        f"💰 Coins: `{u['coins']:,}`\n"
        f"🎴 Total Cards: `{len(u['cards'])}`\n"
        f"⭐ Favorites: `{len(u['favorites'])}`\n"
        f"🏆 Global Rank: `#1`"
    )
    if photos.photos:
        await update.message.reply_photo(photo=photos.photos[0][-1].file_id, caption=caption, parse_mode="Markdown")
    else:
        await update.message.reply_text(caption, parse_mode="Markdown")

async def view_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: `/view <card_id>`", parse_mode="Markdown")
        return
    
    cid = context.args[0]
    m_card = db.data["cards_master"].get(cid)
    if not m_card:
        await update.message.reply_text("❌ Card ID မတွေ့ရှိပါ။")
        return

    img_io = generate_custom_card(
        card_title=m_card["name"],
        rarity_name=RARITY_STAGES[m_card["rarity"]]["name"],
        print_no=1,
        atk=m_card["atk"],
        def_val=m_card["def"],
        hp=m_card["hp"],
        dye_hex="#00FFFF",
        frame_style="Gold"
    )
    await update.message.reply_photo(photo=img_io, caption=f"✨ **{m_card['name']}** (ID: `{cid}`)", parse_mode="Markdown")

async def setlang_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = db.get_user(update.effective_user.id)
    u["lang"] = "EN" if u["lang"] == "MM" else "MM"
    db.save_db()
    await update.message.reply_text(f"✅ Language changed to: **{u['lang']}**")

# Group Management & Event Listeners
async def on_bot_added_to_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    added_by = update.effective_user
    members_count = await chat.get_member_count()
    
    log_msg = (
        f"🤖 **Bot Added to New Group!**\n\n"
        f"🌐 **Group:** `{chat.title}` (ID: `{chat.id}`)\n"
        f"👥 **Members:** `{members_count}`\n"
        f"👤 **Added By:** `{added_by.first_name}` (ID: `{added_by.id}`)"
    )
    try:
        await context.bot.send_message(chat_id=LOG_CHANNEL_ID, text=log_msg, parse_mode="Markdown")
    except Exception:
        pass

    db.get_group(chat.id)
    if members_count < 50:
        await chat.send_message(LANGUAGES["MM"]["NOT_ENOUGH_MEMBERS"].format(count=members_count))
        return

    await chat.send_message(
        "👋 **Nexus Bot ကို ထည့်သွင်းပေးသည့်အတွက် ကျေးဇူးတင်ပါသည်။**\n\n"
        "⚠️ **အသုံးပြုရန် လိုအပ်ချက်များ:**\n"
        "1. Bot အား Admin 권한 ပေးထားရပါမည်။\n"
        "2. Owner ထံမှ Group Approve ရယူပေးပါ။"
    )

async def handle_group_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    if not chat or chat.type == "private":
        return

    gp = db.get_group(chat.id)
    if not gp["approved"]:
        return

    gp["msg_count"] += 1
    if gp["msg_count"] >= gp["spawn_rate"]:
        gp["msg_count"] = 0
        card_ids = list(db.data["cards_master"].keys())
        spawned = random.choice(card_ids)
        gp["spawned_card"] = spawned
        db.save_db()
        
        card_data = db.data["cards_master"][spawned]
        await chat.send_message(
            f"🎴 **A New Card Has Spawned!**\n\n"
            f"Name: **{card_data['name']}**\n"
            f"ကဒ် ကောက်ယူရန် `/Nexus {card_data['name']}` ဟု ရိုက်ထည့်ပါ!"
        )

# Admin Commands
async def approvegroup_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not db.is_admin_or_owner(update.effective_user.id):
        return
    try:
        gid = int(context.args[0])
        gp = db.get_group(gid)
        gp["approved"] = True
        db.save_db()
        await update.message.reply_text(f"✅ Group `{gid}` ကို သုံးစွဲခွင့် Approve ပေးလိုက်ပါပြီ။")
    except Exception:
        await update.message.reply_text("Usage: `/approvegroup <group_id>`")

async def addcard_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not db.is_admin_or_owner(update.effective_user.id):
        return
    try:
        cid = context.args[0]
        rarity = int(context.args[1])
        name = " ".join(context.args[2:])
        
        db.data["cards_master"][cid] = {
            "name": name,
            "rarity": rarity,
            "atk": rarity * 100,
            "def": rarity * 80,
            "hp": rarity * 200
        }
        db.save_db()
        await update.message.reply_text(f"✅ Card `{cid}` - **{name}** အား Database ထဲ ထည့်သွင်းပြီးပါပြီ။")
    except Exception:
        await update.message.reply_text("Usage: `/addcard <id> <rarity_1_to_13> <card_name>`")

# ================= FLASK SERVER FOR RENDER HEALTH CHECK =================
web_app = Flask(__name__)

@web_app.route('/')
def home():
    return "Nexus RPG Card Bot Engine Running!"

def run_flask():
    port = int(os.getenv("PORT", 8080))
    web_app.run(host="0.0.0.0", port=port)

# ================= MAIN RUNNER =================
async def run_bot():
    app = Application.builder().token(BOT_TOKEN).build()

    # Command Handlers
    app.add_handler(CommandHandler(["start", "sratr"], start_cmd))
    app.add_handler(CommandHandler(["help", "Help"], help_cmd))
    app.add_handler(CommandHandler(["harem", "Hearm"], harem_cmd))
    app.add_handler(CommandHandler("profile", profile_cmd))
    app.add_handler(CommandHandler("view", view_cmd))
    app.add_handler(CommandHandler("setlang", setlang_cmd))

    # Admin Commands
    app.add_handler(CommandHandler("approvegroup", approvegroup_cmd))
    app.add_handler(CommandHandler("addcard", addcard_cmd))

    # Group Status & Message Handlers
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, on_bot_added_to_group))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_group_messages))

    print("🚀 Nexus Card Bot Started Successfully!")
    
    async with app:
        await app.start()
        await app.updater.start_polling()
        await asyncio.Event().wait()

def main():
    # Start Web Server in Background
    Thread(target=run_flask, daemon=True).start()

    # Run Async Bot Loop
    asyncio.run(run_bot())

if __name__ == "__main__":
    main()
