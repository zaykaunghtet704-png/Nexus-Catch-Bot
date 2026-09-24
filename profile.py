 /profile command showing full user stats.
"""
import math
import random
from html import escape

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import CallbackContext, CommandHandler

from waifu import application, user_collection, PHOTO_URL


def _xp_for_level(level: int) -> int:
    return int(200 * (level ** 1.5))


def _calc_level(xp: int) -> tuple[int, int, int]:
    """Returns (level, xp_into_level, xp_needed)."""
    level = 1
    while _xp_for_level(level + 1) <= xp:
        level += 1
    floor = _xp_for_level(level)
    nxt   = _xp_for_level(level + 1)
    return level, xp - floor, nxt - floor


def _bar(value: int, maximum: int, length: int = 10) -> str:
    filled = int(length * value / max(maximum, 1))
    return "▓" * filled + "░" * (length - filled)


async def profile(update: Update, context: CallbackContext) -> None:
    if not update.message or not update.effective_user:
        return

    # 1. Target User ကို သတ်မှတ်ခြင်း (Reply သို့မဟုတ် Command Args သို့မဟုတ် မိမိကိုယ်တိုင်)
    if update.message.reply_to_message:
        target = update.message.reply_to_message.from_user
        u_doc = await user_collection.find_one({"$or": [{"id": target.id}, {"user_id": target.id}]})
    elif context.args:
        username = context.args[0].lstrip("@")
        u_doc = await user_collection.find_one({"username": username})
        target = None
    else:
        target = update.effective_user
        u_doc = await user_collection.find_one({"$or": [{"id": target.id}, {"user_id": target.id}]})

        # မိမိကိုယ်တိုင် ကြည့်နေပြီး Database ထဲ မရှိသေးပါက Auto Registraion ပြုလုပ်ခြင်း
        if not u_doc:
            new_user = {
                "id": target.id,
                "user_id": target.id,
                "first_name": target.first_name,
                "username": target.username or target.first_name,
                "balance": 100,
                "coins": 100,
                "xp": 0,
                "characters": [],
                "wins": 0,
                "total_guesses": 0
            }
            await user_collection.insert_one(new_user)
            u_doc = new_user

    if not u_doc:
        await update.message.reply_text("❌ ဒီ User ကို ရှာမတွေ့ပါ သို့မဟုတ် ကစားထားခြင်း မရှိသေးပါ။")
        return

    # 2. Data များ ဆွဲထုတ်ခြင်း
    uid        = u_doc.get("id") or u_doc.get("user_id")
    first_name = escape(u_doc.get("first_name") or target.first_name if target else "User")
    username   = u_doc.get("username")
    coins      = u_doc.get("coins") if "coins" in u_doc else u_doc.get("balance", 0)
    chars      = u_doc.get("characters", [])
    wins       = u_doc.get("wins", 0)
    guesses    = u_doc.get("total_guesses", 0)
    xp         = u_doc.get("xp", 0)
    fav_id     = (u_doc.get("favorites") or [None])[0]

    # 3. Collection နိယာမများ တွက်ချက်ခြင်း
    unique_count = len({c.get("id", c.get("card_id")) for c in chars if isinstance(c, dict)})
    total_count  = len(chars)

    # Rarity အလိုက် အရေအတွက်ခွဲခြားခြင်း
    rarity_count: dict[str, int] = {}
    unique_chars = {c.get("id", c.get("card_id")): c for c in chars if isinstance(c, dict)}.values()
    
    for c in unique_chars:
        r = c.get("rarity", "Unknown")
        rarity_count[r] = rarity_count.get(r, 0) + 1

    level, xp_in, xp_need = _calc_level(xp)
    bar = _bar(xp_in, xp_need, 10)

    # Collection Value Weight တွက်ချက်ခြင်း
    VALUE_MAP = {
        "⚪ Common": 100, "🟢 Medium": 300, "🟣 Rare": 600,
        "🟡 Legendary": 1500, "💮 Special Edition": 5000,
        "R": 300, "SR": 600, "SSR": 1500, "UR": 5000
    }
    total_value = sum(
        VALUE_MAP.get(c.get("rarity", ""), 100)
        for c in unique_chars
    )

    tag = f"@{username}" if username else f"#{uid}"
    rarity_lines = "\n".join(
        f"  • {r}: <b>{n}</b>" for r, n in sorted(rarity_count.items())
    ) or "  • မရှိသေးပါ"

    # 4. Message Format ပြင်ဆင်ခြင်း
    text = (
        f"👤 <b>{first_name}</b> ၏ Profile ({tag})\n"
        f"{'─' * 28}\n"
        f"⭐ Level <b>{level}</b> [{bar}]\n"
        f"   <i>{xp_in:,} / {xp_need:,} XP</i>\n\n"
        f"💰 Coins: <b>{coins:,}</b>\n"
        f"🎒 စုစုပေါင်း ကတ်: <b>{unique_count}</b> (Total: {total_count})\n"
        f"💎 ကတ်များ၏ တန်ဖိုး: <b>{total_value:,}</b> Coins\n"
        f"🎯 Guesses: <b>{guesses}</b>\n"
        f"⚔️ Duel Wins: <b>{wins}</b>\n\n"
        f"<b>Rarity ခွဲခြားမှု:</b>\n{rarity_lines}"
    )

    # 5. Favorite Image သို့မဟုတ် Default Image ဖြင့် ပို့ပေးခြင်း
    photo: str | None = None
    if fav_id:
        fav_char = next((c for c in chars if isinstance(c, dict) and c.get("id") == fav_id), None)
        if fav_char:
            photo = fav_char.get("img_url") or fav_char.get("image_url")

    if not photo and PHOTO_URL:
        photo = random.choice(PHOTO_URL) if isinstance(PHOTO_URL, list) else PHOTO_URL

    if photo:
        try:
            await update.message.reply_photo(photo=photo, caption=text, parse_mode=ParseMode.HTML)
        except Exception:
            await update.message.reply_text(text, parse_mode=ParseMode.HTML)
    else:
        await update.message.reply_text(text, parse_mode=ParseMode.HTML)


application.add_handler(CommandHandler("profile", profile, block=False))
