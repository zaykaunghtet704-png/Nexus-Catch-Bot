import time
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from database import db
from config import RARITY_STAGES

# ================= CONSTANTS & HELPER FUNCTIONS =================
CHANNEL_1_LINK = "https://t.me/+00J7JktW8bJlZTY1"  # Group
CHANNEL_2_LINK = "https://t.me/+E6BxfAj0gaI2Y2Zl"  # Channel
LOG_CHANNEL_ID = -1001234567890  # Bot Add ဖြစ်ပါက စာတက်မည့် Channel ID ထည့်ပါ

# Multi-language dictionary
TEXTS = {
    "MM": {
        "start": "✨ *WELCOME TO NEXUS CATCH BOT* ✨\n\n👋 မင်္ဂလာပါ {name}!\n🎮 Card များ ဖမ်းယူ၊ စုဆောင်း၊ ရောင်းဝယ်၊ Duel တိုက်ခိုက်နိုင်ပါပြီ။",
        "must_join": "⚠️ *အသုံးပြုရန် သတိပေးချက်*\n\nBot ကို အသုံးပြုနိုင်ရန် အောက်ပါ Channel/Group ၂ ခုလုံးကို Join ပေးထားရန် လိုအပ်ပါသည်။",
        "gp_not_approved": "❌ *Group အသုံးပြုခွင့် မရှိသေးပါ*\n\nဤ Bot ကို အသုံးပြုရန် Group တွင် လူဦးရေ အနည်းဆုံး ၅၀ ရှိရမည်ဖြစ်ပြီး Admin Access ပေးထားရပါမည်။ ထို့နောက် Owner မှ Approve ဖွင့်ပေးမှ သုံးနိုင်ပါမည်။",
        "no_card": "🎴 သင့်ထံတွင် မည်သည့် Card မျှ မရှိသေးပါ။",
        "lang_changed": "🇲🇲 မြန်မာဘာသာစကားသို့ ပြောင်းလဲလိုက်ပါပြီ။"
    },
    "EN": {
        "start": "✨ *WELCOME TO NEXUS CATCH BOT* ✨\n\n👋 Welcome {name}!\n🎮 Collect, trade, and battle with anime cards now.",
        "must_join": "⚠️ *REQUIRED CHANNELS*\n\nYou must join both channels below to use this bot's features.",
        "gp_not_approved": "❌ *GROUP NOT APPROVED*\n\nTo use this bot, this group must have at least 50 members, grant Bot Admin rights, and be approved by the Owner.",
        "no_card": "🎴 You don't have any cards yet.",
        "lang_changed": "🇬🇧 Language changed to English successfully."
    }
}

def get_txt(user_id, key):
    lang = db.get_user(user_id).get("lang", "MM")
    return TEXTS[lang].get(key, TEXTS["MM"][key])

