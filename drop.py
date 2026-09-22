import random
from telegram import Update
from telegram.ext import ContextTypes
from database import cards_col, inventory_col

active_drops = {}

async def waifu_drop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    
    all_cards = list(cards_col.find({}))
    if not all_cards:
        await update.message.reply_text("လက်တလော ကတ်များ မရှိသေးပါ။")
        return

    card = random.choice(all_cards)
    active_drops[chat_id] = card['name'].lower()

    media_url = card.get('image_url', '')
    drop_text = (
        f"✨ **WAIFU DROP အသစ် ကျလာပါပြီ!** ✨\n\n"
        f"🌸 အမည်: **???** (ခန့်မှန်းရန် `/guess [နာမည်]` ကိုသုံးပါ)\n"
        f"📺 အန်နီမဲ: {card['anime']}\n"
        f"⭐ ရှားပါးမှု: {card['rarity']}"
    )

    # ပုံ သို့မဟုတ် ဗီဒီယို Link ဟုတ်မဟုတ် စစ်ဆေးပြီး ပို့ခြင်း
    if media_url.endswith(('.mp4', '.gif')):
        await update.message.reply_animation(animation=media_url, caption=drop_text, parse_mode="Markdown")
    elif media_url.startswith('http'):
        await update.message.reply_photo(photo=media_url, caption=drop_text, parse_mode="Markdown")
    else:
        await update.message.reply_text(drop_text, parse_mode="Markdown")

async def guess_card(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user = update.effective_user
    
    if chat_id not in active_drops:
        await update.message.reply_text("ဒီဂရုထဲမှာ လက်ရှိ ဖမ်းစရာ ကတ် မရှိသေးပါ။")
        return

    if not context.args:
        await update.message.reply_text("ကျေးဇူးပြု၍ ကတ်အမည်ကို တွဲ၍ ရေးပါ (ဥပမာ - `/guess Rem`)")
        return

    guessed_name = " ".join(context.args).lower()
    correct_name = active_drops[chat_id]

    if guessed_name == correct_name:
        card_name = active_drops[chat_id].title()
        card_data = cards_col.find_one({"name": {"$regex": f"^{card_name}$", "$options": "i"}})
        
        if card_data:
            inventory_col.insert_one({
                "user_id": user.id,
                "card_id": card_data["card_id"],
                "name": card_data["name"],
                "anime": card_data["anime"],
                "rarity": card_data["rarity"]
            })

        del active_drops[chat_id]
        
        await update.message.reply_text(
            f"🎉 ဂုဏ်ယူပါတယ် {user.first_name} ရေ! `{card_name}` ကတ်ကို အောင်မြင်စွာ ဖမ်းယူနိုင်ခဲ့ပါပြီ။",
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text("❌ နာမည် မမှန်သေးပါ၊ ထပ်ကြိုးစားကြည့်ပါ။")
