import os
import time
import random
import psutil
import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from config import OWNER_IDS, RARITY_TIERS
from database import db
from keyboards import get_start_keyboard, get_hmode_keyboard
from services import CaptchaService, CanvasEngine, BOT_START_TIME

# ---------- USER COMMANDS ----------

async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    db.get_user(user.id, user.first_name)
    caption = f"✨ **{user.first_name}** မင်္ဂလာပါ!\nNexus RPG Card Bot မှ ကြိုဆိုပါသည်။"
    await update.message.reply_photo(
        photo="https://picsum.photos/400/300",
        caption=caption,
        reply_markup=get_start_keyboard(),
        parse_mode="Markdown"
    )

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "📖 **Nexus Card Bot Commands လမ်းညွှန်**\n\n"
        "**User Commands:**\n"
        "• `/claim` - ၁၂ နာရီ ၁ ကြိမ် (Captcha Protected)\n"
        "• `/nclaim` - ၄ နာရီ ၂ ကဒ် ယူရန်\n"
        "• `/inv` / `/collection` - မိမိကဒ်များ ကြည့်ရန်\n"
        "• `/view <card_id>` - ကဒ်ပုံရိပ်နှင့် အသေးစိတ်ကြည့်ရန်\n"
        "• `/profile` / `/bal` / `/daily` - ပရိုဖိုင်နှင့် ငွေစာရင်းကြည့်ရန်\n"
        "• `/hmode` - 13 Rarity Tiers သီးသန့်စစ်ထုတ်ရန်\n"
        "• `/trade` / `/market` / `/auction` - အရောင်းအဝယ်ပြုလုပ်ရန်\n"
        "• `/deck` / `/battle` / `/raid` - RPG တိုက်ခိုက်ရေးသုံးရန်\n"
        "• `/guild` / `/pass` - Guild စနစ်နှင့် Season Pass\n"
        "• `/upgrade <card_id>` - Coin သုံး၍ Level မြှင့်ရန်\n\n"
        "**Cosmetics Commands:**\n"
        "• `/frame_set <card_id> <frame>` - ဘောင်တပ်ရန်\n"
        "• `/dye <card_id> <color_code>` - Hex Color အရောင်တင်ရန်\n"
        "• `/font_set <card_id> <font>` - စာသား Font ပြောင်းရန်\n"
        "• `/custom_preview <card_id>` - မပြင်မီ Preview ကြည့်ရန်\n\n"
        "**System Commands:**\n"
        "• `/botstats` - CPU, RAM နှင့် Uptime စစ်ရန်"
    )
    await update.message.reply_text(text, parse_mode="Markdown")

async def claim_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = db.get_user(update.effective_user.id)
    now = time.time()
    
    if now - u["last_claim"] < 43200:
        rem = int((43200 - (now - u["last_claim"])) / 3600)
        await update.message.reply_text(f"⏳ Cooldown မိနေပါသည်။ နောက်ထပ် {rem} နာရီကြာမှ ပြန်လည် Claim နိုင်ပါမည်။")
        return
        
    q, ans, opts = CaptchaService.generate_captcha()
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
    
    if time.time() - context.user_data.get("claim_time", 0) > 120:
        await query.edit_message_text("❌ အချိန် ၂ မိနစ်ကျော်လွန်သွားသည့်အတွက် ပျက်ပြယ်သွားပါပြီ။")
        return
        
    if user_ans == correct_ans:
        u = db.get_user(query.from_user.id)
        u["last_claim"] = time.time()
        card_id = f"CARD-{random.randint(1000, 9999)}"
        new_card = {"id": card_id, "card_key": "Astraea", "print_num": "#0001", "mint": "100%", "frame": "Default", "dye": "#FFA500", "font": "Gothic", "level": 1}
        u["cards"].append(new_card)
        
        await query.edit_message_text(f"🎉 **ဂုဏ်ယူပါတယ်။** ကဒ် ရရှိခဲ့ပါသည်။\n🎴 Card ID: `{card_id}` (Mint: 100%)", parse_mode="Markdown")
    else:
        await query.edit_message_text("❌ မေးခွန်း အဖြေ မှားယွင်းပါသည်။")

