from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy import select, func

from database import SessionLocal, User, UserCard, Card


router = Router()


# =========================
# MAIN MENU
# =========================

def main_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🎴 My Cards",
                    callback_data="menu_cards"
                ),
                InlineKeyboardButton(
                    text="🎁 Packs",
                    callback_data="menu_packs"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="👤 Profile",
                    callback_data="menu_profile"
                ),
                InlineKeyboardButton(
                    text="💰 Balance",
                    callback_data="menu_balance"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="📊 Stats",
                    callback_data="menu_stats"
                ),
                InlineKeyboardButton(
                    text="🏆 Ranking",
                    callback_data="menu_ranking"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="🛒 Premium Shop",
                    callback_data="menu_shop"
                ),
                InlineKeyboardButton(
                    text="ℹ️ Help",
                    callback_data="menu_help"
                ),
            ],
        ]
    )


# =========================
# GET USER
# =========================

async def get_user(telegram_id: int):
    async with SessionLocal() as session:
        result = await session.execute(
            select(User).where(
                User.telegram_id == telegram_id
            )
        )

        return result.scalar_one_or_none()


# =========================
# /start
# =========================

@router.message(Command("start"))
async def start_command(message: Message):
    if message.from_user is None:
        return

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
                first_name=message.from_user.first_name or "Player",
            )

            session.add(user)
            await session.commit()
            await session.refresh(user)

        text = (
            "╔══════════════════════════════╗\n"
            "        ✦ <b>NEXUS CATCH</b> ✦\n"
            "╚══════════════════════════════╝\n\n"
            f"👋 Welcome, <b>{user.first_name}</b>!\n\n"
            "🎴 <b>ADVANCED CARD COLLECTION</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            f"⭐ Level: <b>{user.level}</b>\n"
            f"✨ XP: <b>{user.xp}</b>\n"
            f"💰 Coins: <b>{user.coins:,}</b>\n"
            f"💎 Gems: <b>{user.gems:,}</b>\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
            "🔥 Collect • Open • Battle • Trade\n"
            "👑 Discover the rarest Premium Edition cards!\n\n"
            "✨ <b>Choose an option below</b>"
        )

        await message.answer(
            text,
            parse_mode="HTML",
            reply_markup=main_menu(),
        )


# =========================
# /help
# =========================

@router.message(Command("help"))
async def help_command(message: Message):
    text = (
        "╔══════════════════════════╗\n"
        "       ℹ️ <b>NEXUS HELP</b>\n"
        "╚══════════════════════════╝\n\n"

        "👤 <b>PLAYER</b>\n"
        "┣ /start — Main Menu\n"
        "┣ /profile — Your Profile\n"
        "┣ /balance — Coins & Gems\n"
        "┗ /stats — Player Statistics\n\n"

        "🎴 <b>CARDS</b>\n"
        "┣ /cards — Card Collection\n"
        "┣ /collection — Collection Info\n"
        "┣ /card — Card Details\n"
        "┗ /search — Search Cards\n\n"

        "🎁 <b>PACKS</b>\n"
        "┣ /packs — Available Packs\n"
        "┣ /open — Open Pack\n"
        "┗ /pity — Pity Status\n\n"

        "💰 <b>ECONOMY</b>\n"
        "┣ /daily — Daily Reward\n"
        "┣ /shop — Shop\n"
        "┗ /sell — Sell Card\n\n"

        "⚔️ <b>COMING SOON</b>\n"
        "┣ Battle\n"
        "┣ Trading\n"
        "┣ Leaderboard\n"
        "┗ Events\n\n"

        "👑 <b>Premium Edition</b>\n"
        "The rarest card tier in Nexus Catch."
    )

    await message.answer(
        text,
        parse_mode="HTML",
        reply_markup=main_menu(),
    )


# =========================
# /profile
# =========================

