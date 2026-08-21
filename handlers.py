import time
import random
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters
from database import db
from config import RARITY_STAGES
from keyboards import get_start_keyboard, get_trade_keyboard

# ================= USER & PROFILE HANDLERS =================
async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    db.get_user(user.id, user.first_name)
    await update.message.reply_text(
        f"👑 *WELCOME TO NEXUS CATCH BOT* 👑\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"👋 မင်္ဂလာပါ *{user.first_name}*!\n\n"
        f"🎮 *Nexus RPG World* မှ နွေးထွေးစွာ ကြိုဆိုပါတယ်။\n"
        f"🏆 Group များတွင် စာတိုများ ပို့ရင်း Card များ ဖမ်းယူ၊ စုဆောင်း၊ Trade လုပ်ပြီး Battle စိန်ခေါ်နိုင်ပါပြီ။\n\n"
        f"💡 Command များ ကြည့်ရန်: `/help`",
        reply_markup=get_start_keyboard(), parse_mode="Markdown"
    )

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "📜 *NEXUS RPG — COMMAND DIRECTORY*\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "🎴 *COLLECTION & CARDS*\n"
        " ├ `/harem` • မိမိပိုင်ဆိုင်သော ကဒ်များ ကြည့်ရန်\n"
        " ├ `/claim` • ၁၂ နာရီ ၁ ကြိမ် Free Card ယူရန်\n"
        " ├ `/daily` • နေ့စဉ် Free Coins ယူရန်\n"
        " ├ `/fav <id>` • Favorite Card မှတ်ရန်\n"
        " ├ `/unfav <id>` • Favorite မှတ်ထားတာ ဖြုတ်ရန်\n"
        " ├ `/burn <id>` • Card ကို Coin အဖြစ် ပြောင်းရန်\n"
        " └ `/search <name>` • Card များ အမည်ဖြင့် ရှာရန်\n\n"
        "🎯 *SPAWN & CATCH*\n"
        " ├ `/guess <name>` • ပေါ်လာသော Card ဖမ်းရန်\n"
        " ├ `/catch <name>` • Card ဖမ်းရန် (Alternative)\n"
        " └ `/droptime` • Next Card Drop မည့်အချိန် စစ်ရန်\n\n"
        "💰 *ECONOMY & MARKETPLACE*\n"
        " ├ `/balance` • လက်ကျန် Wallet စစ်ရန်\n"
        " ├ `/market` • Global Marketplace ကြည့်ရန်\n"
        " ├ `/sell <id> <price>` • Market တွင် Card ရောင်းရန်\n"
        " ├ `/sellprice` • Rarity အလိုက် ရောင်းဈေး စစ်ရန်\n"
        " ├ `/buy <listing_id>` • Market မှ Card ဝယ်ရန်\n"
        " ├ `/pay <user> <amt>` • Coins လွှဲပေးရန် (Reply)\n"
        " ├ `/trade <user>` • Interactive Trade စရန် (Reply)\n"
        " └ `/gift <user> <id>` • Card လက်ဆောင်ပေးရန် (Reply)\n\n"
        "⚔️ *ARENA & LEADERBOARD*\n"
        " ├ `/duel <user>` • Card Battle စိန်ခေါ်ရန် (Reply)\n"
        " ├ `/gacha` • Card Lucky Roll နှိုက်ရန်\n"
        " └ `/top` / `/ctop` / `/ranking` • Leaderboard\n"
        "━━━━━━━━━━━━━━━━━━━━━━"
    )
    await update.message.reply_text(text, parse_mode="Markdown")

async def profile_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = db.get_user(update.effective_user.id, update.effective_user.first_name)
    text = (
        f"🎮 *PLAYER PROFILE OVERVIEW*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 *Name:* `{update.effective_user.first_name}`\n"
        f"🆔 *ID:* `{update.effective_user.id}`\n\n"
        f"💰 *Wallet:* `{u['coins']:,}` Coins\n"
        f"🎴 *Deck:* `{len(u['cards'])}` Cards\n"
        f"⭐ *Favorites:* `{len(u.get('favorites', []))}` Cards\n"
        f"━━━━━━━━━━━━━━━━━━━━━━"
    )
    await update.message.reply_text(text, parse_mode="Markdown")

