import os
import sqlite3
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, ApplicationHandlerStop

# ---------------------------------------------------------
# SQLite Database Setup (Local ဖိုင်ဖြင့် သိမ်းဆည်းမည်)
# ---------------------------------------------------------
DB_FILE = "bot_database.db"

def init_db():
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS force_joins (
                chat_id TEXT PRIMARY KEY,
                title TEXT,
                link TEXT
            )
        ''')
        conn.commit()
        conn.close()
        print("✅ Force Join Module: SQLite Database Connected Successfully!")
    except Exception as e:
        print(f"❌ SQLite Initialization Error: {e}")

init_db()

# ---------------------------------------------------------
# Admin များ သတ်မှတ်ခြင်း
# ---------------------------------------------------------
env_admins = os.getenv("ADMIN_IDS", "")
ADMIN_IDS = [int(x.strip()) for x in env_admins.split(",") if x.strip().isdigit()]

env_owner = os.getenv("OWNER_ID", "")
if env_owner.strip().isdigit():
    ADMIN_IDS.append(int(env_owner.strip()))

HARDCODED_OWNER_ID = 7974865879 
if HARDCODED_OWNER_ID not in ADMIN_IDS:
    ADMIN_IDS.append(HARDCODED_OWNER_ID)


# =========================================================
# ၁။ Force Join စစ်ဆေးသည့် Function
# =========================================================
async def check_must_join(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT chat_id, title, link FROM force_joins")
        rows = cursor.fetchall()
        conn.close()
    except Exception:
        return True

    if not rows:
        return True

    user_id = update.effective_user.id
    bot = context.bot
    not_joined_buttons = []

    for chat_id_val, title, link in rows:
        try:
            target_chat = int(chat_id_val) if (chat_id_val.startswith("-") or chat_id_val.isdigit()) else chat_id_val
            member = await bot.get_chat_member(target_chat, user_id)
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
# ၂။ /addjoin Command
# =========================================================
async def add_must_join(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("❌ Owner/Admin များသာ အသုံးပြုနိုင်ပါသည်။")
        return

    try:
        args = " ".join(context.args)
        parts = [p.strip() for p in args.split("|")]
        if len(parts) < 3:
            raise ValueError()

        chat_id_input = parts[0]
        title = parts[1]
        link = parts[2]

        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO force_joins (chat_id, title, link)
            VALUES (?, ?, ?)
        ''', (str(chat_id_input), title, link))
        conn.commit()
        conn.close()

        await update.message.reply_text(
            f"✅ **Must Join လင့်ခ် အောင်မြင်စွာ သိမ်းဆည်းပြီးပါပြီ!**\n\n"
            f"📢 **Chat ID:** `{chat_id_input}`\n"
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
# ၃။ Force Join Middleware
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
