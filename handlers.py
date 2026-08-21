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

# Progress Bar Generator
def get_progress_bar(val, max_val=100, length=8):
    percent = min(max(val / max_val, 0), 1)
    filled = int(length * percent)
    return "▰" * filled + "▱" * (length - filled)

# Multi-Language Dictionary
TEXTS = {
    "MM": {
        "start": "✨ *WELCOME TO NEXUS CATCH RPG* ✨\n\n👋 မင်္ဂလာပါ {name}!\n🎮 Card များ စုဆောင်းပါ၊ Trade လုပ်ပါ၊ Arena တွင် စိန်ခေါ်လိုက်ပါ!",
        "must_join": "⚠️ *REQUIRED CHANNELS*\n\nBot ကို အသုံးပြုနိုင်ရန် အောက်ပါ Channel / Group ၂ ခုလုံးကို Join ပေးထားရန် လိုအပ်ပါသည်။",
        "no_card": "🎴 သင့်ထံတွင် Card မရှိသေးပါ။ `/claim` သို့မဟုတ် Group ထဲတွင် စာရိုက်၍ `/Nexus` ဖြင့် ဖမ်းယူပါ။",
        "gp_not_approved": "❌ *GROUP NOT APPROVED*\n\nဤ Group တွင် လူဦးရေ အနည်းဆုံး ၅၀ ရှိရမည်ဖြစ်ပြီး အုံနာထံမှ Approval ရရှိမှ သုံးနိုင်ပါမည်။",
        "lang_changed": "🇲🇲 မြန်မာဘာသာသို့ အောင်မြင်စွာ ပြောင်းလဲလိုက်ပါပြီ။"
    },
    "EN": {
        "start": "✨ *WELCOME TO NEXUS CATCH RPG* ✨\n\n👋 Welcome {name}!\n🎮 Collect cards, trade in market, and duel in arena!",
        "must_join": "⚠️ *REQUIRED CHANNELS*\n\nYou must join both channels below to access this bot.",
        "no_card": "🎴 You don't have any cards yet. Use `/claim` or catch with `/Nexus`!",
        "gp_not_approved": "❌ *GROUP NOT APPROVED*\n\nThis group needs at least 50 members and Owner Approval to use the bot.",
        "lang_changed": "🇬🇧 Language changed to English successfully."
    }
}

def t(user_id, key):
    u = db.get_user(user_id)
    lang = u.get("lang", "MM")
    return TEXTS[lang].get(key, TEXTS["MM"][key])

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

# ================= 1. USER & PROFILE HANDLERS =================
async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    db.get_user(user.id, user.first_name)
    
    caption = t(user.id, "start").format(name=user.first_name)
    keyboard = [
        [InlineKeyboardButton("🎴 My Waifu", callback_data="harem_1")],
        [InlineKeyboardButton("💬 Group", url=GROUP_LINK), InlineKeyboardButton("📢 Channel", url=CHANNEL_LINK)]
    ]
    
    img_url = "https://images.unsplash.com/photo-1578632767115-351597cf2477"
    await update.message.reply_photo(
        photo=img_url, caption=caption,
        reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown"
    )

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await help_page(update, context, page=1)

