import asyncio
import logging
import random
import time
from html import escape

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters

# သင့်ကိုယ်ပိုင် database နှင့် config ဖိုင်များမှ Import ပြုလုပ်ခြင်း
from database import (
    cards_col,
    users_col,
    inventory_col,
    chats_col,
    group_user_totals_col,
    top_global_groups_col,
)

try:
    from config import DROP_INTERVAL_MIN, DEFAULT_MSG_FREQUENCY
except ImportError:
    DROP_INTERVAL_MIN = 15
    DEFAULT_MSG_FREQUENCY = 100

logger = logging.getLogger(__name__)

# ── Per-chat Memory States ───────────────────────────────────────────────────
_active_char:      dict[int, dict]  = {}   # chat_id -> active card doc
_claimed:          dict[int, int]   = {}   # chat_id -> claimed user_id
_msg_counts:       dict[int, int]   = {}   # chat_id -> message count
_last_user:        dict[int, dict]  = {}   # chat_id -> {user_id, count}
_warned:           dict[int, float] = {}   # user_id -> warning timestamp
_sent_ids:         dict[int, list]  = {}   # chat_id -> list of recent card IDs
_registered_chats: set[int]         = set()

scheduler = AsyncIOScheduler(timezone="UTC")

# Guess အောင်မြင်ပါက ရရှိမည့် XP ပမာဏ
_XP_PER_GUESS = 50


# ── Helpers ───────────────────────────────────────────────────────────────────

async def _chat_frequency(chat_id: int) -> int:
    """Chat တစ်ခုချင်းစီ၏ Drop ကျမည့် Message အရေအတွက် Limit ကို ဆွဲထုတ်သည်။"""
    doc = await chats_col.find_one({"chat_id": chat_id})
    return int(doc["message_frequency"]) if doc and "message_frequency" in doc else DEFAULT_MSG_FREQUENCY


