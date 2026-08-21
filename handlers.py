import time
import random
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters, CallbackQueryHandler
from database import db
from config import RARITY_STAGES
from keyboards import get_start_keyboard, get_trade_keyboard

# ================= USER & PROFILE HANDLERS =================
async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    db.get_user(user.id, user.first_name)
    await update.message.reply_text(
        f"✨ **မင်္ဂလာပါ {user.first_name}!** ✨\n\n"
        f"🎮 **Nexus RPG Card Catch Bot** မှ နွေးထွေးစွာ ကြိုဆိုပါတယ်။\n"
        f"🏆 Group များတွင် စာတိုများ ပို့ရင်း Cards များကို ဖမ်းယူ၊ စုဆောင်း၊ တိုက်ခိုက် အရောင်းအဝယ် ပြုလုပ်နိုင်ပါသည်။\n\n"
        f"📖 Command များကြည့်ရန် `/help` ကို နှိပ်ပါ။",
        reply_markup=get_start_keyboard(), parse_mode="Markdown"
    )

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "📜 **Nexus RPG Card Bot Directory**\n"
        "━━━━━⬍⬍━━━━━\n"
        "🎴 **Cards & Collection**\n"
        "• `/harem` - မိမိ ပိုင်ဆိုင်သော ကဒ်များ\n"
        "• `/claim` - ၁၂ နာရီ ၁ ကြိမ် Free Card ယူရန်\n"
        "• `/daily` - နေ့စဉ် Coin 500 ယူရန်\n"
        "• `/fav <id>` / `/unfav <id>` - Favorite မှတ်ရန်\n"
        "• `/burn <id>` - မလိုချင်သော ကဒ် ဖျက်ဆီးရန်\n"
        "• `/search <name>` - ကဒ်များ ရှာရန်\n\n"
        "🎯 **Catching & Spawning**\n"
        "• `/guess <name>` (သို့) `/catch` - ပေါ်လာသော ကဒ် ဖမ်းရန်\n"
        "• `/droptime` - ကဒ် နောက်တစ်ကြိမ် ထွက်မည့် အချိန်\n\n"
        "💰 **Economy & Trade**\n"
        "• `/balance` - လက်ကျန် Coins စစ်ရန်\n"
        "• `/pay <user> <amount>` - Coin လွှဲပေးရန်\n"
        "• `/market` / `/sell` / `/buy` - Global Market\n"
        "• `/trade <user>` - Interactive Live Trade\n"
        "• `/gift <user> <card_id>` - Card လက်ဆောင်ပေးရန်\n\n"
        "⚔️ **Battle & Game**\n"
        "• `/duel <user>` - Card Stats ဖြင့် တိုက်ခိုက်ရန်\n"
        "• `/gacha` - Card ကံစမ်းမဲ နှိုက်ရန်\n"
        "• `/top` - Leaderboard Rank ဇယား\n"
        "━━━━━⬍⬍━━━━━"
    )
    await update.message.reply_text(text, parse_mode="Markdown")

async def profile_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = db.get_user(update.effective_user.id, update.effective_user.first_name)
    text = (
        f"👤 **{update.effective_user.first_name}'s Profile**\n"
        f"━━━━━⬍⬍━━━━━\n"
        f"🪙 **Coins:** `{u['coins']:,}`\n"
        f"🎴 **Total Cards:** `{len(u['cards'])}` Cards\n"
        f"⭐ **Favorites:** `{len(u.get('favorites', []))}` Cards\n"
        f"━━━━━⬍⬍━━━━━"
    )
    await update.message.reply_text(text, parse_mode="Markdown")

# ================= CARD MANAGEMENT HANDLERS =================
async def harem_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = db.get_user(update.effective_user.id, update.effective_user.first_name)
    cards = u["cards"]
    if not cards:
        await update.message.reply_text("🎴 သင့်ထံတွင် မမည်သည့် Card မျှ မရှိသေးပါ။ `/claim` ကို သုံး၍ ယူပါ။")
        return
    text = f"🎴 **{update.effective_user.first_name}'s Collection ({len(cards)} Cards):**\n\n"
    for idx, c in enumerate(cards, 1):
        m = db.data["cards_master"].get(c["id"], {"name": "Unknown", "rarity": 1})
        r_info = RARITY_STAGES.get(m["rarity"], {"name": "Common"})
        is_fav = "⭐ " if c["id"] in u.get("favorites", []) else ""
        text += f"{idx}. {is_fav}`{c['id']}` | **{m['name']}** [{r_info['name']}]\n"
    await update.message.reply_text(text, parse_mode="Markdown")

