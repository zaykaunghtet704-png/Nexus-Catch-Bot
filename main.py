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
    1: {"name": "Common", "price": 500},
    2: {"name": "Uncommon", "price": 1000},
    3: {"name": "Rare", "price": 2000},
    4: {"name": "Super Rare", "price": 3500},
    5: {"name": "Ultra Rare", "price": 5000},
    6: {"name": "Epic", "price": 7000},
    7: {"name": "Legendary", "price": 9000},
    8: {"name": "Mythic", "price": 11000},
    9: {"name": "Celestial", "price": 13000},
    10: {"name": "Supreme", "price": 14000},
    11: {"name": "Exalted", "price": 14500},
    12: {"name": "Divine", "price": 14800},
    13: {"name": "Premium Edition", "price": 15000}
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
                    {"id": "0021", "print": 1, "mint": 100, "level": 1, "frame": "Gold", "dye": "#FF0055"}
                ],
                "favorites": [],
                "last_claim": 0,
                "last_daily": 0
            }
            self.save_db()
        return self.data["users"][uid_str]

    def get_group(self, chat_id: int):
        cid_str = str(chat_id)
        if cid_str not in self.data["groups"]:
            self.data["groups"][cid_str] = {
                "spawn_rate": 20,
                "msg_count": 0,
                "approved": True,
                "spawned_card": None
            }
            self.save_db()
        return self.data["groups"][cid_str]

    def is_admin_or_owner(self, uid: int):
        return (uid in OWNER_IDS) or (str(uid) in self.data["sudos"])

db = DatabaseManager()

# ================= TELEGRAM BOT HANDLERS =================
async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    db.get_user(user.id, user.first_name)
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton(" My Waifu", url=LINK_WAIFU)],
        [InlineKeyboardButton("🌐 Group Link", url=LINK_GROUP), InlineKeyboardButton("📢 Channel", url=LINK_CHANNEL)]
    ])
    await update.message.reply_text(f"✨ **{user.first_name}** မင်္ဂလာပါ!\nNexus RPG Card Bot မှ ကြိုဆိုပါသည်!", reply_markup=buttons, parse_mode="Markdown")

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "📖 **Nexus RPG Bot Help Directory**\n\n"
        "• `/harem` - မိမိ ကဒ်များ ကြည့်ရန်\n"
        "• `/claim` - ၁၂ နာရီ ၁ ကြိမ် အခမဲ့ ကဒ် ရယူရန်\n"
        "• `/daily` - နေ့စဉ် Coin 500 ယူရန်\n"
        "• `/balance` - လက်ကျန် Coin စစ်ရန်\n"
        "• `/search <name>` - ကဒ်များ ရှာရန်\n"
        "• `/sellprice` - Rarity ဈေးနှုန်းများ\n"
        "• `/market` / `/sell` / `/buy` - ဈေးကွက် အရောင်းအဝယ်\n"
        "• `/view <card_id>` - ကဒ် ပုံရိပ် ကြည့်ရန်"
    )
    await update.message.reply_text(text, parse_mode="Markdown")

async def harem_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    u = db.get_user(user.id, user.first_name)
    cards = u["cards"]
    text = f"🎴 **{user.first_name}'s Collection ({len(cards)} Cards):**\n\n"
    for idx, c in enumerate(cards, 1):
        m_card = db.data["cards_master"].get(c["id"], {"name": "Unknown"})
        text += f"{idx}. ID: `{c['id']}` | **{m_card['name']}**\n"
    await update.message.reply_text(text, parse_mode="Markdown")

async def balance_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = db.get_user(update.effective_user.id, update.effective_user.first_name)
    await update.message.reply_text(f"💰 **{update.effective_user.first_name}** ၏ လက်ကျန်ငွေ: `{u['coins']:,}` Coins", parse_mode="Markdown")

async def daily_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = db.get_user(update.effective_user.id, update.effective_user.first_name)
    now = time.time()
    if now - u.get("last_daily", 0) < 86400:
        await update.message.reply_text("⏱️ နေ့စဉ် ဆုကြေးကို ၂၄ နာရီမှ ၁ ကြိမ်သာ ယူနိုင်ပါသည်။")
        return
    u["coins"] += 500
    u["last_daily"] = now
    db.save_db()
    await update.message.reply_text("🎉 Daily Bonus 💰 500 Coins ရရှိပါသည်!")

async def claim_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = db.get_user(update.effective_user.id, update.effective_user.first_name)
    now = time.time()
    if now - u.get("last_claim", 0) < 43200:
        await update.message.reply_text("⏱️ Claim ကို ၁၂ နာရီလျှင် ၁ ကြိမ်သာ ပြုလုပ်နိုင်ပါသည်။")
        return
    card_ids = list(db.data["cards_master"].keys())
    if not card_ids:
        await update.message.reply_text("❌ Database တွင် ကဒ်များ မရှိသေးပါ။")
        return
    got_id = random.choice(card_ids)
    u["cards"].append({"id": got_id, "print": 1, "mint": 100})
    u["last_claim"] = now
    db.save_db()
    card_info = db.data["cards_master"][got_id]
    await update.message.reply_text(f"🎁 **Claim အောင်မြင်ပါသည်။**\n\nသင်ရရှိသော ကဒ်: **{card_info['name']}** (ID: `{got_id}`)", parse_mode="Markdown")

