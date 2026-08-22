from telegram import InlineKeyboardButton, InlineKeyboardMarkup

async def check_group_constraints(update, context):
    # လူ 50 ပြည့်မှ သုံးခွင့်ပေးသည့် စနစ်
    count = await update.effective_chat.get_member_count()
    if count < 50:
        keyboard = [[InlineKeyboardButton("Contact Owner", url=f"t.me/{OWNER_USERNAME.replace('@','')}?start=request")]]
        await update.message.reply_text("❌ ဤ Group တွင် အဖွဲ့ဝင် ၅၀ ပြည့်မှသာ Bot ကို သုံးခွင့်ရှိပါသည်။", reply_markup=InlineKeyboardMarkup(keyboard))
        return False
    return True
