import math
import random
from datetime import datetime, timedelta
from config import (
    MY_WAIFU_URL,
    REQUIRED_CHANNEL_ID,
    REQUIRED_CHANNEL_URL,
    REQUIRED_GROUP_ID,
    REQUIRED_GROUP_URL,
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

MESSAGES = {
    "my": {
        "start_caption": "✨ **Nexus Catch Bot မှ ကြိုဆိုပါတယ်!**\n\nအောက်ပါ Link များကို အသုံးပြု၍ Community သို့ သွားရောက်နိုင်ပါသည်။",
        "force_join": "⚠️ **ACCESS RESTRICTED!**\n\n`/harem` ကို ကြည့်ရှုရန် အောက်ပါ Group နှင့် Channel ကို အရင် Join ပေးပါ။",
        "daily_success": "🎉 **Daily Reward:** +`500` Coins 🪙 ရရှိပါသည်။",
        "daily_already": "⏳ 24 နာရီပြည့်မှ Daily reward ပြန်ယူနိုင်ပါမည်။",
        "claim_success": "🎁 **12-HOUR CLAIM REWARD:**\n\n",
        "claim_wait": "⏳ 12 နာရီတစ်ကြိမ်သာ Claim လုပ်နိုင်ပါသည်။",
        "lang_changed": "🌐 ဘာသာစကားကို မြန်မာဘာသာသို့ ပြောင်းလဲလိုက်ပါပြီ။",
    },
    "en": {
        "start_caption": "✨ **Welcome to Nexus Catch Bot!**\n\nUse the links below to access our community.",
        "force_join": "⚠️ **ACCESS RESTRICTED!**\n\nYou must join both channels below to access `/harem`.",
        "daily_success": "🎉 **Daily Reward:** Received +`500` Coins 🪙!",
        "daily_already": "⏳ Daily reward already claimed. Try again in 24 hours.",
        "claim_success": "🎁 **12-HOUR CLAIM REWARD:**\n\n",
        "claim_wait": "⏳ You can only claim once every 12 hours.",
        "lang_changed": "🌐 Language changed to English.",
    }
}


def get_lang(uid: str) -> str:
    session = SessionLocal()
    try:
        u = session.query(User).filter(User.id == uid).first()
        return u.language if u else "my"
    finally:
        session.close()


async def setlang_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    if not context.args or context.args[0].lower() not in ["my", "en"]:
        await update.message.reply_text("🌐 Usage: `/setlang my` or `/setlang en`", parse_mode="Markdown")
        return

    lang = context.args[0].lower()
    session = SessionLocal()
    try:
        user = session.query(User).filter(User.id == uid).first()
        if not user:
            user = User(id=uid, first_name=update.effective_user.first_name, language=lang)
            session.add(user)
        else:
            user.language = lang
        session.commit()
        await update.message.reply_text(MESSAGES[lang]["lang_changed"])
    finally:
        session.close()


async def check_force_join(user_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
    try:
        gm = await context.bot.get_chat_member(chat_id=REQUIRED_GROUP_ID, user_id=user_id)
        cm = await context.bot.get_chat_member(chat_id=REQUIRED_CHANNEL_ID, user_id=user_id)
        return gm.status not in ["left", "kicked"] and cm.status not in ["left", "kicked"]
    except Exception:
        return True


async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    lang = get_lang(uid)

    if context.args and context.args[0] == "harem":
        await harem_cmd(update, context)
        return

    keyboard = [
        [
            InlineKeyboardButton("✨ My Waifu", url=MY_WAIFU_URL),
            InlineKeyboardButton("👥 Group", url=REQUIRED_GROUP_URL),
        ],
        [InlineKeyboardButton("📢 Channel", url=REQUIRED_CHANNEL_URL)],
    ]
    await context.bot.send_photo(
        chat_id=update.effective_chat.id,
        photo=START_IMAGE_URL,
        caption=MESSAGES[lang]["start_caption"],
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown",
    )


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    page = int(context.args[0]) if context.args and context.args[0].isdigit() else 1
    if page == 1:
        text = (
            "📖 **CARD BOT GUIDE - PAGE 1**\n\n"
            "1. Group ထဲတွင် စာပို့ပြီး Card Spawn အောင် လုပ်ပါ။\n"
            "2. `/Nexus <Card_Name>` ဖြင့် Card ဖမ်းယူပါ။\n"
            "3. `/daily` ဖြင့် Coins ရယူပါ။\n"
            "4. `/claim` ဖြင့် 12 နာရီတစ်ကြိမ် Card အခမဲ့ ရယူပါ။\n\n"
            "Page 2 Commands စာရင်းကြည့်ရန် အောက်ပါ Button ကို နှိပ်ပါ။"
        )
        keyboard = [[InlineKeyboardButton("Next Page ▶️", callback_data="help_2")]]
    else:
        text = (
            "📖 **COMMANDS LIST - PAGE 2**\n\n"
            "🎮 **Gameplay:** `/harem` | `/profile` | `/search` | `/duel` | `/upgrade` | `/setlang` | `/hmode` | `/reset`\n"
            "💰 **Economy:** `/market` | `/sell` | `/buy` | `/delist` | `/trade` | `/gift` | `/sellprice`\n"
            "🏆 **Leaderboards:** `/top` | `/ctop` | `/rankings` | `/todayNexusCatch`"
        )
        keyboard = [[InlineKeyboardButton("◀️ Previous Page", callback_data="help_1")]]

    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")


async def help_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "help_1":
        context.args = ["1"]
    elif query.data == "help_2":
        context.args = ["2"]
    await help_cmd(update, context)


async def harem_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    lang = get_lang(uid)

    is_joined = await check_force_join(update.effective_user.id, context)
    if not is_joined:
        keyboard = [
            [InlineKeyboardButton("👥 Join Group", url=REQUIRED_GROUP_URL)],
            [InlineKeyboardButton("📢 Join Channel", url=REQUIRED_CHANNEL_URL)],
            [InlineKeyboardButton("🔄 Joined (Try Again)", callback_data="check_join_harem")]
        ]
        await update.message.reply_text(MESSAGES[lang]["force_join"], reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
        return

    page = int(context.args[0]) if context.args and context.args[0].isdigit() else 1
    limit = 5
    session = SessionLocal()
    try:
        user = session.query(User).filter(User.id == uid).first()
        query_filter = session.query(UserCard).filter(UserCard.user_id == uid)

        # /hmode Filter ပါဝင်ပါက စစ်ဆေးခြင်း
        if user and user.selected_hmode_tier:
            query_filter = query_filter.join(CardBase).filter(CardBase.tier_level == user.selected_hmode_tier)

        total_cards = query_filter.count()
        total_pages = math.ceil(total_cards / limit) or 1
        page = max(1, min(page, total_pages))

        cards = query_filter.offset((page - 1) * limit).limit(limit).all()
        text = f"📚 **YOUR HAREM COLLECTION (Page {page}/{total_pages}):**\n"
        if user and user.selected_hmode_tier:
            text += f"🏷️ **Filtered Tier:** `{user.selected_hmode_tier}`\n\n"
        else:
            text += "\n"

        for c in cards:
            fav_tag = "⭐ " if user and c.uuid == user.fav_card_uuid else ""
            text += f"{fav_tag}• ID: `{c.card_id}` | UUID: `{c.uuid}` | **{c.card_info.name}** ({c.card_info.rarity}) Lvl `{c.level}`\n"

        if not cards:
            text += "📭 သင့်ထံတွင် ကဒ်များ မရှိသေးပါ (သို့မဟုတ် Tier Filter ကြောင့် မပေါ်ပါ)။"

        keyboard = [
            [
                InlineKeyboardButton("◀️ Prev", callback_data=f"harem_{page-1}"),
                InlineKeyboardButton("Next ▶️", callback_data=f"harem_{page+1}"),
            ]
        ]
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
    finally:
        session.close()


async def harem_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    page = int(query.data.split("_")[1])
    context.args = [str(page)]
    await harem_cmd(update, context)


async def hmode_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = []
    for t in range(1, 11, 2):
        keyboard.append([
            InlineKeyboardButton(f"Tier {t}", callback_data=f"set_hmode_{t}"),
            InlineKeyboardButton(f"Tier {t+1}", callback_data=f"set_hmode_{t+1}"),
        ])
    await update.message.reply_text("🎴 **Harem တွင် ကြည့်ရှုလိုသော Card Tier Level ကို ရွေးချယ်ပါ:**", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")


async def hmode_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    tier = int(query.data.split("_")[2])
    uid = str(query.from_user.id)

    session = SessionLocal()
    try:
        user = session.query(User).filter(User.id == uid).first()
        if user:
            user.selected_hmode_tier = tier
            session.commit()
            await query.message.edit_text(f"✅ Harem Filter ကို **Tier {tier}** သို့ ပြောင်းလဲလိုက်ပါပြီ။ `/harem` တွင် ပြန်လည် ကြည့်ရှုနိုင်ပါသည်။")
    finally:
        session.close()


async def reset_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    session = SessionLocal()
    try:
        user = session.query(User).filter(User.id == uid).first()
        if user:
            user.selected_hmode_tier = None
            session.commit()
            await update.message.reply_text("🔄 Harem Tier Filter ကို ဖြုတ်လိုက်ပါပြီ။ ကဒ်အားလုံးကို ပြန်လည် ကြည့်ရှုနိုင်ပါသည်။")
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

        keyboard = [[InlineKeyboardButton("✨ View Waifu Harem", url=MY_WAIFU_URL)]]
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
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

        total_cards = session.query(UserCard).filter(UserCard.user_id == uid).count()

        top_users = (
            session.query(User.id)
            .join(UserCard, User.id == UserCard.user_id)
            .group_by(User.id)
            .order_by(func.count(UserCard.uuid).desc())
            .all()
        )
        user_rank = "N/A"
        for idx, u in enumerate(top_users, 1):
            if u.id == uid:
                user_rank = f"#{idx}"
                break

        text = (
            f"👤 **USER PROFILE:**\n"
            f"• Name: **{user.first_name}** (@{user.username or 'N/A'})\n"
            f"• ID: `{user.id}`\n"
            f"• Level: `{user.level}` (EXP: `{user.exp}`)\n"
            f"• Balance: `{user.coins}` 🪙 Coins\n"
            f"• Total Cards Owned: `{total_cards}`\n"
            f"• Global Leaderboard Rank: **{user_rank}**\n"
        )

        photos = await context.bot.get_user_profile_photos(user_id=int(uid), limit=1)
        if photos.total_count > 0:
            photo_file_id = photos.photos[0][-1].file_id
            await context.bot.send_photo(chat_id=update.effective_chat.id, photo=photo_file_id, caption=text, parse_mode="Markdown")
        else:
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
        text = "🏆 **GLOBAL TOP 15 CARD COLLECTORS:**\n\n"
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
    lang = get_lang(uid)
    session = SessionLocal()
    try:
        user = session.query(User).filter(User.id == uid).first()
        if not user:
            user = User(id=uid, first_name=update.effective_user.first_name)
            session.add(user)

        now = datetime.utcnow()
        if user.last_daily and (now - user.last_daily) < timedelta(hours=24):
            await update.message.reply_text(MESSAGES[lang]["daily_already"])
            return

        user.coins += 500
        user.last_daily = now
        session.commit()
        await update.message.reply_text(MESSAGES[lang]["daily_success"], parse_mode="Markdown")
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
    lang = get_lang(uid)
    session = SessionLocal()
    try:
        user = session.query(User).filter(User.id == uid).first()
        if not user:
            user = User(id=uid, first_name=update.effective_user.first_name)
            session.add(user)

        now = datetime.utcnow()
        if user.last_claim and (now - user.last_claim) < timedelta(hours=12):
            await update.message.reply_text(MESSAGES[lang]["claim_wait"])
            return

        mid_tier_cards = session.query(CardBase).filter(CardBase.tier_level.between(3, 7)).all()
        if not mid_tier_cards:
            mid_tier_cards = session.query(CardBase).all()

        given_cards = random.sample(mid_tier_cards, min(2, len(mid_tier_cards)))
        res_text = MESSAGES[lang]["claim_success"]

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
        u1, u2 = session.query(User).filter(User.id == u1_id).first(), session.query(User).filter(User.id == u2_id).first()
        if not u1 or not u2:
            return

        p1_pow = random.randint(100, 500) + (u1.level * 10)
        p2_pow = random.randint(100, 500) + (u2.level * 10)

        if p1_pow >= p2_pow:
            winner, reward = u1, 200
            winner_name = update.effective_user.first_name
        else:
            winner, reward = u2, 200
            winner_name = update.message.reply_to_message.from_user.first_name

        winner.coins += reward
        winner.exp += 50
        session.commit()
        await update.message.reply_text(f"⚔️ **DUEL RESULT:** Winner: **{winner_name}** (+`200` Coins 🪙 | +`50` EXP)", parse_mode="Markdown")
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