async def help_page(update_or_query, context, page=1):
    pages = {
        1: (
            "📜 *COMMAND DIRECTORY (PAGE 1/2)*\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "👤 *USER & CONFIG*\n"
            "• `/start` — Main Menu / Start\n"
            "• `/help` — Command Manual\n"
            "• `/profile` — Player Profile & Rank\n"
            "• `/lang` — Toggle Language (MM/EN)\n\n"
            "🎴 *COLLECTION & CARDS*\n"
            "• `/harem` — Card Vault List\n"
            "• `/claim` — Free 2 Cards (12h Cooldown)\n"
            "• `/daily` — Daily Coins Reward\n"
            "• `/search <name>` — Global Card Search\n"
            "• `/check <id>` — Inspection Card Details\n"
            "• `/fav <id>` / `/unfav <id>` — Favorite Bookmark\n"
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
            "• `/trade` (Reply) — P2P Interactive Trade\n"
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
        f"👑 *PLAYER PROFILE & OVERVIEW* 👑\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 *Player:* `{user.first_name}`\n"
        f"🆔 *User ID:* `{user.id}`\n"
        f"🌐 *Global Rank:* `#{rank}`\n\n"
        f"💰 *Wallet Balance:* `{u['coins']:,}` Coins\n"
        f"🎴 *Total Deck:* `{len(u['cards'])}` Cards\n"
        f"⭐ *Favorites:* `{len(u.get('favorites', []))}` Cards\n"
        f"🔥 *Daily Reward:* {'Claimed' if time.time() - u.get('last_daily', 0) < 86400 else 'Available'}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━"
    )
    
    if photos.total_count > 0:
        await update.message.reply_photo(photo=photos.photos[0][-1].file_id, caption=caption, parse_mode="Markdown")
    else:
        await update.message.reply_text(caption, parse_mode="Markdown")

# ================= 2. VAULT & SEARCH SYSTEM =================
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
        is_fav = "⭐ " if c["id"] in u.get("favorites", []) else "▪️ "
        lvl = c.get("level", 1)
        bar = get_progress_bar(c.get("exp", 0), 100, length=5)
        text += f"{is_fav}`{c['id']}` | *{m['name']}*\n └ Lv.{lvl} [{bar}]\n"
    
    text += "━━━━━━━━━━━━━━━━━━━━━━"
    nav = []
    if page > 1: nav.append(InlineKeyboardButton("⬅️ Prev", callback_data=f"harem_{page-1}"))
    if page < total_pages: nav.append(InlineKeyboardButton("Next ➡️", callback_data=f"harem_{page+1}"))
    
    markup = InlineKeyboardMarkup([nav]) if nav else None
    if hasattr(update_or_query, "message") and update_or_query.message:
        await update_or_query.message.reply_text(text, reply_markup=markup, parse_mode="Markdown")
    else:
        await update_or_query.edit_message_text(text, reply_markup=markup, parse_mode="Markdown")

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

# ================= 3. CLAIM, HMODE & REWARDS =================
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

async def hmode_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = db.get_user(update.effective_user.id)
    cards = u.get("cards", [])[:10]
    if not cards:
        await update.message.reply_text("❌ သင့်တွင် Card မရှိပါ။")
        return
    
    keyboard = []
    for c in cards:
        m = db.data["cards_master"].get(c["id"], {"name": "Card"})
        keyboard.append([InlineKeyboardButton(f"{m['name']} ({c['id']})", callback_data=f"set_hmode_{c['id']}")])
    
    await update.message.reply_text("🎯 HMode Vault Filter တွင် ပြသရန် Card တစ်ခုကို ရွေးပါ:", reply_markup=InlineKeyboardMarkup(keyboard))

async def reset_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = db.get_user(update.effective_user.id)
    u["hmode_selected"] = None
    db.save_db()
    await update.message.reply_text("✅ Filter အားလုံးကို Clean ပြုလုပ်လိုက်ပါပြီ။ Vault တွင် အားလုံး ပြန်မြင်ရပါမည်။")

async def fav_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("💡 Usage: `/fav <card_id>`")
        return
    cid = context.args[0]
    u = db.get_user(update.effective_user.id)
    if "favorites" not in u: u["favorites"] = []
    if cid not in u["favorites"]:
        u["favorites"].append(cid)
        db.save_db()
        await update.message.reply_text(f"⭐ Card `{cid}` ကို Favorite မှတ်လိုက်ပါပြီ။", parse_mode="Markdown")

async def unfav_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("💡 Usage: `/unfav <card_id>`")
        return
    cid = context.args[0]
    u = db.get_user(update.effective_user.id)
    if "favorites" in u and cid in u["favorites"]:
        u["favorites"].remove(cid)
        db.save_db()
        await update.message.reply_text(f"❌ Card `{cid}` အား Favorite မှ ဖြုတ်လိုက်ပါပြီ။", parse_mode="Markdown")

# ================= 4. MARKETPLACE & TRADE =================
async def sellprice_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "📊 *BASE PRICE CHART (RARITY TIERS)*\n━━━━━━━━━━━━━━━━━━━━━━\n"
        "• Tier 1 (Common): 💰 `1,000` Coins\n"
        "• Tier 2 (Rare): 💰 `3,500` Coins\n"
        "• Tier 3 (Epic): 💰 `7,500` Coins\n"
        "• Tier 4 (Legendary): 💰 `12,000` Coins\n"
        "• Tier 5 (Mythic): 💰 `15,000` Coins (Max Price)\n"
        "━━━━━━━━━━━━━━━━━━━━━━"
    )
    await update.message.reply_text(text, parse_mode="Markdown")

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

