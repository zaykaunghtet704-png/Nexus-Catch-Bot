
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from sqlalchemy import select, func

from database import SessionLocal, User, UserCard, Card


router = Router()

PAGE_SIZE = 5


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


def harem_keyboard(page: int, total_pages: int):
    buttons = []

    if page > 1:
        buttons.append(
            InlineKeyboardButton(
                text="◀️ Previous",
                callback_data=f"harem:{page - 1}",
            )
        )

    buttons.append(
        InlineKeyboardButton(
            text=f"📖 {page}/{total_pages}",
            callback_data="harem:current",
        )
    )

    if page < total_pages:
        buttons.append(
            InlineKeyboardButton(
                text="Next ▶️",
                callback_data=f"harem:{page + 1}",
            )
        )

    return InlineKeyboardMarkup(
        inline_keyboard=[
            buttons,
            [
                InlineKeyboardButton(
                    text="🔄 Refresh",
                    callback_data=f"harem:{page}",
                )
            ],
        ]
    )


# =========================================================
# /harem
# =========================================================

@router.message(Command("harem"))
async def harem_command(message: Message):
    if message.from_user is None:
        return

    await show_harem(
        message,
        message.from_user.id,
        1,
    )


async def show_harem(
    message: Message,
    telegram_id: int,
    page: int,
):
    async with SessionLocal() as session:

        user_result = await session.execute(
            select(User).where(
                User.telegram_id == telegram_id
            )
        )

        user = user_result.scalar_one_or_none()

        if user is None:
            await message.answer(
                "❌ Please use /start first."
            )
            return

        count_result = await session.execute(
            select(func.count(UserCard.id)).where(
                UserCard.user_id == user.id
            )
        )

        total = count_result.scalar() or 0

        if total == 0:
            await message.answer(
                "🎴 <b>YOUR HAREM</b>\n\n"
                "📭 You don't have any cards yet.\n\n"
                "✨ Use the card catch command to get your first card!",
                parse_mode="HTML",
            )
            return

        total_pages = max(
            1,
            (total + PAGE_SIZE - 1) // PAGE_SIZE,
        )

        page = max(1, min(page, total_pages))

        offset = (page - 1) * PAGE_SIZE

        result = await session.execute(
            select(UserCard, Card)
            .join(
                Card,
                UserCard.card_id == Card.id,
            )
            .where(
                UserCard.user_id == user.id
            )
            .order_by(Card.id.asc())
            .offset(offset)
            .limit(PAGE_SIZE)
        )

        rows = result.all()

        lines = [
            "╔══════════════════════════╗",
            "        🎴 <b>HAREM</b>",
            "╚══════════════════════════╝",
            "",
            f"👤 <b>{user.first_name}</b>",
            f"🃏 Cards: <b>{total}</b>",
            "",
        ]

        for user_card, card in rows:

            favorite = " ❤️" if user_card.is_favorite else ""
            locked = " 🔒" if user_card.is_locked else ""

            lines.append(
                f"🎴 <b>#{card.id:04d}</b> — "
                f"<b>{card.name}</b>"
            )

            lines.append(
                f"   ✦ {card.rarity}"
                f" • Lv.{user_card.level}"
                f" • ×{user_card.quantity}"
                f"{favorite}{locked}"
            )

            lines.append("")

        lines.append("━━━━━━━━━━━━━━━━━━━━")
        lines.append(
            f"📖 Page <b>{page}</b>/<b>{total_pages}</b>"
        )

        await message.answer(
            "\n".join(lines),
            parse_mode="HTML",
            reply_markup=harem_keyboard(
                page,
                total_pages,
            ),
        )


# =========================================================
# HAREM PAGINATION
# =========================================================

