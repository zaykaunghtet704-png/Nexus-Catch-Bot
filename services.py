from telegram import Update, ChatMember
from telegram.ext import ContextTypes
from config import OWNER_ID, REQUIRED_CHANNELS
from database import db

async def check_force_join(user_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
    for ch in REQUIRED_CHANNELS:
        try:
            member = await context.bot.get_chat_member(chat_id=ch["chat_id"], user_id=user_id)
            if member.status in [ChatMember.LEFT, ChatMember.BAN]:
                return False
        except Exception:
            pass
    return True

async def check_group_guard(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    chat = update.effective_chat
    if chat.type == 'private':
        return True

    user_id = update.effective_user.id
    if user_id == OWNER_ID:
        return True

    db.cursor.execute("SELECT * FROM approved_groups WHERE chat_id = ?", (chat.id,))
    if not db.cursor.fetchone():
        await update.message.reply_text("⚠️ ဤ Group တွင် ဘော့တ်သုံးခွင့်ကို Owner မှ ဖွင့်လှစ်ပေးထားခြင်း မရှိသေးပါ။")
        return False

    members = await chat.get_member_count()
    if members < 50:
        await update.message.reply_text(f"⚠️ ဘော့တ်အသုံးပြုရန် Group တွင် အနည်းဆုံး လူ ၅၀ ရှိရပါမည်။ (လက်ရှိ: {members} ယောက်)")
        return False

    bot_member = await chat.get_chat_member(context.bot.id)
    if bot_member.status != ChatMember.ADMINISTRATOR:
        await update.message.reply_text("⚠️ ဘော့တ်ကို အသုံးပြုရန် Group တွင် အင်မတန် အက်မင် (Admin) ပေးထားရပါမည်။")
        return False

    return True

def is_sudo(user_id: int) -> bool:
    if user_id == OWNER_ID:
        return True
    db.cursor.execute("SELECT user_id FROM sudo_users WHERE user_id = ?", (user_id,))
    return db.cursor.fetchone() is not None