async def sell_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2:
        await update.message.reply_text("💡 Usage: `/sell [char_id] [price]`")
        return
    cid, price = context.args[0], int(context.args[1])
    if price > 15000:
        await update.message.reply_text("❌ ရောင်းဈေး သတ်မှတ်ချက် အမြင့်ဆုံးမှာ `15,000 Coins` ဖြစ်ပါသည်။")
        return
    
    u = db.get_user(update.effective_user.id)
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
    card = next((c for c in u1["cards"] if c["id"] == cid), None)
    if not card:
        await update.message.reply_text("❌ ထို Card သင့်ထံတွင် မရှိပါ။")
        return
    
    u1["cards"].remove(card)
    u2 = db.get_user(target.id, target.first_name)
    u2["cards"].append(card)
    db.save_db()
    await update.message.reply_text(f"🎁 *{update.effective_user.first_name}* မှ Card `{cid}` အား *{target.first_name}* ထံ လက်ဆောင်ပေးလိုက်ပါပြီ!", parse_mode="Markdown")

async def trade_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.reply_to_message or len(context.args) < 2:
        await update.message.reply_text("💡 Usage: Reply ပြန်၍ `/trade YOUR_ID THEIR_ID` ဟု ရိုက်ပါ။")
        return
    u1_id, u2_id = context.args[0], context.args[1]
    p1 = update.effective_user
    p2 = update.message.reply_to_message.from_user
    
    await update.message.reply_text(
        f"🤝 *TRADE SESSION INITIATED*\n━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 Trader 1: *{p1.first_name}* (`{u1_id}`)\n"
        f"👤 Trader 2: *{p2.first_name}* (`{u2_id}`)\n\n"
        f"အတည်ပြုရန် ညှိနှိုင်းမှု ပြုလုပ်ပါ။", parse_mode="Markdown"
    )

# ================= 5. SPAWN, CATCH & LOG =================
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

async def bot_added_to_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    for member in update.message.new_chat_members:
        if member.id == context.bot.id:
            chat = update.effective_chat
            user = update.effective_user
            count = await context.bot.get_chat_member_count(chat.id)
            
            log_msg = (
                f"🤖 *BOT ADDED TO NEW GROUP*\n━━━━━━━━━━━━━━━━━━━━━━\n"
                f"👥 *Group:* `{chat.title}`\n"
                f"🆔 *Group ID:* `{chat.id}`\n"
                f"👤 *Added By:* `{user.first_name}` (`{user.id}`)\n"
                f"📊 *Members Count:* `{count}`"
            )
            try:
                await context.bot.send_message(chat_id=LOG_CHANNEL_ID, text=log_msg, parse_mode="Markdown")
            except Exception: pass
            
            if count < 50:
                await update.message.reply_text(
                    "⚠️ *သတိပေးချက်:* Group တွင် အနည်းဆုံး လူဦးရေ ၅၀ ရှိရပါမည်။ Admin Access ပေးပြီး Owner အား Approve ပေးရန် အကြောင်းကြားပါ။"
                )

