from database import cards_col, users_col  # database.py မှ Collection များကို Import လုပ်ပါ
from telegram import Update
from telegram.ext import ContextTypes


# /fav <card_id>
async def fav(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if not context.args:
        await update.message.reply_text(
            "⚠️ Favorite လုပ်ချင်သော Card ID ကို ထည့်ပါ။\nဥပမာ - `/fav c001`",
            parse_mode="Markdown",
        )
        return

    card_id = context.args[0]

    # ကတ် Database ထဲမှာ ရှိမရှိ စစ်ပါ
    card = cards_col.find_one({"card_id": card_id})
    if not card:
        await update.message.reply_text("❌ ဒီလို Card ID မရှိပါ။")
        return

    # User ရဲ့ Favorite card ကို Database ထဲ Update လုပ်ပါ
    users_col.update_one(
        {"user_id": user_id}, {"$set": {"fav_card": card_id}}, upsert=True
    )

    await update.message.reply_text(
        f"⭐️ <b>{card['name']}</b> ({card['anime']}) ကို Favorite အဖြစ် သတ်မှတ်လိုက်ပါပြီ။",
        parse_mode="HTML",
    )


# /unfav
async def unfav(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    # User ရဲ့ Favorite card ကို ဖယ်ရှားပါ
    users_col.update_one({"user_id": user_id}, {"$unset": {"fav_card": ""}})

    await update.message.reply_text(
        "❌ Favorite ကတ်ကို အောင်မြင်စွာ ဖယ်ရှားလိုက်ပါပြီ။"
    )


# /search <card_name>
async def search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("⚠️ ရှာချင်သော ကတ်အမည်ကို ထည့်ပေးပါ။")
        return

    query = " ".join(context.args)

    # MongoDB ထဲမှာ Case-insensitive (စာလုံးကြီးသေး မလို) နာမည် ရှာပါ
    results = list(
        cards_col.find({"name": {"$regex": query, "$options": "i"}})
    )

    if not results:
        await update.message.reply_text(
            f"❌ '{query}' နဲ့ ပတ်သက်တဲ့ ကတ် မတွေ့ပါ။"
        )
        return

    text = f"🔍 <b>'{query}' အတွက် ရှာဖွေတွေ့ရှိချက်များ -</b>\n\n"
    for c in results[:10]:  # စာမျက်နှာ မရှည်စေရန် ၁၀ ခုပဲ ပြပါမည်
        text += f"• <b>{c['name']}</b> [{c['rarity']}] - ID: <code>{c['card_id']}</code> ({c['anime']})\n"

    await update.message.reply_text(text, parse_mode="HTML")


# /check <card_id>
async def check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text(
            "⚠️ စစ်ဆေးချင်သော Card ID ကို ထည့်ပေးပါ။\nဥပမာ - `/check c001`",
            parse_mode="Markdown",
        )
        return

    card_id = context.args[0]
    card = cards_col.find_one({"card_id": card_id})

    if not card:
        await update.message.reply_text("❌ Card ID မမှန်ကန်ပါ။")
        return

    caption = (
        f"🎴 <b>Card Info</b>\n\n"
        f"<b>Name:</b> {card['name']}\n"
        f"<b>Anime:</b> {card['anime']}\n"
        f"<b>Rarity:</b> {card['rarity']}\n"
        f"<b>ID:</b> <code>{card['card_id']}</code>"
    )

    # ကတ်၏ ပုံပါရှိပါက ပုံနှင့်တကွ ပြပေးပါမည်
    if "image_url" in card and card["image_url"]:
        await update.message.reply_photo(
            photo=card["image_url"], caption=caption, parse_mode="HTML"
        )
    else:
        await update.message.reply_text(caption, parse_mode="HTML")
