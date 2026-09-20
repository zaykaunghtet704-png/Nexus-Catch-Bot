import html
import io
import random

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import CallbackContext, CommandHandler

from waifu import (
    OWNER_ID,
    PHOTO_URL,
    application,
    group_user_totals_collection,
    top_global_groups_collection,
    user_collection,
)
from waifu import sudo_users as SUDO

_M = ["🥇", "🥈", "🥉"]
_T = 15


def _link(first: str, username: str | None, uid: int) -> str:
    name = html.escape((first or "?")[:_T] + ("…" if len(first or "") > _T else ""))
    if username and username != "Unknown":
        return f'<a href="https://t.me/{username}"><b>{name}</b></a>'
    return f'<a href="tg://user?id={uid}"><b>{name}</b></a>'


def _medal(i: int) -> str:
    return _M[i] if i < 3 else f"{i+1}."


async def _reply_with_photo_or_text(update: Update, lines: list[str]) -> None:
    text = "\n".join(lines)
    photo = random.choice(PHOTO_URL) if PHOTO_URL else None
    if photo:
        try:
            await update.message.reply_photo(photo=photo, caption=text, parse_mode=ParseMode.HTML)
            return
        except Exception:
            pass  # Photo ပို့ရာတွင် Error တက်ပါက Text သို့ Fallback ပြုလုပ်မည်
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)


async def leaderboard(update: Update, context: CallbackContext) -> None:
    cursor = user_collection.aggregate([
        {
            "$project": {
                "username": 1,
                "first_name": 1,
                "id": 1,
                "character_count": {"$size": {"$ifNull": ["$characters", []]}},
            }
        },
        {"$sort": {"character_count": -1}},
        {"$limit": 10},
    ])
    data = await cursor.to_list(10)
    lines = ["<b>🌸 Top 10 Collectors</b>\n"]
    for i, u in enumerate(data):
        lnk = _link(u.get("first_name"), u.get("username"), u.get("id", 0))
        lines.append(f"{_medal(i)} {lnk} ➾ <b>{u.get('character_count', 0)}</b>")
    
    await _reply_with_photo_or_text(update, lines)


async def ctop(update: Update, context: CallbackContext) -> None:
    if not update.effective_chat:
        return
    cid = update.effective_chat.id
    cursor = group_user_totals_collection.aggregate([
        {"$match": {"group_id": cid}},
        {
            "$project": {
                "username": 1,
                "first_name": 1,
                "user_id": 1,
                "character_count": {
                    "$cond": {
                        "if": {"$isArray": "$characters"},
                        "then": {"$size": "$characters"},
                        "else": {"$ifNull": ["$count", 0]}
                    }
                },
            }
        },
        {"$sort": {"character_count": -1}},
        {"$limit": 10},
    ])
    data = await cursor.to_list(10)
    lines = ["<b>🏆 Top 10 in This Group</b>\n"]
    for i, u in enumerate(data):
        lnk = _link(u.get("first_name"), u.get("username"), u.get("user_id", 0))
        lines.append(f"{_medal(i)} {lnk} ➾ <b>{u.get('character_count', 0)}</b>")
    
    await _reply_with_photo_or_text(update, lines)


async def global_leaderboard(update: Update, context: CallbackContext) -> None:
    cursor = top_global_groups_collection.aggregate([
        {"$project": {"group_name": 1, "count": 1}},
        {"$sort": {"count": -1}},
        {"$limit": 10},
    ])
    data = await cursor.to_list(10)
    lines = ["<b>🌍 Top 10 Active Groups</b>\n"]
    for i, g in enumerate(data):
        name = html.escape((g.get("group_name") or "Unknown")[:_T])
        lines.append(f"{_medal(i)} <b>{name}</b> ➾ <b>{g.get('count', 0)}</b>")
    
    await _reply_with_photo_or_text(update, lines)


async def stats(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id if update.effective_user else 0
    if user_id != OWNER_ID:
        await update.message.reply_text("❌ Owner only.")
        return

    users = await user_collection.estimated_document_count()
    groups = len(await top_global_groups_collection.distinct("group_id"))
    await update.message.reply_text(
        f"📊 <b>Bot Stats</b>\n\n👤 Users: <b>{users}</b>\n👥 Groups: <b>{groups}</b>",
        parse_mode=ParseMode.HTML,
    )


async def send_users_doc(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id if update.effective_user else 0
    sudo_list = [int(x) for x in SUDO] if isinstance(SUDO, (list, set, tuple)) else []
    if user_id not in sudo_list and user_id != OWNER_ID:
        await update.message.reply_text("❌ Sudo only.")
        return

    buf = io.BytesIO()
    async for doc in user_collection.find({}, {"first_name": 1, "id": 1}):
        first = doc.get("first_name", "?")
        uid = doc.get("id", "?")
        buf.write(f"{first} ({uid})\n".encode("utf-8"))
    
    buf.seek(0)
    await context.bot.send_document(
        chat_id=update.effective_chat.id,
        document=buf,
        filename="users.txt"
    )


async def send_groups_doc(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id if update.effective_user else 0
    sudo_list = [int(x) for x in SUDO] if isinstance(SUDO, (list, set, tuple)) else []
    if user_id not in sudo_list and user_id != OWNER_ID:
        await update.message.reply_text("❌ Sudo only.")
        return

    buf = io.BytesIO()
    async for doc in top_global_groups_collection.find({}, {"group_name": 1, "group_id": 1}):
        gname = doc.get("group_name", "?")
        gid = doc.get("group_id", "?")
        buf.write(f"{gname} ({gid})\n".encode("utf-8"))
    
    buf.seek(0)
    await context.bot.send_document(
        chat_id=update.effective_chat.id,
        document=buf,
        filename="groups.txt"
    )


application.add_handler(CommandHandler("top", leaderboard, block=False))
application.add_handler(CommandHandler("ctop", ctop, block=False))
application.add_handler(CommandHandler("TopGroups", global_leaderboard, block=False))
application.add_handler(CommandHandler("stats", stats, block=False))
application.add_handler(CommandHandler("list", send_users_doc, block=False))
application.add_handler(CommandHandler("groups", send_groups_doc, block=False))