# ================= CARD MANAGEMENT HANDLERS =================
async def harem_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = db.get_user(update.effective_user.id, update.effective_user.first_name)
    cards = u["cards"]
    if not cards:
        await update.message.reply_text("🎴 သင့်ထံတွင် Card မရှိသေးပါ။ `/claim` သို့မဟုတ် `/gacha` အသုံးပြုပါ။")
        return
    text = f"🎴 *{update.effective_user.first_name}'s CARD VAULT ({len(cards)} Cards)*\n━━━━━━━━━━━━━━━━━━━━━━\n"
    for idx, c in enumerate(cards, 1):
        m = db.data["cards_master"].get(c["id"], {"name": "Unknown", "rarity": 1})
        r_info = RARITY_STAGES.get(m["rarity"], {"name": "Common"})
        is_fav = "⭐ " if c["id"] in u.get("favorites", []) else "▪️ "
        text += f"{is_fav}`{c['id']}` | *{m['name']}* [{r_info['name']}]\n"
    text += "━━━━━━━━━━━━━━━━━━━━━━"
    await update.message.reply_text(text, parse_mode="Markdown")

async def claim_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = db.get_user(update.effective_user.id, update.effective_user.first_name)
    now = time.time()
    if now - u.get("last_claim", 0) < 43200:
        rem = int((43200 - (now - u["last_claim"])) // 3600)
        await update.message.reply_text(f"⏳ Free Claim ပြုလုပ်ရန် `{rem}` နာရီ စောင့်ဆိုင်းပေးပါ။")
        return
    card_ids = list(db.data["cards_master"].keys())
    got_id = random.choice(card_ids)
    u["cards"].append({"id": got_id, "print": random.randint(1, 500), "mint": 100})
    u["last_claim"] = now
    db.save_db()
    c_info = db.data["cards_master"][got_id]
    await update.message.reply_text(
        f"🎁 *CLAIM SUCCESSFUL!*\n━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🎉 သင်ရရှိလိုက်သော Card: *{c_info['name']}*\n"
        f"🆔 *Card ID:* `{got_id}`", parse_mode="Markdown"
    )

async def daily_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = db.get_user(update.effective_user.id, update.effective_user.first_name)
    now = time.time()
    if now - u.get("last_daily", 0) < 86400:
        await update.message.reply_text("⏳ Daily Coins ကို ၂၄ နာရီမှ ၁ ကြိမ်သာ ယူနိုင်ပါသည်။")
        return
    u["coins"] += 500
    u["last_daily"] = now
    db.save_db()
    await update.message.reply_text("🪙 *DAILY REWARD:* 💰 `500` Coins အောင်မြင်စွာ ရရှိပါသည်။", parse_mode="Markdown")

async def fav_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("💡 Usage: `/fav <card_id>`", parse_mode="Markdown")
        return
    cid = context.args[0]
    u = db.get_user(update.effective_user.id)
    if "favorites" not in u: u["favorites"] = []
    if cid not in u["favorites"]:
        u["favorites"].append(cid)
        db.save_db()
        await update.message.reply_text(f"⭐ Card ID `{cid}` ကို Favorite မှတ်လိုက်ပါပြီ။", parse_mode="Markdown")

async def unfav_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("💡 Usage: `/unfav <card_id>`", parse_mode="Markdown")
        return
    cid = context.args[0]
    u = db.get_user(update.effective_user.id)
    if "favorites" in u and cid in u["favorites"]:
        u["favorites"].remove(cid)
        db.save_db()
        await update.message.reply_text(f"❌ Card ID `{cid}` အား Favorite မှ ဖြုတ်လိုက်ပါပြီ။", parse_mode="Markdown")

async def burn_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("💡 Usage: `/burn <card_id>`", parse_mode="Markdown")
        return
    cid = context.args[0]
    u = db.get_user(update.effective_user.id)
    card = next((c for c in u["cards"] if c["id"] == cid), None)
    if not card:
        await update.message.reply_text("❌ ထို Card သင့်ထံတွင် မရှိပါ။")
        return
    u["cards"].remove(card)
    u["coins"] += 300
    db.save_db()
    await update.message.reply_text(f"🔥 Card `{cid}` ကို ဖျက်ဆီးလိုက်ပြီး 🪙 `300` Coins ပြန်ရယူလိုက်ပါသည်။", parse_mode="Markdown")

async def search_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("💡 Usage: `/search <character_name>`", parse_mode="Markdown")
        return
    query = " ".join(context.args).lower()
    results = []
    for cid, info in db.data["cards_master"].items():
        if query in info["name"].lower():
            results.append(f"• `{cid}` - *{info['name']}* (Stage: {info['rarity']})")
    
    if results:
        text = f"🔍 *SEARCH RESULTS FOR '{query.upper()}':*\n━━━━━━━━━━━━━━━━━━━━━━\n" + "\n".join(results)
    else:
        text = f"❌ '{query}' အမည်ဖြင့် Card မတွေ့ပါ။"
    await update.message.reply_text(text, parse_mode="Markdown")

# ================= SPAWN & GUESS HANDLERS =================
async def handle_group_spawns(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_chat or update.effective_chat.type == "private":
        return
    gp = db.get_group(update.effective_chat.id)
    gp["msg_count"] += 1
    
    if gp["msg_count"] >= gp["spawn_rate"]:
        gp["msg_count"] = 0
        card_ids = list(db.data["cards_master"].keys())
        if not card_ids: return
        chosen_id = random.choice(card_ids)
        c_info = db.data["cards_master"][chosen_id]
        
        gp["spawned_card"] = {
            "id": chosen_id,
            "name": c_info["name"].lower(),
            "time": time.time()
        }
        db.save_db()
        r_info = RARITY_STAGES.get(c_info["rarity"], {"name": "Common"})
        text = (
            f"🌟 *A WILD CARD HAS APPEARED!* 🌟\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"💎 *Rarity:* {r_info['name']}\n"
            f"📺 *Anime:* `{c_info.get('series', 'Anime')}`\n\n"
            f"🎯 ဖမ်းယူရန်: `/guess <character_name>` သို့မဟုတ် `/catch <name>`"
        )
        await update.message.reply_text(text, parse_mode="Markdown")

async def guess_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("💡 Usage: `/guess <character_name>`", parse_mode="Markdown")
        return
    gp = db.get_group(update.effective_chat.id)
    spawned = gp.get("spawned_card")
    if not spawned:
        await update.message.reply_text("❌ ဖမ်းယူရန် Card မရှိသေးပါ။ မက်ဆေ့ဂျ်များ ပို့၍ Drop စောင့်ပါ။")
        return
    
    user_guess = " ".join(context.args).lower().strip()
    if user_guess in spawned["name"]:
        cid = spawned["id"]
        c_info = db.data["cards_master"][cid]
        u = db.get_user(update.effective_user.id, update.effective_user.first_name)
        u["cards"].append({"id": cid, "print": random.randint(1, 100), "mint": 100})
        gp["spawned_card"] = None
        db.save_db()
        await update.message.reply_text(
            f"🎉 *CONGRATULATIONS {update.effective_user.first_name}!*\n━━━━━━━━━━━━━━━━━━━━━━\n"
            f"သင်သည် *{c_info['name']}* (ID: `{cid}`) ကို အောင်မြင်စွာ ဖမ်းယူလိုက်ပါပြီ။ 🎴",
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text("❌ အမည်မှားယွင်းနေပါသည်။ ထပ်မံ ကြိုးစားပါ။")

async def droptime_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    gp = db.get_group(update.effective_chat.id)
    rem_msg = gp["spawn_rate"] - gp["msg_count"]
    await update.message.reply_text(f"⏳ *NEXT DROP:* နောက်ထပ် မက်ဆေ့ဂျ် `{rem_msg}` စာကြောင်း လိုအပ်ပါသည်။", parse_mode="Markdown")

# ================= ECONOMY & MARKET HANDLERS =================
async def balance_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = db.get_user(update.effective_user.id, update.effective_user.first_name)
    await update.message.reply_text(f"💳 *{update.effective_user.first_name}* ၏ Wallet balance: 💰 `{u['coins']:,}` Coins", parse_mode="Markdown")

async def sellprice_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = "📊 *MARKET BASE PRICES*\n━━━━━━━━━━━━━━━━━━━━━━\n"
    for r, info in RARITY_STAGES.items():
        text += f"• Stage {r} ({info['name']}): 💰 `{info['price']:,}` Coins\n"
    await update.message.reply_text(text, parse_mode="Markdown")

async def market_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    m_data = db.data.get("market", {})
    if not m_data:
        await update.message.reply_text("🛍️ *GLOBAL MARKETPLACE*\n━━━━━━━━━━━━━━━━━━━━━━\nလက်ရှိ ရောင်းရန် တင်ထားသော Card မရှိပါ။", parse_mode="Markdown")
        return
    text = "🛍️ *GLOBAL MARKETPLACE LISTINGS*\n━━━━━━━━━━━━━━━━━━━━━━\n"
    for idx, (lid, item) in enumerate(m_data.items(), 1):
        c_info = db.data["cards_master"].get(item["card_id"], {"name": "Unknown"})
        text += f"▸ ID: `{lid}` | *{c_info['name']}* — 💰 `{item['price']:,}` Coins\n"
    await update.message.reply_text(text, parse_mode="Markdown")

async def sell_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2:
        await update.message.reply_text("💡 Usage: `/sell <card_id> <price>`", parse_mode="Markdown")
        return
    cid, price = context.args[0], int(context.args[1])
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
    await update.message.reply_text(f"✅ Card `{cid}` အား Marketplace သို့ ID `{lid}` ဖြင့် 💰 `{price:,}` Coins သတ်မှတ်၍ တင်လိုက်ပါပြီ။", parse_mode="Markdown")

async def buy_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("💡 Usage: `/buy <listing_id>`", parse_mode="Markdown")
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
    buyer["cards"].append({"id": item["card_id"], "print": 1, "mint": 100})
    del db.data["market"][lid]
    db.save_db()
    await update.message.reply_text(f"🎉 Listing `{lid}` အား 💰 `{item['price']:,}` Coins ဖြင့် အောင်မြင်စွာ ဝယ်ယူလိုက်ပါပြီ။", parse_mode="Markdown")

async def pay_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 1 or not update.message.reply_to_message:
        await update.message.reply_text("💡 Usage: Target မက်ဆေ့ဂျ်ကို Reply ပြန်၍ `/pay <amount>` ဟု ရိုက်ပါ။", parse_mode="Markdown")
        return
    amt = int(context.args[0])
    target = update.message.reply_to_message.from_user
    u1 = db.get_user(update.effective_user.id)
    if u1["coins"] < amt:
        await update.message.reply_text("❌ Coin မလုံလောက်ပါ။")
        return
    u2 = db.get_user(target.id, target.first_name)
    u1["coins"] -= amt
    u2["coins"] += amt
    db.save_db()
    await update.message.reply_text(f"💸 *{update.effective_user.first_name}* မှ *{target.first_name}* ထံ 💰 `{amt:,}` Coins လွှဲပေးလိုက်ပါပြီ။", parse_mode="Markdown")

async def trade_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.reply_to_message:
        await update.message.reply_text("💡 Trade ပြုလုပ်ရန် Message ကို Reply ပြန်၍ `/trade` ဟု ရိုက်ပါ။")
        return
    sender = update.effective_user
    receiver = update.message.reply_to_message.from_user
    trade_id = str(random.randint(1000, 9999))
    
    await update.message.reply_text(
        f"🤝 *TRADE SESSION STARTED*\n━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👥 *Traders:* {sender.first_name} 🤝 {receiver.first_name}\n\n"
        f"အတည်ပြုရန် အောက်ပါ Confirm ကို နှိပ်ပါ။",
        reply_markup=get_trade_keyboard(trade_id), parse_mode="Markdown"
    )

async def gift_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args or not update.message.reply_to_message:
        await update.message.reply_text("💡 Usage: Message ကို Reply ပြန်၍ `/gift <card_id>` ဟု ရိုက်ပါ။")
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

# ================= BATTLE & GAME HANDLERS =================
async def duel_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.reply_to_message:
        await update.message.reply_text("💡 Duel စိန်ခေါ်ရန် Player ၏ Message ကို Reply ပြန်၍ `/duel` ဟု ရိုက်ပါ။")
        return
    p1 = update.effective_user
    p2 = update.message.reply_to_message.from_user
    u1, u2 = db.get_user(p1.id, p1.first_name), db.get_user(p2.id, p2.first_name)
    if not u1["cards"] or not u2["cards"]:
        await update.message.reply_text("❌ Battle ပြုလုပ်ရန် နှစ်ဦးစလုံးတွင် Card ရှိရပါမည်။")
        return
    
    winner = random.choice([p1, p2])
    db.get_user(winner.id)["coins"] += 200
    db.save_db()
    await update.message.reply_text(
        f"⚔️ *ARENA BATTLE RESULTS* ⚔️\n━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🥊 *{p1.first_name}* VS *{p2.first_name}*\n\n"
        f"🏆 *WINNER:* *{winner.first_name}*\n"
        f"🎁 *Prize:* 💰 `200` Coins", parse_mode="Markdown"
    )

async def gacha_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = db.get_user(update.effective_user.id, update.effective_user.first_name)
    if u["coins"] < 1000:
        await update.message.reply_text("❌ Gacha Roll နှိုက်ရန် Coins `1,000` လိုအပ်ပါသည်။")
        return
    u["coins"] -= 1000
    c_ids = list(db.data["cards_master"].keys())
    got_id = random.choice(c_ids)
    u["cards"].append({"id": got_id, "print": random.randint(1, 50), "mint": 100})
    db.save_db()
    c_info = db.data["cards_master"][got_id]
    await update.message.reply_text(
        f"🎰 *GACHA LUCKY ROLL!*\n━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🎉 ရရှိလိုက်သော Card: *{c_info['name']}*\n"
        f"🆔 *Card ID:* `{got_id}`", parse_mode="Markdown"
    )

async def top_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    users = list(db.data["users"].items())
    users.sort(key=lambda x: x[1].get("coins", 0), reverse=True)
    text = "🏆 *NEXUS TOP LEADERBOARD* 🏆\n━━━━━━━━━━━━━━━━━━━━━━\n"
    for idx, (uid, uinfo) in enumerate(users[:10], 1):
        text += f"{idx}. *{uinfo.get('name', 'Player')}* — 💰 `{uinfo.get('coins', 0):,}` Coins\n"
    text += "━━━━━━━━━━━━━━━━━━━━━━"
    await update.message.reply_text(text, parse_mode="Markdown")

# ================= ADMIN HANDLERS =================
async def approvegroup_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not db.is_admin_or_owner(update.effective_user.id): return
    try:
        gid = int(context.args[0])
        gp = db.get_group(gid)
        gp["approved"] = True
        db.save_db()
        await update.message.reply_text(f"✅ Group `{gid}` အား Approve ပေးလိုက်ပါပြီ။", parse_mode="Markdown")
    except Exception:
        await update.message.reply_text("💡 Usage: `/approvegroup <group_id>`")

async def addcard_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not db.is_admin_or_owner(update.effective_user.id): return
    try:
        cid, rarity, series, *name_parts = context.args
        cname = " ".join(name_parts)
        db.data["cards_master"][cid] = {
            "name": cname, "rarity": int(rarity), "series": series,
            "atk": 500, "def": 500, "hp": 1500
        }
        db.save_db()
        await update.message.reply_text(f"✅ Card အသစ် **{cname}** (ID: `{cid}`) ထည့်သွင်းပြီးပါပြီ။", parse_mode="Markdown")
    except Exception:
        await update.message.reply_text("💡 Usage: `/addcard <id> <rarity_num> <series> <card_name>`")

# ================= REGISTER ALL HANDLERS =================
def register_all_handlers(app):
    # User
    app.add_handler(CommandHandler(["start", "sratr"], start_cmd))
    app.add_handler(CommandHandler(["help", "Help"], help_cmd))
    app.add_handler(CommandHandler("profile", profile_cmd))
    
    # Cards
    app.add_handler(CommandHandler(["harem", "Hearm"], harem_cmd))
    app.add_handler(CommandHandler("claim", claim_cmd))
    app.add_handler(CommandHandler("daily", daily_cmd))
    app.add_handler(CommandHandler("fav", fav_cmd))
    app.add_handler(CommandHandler("unfav", unfav_cmd))
    app.add_handler(CommandHandler("burn", burn_cmd))
    app.add_handler(CommandHandler("search", search_cmd))
    
    # Spawn & Catch
    app.add_handler(CommandHandler(["guess", "catch"], guess_cmd))
    app.add_handler(CommandHandler("droptime", droptime_cmd))
    
    # Economy & Market
    app.add_handler(CommandHandler("balance", balance_cmd))
    app.add_handler(CommandHandler("sellprice", sellprice_cmd))
    app.add_handler(CommandHandler("market", market_cmd))
    app.add_handler(CommandHandler("sell", sell_cmd))
    app.add_handler(CommandHandler("buy", buy_cmd))
    app.add_handler(CommandHandler("pay", pay_cmd))
    app.add_handler(CommandHandler("trade", trade_cmd))
    app.add_handler(CommandHandler("gift", gift_cmd))
    
    # Battle & Leaderboards
    app.add_handler(CommandHandler("duel", duel_cmd))
    app.add_handler(CommandHandler("gacha", gacha_cmd))
    app.add_handler(CommandHandler(["top", "ctop", "ranking", "todaytop", "leaderboard"], top_cmd))
    
    # Admin
    app.add_handler(CommandHandler("approvegroup", approvegroup_cmd))
    app.add_handler(CommandHandler("addcard", addcard_cmd))
    
    # Group Messages (Auto Spawn Listener)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_group_spawns))
