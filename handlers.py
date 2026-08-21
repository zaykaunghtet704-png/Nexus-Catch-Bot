import time
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes, CommandHandler, MessageHandler, CallbackQueryHandler, filters
)
from database import db

# ================= CONSTANTS & LINKS =================
GROUP_LINK = "https://t.me/+00J7JktW8bJlZTY1"
CHANNEL_LINK = "https://t.me/+E6BxfAj0gaI2Y2Zl"
LOG_CHANNEL_ID = -1001234567890  # Owner Log Channel ID

def get_progress_bar(val, max_val=100, length=8):
    percent = min(max(val / max_val, 0), 1)
    filled = int(length * percent)
    return "▰" * filled + "▱" * (length - filled)

# Dynamic Language Helper
TEXTS = {
    "MM": {
        "start": "✨ *WELCOME TO NEXUS CATCH RPG* ✨\n\n👋 မင်္ဂလာပါ {name}!\n🎮 Card များ စုဆောင်းပါ၊ Trade လုပ်ပါ၊ Arena တွင် စိန်ခေါ်လိုက်ပါ!",
        "must_join": "⚠️ *REQUIRED CHANNELS*\n\nBot ကို အသုံးပြုနိုင်ရန် အောက်ပါ Channel / Group ၂ ခုလုံးကို Join ပေးထားရန် လိုအပ်ပါသည်။",
        "no_card": "🎴 သင့်ထံတွင် Card မရှိသေးပါ။ `/claim` သို့မဟုတ် Group ထဲတွင် စာရိုက်၍ `/Nexus` ဖြင့် ဖမ်းယူပါ။",
        "lang_select": "🌐 *SELECT LANGUAGE / ဘာသာစကား ရွေးချယ်ပါ*",
        "lang_set": "🇲🇲 မြန်မာဘာသာသို့ အောင်မြင်စွာ ပြောင်းလဲလိုက်ပါပြီ။"
    },
    "EN": {
        "start": "✨ *WELCOME TO NEXUS CATCH RPG* ✨\n\n👋 Welcome {name}!\n🎮 Collect cards, trade in market, and duel in arena!",
        "must_join": "⚠️ *REQUIRED CHANNELS*\n\nYou must join both channels below to access this bot.",
        "no_card": "🎴 You don't have any cards yet. Use `/claim` or catch with `/Nexus`!",
        "lang_select": "🌐 *SELECT PREFERRED LANGUAGE*",
        "lang_set": "🇬🇧 Language changed to English successfully."
    }
}

def t(user_id, key):
    u = db.get_user(user_id)
    lang = u.get("lang", "MM")
    return TEXTS.get(lang, TEXTS["MM"]).get(key, TEXTS["MM"].get(key, ""))