@router.callback_query(
    F.data.startswith("harem:")
)
async def harem_callback(
    callback: CallbackQuery,
):
    await callback.answer()

    if callback.message is None:
        return

    data = callback.data

    if data == "harem:current":
        return

    try:
        page = int(data.split(":")[1])
    except (ValueError, IndexError):
        page = 1

    telegram_id = callback.from_user.id

    async with SessionLocal() as session:

        user_result = await session.execute(
            select(User).where(
                User.telegram_id == telegram_id
            )
        )

        user = user_result.scalar_one_or_none()

        if user is None:
            await callback.message.answer(
                "❌ Please use /start first."
            )
            return

        count_result = await session.execute(
            select(func.count(UserCard.id)).where(
                UserCard.user_id == user.id
            )
        )

        total = count_result.scalar() or 0

        if total == 0:
            await callback.message.edit_text(
                "🎴 <b>YOUR HAREM</b>\n\n"
                "📭 Your collection is empty.",
                parse_mode="HTML",
            )
            return

        total_pages = max(
            1,
            (total + PAGE_SIZE - 1) // PAGE_SIZE,
        )

        page = max(
            1,
            min(page, total_pages),
        )

        offset = (page - 1) * PAGE_SIZE

        result = await session.execute(
            select(UserCard, Card)
            .join(
                Card,
                UserCard.card_id == Card.id,
            )
            .where(
                UserCard.user_id == user.id
            )
            .order_by(Card.id.asc())
            .offset(offset)
            .limit(PAGE_SIZE)
        )

        rows = result.all()

        lines = [
            "╔══════════════════════════╗",
            "        🎴 <b>HAREM</b>",
            "╚══════════════════════════╝",
            "",
            f"👤 <b>{user.first_name}</b>",
            f"🃏 Cards: <b>{total}</b>",
            "",
        ]

        for user_card, card in rows:

            favorite = " ❤️" if user_card.is_favorite else ""
            locked = " 🔒" if user_card.is_locked else ""

            lines.append(
                f"🎴 <b>#{card.id:04d}</b> — "
                f"<b>{card.name}</b>"
            )

            lines.append(
                f"   ✦ {card.rarity}"
                f" • Lv.{user_card.level}"
                f" • ×{user_card.quantity}"
                f"{favorite}{locked}"
            )

            lines.append("")

        lines.append("━━━━━━━━━━━━━━━━━━━━")
        lines.append(
            f"📖 Page <b>{page}</b>/<b>{total_pages}</b>"
        )

        await callback.message.edit_text(
            "\n".join(lines),
            parse_mode="HTML",
            reply_markup=harem_keyboard(
                page,
                total_pages,
            ),
        )


# =========================================================
# /check
# =========================================================

@router.message(Command("check"))
async def check_command(message: Message):
    parts = message.text.split() if message.text else []

    if len(parts) < 2:
        await message.answer(
            "🎴 <b>Card Check</b>\n\n"
            "Usage:\n"
            "<code>/check 0021</code>",
            parse_mode="HTML",
        )
        return

    try:
        card_id = int(parts[1])
    except ValueError:
        await message.answer(
            "❌ Invalid card ID."
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
                "❌ Card not found."
            )
            return

        text = (
            "╔══════════════════════════╗\n"
            "        🎴 <b>CARD</b>\n"
            "╚══════════════════════════╝\n\n"
            f"🆔 ID: <code>{card.id:04d}</code>\n"
            f"✨ Name: <b>{card.name}</b>\n"
            f"💠 Rarity: <b>{card.rarity}</b>\n\n"
            f"⚔️ ATK: <b>{card.attack}</b>\n"
            f"🛡 DEF: <b>{card.defense}</b>\n"
            f"❤️ HP: <b>{card.hp}</b>\n"
            f"💨 Speed: <b>{card.speed}</b>\n\n"
            f"🌟 Element: <b>{card.element or 'Unknown'}</b>\n"
            f"🎭 Class: <b>{card.card_class or 'Unknown'}</b>\n"
            f"💰 Base Price: <b>{card.base_price:,}</b> Coins\n"
        )

        if card.description:
            text += (
                f"\n📝 <b>Description</b>\n"
                f"{card.description}\n"
            )

        if card.image_url:
            await message.answer_photo(
                photo=card.image_url,
                caption=text,
                parse_mode="HTML",
            )
        else:
            await message.answer(
                text,
                parse_mode="HTML",
            )


# =========================================================
# /fav
# =========================================================

@router.message(Command("fav"))
async def fav_command(message: Message):
    parts = message.text.split() if message.text else []

    if len(parts) < 2:
        await message.answer(
            "❤️ Usage: <code>/fav 0021</code>",
            parse_mode="HTML",
        )
        return

    try:
        card_id = int(parts[1])
    except ValueError:
        await message.answer(
            "❌ Invalid card ID."
        )
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

        result = await session.execute(
            select(UserCard).where(
                UserCard.user_id == user.id,
                UserCard.card_id == card_id,
            )
        )

        user_card = result.scalar_one_or_none()

        if user_card is None:
            await message.answer(
                "❌ You don't own this card."
            )
            return

        user_card.is_favorite = True

        await session.commit()

        await message.answer(
            f"❤️ Card <code>{card_id:04d}</code> "
            "has been added to your favorites!",
            parse_mode="HTML",
        )


