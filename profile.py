import math
import random
from html import escape

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes, CommandHandler

# သင့်ကိုယ်ပိုင် config နှင့် database ဖိုင်များမှ ချိတ်ဆက်ခြင်း
from database import users_col, inventory_col
from config import PHOTO_URL  # (ဥပမာ - Default ပုံအတွက် Config ထဲတွင် PHOTO_URL = "https://..." ဟု ထည့်ထားရန်)

def _xp_for_level(level: int) -> int:
    return int(200 * (level ** 1.5))

def _calc_level(xp: int) -> tuple[int, int, int]:
    """Level, လက်ရှိ Level အတွက်ရထားသော XP နှင့် နောက် Level အတွက်လိုသော XP တို့ကို တွက်ချက်ပေးသည်။"""
    level = 1
    while _xp_for_level(level + 1) <= xp:
        level += 1
    floor = _xp_for_level(level)
    nxt   = _xp_for_level(level + 1)
    return level, xp - floor, nxt - floor

def _bar(value: int, maximum: int, length: int = 10) -> str:
    filled = int(length * value / max(maximum, 1))
    return "▓" * filled + "░" * (length - filled)

async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    target = None
    username = None

    # Reply လုပ်ထားလျှင် (သို့) Username ရိုက်ထည့်လျှင် (သို့) မိမိ Profile ကိုကြည့်လျှင်
    if update.message.reply_to_message:
        target = update.message.reply_to_message.from_user
    elif context.args:
        username = context.args[0].lstrip("@")
        u_doc = await users_col.find_one({"username": username})
        if not u_doc:
            await update.message.reply_text("❌ ထို User ကို ရှာမတွေ့ပါ။")
            return
    else:
        target = update.effective_user

    # Target ရှိနေလျှင် Database မှ User Data ကို ဆွဲထုတ်မည်
    if target:
        u_doc = await users_col.find_one({"user_id": target.id})

    if not u_doc:
        await update.message.reply_text("❌ ဤ User သည် မှတ်တမ်း မရှိသေးပါ။ ဂိမ်းစတင်ကစားရန် လိုအပ်သည်။")
        return

    uid        = u_doc.get("user_id", 0)
    first_name = escape(u_doc.get("first_name", "User"))
    db_username = u_doc.get("username")
    coins      = u_doc.get("coins", 0)
    wins       = u_doc.get("wins", 0)
    guesses    = u_doc.get("total_guesses", 0)
    xp         = u_doc.get("xp", 0)
    fav_id     = (u_doc.get("favorites") or [None])[0]

    # User ပိုင်ဆိုင်သော ကတ်များကို Inventory Collection မှ ဆွဲထုတ်ခြင်း
    chars = await inventory_col.find({"user_id": uid}).to_list(length=None)

    unique_count = len({c["card_id"] for c in chars})
    total_count  = len(chars)

    # Rarity အလိုက် ကတ်အရေအတွက်ကို ခွဲခြမ်းစိတ်ဖြာခြင်း (Unique ကတ်များအတွက်)
    rarity_count: dict[str, int] = {}
    unique_chars = {c["card_id"]: c for c in chars}.values()
    
    for c in unique_chars:
        r = c.get("rarity", "Unknown")
        rarity_count[r] = rarity_count.get(r, 0) + 1

    level, xp_in, xp_need = _calc_level(xp)
    bar = _bar(xp_in, xp_need, 12)

    # Rarity အလိုက် Collection ၏ ခန့်မှန်းတန်ဖိုး တွက်ချက်ခြင်း
    VALUE_MAP = {
        "⚪ Common": 100, 
        "🟢 Uncommon": 300, 
        "🔵 Rare": 600,
        "🟣 Epic": 1000, 
        "🟡 Legendary": 1500, 
        "👑 Mythic": 5000
    }
    total_value = sum(VALUE_MAP.get(c.get("rarity", ""), 100) for c in unique_chars)

    tag = f"@{db_username}" if db_username else f"#{uid}"
    rarity_lines = "\n".join(
        f"  {r}: {n}" for r, n in sorted(rarity_count.items())
    ) or "  ကတ်မရှိသေးပါ"

    text = (
        f"👤 <b>{first_name}</b>  <code>{tag}</code>\n"
        f"{'─' * 28}\n"
        f"⭐ Level <b>{level}</b>  [{bar}]\n"
        f"   <i>{xp_in:,} / {xp_need:,} XP</i>\n\n"
        f"💰 Coins:     <b>{coins:,}</b>\n"
        f"🗂 Collection: <b>{unique_count}</b> ခု (စုစုပေါင်း {total_count} ကတ်)\n"
        f"💎 ခန့်မှန်းတန်ဖိုး: <b>{total_value:,}</b> Coins\n"
        f"🎯 ဖမ်းဆီးမှုများ:   <b>{guesses}</b>\n"
        f"⚔️ Duel နိုင်ပွဲများ: <b>{wins}</b>\n\n"
        f"<b>Rarity စာရင်း:</b>\n{rarity_lines}"
    )

    # Favourite ကတ် ရှိပါက ၎င်း၏ပုံကို ယူမည်၊ မရှိပါက Config ထဲမှ Random ပုံပြမည်
    photo = None
    if fav_id:
        fav_char = next((c for c in chars if c["card_id"] == fav_id), None)
        photo    = (fav_char or {}).get("img_url")
        
    if not photo and PHOTO_URL:
        photo = random.choice(PHOTO_URL) if isinstance(PHOTO_URL, list) else PHOTO_URL

    if photo:
        await update.message.reply_photo(photo, caption=text, parse_mode=ParseMode.HTML)
    else:
        await update.message.reply_text(text, parse_mode=ParseMode.HTML)

# ── Handlers များကို Main File သို့ လှမ်းပေးရန် ────────────────────────────────
def get_profile_handlers():
    return [CommandHandler("profile", profile, block=False)]
