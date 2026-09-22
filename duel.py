import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database import inventory_col

async def start_duel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    
    user_cards = list(inventory_col.find({"user_id": user.id}))
    if not user_cards:
        await update.message.reply_text("❌ သင့်တွင် Duel ထိုးရန် ကတ် တစ်ကတ်မှ မရှိသေးပါ။")
        return

    my_card = random.choice(user_cards)

    keyboard = [
        [InlineKeyboardButton("⚔️ လက်ခံမည် (Accept Duel)", callback_data=f"accept_duel_{user.id}_{my_card['card_id']}")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        f"⚔️ **{user.first_name}** မှ Waifu Duel (တိုက်ပွဲ) စိန်ခေါ်လိုက်ပါပြီ!\n\n"
        f"🌸 အသုံးပြုမည့်ကတ်: **{my_card['name']}** (`{my_card['rarity']}`)\n"
        f"တိုက်ပွဲဝင်ရန် အောက်ပါခလုတ်ကို နှိပ်ပါ -",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )
