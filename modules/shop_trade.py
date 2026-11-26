from datetime import datetime, timedelta
from html import escape
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from database import atomic, users_col, inventory_col

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

    # Race-safe 24-hour claim with consecutive-day streak tracking.
    if last_daily:
        if isinstance(last_daily, str):
            try:
                last_daily = datetime.fromisoformat(last_daily)
            except Exception:
                last_daily = None
        if last_daily and (now - last_daily) < timedelta(hours=24):
            remaining = timedelta(hours=24) - (now - last_daily)
            hours, remainder = divmod(int(remaining.total_seconds()), 3600)
            minutes, _ = divmod(remainder, 60)
            await update.message.reply_text(
                f"⏳ Daily Reward ရယူထားပြီးပါပြီ။ နောက်တစ်ကြိမ်: <b>{hours} နာရီ {minutes} မိနစ်</b>",
                parse_mode=ParseMode.HTML,
            )
            return

    bonus_coins = 1000
    bonus_gems = 5
    streak = 1
    milestone_bonus = 0
    previous_stamp = user_data.get("last_daily")
    condition = {"user_id": user_id}
    if "last_daily" in user_data:
        condition["last_daily"] = previous_stamp
    else:
        condition["last_daily"] = {"$exists": False}

    try:
        with atomic():
            fresh = users_col.find_one({"user_id": user_id}) or {}
            fresh_last = fresh.get("last_daily")
            if isinstance(fresh_last, str):
                try:
                    fresh_last = datetime.fromisoformat(fresh_last)
                except Exception:
                    fresh_last = None
            if fresh_last and (now - fresh_last) < timedelta(hours=24):
                await update.message.reply_text("⏳ Daily Reward ကို ရယူပြီးပါပြီ။")
                return
            if fresh_last and (now - fresh_last) <= timedelta(hours=48):
                streak = int(fresh.get("daily_streak", 0) or 0) + 1
            milestone_bonus = 100 if streak % 7 == 0 else 0
            wallet_field = "coins" if "coins" in fresh else "balance"
            result = users_col.update_one(
                condition,
                {
                    "$inc": {wallet_field: bonus_coins + milestone_bonus, "gems": bonus_gems},
                    "$set": {
                        "last_daily": now,
                        "daily_streak": streak,
                        "first_name": user.first_name,
                        "username": user.username,
                    },
                },
            )
            if result.modified_count != 1:
                await update.message.reply_text("⏳ Daily Reward တစ်ကြိမ်သာ ရယူနိုင်ပါသည်။")
                return
    except Exception:
        await update.message.reply_text("❌ Daily Bonus ရယူရာတွင် Error ဖြစ်နေပါသည်။")
        return

    updated_user = get_user(user_id)
    total_coins = updated_user.get("coins", updated_user.get("balance", bonus_coins))
    total_gems = updated_user.get("gems", bonus_gems)

    await update.message.reply_text(
        f"╭━━━━━━━━━━━━━━━━━━╮\n"
        f"      🎁 <b>DAILY REWARD</b>\n"
        f"╰━━━━━━━━━━━━━━━━━━╯\n\n"
        f"🎉 ဒီနေ့ရဲ့ ဆုလက်ဆောင် ရရှိပါပြီ!\n\n"
        f"🪙 Coins: <b>+{bonus_coins + milestone_bonus:,}</b>\n"
        f"💎 Gems: <b>+{bonus_gems}</b>\n"
        f"🔥 Daily Streak: <b>{streak} ရက်</b>\n\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"💰 လက်ကျန် Coins: <b>{total_coins:,}</b>\n"
        f"💎 လက်ကျန် Gems: <b>{total_gems}</b>\n\n"
        f"✨ မနက်ဖြန်လည်း ပြန်လာခဲ့ပါဦး!",
        parse_mode=ParseMode.HTML
    )

# ── 2. Shop Command ───────────────────────────────────────────────────────────

async def shop_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = int(update.effective_user.id)
    user_data = get_user(user_id)
    
    coins = user_data.get("coins", 0)
    gems = user_data.get("gems", 0)

    text = (
        f"╭━━━━━━━━━━━━━━━━━━╮\n"
        f"        🛍️ <b>NEXUS SHOP</b>\n"
        f"╰━━━━━━━━━━━━━━━━━━╯\n\n"
        f"👛 <b>YOUR WALLET</b>\n"
        f"├ 🪙 Coins: <b>{coins:,}</b>\n"
        f"└ 💎 Gems: <b>{gems:,}</b>\n\n"
        f"🎁 <b>AVAILABLE ITEMS</b>\n"
        f"├ 📦 <b>Common Chest</b> — 500 Coins\n"
        f"├ 🎀 <b>Rare Chest</b> — 2,000 Coins\n"
        f"└ 👑 <b>Legendary Crate</b> — 50 Gems\n\n"
        f"📦 Chest ဖွင့်ရန် <code>/chest common</code>, <code>/chest rare</code> သို့မဟုတ် <code>/chest legendary</code> ကို သုံးပါ။\n"
        f"🏪 Market ကြည့်ရန် <code>/market</code> ကို အသုံးပြုပါ။\n"
        f"💫 <i>Choose your next treasure!</i>"
    )
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)