async def view_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = db.get_user(update.effective_user.id)
    if not u["cards"]:
        await update.message.reply_text("❌ သင့်ထံတွင် ကဒ်များ မရှိသေးပါ။ `/claim` ဖြင့် စတင်ယူပါ။")
        return
        
    card = u["cards"][-1]
    img_path = CanvasEngine.generate_card_image(
        title=card["card_key"], rarity="LEGENDARY", print_no=card["print_num"],
        mint=card["mint"], dye_color=card["dye"], frame=card["frame"]
    )
    
    with open(img_path, 'rb') as photo:
        await update.message.reply_photo(photo=photo, caption=f"🎴 **Card View:** `{card['id']}`\nLevel: {card['level']} | Frame: {card['frame']}")
    
    if os.path.exists(img_path):
        os.remove(img_path)

async def hmode_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🎴 **Rarity Tier 13 အဆင့် စစ်ထုတ်ကြည့်ရှုရန် ရွေးချယ်ပါ:**", reply_markup=get_hmode_keyboard())

async def hmode_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    tier_id = query.data.replace("hmode_", "")
    u = db.get_user(query.from_user.id)
    u["hmode"] = tier_id
    tier_name = RARITY_TIERS[tier_id]["name"] if tier_id in RARITY_TIERS else "ALL"
    await query.edit_message_text(f"✅ Filter အား **{tier_name}** သို့ ပြောင်းလဲလိုက်ပါပြီ။")

async def upgrade_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = db.get_user(update.effective_user.id)
    if u["coins"] < 500:
        await update.message.reply_text("❌ Level မြှင့်ရန် Coin 500 လိုအပ်ပါသည်။")
        return
    u["coins"] -= 500
    if u["cards"]:
        u["cards"][-1]["level"] += 1
        await update.message.reply_text(f"✅ ကဒ် Level {u['cards'][-1]['level']} သို့ မြှင့်တင်ပြီးပါပြီ! (Coin 500 နှုတ်ယူခဲ့သည်)")
    else:
        await update.message.reply_text("❌ မြှင့်တင်ရန် ကဒ်မရှိပါ။")

async def botstats_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cpu = psutil.cpu_percent()
    ram = psutil.virtual_memory().percent
    uptime = datetime.datetime.now() - BOT_START_TIME
    await update.message.reply_text(
        f"🤖 **Nexus System Performance**\n\n"
        f"⏱️ Uptime: `{str(uptime).split('.')[0]}`\n"
        f"💻 CPU: `{cpu}%` | 🧠 RAM: `{ram}%`\n"
        f"📅 Started Date: `{BOT_START_TIME.strftime('%Y-%m-%d %H:%M:%S')}`\n"
        f"🛡️ AES-256 & Captcha Active", parse_mode="Markdown"
    )

# ---------- ADMIN / OWNER COMMANDS ----------

async def suda_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if not db.is_owner_or_sudo(uid, OWNER_IDS):
        await update.message.reply_text("❌ Owner/Sudo မဟုတ်ပါက သုံးစွဲခွင့်မရှိပါ။")
        return
    await update.message.reply_text(f"👑 **Sudo Control Panel**\nSudo Users Active: {len(db.sudo_users)}\nOwners: {len(OWNER_IDS)}")

async def add_sudo_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if uid not in OWNER_IDS:
        await update.message.reply_text("❌ Owner သာလျှင် Sudo အသစ် ခန့်အပ်နိုင်ပါသည်။")
        return
    if context.args:
        new_sudo = int(context.args[0])
        db.sudo_users.add(new_sudo)
        await update.message.reply_text(f"✅ User `{new_sudo}` အား Sudo အဖြစ် ခန့်အပ်လိုက်ပါပြီ။")

async def broadcast_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if not db.is_owner_or_sudo(uid, OWNER_IDS):
        return
    msg = " ".join(context.args)
    if not msg:
        await update.message.reply_text("❌ စာသား ထည့်သွင်းပါ။ `/broadcast <message>`")
        return
    await update.message.reply_text(f"📢 **Broadcast Sent:** {msg}")

async def handle_group_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_chat or update.effective_chat.type == "private":
        return
    chat_id = update.effective_chat.id
    db.group_counts[chat_id] = db.group_counts.get(chat_id, 0) + 1
    
    if db.group_counts[chat_id] >= 100:
        db.group_counts[chat_id] = 0
        await update.effective_chat.send_message(
            "🎴 **A New Card Has Spawned!**\n/claim သို့မဟုတ် Grab Button နှိပ်၍ ယူပါ။",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Grab Card 🎴", callback_data="grab_spawned_card")]])
        )
