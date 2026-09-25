"""
profile.py - Custom Tree-style Profile Display
"""
from html import escape
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from database import users_col, inventory_col


def _bar(value: int, maximum: int, length: int = 10) -> str:
    filled = int(length * value / max(maximum, 1))
    return "▭" * filled + "▬" * (length - filled)


async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or not update.effective_user:
        return

    user = update.effective_user
    user_id = user.id

    # User ဒေတာ စစ်ဆေးခြင်း/အသစ်ထည့်ခြင်း
    user_data = users_col.find_one({"user_id": user_id})
    if not user_data:
        new_user = {
            "user_id": user_id,
            "username": user.username or user.first_name,
            "balance": 100,
            "xp": 0,
            "level": 1
        }
        users_col.insert_one(new_user)
        user_data = new_user

    # Rarity အလိုက် စုစုပေါင်း ကတ်ပမာဏ ရေတွက်ခြင်း
    rarity_counts = {
        "Supreme": inventory_col.count_documents({"user_id": user_id, "rarity": "Supreme"}),
        "Cataphract": inventory_col.count_documents({"user_id": user_id, "rarity": "Cataphract"}),
        "CrossVerse": inventory_col.count_documents({"user_id": user_id, "rarity": "CrossVerse"}),
        "Divine": inventory_col.count_documents({"user_id": user_id, "rarity": "Divine"}),
        "Mystical": inventory_col.count_documents({"user_id": user_id, "rarity": "Mystical"}),
        "Legendary": inventory_col.count_documents({"user_id": user_id, "rarity": "Legendary"}),
        "Rare": inventory_col.count_documents({"user_id": user_id, "rarity": "Rare"}),
        "Uncommon": inventory_col.count_documents({"user_id": user_id, "rarity": "Uncommon"}),
        "Common": inventory_col.count_documents({"user_id": user_id, "rarity": "Common"}),
    }

    total_cards = inventory_col.count_documents({"user_id": user_id})
    level = user_data.get("level", 1)
    xp = user_data.get("xp", 0)
    progress_bar = _bar(xp % 100, 100, 10)

    # Rarity Icons
    icons = {
        "Supreme": "💎",
        "Cataphract": "✨",
        "CrossVerse": "⚡",
        "Divine": "⚜️",
        "Mystical": "🏵️",
        "Legendary": "📦",
        "Rare": "🎁",
        "Uncommon": "🔮",
        "Common": "🎁",
    }

    # Rarity စာကြောင်းများ တည်ဆောက်ခြင်း
    rarity_text = ""
    for r_name, count in rarity_counts.items():
        icon = icons.get(r_name, "🔹")
        rarity_text += f"├──⇒ {icon} <b>RARITY: {r_name}:</b> {count}\n"

    # Profile Text အပြည့်အစုံ ရေးဆွဲခြင်း
    text = (
        f"┌──🩵 <b>CATCHER PROFILE</b>\n"
        f"├──⇒ 👤 <b>USER:</b> {escape(user.first_name)}\n"
        f"├──⇒ 📑 <b>USER ID:</b> <code>{user_id}</code>\n"
        f"├──⇒ ⚡ <b>TOTAL CHARACTER:</b> {total_cards}\n"
        f"├──⇒ ⚙️ <b>HAREM:</b> {total_cards}/7261\n"
        f"├──⇒ ℹ️ <b>EXPERIENCE LEVEL:</b> {level}\n"
        f"└──⇒ 📈 <b>PROGRESS BAR:</b>\n"
        f"      {progress_bar}\n"
        f"─────────────────────────\n"
        f"┌──\n"
        f"{rarity_text}"
        f"─────────────────────────\n"
        f"┌──\n"
        f"├──⇒ 🌍 <b>GLOBAL POSITION:</b> 1\n"
        f"└──⇒ 🍁 <b>CHAT POSITION:</b> 1"
    )

    # Favorite Card Image ပါလျှင် ပုံပါပြရန် (မပါလျှင် စာပဲ ပို့ရန်)
    fav_card = inventory_col.find_one({"user_id": user_id, "is_fav": True})
    photo_url = fav_card.get("image_url") if fav_card else None

    if photo_url:
        await update.message.reply_photo(photo=photo_url, caption=text, parse_mode=ParseMode.HTML)
    else:
        await update.message.reply_text(text, parse_mode=ParseMode.HTML)
