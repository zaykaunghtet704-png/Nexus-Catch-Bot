import time
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes, CommandHandler, MessageHandler, CallbackQueryHandler, filters
)
from database import db

# ================= CONSTANTS & CONFIG =================
GROUP_LINK = "https://t.me/+00J7JktW8bJlZTY1"
CHANNEL_LINK = "https://t.me/+E6BxfAj0gaI2Y2Zl"
LOG_CHANNEL_ID = -1001234567890
OWNER_IDS = [7974865879]  # သင်၏ Telegram User ID ကို ဒီမှာထည့်ပါ

def is_owner(user_id: int) -> bool:
    return user_id in OWNER_IDS

def get_progress_bar(val, max_val=100, length=8):
    percent = min(max(val / max_val, 0), 1)
    filled = int(length * percent)
    return "▰" * filled + "▱" * (length - filled)

# Dynamic Multi-Language Helper (MM / EN)
TEXTS = {
    "MM": {
        "start": "✨ *WELCOME TO NEXUS CATCH RPG* ✨\n\n👋 မင်္ဂလာပါ {name}!\n🎮 Card များ စုဆောင်းပါ၊ Trade လုပ်ပါ၊ Arena တွင် စိန်ခေါ်လိုက်ပါ!",
        "must_join": "⚠️ *REQUIRED CHANNELS*\n\nBot ကို အသုံးပြုနိုင်ရန် အောက်ပါ Channel / Group ၂ ခုလုံးကို Join ပေးထားရန် လိုအပ်ပါသည်။",
        "no_card": "🎴 သင့်ထံတွင် Card မရှိသေးပါ။ `/claim` သို့မဟုတ် Group ထဲတွင် `/Nexus` ဖြင့် ဖမ်းယူပါ။",
        "lang_select": "🌐 *SELECT LANGUAGE / ဘာသာစကား ရွေးချယ်ပါ*",
        "lang_set": "🇲🇲 မြန်မာဘာသာသို့ အောင်မြင်စွာ ပြောင်းလဲလိုက်ပါပြီ။",
        "not_admin": "🚫 ဤ Command ကို Admin/Owner သာ အသုံးပြုနိုင်ပါသည်။"
    },
    "EN": {
        "start": "✨ *WELCOME TO NEXUS CATCH RPG* ✨\n\n👋 Welcome {name}!\n🎮 Collect cards, trade in market, and duel in arena!",
        "must_join": "⚠️ *REQUIRED CHANNELS*\n\nYou must join both channels below to access this bot.",
        "no_card": "🎴 You don't have any cards yet. Use `/claim` or catch with `/Nexus`!",
        "lang_select": "🌐 *SELECT PREFERRED LANGUAGE*",
        "lang_set": "🇬🇧 Language changed to English successfully.",
        "not_admin": "🚫 Only Admins/Owners can use this command."
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

# ================= 1. USER CORE & NAVIGATION =================
async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    db.get_user(user.id, user.first_name)
    
    caption = t(user.id, "start").format(name=user.first_name)
    keyboard = [
        [InlineKeyboardButton("🎴 My Vault", callback_data="harem_1"), InlineKeyboardButton("🌐 Language", callback_data="open_lang")],
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
            "📜 *USER COMMANDS (PAGE 1/3)*\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "👤 *USER SYSTEM*\n"
            "• `/start` — Start & Main Menu\n"
            "• `/help` — Command Directory\n"
            "• `/profile` — Player Profile & Statistics\n"
            "• `/lang` — Toggle Language (MM/EN)\n\n"
            "🎴 *COLLECTION & VAULT*\n"
            "• `/harem` — View Card Vault\n"
            "• `/claim` — Free 2 Cards (12h Cooldown)\n"
            "• `/daily` — Daily Free Coins\n"
            "• `/search <name>` — Find Cards\n"
            "• `/check <id>` — Inspect Card Info\n"
            "• `/fav <id>` / `/unfav <id>` — Bookmark Favorite\n"
            "• `/lock <id>` / `/unlock <id>` — Protect Card\n"
            "• `/hmode <id>` — Filter Vault View\n"
            "• `/reset` — Clear Vault Filter"
        ),
        2: (
            "📜 *GAMEPLAY & ECONOMY (PAGE 2/3)*\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "🎯 *CATCHING & ARENA*\n"
            "• `/Nexus <Name>` — Catch Spawned Card\n"
            "• `/duel` (Reply) — Challenge Player to Battle\n\n"
            "💰 *ECONOMY & TRADE*\n"
            "• `/balance` — Check Coin Balance\n"
            "• `/market` — Marketplace Listings\n"
            "• `/sell <id> <price>` — Put Card on Sale\n"
            "• `/buy <list_id>` — Buy Listed Card\n"
            "• `/delist <list_id>` — Cancel Sale\n"
            "• `/sellprice` — Official Price Guide\n"
            "• `/trade` (Reply) — Trade Card with Player\n"
            "• `/gift <id>` (Reply) — Send Free Card\n\n"
            "🏆 *LEADERBOARDS*\n"
            "• `/top` / `/rankings` — Global Rank\n"
            "• `/ctop` — Group Top Catchers\n"
            "• `/todayNexusCatch` — Daily Top Catchers"
        ),
        3: (
            "📜 *ADMIN & OWNER COMMANDS (PAGE 3/3)*\n━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "🛡️ *ADMIN PANEL*\n"
            "• `/approve` — Approve Group for Spawns\n"
            "• `/disapprove` — Disable Group Spawns\n"
            "• `/setspawn <number>` — Set Message Spawn Rate\n"
            "• `/force_spawn` — Force Spawn Card Immediately\n\n"
            "👑 *OWNER SYSTEM*\n"
            "• `/addcard <id> <rarity> <name>` — Add Card to DB\n"
            "• `/delcard <id>` — Remove Card from DB\n"
            "• `/givecoins <user_id> <amount>` — Add Coins\n"
            "• `/givecard <user_id> <card_id>` — Give Card\n"
            "• `/ban <user_id>` / `/unban <user_id>` — Ban System\n"
            "• `/broadcast <message>` — Send News to All"
        )
    }
    
    keyboard = []
    if page == 1:
        keyboard.append([InlineKeyboardButton("Next Page ➡️", callback_data="help_2")])
    elif page == 2:
        keyboard.append([InlineKeyboardButton("⬅️ Prev", callback_data="help_1"), InlineKeyboardButton("Next ➡️", callback_data="help_3")])
    else:
        keyboard.append([InlineKeyboardButton("⬅️ Prev Page", callback_data="help_2")])

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

    caption = (
        f"👑 *PLAYER PROFILE OVERVIEW* 👑\n━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 *Player:* `{user.first_name}`\n"
        f"🆔 *User ID:* `{user.id}`\n"
        f"🌐 *Global Rank:* `#{rank}`\n"
        f"🗣️ *Language:* `{u.get('lang', 'MM')}`\n\n"
        f"💰 *Wallet:* `{u['coins']:,}` Coins\n"
        f"🎴 *Total Cards:* `{len(u['cards'])}` Cards\n"
        f"🔒 *Locked:* `{len(u.get('locked', []))}` | ⭐ *Favs:* `{len(u.get('favorites', []))}`\n"
        f"━━━━━━━━━━━━━━━━━━━━━━"
    )
    await update.message.reply_text(caption, parse_mode="Markdown")

# ================= 2. VAULT & FAVORITES SYSTEM =================
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
        text += f"{is_lock}{is_fav}`{c['id']}` | *{m['name']}*\n"
    
    text += "━━━━━━━━━━━━━━━━━━━━━━"
    nav = []
    if page > 1: nav.append(InlineKeyboardButton("⬅️ Prev", callback_data=f"harem_{page-1}"))
    if page < total_pages: nav.append(InlineKeyboardButton("Next ➡️", callback_data=f"harem_{page+1}"))
    
    markup = InlineKeyboardMarkup([nav]) if nav else None
    if hasattr(update_or_query, "message") and update_or_query.message:
        await update_or_query.message.reply_text(text, reply_markup=markup, parse_mode="Markdown")
    else:
        await update_or_query.edit_message_text(text, reply_markup=markup, parse_mode="Markdown")

async def fav_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args: return await update.message.reply_text("💡 Usage: `/fav <card_id>`")
    cid = context.args[0]
    u = db.get_user(update.effective_user.id)
    if "favorites" not in u: u["favorites"] = []
    if cid not in u["favorites"]:
        u["favorites"].append(cid)
        db.save_db()
        await update.message.reply_text(f"⭐ Card `{cid}` ကို Favorite စာရင်းထဲ ထည့်လိုက်ပါပြီ။", parse_mode="Markdown")

async def unfav_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args: return await update.message.reply_text("💡 Usage: `/unfav <card_id>`")
    cid = context.args[0]
    u = db.get_user(update.effective_user.id)
    if "favorites" in u and cid in u["favorites"]:
        u["favorites"].remove(cid)
        db.save_db()
        await update.message.reply_text(f"❌ Card `{cid}` ကို Favorite မှ ပြန်ဖြုတ်လိုက်ပါပြီ။", parse_mode="Markdown")

async def hmode_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args: return await update.message.reply_text("💡 Usage: `/hmode <card_id>`")
    cid = context.args[0]
    u = db.get_user(update.effective_user.id)
    u["hmode_selected"] = cid
    db.save_db()
    await update.message.reply_text(f"🔍 Vault Filter အား Card `{cid}` သို့ သတ်မှတ်လိုက်ပါပြီ။ `/reset` ဖြင့် ပြန်ဖြုတ်နိုင်ပါသည်။", parse_mode="Markdown")

async def reset_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = db.get_user(update.effective_user.id)
    u["hmode_selected"] = None
    db.save_db()
    await update.message.reply_text("🔄 Vault Filter များကို ပြန်လည် Reset လုပ်ပြီးပါပြီ။")

async def lock_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args: return await update.message.reply_text("💡 Usage: `/lock <card_id>`")
    cid = context.args[0]
    u = db.get_user(update.effective_user.id)
    if "locked" not in u: u["locked"] = []
    if cid not in u["locked"]:
        u["locked"].append(cid)
        db.save_db()
        await update.message.reply_text(f"🔒 Card `{cid}` အား Lock ခတ်လိုက်ပါပြီ။", parse_mode="Markdown")

async def unlock_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args: return await update.message.reply_text("💡 Usage: `/unlock <card_id>`")
    cid = context.args[0]
    u = db.get_user(update.effective_user.id)
    if "locked" in u and cid in u["locked"]:
        u["locked"].remove(cid)
        db.save_db()
        await update.message.reply_text(f"🔓 Card `{cid}` အား Unlock ပြန်ဖြုတ်လိုက်ပါပြီ။", parse_mode="Markdown")

# ================= 3. GAMEPLAY, ARENA & TRADE =================
async def duel_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.reply_to_message:
        return await update.message.reply_text("💡 စိန်ခေါ်လိုသော ကစားသမား၏ Message ကို Reply ပြန်ပြီး `/duel` ဟု ရိုက်ပါ။")
    
    p1 = update.effective_user
    p2 = update.message.reply_to_message.from_user
    if p1.id == p2.id: return await update.message.reply_text("❌ မိမိကိုယ်ကို Duel ခေါ်၍ မရပါ။")
    
    u1, u2 = db.get_user(p1.id), db.get_user(p2.id)
    if not u1.get("cards") or not u2.get("cards"):
        return await update.message.reply_text("❌ Duel ယှဉ်ပြိုင်ရန် နှစ်ဦးလုံးထံတွင် Card အနည်းဆုံး ၁ ခုရှိရပါမည်။")

    winner = random.choice([p1, p2])
    await update.message.reply_text(
        f"⚔️ *ARENA DUEL BATTLE* ⚔️\n━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🔴 *{p1.first_name}* VS 🔵 *{p2.first_name}*\n\n"
        f"🎉 တိုက်ပွဲတွင် *{winner.first_name}* မှ အနိုင်ရရှိသွားပါသည်။ 🏆", parse_mode="Markdown"
    )

async def trade_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.reply_to_message or len(context.args) < 2:
        return await update.message.reply_text("💡 Usage: Message ကို Reply ပြန်၍ `/trade <Give_Card_ID> <Take_Card_ID>`")
    
    p1 = update.effective_user
    p2 = update.message.reply_to_message.from_user
    give_cid, take_cid = context.args[0], context.args[1]
    
    u1, u2 = db.get_user(p1.id), db.get_user(p2.id)
    c1 = next((c for c in u1["cards"] if c["id"] == give_cid), None)
    c2 = next((c for c in u2["cards"] if c["id"] == take_cid), None)

    if not c1 or not c2: return await update.message.reply_text("❌ Card များ လဲလှယ်ရန် သက်ဆိုင်ရာ Player ထံတွင် မရှိပါ။")
    if give_cid in u1.get("locked", []) or take_cid in u2.get("locked", []):
        return await update.message.reply_text("❌ Lock ခတ်ထားသော Card များကို Trade လုပ်၍ မရပါ။")

    u1["cards"].remove(c1); u2["cards"].append(c1)
    u2["cards"].remove(c2); u1["cards"].append(c2)
    db.save_db()
    await update.message.reply_text(f"🤝 *TRADE SUCCESSFUL!*\n*{p1.first_name}* နှင့် *{p2.first_name}* တို့ Card လဲလှယ်မှု အောင်မြင်ပါသည်။", parse_mode="Markdown")

async def sellprice_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "📊 *OFFICIAL CARD TIER PRICE GUIDE*\n━━━━━━━━━━━━━━━━━━━━━━\n"
        "• Tier 1 (Common): 💰 `500 - 1,500` Coins\n"
        "• Tier 2 (Rare): 💰 `2,000 - 5,000` Coins\n"
        "• Tier 3 (Epic): 💰 `6,000 - 15,000` Coins\n"
        "• Tier 4 (Legendary): 💰 `20,000+` Coins\n━━━━━━━━━━━━━━━━━━━━━━"
    )
    await update.message.reply_text(text, parse_mode="Markdown")

