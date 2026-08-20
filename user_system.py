import math
import random
from datetime import datetime, timedelta
from models import CardBase, MarketItem, SessionLocal, User, UserCard
from telegram import Update
from telegram.ext import ContextTypes


async def profile_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    session = SessionLocal()
    try:
        user = session.query(User).filter(User.id == uid).first()
        if not user:
            user = User(
                id=uid,
                first_name=update.effective_user.first_name,
                username=update.effective_user.username,
            )
            session.add(user)
            session.commit()

        card_count = (
            session.query(UserCard).filter(UserCard.user_id == uid).count()
        )
        text = (
            f"👤 **USER PROFILE:**\n\n"
            f"• Name: **{user.first_name}** (@{user.username or 'N/A'})\n"
            f"• Level: `{user.level}` (EXP: `{user.exp}`)\n"
            f"• Coins: `{user.coins} 🪙` | Shards: `{user.shards} 💎`\n"
            f"• Total Cards: `{card_count}`"
        )
        await update.message.reply_text(text, parse_mode="Markdown")
    finally:
        session.close()


async def daily_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    session = SessionLocal()
    try:
        user = session.query(User).filter(User.id == uid).first()
        if not user:
            user = User(id=uid, first_name=update.effective_user.first_name)
            session.add(user)

        now = datetime.utcnow()
        if user.last_daily and (now - user.last_daily) < timedelta(hours=24):
            diff = timedelta(hours=24) - (now - user.last_daily)
            hours, remainder = divmod(int(diff.total_seconds()), 3600)
            minutes, _ = divmod(remainder, 60)
            await update.message.reply_text(
                f"⏳ **Daily Reward ရယူပြီးပါပြီ။**\nနောက်ထပ် `{hours}` နာရီ `{minutes}` မိနစ် ကြာမှ ပြန်ယူပါ။",
                parse_mode="Markdown",
            )
            return

        user.coins += 500
        user.shards += 10
        user.last_daily = now
        session.commit()
        await update.message.reply_text(
            "🎉 **Daily Reward ရရှိပါသည်!**\n+`500` Coins 🪙\n+`10` Shards 💎",
            parse_mode="Markdown",
        )
    finally:
        session.close()


async def inventory_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    page = (
        int(context.args[0])
        if context.args and context.args[0].isdigit()
        else 1
    )
    limit = 5

    session = SessionLocal()
    try:
        total_cards = (
            session.query(UserCard).filter(UserCard.user_id == uid).count()
        )
        total_pages = math.ceil(total_cards / limit) or 1
        page = max(1, min(page, total_pages))

        cards = (
            session.query(UserCard)
            .filter(UserCard.user_id == uid)
            .offset((page - 1) * limit)
            .limit(limit)
            .all()
        )

        if not cards:
            await update.message.reply_text("📭 သင့်ထံတွင် Card မရှိသေးပါ။")
            return

        text = f"🎒 **INVENTORY (Page {page}/{total_pages}):**\n\n"
        for c in cards:
            lock = "🔒" if c.is_locked else "🔓"
            text += f"• UUID: `{c.uuid}` | **{c.card_info.name}** ({c.card_info.rarity}) #{c.print_number} {lock}\n"

        await update.message.reply_text(text, parse_mode="Markdown")
    finally:
        session.close()


async def roll_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    cost = 300
    session = SessionLocal()
    try:
        user = session.query(User).filter(User.id == uid).first()

        if not user or user.coins < cost:
            await update.message.reply_text(
                f"❌ Coins မလုံလောက်ပါ။ (လိုအပ်ချက်: `{cost}` Coins)",
                parse_mode="Markdown",
            )
            return

        cards = session.query(CardBase).all()
        if not cards:
            await update.message.reply_text(
                "❌ Database ထဲတွင် Card များ မရှိသေးပါ။"
            )
            return

        user.coins -= cost
        selected = random.choice(cards)
        selected.total_prints += 1

        new_card = UserCard(
            user_id=uid, card_id=selected.id, print_number=selected.total_prints
        )
        session.add(new_card)
        session.commit()

        await update.message.reply_text(
            f"🎰 **GACHA RESULT:**\n\n🎉 **{selected.name}** ({selected.rarity})\n🆔 UUID: `{new_card.uuid}`\n🔢 Print: `#{selected.total_prints}`",
            parse_mode="Markdown",
        )
    finally:
        session.close()


async def lock_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text(
            "❌ Format: `/lock <card_uuid>`", parse_mode="Markdown"
        )
        return
    card_uuid = context.args[0]
    uid = str(update.effective_user.id)

    session = SessionLocal()
    try:
        card = (
            session.query(UserCard)
            .filter(UserCard.uuid == card_uuid, UserCard.user_id == uid)
            .first()
        )
        if not card:
            await update.message.reply_text("❌ အဆိုပါ Card မတွေ့ပါ။")
            return

        card.is_locked = not card.is_locked
        st = "🔒 Locked" if card.is_locked else "🔓 Unlocked"
        session.commit()
        await update.message.reply_text(
            f"✅ Card status: **{st}**", parse_mode="Markdown"
        )
    finally:
        session.close()


async def leaderboard_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    session = SessionLocal()
    try:
        top_users = (
            session.query(User).order_by(User.coins.desc()).limit(10).all()
        )
        text = "🏆 **GLOBAL RICH LEADERBOARD:**\n\n"
        for idx, u in enumerate(top_users, 1):
            text += f"{idx}. **{u.first_name or 'User'}** - `{u.coins}` 🪙\n"
        await update.message.reply_text(text, parse_mode="Markdown")
    finally:
        session.close()
