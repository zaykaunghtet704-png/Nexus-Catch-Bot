"""
NEXUS CATCH BOT
modules/game.py - Game Spawn, Catch & Collection Module
"""

import random
from html import escape
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters

from database import cards_col, inventory_col, users_col, chats_col

# Runtime Memory Trackers
SPAWNED_CARDS = {}

# Default Spawn Threshold (စာစောင် ၁၀၀ ပြည့်တိုင်း ပုံမှန်ထွက်မည်)
DEFAULT_SPAWN_THRESHOLD = 100

async def set_spawn_threshold(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Group တစ်ခုချင်းစီအတွက် ကတ်ထွက်မည့် စာစောင်ရေ သတ်မှတ်ရန် (/setspawn)"""
    chat = update.effective_chat
    user = update.effective_user

    if not chat or chat.type == "private":
        await update.message.reply_text("❌ ဤ Command ကို Group ထဲတွင်သာ အသုံးပြုနိုင်ပါသည်။")
        return

    # Admin ဟုတ်မဟုတ် စစ်ဆေးခြင်း
    try:
        member = await chat.get_member(user.id)
        if member.status not in ["creator", "administrator"] and user.id != 123456789: # Owner ID ထည့်နိုင်သည်
            await update.message.reply_text("❌ ဤ Command ကို Group Admin များသာ အသုံးပြုနိုင်ပါသည်။")
            return
    except Exception:
        pass

    if not context.args:
        await update.message.reply_text(
            "အသုံးပြုပုံ: <code>/setspawn [number]</code>\n"
            "ဥပမာ: <code>/setspawn 5</code> (စာ ၅ စောင်ပို့တိုင်း ကတ်ကျမည်)",
            parse_mode=ParseMode.HTML
        )
        return

    try:
        threshold = int(context.args[0])
        if threshold < 1:
            raise ValueError

        # Database ထဲတွင် Group ၏ spawn_rate သို့မဟုတ် threshold ကို သိမ်းဆည်းခြင်း
        chats_col.update_one(
            {"chat_id": chat.id},
            {"$set": {"spawn_threshold": threshold, "chat_title": chat.title or "Group Chat"}},
            upsert=True
        )

        await update.message.reply_text(
            f"✅ <b>Spawn Settings ပြောင်းလဲပြီးပါပြီ!</b>\n\n"
            f"ယခု Group အတွက် စာစောင် <b>{threshold}</b> စောင်ပြည့်တိုင်း Character ကတ်တလတ်တလတ် အလိုအလျောက် ပေါ်လာလိမ့်မည်။",
            parse_mode=ParseMode.HTML
        )
    except ValueError:
        await update.message.reply_text("❌ ကျေးဇူးပြု၍ မှန်ကန်သော ဂဏန်းအပေါင်းကိုသာ ထည့်သွင်းပါ။")

async def message_counter(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Group ထဲတွင် စာရိုက်ပါက ကတ်အလိုအလျောက် ပေါ်စေမည့် Logic"""
    if not update.effective_chat or update.effective_chat.type == "private":
        return

    chat_id = update.effective_chat.id
    
    # Database မှ Group ၏ သတ်မှတ်ထားသော Threshold ကို ယူခြင်း (မရှိလျှင် Default 100)
    chat_doc = chats_col.find_one({"chat_id": chat_id}) or {}
    threshold = chat_doc.get("spawn_threshold", DEFAULT_SPAWN_THRESHOLD)

    # Counter တိုးမြှင့်ခြင်း
    current_count = chat_doc.get("message_count", 0) + 1

    if current_count >= threshold:
        # Counter ကို 0 သို့ ပြန်ပြောင်းခြင်း
        chats_col.update_one({"chat_id": chat_id}, {"$set": {"message_count": 0}}, upsert=True)
        
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
            img_url = card.get("img_url") or card.get("image")
            if img_url:
                await context.bot.send_photo(
                    chat_id=chat_id,
                    photo=img_url,
                    caption=caption,
                    parse_mode=ParseMode.HTML
                )
            else:
                await context.bot.send_message(chat_id=chat_id, text=caption, parse_mode=ParseMode.HTML)
        except Exception:
            pass
    else:
        # လက်ရှိ Count ကို DB ထဲ ဆက်သိမ်းထားမည်
        chats_col.update_one({"chat_id": chat_id}, {"$set": {"message_count": current_count}}, upsert=True)

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

        card_id = actual_card.get("card_id") or actual_card.get("id")
        inv_item = {
            "user_id": user_id,
            "card_id": card_id,
            "name": actual_card.get("name"),
            "anime": actual_card.get("anime"),
            "rarity": actual_card.get("rarity"),
            "img_url": actual_card.get("img_url") or actual_card.get("image")
        }
        try:
            inventory_col.insert_one(inv_item)
            users_col.update_one({"user_id": user_id}, {"$inc": {"balance": 100, "xp": 10}}, upsert=True)
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
        CommandHandler("setspawn", set_spawn_threshold, block=False),
        CommandHandler(["catch", "roll"], catch_command, block=False),
        CommandHandler("collection", collection_command, block=False),
        CommandHandler("leaderboard", leaderboard_command, block=False),
        MessageHandler(filters.TEXT & (~filters.COMMAND) & (~filters.ChatType.PRIVATE), message_counter, block=False)
    ]