@router.message(Command("profile"))
async def profile_command(message: Message):
    if message.from_user is None:
        return

    async with SessionLocal() as session:
        result = await session.execute(
            select(User).where(
                User.telegram_id == message.from_user.id
            )
        )

        user = result.scalar_one_or_none()

        if user is None:
            await message.answer(
                "❌ Profile not found.\n\n"
                "Please use /start first."
            )
            return

        card_result = await session.execute(
            select(func.count(UserCard.id)).where(
                UserCard.user_id == user.id
            )
        )

        card_count = card_result.scalar() or 0

        text = (
            "╔══════════════════════════╗\n"
            "        👤 <b>PROFILE</b>\n"
            "╚══════════════════════════╝\n\n"
            f"👤 Name: <b>{user.first_name}</b>\n"
            f"🆔 ID: <code>{user.telegram_id}</code>\n\n"
            f"⭐ Level: <b>{user.level}</b>\n"
            f"✨ XP: <b>{user.xp}</b>\n"
            f"🎴 Cards: <b>{card_count}</b>\n\n"
            f"💰 Coins: <b>{user.coins:,}</b>\n"
            f"💎 Gems: <b>{user.gems:,}</b>\n\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "👑 <b>NEXUS COLLECTOR</b>"
        )

        await message.answer(
            text,
            parse_mode="HTML",
            reply_markup=main_menu(),
        )


# =========================
# /balance
# =========================

@router.message(Command("balance"))
async def balance_command(message: Message):
    if message.from_user is None:
        return

    user = await get_user(message.from_user.id)

    if user is None:
        await message.answer(
            "❌ Please use /start first."
        )
        return

    text = (
        "╔══════════════════════════╗\n"
        "        💰 <b>WALLET</b>\n"
        "╚══════════════════════════╝\n\n"
        f"🪙 Coins\n"
        f"   <b>{user.coins:,}</b>\n\n"
        f"💎 Gems\n"
        f"   <b>{user.gems:,}</b>\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "💡 Use Coins to open packs and buy items."
    )

    await message.answer(
        text,
        parse_mode="HTML",
        reply_markup=main_menu(),
    )


# =========================
# /stats
# =========================

@router.message(Command("stats"))
async def stats_command(message: Message):
    if message.from_user is None:
        return

    async with SessionLocal() as session:
        result = await session.execute(
            select(User).where(
                User.telegram_id == message.from_user.id
            )
        )

        user = result.scalar_one_or_none()

        if user is None:
            await message.answer(
                "❌ Please use /start first."
            )
            return

        card_result = await session.execute(
            select(func.count(UserCard.id)).where(
                UserCard.user_id == user.id
            )
        )

        total_cards = card_result.scalar() or 0

        quantity_result = await session.execute(
            select(func.coalesce(func.sum(UserCard.quantity), 0)).where(
                UserCard.user_id == user.id
            )
        )

        total_quantity = quantity_result.scalar() or 0

        text = (
            "╔══════════════════════════╗\n"
            "        📊 <b>STATISTICS</b>\n"
            "╚══════════════════════════╝\n\n"
            f"⭐ Level: <b>{user.level}</b>\n"
            f"✨ XP: <b>{user.xp:,}</b>\n\n"
            f"🎴 Unique Cards: <b>{total_cards}</b>\n"
            f"🃏 Total Cards: <b>{total_quantity}</b>\n\n"
            f"💰 Coins: <b>{user.coins:,}</b>\n"
            f"💎 Gems: <b>{user.gems:,}</b>\n\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "🔥 Keep collecting to become a top collector!"
        )

        await message.answer(
            text,
            parse_mode="HTML",
            reply_markup=main_menu(),
        )


# =========================
# /cards
# =========================