# ================= 4. ADMIN & OWNER COMMANDS =================
async def approve_group_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id): return await update.message.reply_text(t(update.effective_user.id, "not_admin"))
    gp = db.get_group(update.effective_chat.id)
    gp["approved"] = True
    db.save_db()
    await update.message.reply_text("✅ ဤ Group အား Card Spawn ရန် အတည်ပြု (Approve) လိုက်ပါပြီ။")

async def disapprove_group_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id): return await update.message.reply_text(t(update.effective_user.id, "not_admin"))
    gp = db.get_group(update.effective_chat.id)
    gp["approved"] = False
    db.save_db()
    await update.message.reply_text("❌ ဤ Group ၏ Card Spawn စနစ်ကို ပိတ်လိုက်ပါပြီ။")

async def setspawn_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id): return await update.message.reply_text(t(update.effective_user.id, "not_admin"))
    if not context.args: return await update.message.reply_text("💡 Usage: `/setspawn <msg_count>`")
    rate = int(context.args[0])
    gp = db.get_group(update.effective_chat.id)
    gp["spawn_rate"] = rate
    db.save_db()
    await update.message.reply_text(f"⚙️ Message Spawn Rate ကို `{rate}` စာစောင် ဟု သတ်မှတ်လိုက်ပါပြီ။", parse_mode="Markdown")

async def force_spawn_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id): return await update.message.reply_text(t(update.effective_user.id, "not_admin"))
    gp = db.get_group(update.effective_chat.id)
    card_ids = list(db.data["cards_master"].keys())
    if not card_ids: return await update.message.reply_text("❌ Card Database အလွတ်ဖြစ်နေပါသည်။")
    
    chosen_id = random.choice(card_ids)
    c_info = db.data["cards_master"][chosen_id]
    gp["spawned_card"] = {"id": chosen_id, "name": c_info["name"].lower()}
    db.save_db()
    await update.message.reply_text(f"🌟 *FORCE SPAWN SUCCESSFUL!*\n🎯 ဖမ်းယူရန်: `/Nexus <Card_Name>`", parse_mode="Markdown")

async def addcard_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id): return await update.message.reply_text(t(update.effective_user.id, "not_admin"))
    if len(context.args) < 3: return await update.message.reply_text("💡 Usage: `/addcard <id> <rarity> <card_name>`")
    cid, rarity, name = context.args[0], int(context.args[1]), " ".join(context.args[2:])
    db.data["cards_master"][cid] = {"name": name, "rarity": rarity}
    db.save_db()
    await update.message.reply_text(f"✅ Card ထည့်သွင်းပြီးပါပြီ: `{cid}` — *{name}* (Rarity: {rarity})", parse_mode="Markdown")

