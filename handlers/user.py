from datetime import datetime, timedelta

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy import func, select

from database import (
    Card,
    DailyReward,
    SessionLocal,
    User,
    UserCard,
)


router = Router()


# =========================================================
# HELPERS
# =========================================================

async def get_user(telegram_id: int):
    async with SessionLocal() as session:
        result = await session.execute(
            select(User).where(
                User.telegram_id == telegram_id
            )
        )
        return result.scalar_one_or_none()


async def get_or_create_user(message: Message):
    if message.from_user is None:
        return None

    async with SessionLocal() as session:
        result = await session.execute(
            select(User).where(
                User.telegram_id == message.from_user.id
            )
        )

        user = result.scalar_one_or_none()

        if user is None:
            user = User(
                telegram_id=message.from_user.id,
                username=message.from_user.username,
                first_name=(
                    message.from_user.first_name
                    or "Player"
                ),
            )

            session.add(user)
            await session.commit()
            await session.refresh(user)

        return user


# =========================================================
# /START
# =========================================================

@router.message(Command("start"))
async def start_command(message: Message):
    user = await get_or_create_user(message)

    if user is None:
        return

    await message.answer(
        f"🌸 <b>Welcome to Nexus Catch!</b>\n\n"
        f"👤 Player: <b>{user.first_name}</b>\n"
        f"⭐ Level: <b>{user.level}</b>\n"
        f"✨ XP: <b>{user.xp}</b>\n"
        f"💰 Coins: <b>{user.coins:,}</b>\n"
        f"💎 Gems: <b>{user.gems:,}</b>\n\n"
        f"🎴 ကဒ်တွေကို စုဆောင်းပြီး\n"
        f"🏆 Rank တက်နိုင်ပါတယ်။\n\n"
        f"📖 အသုံးပြုနည်းကြည့်ရန် /help ကိုနှိပ်ပါ။",
    )


# =========================================================
# /HELP
# =========================================================

@router.message(Command("help"))
async def help_command(message: Message):
    await message.answer(
        "📖 <b>Nexus Catch Commands</b>\n\n"

        "👤 <b>Account</b>\n"
        "/start — Bot စတင်အသုံးပြုရန်\n"
        "/profile — မိမိ Profile\n"
        "/balance — Coin / Gem ကြည့်ရန်\n"
        "/stats — မိမိ Stats\n\n"

        "🎴 <b>Cards</b>\n"
        "/cards — Card အမျိုးအစားများ\n"
        "/collection — မိမိ Card Collection\n"
        "/harem — မိမိရထားသော Card များ\n"
        "/search — Card ရှာရန်\n"
        "/check — Card အသေးစိတ်ကြည့်ရန်\n"
        "/fav — Favorite Card\n"
        "/unfav — Favorite ဖြုတ်ရန်\n"
        "/upgrade — Card Level တင်ရန်\n\n"

        "🎁 <b>Rewards</b>\n"
        "/daily — နေ့စဉ် Coin 500 ရယူရန်\n"
        "/claim — Card ရယူရန်\n\n"

        "🏆 <b>Ranking</b>\n"
        "/top — Global Top 15\n"
        "/rankings — Ranking\n"
        "/ctop — Group Ranking\n"
        "/todayNexusCatch — ဒီနေ့ Card Catch Top\n\n"

        "🏪 <b>Market</b>\n"
        "/market — Market ကြည့်ရန်\n"
        "/sell — Card ရောင်းရန်\n"
        "/buy — Card ဝယ်ရန်\n"
        "/delist — Listing ဖယ်ရန်\n"
        "/sellprice — Card စျေးနှုန်းများ\n\n"

        "⚔️ <b>Games</b>\n"
        "/duel — Card Duel\n"
        "/mines — Mines Game\n\n"

        "⚙️ <b>Settings</b>\n"
        "/hmode — Harem Mode\n"
        "/reset — Harem Reset\n"
        "/changetime — Catch Time ပြောင်းရန်\n",
    )


