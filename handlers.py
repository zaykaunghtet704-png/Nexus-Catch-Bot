from telegram import Update
from telegram.ext import ContextTypes
from config import OWNER_ID, OWNER_USERNAME
from keyboards import get_start_keyboard, get_force_join_keyboard, get_owner_approval_keyboard
from services import check_force_join
from database import get_db

POWER_FOOTER = "\n\n⚡ *Powered by 'maybe'*"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat = update.effective_chat
    
    # 1. Group member count check (Must be >= 50)
    if chat.type in ["group", "supergroup"]:
        member_count = await chat.get_member_count()
        if member_count < 50:
            await update.message.reply_text(
                f"⚠️ *ဤ Group တွင် အဖွဲ့ဝင်ဦးရေ {member_count} ဦးသာ ရှိသေးပါသည် (အနည်းဆုံး ၅၀ ဦး လိုအပ်ပါသည်)* ❌\n\n"
                f"ကျေးဇူးပြု၍ အုံနာထံ ခွင့်တောင်းပါရှင်။ ID: `{OWNER_ID}`",
                parse_mode="Markdown",
                reply_markup=get_owner_approval_keyboard()
            )
            return

    # 2. Force Join Check
    # (Note: Replace with actual channel/group chat IDs or usernames for verification)
    joined = True # Simplified check placeholder
    if not joined:
        await update.message.reply_text(
            "✨ *ဘော့ကို စတင်အသုံးပြုရန် ကျေးဇူးပြု၍ အောက်ပါလင့်ခ်များကို အရင်ဆုံး ဂျွိုင်းပေးပါရှင်* 👇",
            parse_mode="Markdown",
            reply_markup=get_force_join_keyboard()
        )
        return

    welcome_text = (
        f"✨ **မင်္ဂလာပါရှင် Mr/Ms. {user.first_name}** ✨\n\n"
        "💎 Telegram ၏ အမိုက်ဆုံး **Ultimate Card & Gacha Bot** မှ ကြိုဆိုပါတယ်ရှင်။\n"
        "အောက်ပါ မီနူးများမှတစ်ဆင့် ကဒ်များ စုဆောင်းခြင်း၊ တိုက်ခိုက်ခြင်းများ ပြုလုပ်နိုင်ပါပြီ။"
        f"{POWER_FOOTER}"
    )
    await update.message.reply_text(welcome_text, parse_mode="Markdown", reply_markup=get_start_keyboard("my"))

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_msg = (
        "📖 **Ultimate Card Bot - Help & Commands** 📖\n\n"
        "🌟 `/start` - ပင်မ မီနူးနှင့် ကြိုဆိုချက်များ\n"
        "🌟 `/harem` - ကိုယ်ပိုင်ကဒ်စုဆောင်းမှုများကို ကြည့်ရန်\n"
        "🌟 `/search` - ဒေတာဘေ့စ်ထဲရှိ ကဒ်များ ရှာဖွေရန်\n"
        "🌟 `/profile` - ကိုယ်ပိုင် ပရိုဖိုင်နှင့် ငွေကြေးစစ်ဆေးရန်\n"
        "🌟 `/daily` - နေ့စဥ် Coins ၅၀၀ ရယူရန်\n"
        "🌟 `/claim` - ကျပန်းကဒ် တစ်စောင် အခမဲ့ထုတ်ရန်\n"
        "🌟 `/market` - ကဒ်ဈေးကွက် ကြည့်ရှုရန်\n"
        f"{POWER_FOOTER}"
    )
    await update.message.reply_text(help_msg, parse_mode="Markdown", reply_markup=get_start_keyboard("my"))

async def profile_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT coins FROM users WHERE user_id = ?", (user.id,))
    row = cursor.fetchone()
    coins = row[0] if row else 500
    
    profile_text = (
        f"👤 **User Profile: {user.first_name}**\n\n"
        f"💰 Coins: `{coins}` 🪙\n"
        f"🎒 Total Cards: `0`\n"
        f"🌍 Global Rank: `#1`\n"
        f"{POWER_FOOTER}"
    )
    await update.message.reply_text(profile_text, parse_mode="Markdown")