async def claim_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = db.get_user(update.effective_user.id, update.effective_user.first_name)
    now = time.time()
    if now - u.get("last_claim", 0) < 43200:
        rem = int((43200 - (now - u["last_claim"])) // 3600)
        await update.message.reply_text(f"⏱️ Claim ပြုလုပ်ရန် `{rem}` နာရီ လိုသေးပါသည်။")
        return
    card_ids = list(db.data["cards_master"].keys())
    got_id = random.choice(card_ids)
    u["cards"].append({"id": got_id, "print": random.randint(1, 500), "mint": 100})
    u["last_claim"] = now
    db.save_db()
    c_info = db.data["cards_master"][got_id]
    await update.message.reply_text(f"🎁 **Claim အောင်မြင်ပါသည်။**\n\n🎉 ရရှိသော ကဒ်: **{c_info['name']}** (ID: `{got_id}`)", parse_mode="Markdown")

async def daily_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = db.get_user(update.effective_user.id, update.effective_user.first_name)
    now = time.time()
    if now - u.get("last_daily", 0) < 86400:
        await update.message.reply_text("⏱️ Daily Reward ကို ၂၄ နာရီမှ ၁ ကြိမ်သာ ယူနိုင်ပါသည်။")
        return
    u["coins"] += 500
    u["last_daily"] = now
    db.save_db()
    await update.message.reply_text("🪙 **Daily Reward:** 💰 `500` Coins အောင်မြင်စွာ ရရှိပါသည်။")

async def fav_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: `/fav <card_id>`", parse_mode="Markdown")
        return
    cid = context.args[0]
    u = db.get_user(update.effective_user.id)
    if "favorites" not in u: u["favorites"] = []
    if cid not in u["favorites"]:
        u["favorites"].append(cid)
        db.save_db()
        await update.message.reply_text(f"⭐ Card `{cid}` အား Favorite စာရင်းသို့ ထည့်လိုက်ပါပြီ။", parse_mode="Markdown")

async def burn_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: `/burn <card_id>`", parse_mode="Markdown")
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
    await update.message.reply_text(f"🔥 Card `{cid}` အား ဖျက်ဆီးလိုက်ပြီး 🪙 `300` Coins ပြန်လည်ရရှိပါသည်။", parse_mode="Markdown")

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
            f"✨ **A Wild Card Appeared!** ✨\n\n"
            f"🔮 **Rarity:** {r_info['name']}\n"
            f"📺 **Series:** `{c_info.get('series', 'Anime')}`\n\n"
            f"🎯 ဖမ်းယူရန် `/guess <character_name>` သို့မဟုတ် `/catch <name>` ဟု ရိုက်ပါ!"
        )
        await update.message.reply_text(text, parse_mode="Markdown")

async def guess_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: `/guess <character_name>`", parse_mode="Markdown")
        return
    gp = db.get_group(update.effective_chat.id)
    spawned = gp.get("spawned_card")
    if not spawned:
        await update.message.reply_text("❌ လက်ရှိ ဖမ်းယူရန် Card ပေါ်မနေပါ။")
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
            f"🎉 **Congratulations {update.effective_user.first_name}!**\n\n"
            f"သင်သည် **{c_info['name']}** (ID: `{cid}`) ကို အောင်မြင်စွာ ဖမ်းယူနိုင်ခဲ့ပါသည်။ 🎴",
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text("❌ မှားယွင်းနေပါသည်။ ထပ်မံ ကြိုးစားကြည့်ပါ။")

async def droptime_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    gp = db.get_group(update.effective_chat.id)
    rem_msg = gp["spawn_rate"] - gp["msg_count"]
    await update.message.reply_text(f"⏳ **Next Spawn:** နောက်ထပ် မက်ဆေ့ဂျ် `{rem_msg}` စာကြောင်း ပို့ပြီးပါက Card ပေါ်လာပါမည်။", parse_mode="Markdown")

# ================= ECONOMY & TRADE HANDLERS =================
async def balance_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = db.get_user(update.effective_user.id, update.effective_user.first_name)
    await update.message.reply_text(f"💰 **{update.effective_user.first_name}** ၏ လက်ကျန်ငွေ: `{u['coins']:,}` Coins", parse_mode="Markdown")

async def pay_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 1 or not update.message.reply_to_message:
        await update.message.reply_text("Usage: Message ကို Reply ပြန်၍ `/pay <amount>` ဟု ရိုက်ပါ။", parse_mode="Markdown")
        return
    amt = int(context.args[0])
    target = update.message.reply_to_message.from_user
    u1 = db.get_user(update.effective_user.id)
    if u1["coins"] < amt:
        await update.message.reply_text("❌ လက်ကျန် Coin မလုံလောက်ပါ။")
        return
    u2 = db.get_user(target.id, target.first_name)
    u1["coins"] -= amt
    u2["coins"] += amt
    db.save_db()
    await update.message.reply_text(f"💸 **{update.effective_user.first_name}** မှ **{target.first_name}** ထံ 💰 `{amt:,}` Coins လွှဲပေးလိုက်ပါပြီ။", parse_mode="Markdown")