@router.message(Command("cards"))
async def cards_command(message: Message):
    if message.from_user is None:
        return

    async with SessionLocal() as session:
        result = await session.execute(
            select(User).where(
                User.telegram_id == message.from_user.id
            )
        )

        user = result.scalar_one_or_none()

        if user is None:
            await message.answer(
                "❌ Please use /start first."
            )
            return

        cards_result = await session.execute(
            select(UserCard, Card)
            .join(Card, UserCard.card_id == Card.id)
            .where(UserCard.user_id == user.id)
            .order_by(Card.id.desc())
            .limit(20)
        )

        rows = cards_result.all()

        if not rows:
            await message.answer(
                "🎴 <b>YOUR COLLECTION</b>\n\n"
                "📭 Your collection is empty.\n\n"
                "🎁 Open a pack to discover your first card!",
                parse_mode="HTML",
                reply_markup=main_menu(),
            )
            return

        lines = [
            "╔══════════════════════════╗",
            "        🎴 <b>MY CARDS</b>",
            "╚══════════════════════════╝",
            "",
        ]

        for user_card, card in rows:
            favorite = " ❤️" if user_card.is_favorite else ""
            locked = " 🔒" if user_card.is_locked else ""

            lines.append(
                f"🎴 <b>#{card.id}</b> — {card.name}"
            )
            lines.append(
                f"   ✦ {card.rarity} | 💰 {card.id}"
                f"{favorite}{locked}"
            )
            lines.append("")

        lines.append("━━━━━━━━━━━━━━━━━━━━")
        lines.append("💡 Use /card <code>ID</code> for details.")

        await message.answer(
            "\n".join(lines),
            parse_mode="HTML",
            reply_markup=main_menu(),
        )


# =========================
# /collection
# =========================

@router.message(Command("collection"))
async def collection_command(message: Message):
    if message.from_user is None:
        return

    async with SessionLocal() as session:
        user_result = await session.execute(
            select(User).where(
                User.telegram_id == message.from_user.id
            )
        )

        user = user_result.scalar_one_or_none()

        if user is None:
            await message.answer(
                "❌ Please use /start first."
            )
            return

        unique_result = await session.execute(
            select(func.count(UserCard.id)).where(
                UserCard.user_id == user.id
            )
        )

        unique_cards = unique_result.scalar() or 0

        total_result = await session.execute(
            select(func.coalesce(func.sum(UserCard.quantity), 0)).where(
                UserCard.user_id == user.id
            )
        )

        total_cards = total_result.scalar() or 0

        text = (
            "╔══════════════════════════╗\n"
            "      🗃️ <b>COLLECTION</b>\n"
            "╚══════════════════════════╝\n\n"
            f"🎴 Unique Cards: <b>{unique_cards}</b>\n"
            f"🃏 Total Cards: <b>{total_cards}</b>\n\n"
            "📈 Collection Progress\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "🔒 More collection features coming soon.\n\n"
            "🎁 Open packs to expand your collection!"
        )

        await message.answer(
            text,
            parse_mode="HTML",
            reply_markup=main_menu(),
        )


# =========================
# CALLBACK: PROFILE
# =========================

@router.callback_query(F.data == "menu_profile")
async def menu_profile(callback: CallbackQuery):
    await callback.answer()

    if callback.from_user is None:
        return

    user = await get_user(callback.from_user.id)

    if user is None:
        await callback.message.answer(
            "❌ Please use /start first."
        )
        return

    text = (
        "╔══════════════════════════╗\n"
        "        👤 <b>PROFILE</b>\n"
        "╚══════════════════════════╝\n\n"
        f"👤 <b>{user.first_name}</b>\n"
        f"⭐ Level: <b>{user.level}</b>\n"
        f"✨ XP: <b>{user.xp}</b>\n"
        f"💰 Coins: <b>{user.coins:,}</b>\n"
        f"💎 Gems: <b>{user.gems:,}</b>"
    )

    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=main_menu(),
    )


# =========================
# CALLBACK: BALANCE
# =========================

@router.callback_query(F.data == "menu_balance")
async def menu_balance(callback: CallbackQuery):
    await callback.answer()

    user = await get_user(callback.from_user.id)

    if user is None:
        await callback.message.answer(
            "❌ Please use /start first."
        )
        return

    text = (
        "╔══════════════════════════╗\n"
        "        💰 <b>WALLET</b>\n"
        "╚══════════════════════════╝\n\n"
        f"🪙 Coins: <b>{user.coins:,}</b>\n"
        f"💎 Gems: <b>{user.gems:,}</b>"
    )

    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=main_menu(),
    )


# =========================
# CALLBACK: HELP
# =========================

