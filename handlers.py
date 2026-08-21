import os
import time
import random
import psutil
import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from config import OWNER_IDS, RARITY_TIERS, STRINGS, LOG_CHANNEL_ID
from database import db
from keyboards import get_start_keyboard, get_force_join_keyboard, get_hmode_keyboard, get_page_keyboard
from services import CanvasEngine, BOT_START_TIME

# Helper: Force Join Check
async def is_user_joined(user_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
    try:
        # Check channels
        m1 = await context.bot.get_chat_member(chat_id="-1001234567890", user_id=user_id) # Replace with real channel/group chat_ids
        return m1.status in ["member", "administrator", "creator"]
    except Exception:
        return True # Bypass if checking private link chat_ids directly

# ---------- USER COMMANDS ----------

async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    u = db.get_user(user.id, user.first_name)
    lang = u["lang"]
    
    caption = STRINGS[lang]["start"].format(name=user.first_name)
    await update.message.reply_photo(
        photo="https://picsum.photos/400/300",
        caption=caption,
        reply_markup=get_start_keyboard(),
        parse_mode="Markdown"
    )

async def setlang_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = db.get_user(update.effective_user.id)
    if u["lang"] == "MM":
        u["lang"] = "EN"
        await update.message.reply_text("✅ Language changed to English!")
    else:
        u["lang"] = "MM"
        await update.message.reply_text("✅ ဘာသာစကားအား မြန်မာသို့ ပြောင်းလဲလိုက်ပါပြီ!")

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "📖 **Nexus Bot Commands လမ်းညွှန်**\n\n"
        "**General & Cards:**\n"
        "• `/harem` - မိမိကဒ်များ ကြည့်ရန် (Force Join လိုအပ်)\n"
        "• `/search` - ဘော့ထဲရှိ ကဒ်များ ရှာဖွေကြည့်ရှုရန်\n"
        "• `/check <card_id>` - ကဒ်အသေးစိတ် ကြည့်ရန်\n"
        "• `/fav <id>` / `/unfav <id>` - Fav ကဒ် သတ်မှတ်ရန်\n"
        "• `/claim` - ၁၂ နာရီ ၁ ကြိမ် (၂၄ နာရီလျှင် ၂ ကဒ် ရရှိ)\n"
        "• `/hmode` - Harem Rarity Filter ချိန်ရန်\n"
        "• `/reset` - Filter မူလအတိုင်း ပြန်ရှင်းရန်\n\n"
        "**Economy & Market:**\n"
        "• `/profile` / `/bal` / `/daily` - ပရိုဖိုင်၊ Coin နှင့် Daily Coin (500) ယူရန်\n"
        "• `/sellprice` - Rarity အလိုက် ကဒ်ရောင်းစျေး သတ်မှတ်ချက်များ ကြည့်ရန်\n"
        "• `/market` - စျေးကွက်တင်ထားသော ကဒ်များ ကြည့်ရန်\n"
        "• `/sell <char_id> <price>` - စျေးကွက်တွင် ကဒ်တင်ရောင်းရန်\n"
        "• `/buy <listing_id>` / `/delist <id>` - ကဒ် ဝယ်ယူရန်/ပြန်ဖြုတ်ရန်\n"
        "• `/trade` (Reply Msg) - ကဒ်ချင်း တိုက်ရိုက် လဲလှယ်ရန်\n"
        "• `/gift` (Reply Msg) - ကဒ် လက်ဆောင်ပေးရန်\n"
        "• `/duel` - တိုက်ခိုက်၍ Level, Exp နှင့် Coin ရယူရန်\n\n"
        "**Leaderboards:**\n"
        "• `/top` / `/rankings` - Global Top 15 ကဒ်အများဆုံး ရထားသူများ ကြည့်ရန်\n"
        "• `/ctop` - ဤ Group အတွင်း ကဒ်အများဆုံး ကောက်ထားသူများ ကြည့်ရန်\n"
        "• `/todayNexusCatch` - ဒီနေ့ ကဒ်အများဆုံး ကောက်သူများ စာရင်း"
    )
    await update.message.reply_text(text, reply_markup=get_page_keyboard("help", 1, 3), parse_mode="Markdown")