# =========================================================
# /PROFILE
# =========================================================

@router.message(Command("profile"))
async def profile_command(message: Message):
    user = await get_user(
        message.from_user.id
    )

    if user is None:
        await message.answer(
            "❌ Profile မရှိသေးပါ။\n"
            "/start ကိုအရင်နှိပ်ပါ။"
        )
        return

    async with SessionLocal() as session:
        card_result = await session.execute(
            select(func.coalesce(func.sum(UserCard.quantity), 0))
            .where(UserCard.user_id == user.id)
        )

        card_count = card_result.scalar() or 0

        unique_result = await session.execute(
            select(func.count(UserCard.id))
            .where(UserCard.user_id == user.id)
        )

        unique_cards = unique_result.scalar() or 0

    await message.answer(
        f"👤 <b>{user.first_name}</b>\n\n"
        f"🆔 ID: <code>{user.telegram_id}</code>\n"
        f"⭐ Level: <b>{user.level}</b>\n"
        f"✨ XP: <b>{user.xp}</b>\n"
        f"💰 Coins: <b>{user.coins:,}</b>\n"
        f"💎 Gems: <b>{user.gems:,}</b>\n"
        f"🎴 Cards: <b>{card_count}</b>\n"
        f"📚 Unique: <b>{unique_cards}</b>\n\n"
        f"🏆 Keep collecting!",
    )


# =========================================================
# /BALANCE
# =========================================================

@router.message(Command("balance"))
async def balance_command(message: Message):
    user = await get_user(
        message.from_user.id
    )

    if user is None:
        await message.answer(
            "❌ /start ကိုအရင်နှိပ်ပါ။"
        )
        return

    await message.answer(
        f"💰 <b>Your Balance</b>\n\n"
        f"🪙 Coins: <b>{user.coins:,}</b>\n"
        f"💎 Gems: <b>{user.gems:,}</b>"
    )


# =========================================================
# /STATS
# =========================================================

@router.message(Command("stats"))
async def stats_command(message: Message):
    user = await get_user(
        message.from_user.id
    )

    if user is None:
        await message.answer(
            "❌ /start ကိုအရင်နှိပ်ပါ။"
        )
        return

    async with SessionLocal() as session:
        result = await session.execute(
            select(func.coalesce(func.sum(UserCard.quantity), 0))
            .where(UserCard.user_id == user.id)
        )

        total_cards = result.scalar() or 0

        unique_result = await session.execute(
            select(func.count(UserCard.id))
            .where(UserCard.user_id == user.id)
        )

        unique_cards = unique_result.scalar() or 0

    await message.answer(
        f"📊 <b>Your Statistics</b>\n\n"
        f"⭐ Level: <b>{user.level}</b>\n"
        f"✨ XP: <b>{user.xp}</b>\n"
        f"🎴 Total Cards: <b>{total_cards}</b>\n"
        f"📚 Unique Cards: <b>{unique_cards}</b>\n"
        f"💰 Coins: <b>{user.coins:,}</b>\n"
        f"💎 Gems: <b>{user.gems:,}</b>"
    )


# =========================================================
# /CARDS
# =========================================================

@router.message(Command("cards"))
async def cards_command(message: Message):
    async with SessionLocal() as session:
        result = await session.execute(
            select(Card)
            .order_by(Card.id.asc())
            .limit(20)
        )

        cards = result.scalars().all()

    if not cards:
        await message.answer(
            "🎴 Card မရှိသေးပါ။"
        )
        return

    text = "🎴 <b>Nexus Card Database</b>\n\n"

    for card in cards:
        premium = " 💎" if card.is_premium else ""

        text += (
            f"#{card.id:04d} "
            f"<b>{card.name}</b>{premium}\n"
            f"✦ {card.rarity}\n"
            f"⚔️ {card.attack}  "
            f"🛡️ {card.defense}  "
            f"❤️ {card.hp}\n\n"
        )

    await message.answer(text)


