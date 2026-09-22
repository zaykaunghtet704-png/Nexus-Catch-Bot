from telegram import Update
from telegram.ext import ContextTypes
from database import inventory_col

async def view_harem(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id

    user_cards = list(inventory_col.find({"user_id": user_id}))

    if not user_cards:
        await update.message.reply_text("သင့်မှာ သိမ်းဆည်းထားတဲ့ Waifu ကတ် တစ်ကတ်မှ မရှိသေးပါ။ ကတ်များ ကျလာချိန်တွင် `/guess` ဖြင့် ဖမ်းယူပါ။")
        return

    harem_text = f"🎒 **{user.first_name} ၏ Waifu Harem စာရင်း 🎒\n\n"
    
    for index, card in enumerate(user_cards, 1):
        harem_text += f"{index}. ** ({card['anime']}) - `[{card['rarity']}]`\n"

    harem_text += f"\nစုစုပေါင်း ကတ်ပမာဏ: {len(user_cards)} ခု"

    await update.message.reply_text(harem_text, parse_mode="Markdown")