async def delcard_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id): return await update.message.reply_text(t(update.effective_user.id, "not_admin"))
    if not context.args: return await update.message.reply_text("💡 Usage: `/delcard <id>`")
    cid = context.args[0]
    if cid in db.data["cards_master"]:
        del db.data["cards_master"][cid]
        db.save_db()
        await update.message.reply_text(f"🗑️ Card `{cid}` အား Database မှ ဖျက်လိုက်ပါပြီ။", parse_mode="Markdown")

async def givecoins_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id): return await update.message.reply_text(t(update.effective_user.id, "not_admin"))
    if len(context.args) < 2: return await update.message.reply_text("💡 Usage: `/givecoins <user_id> <amount>`")
    uid, amount = int(context.args[0]), int(context.args[1])
    u = db.get_user(uid)
    u["coins"] += amount
    db.save_db()
    await update.message.reply_text(f"💰 User `{uid}` ထံသို့ Coins `{amount:,}` ထည့်ပေးလိုက်ပါပြီ။", parse_mode="Markdown")

async def givecard_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id): return await update.message.reply_text(t(update.effective_user.id, "not_admin"))
    if len(context.args) < 2: return await update.message.reply_text("💡 Usage: `/givecard <user_id> <card_id>`")
    uid, cid = int(context.args[0]), context.args[1]
    if cid not in db.data["cards_master"]: return await update.message.reply_text("❌ ထို Card ID မရှိပါ။")
    u = db.get_user(uid)
    u["cards"].append({"id": cid, "level": 1, "exp": 0})
    db.save_db()
    await update.message.reply_text(f"🎁 User `{uid}` ထံသို့ Card `{cid}` ထည့်ပေးလိုက်ပါပြီ။", parse_mode="Markdown")

