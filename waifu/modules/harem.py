"""
modules/harem.py — Paginated collection with inline action buttons per character.
"""
import math
from html import escape
from itertools import groupby

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.error import BadRequest
from telegram.ext import CallbackContext, CallbackQueryHandler, CommandHandler

from waifu import application, user_collection, waifu_collection

_PAGE = 15

# Rarity 13 ဆင့်အတွက် Icon များ အပြည့်အစုံ
_MEDALS = {
    "⚪ Common": "⚪",
    "🟢 Uncommon": "🟢",
    "🔵 Rare": "🔵",
    "🟣 Epic": "🟣",
    "🟡 Legendary": "🟡",
    "🟠 Mythic": "🟠",
    "🔴 Ancient": "🔴",
    "🔮 Celestial": "🔮",
    "🌟 Exotic": "🌟",
    "🌌 Cosmic": "🌌",
    "✨ Immortal": "✨",
    "👑 Exclusive Edition": "👑",
    "🏆 Premium Edition": "🏆",
}


def _rarity_icon(rarity: str) -> str:
    return _MEDALS.get(rarity, "🎴")


async def _anime_totals(animes: list[str]) -> dict[str, int]:
    pipeline = [
        {"$match": {"anime": {"$in": animes}}},
        {"$group": {"_id": "$anime", "n": {"$sum": 1}}},
    ]
    return {d["_id"]: d["n"] async for d in waifu_collection.aggregate(pipeline)}


async def _build_page(user_id: int, page: int) -> tuple[str, InlineKeyboardMarkup, str | None]:
    """Returns (text, keyboard, photo_url)."""
    user = await user_collection.find_one({"$or": [{"id": user_id}, {"user_id": user_id}]})
    if not user or not user.get("characters"):
        return "📭 သင့်ထံတွင် Character များ မရှိသေးပါ။ (/claim သို့မဟုတ် drop စောင့်ပြီး ဖမ်းပါ)", InlineKeyboardMarkup([]), None

    chars = user["characters"]
    # Deduplicate keeping all counts
    id_counts: dict[str, int] = {}
    for c in chars:
        cid = str(c.get("id", ""))
        if cid:
            id_counts[cid] = id_counts.get(cid, 0) + 1

    unique: list[dict] = list({str(c["id"]): c for c in chars if "id" in c}.values())
    unique.sort(key=lambda x: (x.get("anime", ""), str(x.get("id", ""))))

    total_unique = len(unique)
    total_pages = max(1, math.ceil(total_unique / _PAGE))
    page = max(0, min(page, total_pages - 1))

    page_chars = unique[page * _PAGE:(page + 1) * _PAGE]
    animes = list({c.get("anime", "Unknown") for c in page_chars})
    db_totals = await _anime_totals(animes)

    # Header
    fav_id = (user.get("favorites") or [None])[0]
    lines = [
        f"<b>🌸 {escape(user.get('first_name', 'User'))}'s Harem</b>",
        f"📦 {total_unique} Unique  |  🗂 {len(chars)} Total  |  "
        f"💰 {user.get('coins', 0):,} Coins",
        f"Page {page+1}/{total_pages}\n",
    ]

    # Group by anime
    sorted_page = sorted(page_chars, key=lambda x: x.get("anime", "Unknown"))
    for anime, group_iter in groupby(sorted_page, key=lambda x: x.get("anime", "Unknown")):
        group_list = list(group_iter)
        db_total = db_totals.get(anime, "?")
        lines.append(f"\n<b>{escape(anime)}  {len(group_list)}/{db_total}</b>")
        for c in group_list:
            cid = str(c.get("id", ""))
            icon = _rarity_icon(c.get("rarity", ""))
            cnt = id_counts.get(cid, 1)
            dup = f" ×{cnt}" if cnt > 1 else ""
            fav = " ⭐" if cid == str(fav_id) else ""
            lines.append(f"  {icon} <code>{cid}</code> {escape(c.get('name', ''))}{dup}{fav}")

    text = "\n".join(lines)

    # Keyboard
    kb: list[list] = []
    kb.append([InlineKeyboardButton(
        f"🔍 Browse Collection ({len(chars)})",
        switch_inline_query_current_chat=f"collection.{user_id}",
    )])
    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton("⬅️", callback_data=f"harem:{page-1}:{user_id}"))
    nav.append(InlineKeyboardButton(f"{page+1}/{total_pages}", callback_data="noop"))
    if page < total_pages - 1:
        nav.append(InlineKeyboardButton("➡️", callback_data=f"harem:{page+1}:{user_id}"))
    if nav:
        kb.append(nav)

    markup = InlineKeyboardMarkup(kb)

    # Photo URL
    photo: str | None = None
    if fav_id:
        fav_char = next((c for c in chars if str(c.get("id")) == str(fav_id)), None)
        photo = (fav_char or {}).get("img_url")
    if not photo and page_chars:
        photo = page_chars[0].get("img_url")

    return text, markup, photo


async def _reply_harem(update: Update, text: str,
                       markup: InlineKeyboardMarkup, photo: str | None) -> None:
    is_cb = bool(update.callback_query)
    if not is_cb:
        if photo:
            try:
                await update.message.reply_photo(
                    photo, caption=text, parse_mode=ParseMode.HTML, reply_markup=markup
                )
                return
            except Exception:
                pass
        await update.message.reply_text(
            text, parse_mode=ParseMode.HTML, reply_markup=markup
        )
        return

    q = update.callback_query
    try:
        if q.message.photo:
            await q.edit_message_caption(
                caption=text, parse_mode=ParseMode.HTML, reply_markup=markup
            )
        else:
            await q.edit_message_text(
                text, parse_mode=ParseMode.HTML, reply_markup=markup
            )
    except BadRequest as e:
        if "not modified" not in str(e).lower():
            try:
                await q.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=markup)
            except Exception:
                pass


async def harem(update: Update, context: CallbackContext, page: int = 0) -> None:
    user_id = update.effective_user.id
    text, markup, photo = await _build_page(user_id, page)
    await _reply_harem(update, text, markup, photo)


async def harem_callback(update: Update, context: CallbackContext) -> None:
    q = update.callback_query
    _, page_str, uid_str = q.data.split(":")
    if q.from_user.id != int(uid_str):
        await q.answer("❌ သင်၏ Harem မဟုတ်ပါ။", show_alert=True)
        return
    await q.answer()
    await harem(update, context, page=int(page_str))


async def noop(update: Update, context: CallbackContext) -> None:
    await update.callback_query.answer()


application.add_handler(CommandHandler(["harem", "collection", "hh"], harem, block=False))
application.add_handler(CallbackQueryHandler(harem_callback, pattern=r"^harem:\d+:\d+$", block=False))
application.add_handler(CallbackQueryHandler(noop, pattern=r"^noop$", block=False))
