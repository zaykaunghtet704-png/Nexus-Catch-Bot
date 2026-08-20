import math
import random
from datetime import datetime, timedelta
from models import CardBase, MarketItem, SessionLocal, User, UserCard
from telegram import Update
from telegram.ext import ContextTypes

# 10-Tier Rarity Mapping
TIERS = {
    1: "⚪ Common (Tier 1)",
    2: "🟢 Uncommon (Tier 2)",
    3: "🔵 Rare (Tier 3)",
    4: "🟣 Epic (Tier 4)",
    5: "🟡 Legendary (Tier 5)",
    6: "🟠 Mythic (Tier 6)",
    7: "🔴 Ancient (Tier 7)",
    8: "✨ Divine (Tier 8)",
    9: "💎 Immortal (Tier 9)",
    10: "👑 Celestial (Tier 10)"
}

async def hmode_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = "📖 **10-TIER RARITY SYSTEM RULES**\n\n"
    for tier, name in TIERS.items():
        text += f"• **Level {tier}:** {name}\n"
    text += "\n💡 *ဂိမ်းစည်းမျဉ်း:* Rarity အဆင့်မြင့်လေ ပွဲစဉ် Power ပိုမိုမြင့်မားလေဖြစ်ပါသည်။"
    await update.message.reply_text(text, parse_mode="Markdown")

async def profile_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    session = SessionLocal()
    try:
        user = session.query(User).filter(User.id == uid).first()
        if not user:
            user = User(id=uid, first_name=update.effective_user.first_name, username=update.effective_user.username)
            session.add(user)
            session.commit()

        card_count = session.query(UserCard).filter(UserCard.user_id == uid).count()
        text = (
            f"👤 **USER PROFILE:**\n\n"
            f"• Name: **{user.first_name}** (@{user.username or 'N/A'})\n"
            f"• Level: `{user.level}` | EXP: `{user.exp}`\n"
            f"• Coins: `{user.coins}` 🪙 | Shards: `{user.shards}` 💎\n"
            f"• Total Collection: `{card_count}` Cards 🃏\n"
            f"• Favorite Card UUID: `{user.fav_card_uuid or 'None'}`"
        )
        await update.message.reply_text(text, parse_mode="Markdown")
    finally:
        session.close()

async def grab_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    session = SessionLocal()
    try:
        user = session.query(User).filter(User.id == uid).first()
        if not user:
            user = User(id=uid, first_name=update.effective_user.first_name)
            session.add(user)

        now = datetime.utcnow()
        if user.last_grab and (now - user.last_grab) < timedelta(minutes=15):
            diff = timedelta(minutes=15) - (now - user.last_grab)
            mins, secs = divmod(int(diff.total_seconds()), 60)
            await update.message.reply_text(f"⏳ **Grab Cooldown!**\nနောက်ထပ် `{mins}` မိနစ် `{secs}` စက္ကန့် စောင့်ပါ။", parse_mode="Markdown")
            return

        cards = session.query(CardBase).all()
        if not cards:
            await update.message.reply_text("❌ Database တွင် Card များ မရှိသေးပါ။")
            return

        selected = random.choice(cards)
        selected.total_prints += 1
        new_card = UserCard(user_id=uid, card_id=selected.id, print_number=selected.total_prints)
        
        user.last_grab = now
        session.add(new_card)
        session.commit()

        await update.message.reply_text(
            f"🎁 **FREE CLAIM RESULT!**\n\n🎉 **{selected.name}** ({selected.rarity})\n🆔 UUID: `{new_card.uuid}` | Print: `#{selected.total_prints}`",
            parse_mode="Markdown"
        )
    finally:
        session.close()

async def harem_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    page = int(context.args[0]) if context.args and context.args[0].isdigit() else 1
    limit = 5

    session = SessionLocal()
    try:
        total_cards = session.query(UserCard).filter(UserCard.user_id == uid).count()
        total_pages = math.ceil(total_cards / limit) or 1
        page = max(1, min(page, total_pages))

        cards = session.query(UserCard).filter(UserCard.user_id == uid).offset((page - 1) * limit).limit(limit).all()

        if not cards:
            await update.message.reply_text("📭 သင့်ထံတွင် Card မရှိသေးပါ။")
            return

        text = f"📚 **COLLECTION / HAREM (Page {page}/{total_pages}):**\n\n"
        for c in cards:
            text += f"• `{c.uuid}` | **{c.card_info.name}** | {c.card_info.rarity} | Lvl `{c.level}`\n"

        await update.message.reply_text(text, parse_mode="Markdown")
    finally:
        session.close()

async def fav_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❌ Format: `/fav <card_uuid>`", parse_mode="Markdown")
        return
    card_uuid = context.args[0]
    uid = str(update.effective_user.id)

    session = SessionLocal()
    try:
        card = session.query(UserCard).filter(UserCard.uuid == card_uuid, UserCard.user_id == uid).first()
        if not card:
            await update.message.reply_text("❌ အဆိုပါ Card ပိုင်ဆိုင်ထားခြင်း မရှိပါ။")
            return

        user = session.query(User).filter(User.id == uid).first()
        user.fav_card_uuid = card_uuid
        session.commit()
        await update.message.reply_text(f"⭐ **{card.card_info.name}** ကို Favorite Battle Card အဖြစ် သတ်မှတ်လိုက်ပါပြီ။", parse_mode="Markdown")
    finally:
        session.close()

