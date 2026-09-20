"""
modules/waifu_drop.py

Core game loop:
  - Message counter → threshold drop
  - APScheduler timed drop every N minutes
  - /guess to claim
  - /fav to favourite
  - Anti-spam (10 consecutive messages from same user → 10-min ignore)
"""
import asyncio
import random
import re
import time
from html import escape

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.ext import CallbackContext, CommandHandler, MessageHandler, filters

from waifu import (
    LOGGER,
    application,
    collection,
    group_user_totals_collection,
    top_global_groups_collection,
    user_collection,
    user_totals_collection,
)
from waifu.config import Config

# ── Per-chat in-memory state ──────────────────────────────────────────────────
_active_char: dict[int, dict] = {}  # chat_id → currently active character
_claimed: dict[int, int] = {}  # chat_id → user_id who claimed it
_msg_counts: dict[int, int] = {}  # chat_id → message counter
_last_user: dict[int, dict] = {}  # chat_id → {user_id, count}
_warned: dict[int, float] = {}  # user_id → timestamp of last warning
_sent_ids: dict[int, list] = {}  # chat_id → recently sent char IDs
_registered_chats: set[int] = set()

scheduler = AsyncIOScheduler(timezone="UTC")

# XP reward for a correct guess
_XP_PER_GUESS = 50


# ── Helpers ───────────────────────────────────────────────────────────────────

async def _chat_frequency(chat_id: int) -> int:
    doc = await user_totals_collection.find_one({"chat_id": chat_id})
    if doc and "message_frequency" in doc:
        try:
            return int(doc["message_frequency"])
        except (ValueError, TypeError):
            pass
    return getattr(Config, "DEFAULT_MSG_FREQUENCY", 100)


