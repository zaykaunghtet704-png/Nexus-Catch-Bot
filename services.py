import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from config import OWNER_ID, OWNER_USERNAME, CHANNEL_LINK, GROUP_LINK
from database import db

def is_sudo(user_id: int) -> bool:
    return user_id == OWNER_ID

def get_user_lang(user_id: int) -> str:
    db.cursor.execute("SELECT lang FROM users WHERE user_id = ?", (user_id,))
    res = db.cursor.fetchone()
    return res[0] if res else "my"

async def check_group_guard(update: Update, context) -> bool:
    chat = update.effective_chat
    if chat.type == "private":
        return True
    
    # ဤ Group အား Owner မှ ခွင့်ပြုထားပြီးသား (Bypass) ဟုတ်မဟုတ် စစ်ဆေးရန်
    db.cursor.execute("SELECT chat_id FROM allowed_groups WHERE chat_id = ?", (chat.id,))
    if db.cursor.fetchone():
        return True

    try:
        member_count = await chat.get_member_count()
    except Exception:
        member_count = 10

    if member_count < 50:
        keyboard = [[InlineKeyboardButton("👑 Owner ထံ ခွင့်တောင်းရန် / Ask Owner", url=f"https://t.me/{OWNER_USERNAME}")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            f"⚠️ <b>Group တွင် လူဦးရေ {member_count} ဦးသာ ရှိပါသေးသည်။ (Members: {member_count}/50)</b>\n\n"
            f"ဘော့တ်ကို အသုံးပြုရန် လူဦးရေ <b>၅၀ ဦး</b> ပြည့်မီရပါမည်။ သို့မဟုတ် Owner မှ `/allowgroup` ဖြင့် ဝင်ရောက်ခွင့်ပြုပေးရပါမည်။ 🛡️\n\n"
            f"power by \"maybe\"",
            parse_mode="HTML",
            reply_markup=reply_markup
        )
        return False
    return True

def get_weighted_rarity() -> int:
    weights = [35.0, 22.0, 14.0, 10.0, 7.0, 5.0, 3.0, 2.0, 1.2, 0.5, 0.15, 0.1, 0.05]
    tier = random.choices(range(1, 14), weights=weights)[0]
    return tier

def add_power_footer(text: str) -> str:
    return f"{text}\n\npower by \"maybe\""