async def fuse_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2:
        await update.message.reply_text("❌ Format: `/fuse <uuid1> <uuid2>`", parse_mode="Markdown")
        return
    u1, u2 = context.args[0], context.args[1]
    uid = str(update.effective_user.id)

    session = SessionLocal()
    try:
        c1 = session.query(UserCard).filter(UserCard.uuid == u1, UserCard.user_id == uid).first()
        c2 = session.query(UserCard).filter(UserCard.uuid == u2, UserCard.user_id == uid).first()

        if not c1 or not c2:
            await update.message.reply_text("❌ တင်ပြထားသော Card UUID များ မမှန်ကန်ပါ။")
            return

        if c1.is_locked or c2.is_locked:
            await update.message.reply_text("❌ Locked ပြုလုပ်ထားသော Card ကို Fuse လုပ်၍မရပါ။")
            return

        session.delete(c1)
        session.delete(c2)

        cards = session.query(CardBase).all()
        selected = random.choice(cards)
        selected.total_prints += 1
        
        new_card = UserCard(user_id=uid, card_id=selected.id, print_number=selected.total_prints, level=2)
        session.add(new_card)
        session.commit()

        await update.message.reply_text(
            f"⚛️ **FUSION SUCCESSFUL!**\n\n🎉 ရရှိလာသော Card: **{selected.name}**\n🆔 UUID: `{new_card.uuid}` | Level: `2`",
            parse_mode="Markdown"
        )
    finally:
        session.close()

async def upgrade_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❌ Format: `/upgrade <card_uuid>`", parse_mode="Markdown")
        return
    card_uuid = context.args[0]
    uid = str(update.effective_user.id)

    session = SessionLocal()
    try:
        card = session.query(UserCard).filter(UserCard.uuid == card_uuid, UserCard.user_id == uid).first()
        user = session.query(User).filter(User.id == uid).first()

        if not card:
            await update.message.reply_text("❌ Card မတွေ့ပါ။")
            return

        cost = card.level * 20
        if user.shards < cost:
            await update.message.reply_text(f"❌ Shards မလုံလောက်ပါ။ (လိုအပ်ချက်: `{cost}` Shards 💎)", parse_mode="Markdown")
            return

        user.shards -= cost
        card.level += 1
        session.commit()

        await update.message.reply_text(f"⚔️ **{card.card_info.name}** ကို Level `{card.level}` သို့ မြှင့်တင်လိုက်ပါပြီ!", parse_mode="Markdown")
    finally:
        session.close()

async def duel_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.reply_to_message:
        await update.message.reply_text("❌ ယှဉ်ပြိုင်လိုသည့် User ၏ Message ကို Reply ပြုလုပ်၍ ခေါ်ပါ။")
        return

    uid1 = str(update.effective_user.id)
    uid2 = str(update.message.reply_to_message.from_user.id)

    if uid1 == uid2:
        await update.message.reply_text("❌ မိမိကိုယ်ကို Duel ခေါ်၍မရပါ။")
        return

    session = SessionLocal()
    try:
        u1 = session.query(User).filter(User.id == uid1).first()
        u2 = session.query(User).filter(User.id == uid2).first()

        c1 = session.query(UserCard).filter(UserCard.uuid == u1.fav_card_uuid if u1 else None).first()
        c2 = session.query(UserCard).filter(UserCard.uuid == u2.fav_card_uuid if u2 else None).first()

        p1_power = (c1.card_info.base_power * c1.level) if c1 else random.randint(100, 500)
        p2_power = (c2.card_info.base_power * c2.level) if c2 else random.randint(100, 500)

        winner = update.effective_user.first_name if p1_power >= p2_power else update.message.reply_to_message.from_user.first_name

        text = (
            f"⚔️ **DUEL RESULT:**\n\n"
            f"🔴 {update.effective_user.first_name}: `{p1_power}` Power\n"
            f"🔵 {update.message.reply_to_message.from_user.first_name}: `{p2_power}` Power\n\n"
            f"🏆 **Winner:** **{winner}**"
        )
        await update.message.reply_text(text, parse_mode="Markdown")
    finally:
        session.close()

async def disassemble_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❌ Format: `/disassemble <card_uuid>`", parse_mode="Markdown")
        return
    card_uuid = context.args[0]
    uid = str(update.effective_user.id)

    session = SessionLocal()
    try:
        card = session.query(UserCard).filter(UserCard.uuid == card_uuid, UserCard.user_id == uid).first()
        if not card or card.is_locked:
            await update.message.reply_text("❌ Card မတွေ့ပါ သို့မဟုတ် Card အား Lock ခတ်ထားပါသည်။")
            return

        gained_shards = card.level * 15
        user = session.query(User).filter(User.id == uid).first()
        user.shards += gained_shards

        session.delete(card)
        session.commit()
        await update.message.reply_text(f"♻️ Card ကို ဖျက်ဆီးပြီး `{gained_shards}` Shards 💎 ရယူလိုက်ပါပြီ။", parse_mode="Markdown")
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
            await update.message.reply_text(f"⏳ Daily reward ကို လာမည့် `{hours}` နာရီအကြာမှ ပြန်ယူပါ။", parse_mode="Markdown")
            return

        user.coins += 1000
        user.shards += 20
        user.last_daily = now
        session.commit()
        await update.message.reply_text("🎉 **Daily Reward ရရှိပါသည်!**\n+`1000` Coins 🪙\n+`20` Shards 💎", parse_mode="Markdown")
    finally:
        session.close()
