from telegram import Update
from telegram.ext import ContextTypes
from database import inventory_col, users_col

async def gift_card(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    
    if not context.args or len(context.args) < 2:
        await update.message.reply_text("⚠️ ပုံစံမှန်ကန်စွာ ရေးပါ (ဥပမာ - `/gift c001 123456789`)")
        return

    card_id = context.args[0]
    try:
        receiver_id = int(context.args[1])
    except ValueError:
        await update.message.reply_text("❌ Receiver User ID သည် နံပါတ်ဖြစ်ရပါမည်။")
        return

    if user.id == receiver_id:
        await update.message.reply_text("❌ မိမိကိုယ်ကို ကတ်လက်ဆောင်ပေး၍ မရပါ။")
        return

    card = inventory_col.find_one({"user_id": user.id, "card_id": card_id})
    if not card:
        await update.message.reply_text("❌ သင့်ထံတွင် ဤ Card ID ရှိသော ကတ် မရှိပါ။")
        return

    receiver = users_col.find_one({"user_id": receiver_id})
    if not receiver:
        await update.message.reply_text("❌ လက်ခံမည့်သူကို ဒေတာဘေ့စ်ထဲတွင် မတွေ့ရပါ။ (သူတို့လည်း /start လုပ်ထားရပါမည်)")
        return

    inventory_col.update_one(
        {"_id": card["_id"]},
        {"$set": {"user_id": receiver_id}}
    )

    await update.message.reply_text(
        f"🎁 အောင်မြင်ပါပြီ! `{card['name']}` ကတ်ကို **{receiver.get('username', 'User')}** ထံသို့ လက်ဆောင်ပေးအပ်လိုက်ပါပြီ။",
        parse_mode="Markdown"
    )