# =========================================================
# /COLLECTION
# =========================================================

@router.message(Command("collection"))
async def collection_command(message: Message):
    user = await get_user(
        message.from_user.id
    )

    if user is None:
        await message.answer(
            "❌ /start ကိုအရင်နှိပ်ပါ။"
        )
        return

    async with SessionLocal() as session:
        result = await session.execute(
            select(UserCard, Card)
            .join(
                Card,
                Card.id == UserCard.card_id,
            )
            .where(
                UserCard.user_id == user.id
            )
            .order_by(
                Card.rarity.desc(),
                Card.id.asc(),
            )
            .limit(20)
        )

        rows = result.all()

    if not rows:
        await message.answer(
            "📚 <b>Your Collection</b>\n\n"
            "🎴 Card မရသေးပါ။\n"
            "/claim နဲ့ စမ်းကြည့်နိုင်ပါတယ်။"
        )
        return

    text = (
        f"📚 <b>{user.first_name}'s Collection</b>\n\n"
    )

    for user_card, card in rows:
        text += (
            f"🎴 #{card.id:04d} "
            f"<b>{card.name}</b>\n"
            f"✦ {card.rarity}\n"
            f"⭐ Lv.{user_card.level} "
            f"×{user_card.quantity}\n\n"
        )

    await message.answer(text)


# =========================================================
# /HAREM
# =========================================================

@router.message(Command("harem"))
async def harem_command(message: Message):
    user = await get_user(
        message.from_user.id
    )

    if user is None:
        await message.answer(
            "❌ /start ကိုအရင်နှိပ်ပါ။"
        )
        return

    async with SessionLocal() as session:
        result = await session.execute(
            select(UserCard, Card)
            .join(
                Card,
                Card.id == UserCard.card_id,
            )
            .where(
                UserCard.user_id == user.id
            )
            .order_by(
                UserCard.obtained_at.desc()
            )
            .limit(10)
        )

        rows = result.all()

    if not rows:
        await message.answer(
            "🎴 Harem ထဲမှာ Card မရှိသေးပါ။"
        )
        return

    text = "💎 <b>Your Harem</b>\n\n"

    for user_card, card in rows:
        favorite = " ❤️" if user_card.is_favorite else ""

        text += (
            f"#{card.id:04d} "
            f"<b>{card.name}</b>{favorite}\n"
            f"✦ {card.rarity} | "
            f"⭐ Lv.{user_card.level}\n"
            f"×{user_card.quantity}\n\n"
        )

    await message.answer(text)


# =========================================================
# /DAILY
# =========================================================

@router.message(Command("daily"))
async def daily_command(message: Message):
    user = await get_user(
        message.from_user.id
    )

    if user is None:
        await message.answer(
            "❌ /start ကိုအရင်နှိပ်ပါ။"
        )
        return

    now = datetime.utcnow()

    async with SessionLocal() as session:
        result = await session.execute(
            select(DailyReward).where(
                DailyReward.user_id == user.id
            )
        )

        daily = result.scalar_one_or_none()

        if daily is None:
            daily = DailyReward(
                user_id=user.id,
                streak=1,
                last_claimed_at=now,
            )

            session.add(daily)

            user.coins += 500

            await session.commit()

            await message.answer(
                "🎁 <b>Daily Reward</b>\n\n"
                "💰 +500 Coins ရရှိပါပြီ!\n"
                "🔥 Streak: <b>1</b>"
            )

            return

        if daily.last_claimed_at:
            elapsed = now - daily.last_claimed_at

            if elapsed < timedelta(hours=24):
                remaining = timedelta(
                    hours=24
                ) - elapsed

                hours = remaining.seconds // 3600
                minutes = (
                    remaining.seconds % 3600
                ) // 60

                await message.answer(
                    "⏳ Daily Reward ကို "
                    "ပြန်ယူလို့မရသေးပါ။\n\n"
                    f"🕐 နောက်ထပ် <b>"
                    f"{hours}h {minutes}m"
                    f"</b> စောင့်ပါ။"
                )

                return

        if daily.last_claimed_at:
            if now - daily.last_claimed_at <= timedelta(
                hours=48
            ):
                daily.streak += 1
            else:
                daily.streak = 1

        daily.last_claimed_at = now

        user.coins += 500

        await session.commit()

        await message.answer(
            "🎁 <b>Daily Reward Claimed!</b>\n\n"
            "💰 +500 Coins\n"
            f"🔥 Streak: <b>{daily.streak}</b>"
        )