async def check_joined(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """ User မန်ဘာ ဝင်ထားခြင်း ရှိမရှိ စစ်ဆေးသည့် Middleware """
    user_id = update.effective_user.id
    u = db.get_user(user_id)
    if u.get("is_verified", False):
        return True

    # Forced Join Keyboard
    keyboard = [
        [InlineKeyboardButton("💬 Join Group", url=CHANNEL_1_LINK), InlineKeyboardButton("📢 Join Channel", url=CHANNEL_2_LINK)],
        [InlineKeyboardButton("✅ Verified (ဝင်ပြီးပါပြီ)", callback_data="verify_join")]
    ]
    await update.message.reply_text(
        get_txt(user_id, "must_join"),
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )
    return False

# ================= START & HELP & PROFILE =================
async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    db.get_user(user.id, user.first_name)
    
    caption = get_txt(user.id, "start").format(name=user.first_name)
    keyboard = [
        [InlineKeyboardButton("🎴 My Waifu", callback_data="harem_1")],
        [InlineKeyboardButton("💬 Group", url=CHANNEL_1_LINK), InlineKeyboardButton("📢 Channel", url=CHANNEL_2_LINK)]
    ]
    
    # Start မှာ ပုံ အမြဲပါရန် Sample Image URL (မိမိ ကြိုက်နှစ်သက်ရာ Image Link ပြောင်းနိုင်သည်)
    img_url = "https://images.unsplash.com/photo-1578632767115-351597cf2477"
    await update.message.reply_photo(
        photo=img_url,
        caption=caption,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await help_page(update, context, page=1)

async def help_page(update_or_query, context, page=1):
    help_texts = {
        1: (
            "📖 *NEXUS CATCH BOT DIRECTORY (Page 1/2)*\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "▫️ `/start` - Start bot and main menu\n"
            "▫️ `/help` - View command listings\n"
            "▫️ `/profile` - View player stats & rank\n"
            "▫️ `/lang` - Switch language (MM / EN)\n\n"
            "🎴 *COLLECTION COMMANDS*\n"
            "▫️ `/harem` - View collected card deck\n"
            "▫️ `/claim` - Claim 2 free cards (12h Cooldown)\n"
            "▫️ `/daily` - Claim daily 500 Coins\n"
            "▫️ `/search` - Search all cards in bot\n"
            "▫️ `/check <id>` - Inspection of specific card\n"
            "▫️ `/fav <id>` / `/unfav <id>` - Set favorite card\n"
            "▫️ `/hmode` - Filter top 10 cards mode\n"
            "▫️ `/reset` - Clear hmode filter"
        ),
        2: (
            "📖 *NEXUS CATCH BOT DIRECTORY (Page 2/2)*\n"
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "🎯 *CATCHING & GAMEPLAY*\n"
            "▫️ `/Nexus <Card_Name>` - Catch spawned card\n"
            "▫️ `/changetime <gp_id> <msg_count>` - Set drop rate\n\n"
            "💰 *ECONOMY & TRADE*\n"
            "▫️ `/balance` - Check wallet balance\n"
            "▫️ `/market` - View marketplace listings\n"
            "▫️ `/sell <id> <price>` - List card for sale\n"
            "▫️ `/buy <list_id>` - Buy card from market\n"
            "▫️ `/delist <list_id>` - Remove market listing\n"
            "▫️ `/sellprice` - Base price tier chart\n"
            "▫️ `/trade` (Reply) - Initiate interactive trade\n"
            "▫️ `/gift <id>` (Reply) - Send card as gift\n\n"
            "🏆 *LEADERBOARDS & ARENA*\n"
            "▫️ `/duel` (Reply) - Battle another player\n"
            "▫️ `/upgrade <id>` - Level up card\n"
            "▫️ `/top` / `/rankings` - Global top 15 players\n"
            "▫️ `/ctop` - Group local top catchers\n"
            "▫️ `/todayNexusCatch` - Today's top catchers"
        )
    }
    
    keyboard = []
    if page == 1:
        keyboard.append([InlineKeyboardButton("Next Page ➡️", callback_data="help_2")])
    else:
        keyboard.append([InlineKeyboardButton("⬅️ Prev Page", callback_data="help_1")])

    markup = InlineKeyboardMarkup(keyboard)
    if hasattr(update_or_query, "message") and update_or_query.message:
        await update_or_query.message.reply_text(help_texts[page], reply_markup=markup, parse_mode="Markdown")
    else:
        await update_or_query.edit_message_text(help_texts[page], reply_markup=markup, parse_mode="Markdown")

async def profile_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    u = db.get_user(user.id, user.first_name)
    
    # Global Ranking Logic
    all_users = sorted(db.data["users"].items(), key=lambda x: len(x[1].get("cards", [])), reverse=True)
    rank = next((i for i, (uid, _) in enumerate(all_users, 1) if int(uid) == user.id), "N/A")

    photos = await context.bot.get_user_profile_photos(user.id, limit=1)
    
    caption = (
        f"👤 *PLAYER PROFILE & RULES STATUS*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🆔 *Name:* `{user.first_name}`\n"
        f"🌐 *Global Catch Rank:* #{rank}\n"
        f"💰 *Coins Balance:* `{u['coins']:,}`\n"
        f"🎴 *Total Cards:* `{len(u['cards'])}` Cards\n"
        f"⭐ *Favorites:* `{len(u.get('favorites', []))}` Cards\n"
        f"🔥 *Daily Claimed:* {'Yes' if time.time() - u.get('last_daily', 0) < 86400 else 'No'}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━"
    )
    
    if photos.total_count > 0:
        await update.message.reply_photo(photo=photos.photos[0][-1].file_id, caption=caption, parse_mode="Markdown")
    else:
        await update.message.reply_text(caption, parse_mode="Markdown")

# ================= COLLECTION (HAREM & SEARCH) =================
async def harem_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_joined(update, context): return
    await harem_page(update, context, page=1)

async def harem_page(update_or_query, context, page=1):
    user = update_or_query.effective_user
    u = db.get_user(user.id)
    cards = u.get("cards", [])

    if not cards:
        msg = get_txt(user.id, "no_card")
        if hasattr(update_or_query, "message") and update_or_query.message:
            await update_or_query.message.reply_text(msg)
        else:
            await update_or_query.edit_message_text(msg)
        return

    # Filter by hmode if active
    if u.get("hmode_selected"):
        cards = [c for c in cards if c["id"] == u["hmode_selected"]]

    per_page = 10
    total_pages = max(1, (len(cards) + per_page - 1) // per_page)
    start_idx = (page - 1) * per_page
    page_cards = cards[start_idx:start_idx + per_page]

    text = f"🎴 *{user.first_name}'s CARD VAULT (Page {page}/{total_pages})*\n━━━━━━━━━━━━━━━━━━━━━━\n"
    for idx, c in enumerate(page_cards, start_idx + 1):
        m = db.data["cards_master"].get(c["id"], {"name": "Unknown", "rarity": 1})
        is_fav = "⭐ " if c["id"] in u.get("favorites", []) else ""
        lvl = c.get("level", 1)
        text += f"{idx}. {is_fav}`{c['id']}` | *{m['name']}* (Lv.{lvl})\n"
    
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
            results.append(f"• `{cid}` - *{info['name']}*")

    if not results:
        await update.message.reply_text("❌ မည်သည့် Card မှ ရှာမတွေ့ပါ။")
        return

    text = f"🔍 *CARD SEARCH DIRECTORY ({len(results)} Found):*\n\n" + "\n".join(results[:15])
    keyboard = [[InlineKeyboardButton("💬 Channel", url=CHANNEL_2_LINK)]]
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

# ================= CLAIM & HMODE =================
async def claim_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = db.get_user(update.effective_user.id, update.effective_user.first_name)
    now = time.time()
    if now - u.get("last_claim", 0) < 43200:
        rem = int((43200 - (now - u["last_claim"])) // 3600)
        await update.message.reply_text(f"⏱️ Claim ပြုလုပ်ရန် `{rem}` နာရီ လိုသေးပါသည်။ (Cooldown: 12 Hours)")
        return
    
    card_ids = list(db.data["cards_master"].keys())
    got_ids = random.sample(card_ids, min(2, len(card_ids)))
    for gid in got_ids:
        u["cards"].append({"id": gid, "level": 1, "exp": 0})
    
    u["last_claim"] = now
    db.save_db()
    c_names = ", ".join([db.data["cards_master"][i]['name'] for i in got_ids])
    await update.message.reply_text(f"🎁 *CLAIM SUCCESSFUL (2 Cards)!*\n\n🎉 ရရှိသော ကဒ်များ: *{c_names}*", parse_mode="Markdown")

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
    
    await update.message.reply_text("🎯 HMode တွင် ပြသလိုသော ကဒ်ကို ရွေးချယ်ပါ:", reply_markup=InlineKeyboardMarkup(keyboard))

async def reset_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = db.get_user(update.effective_user.id)
    u["hmode_selected"] = None
    db.save_db()
    await update.message.reply_text("✅ Filter အားလုံးကို ပြန်လည် Reset ပြုလုပ်ပြီးပါပြီ။ Harem တွင် အားလုံး ပြန်မြင်ရပါမည်။")

# ================= LEADERBOARDS =================
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
    text = "🔥 *TODAY'S TOP CARD CATCHERS* 🔥\n━━━━━━━━━━━━━━━━━━━━━━\n"
    for idx, (uid, uinfo) in enumerate(users[:10], 1):
        text += f"{idx}. *{uinfo.get('name', 'User')}* — 🎴 `{uinfo.get('today_catches', 0)}` Cards\n"
    await update.message.reply_text(text, parse_mode="Markdown")

# ================= GROUP SPAWN & APPROVAL MIDDLEWARE =================
async def handle_group_spawns(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_chat or update.effective_chat.type == "private":
        return
    
    chat_id = update.effective_chat.id
    gp = db.get_group(chat_id)
    
    # Check Approval & Member Limit Status
    if not gp.get("approved", False):
        return  # Approve မလုပ်ထားပါက Spawns အလုပ်မလုပ်ပါ
    
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
            f"✨ *A WILD CARD HAS APPEARED!* ✨\n\n"
            f"🎴 Name: ???\n"
            f"🎯 ဖမ်းယူရန်: `/Nexus <Card_Name>` ဟု ရိုက်ပါ!", parse_mode="Markdown"
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
        
        # Track Group Top
        gp["top_catchers"] = gp.get("top_catchers", {})
        gp["top_catchers"][str(user.id)] = gp["top_catchers"].get(str(user.id), 0) + 1
        gp["spawned_card"] = None
        db.save_db()
        
        await update.message.reply_text(f"🎉 *CONGRATULATIONS {update.effective_user.first_name}!*\nသင်သည် *{c_info['name']}* (`{cid}`) အား ဖမ်းယူလိုက်ပါပြီ။", parse_mode="Markdown")

# ================= BOT ADDED TO GROUP EVENT (AUTO LOG) =================
async def bot_added_to_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    for member in update.message.new_chat_members:
        if member.id == context.bot.id:
            chat = update.effective_chat
            user = update.effective_user
            count = await context.bot.get_chat_member_count(chat.id)
            
            # Send alert to Owner Channel
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
            
            # Group Warning Message
            if count < 50:
                await update.message.reply_text("⚠️ *သတိပေးချက်:* ဤ Bot ကို သုံးနိုင်ရန် Group တွင် လူဦးရေ အနည်းဆုံး ၅၀ ရှိရပါမည်။ Admin ပေးပြီး အုံနာထံမှ Approval တောင်းခံပါ။")

# ================= BATTLE / DUEL & UPGRADE =================
async def duel_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.reply_to_message:
        await update.message.reply_text("⚔️ Message ကို Reply ပြန်၍ `/duel` ဟု ရိုက်ပါ။")
        return
    p1, p2 = update.effective_user, update.message.reply_to_message.from_user
    u1, u2 = db.get_user(p1.id), db.get_user(p2.id)
    if not u1.get("cards") or not u2.get("cards"):
        await update.message.reply_text("❌ တိုက်ခိုက်ရန် Card အနည်းဆုံး ၁ ခု စီ ရှိရပါမည်။")
        return
    
    winner = random.choice([p1, p2])
    db.get_user(winner.id)["coins"] += 300
    db.save_db()
    await update.message.reply_text(f"⚔️ *DUEL RESULT!*\n🏆 Winner: *{winner.first_name}* (+300 Coins & EXP)", parse_mode="Markdown")

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
    db.save_db()
    await update.message.reply_text(f"⬆️ Card `{cid}` အား Level `{card['level']}` သို့ အောင်မြင်စွာ Upgrade မြှင့်လိုက်ပါပြီ။")

# ================= OWNER & ADMIN ADVANCED COMMANDS =================
async def addcard_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ စာထောက်၍သော်လည်းကောင်း Text ဖြင့်သော်လည်းကောင်း Card အများအပြား ထည့်နိုင်သော စနစ် """
    if not db.is_admin_or_owner(update.effective_user.id): return
    try:
        cid, rarity, series, *name_parts = context.args
        cname = " ".join(name_parts)
        db.data["cards_master"][cid] = {"name": cname, "rarity": int(rarity), "series": series}
        db.save_db()
        await update.message.reply_text(f"✅ Card *{cname}* (`{cid}`) အား Master DB သို့ ထည့်ပြီးပါပြီ။", parse_mode="Markdown")
    except Exception:
        await update.message.reply_text("💡 Usage: `/addcard <id> <rarity> <series> <card_name>`")

async def giveall_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ User တိုင်းထံ Coin သို့မဟုတ် Card အများအပြား Giveaway ပေးသည့် စနစ် """
    if not db.is_admin_or_owner(update.effective_user.id): return
    amt = int(context.args[0])
    for uid, udata in db.data["users"].items():
        udata["coins"] = udata.get("coins", 0) + amt
    db.save_db()
    await update.message.reply_text(f"🎉 All Users received 💰 `{amt}` Coins Giveaway!")

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
        await update.message.reply_text(f"✅ Group `{gid}` ၏ Drop Rate အား `{count}` စာကြောင်းသို့ ပြောင်းလိုက်ပါပြီ။")
    except Exception: pass

async def lang_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = db.get_user(update.effective_user.id)
    u["lang"] = "EN" if u.get("lang") == "MM" else "MM"
    db.save_db()
    await update.message.reply_text(get_txt(update.effective_user.id, "lang_changed"))

# ================= CALLBACK QUERY HANDLER =================
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
        await query.answer(f"✅ Card ID {cid} ကို HMode Filter မှတ်လိုက်ပါပြီ။")

# ================= REGISTER ALL HANDLERS =================
def register_all_handlers(app):
    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("profile", profile_cmd))
    app.add_handler(CommandHandler("harem", harem_cmd))
    app.add_handler(CommandHandler("search", search_cmd))
    app.add_handler(CommandHandler("claim", claim_cmd))
    app.add_handler(CommandHandler("hmode", hmode_cmd))
    app.add_handler(CommandHandler("reset", reset_cmd))
    app.add_handler(CommandHandler("top", top_cmd))
    app.add_handler(CommandHandler("rankings", top_cmd))
    app.add_handler(CommandHandler("ctop", ctop_cmd))
    app.add_handler(CommandHandler("todayNexusCatch", today_nexus_catch_cmd))
    app.add_handler(CommandHandler("Nexus", nexus_cmd))
    app.add_handler(CommandHandler("duel", duel_cmd))
    app.add_handler(CommandHandler("upgrade", upgrade_cmd))
    app.add_handler(CommandHandler("lang", lang_cmd))
    
    # Admin Commands
    app.add_handler(CommandHandler("addcard", addcard_cmd))
    app.add_handler(CommandHandler("giveall", giveall_cmd))
    app.add_handler(CommandHandler("setadmin", setadmin_cmd))
    app.add_handler(CommandHandler("approvegroup", approvegroup_cmd))
    app.add_handler(CommandHandler("changetime", changetime_cmd))
    
    # Listeners
    app.add_handler(CallbackQueryHandler(callback_handler))
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, bot_added_to_group))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_group_spawns))