def _rolling_window_size(total_chars: int) -> int:
    """ထပ်ခါထပ်ခါ မကျစေရန် Rolling Window Size ကို စုစုပေါင်း ကတ်အရေအတွက်၏ ထက်ဝက် (အနည်းဆုံး ၂၀) သတ်မှတ်သည်။"""
    return max(20, total_chars // 2)


async def _send_drop(chat_id: int, bot) -> None:
    """Random ကတ်တစ်ခုကို ရွေးချယ်ပြီး Chat သို့ Drop ပေးပို့သည်။"""
    all_chars = await cards_col.find({}).to_list(length=5000)
    if not all_chars:
        logger.debug("Database ထဲတွင် Card များ မရှိသေးပါ — Drop ကို ကျော်လိုက်ပါသည် %s", chat_id)
        return

    window = _rolling_window_size(len(all_chars))
    sent   = _sent_ids.get(chat_id, [])

    # မကြာသေးမီက မကျသေးသော ကတ်များကို စစ်ထုတ်ခြင်း
    unsent = [c for c in all_chars if (c.get("card_id") or c.get("id")) not in sent]

    # ကတ်အားလုံး ကျပြီးပါက Rolling Window ကို Reset လုပ်ခြင်း
    if not unsent:
        _sent_ids[chat_id] = []
        unsent = all_chars
        logger.debug("Rolling window reset for chat %s", chat_id)

    char = random.choice(unsent)
    char_id = char.get("card_id") or char.get("id")

    # Rolling window ထဲသို့ ကတ်အသစ် ထည့်ခြင်း
    new_sent = sent + [char_id]
    _sent_ids[chat_id] = new_sent[-window:]

    # Active Character အဖြစ် သတ်မှတ်ခြင်း
    _active_char[chat_id] = char
    _claimed.pop(chat_id, None)

    try:
        await bot.send_photo(
            chat_id=chat_id,
            photo=char["img_url"],
            caption=(
                "✨ <b>A new character appeared!</b>\n\n"
                "<i>Use /guess [name] to add them to your harem!</i>"
            ),
            parse_mode=ParseMode.HTML,
        )
        logger.info("Drop sent to chat %s: %s", chat_id, char.get("name"))
    except Exception as e:
        _active_char.pop(chat_id, None)
        logger.warning("Drop send failed in chat %s: %s", chat_id, e)


# ── Scheduler ─────────────────────────────────────────────────────────────────

async def _timed_drop_job(bot) -> None:
    for chat_id in list(_registered_chats):
        await _send_drop(chat_id, bot)


def start_scheduler(bot) -> None:
    scheduler.add_job(
        _timed_drop_job,
        trigger=IntervalTrigger(minutes=DROP_INTERVAL_MIN),
        kwargs={"bot": bot},
        id="timed_drop",
        replace_existing=True,
    )
    if not scheduler.running:
        scheduler.start()
    logger.info("Drop scheduler started (Interval: %d mins)", DROP_INTERVAL_MIN)


# ── Message Counter & Anti-Spam ───────────────────────────────────────────────

async def message_counter(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.effective_chat or update.effective_chat.type == "private":
        return

    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    _registered_chats.add(chat_id)

    # Anti-spam: တစ်ဦးတည်း ၁၀ စာ ဆက်တိုက်ပို့ပါက ၁၀ မိနစ် Ignored လုပ်ခြင်း
    last = _last_user.get(chat_id)
    if last and last["user_id"] == user_id:
        last["count"] += 1
        if last["count"] >= 10:
            warned_at = _warned.get(user_id, 0)
            if time.time() - warned_at < 600:
                return
            _warned[user_id] = time.time()
            await update.message.reply_text(
                f"⚠️ {escape(update.effective_user.first_name)}, slow down!\n"
                f"Your messages will be ignored for 10 minutes."
            )
            return
    else:
        _last_user[chat_id] = {"user_id": user_id, "count": 1}

    _msg_counts[chat_id] = _msg_counts.get(chat_id, 0) + 1
    freq = await _chat_frequency(chat_id)
    if _msg_counts[chat_id] >= freq:
        _msg_counts[chat_id] = 0
        await _send_drop(chat_id, context.bot)


# ── /guess ────────────────────────────────────────────────────────────────────

async def guess(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id

    char = _active_char.get(chat_id)
    if not char:
        return

    if chat_id in _claimed:
        await update.message.reply_text("❌ အခြားသူတစ်ဦးမှ ဖမ်းယူသွားပြီးပါပြီ!")
        return

    user_guess = " ".join(context.args).strip().lower() if context.args else ""
    if not user_guess:
        await update.message.reply_text("အသုံးပြုပုံ: /guess <character name>")
        return

    # တားမြစ်ထားသော စာလုံးများ စစ်ဆေးခြင်း
    if any(bad in user_guess for bad in ("()", "&&", "||", "<script")):
        await update.message.reply_text("❌ Invalid characters in guess.")
        return

    # နာမည် စစ်ဆေးခြင်း (Full match သို့မဟုတ် Word match)
    char_name = char.get("name", "")
    name_parts = char_name.lower().split()
    correct = (
        sorted(name_parts) == sorted(user_guess.split())
        or any(part == user_guess for part in name_parts)
    )

    if not correct:
        await update.message.reply_text("❌ နာမည်မှားယွင်းနေပါသည်၊ ပြန်လည်ကြိုးစားပါ!")
        return

    # ── Correct Guess (Claim State ချက်ချင်းရှင်းထုတ်ခြင်း) ──────────────────
    _claimed[chat_id] = user_id
    _active_char.pop(chat_id, None)

    u = update.effective_user

    # 1. User document update / upsert
    await users_col.update_one(
        {"user_id": user_id},
        {
            "$inc": {"total_guesses": 1, "xp": _XP_PER_GUESS},
            "$set": {"username": u.username, "first_name": u.first_name},
            "$setOnInsert": {"coins": 0, "wins": 0, "favorites": []},
        },
        upsert=True,
    )

    # 2. Add character into inventory collection
    inv_item = dict(char)
    inv_item["user_id"] = user_id
    if "_id" in inv_item:
        del inv_item["_id"]
    await inventory_col.insert_one(inv_item)

    # 3. Group and Global totals update
    await group_user_totals_col.update_one(
        {"user_id": user_id, "group_id": chat_id},
        {"$set": {"username": u.username, "first_name": u.first_name}, "$inc": {"count": 1}},
        upsert=True,
    )
    await top_global_groups_col.update_one(
        {"group_id": chat_id},
        {"$set": {"group_name": update.effective_chat.title}, "$inc": {"count": 1}},
        upsert=True,
    )

    # ── Response ──────────────────────────────────────────────────────────────
    kb = InlineKeyboardMarkup([[
        InlineKeyboardButton(
            "📖 My Harem",
            switch_inline_query_current_chat=f"collection.{user_id}",
        )
    ]])
    await update.message.reply_text(
        f'🎉 <a href="tg://user?id={user_id}">{escape(u.first_name)}</a> guessed it!\n\n'
        f'🌸 <b>{escape(char_name)}</b>\n'
        f'📺 {escape(char.get("anime", "Unknown"))}\n'
        f'💎 {char.get("rarity", "⚪ Common")}\n\n'
        f'Added to your harem! +{_XP_PER_GUESS} XP ✨',
        parse_mode=ParseMode.HTML,
        reply_markup=kb,
    )


# ── /fav ──────────────────────────────────────────────────────────────────────

async def fav(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    if not context.args:
        await update.message.reply_text("အသုံးပြုပုံ: /fav <character_id>")
        return

    char_id = context.args[0]

    # Inventory ထဲတွင် ထို ကတ် ရှိမရှိ စစ်ဆေးခြင်း
    char = await inventory_col.find_one({
        "user_id": user_id,
        "$or": [{"card_id": char_id}, {"id": char_id}]
    })

    if not char:
        await update.message.reply_text("❌ ထို Character သည် သင့် Harem/Collection ထဲတွင် မရှိပါ။")
        return

    actual_id = char.get("card_id") or char.get("id")
    await users_col.update_one({"user_id": user_id}, {"$set": {"favorites": [actual_id]}})
    await update.message.reply_text(
        f"⭐ <b>{escape(char.get('name', 'Character'))}</b> ကို သင့် Favourite အဖြစ် သတ်မှတ်လိုက်ပါပြီ!",
        parse_mode=ParseMode.HTML,
    )


# ── Handlers များကို Main File သို့ လှမ်းပေးရန် ────────────────────────────────
def get_waifu_drop_handlers():
    return [
        CommandHandler(["guess", "protecc", "collect", "grab", "hunt"], guess, block=False),
        CommandHandler("fav", fav, block=False),
        MessageHandler(
            filters.TEXT & ~filters.COMMAND & filters.ChatType.GROUPS,
            message_counter,
            block=False,
        )
    ]