async def trade_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.reply_to_message:
        await update.message.reply_text("❌ Trade လုပ်ချင်သော သူ၏ Message ကို Reply လုပ်၍ `/trade` ဟု ရိုက်ပါ။")
        return
    sender = update.effective_user
    receiver = update.message.reply_to_message.from_user
    trade_id = str(random.randint(1000, 9999))
    
    await update.message.reply_text(
        f"🤝 **Trade Session Started!**\n\n"
        f"👥 **Participants:** {sender.first_name} 🤝 {receiver.first_name}\n"
        f"အတည်ပြုရန် Confirm ကို နှိပ်ပါ။",
        reply_markup=get_trade_keyboard(trade_id), parse_mode="Markdown"
    )

async def gift_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args or not update.message.reply_to_message:
        await update.message.reply_text("Usage: Message ကို Reply ပြီး `/gift <card_id>` ဟု ရိုက်ပါ။")
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
    await update.message.reply_text(f"🎁 **{update.effective_user.first_name}** မှ Card `{cid}` ကို **{target.first_name}** ထံ လက်ဆောင်ပေးလိုက်ပါပြီ!", parse_mode="Markdown")

# ================= BATTLE & GAME HANDLERS =================
async def duel_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.reply_to_message:
        await update.message.reply_text("⚔️ Duel စိန်ခေါ်ရန် Player ၏ Message ကို Reply ပြန်၍ `/duel` ဟု ရိုက်ပါ။")
        return
    p1 = update.effective_user
    p2 = update.message.reply_to_message.from_user
    u1, u2 = db.get_user(p1.id, p1.first_name), db.get_user(p2.id, p2.first_name)
    if not u1["cards"] or not u2["cards"]:
        await update.message.reply_text("❌ နှစ်ဖက်စလုံးတွင် Card အနည်းဆုံး ၁ ခု စီ ရှိရပါမည်။")
        return
    
    winner = random.choice([p1, p2])
    db.get_user(winner.id)["coins"] += 200
    db.save_db()
    await update.message.reply_text(
        f"⚔️ **Card Battle Duel Results!** ⚔️\n\n"
        f"🥊 {p1.first_name} VS {p2.first_name}\n\n"
        f"🏆 **Winner:** **{winner.first_name}** 🎉\n"
        f"💰 **Reward:** `200` Coins", parse_mode="Markdown"
    )

async def gacha_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = db.get_user(update.effective_user.id, update.effective_user.first_name)
    if u["coins"] < 1000:
        await update.message.reply_text("❌ Gacha နှိုက်ရန် Coins `1,000` လိုအပ်ပါသည်။")
        return
    u["coins"] -= 1000
    c_ids = list(db.data["cards_master"].keys())
    got_id = random.choice(c_ids)
    u["cards"].append({"id": got_id, "print": random.randint(1, 50), "mint": 100})
    db.save_db()
    c_info = db.data["cards_master"][got_id]
    await update.message.reply_text(f"🎰 **Gacha Roll Result!**\n\n🎉 သင် ရရှိလိုက်သော ကဒ်: **{c_info['name']}** (ID: `{got_id}`)", parse_mode="Markdown")

async def top_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    users = list(db.data["users"].items())
    users.sort(key=lambda x: x[1].get("coins", 0), reverse=True)
    text = "🏆 **Nexus Top Coin Leaderboard** 🏆\n\n"
    for idx, (uid, uinfo) in enumerate(users[:10], 1):
        text += f"{idx}. **{uinfo.get('name', 'User')}** — 💰 `{uinfo.get('coins', 0):,}` Coins\n"
    await update.message.reply_text(text, parse_mode="Markdown")

# ================= ADMIN HANDLERS =================
async def approvegroup_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not db.is_admin_or_owner(update.effective_user.id): return
    try:
        gid = int(context.args[0])
        gp = db.get_group(gid)
        gp["approved"] = True
        db.save_db()
        await update.message.reply_text(f"✅ Group `{gid}` အား အသုံးပြုခွင့် Approve ပေးလိုက်ပါပြီ။", parse_mode="Markdown")
    except Exception:
        await update.message.reply_text("Usage: `/approvegroup <group_id>`")

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
        await update.message.reply_text("Usage: `/addcard <id> <rarity_num> <series> <card_name>`")

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
    app.add_handler(CommandHandler("burn", burn_cmd))
    
    # Spawn
    app.add_handler(CommandHandler(["guess", "catch"], guess_cmd))
    app.add_handler(CommandHandler("droptime", droptime_cmd))
    
    # Economy & Trade
    app.add_handler(CommandHandler("balance", balance_cmd))
    app.add_handler(CommandHandler("pay", pay_cmd))
    app.add_handler(CommandHandler("trade", trade_cmd))
    app.add_handler(CommandHandler("gift", gift_cmd))
    
    # Game & Battle
    app.add_handler(CommandHandler("duel", duel_cmd))
    app.add_handler(CommandHandler("gacha", gacha_cmd))
    app.add_handler(CommandHandler(["top", "leaderboard"], top_cmd))
    
    # Admin
    app.add_handler(CommandHandler("approvegroup", approvegroup_cmd))
    app.add_handler(CommandHandler("addcard", addcard_cmd))
    
    # Group Messages (Auto Spawn)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_group_spawns))
