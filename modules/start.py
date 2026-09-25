"""
modules/start.py - Start & Help Module
"""
from datetime import datetime
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes
from database import chats_col, users_col

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat = update.effective_chat

    users_col.update_one(
        {"user_id": user.id},
        {
            "$set": {"username": user.username, "first_name": user.first_name},
            "$setOnInsert": {
                "balance": 500,
                "gems": 10,
                "xp": 0,
                "is_vip": False,
                "is_gbanned": False,
                "joined_at": datetime.utcnow()
            }
        },
        upsert=True
    )

    if chat.type == "private":
        keyboard = [
            [InlineKeyboardButton("➕ Add Me To Group", url=f"https://t.me/{context.bot.username}?startgroup=true")],
            [InlineKeyboardButton("📖 Help Menu", callback_data="help_menu"), InlineKeyboardButton("💎 Shop", callback_data="shop_menu")]
        ]
        text = (
            f"👋 မင်္ဂလာပါ <b>{user.first_name}</b>!\n\n"
            f"🃏 ဤသည်မှာ Anime Character ကတ်များ ဖမ်းဆီးခြင်း၊ စုဆောင်းခြင်းနှင့် "
            f"Collector များ ယှဉ်ပြိုင်ကစားနိုင်သော <b>Nexus Catch Bot</b> ဖြစ်ပါသည်။"
        )
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)
    else:
        chats_col.update_one({"chat_id": chat.id}, {"$set": {"chat_title": chat.title}}, upsert=True)
        await update.message.reply_text("🤖 <b>Nexus Catch Bot Active!</b> ကတ်များ ဖမ်းဆီးရန် အဆင်သင့်ဖြစ်ပါပြီ။", parse_mode=ParseMode.HTML)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "📖 <b>NEXUS CATCH BOT - HELP MENU</b>\n"
        "─────────────────────────\n"
        "• `/start` - Bot ကို စတင်ရန်\n"
        "• `/profile` - မိမိ Profile နှင့် Stats ကြည့်ရန်\n"
        "• `/catch` - Group ထဲတွင် ကတ်ဖမ်းရန်\n"
        "• `/collection` - ပိုင်ဆိုင်သမျှ ကတ်များကြည့်ရန်\n"
        "• `/daily` - နေ့စဉ် ဆုလာဘ် (Coins/Gems) ရယူရန်\n"
        "• `/leaderboard` - Top Collectors စာရင်းကြည့်ရန်\n"
        "• `/shop` - Item နှင့် Card Packs ဝယ်ရန်"
    )
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)
