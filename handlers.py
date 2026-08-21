import os
import time
import random
import psutil
import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from config import OWNER_IDS, RARITY_TIERS, LINK_GROUP, LINK_CHANNEL, LINK_WAIFU, LOG_CHANNEL_ID
from database import db

# ---------- USER COMMANDS ----------

async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    db.get_user(user.id, user.first_name)
    
    caption = f"✨ **{user.first_name}** မင်္ဂလာပါ!\nNexus RPG Card Bot မှ ကြိုဆိုပါသည်!"
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton(" My Waifu", url=LINK_WAIFU)],
        [InlineKeyboardButton("🌐 Group Link", url=LINK_GROUP), InlineKeyboardButton("📢 Update Channel", url=LINK_CHANNEL)]
    ])
    await update.message.reply_photo(
        photo="https://picsum.photos/400/300",
        caption=caption,
        reply_markup=buttons,
        parse_mode="Markdown"
    )

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "📖 **Nexus Bot Commands လမ်းညွှန်**\n\n"
        "• `/harem` - မိမိကဒ်များ ကြည့်ရန်\n"
        "• `/search` - ကဒ်များ ရှာရန်\n"
        "• `/check <card_id>` - ကဒ်ကြည့်ရန်\n"
        "• `/profile` - ပရိုဖိုင်\n"
        "• `/top` / `/ctop` / `/rankings` - Top စာရင်းများ\n"
        "• `/daily` - 500 Free Coin\n"
        "• `/sellprice` - ကဒ်စျေးနှုန်းများ\n"
        "• `/market` / `/sell` / `/buy` - စျေးကွက်\n"
        "• `/trade` / `/gift` / `/duel` - တိုက်ခိုက်ခြင်းနှင့် လက်ဆောင်ပေးခြင်း\n"
        "• `/claim` - ၁၂ နာရီ ၁ ကြိမ် ကဒ်ယူရန်\n"
        "• `/hmode` / `/reset` - Harem စစ်ထုတ်ရန်\n"
        "• `/fav <id>` / `/unfav <id>` - Fav သတ်မှတ်ရန်"
    )
    await update.message.reply_text(text, parse_mode="Markdown")

async def harem_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    u = db.get_user(user.id, user.first_name)
    
    # Force Join Check Links
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("🌐 Group Link", url=LINK_GROUP)],
        [InlineKeyboardButton("📢 Channel Link", url=LINK_CHANNEL)]
    ])
    
    cards = u["cards"]
    if not cards:
        await update.message.reply_text("❌ သင့်ထံတွင် ကဒ်များ မရှိသေးပါ။", reply_markup=buttons)
        return
        
    text = f"🎴 **{user.first_name}'s Harem Collection:**\n\n"
    for idx, c in enumerate(cards, 1):
        text += f"{idx}. ID: `{c['id']}` - **{c['name']}** (Lvl: {c.get('level', 1)})\n"
        
    await update.message.reply_text(text, reply_markup=buttons, parse_mode="Markdown")

async def search_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = "🔍 **Nexus Cards Database:**\n\n• `0021` - Astraea Guardian (15,000 Coins)\n• `0022` - Shadow Assassin (9,000 Coins)"
    buttons = InlineKeyboardMarkup([[InlineKeyboardButton("📢 Channel", url=LINK_CHANNEL)]])
    await update.message.reply_text(text, reply_markup=buttons, parse_mode="Markdown")

async def profile_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    u = db.get_user(user.id, user.first_name)
    
    caption = (
        f"👤 **{user.first_name}'s Profile**\n\n"
        f"💰 Coins: `{u['coins']}`\n"
        f"🎴 Total Cards: `{len(u['cards'])}`\n"
        f"⭐ Favorites: `{len(u['favorites'])}`\n"
        f"🌐 Global Rank: `#1`"
    )
    await update.message.reply_text(caption, parse_mode="Markdown")

async def top_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = "🏆 **Global Top 15 Card Collectors:**\n\n1. User1 - 150 Cards\n2. User2 - 120 Cards\n3. User3 - 95 Cards"
    await update.message.reply_text(text, parse_mode="Markdown")

async def ctop_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = f"🏆 **{update.effective_chat.title} Top Collectors:**\n\n1. {update.effective_user.first_name} - 10 Cards"
    await update.message.reply_text(text, parse_mode="Markdown")

async def daily_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = db.get_user(update.effective_user.id)
    u["coins"] += 500
    await update.message.reply_text(f"🪙 နေ့စဉ် အခမဲ့ Coin 500 ရရှိခဲ့ပါပြီ! (လက်ကျန်: {u['coins']})")