async def ban_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id): return await update.message.reply_text(t(update.effective_user.id, "not_admin"))
    if not context.args: return await update.message.reply_text("💡 Usage: `/ban <user_id>`")
    uid = int(context.args[0])
    u = db.get_user(uid)
    u["is_banned"] = True
    db.save_db()
    await update.message.reply_text(f"🚫 User `{uid}` အား Ban လိုက်ပါပြီ။", parse_mode="Markdown")

async def unban_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id): return await update.message.reply_text(t(update.effective_user.id, "not_admin"))
    if not context.args: return await update.message.reply_text("💡 Usage: `/unban <user_id>`")
    uid = int(context.args[0])
    u = db.get_user(uid)
    u["is_banned"] = False
    db.save_db()
    await update.message.reply_text(f"✅ User `{uid}` အား Unban လိုက်ပါပြီ။", parse_mode="Markdown")

async def broadcast_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id): return await update.message.reply_text(t(update.effective_user.id, "not_admin"))
    if not context.args: return await update.message.reply_text("💡 Usage: `/broadcast <message>`")
    msg = " ".join(context.args)
    count = 0
    for uid in db.data["users"].keys():
        try:
            await context.bot.send_message(chat_id=int(uid), text=f"📢 *ANNOUNCEMENT*\n━━━━━━━━━━━━━━━━━━━━━━\n{msg}", parse_mode="Markdown")
            count += 1
        except Exception:
            continue
    await update.message.reply_text(f"📢 User ပေါင်း `{count}` ယောက်ထံသို့ စာပို့ပြီးပါပြီ။", parse_mode="Markdown")

