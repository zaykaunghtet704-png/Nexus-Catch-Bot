from datetime import datetime, timedelta
from html import escape
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from database import users_col, inventory_col

def get_user(user_id: int):
    """PyMongo Safe User Fetch"""
    user_id = int(user_id)
    try:
        user = users_col.find_one({"user_id": user_id})
        if not user:
            user = {
                "user_id": user_id,
                "coins": 0,
                "gems": 0,
                "xp": 0,
                "title": "Novice Collector",
                "vip_status": "None",
                "last_daily": None
            }
            users_col.insert_one(user)
        return user
    except Exception:
        return {"user_id": user_id, "coins": 0, "gems": 0, "xp": 0, "title": "Novice Collector", "vip_status": "None"}

# ── 1. Daily Command (24-Hour Cooldown) ───────────────────────────────────────

async def daily_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    user_id = int(user.id)
    user_data = get_user(user_id)

    last_daily = user_data.get("last_daily")
    now = datetime.utcnow()

    # 24 Hours Cooldown Check
    if last_daily:
        if isinstance(last_daily, str):
            try:
                last_daily = datetime.fromisoformat(last_daily)
            except Exception:
                last_daily = None

        if last_daily and (now - last_daily) < timedelta(hours=24):
            remaining = timedelta(hours=24) - (now - last_daily)
            hours, remainder = divmod(int(remaining.total_seconds()), 3600)
            minutes, seconds = divmod(remainder, 60)
            
            await update.message.reply_text(
                f"⏳ <b>{escape(user.first_name)}</b>၊ သင် Daily Bonus ရယူထားပြီးပါပြီ!\n\n"
                f"နောက်တစ်ကြိမ် ရယူနိုင်ရန် <b>{hours} နာရီ {minutes} မိနစ်</b> စောင့်ဆိုင်းပေးပါ။",
                parse_mode=ParseMode.HTML
            )
            return

    bonus_coins = 1000
    bonus_gems = 5

    try:
        users_col.update_one(
            {"user_id": user_id},
            {
                "$inc": {"coins": bonus_coins, "gems": bonus_gems},
                "$set": {
                    "last_daily": now,
                    "first_name": user.first_name,
                    "username": user.username
                }
            },
            upsert=True
        )
    except Exception as e:
        await update.message.reply_text(f"❌ Daily Bonus ရယူရာတွင် Error ဖြစ်ပေါ်ခဲ့သည်: {e}")
        return

    updated_user = get_user(user_id)
    total_coins = updated_user.get("coins", bonus_coins)
    total_gems = updated_user.get("gems", bonus_gems)

    await update.message.reply_text(
        f"🎁 <b>Daily Bonus Received!</b>\n"
        f"+<b>{bonus_coins:,}</b> Coins နှင့် +<b>{bonus_gems}</b> Gems ရရှိသွားပါပြီ။\n\n"
        f"💰 လက်ရှိစုစုပေါင်း: <b>{total_coins:,}</b> Coins | 💎 <b>{total_gems}</b> Gems",
        parse_mode=ParseMode.HTML
    )

# ── 2. Shop Command ───────────────────────────────────────────────────────────

async def shop_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = int(update.effective_user.id)
    user_data = get_user(user_id)
    
    coins = user_data.get("coins", 0)
    gems = user_data.get("gems", 0)

    text = (
        f"🏪 <b>NEXUS ITEM SHOP</b>\n"
        f"⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n"
        f"💰 <b>Your Coins:</b> {coins:,}\n"
        f"💎 <b>Your Gems:</b> {gems:,}\n\n"
        f"<b>ရရှိနိုင်သော ပစ္စည်းများ:</b>\n"
        f"1. 📦 <b>Common Chest</b> - 500 Coins\n"
        f"2. 🎁 <b>Rare Chest</b> - 2,000 Coins\n"
        f"3. 👑 <b>Legendary Crate</b> - 50 Gems\n\n"
        f"<i>Marketplace ကိုကြည့်ရန် <code>/market</code> ကို အသုံးပြုပါ။</i>"
    )
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)