# ================= 6. BATTLE & RANKINGS =================
async def duel_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.reply_to_message:
        await update.message.reply_text("⚔️ Message ကို Reply ပြန်၍ `/duel` ဟု ရိုက်ပါ။")
        return
    p1, p2 = update.effective_user, update.message.reply_to_message.from_user
    u1, u2 = db.get_user(p1.id), db.get_user(p2.id)
    if not u1.get("cards") or not u2.get("cards"):
        await update.message.reply_text("❌ Duel တိုက်ရန် နှစ်ဦးစလုံးတွင် Card ရှိရပါမည်။")
        return
    
    winner = random.choice([p1, p2])
    db.get_user(winner.id)["coins"] += 300
    db.save_db()
    await update.message.reply_text(
        f"⚔️ *ARENA BATTLE RESULTS* ⚔️\n━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🥊 *{p1.first_name}* VS *{p2.first_name}*\n\n"
        f"🏆 *WINNER:* *{winner.first_name}*\n"
        f"🎁 *Prize:* 💰 `300` Coins & EXP", parse_mode="Markdown"
    )

async def upgrade_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("💡 Usage: `/upgrade <card_id>`")
        return
    cid = context.args[0]
    u = db.get_user(update.effective_user.id)
    card = next((c for c in u["cards"] if c["id"] == cid), None)
    if not card:
        await update.message.reply_text("❌ သင့်ထံတွင် ထို Card မရှိပါ။")
        return
    
    cost = card.get("level", 1) * 500
    if u["coins"] < cost:
        await update.message.reply_text(f"❌ Level Up ပြုလုပ်ရန် Coin `{cost}` လိုအပ်ပါသည်။")
        return
    
    u["coins"] -= cost
    card["level"] = card.get("level", 1) + 1
    card["exp"] = 0
    db.save_db()
    await update.message.reply_text(f"⬆️ Card `{cid}` အား Level `{card['level']}` သို့ အောင်မြင်စွာ Upgrade မြှင့်လိုက်ပါပြီ။")

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

# ================= 7. ADVANCED OWNER / ADMIN SYSTEM =================
async def addcard_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not db.is_admin_or_owner(update.effective_user.id): return
    try:
        # Check if Message Reply with Photo / Text
        if update.message.reply_to_message and update.message.reply_to_message.photo:
            cid, rarity, series, *name_parts = context.args
            cname = " ".join(name_parts)
            file_id = update.message.reply_to_message.photo[-1].file_id
            db.data["cards_master"][cid] = {"name": cname, "rarity": int(rarity), "series": series, "image": file_id}
        else:
            cid, rarity, series, *name_parts = context.args
            cname = " ".join(name_parts)
            db.data["cards_master"][cid] = {"name": cname, "rarity": int(rarity), "series": series}
        
        db.save_db()
        await update.message.reply_text(f"✅ Card *{cname}* (`{cid}`) ထည့်သွင်းပြီးပါပြီ။", parse_mode="Markdown")
    except Exception:
        await update.message.reply_text("💡 Usage: `/addcard <id> <rarity> <series> <card_name>` (Message Reply ဖြင့်လည်း ထည့်နိုင်ပါသည်)")

async def giveall_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not db.is_admin_or_owner(update.effective_user.id): return
    try:
        amt = int(context.args[0])
        for uid, udata in db.data["users"].items():
            udata["coins"] = udata.get("coins", 0) + amt
        db.save_db()
        await update.message.reply_text(f"🎉 All Users received 💰 `{amt}` Coins Giveaway!")
    except Exception: pass

async def givecard_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not db.is_admin_or_owner(update.effective_user.id): return
    try:
        target_id, cid = int(context.args[0]), context.args[1]
        u = db.get_user(target_id)
        u["cards"].append({"id": cid, "level": 1, "exp": 0})
        db.save_db()
        await update.message.reply_text(f"✅ User `{target_id}` ထံ Card `{cid}` ထည့်ပေးလိုက်ပါပြီ။")
    except Exception: pass

