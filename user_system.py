import math
import random
from datetime import datetime, timedelta
from config import (
    FORCE_CHANNEL_URL,
    FORCE_GROUP_URL,
    MY_WAIFU_URL,
    REQUIRED_CHANNEL_ID,
    REQUIRED_GROUP_ID,
    START_IMAGE_URL,
)
from models import CardBase, SessionLocal, User, UserCard
from sqlalchemy import func
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

TIER_PRICES = {
    1: 1500, 2: 3000, 3: 4500, 4: 6000, 5: 7500,
    6: 9000, 7: 10500, 8: 12000, 9: 13500, 10: 15000,
}


async def check_force_join(user_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
    try:
        group_member = await context.bot.get_chat_member(
            chat_id=REQUIRED_GROUP_ID, user_id=user_id
        )
        if group_member.status in ["left", "kicked"]:
            return False

        channel_member = await context.bot.get_chat_member(
            chat_id=REQUIRED_CHANNEL_ID, user_id=user_id
        )
        if channel_member.status in ["left", "kicked"]:
            return False

        return True
    except Exception:
        return True


async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # PM ထဲတွင် start=harem ဖြင့် ပွင့်လာပါက Harem ကို တိုက်ရိုက်ပြပေးခြင်း
    if context.args and context.args[0] == "harem":
        await harem_cmd(update, context)
        return

    keyboard = [
        [
            InlineKeyboardButton("✨ My Waifu", url=MY_WAIFU_URL),
            InlineKeyboardButton("👥 Group", url=FORCE_GROUP_URL),
        ],
        [InlineKeyboardButton("📢 Channel", url=FORCE_CHANNEL_URL)],
    ]
    caption = "✨ **Nexus Catch Bot မှ ကြိုဆိုပါတယ်!**\n\nအောက်ပါ Link များကို အသုံးပြု၍ Community သို့ သွားရောက်နိုင်ပါသည်။"
    await context.bot.send_photo(
        chat_id=update.effective_chat.id,
        photo=START_IMAGE_URL,
        caption=caption,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown",
    )


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    page = int(context.args[0]) if context.args and context.args[0].isdigit() else 1
    if page == 1:
        text = (
            "📖 **CARD BOT GUIDE - PAGE 1**\n\n"
            "1. Group ထဲတွင် စာစောင်များ ပို့ပြီး Card Spawn အောင် ပြုလုပ်ပါ။\n"
            "2. Spawn လာပါက `/Nexus <Card_Name>` ဖြင့် ဖမ်းယူပါ။\n"
            "3. `/daily` ဖြင့် Coins ရယူပါ။\n"
            "4. `/claim` ဖြင့် 12 နာရီတစ်ကြိမ် Card အခမဲ့ ရယူပါ။\n\n"
            "နောက်တစ်မျက်နှာ: `/help 2`"
        )
    else:
        text = (
            "📖 **COMMANDS LIST - PAGE 2**\n\n"
            "🎮 **Gameplay:**\n"
            "• `/harem` | `/profile` | `/search` | `/duel` | `/upgrade`\n\n"
            "💰 **Economy & Market:**\n"
            "• `/market` | `/sell` | `/buy` | `/delist` | `/trade` | `/gift` | `/sellprice`\n\n"
            "🏆 **Leaderboards:**\n"
            "• `/top` | `/ctop` | `/todayNexusCatch`"
        )
    await update.message.reply_text(text, parse_mode="Markdown")


async def harem_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    user_id_int = update.effective_user.id

    is_joined = await check_force_join(user_id_int, context)
    if not is_joined:
        keyboard = [
            [InlineKeyboardButton("👥 Join Group", url=FORCE_GROUP_URL)],
            [InlineKeyboardButton("📢 Join Channel", url=FORCE_CHANNEL_URL)],
            [InlineKeyboardButton("🔄 Joined (Try Again)", callback_data="check_join_harem")]
        ]
        await update.message.reply_text(
            "⚠️ **ACCESS RESTRICTED!**\n\n"
            " `/harem` စာရင်းကို ကြည့်ရှုရန်အတွက် အောက်ပါ Group နှင့် Channel 2 ခုလုံးသို့ မဖြစ်မနေ Join ပေးရန် လိုအပ်ပါသည်။",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
        return

    page = int(context.args[0]) if context.args and context.args[0].isdigit() else 1
    limit = 5

    session = SessionLocal()
    try:
        total_cards = session.query(UserCard).filter(UserCard.user_id == uid).count()
        total_pages = math.ceil(total_cards / limit) or 1
        page = max(1, min(page, total_pages))

        cards = (
            session.query(UserCard)
            .filter(UserCard.user_id == uid)
            .offset((page - 1) * limit)
            .limit(limit)
            .all()
        )

        text = f"📚 **YOUR HAREM COLLECTION (Page {page}/{total_pages}):**\n\n"
        for c in cards:
            fav_tag = "⭐ " if c.uuid == c.owner.fav_card_uuid else ""
            text += f"{fav_tag}• ID: `{c.card_id}` | UUID: `{c.uuid}` | **{c.card_info.name}** ({c.card_info.rarity}) Lvl `{c.level}`\n"

        if not cards:
            text += "📭 သင့်ထံတွင် ကဒ်များ မရှိသေးပါ။"

        keyboard = [
            [
                InlineKeyboardButton("◀️ Prev", callback_data=f"harem_{page-1}"),
                InlineKeyboardButton("Next ▶️", callback_data=f"harem_{page+1}"),
            ]
        ]
        await update.message.reply_text(
            text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown"
        )
    finally:
        session.close()


async def profile_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    session = SessionLocal()
    try:
        user = session.query(User).filter(User.id == uid).first()
        if not user:
            user = User(id=uid, first_name=update.effective_user.first_name, username=update.effective_user.username)
            session.add(user)
            session.commit()

        user_cards = session.query(UserCard).filter(UserCard.user_id == uid).all()
        total_cards = len(user_cards)

        text = (
            f"👤 **USER PROFILE:**\n"
            f"• Name: **{user.first_name}** (@{user.username or 'N/A'})\n"
            f"• ID: `{user.id}`\n"
            f"• Level: `{user.level}` (EXP: `{user.exp}`)\n"
            f"• Balance: `{user.coins}` 🪙 Coins\n"
            f"• Total Cards: `{total_cards}`\n"
        )
        await update.message.reply_text(text, parse_mode="Markdown")
    finally:
        session.close()


async def search_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = " ".join(context.args) if context.args else ""
    session = SessionLocal()
    try:
        cards = session.query(CardBase).filter(CardBase.name.ilike(f"%{query}%")).limit(10).all()
        text = f"🔍 **CARD SEARCH RESULTS ({len(cards)}):**\n\n"
        for c in cards:
            text += f"• ID: `{c.id}` | **{c.name}** | {c.rarity}\n"
        await update.message.reply_text(text, parse_mode="Markdown")
    finally:
        session.close()


async def top_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    session = SessionLocal()
    try:
        top_users = (
            session.query(User.first_name, func.count(UserCard.uuid).label("total_cards"))
            .join(UserCard, User.id == UserCard.user_id)
            .group_by(User.id)
            .order_by(func.count(UserCard.uuid).desc())
            .limit(15)
            .all()
        )
        text = "🏆 **GLOBAL TOP 15 COLLECTORS:**\n\n"
        for idx, (name, count) in enumerate(top_users, 1):
            text += f"{idx}. **{name}** — `{count}` Cards 🃏\n"
        await update.message.reply_text(text, parse_mode="Markdown")
    finally:
        session.close()


async def ctop_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = str(update.effective_chat.id)
    session = SessionLocal()
    try:
        top_chat_users = (
            session.query(User.first_name, func.count(UserCard.uuid).label("total_cards"))
            .join(UserCard, User.id == UserCard.user_id)
            .filter(UserCard.chat_id == chat_id)
            .group_by(User.id)
            .order_by(func.count(UserCard.uuid).desc())
            .limit(10)
            .all()
        )
        text = "🏰 **THIS GROUP TOP COLLECTORS:**\n\n"
        for idx, (name, count) in enumerate(top_chat_users, 1):
            text += f"{idx}. **{name}** — `{count}` Cards 🃏\n"
        await update.message.reply_text(text, parse_mode="Markdown")
    finally:
        session.close()


async def today_nexus_catch_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    today = datetime.utcnow().date()
    session = SessionLocal()
    try:
        catches = (
            session.query(User.first_name, func.count(UserCard.uuid).label("today_cnt"))
            .join(UserCard, User.id == UserCard.user_id)
            .filter(func.date(UserCard.created_at) == today)
            .group_by(User.id)
            .order_by(func.count(UserCard.uuid).desc())
            .limit(10)
            .all()
        )
        text = f"📅 **TODAY'S TOP CATCHERS ({today}):**\n\n"
        for idx, (name, cnt) in enumerate(catches, 1):
            text += f"{idx}. **{name}** — `{cnt}` Cards Today ⚡\n"
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
            await update.message.reply_text("⏳ Daily reward ရယူပြီးပါပြီ။ 24 နာရီပြည့်မှ ပြန်လာပါ။")
            return

        user.coins += 500
        user.last_daily = now
        session.commit()
        await update.message.reply_text("🎉 **Daily Reward:** +`500` Coins 🪙 ရရှိပါသည်။", parse_mode="Markdown")
    finally:
        session.close()


async def balance_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    session = SessionLocal()
    try:
        user = session.query(User).filter(User.id == uid).first()
        coins = user.coins if user else 0
        await update.message.reply_text(f"💰 **YOUR BALANCE:** `{coins}` Coins 🪙", parse_mode="Markdown")
    finally:
        session.close()


async def sellprice_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = "🏷️ **CARD TIER SELL PRICES:**\n\n"
    for tier, price in TIER_PRICES.items():
        text += f"• **Tier {tier}:** `{price}` Coins 🪙\n"
    await update.message.reply_text(text, parse_mode="Markdown")


async def claim_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    session = SessionLocal()
    try:
        user = session.query(User).filter(User.id == uid).first()
        if not user:
            user = User(id=uid, first_name=update.effective_user.first_name)
            session.add(user)

        now = datetime.utcnow()
        if user.last_claim and (now - user.last_claim) < timedelta(hours=12):
            await update.message.reply_text("⏳ 12 နာရီတစ်ကြိမ်သာ Claim လုပ်နိုင်ပါသည်။")
            return

        mid_tier_cards = session.query(CardBase).filter(CardBase.tier_level.between(3, 7)).all()
        if not mid_tier_cards:
            mid_tier_cards = session.query(CardBase).all()

        given_cards = random.sample(mid_tier_cards, min(2, len(mid_tier_cards)))
        res_text = "🎁 **12-HOUR CLAIM REWARD:**\n\n"

        for card in given_cards:
            card.total_prints += 1
            uc = UserCard(user_id=uid, card_id=card.id, print_number=card.total_prints, chat_id=str(update.effective_chat.id))
            session.add(uc)
            res_text += f"• **{card.name}** ({card.rarity}) | Print #{card.total_prints}\n"

        user.last_claim = now
        session.commit()
        await update.message.reply_text(res_text, parse_mode="Markdown")
    finally:
        session.close()


async def check_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        return
    cid = context.args[0]
    session = SessionLocal()
    try:
        card = session.query(CardBase).filter(CardBase.id == cid).first()
        if card:
            caption = f"🃏 **CARD DETAILS:**\n\n• Name: **{card.name}**\n• Rarity: **{card.rarity}**"
            await context.bot.send_photo(chat_id=update.effective_chat.id, photo=card.image_url, caption=caption, parse_mode="Markdown")
    finally:
        session.close()


async def fav_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        return
    cid = context.args[0]
    uid = str(update.effective_user.id)
    session = SessionLocal()
    try:
        uc = session.query(UserCard).filter(UserCard.card_id == cid, UserCard.user_id == uid).first()
        if uc:
            user = session.query(User).filter(User.id == uid).first()
            user.fav_card_uuid = uc.uuid
            session.commit()
            await update.message.reply_text(f"⭐ Card `{cid}` ကို Favorite ပြုလုပ်ပြီးပါပြီ။", parse_mode="Markdown")
    finally:
        session.close()


async def unfav_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    session = SessionLocal()
    try:
        user = session.query(User).filter(User.id == uid).first()
        if user:
            user.fav_card_uuid = None
            session.commit()
            await update.message.reply_text("❌ Favorite Card ကို ပယ်ဖျက်လိုက်ပါပြီ။")
    finally:
        session.close()


async def duel_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.reply_to_message:
        return
    u1_id, u2_id = str(update.effective_user.id), str(update.message.reply_to_message.from_user.id)
    session = SessionLocal()
    try:
        p1_pow, p2_pow = random.randint(100, 500), random.randint(100, 500)
        winner_name = update.effective_user.first_name if p1_pow >= p2_pow else update.message.reply_to_message.from_user.first_name
        await update.message.reply_text(f"⚔️ **DUEL RESULT:** Winner: **{winner_name}**", parse_mode="Markdown")
    finally:
        session.close()


async def upgrade_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        return
    card_uuid = context.args[0]
    uid = str(update.effective_user.id)
    session = SessionLocal()
    try:
        uc = session.query(UserCard).filter(UserCard.uuid == card_uuid, UserCard.user_id == uid).first()
        if uc:
            uc.level += 1
            session.commit()
            await update.message.reply_text(f"⬆️ Level `{uc.level}` သို့ မြှင့်တင်ပြီးပါပြီ!", parse_mode="Markdown")
    finally:
        session.close()