# =========================================================
# /unfav
# =========================================================

@router.message(Command("unfav"))
async def unfav_command(message: Message):
    parts = message.text.split() if message.text else []

    if len(parts) < 2:
        await message.answer(
            "Usage: <code>/unfav 0021</code>",
            parse_mode="HTML",
        )
        return

    try:
        card_id = int(parts[1])
    except ValueError:
        await message.answer(
            "❌ Invalid card ID."
        )
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

        result = await session.execute(
            select(UserCard).where(
                UserCard.user_id == user.id,
                UserCard.card_id == card_id,
            )
        )

        user_card = result.scalar_one_or_none()

        if user_card is None:
            await message.answer(
                "❌ You don't own this card."
            )
            return

        user_card.is_favorite = False

        await session.commit()

        await message.answer(
            f"💔 Card <code>{card_id:04d}</code> "
            "removed from favorites.",
            parse_mode="HTML",
        )


# =========================================================
# /hmode
# =========================================================

@router.message(Command("hmode"))
async def hmode_command(message: Message):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="⭐ Highest Level",
                    callback_data="hmode:level",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="💠 Rarity",
                    callback_data="hmode:rarity",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="🆕 Newest",
                    callback_data="hmode:newest",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="🔢 Card ID",
                    callback_data="hmode:id",
                ),
            ],
        ]
    )

    await message.answer(
        "🎛 <b>HAREM MODE</b>\n\n"
        "Choose how you want your cards to be displayed:",
        parse_mode="HTML",
        reply_markup=keyboard,
    )


# =========================================================
# HMODE CALLBACK
# =========================================================

@router.callback_query(
    F.data.startswith("hmode:")
)
async def hmode_callback(
    callback: CallbackQuery,
):
    await callback.answer()

    mode = callback.data.split(":")[1]

    names = {
        "level": "⭐ Highest Level",
        "rarity": "💠 Rarity",
        "newest": "🆕 Newest",
        "id": "🔢 Card ID",
    }

    await callback.message.edit_text(
        "🎛 <b>HAREM MODE UPDATED</b>\n\n"
        f"Selected: <b>{names.get(mode, mode)}</b>\n\n"
        "✨ Your next /harem will use this mode.",
        parse_mode="HTML",
    )


# =========================================================
# /reset
# =========================================================

@router.message(Command("reset"))
async def reset_command(message: Message):
    await message.answer(
        "🔄 <b>Harem Reset</b>\n\n"
        "Your cards are not deleted.\n"
        "All cards will be visible again in your collection.",
        parse_mode="HTML",
    )


# =========================================================
# /upgrade
# =========================================================

@router.message(Command("upgrade"))
async def upgrade_command(message: Message):
    parts = message.text.split() if message.text else []

    if len(parts) < 2:
        await message.answer(
            "⬆️ <b>Card Upgrade</b>\n\n"
            "Usage:\n"
            "<code>/upgrade 0021</code>",
            parse_mode="HTML",
        )
        return

    try:
        card_id = int(parts[1])
    except ValueError:
        await message.answer(
            "❌ Invalid card ID."
        )
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

        result = await session.execute(
            select(UserCard).where(
                UserCard.user_id == user.id,
                UserCard.card_id == card_id,
            )
        )

        user_card = result.scalar_one_or_none()

        if user_card is None:
            await message.answer(
                "❌ You don't own this card."
            )
            return

        cost = user_card.level * 500

        if user.coins < cost:
            await message.answer(
                f"❌ Not enough Coins.\n\n"
                f"💰 Required: <b>{cost:,}</b>\n"
                f"🪙 Your Coins: <b>{user.coins:,}</b>",
                parse_mode="HTML",
            )
            return

        user.coins -= cost
        user_card.level += 1
        user_card.xp = 0

        await session.commit()

        await message.answer(
            "⬆️ <b>CARD UPGRADED!</b>\n\n"
            f"🎴 Card: <code>{card_id:04d}</code>\n"
            f"⭐ New Level: <b>{user_card.level}</b>\n"
            f"💰 Cost: <b>{cost:,}</b> Coins",
            parse_mode="HTML",
        )