@router.callback_query(F.data == "menu_help")
async def menu_help(callback: CallbackQuery):
    await callback.answer()

    text = (
        "╔══════════════════════════╗\n"
        "        ℹ️ <b>HELP</b>\n"
        "╚══════════════════════════╝\n\n"
        "🎴 <b>Cards</b> — Collect powerful Anime-style cards.\n\n"
        "🎁 <b>Packs</b> — Open packs and discover rare cards.\n\n"
        "💰 <b>Economy</b> — Earn Coins and Gems.\n\n"
        "⚔️ <b>Battle</b> — Coming soon.\n\n"
        "🏆 <b>Ranking</b> — Coming soon.\n\n"
        "👑 <b>Premium Edition</b> — The rarest tier."
    )

    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=main_menu(),
    )


# =========================
# CALLBACK: CARDS
# =========================

@router.callback_query(F.data == "menu_cards")
async def menu_cards(callback: CallbackQuery):
    await callback.answer()

    user = await get_user(callback.from_user.id)

    if user is None:
        await callback.message.answer(
            "❌ Please use /start first."
        )
        return

    async with SessionLocal() as session:
        result = await session.execute(
            select(func.count(UserCard.id)).where(
                UserCard.user_id == user.id
            )
        )

        card_count = result.scalar() or 0

    text = (
        "╔══════════════════════════╗\n"
        "        🎴 <b>MY CARDS</b>\n"
        "╚══════════════════════════╝\n\n"
        f"🃏 Cards Owned: <b>{card_count}</b>\n\n"
        "Use <b>/cards</b> to view your collection.\n\n"
        "🎁 More card features are coming soon!"
    )

    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=main_menu(),
    )


# =========================
# CALLBACK: PACKS
# =========================

@router.callback_query(F.data == "menu_packs")
async def menu_packs(callback: CallbackQuery):
    await callback.answer()

    text = (
        "╔══════════════════════════╗\n"
        "         🎁 <b>PACKS</b>\n"
        "╚══════════════════════════╝\n\n"
        "🎁 Basic Pack\n"
        "🎁 Rare Pack\n"
        "🎁 Premium Pack\n"
        "🎁 Event Pack\n\n"
        "🔥 Pack opening system is coming next!"
    )

    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=main_menu(),
    )


# =========================
# CALLBACK: STATS
# =========================

@router.callback_query(F.data == "menu_stats")
async def menu_stats(callback: CallbackQuery):
    await callback.answer()

    user = await get_user(callback.from_user.id)

    if user is None:
        return

    async with SessionLocal() as session:
        result = await session.execute(
            select(func.count(UserCard.id)).where(
                UserCard.user_id == user.id
            )
        )

        cards = result.scalar() or 0

    text = (
        "╔══════════════════════════╗\n"
        "        📊 <b>STATISTICS</b>\n"
        "╚══════════════════════════╝\n\n"
        f"⭐ Level: <b>{user.level}</b>\n"
        f"✨ XP: <b>{user.xp:,}</b>\n"
        f"🎴 Cards: <b>{cards}</b>\n"
        f"💰 Coins: <b>{user.coins:,}</b>\n"
        f"💎 Gems: <b>{user.gems:,}</b>"
    )

    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=main_menu(),
    )


# =========================
# CALLBACK: RANKING
# =========================

@router.callback_query(F.data == "menu_ranking")
async def menu_ranking(callback: CallbackQuery):
    await callback.answer()

    text = (
        "╔══════════════════════════╗\n"
        "        🏆 <b>RANKING</b>\n"
        "╚══════════════════════════╝\n\n"
        "🥇 Leaderboard system\n"
        "🥈 Collection ranking\n"
        "🥉 Wealth ranking\n\n"
        "🔥 Coming soon!"
    )

    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=main_menu(),
    )


# =========================
# CALLBACK: SHOP
# =========================

@router.callback_query(F.data == "menu_shop")
async def menu_shop(callback: CallbackQuery):
    await callback.answer()

    text = (
        "╔══════════════════════════╗\n"
        "       💎 <b>PREMIUM SHOP</b>\n"
        "╚══════════════════════════╝\n\n"
        "🎁 Packs\n"
        "💎 Gems\n"
        "✨ Special Items\n"
        "👑 Premium Edition\n\n"
        "🛒 Shop system is coming next!"
    )

    await callback.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=main_menu(),
    )
