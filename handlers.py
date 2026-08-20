import time
import random
import psutil
import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from config import OWNER_IDS, RARITY_TIERS
from database import db
from keyboards import get_start_keyboard, get_hmode_keyboard
from services import CaptchaService, BOT_START_TIME

async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    db.get_user(user.id, user.first_name)
    caption = f"✨ **{user.first_name}** မင်္ဂလာပါ!\nNexus Collectible RPG Card Bot မှ ကြိုဆိုပါသည်။"
    await update.message.reply_photo(
        photo="https://picsum.photos/400/300",
        caption=caption,
        reply_markup=get_start_keyboard(),
        parse_mode="Markdown"
    )

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "📖 **Nexus Card Bot Commands လမ်းညွှန်**\n\n"
        "• `/claim` - ၁၂ နာရီလျှင် ၁ ကဒ်ယူရန် (Captcha Protected)\n"
        "• `/nclaim` - ၄ နာရီလျှင် ၂ ကဒ်ယူရန်\n"
        "• `/inv` / `/check` / `/collection` - မိမိကဒ်များကြည့်ရန်\n"
        "• `/view <card_id>` - ကဒ်ပုံရိပ်နှင့် အသေးစိတ်ကြည့်ရန်\n"
        "• `/profile` / `/bal` / `/daily` - ပရိုဖိုင်နှင့် ဘာလန့်ကြည့်ရန်\n"
        "• `/hmode` - Rarity 13 အဆင့် စစ်ထုတ်ကြည့်ရှုရန်\n"
        "• `/trade` / `/market` / `/auction` - အရောင်းအဝယ် ပြုလုပ်ရန်\n"
        "• `/deck` / `/battle` / `/raid` - RPG တိုက်ခိုက်ရေးသုံးရန်\n"
        "• `/guild` / `/pass` - Guild စနစ်နှင့် Season Pass\n"
        "• `/upgrade` - Coin ဖြင့် ကဒ် Level မြှင့်ရန်\n"
        "• `/botstats` / `/suda` - System Status ကြည့်ရန်"
    )
    await update.message.reply_text(text, parse_mode="Markdown")

async def hmode_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎴 **Card Rules (Rarity Tier 13 အဆင့်) မှ ကြည့်ရှုလိုသော အဆင့်အား ရွေးချယ်ပါ:**",
        reply_markup=get_hmode_keyboard()
    )

async def hmode_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    tier_id = query.data.replace("hmode_", "")
    u = db.get_user(query.from_user.id)
    u["hmode"] = tier_id
    tier_name = RARITY_TIERS[tier_id]["name"] if tier_id in RARITY_TIERS else "ALL"
    await query.edit_message_text(f"✅ Harem Filter အား **{tier_name}** သို့ ပြောင်းလဲလိုက်ပါပြီ။")

async def claim_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = db.get_user(update.effective_user.id)
    now = time.time()
    
    if now - u["last_claim"] < 43200:
        rem = int((43200 - (now - u["last_claim"])) / 3600)
        await update.message.reply_text(f"⏳ Cooldown မိနေပါသည်။ နောက်ထပ် {rem} နာရီကြာမှ ပြန်လည် Claim နိုင်ပါမည်။")
        return
        
    q, ans, opts = CaptchaService.generate_math_captcha()
    context.user_data["captcha_ans"] = ans
    context.user_data["claim_time"] = now

    buttons = [[InlineKeyboardButton(str(o), callback_data=f"cap_claim_{o}")] for o in opts]
    await update.message.reply_text(
        f"🤖 **Anti-Cheat Verification (၂ မိနစ်အတွင်း ဖြေဆိုပါ):**\n\nပုစ္ဆာ: `{q}`",
        reply_markup=InlineKeyboardMarkup(buttons),
        parse_mode="Markdown"
    )

async def captcha_claim_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_ans = int(query.data.replace("cap_claim_", ""))
    correct_ans = context.user_data.get("captcha_ans")
    claim_time = context.user_data.get("claim_time", 0)
    
    if time.time() - claim_time > 120:
        await query.edit_message_text("❌ အချိန် ၂ မိနစ်ကျော်လွန်သွားသည့်အတွက် Claim ခွင့် ပျက်ပြယ်သွားပါပြီ။")
        return
        
    if user_ans == correct_ans:
        u = db.get_user(query.from_user.id)
        u["last_claim"] = time.time()
        card_sn = f"CARD-{random.randint(1000, 9999)} (#1 Print)"
        u["cards"].append(card_sn)
        await query.edit_message_text(f"🎉 **ဂုဏ်ယူပါတယ်။** ကဒ် ရရှိခဲ့ပါသည်။\n🎴 ရရှိသောကဒ်: `{card_sn}`", parse_mode="Markdown")
    else:
        await query.edit_message_text("❌ မေးခွန်း အဖြေ မှားယွင်းပါသည်။")

async def botstats_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    is_owner = " (Owner)" if user_id in OWNER_IDS else ""
    
    cpu = psutil.cpu_percent()
    ram = psutil.virtual_memory().percent
    uptime = datetime.datetime.now() - BOT_START_TIME
    
    text = (
        f"🤖 **Bot System Performance{is_owner}**\n\n"
        f"⏱️ Uptime: `{str(uptime).split('.')[0]}`\n"
        f"💻 CPU Usage: `{cpu}%`\n"
        f"🧠 RAM Usage: `{ram}%`\n"
        f"👑 Owners Authorized: `{len(OWNER_IDS)} Users`"
    )
    await update.message.reply_text(text, parse_mode="Markdown")

async def handle_group_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_chat or update.effective_chat.type == "private":
        return
        
    chat_id = update.effective_chat.id
    db.group_counts[chat_id] = db.group_counts.get(chat_id, 0) + 1
    
    if db.group_counts[chat_id] >= 100:
        db.group_counts[chat_id] = 0
        await update.effective_chat.send_message(
            "🎴 **A New Card Has Spawned!**\n/claim သို့မဟုတ် အောက်ပါ Grab Button ကို နှိပ်၍ ယူပါ။",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Grab Card 🎴", callback_data="grab_spawned_card")]])
        )
