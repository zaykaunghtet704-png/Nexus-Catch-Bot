import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, ApplicationHandlerStop
from pymongo import MongoClient

# ---------------------------------------------------------
# MongoDB Connection (ကတ်တွေ သိမ်းတဲ့ Database နဲ့ ချိတ်ဆက်ပုံစံတူညီစေရန်)
# ---------------------------------------------------------
MONGO_URL = os.getenv("MONGO_URL")
db = None
force_join_col = None

if MONGO_URL:
    try:
        client = MongoClient(MONGO_URL)
        # Default Database ကို ယူမည်၊ URI ထဲတွင် နာမည်မပါပါက 'nexus_catch_db' ကို သုံးမည်
        db = client.get_default_database()
        if db is None or db.name == "test":
            db = client["nexus_catch_db"]
        force_join_col = db["force_joins"]
        print("✅ Force Join Module: MongoDB Connected Successfully!")
    except Exception as e:
        print(f"❌ MongoDB Connection Error in Force Join Module: {e}")

# ---------------------------------------------------------
# ဆာဗာ Env နှင့် Hardcoded Fallback မှ Owner/Admin ID များ စစ်ထုတ်ခြင်း
# ---------------------------------------------------------
env_admins = os.getenv("ADMIN_IDS", "")
ADMIN_IDS = [int(x.strip()) for x in env_admins.split(",") if x.strip().isdigit()]

env_owner = os.getenv("OWNER_ID", "")
if env_owner.strip().isdigit():
    ADMIN_IDS.append(int(env_owner.strip()))

# Fallback Owner ID
HARDCODED_OWNER_ID = 7974865879 
if HARDCODED_OWNER_ID not in ADMIN_IDS:
    ADMIN_IDS.append(HARDCODED_OWNER_ID)


# =========================================================
# ၁။ Force Join စစ်ဆေးသည့် Function (Database မှ ဖတ်မည်)
# =========================================================
async def check_must_join(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    if force_join_col is None:
        return True

    must_join_chats = list(force_join_col.find({}))
    if not must_join_chats:
        return True

    user_id = update.effective_user.id
    bot = context.bot
    not_joined_buttons = []

    for chat in must_join_chats:
        chat_id = chat["chat_id"]
        title = chat["title"]
        link = chat["link"]
        try:
            member = await bot.get_chat_member(chat_id, user_id)
            if member.status in ["banned", "kicked"]:
                await update.message.reply_text("❌ သင်သည် လိုအပ်သော Channel မှ Ban ခံထားရသဖြင့် Bot သုံးခွင့်မရှိပါ။")
                return False
        except Exception:
            not_joined_buttons.append([
                InlineKeyboardButton(title, url=link)
            ])

    if not_joined_buttons:
        bot_username = (await bot.get_me()).username
        not_joined_buttons.append([
            InlineKeyboardButton("✅ Join ပြီးပါပြီ (ပြန်လည်စစ်ဆေးမည်)", url=f"https://t.me/{bot_username}?start=start")
        ])

        await update.message.reply_text(
            "⚠️ **Bot ကို အသုံးပြုရန်အတွက် အောက်ပါ လင့်ခ်များအားလုံးကို မဖြစ်မနေ Join ပေးရပါမည်။**",
            reply_markup=InlineKeyboardMarkup(not_joined_buttons)
        )
        return False

    return True


# =========================================================
# ၂။ /addjoin Command (Database ထဲသို့ သိမ်းမည်)
# =========================================================
async def add_must_join(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("❌ Owner/Admin များသာ အသုံးပြုနိုင်ပါသည်။")
        return

    if force_join_col is None:
        await update.message.reply_text("❌ Database ချိတ်ဆက်မှု မရှိသေးပါ။ MONGO_URL ကို စစ်ဆေးပါ။")
        return

    try:
        args = " ".join(context.args)
        parts = [p.strip() for p in args.split("|")]
        if len(parts) < 3:
            raise ValueError()

        chat_id_input = parts[0]
        title = parts[1]
        link = parts[2]
        chat_id = int(chat_id_input) if (chat_id_input.startswith("-") and chat_id_input[1:].isdigit()) else chat_id_input

        force_join_col.update_one(
            {"chat_id": chat_id},
            {
                "$set": {
                    "chat_id": chat_id,
                    "title": title,
                    "link": link
                }
            },
            upsert=True
        )

        await update.message.reply_text(
            f"✅ **Must Join လင့်ခ် အောင်မြင်စွာ သိမ်းဆည်းပြီးပါပြီ!**\n\n"
            f"📢 **Chat ID:** `{chat_id}`\n"
            f"🏷️ **Title:** `{title}`\n"
            f"🔗 **Link:** `{link}`",
            parse_mode="Markdown"
        )
    except Exception:
        await update.message.reply_text(
            "⚠️ **အသုံးပြုပုံ မှားယွင်းနေပါသည်။**\n\n"
            "**Format:** `/addjoin [Chat ID သို့မဟုတ် @Username] | [Title] | [Link]`\n"
            "**ဥပမာ:** `/addjoin @NexusCatchNews | 📢 News Channel | https://t.me/NexusCatchNews`",
            parse_mode="Markdown"
        )


# =========================================================
# ၃။ Force Join Middleware (အသုံးပြုသူများ မဖြစ်မနေ Join ရန် စစ်ဆေးခြင်း)
# =========================================================
async def force_join_middleware(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_user or not update.effective_message:
        return
    
    user_id = update.effective_user.id
    if user_id in ADMIN_IDS:
        return

    joined = await check_must_join(update, context)
    if not joined:
        raise ApplicationHandlerStop()


def get_force_join_handlers():
    return [
        CommandHandler("addjoin", add_must_join)
    ]