def _rolling_window_size(total_chars: int) -> int:
    """
    How many recently-sent IDs to remember before a character can reappear.
    Capped at half the catalogue (minimum 20) so even small DBs work properly.
    """
    return max(20, total_chars // 2) if total_chars > 0 else 20


async def _send_drop(chat_id: int, bot) -> None:
    """Pick a random unseen-recently character and post it to the chat."""
    # Projection to fetch only required fields and reduce memory usage
    all_chars = await collection.find(
        {}, {"id": 1, "name": 1, "anime": 1, "rarity": 1, "img_url": 1}
    ).to_list(length=5000)

    if not all_chars:
        LOGGER.debug("No characters in DB — skipping drop for chat %s", chat_id)
        return

    window = _rolling_window_size(len(all_chars))
    sent = _sent_ids.get(chat_id, [])

    # Characters not in the rolling window
    unsent = [c for c in all_chars if str(c["id"]) not in sent]

    # If every character has been seen recently, clear the window and start fresh
    if not unsent:
        _sent_ids[chat_id] = []
        unsent = all_chars
        LOGGER.debug("Sent-IDs window cleared for chat %s", chat_id)

    char = random.choice(unsent)
    char_id_str = str(char["id"])

    # Append to rolling window; trim to keep only the most recent `window` entries
    new_sent = sent + [char_id_str]
    _sent_ids[chat_id] = new_sent[-window:]

    # Register as the active drop — clear any previous claim state
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
        LOGGER.info(
            "Drop sent to chat %s: %s (%s)",
            chat_id,
            char.get("name"),
            char.get("rarity", "?"),
        )
    except Exception as e:
        # Roll back state if post fails
        _active_char.pop(chat_id, None)
        LOGGER.warning("Drop failed in chat %s: %s", chat_id, e)


# ── Scheduler ─────────────────────────────────────────────────────────────────

async def _timed_drop_job(bot) -> None:
    for chat_id in list(_registered_chats):
        await _send_drop(chat_id, bot)


def start_scheduler(bot) -> None:
    interval = getattr(Config, "DROP_INTERVAL_MIN", 15)
    scheduler.add_job(
        _timed_drop_job,
        trigger=IntervalTrigger(minutes=interval),
        kwargs={"bot": bot},
        id="timed_drop",
        replace_existing=True,
    )
    if not scheduler.running:
        scheduler.start()
    LOGGER.info("Drop scheduler started — interval: every %d min", interval)


# ── Message counter ───────────────────────────────────────────────────────────

async def message_counter(update: Update, context: CallbackContext) -> None:
    if not update.effective_chat or update.effective_chat.type == "private":
        return

    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    _registered_chats.add(chat_id)

    # Anti-spam logic
    last = _last_user.get(chat_id)
    if last and last["user_id"] == user_id:
        last["count"] += 1
        if last["count"] >= 10:
            warned_at = _warned.get(user_id, 0)
            now = time.time()
            if now - warned_at < 600:
                return  # Ignored window
            
            _warned[user_id] = now
            _last_user[chat_id] = {"user_id": user_id, "count": 0}  # Reset counter
            if update.effective_user and update.message:
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

async def guess(update: Update, context: CallbackContext) -> None:
    if not update.effective_chat or not update.effective_user or not update.message:
        return

    chat_id = update.effective_chat.id
    user_id = update.effective_user.id

    char = _active_char.get(chat_id)
    if not char:
        return  # No active drop

    if chat_id in _claimed:
        await update.message.reply_text(
            "❌ Already claimed by someone else! Wait for the next character."
        )
        return

    user_guess = " ".join(context.args).strip().lower() if context.args else ""
    if not user_guess:
        await update.message.reply_text("Usage: /guess <character name>")
        return

    if any(bad in user_guess for bad in ("()", "&&", "||", "<script", "http")):
        await update.message.reply_text("❌ Invalid characters in guess.")
        return

    # Clean punctuation & multi-spaces for name matching
    clean_guess = re.sub(r"[^\w\s]", "", user_guess)
    clean_char_name = re.sub(r"[^\w\s]", "", char.get("name", "").lower())

    guess_parts = set(clean_guess.split())
    name_parts = clean_char_name.split()

    # Match logic: Full match OR any part match
    correct = (
        clean_guess == clean_char_name
        or sorted(name_parts) == sorted(clean_guess.split())
        or any(part in guess_parts for part in name_parts if len(part) > 2)
    )

    if not correct:
        await update.message.reply_text("❌ Wrong name, try again!")
        return

    # Correct Guess - Immediately clear state to prevent double claim
    _claimed[chat_id] = user_id
    _active_char.pop(chat_id, None)

    u = update.effective_user
    first_name = u.first_name or "User"
    username = u.username or ""

    # Persist to database
    await user_collection.update_one(
        {"id": user_id},
        {
            "$push": {"characters": char},
            "$inc": {"total_guesses": 1, "xp": _XP_PER_GUESS},
            "$set": {"username": username, "first_name": first_name},
            "$setOnInsert": {
                "coins": 0,
                "wins": 0,
                "favorites": [],
            },
        },
        upsert=True,
    )

    await group_user_totals_collection.update_one(
        {"user_id": user_id, "group_id": chat_id},
        {
            "$set": {"username": username, "first_name": first_name},
            "$inc": {"count": 1},
        },
        upsert=True,
    )

    chat_title = update.effective_chat.title or "Group"
    await top_global_groups_collection.update_one(
        {"group_id": chat_id},
        {"$set": {"group_name": chat_title}, "$inc": {"count": 1}},
        upsert=True,
    )

    kb = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "📖 My Harem",
                    switch_inline_query_current_chat=f"collection.{user_id}",
                )
            ]
        ]
    )

    c_name = escape(str(char.get("name", "Unknown")))
    c_anime = escape(str(char.get("anime", "Unknown")))
    c_rarity = escape(str(char.get("rarity", "Common")))

    await update.message.reply_text(
        f'🎉 <a href="tg://user?id={user_id}">{escape(first_name)}</a> guessed it!\n\n'
        f"🌸 <b>{c_name}</b>\n"
        f"📺 {c_anime}\n"
        f"💎 {c_rarity}\n\n"
        f"Added to your harem! +{_XP_PER_GUESS} XP ✨",
        parse_mode=ParseMode.HTML,
        reply_markup=kb,
    )


# ── /fav ──────────────────────────────────────────────────────────────────────

async def fav(update: Update, context: CallbackContext) -> None:
    if not update.effective_user or not update.message:
        return

    user_id = update.effective_user.id
    if not context.args:
        await update.message.reply_text("Usage: /fav <character_id>")
        return

    char_id = str(context.args[0]).strip()
    user_doc = await user_collection.find_one({"id": user_id})
    if not user_doc:
        await update.message.reply_text("You haven't guessed any characters yet.")
        return

    char = next(
        (c for c in user_doc.get("characters", []) if str(c.get("id")) == char_id), None
    )
    if not char:
        await update.message.reply_text("That character isn't in your collection.")
        return

    await user_collection.update_one(
        {"id": user_id}, {"$set": {"favorites": [char_id]}}
    )
    await update.message.reply_text(
        f"⭐ <b>{escape(str(char.get('name', 'Character')))}</b> set as your favourite!",
        parse_mode=ParseMode.HTML,
    )


# ── Register handlers ─────────────────────────────────────────────────────────

application.add_handler(
    CommandHandler(
        ["guess", "protecc", "collect", "grab", "hunt"], guess, block=False
    )
)
application.add_handler(CommandHandler("fav", fav, block=False))
application.add_handler(
    MessageHandler(
        filters.TEXT & ~filters.COMMAND & filters.ChatType.GROUPS,
        message_counter,
        block=False,
    )
)