# =========================================================
# /TOP
# =========================================================

@router.message(Command("top"))
async def top_command(message: Message):
    async with SessionLocal() as session:
        result = await session.execute(
            select(
                User.first_name,
                User.username,
                func.coalesce(
                    func.sum(UserCard.quantity),
                    0,
                ).label("card_count"),
            )
            .join(
                UserCard,
                UserCard.user_id == User.id,
                isouter=True,
            )
            .group_by(
                User.id,
                User.first_name,
                User.username,
            )
            .order_by(
                func.coalesce(
                    func.sum(UserCard.quantity),
                    0,
                ).desc()
            )
            .limit(15)
        )

        rows = result.all()

    if not rows:
        await message.answer(
            "🏆 Ranking မရှိသေးပါ။"
        )
        return

    text = "🏆 <b>GLOBAL TOP 15</b>\n\n"

    medals = [
        "🥇",
        "🥈",
        "🥉",
    ]

    for index, row in enumerate(rows, start=1):
        medal = (
            medals[index - 1]
            if index <= 3
            else f"<b>{index}.</b>"
        )

        name = row.first_name or "Player"

        text += (
            f"{medal} "
            f"<b>{name}</b> — "
            f"🎴 {row.card_count}\n"
        )

    await message.answer(text)


# =========================================================
# /RANKINGS
# =========================================================

@router.message(Command("rankings"))
async def rankings_command(message: Message):
    await top_command(message)


# =========================================================
# /SEARCH
# =========================================================

@router.message(Command("search"))
async def search_command(message: Message):
    parts = message.text.split(maxsplit=1)

    if len(parts) < 2:
        await message.answer(
            "🔎 <b>Card Search</b>\n\n"
            "အသုံးပြုပုံ:\n"
            "<code>/search Card Name</code>\n\n"
            "ဥပမာ:\n"
            "<code>/search Naruto</code>"
        )
        return

    keyword = parts[1].strip()

    async with SessionLocal() as session:
        result = await session.execute(
            select(Card)
            .where(
                Card.name.ilike(
                    f"%{keyword}%"
                )
            )
            .order_by(Card.id.asc())
            .limit(10)
        )

        cards = result.scalars().all()

    if not cards:
        await message.answer(
            f"❌ <b>{keyword}</b> ကို "
            "Card Database ထဲမှာ မတွေ့ပါ။"
        )
        return

    text = (
        f"🔎 <b>Search Results</b>\n"
        f"Keyword: <code>{keyword}</code>\n\n"
    )

    for card in cards:
        text += (
            f"🎴 #{card.id:04d} "
            f"<b>{card.name}</b>\n"
            f"✦ {card.rarity}\n\n"
        )

    await message.answer(text)


# =========================================================
# /CHECK
# =========================================================

