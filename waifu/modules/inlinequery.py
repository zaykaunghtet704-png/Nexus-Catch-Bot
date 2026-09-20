import asyncio
import re
import time
from html import escape
from pymongo import ASCENDING
from cachetools import TTLCache
from telegram import InlineQueryResultPhoto, Update
from telegram.ext import CallbackContext, InlineQueryHandler
from waifu import application, collection, db, user_collection

_all_cache = TTLCache(maxsize=1, ttl=3600)
_user_cache = TTLCache(maxsize=10000, ttl=60)
_url_cache = TTLCache(maxsize=5000, ttl=3600)  # file_id → HTTP URL cache
_PAGE = 25


async def create_indexes() -> None:
    await db.anime_characters.create_index([("id", ASCENDING)])
    await db.anime_characters.create_index([("anime", ASCENDING)])
    await db.users.create_index([("characters.id", ASCENDING)])


# ── Helpers ───────────────────────────────────────────────────────────────────

async def _resolve_url(img: str, bot) -> str | None:
    """
    Return a public HTTPS URL for the image.
    - If img already starts with http  → return as-is.
    - If img looks like a Telegram file_id → ask Telegram for the download URL.
      Results are cached 1 hour to avoid hammering the API.
    """
    if not img:
        return None
    if img.startswith("http"):
        return img
    if img in _url_cache:
        return _url_cache[img]
    try:
        file = await bot.get_file(img)
        url = file.file_path  # always https://api.telegram.org/…
        _url_cache[img] = url
        return url
    except Exception:
        return None


async def _batch_global(ids: list) -> dict:
    if not ids:
        return {}
    pipeline = [
        {"$unwind": "$characters"},
        {"$match": {"characters.id": {"$in": ids}}},
        {"$group": {"_id": "$characters.id", "n": {"$sum": 1}}},
    ]
    return {d["_id"]: d["n"] async for d in user_collection.aggregate(pipeline)}


async def _batch_anime(animes: list) -> dict:
    if not animes:
        return {}
    pipeline = [
        {"$match": {"anime": {"$in": animes}}},
        {"$group": {"_id": "$anime", "n": {"$sum": 1}}},
    ]
    return {d["_id"]: d["n"] async for d in collection.aggregate(pipeline)}


# ── Main handler ──────────────────────────────────────────────────────────────

async def inlinequery(update: Update, context: CallbackContext) -> None:
    if not update.inline_query:
        return

    raw = update.inline_query.query.strip()
    offset = int(update.inline_query.offset) if update.inline_query.offset else 0
    user: dict | None = None
    chars: list[dict] = []

    if raw.startswith("collection."):
        # ── User's personal collection ──────────────────────────────────────
        parts = raw.split(" ", 1)
        uid_part = parts[0].split(".")[1]
        search = parts[1].strip() if len(parts) > 1 else ""

        if uid_part.isdigit():
            uid = int(uid_part)
            key = uid_part

            # FIX 1: Only use cache when stored value is not None
            if key in _user_cache and _user_cache[key] is not None:
                user = _user_cache[key]
            else:
                user = await user_collection.find_one({"id": uid})
                if user:
                    _user_cache[key] = user

            if user:
                deduped = list({c["id"]: c for c in user.get("characters", [])}.values())
                if search:
                    pat = re.compile(re.escape(search), re.IGNORECASE)
                    deduped = [
                        c for c in deduped
                        if pat.search(c.get("name", "")) or pat.search(c.get("anime", ""))
                    ]
                chars = deduped

        page_chars = chars[offset:offset + _PAGE]
    else:
        # ── Global catalogue search ─────────────────────────────────────────
        if raw:
            # FIX 2: MongoDB $regex search with offset-based skip/limit
            query = {
                "$or": [
                    {"name": {"$regex": re.escape(raw), "$options": "i"}},
                    {"anime": {"$regex": re.escape(raw), "$options": "i"}},
                ]
            }
            page_chars = await collection.find(query).skip(offset).limit(_PAGE).to_list(_PAGE)
        else:
            if "all" in _all_cache:
                all_chars = _all_cache["all"]
            else:
                all_chars = await collection.find({}).to_list(5000)
                _all_cache["all"] = all_chars
            page_chars = all_chars[offset:offset + _PAGE]

    next_offset = str(offset + len(page_chars)) if len(page_chars) == _PAGE else ""

    if not page_chars:
        await update.inline_query.answer([], cache_time=5)
        return

    # ── Parallel Async Fetch (Stats + Image URLs) ─────────────────────────────
    ids = [c["id"] for c in page_chars]
    animes = list({c["anime"] for c in page_chars if c.get("anime")})

    # Fetch DB stats and resolve photo URLs simultaneously
    g_count_task = _batch_global(ids)
    a_total_task = _batch_anime(animes)
    url_tasks = [_resolve_url(c.get("img_url", ""), context.bot) for c in page_chars]

    results_gather = await asyncio.gather(g_count_task, a_total_task, *url_tasks)
    g_count: dict = results_gather[0]
    a_total: dict = results_gather[1]
    photo_urls: list[str | None] = results_gather[2:]

    # ── Build results ─────────────────────────────────────────────────────────
    results = []
    timestamp = time.time_ns()

    for c, photo_url in zip(page_chars, photo_urls):
        if not photo_url:
            continue  # skip characters whose image can't be resolved

        name = escape(c.get("name", "Unknown"))
        anime = escape(c.get("anime", "Unknown"))

        if user and raw.startswith("collection."):
            u_cnt = sum(1 for x in user.get("characters", []) if x.get("id") == c["id"])
            u_an = sum(1 for x in user.get("characters", []) if x.get("anime") == c["anime"])
            db_an = a_total.get(c.get("anime"), "?")
            uid = user.get("id", "")
            uname = escape(user.get("first_name", str(uid)))
            cap = (
                f"<b><a href='tg://user?id={uid}'>{uname}</a>'s Character</b>\n\n"
                f"🌸 <b>{name}</b> (×{u_cnt})\n"
                f"📺 <b>{anime}</b> ({u_an}/{db_an})\n"
                f"💎 {c.get('rarity', '')}\n"
                f"🆔 {c['id']}"
            )
        else:
            gc = g_count.get(c["id"], 0)
            cap = (
                f"🌸 <b>{name}</b>\n\n"
                f"📺 {anime}\n"
                f"💎 {c.get('rarity', '')}\n"
                f"🆔 {c['id']}\n\n"
                f"Guessed globally <b>{gc}</b> time{'s' if gc != 1 else ''}."
            )

        results.append(
            InlineQueryResultPhoto(
                id=f"{c['id']}_{timestamp}",
                photo_url=photo_url,
                thumbnail_url=photo_url,
                caption=cap,
                parse_mode="HTML",
            )
        )

    await update.inline_query.answer(results, next_offset=next_offset, cache_time=5)


application.add_handler(InlineQueryHandler(inlinequery, block=False))
