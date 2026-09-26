import math
from html import escape
from itertools import groupby

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.error import BadRequest
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler

# သင့်ကိုယ်ပိုင် database ဖိုင်မှ Import လုပ်ခြင်း
from database import users_col, cards_col, inventory_col

_PAGE = 15
_MEDALS = {
    "⚪ Common": "⚪",
    "🟢 Uncommon": "🟢",
    "🔵 Rare": "🔵",
    "🟣 Epic": "🟣",
    "🟡 Legendary": "🟡",
    "👑 Mythic": "👑",
}

def _rarity_icon(rarity: str) -> str:
    return _MEDALS.get(rarity, "🎴")

async def _anime_totals(animes: list[str]) -> dict[str, int]:
    """Database (cards_col) ထဲရှိ Anime တစ်ခုချင်းစီ၏ စုစုပေါင်း ကတ်အရေအတွက်ကို တွက်ချက်ပေးသည်။"""
    pipeline = [
        {"$match": {"anime": {"$in": animes}}},
        {"$group": {"_id": "$anime", "n": {"$sum": 1}}},
    ]
    res = {}
    async for d in cards_col.aggregate(pipeline):
        res[d["_id"]] = d["n"]
    return res

async def _build_page(user_id: int, page: int) -> tuple[str, InlineKeyboardMarkup, str | None]:
    """Harem Text၊ Inline Keyboard နှင့် Photo URL တို့ကို တည်ဆောက်ပေးသည်။"""
    user = await users_col.find_one({"user_id": user_id})
    inventory = await inventory_col.find({"user_id": user_id}).to_list(length=None)

    if not inventory:
        return "📭 သင့်ထံတွင် ကတ်တစ်ကတ်မှ မရှိသေးပါ။ Group များတွင် ကတ်များ စတင်ဖမ်းယူပါ!", InlineKeyboardMarkup([]), None

    # ထပ်နေသော ကတ်များကို အရေအတွက် တွက်ချက်ခြင်း
    id_counts: dict[str, int] = {}
    for c in inventory:
        c_id = c.get("card_id") or c.get("id")
        id_counts[c_id] = id_counts.get(c_id, 0) + 1

    # Unique ကတ်များကိုသာ သီးသန့်ထုတ်ယူခြင်း
    unique_dict = {}
    for c in inventory:
        c_id = c.get("card_id") or c.get("id")
        if c_id not in unique_dict:
            unique_dict[c_id] = c
    
    unique: list[dict] = list(unique_dict.values())
    unique.sort(key=lambda x: (x.get("anime", ""), x.get("card_id") or x.get("id")))

    total_unique = len(unique)
    total_pages  = max(1, math.ceil(total_unique / _PAGE))
    page = max(0, min(page, total_pages - 1))

    page_chars  = unique[page * _PAGE:(page + 1) * _PAGE]
    animes      = list({c.get("anime", "") for c in page_chars})
    db_totals   = await _anime_totals(animes)

    # Header ရေးဆွဲခြင်း
    fav_id = ((user or {}).get("favorites") or [None])[0]
    first_name = escape((user or {}).get("first_name", "User"))
    coins = (user or {}).get("coins", 0)

    lines = [
        f"<b>🌸 {first_name}'s Harem</b>",
        f"📦 Unique: <b>{total_unique}</b>  |  🗂 Total: <b>{len(inventory)}</b>  |  💰 Coins: <b>{coins:,}</b>",
        f"Page <b>{page+1}/{total_pages}</b>\n",
    ]

    # Anime အလိုက် အုပ်စုဖွဲ့၍ စာရင်းထုတ်ခြင်း
    sorted_page = sorted(page_chars, key=lambda x: x.get("anime", ""))
    for anime, group_iter in groupby(sorted_page, key=lambda x: x.get("anime", "")):
        group_list = list(group_iter)
        db_total   = db_totals.get(anime, "?")
        lines.append(f"\n<b>{escape(anime)}  {len(group_list)}/{db_total}</b>")
        for c in group_list:
            c_id  = c.get("card_id") or c.get("id")
            icon  = _rarity_icon(c.get("rarity", ""))
            cnt   = id_counts.get(c_id, 1)
            dup   = f" ×{cnt}" if cnt > 1 else ""
            fav   = " ⭐" if c_id == fav_id else ""
            lines.append(f"  {icon} <code>{c_id}</code> {escape(c.get('name', ''))}{dup}{fav}")

    text = "\n".join(lines)

    # Inline Navigation Keyboard တည်ဆောက်ခြင်း
    kb: list[list] = []
    kb.append([InlineKeyboardButton(
        f"🔍 Search Collection ({len(inventory)})",
        switch_inline_query_current_chat=f"collection.{user_id}",
    )])
    
    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton("⬅️ Back", callback_data=f"harem:{page-1}:{user_id}"))
    nav.append(InlineKeyboardButton(f"📖 {page+1}/{total_pages}", callback_data="noop"))
    if page < total_pages - 1:
        nav.append(InlineKeyboardButton("Next ➡️", callback_data=f"harem:{page+1}:{user_id}"))
    
    if len(nav) > 1:
        kb.append(nav)

    markup = InlineKeyboardMarkup(kb)

    # Fav ကတ်ပုံ (သို့) စာမျက်နှာ၏ ပထမဆုံးကတ်ပုံကို ယူခြင်း
    photo: str | None = None
    if fav_id:
        fav_char = next((c for c in inventory if (c.get("card_id") or c.get("id")) == fav_id), None)
        photo    = (fav_char or {}).get("img_url")
    if not photo and page_chars:
        photo = page_chars[0].get("img_url")

    return text, markup, photo

async def _reply_harem(update: Update, text: str, markup: InlineKeyboardMarkup, photo: str | None) -> None:
    is_cb = bool(update.callback_query)
    if not is_cb:
        if photo:
            await update.message.reply_photo(photo, caption=text, parse_mode=ParseMode.HTML, reply_markup=markup)
        else:
            await update.message.reply_text(text, parse_mode=ParseMode.HTML, reply_markup=markup)
        return

    try:
        if photo:
            await update.callback_query.edit_message_caption(caption=text, parse_mode=ParseMode.HTML, reply_markup=markup)
        else:
            await update.callback_query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=markup)
    except BadRequest as e:
        if "not modified" not in str(e).lower():
            raise

async def harem(update: Update, context: ContextTypes.DEFAULT_TYPE, page: int = 0) -> None:
    user_id = update.effective_user.id
    text, markup, photo = await _build_page(user_id, page)
    await _reply_harem(update, text, markup, photo)

async def harem_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    q = update.callback_query
    await q.answer()
    _, page_str, uid_str = q.data.split(":")
    
    # မိမိ၏ Harem မဟုတ်ပါက နှိပ်၍မရအောင် တားဆီးခြင်း
    if q.from_user.id != int(uid_str):
        await q.answer("❌ ဤ Harem စာမျက်နှာသည် သင့်အတွက် မဟုတ်ပါ။", show_alert=True)
        return
        
    user_id = int(uid_str)
    text, markup, photo = await _build_page(user_id, page=int(page_str))
    await _reply_harem(update, text, markup, photo)

async def noop(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.callback_query.answer()

# ── Handlers များကို Main File သို့ လှမ်းပေးရန် ────────────────────────────────
def get_harem_handlers():
    return [
        CommandHandler(["harem", "collection"], harem, block=False),
        CallbackQueryHandler(harem_callback, pattern=r"^harem:\d+:\d+$", block=False),
        CallbackQueryHandler(noop, pattern=r"^noop$", block=False)
    ]
