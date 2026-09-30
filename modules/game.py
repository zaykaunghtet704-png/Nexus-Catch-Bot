import random
from html import escape
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters

from database import cards_col, inventory_col, users_col

# Group တစ်ခုစီ၏ စာရိုက်ရေတွက်မှု Counter
CHAT_COUNTERS = {}
SPAWNED_CARDS = {}
SPAWN_THRESHOLD = 100  # စာစောင် ၁၀၀ ပြည့်တိုင်း ကတ်တစ်ကတ် ပေါ်မည်

async def message_counter(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Group ထဲတွင် စာရိုက်ပါက ကတ်အလိုအလျောက် ပေါ်စေမည့် Logic"""
    if not update.effective_chat or update.effective_chat.type == "private":
        return

    chat_id = update.effective_chat.id
    CHAT_COUNTERS[chat_id] = CHAT_COUNTERS.get(chat_id, 0) + 1

    if CHAT_COUNTERS[chat_id] >= SPAWN_THRESHOLD:
        CHAT_COUNTERS[chat_id] = 0
        
        try:
            pipeline = [{"$sample": {"size": 1}}]
            random_cards = list(cards_col.aggregate(pipeline))
        except Exception:
            random_cards = []

        if not random_cards:
            return

        card = random_cards[0]
        SPAWNED_CARDS[chat_id] = card

        caption = (
            f"🍁 <b>A WILD CHARACTER APPEARED!</b>\n\n"
            f"📺 <b>Anime:</b> {escape(card.get('anime', 'Unknown'))}\n"
            f"🎴 <b>Rarity:</b> {card.get('rarity', 'Common')}\n\n"
            f"ဖမ်းယူရန် <code>/catch [Character Name]</code> ကို ရိုက်ပါ။"
        )

        try:
            await context.bot.send_photo(
                chat_id=chat_id,
                photo=card.get("img_url"),
                caption=caption,
                parse_mode=ParseMode.HTML
            )
        except Exception:
            pass

async def catch_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """ပေါ်နေသော ကတ်ကို ဖမ်းယူသည့် Command"""
    chat_id = update.effective_chat.id
    user = update.effective_user
    user_id = int(user.id)

    if chat_id not in SPAWNED_CARDS:
        await update.message.reply_text("❌ ဖမ်းယူရန် ကတ်မရှိသေးပါ။ စာများများ ရိုက်ပေးပါ!")
        return

    if not context.args:
        await update.message.reply_text("❌ ဖမ်းယူလိုသော Character အမည်ကို ထည့်သွင်းပါ!\nဥပမာ: <code>/catch Naruto</code>", parse_mode=ParseMode.HTML)
        return

    guess_name = " ".join(context.args).strip().lower()
    actual_card = SPAWNED_CARDS[chat_id]
    actual_name = actual_card.get("name", "").strip().lower()

    if guess_name == actual_name:
        del SPAWNED_CARDS[chat_id]

        inv_item = {
            "user_id": user_id,
            "card_id": actual_card.get("id"),
            "name": actual_card.get("name"),
            "anime": actual_card.get("anime"),
            "rarity": actual_card.get("rarity"),
            "img_url": actual_card.get("img_url")
        }
        try:
            inventory_col.insert_one(inv_item)
            users_col.update_one({"user_id": user_id}, {"$inc": {"coins": 100, "xp": 10}}, upsert=True)
        except Exception:
            pass

        await update.message.reply_text(
            f"🎉 <b>ဂုဏ်ယူပါတယ် {escape(user.first_name)}!</b>\n\n"
            f"<b>{actual_card['name']}</b> ({actual_card['rarity']}) ကို အောင်မြင်စွာ ဖမ်းယူနိုင်ခဲ့ပါပြီ!\n"
            f"💰 +100 Coins | ⚡ +10 XP ရရှိသည်။",
            parse_mode=ParseMode.HTML
        )
    else:
        await update.message.reply_text("❌ Character အမည် မှားယွင်းနေပါသည်။ ပြန်လည် ကြိုးစားပါ။")

async def collection_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/collection Command"""
    user_id = int(update.effective_user.id)
    try:
        count = inventory_col.count_documents({"user_id": user_id})
    except Exception:
        count = 0
    await update.message.reply_text(f"🎴 <b>သင့်ထံတွင် စုစုပေါင်း ကတ်ပေါင်း ({count}) ကတ် ရှိပါသည်။</b>", parse_mode=ParseMode.HTML)

async def leaderboard_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/leaderboard Command"""
    try:
        pipeline = [
            {"$group": {"_id": "$user_id", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 10}
        ]
        top_users = list(inventory_col.aggregate(pipeline))
    except Exception:
        top_users = []

    text = "🏆 <b>TOP 10 CARD COLLECTORS</b>\n⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n"
    for idx, u in enumerate(top_users, 1):
        text += f"{idx}. User ID: <code>{u['_id']}</code> — <b>{u['count']} Cards</b>\n"

    await update.message.reply_text(text, parse_mode=ParseMode.HTML)

def get_game_handlers():
    return [
        CommandHandler(["catch", "roll"], catch_command, block=False),
        CommandHandler("collection", collection_command, block=False),
        CommandHandler("leaderboard", leaderboard_command, block=False),
        MessageHandler(filters.TEXT & (~filters.COMMAND), message_counter, block=False)
    ]
