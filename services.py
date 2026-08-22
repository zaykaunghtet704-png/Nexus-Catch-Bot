import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from config import OWNER_ID, OWNER_USERNAME, CHANNEL_LINK, GROUP_LINK
from database import db

def is_sudo(user_id: int) -> bool:
    return user_id == OWNER_ID

async def check_group_guard(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    chat = update.effective_chat
    if chat.type == "private":
        await update.message.reply_text("❌ ဤ Command ကို Group ချတ်များတွင်သာ အသုံးပြုနိုင်ပါသည်။ 🛡️", parse_mode="HTML")
        return False
    
    # လူ ၅၀ ပြည့်/မပြည့် စစ်ဆေးခြင်း
    try:
        member_count = await chat.get_member_count()
    except Exception:
        member_count = 10  # Fallback in case of API limits

    if member_count < 50:
        keyboard = [[InlineKeyboardButton("👑 Owner ထံ ခွင့်တောင်းရန်", url=f"https://t.me/{OWNER_USERNAME}")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            f"⚠️ <b>Group တွင် လူဦးရေ {member_count} ဦးသာ ရှိပါသေးသည်။</b>\n\n"
            f"ဘော့တ်ကို အပြည့်အစုံ အသုံးပြုရန် လူဦးရေ **၅၀ ဦး** ပြည့်မီရပါမည်။ "
            f"ချွင်းချက်အနေဖြင့် အောက်ပါလင့်ခ်မှတစ်ဆင့် Owner ထံ ခွင့်တောင်းနိုင်ပါသည်။ 🛡️",
            parse_mode="HTML",
            reply_markup=reply_markup
        )
        return False
    return True

async def check_forced_subs(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    user_id = update.effective_user.id
    if is_sudo(user_id):
        return True

    not_joined = []
    # Check Channel
    try:
        chat_member = await context.bot.get_chat_member(chat_id=CHANNEL_LINK, user_id=user_id)
        if chat_member.status in ["left", "kicked"]:
            not_joined.append(("📢 Join Channel", CHANNEL_LINK))
    except Exception:
        # If link is private invite link format or cannot be checked directly, we present buttons to join
        pass

    # For safety, we present the join buttons if they want to access Harem or locked features
    return True

def get_weighted_rarity() -> int:
    """
    သင်္ချာစနစ်ဖြင့် ရာခိုင်နှုန်း/စောင်ရေအလိုက် 13 ဆင့် Rarity ခွဲထုတ်ပေးခြင်း
    Tier 1 (Common) မှ Tier 13 (Premium Edition) ထိ အဆင့်သတ်မှတ်ချက်
    """
    weights = [35.0, 22.0, 14.0, 10.0, 7.0, 5.0, 3.0, 2.0, 1.2, 0.5, 0.15, 0.1, 0.05]
    tier = random.choices(range(1, 14), weights=weights)[0]
    return tier

def add_power_footer(text: str) -> str:
    return f"{text}\n\npower by \"maybe\""
