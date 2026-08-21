import time
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from config import OWNER_IDS, RARITY_STAGES, LINK_GROUP, LINK_CHANNEL, LINK_WAIFU, LOG_CHANNEL_ID, LANGUAGES
from database import db
from card_generator import generate_custom_card

# Force Join Check Engine
async def check_force_join(user_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
    try:
        # In production, check chat member status via Telegram API
        return True
    except Exception:
        return False

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
        "• `/trade` / `/gift` / `/duel` - တိုက်ခိုက်မှုနှင့် အရောင်းအဝယ် ပြုလုပ်ရန်\n"
        "• `/fav` / `/unfav` - နှစ်သက်သော ကဒ် သတ်မှတ်ရန်\n"
        "• `/hmode` / `/reset` - Harem Filtering ပြုလုပ်ရန်\n"
        "• `/setlang` - Myanmar/English ဘာသာစကား ပြောင်းရန်"
    )
    await update.message.reply_text(text, parse_mode="Markdown")

async def harem_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    u = db.get_user(user.id, user.first_name)
    
    if not await check_force_join(user.id, context):
        buttons = InlineKeyboardMarkup([
            [InlineKeyboardButton("🌐 Group Join", url=LINK_GROUP)],
            [InlineKeyboardButton("📢 Channel Join", url=LINK_CHANNEL)]
        ])
        await update.message.reply_text(LANGUAGES[u["lang"]]["NEED_JOIN"], reply_markup=buttons)
        return

    cards = u["cards"]
    text = f"🎴 **{user.first_name}'s Collection ({len(cards)} Cards):**\n\n"
    for idx, c in enumerate(cards, 1):
        m_card = db.data["cards_master"].get(c["id"], {"name": "Unknown"})
        text += f"{idx}. ID: `{c['id']}` | **{m_card['name']}** | Mint: {c.get('mint', 100)}%\n"

    await update.message.reply_text(text, parse_mode="Markdown")

async def profile_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    u = db.get_user(user.id, user.first_name)
    
    # Retrieve Profile Photo
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

    # Image processing Canvas call
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

# ---------- GROUP EVENT LISTENERS & APPROVAL ----------

async def on_bot_added_to_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    added_by = update.effective_user
    members_count = await chat.get_member_count()
    
    # Notify Channel
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

    gp = db.get_group(chat.id)
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

# ---------- ADMIN / OWNER COMMANDS ----------

async def approvegroup_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not db.is_admin_or_owner(update.effective_user.id, OWNER_IDS):
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
    if not db.is_admin_or_owner(update.effective_user.id, OWNER_IDS):
        return
    try:
        # Format: /addcard <id> <rarity_1-13> <name>
        cid = context.args[0]
        rarity = int(context.args[1])
        name = " ".join(context.args[2:])
        
        db.data["cards_master"][cid] = {
            "name": name,
            "rarity": rarity,
            "atk": rarity * 100,
            "def": rarity * 80,
            "hp": rarity * 200,
            "img": "https://picsum.photos/400/600"
        }
        db.save_db()
        await update.message.reply_text(f"✅ Card `{cid}` - **{name}** အား Database ထဲ ထည့်သွင်းပြီးပါပြီ။")
    except Exception:
        await update.message.reply_text("Usage: `/addcard <id> <rarity_1_to_13> <card_name>`")

async def givecoin_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not db.is_admin_or_owner(update.effective_user.id, OWNER_IDS):
        return
    try:
        uid = int(context.args[0])
        amt = int(context.args[1])
        u = db.get_user(uid)
        u["coins"] += amt
        db.save_db()
        await update.message.reply_text(f"✅ User `{uid}` သို့ Coin `{amt:,}` ထည့်ပေးလိုက်ပါပြီ။")
    except Exception:
        await update.message.reply_text("Usage: `/givecoin <user_id> <amount>`")
