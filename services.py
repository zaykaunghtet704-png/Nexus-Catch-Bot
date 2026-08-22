from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from config import OWNER_ID, OWNER_USERNAME, FORCE_JOIN_CHANNELS

async def check_group_member_count(update, context):
    chat = update.effective_chat
    if chat.type in ["group", "supergroup"]:
        try:
            member_count = await context.bot.get_chat_member_count(chat.id)
            if member_count < 50:
                keyboard = [[InlineKeyboardButton("👑 Owner သို့ ခွင့်တောင်းရန်", url=f"https://t.me/{OWNER_USERNAME}")]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await update.message.reply_text(
                    f"❌ ဤဂရုတွင် လူဦးရေ {member_count} ယောက်သာ ရှိသေးပါသည် ဆော့ရန် လူဦးရေ 50 ပြည့်ရန် လိုအပ်ပါသည်။ (Owner ID: {OWNER_ID})\n\n"
                    f"ကျေးဇူးပြု၍ အုံနာထံသို့ ခွင့်တောင်းပါ။",
                    reply_markup=reply_markup
                )
                return False
        except Exception:
            pass
    return True

async def check_force_join(update, context):
    user_id = update.effective_user.id
    # Owner အတွက် Force Join ဖြတ်ကျော်ခွင့်ပေးနိုင်
    if user_id == OWNER_ID:
        return True
        
    for channel in FORCE_JOIN_CHANNELS:
        # ဤနေရာတွင် User က channel/group ကို joinထားခြင်းရှိမရှိ စစ်ဆေးသည့် logic ထည့်နိုင်ပါသည်။
        pass
    return True
