import math
import random
from datetime import datetime, timedelta
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes
from models import SessionLocal, User, CardBase, UserCard, MarketItem


async def profile_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    session = SessionLocal()
    user = session.query(User).filter(User.id == uid).first()
    if not user:
        user = User(id=uid, first_name=update.effective_user.first_name, username=update.effective_user.username)
        session.add(user)
        session.commit()

    card_count = session.query(UserCard).filter(UserCard.user_id == uid).count()
    session.close()

    text = (
        f"👤 **USER PROFILE:**\n\n"
        f"• Name: **{user.first_name}** (@{user.username or 'N/A'})\n"
        f"• Level: `{user.level}` (EXP: `{user.exp}`)\n"
        f"• Coins: `{user.coins} 🪙` | Shards: `{user.shards} 💎`\n"
        f"• Total Cards Owned: `{card_count}`"
    )
    await update.message.reply_text(text, parse_mode="Markdown")


async def daily_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    session = SessionLocal()
    user = session.query(User).filter(User.id == uid).first()
    if not user:
        user = User(id=uid, first_name=update.effective_user.first_name)
        session.add(user)

    now = datetime.utcnow()
    if user.last_daily and (now - user.last_daily) < timedelta(hours=24):
        diff = timedelta(hours=24) - (now - user.last_daily)
        hours, remainder = divmod(int(diff.total_seconds()), 3600)
        minutes, _ = divmod(remainder, 60)
        await update.message.reply_text(f"⏳ **Daily Reward ကို ရယူပြီးပါပြီ။**\n{hours} နာရီ {minutes} မိနစ် ကြာမှ ပြန်ယူပါ။")
        session.close()
        return

    reward_coins = 500
    reward_shards = 10
    user.coins += reward_coins
    user.shards += reward_shards
    user.last_daily = now
    session.commit()
    session.close()

    await update.message.reply_text(f"🎉 **Daily Reward ရယူမှု အောင်မြင်ပါသည်။**\n+`{reward_coins}` Coins 🪙\n+`{reward_shards}` Shards 💎", parse_mode="Markdown")


async def inventory_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    page = int(context.args[0]) if context.args and context.args[0].isdigit() else 1
    limit = 5

    session = SessionLocal()
    total_cards = session.query(UserCard).filter(UserCard.user_id == uid).count()
    total_pages = math.ceil(total_cards / limit) or 1
    page = max(1, min(page, total_pages))

    cards = session.query(UserCard).filter(UserCard.user_id == uid).offset((page - 1) * limit).limit(limit).all()

    if not cards:
        await update.message.reply_text("📭 သင့်တွင် Card တစ်ခုမျှ မရှိသေးပါ။")
        session.close()
        return

    text = f"🎒 **YOUR INVENTORY (Page {page}/{total_pages}):**\n\n"
    for c in cards:
        lock = "🔒" if c.is_locked else "🔓"
        text += f"• `{c.uuid}` | **{c.card_info.name}** ({c.card_info.rarity}) [Print #{c.print_number}] {lock}\n"

    session.close()
    await update.message.reply_text(text, parse_mode="Markdown")


async def roll_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    cost = 300
    session = SessionLocal()
    user = session.query(User).filter(User.id == uid).first()

    if not user or user.coins < cost:
        await update.message.reply_text(f"❌ Gacha Roll ပြုလုပ်ရန် Coin မလုံလောက်ပါ။ (လိုအပ်ချက်: `{cost}` Coins)", parse_mode="Markdown")
        session.close()
        return

    cards = session.query(CardBase).all()
    if not cards:
        await update.message.reply_text("❌ Database ထဲတွင် ကဒ်များ မရှိသေးပါ။")
        session.close()
        return

    user.coins -= cost
    selected = random.choice(cards)
    selected.total_prints += 1

    new_card = UserCard(user_id=uid, card_id=selected.id, print_number=selected.total_prints)
    session.add(new_card)
    session.commit()

    text = f"🎰 **GACHA ROLL RESULT!**\n\n🎉 သင်သည် **{selected.name}** ({selected.rarity}) ကို ရရှိခဲ့သည်။\n🆔 UUID: `{new_card.uuid}`\n🔢 Print: `#{selected.total_prints}`"
    session.close()
    await update.message.reply_text(text, parse_mode="Markdown")


async def lock_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❌ Format: `/lock <card_uuid>`", parse_mode="Markdown")
        return
    card_uuid = context.args[0]
    uid = str(update.effective_user.id)

    session = SessionLocal()
    card = session.query(UserCard).filter(UserCard.uuid == card_uuid, UserCard.user_id == uid).first()
    if not card:
        await update.message.reply_text("❌ သင့်ထံတွင် အဆိုပါ Card မရှိပါ။")
        session.close()
        return

    card.is_locked = not card.is_locked
    st = "🔒 Locked" if card.is_locked else "🔓 Unlocked"
    session.commit()
    session.close()
    await update.message.reply_text(f"✅ Card status updated to **{st}**", parse_mode="Markdown")


async def sellmarket_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2:
        await update.message.reply_text("❌ Format: `/sellmarket <card_uuid> <price>`", parse_mode="Markdown")
        return
    card_uuid, price = context.args[0], int(context.args[1])
    uid = str(update.effective_user.id)

    session = SessionLocal()
    card = session.query(UserCard).filter(UserCard.uuid == card_uuid, UserCard.user_id == uid).first()
    if not card or card.is_locked:
        await update.message.reply_text("❌ Card မရှိပါ သို့မဟုတ် Lock ခတ်ထားပါသည်။")
        session.close()
        return

    item = MarketItem(seller_id=uid, card_uuid=card_uuid, price=price)
    session.add(item)
    session.commit()
    session.close()
    await update.message.reply_text(f"🛒 Card `{card_uuid}` အား Marketplace တွင် `{price}` 🪙 ဖြင့် တင်ရောင်းလိုက်ပါပြီ။", parse_mode="Markdown")


async def leaderboard_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    session = SessionLocal()
    top_users = session.query(User).order_by(User.coins.desc()).limit(10).all()
    session.close()

    text = "🏆 **GLOBAL RICH LEADERBOARD:**\n\n"
    for idx, u in enumerate(top_users, 1):
        text += f"{idx}. **{u.first_name}** - `{u.coins}` 🪙\n"

    await update.message.reply_text(text, parse_mode="Markdown")