async def check_joined(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    user_id = update.effective_user.id
    u = db.get_user(user_id)
    if u.get("is_verified", False):
        return True

    keyboard = [
        [InlineKeyboardButton("💬 Join Group", url=GROUP_LINK), InlineKeyboardButton("📢 Join Channel", url=CHANNEL_LINK)],
        [InlineKeyboardButton("✅ Verified (ဝင်ပြီးပါပြီ)", callback_data="verify_join")]
    ]
    await update.message.reply_text(
        t(user_id, "must_join"),
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )
    return False

# ================= 1. USER & SYSTEM CONFIG =================
async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    db.get_user(user.id, user.first_name)
    
    caption = t(user.id, "start").format(name=user.first_name)
    keyboard = [
        [InlineKeyboardButton("🎴 My Waifu", callback_data="harem_1"), InlineKeyboardButton("🌐 Language", callback_data="open_lang")],
        [InlineKeyboardButton("💬 Group", url=GROUP_LINK), InlineKeyboardButton("📢 Channel", url=CHANNEL_LINK)]
    ]
    
    img_url = "https://images.unsplash.com/photo-1578632767115-351597cf2477"
    await update.message.reply_photo(
        photo=img_url, caption=caption,
        reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown"
    )

async def lang_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    keyboard = [
        [InlineKeyboardButton("🇲🇲 မြန်မာစာ", callback_data="set_lang_MM"), InlineKeyboardButton("🇬🇧 English", callback_data="set_lang_EN")]
    ]
    await update.message.reply_text(t(user_id, "lang_select"), reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await help_page(update, context, page=1)

async def help_page(update_or_query, context, page=1):
    pages = {
        1: (
            "📜 *COMMAND DIRECTORY (PAGE 1/2)*\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "👤 *USER SYSTEM*\n"
            "• `/start` — Main Menu / Start\n"
            "• `/help` — Command Directory\n"
            "• `/profile` — Player Profile & Rank\n"
            "• `/lang` — Toggle Language (MM/EN)\n\n"
            "🎴 *COLLECTION & CARDS*\n"
            "• `/harem` — Card Vault List\n"
            "• `/claim` — Free 2 Cards (12h Cooldown)\n"
            "• `/daily` — Daily Coins Reward\n"
            "• `/search <name>` — Global Card Search\n"
            "• `/check <id>` — Inspection Card Details\n"
            "• `/fav <id>` / `/unfav <id>` — Favorite Bookmark\n"
            "• `/lock <id>` / `/unlock <id>` — Lock/Unlock Card\n"
            "• `/hmode` — Filter Top 10 Vault Mode\n"
            "• `/reset` — Clean Vault Filters"
        ),
        2: (
            "📜 *COMMAND DIRECTORY (PAGE 2/2)*\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "🎯 *CATCHING & ARENA*\n"
            "• `/Nexus <Name>` — Catch Spawned Card\n"
            "• `/upgrade <id>` — Upgrade Card Level\n"
            "• `/duel` (Reply) — Arena Card Battle\n\n"
            "💰 *ECONOMY & TRADE*\n"
            "• `/balance` — Check Coin Balance\n"
            "• `/market` — Marketplace Listings\n"
            "• `/sell <id> <price>` — List Card for Sale\n"
            "• `/buy <list_id>` — Buy Listed Card\n"
            "• `/delist <list_id>` — Cancel Market Listing\n"
            "• `/sellprice` — Tier Pricing Chart\n"
            "• `/trade` (Reply) — Trade System\n"
            "• `/gift <id>` (Reply) — Send Gift Card\n\n"
            "🏆 *LEADERBOARDS*\n"
            "• `/top` / `/rankings` — Global Leaderboard\n"
            "• `/ctop` — Local Group Top Catchers\n"
            "• `/todayNexusCatch` — Daily Top Catchers"
        )
    }
    
    keyboard = []
    if page == 1:
        keyboard.append([InlineKeyboardButton("Next Page ➡️", callback_data="help_2")])
    else:
        keyboard.append([InlineKeyboardButton("⬅️ Prev Page", callback_data="help_1")])

    markup = InlineKeyboardMarkup(keyboard)
    if hasattr(update_or_query, "message") and update_or_query.message:
        await update_or_query.message.reply_text(pages[page], reply_markup=markup, parse_mode="Markdown")
    else:
        await update_or_query.edit_message_text(pages[page], reply_markup=markup, parse_mode="Markdown")

async def profile_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    u = db.get_user(user.id, user.first_name)
    
    all_users = sorted(db.data["users"].items(), key=lambda x: len(x[1].get("cards", [])), reverse=True)
    rank = next((i for i, (uid, _) in enumerate(all_users, 1) if int(uid) == user.id), "N/A")

    photos = await context.bot.get_user_profile_photos(user.id, limit=1)
    
    caption = (
        f"👑 *PLAYER PROFILE OVERVIEW* 👑\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 *Player:* `{user.first_name}`\n"
        f"🆔 *User ID:* `{user.id}`\n"
        f"🌐 *Global Rank:* `#{rank}`\n"
        f"🗣️ *Language:* `{u.get('lang', 'MM')}`\n\n"
        f"💰 *Wallet:* `{u['coins']:,}` Coins\n"
        f"🎴 *Total Cards:* `{len(u['cards'])}` Cards\n"
        f"🔒 *Locked Cards:* `{len(u.get('locked', []))}` Cards\n"
        f"⭐ *Favorites:* `{len(u.get('favorites', []))}` Cards\n"
        f"━━━━━━━━━━━━━━━━━━━━━━"
    )
    
    if photos.total_count > 0:
        await update.message.reply_photo(photo=photos.photos[0][-1].file_id, caption=caption, parse_mode="Markdown")
    else:
        await update.message.reply_text(caption, parse_mode="Markdown")

# ================= 2. VAULT, SEARCH & LOCK SYSTEM =================
async def harem_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_joined(update, context): return
    await harem_page(update, context, page=1)

async def harem_page(update_or_query, context, page=1):
    user = update_or_query.effective_user
    u = db.get_user(user.id)
    cards = u.get("cards", [])

    if not cards:
        msg = t(user.id, "no_card")
        if hasattr(update_or_query, "message") and update_or_query.message:
            await update_or_query.message.reply_text(msg)
        else:
            await update_or_query.edit_message_text(msg)
        return

    if u.get("hmode_selected"):
        cards = [c for c in cards if c["id"] == u["hmode_selected"]]

    per_page = 8
    total_pages = max(1, (len(cards) + per_page - 1) // per_page)
    start_idx = (page - 1) * per_page
    page_cards = cards[start_idx:start_idx + per_page]

    text = f"🎴 *{user.first_name}'s CARD VAULT (Page {page}/{total_pages})*\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
    for idx, c in enumerate(page_cards, start_idx + 1):
        m = db.data["cards_master"].get(c["id"], {"name": "Unknown"})
        is_fav = "⭐ " if c["id"] in u.get("favorites", []) else ""
        is_lock = "🔒 " if c["id"] in u.get("locked", []) else ""
        lvl = c.get("level", 1)
        bar = get_progress_bar(c.get("exp", 0), 100, length=5)
        text += f"{is_lock}{is_fav}`{c['id']}` | *{m['name']}*\n └ Lv.{lvl} [{bar}]\n"
    
    text += "━━━━━━━━━━━━━━━━━━━━━━"
    nav = []
    if page > 1: nav.append(InlineKeyboardButton("⬅️ Prev", callback_data=f"harem_{page-1}"))
    if page < total_pages: nav.append(InlineKeyboardButton("Next ➡️", callback_data=f"harem_{page+1}"))
    
    markup = InlineKeyboardMarkup([nav]) if nav else None
    if hasattr(update_or_query, "message") and update_or_query.message:
        await update_or_query.message.reply_text(text, reply_markup=markup, parse_mode="Markdown")
    else:
        await update_or_query.edit_message_text(text, reply_markup=markup, parse_mode="Markdown")

async def lock_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("💡 Usage: `/lock <card_id>`")
        return
    cid = context.args[0]
    u = db.get_user(update.effective_user.id)
    if "locked" not in u: u["locked"] = []
    if cid not in u["locked"]:
        u["locked"].append(cid)
        db.save_db()
        await update.message.reply_text(f"🔒 Card `{cid}` အား Lock ခတ်လိုက်ပါပြီ။ ရောင်းချ/လက်ဆောင်ပေးခြင်း ပြုလုပ်၍ ရတော့မည်မဟုတ်ပါ။", parse_mode="Markdown")

async def unlock_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("💡 Usage: `/unlock <card_id>`")
        return
    cid = context.args[0]
    u = db.get_user(update.effective_user.id)
    if "locked" in u and cid in u["locked"]:
        u["locked"].remove(cid)
        db.save_db()
        await update.message.reply_text(f"🔓 Card `{cid}` အား Unlock ပြန်ဖြုတ်လိုက်ပါပြီ။", parse_mode="Markdown")

async def search_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = " ".join(context.args).lower() if context.args else ""
    results = []
    for cid, info in db.data["cards_master"].items():
        if not query or query in info["name"].lower():
            results.append(f"• `{cid}` — *{info['name']}*")

    if not results:
        await update.message.reply_text("❌ မည်သည့် Card မှ ရှာမတွေ့ပါ။")
        return

    text = f"🔍 *CARD DATABASE ({len(results)} Found):*\n━━━━━━━━━━━━━━━━━━━━━━\n" + "\n".join(results[:12])
    keyboard = [[InlineKeyboardButton("📢 Updates Channel", url=CHANNEL_LINK)]]
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

async def check_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("💡 Usage: `/check <card_id>`")
        return
    cid = context.args[0]
    info = db.data["cards_master"].get(cid)
    if not info:
        await update.message.reply_text("❌ ထို Card ID မရှိပါ။")
        return
    
    text = (
        f"🎴 *CARD DETAILS INSPECTION*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🆔 *ID:* `{cid}`\n"
        f"👤 *Name:* *{info['name']}*\n"
        f"📺 *Series:* `{info.get('series', 'Anime')}`\n"
        f"⭐ *Rarity Tier:* Level {info.get('rarity', 1)}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━"
    )
    await update.message.reply_text(text, parse_mode="Markdown")

# ================= 3. REWARDS & MARKETPLACE =================
async def claim_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = db.get_user(update.effective_user.id, update.effective_user.first_name)
    now = time.time()
    if now - u.get("last_claim", 0) < 43200:
        rem = int((43200 - (now - u["last_claim"])) // 3600)
        await update.message.reply_text(f"⏱️ Free Claim ပြုလုပ်ရန် `{rem}` နာရီ လိုသေးပါသည်။ (Cooldown: 12 Hours)")
        return
    
    card_ids = list(db.data["cards_master"].keys())
    if not card_ids:
        await update.message.reply_text("❌ Card Database အလွတ်ဖြစ်နေပါသည်။")
        return
    
    got_ids = random.sample(card_ids, min(2, len(card_ids)))
    for gid in got_ids:
        u["cards"].append({"id": gid, "level": 1, "exp": 0})
    
    u["last_claim"] = now
    db.save_db()
    c_names = ", ".join([db.data["cards_master"][i]['name'] for i in got_ids])
    await update.message.reply_text(f"🎁 *CLAIM SUCCESSFUL (2 Cards)!*\n━━━━━━━━━━━━━━━━━━━━━━\n🎉 ရရှိသော ကဒ်များ: *{c_names}*", parse_mode="Markdown")

async def daily_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = db.get_user(update.effective_user.id, update.effective_user.first_name)
    now = time.time()
    if now - u.get("last_daily", 0) < 86400:
        await update.message.reply_text("⏱️ Daily Rewards ကို ၂၄ နာရီမှ ၁ ကြိမ်သာ ယူနိုင်ပါသည်။")
        return
    u["coins"] += 500
    u["last_daily"] = now
    db.save_db()
    await update.message.reply_text("🪙 *DAILY REWARD:* 💰 `500` Coins အောင်မြင်စွာ ရရှိပါသည်။", parse_mode="Markdown")

async def balance_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = db.get_user(update.effective_user.id, update.effective_user.first_name)
    await update.message.reply_text(f"💳 *{update.effective_user.first_name}* ၏ Wallet: 💰 `{u['coins']:,}` Coins", parse_mode="Markdown")

async def sell_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2:
        await update.message.reply_text("💡 Usage: `/sell [char_id] [price]`")
        return
    cid, price = context.args[0], int(context.args[1])
    u = db.get_user(update.effective_user.id)
    
    if cid in u.get("locked", []):
        await update.message.reply_text("❌ ဤ Card အား Lock ခတ်ထားသဖြင့် ရောင်းချ၍မရပါ။ ရှေးဦးစွာ `/unlock` ပြုလုပ်ပါ။")
        return

    card = next((c for c in u["cards"] if c["id"] == cid), None)
    if not card:
        await update.message.reply_text("❌ ထို Card သင့်ထံတွင် မရှိပါ။")
        return
    
    u["cards"].remove(card)
    lid = str(random.randint(1000, 9999))
    if "market" not in db.data: db.data["market"] = {}
    db.data["market"][lid] = {"seller_id": update.effective_user.id, "card_id": cid, "price": price}
    db.save_db()
    await update.message.reply_text(f"✅ Card `{cid}` အား Market ထဲသို့ Listing ID `{lid}` ဖြင့် တင်လိုက်ပါပြီ။", parse_mode="Markdown")

async def market_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    m_data = db.data.get("market", {})
    if not m_data:
        await update.message.reply_text("🛍️ *GLOBAL MARKETPLACE*\n━━━━━━━━━━━━━━━━━━━━━━\nလက်ရှိ ရောင်းရန် တင်ထားသော Card မရှိပါ။", parse_mode="Markdown")
        return
    text = "🛍️ *GLOBAL MARKETPLACE LISTINGS*\n━━━━━━━━━━━━━━━━━━━━━━\n"
    for lid, item in list(m_data.items())[:10]:
        c_info = db.data["cards_master"].get(item["card_id"], {"name": "Unknown"})
        text += f"▸ ID: `{lid}` | *{c_info['name']}* — 💰 `{item['price']:,}` Coins\n"
    await update.message.reply_text(text, parse_mode="Markdown")

async def buy_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("💡 Usage: `/buy [listing_id]`")
        return
    lid = context.args[0]
    item = db.data.get("market", {}).get(lid)
    if not item:
        await update.message.reply_text("❌ ထို Listing ID မရှိပါ။")
        return
    buyer = db.get_user(update.effective_user.id)
    if buyer["coins"] < item["price"]:
        await update.message.reply_text("❌ Coins မလုံလောက်ပါ။")
        return
    
    buyer["coins"] -= item["price"]
    seller = db.get_user(item["seller_id"])
    seller["coins"] += item["price"]
    buyer["cards"].append({"id": item["card_id"], "level": 1, "exp": 0})
    del db.data["market"][lid]
    db.save_db()
    await update.message.reply_text(f"🎉 Listing `{lid}` မှ Card ကို 💰 `{item['price']:,}` Coins ဖြင့် ဝယ်ယူလိုက်ပါပြီ။", parse_mode="Markdown")

async def delist_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("💡 Usage: `/delist [listing_id]`")
        return
    lid = context.args[0]
    item = db.data.get("market", {}).get(lid)
    if not item or item["seller_id"] != update.effective_user.id:
        await update.message.reply_text("❌ သင့် Listing ID မဟုတ်ပါ။")
        return
    u = db.get_user(update.effective_user.id)
    u["cards"].append({"id": item["card_id"], "level": 1, "exp": 0})
    del db.data["market"][lid]
    db.save_db()
    await update.message.reply_text(f"✅ Listing `{lid}` အား Market ပေါ်မှ ပြန်ဖြုတ်လိုက်ပါပြီ။")

async def gift_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args or not update.message.reply_to_message:
        await update.message.reply_text("💡 Usage: Message ကို Reply ပြန်ပြီး `/gift <CHAR_ID>` ဟု ရိုက်ပါ။")
        return
    cid = context.args[0]
    target = update.message.reply_to_message.from_user
    u1 = db.get_user(update.effective_user.id)
    
    if cid in u1.get("locked", []):
        await update.message.reply_text("❌ Lock ခတ်ထားသော Card ကို လက်ဆောင်ပေး၍ မရပါ။")
        return

    card = next((c for c in u1["cards"] if c["id"] == cid), None)
    if not card:
        await update.message.reply_text("❌ ထို Card သင့်ထံတွင် မရှိပါ။")
        return
    
    u1["cards"].remove(card)
    u2 = db.get_user(target.id, target.first_name)
    u2["cards"].append(card)
    db.save_db()
    await update.message.reply_text(f"🎁 *{update.effective_user.first_name}* မှ Card `{cid}` အား *{target.first_name}* ထံ လက်ဆောင်ပေးလိုက်ပါပြီ!", parse_mode="Markdown")

# ================= 4. SPAWN & CATCHING =================
async def handle_group_spawns(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_chat or update.effective_chat.type == "private":
        return
    
    chat_id = update.effective_chat.id
    gp = db.get_group(chat_id)
    
    if not gp.get("approved", False): return
    
    gp["msg_count"] += 1
    if gp["msg_count"] >= gp.get("spawn_rate", 85):
        gp["msg_count"] = 0
        card_ids = list(db.data["cards_master"].keys())
        if not card_ids: return
        chosen_id = random.choice(card_ids)
        c_info = db.data["cards_master"][chosen_id]
        
        gp["spawned_card"] = {"id": chosen_id, "name": c_info["name"].lower()}
        db.save_db()
        await update.message.reply_text(
            f"🌟 *A WILD CARD HAS APPEARED!* 🌟\n━━━━━━━━━━━━━━━━━━━━━━\n"
            f"❓ Name: ???\n🎯 ဖမ်းယူရန်: `/Nexus <Card_Name>`", parse_mode="Markdown"
        )

async def nexus_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args: return
    gp = db.get_group(update.effective_chat.id)
    spawned = gp.get("spawned_card")
    if not spawned:
        await update.message.reply_text("❌ ဖမ်းယူရန် Card မရှိသေးပါ။")
        return
    
    guess = " ".join(context.args).lower().strip()
    if guess == spawned["name"]:
        cid = spawned["id"]
        c_info = db.data["cards_master"][cid]
        u = db.get_user(update.effective_user.id, update.effective_user.first_name)
        u["cards"].append({"id": cid, "level": 1, "exp": 0})
        u["today_catches"] = u.get("today_catches", 0) + 1
        
        gp["top_catchers"] = gp.get("top_catchers", {})
        uid_str = str(update.effective_user.id)
        gp["top_catchers"][uid_str] = gp["top_catchers"].get(uid_str, 0) + 1
        gp["spawned_card"] = None
        db.save_db()
        
        await update.message.reply_text(
            f"🎉 *CONGRATULATIONS {update.effective_user.first_name}!*\n"
            f"သင်သည် *{c_info['name']}* (`{cid}`) ကို အောင်မြင်စွာ ဖမ်းယူလိုက်ပါပြီ။ 🎴", parse_mode="Markdown"
        )

# ================= 5. RANKINGS & ARENA =================
async def top_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    users = list(db.data["users"].items())
    users.sort(key=lambda x: len(x[1].get("cards", [])), reverse=True)
    text = "🏆 *GLOBAL TOP 15 CARD COLLECTORS* 🏆\n━━━━━━━━━━━━━━━━━━━━━━\n"
    for idx, (uid, uinfo) in enumerate(users[:15], 1):
        text += f"{idx}. *{uinfo.get('name', 'User')}* — 🎴 `{len(uinfo.get('cards', []))}` Cards\n"
    await update.message.reply_text(text, parse_mode="Markdown")

async def ctop_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == "private":
        await update.message.reply_text("❌ ဤ Command ကို Group ထဲတွင်သာ သုံး၍ရပါသည်။")
        return
    gp = db.get_group(update.effective_chat.id)
    catches = gp.get("top_catchers", {})
    sorted_c = sorted(catches.items(), key=lambda x: x[1], reverse=True)
    
    text = f"🏆 *GROUP TOP CATCHERS ({update.effective_chat.title})*\n━━━━━━━━━━━━━━━━━━━━━━\n"
    for idx, (uid, count) in enumerate(sorted_c[:10], 1):
        uinfo = db.get_user(int(uid))
        text += f"{idx}. *{uinfo.get('name', 'User')}* — 🎯 `{count}` Catches\n"
    await update.message.reply_text(text, parse_mode="Markdown")

async def today_nexus_catch_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    users = list(db.data["users"].items())
    users.sort(key=lambda x: x[1].get("today_catches", 0), reverse=True)
    text = "🔥 *TODAY'S TOP CATCHERS* 🔥\n━━━━━━━━━━━━━━━━━━━━━━\n"
    for idx, (uid, uinfo) in enumerate(users[:10], 1):
        text += f"{idx}. *{uinfo.get('name', 'User')}* — 🎴 `{uinfo.get('today_catches', 0)}` Cards\n"
    await update.message.reply_text(text, parse_mode="Markdown")

# ================= 6. CALLBACK QUERY HANDLER =================
async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    user = query.from_user
    
    if data == "verify_join":
        u = db.get_user(user.id)
        u["is_verified"] = True
        db.save_db()
        await query.answer("✅ Verification အောင်မြင်ပါသည်။")
        await query.message.delete()
        
    elif data == "open_lang":
        keyboard = [
            [InlineKeyboardButton("🇲🇲 မြန်မာစာ", callback_data="set_lang_MM"), InlineKeyboardButton("🇬🇧 English", callback_data="set_lang_EN")]
        ]
        await query.message.edit_text(t(user.id, "lang_select"), reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

    elif data.startswith("set_lang_"):
        lang_code = data.split("_")[2]
        u = db.get_user(user.id)
        u["lang"] = lang_code
        db.save_db()
        await query.answer("✅ Language Updated!")
        await query.message.edit_text(t(user.id, "lang_set"), parse_mode="Markdown")

    elif data.startswith("harem_"):
        page = int(data.split("_")[1])
        await harem_page(query, context, page)
        
    elif data.startswith("help_"):
        page = int(data.split("_")[1])
        await help_page(query, context, page)

# ================= REGISTER ALL HANDLERS =================
def register_all_handlers(app):
    # Core User Commands
    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("profile", profile_cmd))
    app.add_handler(CommandHandler("lang", lang_cmd))
    
    # Collection Commands
    app.add_handler(CommandHandler("harem", harem_cmd))
    app.add_handler(CommandHandler("search", search_cmd))
    app.add_handler(CommandHandler("check", check_cmd))
    app.add_handler(CommandHandler("claim", claim_cmd))
    app.add_handler(CommandHandler("daily", daily_cmd))
    app.add_handler(CommandHandler("lock", lock_cmd))
    app.add_handler(CommandHandler("unlock", unlock_cmd))
    
    # Economy & Market
    app.add_handler(CommandHandler("balance", balance_cmd))
    app.add_handler(CommandHandler("market", market_cmd))
    app.add_handler(CommandHandler("sell", sell_cmd))
    app.add_handler(CommandHandler("buy", buy_cmd))
    app.add_handler(CommandHandler("delist", delist_cmd))
    app.add_handler(CommandHandler("gift", gift_cmd))
    
    # Catching & Rankings
    app.add_handler(CommandHandler("Nexus", nexus_cmd))
    app.add_handler(CommandHandler(["top", "rankings"], top_cmd))
    app.add_handler(CommandHandler("ctop", ctop_cmd))
    app.add_handler(CommandHandler("todayNexusCatch", today_nexus_catch_cmd))
    
    # Listeners
    app.add_handler(CallbackQueryHandler(callback_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_group_spawns))