@router.message(Command("check"))
async def check_command(message: Message):
    parts = message.text.split(maxsplit=1)

    if len(parts) < 2:
        await message.answer(
            "🎴 အသုံးပြုပုံ:\n"
            "<code>/check CARD_ID</code>\n\n"
            "ဥပမာ:\n"
            "<code>/check 21</code>"
        )
        return

    try:
        card_id = int(parts[1])
    except ValueError:
        await message.answer(
            "❌ Card ID မှားနေပါတယ်။"
        )
        return

    async with SessionLocal() as session:
        result = await session.execute(
            select(Card).where(
                Card.id == card_id
            )
        )

        card = result.scalar_one_or_none()

    if card is None:
        await message.answer(
            "❌ ဒီ Card ID မရှိပါ။"
        )
        return

    premium = (
        "💎 PREMIUM EDITION"
        if card.is_premium
        else ""
    )

    text = (
        f"🎴 <b>{card.name}</b>\n\n"
        f"🆔 ID: <code>{card.id:04d}</code>\n"
        f"✦ Rarity: <b>{card.rarity}</b>\n"
        f"{premium}\n\n"
        f"⚔️ Attack: <b>{card.attack}</b>\n"
        f"🛡️ Defense: <b>{card.defense}</b>\n"
        f"❤️ HP: <b>{card.hp}</b>\n"
        f"💨 Speed: <b>{card.speed}</b>\n"
    )

    if card.element:
        text += f"🌟 Element: {card.element}\n"

    if card.card_class:
        text += f"🎭 Class: {card.card_class}\n"

    if card.base_price:
        text += (
            f"\n💰 Sell Price: "
            f"<b>{card.base_price:,}</b> Coins"
        )

    if card.description:
        text += (
            f"\n\n📖 {card.description}"
        )

    await message.answer(text)


# =========================================================
# /FAV
# =========================================================

@router.message(Command("fav"))
async def fav_command(message: Message):
    user = await get_user(
        message.from_user.id
    )

    if user is None:
        await message.answer(
            "❌ /start ကိုအရင်နှိပ်ပါ။"
        )
        return

    parts = message.text.split(maxsplit=1)

    if len(parts) < 2:
        await message.answer(
            "❤️ အသုံးပြုပုံ:\n"
            "<code>/fav CARD_ID</code>"
        )
        return

    try:
        card_id = int(parts[1])
    except ValueError:
        await message.answer(
            "❌ Card ID မှားနေပါတယ်။"
        )
        return

    async with SessionLocal() as session:
        result = await session.execute(
            select(UserCard).where(
                UserCard.user_id == user.id,
                UserCard.card_id == card_id,
            )
        )

        user_card = result.scalar_one_or_none()

        if user_card is None:
            await message.answer(
                "❌ ဒီ Card ကို မပိုင်ပါ။"
            )
            return

        user_card.is_favorite = True

        await session.commit()

    await message.answer(
        "❤️ Card ကို Favorite ထည့်ပြီးပါပြီ။"
    )


# =========================================================
# /UNFAV
# =========================================================

@router.message(Command("unfav"))
async def unfav_command(message: Message):
    user = await get_user(
        message.from_user.id
    )

    if user is None:
        await message.answer(
            "❌ /start ကိုအရင်နှိပ်ပါ။"
        )
        return

    parts = message.text.split(maxsplit=1)

    if len(parts) < 2:
        await message.answer(
            "💔 အသုံးပြုပုံ:\n"
            "<code>/unfav CARD_ID</code>"
        )
        return

    try:
        card_id = int(parts[1])
    except ValueError:
        await message.answer(
            "❌ Card ID မှားနေပါတယ်။"
        )
        return

    async with SessionLocal() as session:
        result = await session.execute(
            select(UserCard).where(
                UserCard.user_id == user.id,
                UserCard.card_id == card_id,
            )
        )

        user_card = result.scalar_one_or_none()

        if user_card is None:
            await message.answer(
                "❌ ဒီ Card ကို မပိုင်ပါ။"
            )
            return

        user_card.is_favorite = False

        await session.commit()

    await message.answer(
        "💔 Favorite ကနေ ဖယ်ပြီးပါပြီ။"
    )