async def setadmin_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != db.OWNER_ID: return
    try:
        target_id = int(context.args[0])
        if target_id not in db.data["admins"]:
            db.data["admins"].append(target_id)
            db.save_db()
            await update.message.reply_text(f"👑 User `{target_id}` အား Admin ခန့်အပ်လိုက်ပါပြီ။")
    except Exception: pass

async def approvegroup_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not db.is_admin_or_owner(update.effective_user.id): return
    try:
        gid = int(context.args[0])
        gp = db.get_group(gid)
        gp["approved"] = True
        db.save_db()
        await update.message.reply_text(f"✅ Group `{gid}` ၏ အသုံးပြုခွင့် Approved ပေးလိုက်ပါပြီ။")
    except Exception: pass

async def changetime_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not db.is_admin_or_owner(update.effective_user.id): return
    try:
        gid, count = int(context.args[0]), int(context.args[1])
        gp = db.get_group(gid)
        gp["spawn_rate"] = count
        db.save_db()
        await update.message.reply_text(f"✅ Group `{gid}` ၏ Drop Rate အား မက်ဆေ့ဂျ် `{count}` စာကြောင်းဟု ပြောင်းလဲလိုက်ပါပြီ။")
    except Exception: pass

async def lang_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = db.get_user(update.effective_user.id)
    u["lang"] = "EN" if u.get("lang") == "MM" else "MM"
    db.save_db()
    await update.message.reply_text(t(update.effective_user.id, "lang_changed"))

# ================= 8. CALLBACK QUERY HANDLER =================
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
        
    elif data.startswith("harem_"):
        page = int(data.split("_")[1])
        await harem_page(query, context, page)
        
    elif data.startswith("help_"):
        page = int(data.split("_")[1])
        await help_page(query, context, page)
        
    elif data.startswith("set_hmode_"):
        cid = data.split("_")[2]
        u = db.get_user(user.id)
        u["hmode_selected"] = cid
        db.save_db()
        await query.answer(f"✅ Card ID {cid} ကို Vault Filter မှတ်လိုက်ပါပြီ။")

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
    app.add_handler(CommandHandler("hmode", hmode_cmd))
    app.add_handler(CommandHandler("reset", reset_cmd))
    app.add_handler(CommandHandler("fav", fav_cmd))
    app.add_handler(CommandHandler("unfav", unfav_cmd))
    
    # Economy & Market
    app.add_handler(CommandHandler("balance", balance_cmd))
    app.add_handler(CommandHandler("sellprice", sellprice_cmd))
    app.add_handler(CommandHandler("market", market_cmd))
    app.add_handler(CommandHandler("sell", sell_cmd))
    app.add_handler(CommandHandler("buy", buy_cmd))
    app.add_handler(CommandHandler("delist", delist_cmd))
    app.add_handler(CommandHandler("gift", gift_cmd))
    app.add_handler(CommandHandler("trade", trade_cmd))
    
    # Catching, Gameplay & Leaderboards
    app.add_handler(CommandHandler("Nexus", nexus_cmd))
    app.add_handler(CommandHandler("duel", duel_cmd))
    app.add_handler(CommandHandler("upgrade", upgrade_cmd))
    app.add_handler(CommandHandler(["top", "rankings"], top_cmd))
    app.add_handler(CommandHandler("ctop", ctop_cmd))
    app.add_handler(CommandHandler("todayNexusCatch", today_nexus_catch_cmd))
    
    # Admin / Owner Commands
    app.add_handler(CommandHandler("addcard", addcard_cmd))
    app.add_handler(CommandHandler("giveall", giveall_cmd))
    app.add_handler(CommandHandler("givecard", givecard_cmd))
    app.add_handler(CommandHandler("setadmin", setadmin_cmd))
    app.add_handler(CommandHandler("approvegroup", approvegroup_cmd))
    app.add_handler(CommandHandler("changetime", changetime_cmd))
    
    # Listeners
    app.add_handler(CallbackQueryHandler(callback_handler))
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, bot_added_to_group))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_group_spawns))