# ================= 5. EXISTING MARKET & SPAWN IMPORTED =================
async def claim_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = db.get_user(update.effective_user.id, update.effective_user.first_name)
    now = time.time()
    if now - u.get("last_claim", 0) < 43200:
        rem = int((43200 - (now - u["last_claim"])) // 3600)
        return await update.message.reply_text(f"⏱️ Cooldown: `{rem}` နာရီ လိုသေးပါသည်။")
    
    card_ids = list(db.data["cards_master"].keys())
    if not card_ids: return await update.message.reply_text("❌ Card Database အလွတ်ဖြစ်နေပါသည်။")
    
    got_ids = random.sample(card_ids, min(2, len(card_ids)))
    for gid in got_ids: u["cards"].append({"id": gid, "level": 1, "exp": 0})
    u["last_claim"] = now
    db.save_db()
    await update.message.reply_text(f"🎁 Free 2 Cards အောင်မြင်စွာ ရရှိပါပြီ!", parse_mode="Markdown")

async def daily_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = db.get_user(update.effective_user.id)
    now = time.time()
    if now - u.get("last_daily", 0) < 86400: return await update.message.reply_text("⏱️ Daily Rewards ကို ၂၄ နာရီမှ ၁ ကြိမ်သာ ယူနိုင်ပါသည်။")
    u["coins"] += 500; u["last_daily"] = now
    db.save_db()
    await update.message.reply_text("🪙 Daily Reward 💰 `500` Coins ရရှိပါသည်။", parse_mode="Markdown")

async def balance_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = db.get_user(update.effective_user.id)
    await update.message.reply_text(f"💳 Wallet Balance: 💰 `{u['coins']:,}` Coins", parse_mode="Markdown")

async def sell_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2: return await update.message.reply_text("💡 Usage: `/sell [char_id] [price]`")
    cid, price = context.args[0], int(context.args[1])
    u = db.get_user(update.effective_user.id)
    card = next((c for c in u["cards"] if c["id"] == cid), None)
    if not card: return await update.message.reply_text("❌ Card သင့်ထံတွင် မရှိပါ။")
    u["cards"].remove(card)
    lid = str(random.randint(1000, 9999))
    if "market" not in db.data: db.data["market"] = {}
    db.data["market"][lid] = {"seller_id": update.effective_user.id, "card_id": cid, "price": price}
    db.save_db()
    await update.message.reply_text(f"✅ Market Listing ID `{lid}` ဖြင့် ရောင်းချလိုက်ပါပြီ။", parse_mode="Markdown")

async def market_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    m_data = db.data.get("market", {})
    if not m_data: return await update.message.reply_text("🛍️ Market အလွတ်ဖြစ်နေပါသည်။")
    text = "🛍️ *GLOBAL MARKETPLACE*\n━━━━━━━━━━━━━━━━━━━━━━\n"
    for lid, item in list(m_data.items())[:10]:
        c_info = db.data["cards_master"].get(item["card_id"], {"name": "Unknown"})
        text += f"▸ ID: `{lid}` | *{c_info['name']}* — 💰 `{item['price']:,}` Coins\n"
    await update.message.reply_text(text, parse_mode="Markdown")

async def buy_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args: return await update.message.reply_text("💡 Usage: `/buy [listing_id]`")
    lid = context.args[0]
    item = db.data.get("market", {}).get(lid)
    if not item: return await update.message.reply_text("❌ Listing မရှိပါ။")
    buyer = db.get_user(update.effective_user.id)
    if buyer["coins"] < item["price"]: return await update.message.reply_text("❌ Coins မလုံလောက်ပါ။")
    buyer["coins"] -= item["price"]
    seller = db.get_user(item["seller_id"])
    seller["coins"] += item["price"]
    buyer["cards"].append({"id": item["card_id"], "level": 1, "exp": 0})
    del db.data["market"][lid]
    db.save_db()
    await update.message.reply_text(f"🎉 Listing `{lid}` အား ဝယ်ယူလိုက်ပါပြီ။", parse_mode="Markdown")

async def delist_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args: return await update.message.reply_text("💡 Usage: `/delist [listing_id]`")
    lid = context.args[0]
    item = db.data.get("market", {}).get(lid)
    if not item or item["seller_id"] != update.effective_user.id: return await update.message.reply_text("❌ သင့် Listing မဟုတ်ပါ။")
    u = db.get_user(update.effective_user.id)
    u["cards"].append({"id": item["card_id"], "level": 1, "exp": 0})
    del db.data["market"][lid]
    db.save_db()
    await update.message.reply_text(f"✅ Listing `{lid}` အား ပြန်ဖြုတ်လိုက်ပါပြီ။")

async def gift_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args or not update.message.reply_to_message: return await update.message.reply_text("💡 Reply ပြီး `/gift <CHAR_ID>` ရိုက်ပါ။")
    cid = context.args[0]
    target = update.message.reply_to_message.from_user
    u1 = db.get_user(update.effective_user.id)
    card = next((c for c in u1["cards"] if c["id"] == cid), None)
    if not card: return await update.message.reply_text("❌ Card မရှိပါ။")
    u1["cards"].remove(card)
    u2 = db.get_user(target.id, target.first_name)
    u2["cards"].append(card)
    db.save_db()
    await update.message.reply_text(f"🎁 Card `{cid}` အား *{target.first_name}* ထံ လက်ဆောင်ပေးလိုက်ပါပြီ!", parse_mode="Markdown")

async def search_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = " ".join(context.args).lower() if context.args else ""
    results = [f"• `{cid}` — *{info['name']}*" for cid, info in db.data["cards_master"].items() if not query or query in info["name"].lower()]
    if not results: return await update.message.reply_text("❌ မည်သည့် Card မှ ရှာမတွေ့ပါ။")
    await update.message.reply_text(f"🔍 *CARDS FOUND ({len(results)}):*\n" + "\n".join(results[:12]), parse_mode="Markdown")

async def check_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args: return await update.message.reply_text("💡 Usage: `/check <card_id>`")
    cid = context.args[0]
    info = db.data["cards_master"].get(cid)
    if not info: return await update.message.reply_text("❌ Card ID မရှိပါ။")
    await update.message.reply_text(f"🎴 *CARD INFO*\n🆔 `{cid}` | Name: *{info['name']}*", parse_mode="Markdown")

async def handle_group_spawns(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_chat or update.effective_chat.type == "private": return
    gp = db.get_group(update.effective_chat.id)
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
        await update.message.reply_text("🌟 *A WILD CARD HAS APPEARED!*\n🎯 `/Nexus <Card_Name>`", parse_mode="Markdown")

async def nexus_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args: return
    gp = db.get_group(update.effective_chat.id)
    spawned = gp.get("spawned_card")
    if not spawned: return await update.message.reply_text("❌ ဖမ်းယူရန် Card မရှိသေးပါ။")
    if " ".join(context.args).lower().strip() == spawned["name"]:
        cid = spawned["id"]
        c_info = db.data["cards_master"][cid]
        u = db.get_user(update.effective_user.id, update.effective_user.first_name)
        u["cards"].append({"id": cid, "level": 1, "exp": 0})
        gp["spawned_card"] = None
        db.save_db()
        await update.message.reply_text(f"🎉 *{update.effective_user.first_name}* မှ *{c_info['name']}* ကို ဖမ်းယူလိုက်ပါပြီ။ 🎴", parse_mode="Markdown")

async def top_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    users = sorted(db.data["users"].items(), key=lambda x: len(x[1].get("cards", [])), reverse=True)
    text = "🏆 *GLOBAL TOP COLLECTORS*\n━━━━━━━━━━━━━━━━━━━━━━\n"
    for idx, (uid, uinfo) in enumerate(users[:10], 1):
        text += f"{idx}. *{uinfo.get('name', 'User')}* — 🎴 `{len(uinfo.get('cards', []))}` Cards\n"
    await update.message.reply_text(text, parse_mode="Markdown")

async def ctop_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == "private": return
    gp = db.get_group(update.effective_chat.id)
    sorted_c = sorted(gp.get("top_catchers", {}).items(), key=lambda x: x[1], reverse=True)
    text = "🏆 *GROUP TOP CATCHERS*\n━━━━━━━━━━━━━━━━━━━━━━\n"
    for idx, (uid, count) in enumerate(sorted_c[:10], 1):
        text += f"{idx}. *User {uid}* — 🎯 `{count}` Catches\n"
    await update.message.reply_text(text, parse_mode="Markdown")

async def today_nexus_catch_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    users = sorted(db.data["users"].items(), key=lambda x: x[1].get("today_catches", 0), reverse=True)
    text = "🔥 *TODAY TOP CATCHERS*\n━━━━━━━━━━━━━━━━━━━━━━\n"
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
        keyboard = [[InlineKeyboardButton("🇲🇲 မြန်မာစာ", callback_data="set_lang_MM"), InlineKeyboardButton("🇬🇧 English", callback_data="set_lang_EN")]]
        await query.message.edit_text(t(user.id, "lang_select"), reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
    elif data.startswith("set_lang_"):
        lang_code = data.split("_")[2]
        u = db.get_user(user.id)
        u["lang"] = lang_code
        db.save_db()
        await query.answer("✅ Language Updated!")
        await query.message.edit_text(t(user.id, "lang_set"), parse_mode="Markdown")
    elif data.startswith("harem_"):
        await harem_page(query, context, int(data.split("_")[1]))
    elif data.startswith("help_"):
        await help_page(query, context, int(data.split("_")[1]))

# ================= REGISTER ALL HANDLERS =================
def register_all_handlers(app):
    # Core User Commands
    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("profile", profile_cmd))
    app.add_handler(CommandHandler("lang", lang_cmd))
    
    # Vault & Favorites Commands
    app.add_handler(CommandHandler("harem", harem_cmd))
    app.add_handler(CommandHandler("fav", fav_cmd))
    app.add_handler(CommandHandler("unfav", unfav_cmd))
    app.add_handler(CommandHandler("hmode", hmode_cmd))
    app.add_handler(CommandHandler("reset", reset_cmd))
    app.add_handler(CommandHandler("lock", lock_cmd))
    app.add_handler(CommandHandler("unlock", unlock_cmd))
    app.add_handler(CommandHandler("search", search_cmd))
    app.add_handler(CommandHandler("check", check_cmd))
    
    # Economy & Trade Commands
    app.add_handler(CommandHandler("claim", claim_cmd))
    app.add_handler(CommandHandler("daily", daily_cmd))
    app.add_handler(CommandHandler("balance", balance_cmd))
    app.add_handler(CommandHandler("sell", sell_cmd))
    app.add_handler(CommandHandler("buy", buy_cmd))
    app.add_handler(CommandHandler("market", market_cmd))
    app.add_handler(CommandHandler("delist", delist_cmd))
    app.add_handler(CommandHandler("sellprice", sellprice_cmd))
    app.add_handler(CommandHandler("gift", gift_cmd))
    app.add_handler(CommandHandler("trade", trade_cmd))
    
    # Gameplay & Rankings
    app.add_handler(CommandHandler("duel", duel_cmd))
    app.add_handler(CommandHandler("Nexus", nexus_cmd))
    app.add_handler(CommandHandler(["top", "rankings"], top_cmd))
    app.add_handler(CommandHandler("ctop", ctop_cmd))
    app.add_handler(CommandHandler("todayNexusCatch", today_nexus_catch_cmd))
    
    # Admin & Owner Controls
    app.add_handler(CommandHandler("approve", approve_group_cmd))
    app.add_handler(CommandHandler("disapprove", disapprove_group_cmd))
    app.add_handler(CommandHandler("setspawn", setspawn_cmd))
    app.add_handler(CommandHandler("force_spawn", force_spawn_cmd))
    app.add_handler(CommandHandler("addcard", addcard_cmd))
    app.add_handler(CommandHandler("delcard", delcard_cmd))
    app.add_handler(CommandHandler("givecoins", givecoins_cmd))
    app.add_handler(CommandHandler("givecard", givecard_cmd))
    app.add_handler(CommandHandler("ban", ban_cmd))
    app.add_handler(CommandHandler("unban", unban_cmd))
    app.add_handler(CommandHandler("broadcast", broadcast_cmd))
    
    # Listeners
    app.add_handler(CallbackQueryHandler(callback_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_group_spawns))
