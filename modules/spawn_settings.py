from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import CommandHandler, ContextTypes

try:
    from config import OWNER_ID
except ImportError:
    OWNER_ID = 0

from database import db

chats_col = db["chats"]

def _is_owner(user_id: int) -> bool:
    return user_id == OWNER_ID

async def set_spawn_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Bot Owner သာ Group ၏ Spawn Threshold (စာစောင် အရေအတွက်) ကို ပြောင်းလဲနိုင်သည်"""
    user_id = update.effective_user.id
    chat = update.effective_chat

    if not _is_owner(user_id):
        await update.message.reply_text("❌ ဤ Command အား Bot Owner တစ်ဦးတည်းသာ အသုံးပြုနိုင်ပါသည်။")
        return

    if not context.args or not context.args[0].isdigit():
        await update.message.reply_text(
            "❌ <b>အသုံးပြုပုံ မှားယွင်းနေပါသည်။</b>\n\n"
            "<code>/setspawn [စာစောင်အရေအတွက်]</code> သို့မဟုတ် <code>/changetime [စာစောင်အရေအတွက်]</code>\n"
            "ဥပမာ: <code>/setspawn 50</code>",
            parse_mode=ParseMode.HTML
        )
        return

    new_threshold = int(context.args[0])
    if new_threshold < 5:
        await update.message.reply_text("❌ စာစောင်အရေအတွက်သည် အနည်းဆုံး ၅ စောင် အထက် ဖြစ်ရပါမည်။")
        return

    try:
        chats_col.update_one(
            {"chat_id": chat.id},
            {"$set": {"spawn_threshold": new_threshold}},
            upsert=True
        )
        await update.message.reply_text(
            f"✅ <b>Spawn Settings ပြောင်းလဲပြီးပါပြီ!</b>\n\n"
            f"ယခု Group အတွက် စာစောင် <b>{new_threshold}</b> စောင် ပြည့်တိုင်း Character ကတ်တစ်ကတ် အလိုအလျောက် ပေါ်လာပါမည်။",
            parse_mode=ParseMode.HTML
        )
    except Exception as e:
        await update.message.reply_text(f"❌ Database error: {e}")

def get_spawn_settings_handlers():
    return [
        CommandHandler(["setspawn", "changetime"], set_spawn_command, block=False)
    ]