async def sellprice_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = "💰 **Card Rarity Market Prices:**\n\n"
    for k, v in RARITY_TIERS.items():
        text += f"• **Tier {k} ({v['name']})**: `{v['price']} Coins`\n"
    await update.message.reply_text(text, parse_mode="Markdown")

async def claim_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = db.get_user(update.effective_user.id)
    now = time.time()
    if now - u["last_claim"] < 43200:
        rem = int((43200 - (now - u["last_claim"])) / 3600)
        await update.message.reply_text(f"⏳ Cooldown မိနေပါသည်။ {rem} နာရီကြာမှ ပြန်ယူပါ။")
        return
    u["last_claim"] = now
    cid = f"CARD-{random.randint(1000,9999)}"
    u["cards"].append({"id": cid, "name": "Astraea Guardian", "rarity": "10", "level": 1})
    await update.message.reply_text(f"🎉 ကဒ်သစ် ရရှိခဲ့ပါသည်: `{cid}`", parse_mode="Markdown")

async def nexus_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # /Nexus Card_Name (ကဒ်ကောက်ရန်)
    if not context.args:
        await update.message.reply_text("Usage: `/Nexus <Card_Name>`", parse_mode="Markdown")
        return
    card_name = " ".join(context.args)
    u = db.get_user(update.effective_user.id)
    cid = f"{random.randint(1000,9999)}"
    u["cards"].append({"id": cid, "name": card_name, "level": 1})
    u["today_catches"] += 1
    await update.message.reply_text(f"🎉 **{card_name}** အား ကောက်ယူလိုက်ပါပြီ! (Card ID: `{cid}`)", parse_mode="Markdown")

# ---------- GROUP BOT ENTRY / RULES CHECK ----------

async def on_bot_added_to_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    added_by = update.effective_user
    members_count = await chat.get_member_count()
    
    # Owner Log Notification
    log_msg = (
        f"🤖 **Bot Added to Group!**\n\n"
        f"🌐 Group: `{chat.title}` (ID: `{chat.id}`)\n"
        f"👥 Members: `{members_count}`\n"
        f"👤 Added By: `{added_by.id}`"
    )
    try:
        await context.bot.send_message(chat_id=LOG_CHANNEL_ID, text=log_msg, parse_mode="Markdown")
    except Exception:
        pass

    if members_count < 50:
        await chat.send_message("⚠️ ဤ Group တွင် လူ ၅၀ အနည်းဆုံး မရှိသေးပါ။ Bot ကို သုံးစွဲနိုင်မည် မဟုတ်ပါ။")
        return

    await chat.send_message(
        "👋 **Nexus Bot ကို ထည့်သွင်းပေးသည့်အတွက် ကျေးဇူးတင်ပါသည်။**\n\n"
        "⚠️ **စည်းကမ်းချက်များ:**\n"
        "1. Bot အား Group Admin ပေးထားရပါမည်။\n"
        "2. Owner ထံမှ Group Approve ရယူပေးပါ။"
    )

async def handle_group_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    if not chat or chat.type == "private":
        return
    
    gp = db.get_group(chat.id)
    gp["msg_count"] += 1
    if gp["msg_count"] >= gp["spawn_rate"]:
        gp["msg_count"] = 0
        await chat.send_message("🎴 **A New Card Has Spawned!**\n`/Nexus Astraea` ဟု ရိုက်ထည့်၍ ကဒ် ကောက်ယူပါ!")

# ---------- ADMIN / OWNER COMMANDS ----------

async def changetime_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not db.is_owner_or_sudo(update.effective_user.id, OWNER_IDS):
        return
    try:
        gid = int(context.args[0])
        rate = int(context.args[1])
        gp = db.get_group(gid)
        gp["spawn_rate"] = rate
        await update.message.reply_text(f"✅ Group `{gid}` ၏ Message Spawn Limit အား `{rate}` စာစောင် သို့ ပြောင်းလဲလိုက်ပါပြီ။")
    except Exception:
        await update.message.reply_text("Usage: `/changetime <group_id> <messages_count>`")

async def givecoin_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not db.is_owner_or_sudo(update.effective_user.id, OWNER_IDS):
        return
    try:
        target_id = int(context.args[0])
        amt = int(context.args[1])
        u = db.get_user(target_id)
        u["coins"] += amt
        await update.message.reply_text(f"✅ User `{target_id}` သို့ Coin `{amt}` ပေးလိုက်ပါပြီ။")
    except Exception:
        await update.message.reply_text("Usage: `/givecoin <user_id> <amount>`")
