from pymongo import ReturnDocument
from telegram import Update
from telegram.constants import ParseMode, ChatType
from telegram.ext import CommandHandler, CallbackContext
from waifu import application, user_totals_collection, OWNER_ID, sudo_users
from waifu.config import Config

_MIN, _MAX = 30, 10_000


async def _is_admin(update: Update, context: CallbackContext) -> bool:
    # Chat type စစ်ဆေးခြင်း
    if update.effective_chat.type == ChatType.PRIVATE:
        return False
        
    user_id = update.effective_user.id
    # Owner သို့မဟုတ် Sudo User ဖြစ်ပါက တိုက်ရိုက် Admin အဖြစ် သတ်မှတ်မည်
    if user_id == OWNER_ID or user_id in sudo_users:
        return True

    try:
        m = await context.bot.get_chat_member(update.effective_chat.id, user_id)
        return m.status in ("administrator", "creator")
    except Exception:
        return False


async def get_freq(chat_id: int) -> int:
    doc = await user_totals_collection.find_one({"chat_id": chat_id})
    return int(doc["message_frequency"]) if doc and "message_frequency" in doc else Config.DEFAULT_MSG_FREQUENCY


async def changetime(update: Update, context: CallbackContext) -> None:
    if update.effective_chat.type == ChatType.PRIVATE:
        await update.message.reply_text("❌ ဒီ Command ကို Group ထဲတွင်သာ အသုံးပြုနိုင်ပါသည်။")
        return

    if not await _is_admin(update, context):
        await update.message.reply_text("❌ Group Admin များသာ အသုံးပြုနိုင်ပါသည်။")
        return

    if not context.args or not context.args[0].lstrip("-").isdigit():
        cur = await get_freq(update.effective_chat.id)
        await update.message.reply_text(
            f"📋 **လက်ရှိ Drop အကြိမ်ရေ:** စာ <b>{cur}</b> စောင်းလျှင် ၁ ကြိမ်\n\n"
            f"<b>အသုံးပြုနည်း:</b> <code>/changetime <{_MIN}–{_MAX}></code>\n"
            f"<b>မူလအတိုင်း ပြန်ထားရန်:</b> <code>/resettime</code>",
            parse_mode=ParseMode.HTML,
        )
        return

    n = int(context.args[0])
    if n < _MIN:
        await update.message.reply_text(f"❌ အနည်းဆုံး စာအစောင်ရေ {_MIN} သတ်မှတ်ပေးပါ။")
        return
    if n > _MAX:
        await update.message.reply_text(f"❌ အများဆုံး စာအစောင်ရေ {_MAX} ထက် မပိုရပါ။")
        return

    old = await get_freq(update.effective_chat.id)
    await user_totals_collection.find_one_and_update(
        {"chat_id": update.effective_chat.id},
        {"$set": {"message_frequency": n}},
        upsert=True,
        return_document=ReturnDocument.AFTER,
    )
    await update.message.reply_text(
        f"✅ Drop frequency အောင်မြင်စွာ ပြောင်းလဲပြီးပါပြီ:\n<b>{old}</b> → <b>{n}</b> messages",
        parse_mode=ParseMode.HTML,
    )


async def resettime(update: Update, context: CallbackContext) -> None:
    if update.effective_chat.type == ChatType.PRIVATE:
        await update.message.reply_text("❌ ဒီ Command ကို Group ထဲတွင်သာ အသုံးပြုနိုင်ပါသည်။")
        return

    if not await _is_admin(update, context):
        await update.message.reply_text("❌ Group Admin များသာ အသုံးပြုနိုင်ပါသည်။")
        return

    await user_totals_collection.update_one(
        {"chat_id": update.effective_chat.id},
        {"$unset": {"message_frequency": ""}},
    )
    await update.message.reply_text(
        f"✅ Default drop frequency အဖြစ် စာ <b>{Config.DEFAULT_MSG_FREQUENCY}</b> စောင်လျှင် ၁ ကြိမ်သို့ ပြန်လည်ပြင်ဆင်ပြီးပါပြီ။",
        parse_mode=ParseMode.HTML,
    )


application.add_handler(CommandHandler("changetime", changetime))
application.add_handler(CommandHandler("resettime", resettime))