async def harem_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    u = db.get_user(user_id)
    
    # Check Force Join Links
    if not await is_user_joined(user_id, context):
        await update.message.reply_text(
            STRINGS[u["lang"]]["force_join"],
            reply_markup=get_force_join_keyboard()
        )
        return

    cards = u["cards"]
    if not cards:
        await update.message.reply_text("❌ သင့်ထံတွင် ကဒ်များ မရှိသေးပါ `/claim` ဖြင့် စတင်ယူပါ။")
        return
        
    text = f"🎴 **{update.effective_user.first_name}'s Harem Collection:**\n\n"
    for idx, c in enumerate(cards[:5], 1):
        text += f"{idx}. `{c['id']}` - **{c['card_key']}** (Lvl: {c['level']})\n"
        
    await update.message.reply_text(text, reply_markup=get_page_keyboard("harem", 1, max(1, len(cards)//5)), parse_mode="Markdown")

async def claim_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = db.get_user(update.effective_user.id)
    now = time.time()
    
    if now - u["last_claim"] < 43200: # 12 Hours
        rem = int((43200 - (now - u["last_claim"])) / 3600)
        await update.message.reply_text(f"⏳ Cooldown မိနေပါသည်။ နောက်ထပ် {rem} နာရီကြာမှ ပြန်လည် Claim နိုင်ပါမည်။")
        return
        
    u["last_claim"] = now
    c1_id, c2_id = f"CARD-{random.randint(1000,9999)}", f"CARD-{random.randint(1000,9999)}"
    u["cards"].extend([
        {"id": c1_id, "card_key": "Astraea Guardian", "level": 1},
        {"id": c2_id, "card_key": "Shadow Assassin", "level": 1}
    ])
    await update.message.reply_text(f"🎉 **Claim အောင်မြင်ပါသည်။** 24hr အတွက် ကဒ် ၂ ကဒ် ရရှိခဲ့ပါသည်:\n1. `{c1_id}`\n2. `{c2_id}`", parse_mode="Markdown")

async def profile_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    u = db.get_user(user.id, user.first_name)
    
    photos = await user.get_profile_photos(limit=1)
    photo_file = photos.photos[0][-1].file_id if photos.total_count > 0 else "https://picsum.photos/300/300"
    
    caption = (
        f"👤 **{user.first_name}'s Profile**\n\n"
        f"💰 Coins: `{u['coins']}`\n"
        f"🎴 Total Cards: `{len(u['cards'])}`\n"
        f"⭐ Favorites: `{len(u['favorites'])}`\n"
        f"🌐 Global Rank: `#1` (Top Collector)\n"
        f"🌐 Language: `{u['lang']}`"
    )
    await update.message.reply_photo(photo=photo_file, caption=caption, parse_mode="Markdown")

async def daily_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = db.get_user(update.effective_user.id)
    u["coins"] += 500
    await update.message.reply_text("🪙 နေ့စဉ် အခမဲ့ Coin 500 ရရှိခဲ့ပါပြီ! (Current Bal: " + str(u["coins"]) + ")")

async def sellprice_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = "💰 **Card Rarity Market Price Rules (အမြင့်ဆုံး 15,000 Coin):**\n\n"
    for k, v in RARITY_TIERS.items():
        text += f"• **{v['name']}**: `{v['price']} Coins`\n"
    await update.message.reply_text(text, parse_mode="Markdown")

# ---------- GROUP BOT ENTRY / RULES CHECK ----------

async def on_bot_added_to_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    added_by = update.effective_user
    
    # 1. Check member count >= 50
    members_count = await chat.get_member_count()
    
    # Send Log to Owner Log Channel
    log_msg = (
        f"🤖 **Bot Added to New Group!**\n\n"
        f"🌐 Group Name: `{chat.title}`\n"
        f"🆔 Group ID: `{chat.id}`\n"
        f"👥 Members Count: `{members_count}`\n"
        f"👤 Added By: {added_by.full_name} (`{added_by.id}`)"
    )
    try:
        await context.bot.send_message(chat_id=LOG_CHANNEL_ID, text=log_msg, parse_mode="Markdown")
    except Exception:
        pass

    gp_data = db.get_group(chat.id)
    if members_count < 50:
        await chat.send_message("⚠️ ဤ Group တွင် လူ ၅၀ အနည်းဆုံး မရှိသေးပါ။ Bot ကို သုံးစွဲနိုင်မည် မဟုတ်ပါ။")
        return
        
    await chat.send_message(
        "👋 **မင်္ဂလာပါ! Nexus Card Bot ကို Group ထဲသို့ ထည့်သွင်းပေးသည့်အတွက် ကျေးဇူးတင်ပါသည်။**\n\n"
        "⚠️ **အသုံးပြုရန် လိုအပ်ချက်များ:**\n"
        "1. Bot အား Group Admin 권한 ပေးထားရပါမည်။\n"
        "2. Owner ထံမှ Group Approval (ခွင့်ပြုချက်) ရရှိရန် အကြောင်းကြားပေးပါ။",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Contact Owner", url="https://t.me/example_owner")]])
    )

async def handle_group_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    if not chat or chat.type == "private":
        return
        
    gp = db.get_group(chat.id)
    if not gp["approved"]:
        return # Group not activated by Owner
        
    gp["msg_count"] += 1
    if gp["msg_count"] >= gp["spawn_rate"]:
        gp["msg_count"] = 0
        await chat.send_message(
            "🎴 **A New Nexus Card Has Spawned!**\n`/Nexus Astraea` ရိုက်ထည့်၍ ကဒ် ကောက်ယူပါ!",
            parse_mode="Markdown"
        )

# ---------- ADMIN / OWNER COMMANDS ----------

async def approvegroup_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if not db.is_owner_or_sudo(uid, OWNER_IDS):
        return
    if context.args:
        gid = int(context.args[0])
        gp = db.get_group(gid)
        gp["approved"] = True
        await update.message.reply_text(f"✅ Group ID `{gid}` အား Bot အသုံးပြုခွင့် Approve ပေးလိုက်ပါပြီ။")

async def givecoin_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not db.is_owner_or_sudo(update.effective_user.id, OWNER_IDS):
        return
    try:
        target_id = int(context.args[0])
        amt = int(context.args[1])
        u = db.get_user(target_id)
        u["coins"] += amt
        await update.message.reply_text(f"✅ User `{target_id}` ထံသို့ Coin `{amt}` ပေးအပ်ပြီးပါပြီ။")
    except Exception:
        await update.message.reply_text("Usage: `/givecoin <user_id> <amount>`")