async def search_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: `/search <card_name>`", parse_mode="Markdown")
        return
    query = " ".join(context.args).lower()
    results = []
    for cid, info in db.data["cards_master"].items():
        if query in info["name"].lower():
            results.append(f"• ID: `{cid}` | **{info['name']}**")
    if results:
        await update.message.reply_text("🔍 **ရှာဖွေတွေ့ရှိသော ကဒ်များ:**\n\n" + "\n".join(results), parse_mode="Markdown")
    else:
        await update.message.reply_text("❌ မည်သည့် ကဒ်မျှ ရှာမတွေ့ပါ။")

async def sellprice_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = "📊 **Rarity အလိုက် ရောင်းဈေး သတ်မှတ်ချက်များ:**\n\n"
    for r, info in RARITY_STAGES.items():
        text += f"• Level {r} ({info['name']}): `{info['price']:,}` Coins\n"
    await update.message.reply_text(text, parse_mode="Markdown")

async def market_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    m = db.data["market"]
    if not m:
        await update.message.reply_text("🛒 **Market တွင် ရောင်းရန် တင်ထားသော ကဒ် မရှိသေးပါ။**")
        return
    text = "🛒 **Market List:**\n\n"
    for listing_id, item in m.items():
        cinfo = db.data["cards_master"].get(item["card_id"], {"name": "Unknown"})
        text += f"• ID: `{listing_id}` | **{cinfo['name']}** | Price: `{item['price']:,}` Coins\n"
    await update.message.reply_text(text, parse_mode="Markdown")

async def sell_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2:
        await update.message.reply_text("Usage: `/sell <card_id> <price>`", parse_mode="Markdown")
        return
    cid, price = context.args[0], int(context.args[1])
    u = db.get_user(update.effective_user.id)
    user_card = next((c for c in u["cards"] if c["id"] == cid), None)
    if not user_card:
        await update.message.reply_text("❌ ထို ကဒ် သင့်ထံတွင် မရှိပါ။")
        return
    u["cards"].remove(user_card)
    listing_id = str(random.randint(1000, 9999))
    db.data["market"][listing_id] = {"seller_id": update.effective_user.id, "card_id": cid, "price": price}
    db.save_db()
    await update.message.reply_text(f"✅ Card `{cid}` အား Market တွင် Listing ID `{listing_id}` ဖြင့် ရောင်းရန် တင်လိုက်ပါပြီ။", parse_mode="Markdown")

async def buy_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: `/buy <listing_id>`", parse_mode="Markdown")
        return
    lid = context.args[0]
    item = db.data["market"].get(lid)
    if not item:
        await update.message.reply_text("❌ Listing ID မှားယွင်းနေပါသည်။")
        return
    u = db.get_user(update.effective_user.id)
    if u["coins"] < item["price"]:
        await update.message.reply_text("❌ လက်ကျန် Coin မလုံလောက်ပါ။")
        return
    u["coins"] -= item["price"]
    u["cards"].append({"id": item["card_id"], "print": 1, "mint": 100})
    
    seller = db.get_user(item["seller_id"])
    seller["coins"] += item["price"]
    del db.data["market"][lid]
    db.save_db()
    await update.message.reply_text(f"🎉 Listing `{lid}` မှ ကဒ်ကို အောင်မြင်စွာ ဝယ်ယူလိုက်ပါပြီ!", parse_mode="Markdown")

async def approvegroup_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not db.is_admin_or_owner(update.effective_user.id):
        return
    try:
        gid = int(context.args[0])
        gp = db.get_group(gid)
        gp["approved"] = True
        db.save_db()
        await update.message.reply_text(f"✅ Group `{gid}` ကို သုံးစွဲခွင့် Approve ပေးလိုက်ပါပြီ။", parse_mode="Markdown")
    except Exception:
        await update.message.reply_text("Usage: `/approvegroup <group_id>`")

# ================= FLASK SERVER =================
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

    # User Commands
    app.add_handler(CommandHandler(["start", "sratr"], start_cmd))
    app.add_handler(CommandHandler(["help", "Help"], help_cmd))
    app.add_handler(CommandHandler(["harem", "Hearm"], harem_cmd))
    app.add_handler(CommandHandler("balance", balance_cmd))
    app.add_handler(CommandHandler("daily", daily_cmd))
    app.add_handler(CommandHandler("claim", claim_cmd))
    app.add_handler(CommandHandler("search", search_cmd))
    app.add_handler(CommandHandler("sellprice", sellprice_cmd))
    app.add_handler(CommandHandler("market", market_cmd))
    app.add_handler(CommandHandler("sell", sell_cmd))
    app.add_handler(CommandHandler("buy", buy_cmd))

    # Admin Commands
    app.add_handler(CommandHandler("approvegroup", approvegroup_cmd))

    print("🚀 Nexus Card Bot Started Successfully!")
    
    async with app:
        await app.start()
        await app.updater.start_polling()
        await asyncio.Event().wait()

def main():
    Thread(target=run_flask, daemon=True).start()
    asyncio.run(run_bot())

if __name__ == "__main__":
    main()
