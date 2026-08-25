from __future__ import annotations

import random
from collections import defaultdict
from datetime import datetime, timezone

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from sqlalchemy import select, func

from database import (
    SessionLocal,
    User,
    UserCard,
    Card,
    Group,
    CardDrop,
    CatchLog,
)


router = Router()


# =========================================================
# CONFIG
# =========================================================

OWNER_ID = 7974865879

# Group message count before automatic drop
DROP_MESSAGE_COUNT = 85

# At 1000 messages, give better cards
HIGH_DROP_MESSAGE_COUNT = 1000

PAGE_SIZE = 5


# Runtime message counters.
# This resets if Render restarts.
group_message_counts: dict[int, int] = defaultdict(int)


# =========================================================
# ADMIN / OWNER
# =========================================================

def is_owner(user_id: int) -> bool:
    return user_id == OWNER_ID


# =========================================================
# HTML ESCAPE
# =========================================================

def safe_text(value) -> str:
    if value is None:
        return ""

    text = str(value)

    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


# =========================================================
# GET / CREATE USER
# =========================================================

async def get_or_create_user(message: Message):
    if message.from_user is None:
        return None

    telegram_id = message.from_user.id

    async with SessionLocal() as session:

        result = await session.execute(
            select(User).where(
                User.telegram_id == telegram_id
            )
        )

        user = result.scalar_one_or_none()

        if user is None:

            user = User(
                telegram_id=telegram_id,
                username=message.from_user.username,
                first_name=message.from_user.first_name or "Player",
            )

            session.add(user)

            await session.commit()
            await session.refresh(user)

        else:

            user.username = message.from_user.username
            user.first_name = (
                message.from_user.first_name or user.first_name
            )

            await session.commit()

        return user


# =========================================================
# GET / CREATE GROUP
# =========================================================

async def get_or_create_group(message: Message):
    if message.chat.type not in ("group", "supergroup"):
        return None

    async with SessionLocal() as session:

        result = await session.execute(
            select(Group).where(
                Group.telegram_id == message.chat.id
            )
        )

        group = result.scalar_one_or_none()

        if group is None:

            group = Group(
                telegram_id=message.chat.id,
                title=message.chat.title or "Telegram Group",
                username=getattr(
                    message.chat,
                    "username",
                    None,
                ),
                enabled=True,
                drop_enabled=True,
            )

            session.add(group)

            await session.commit()
            await session.refresh(group)

        else:

            group.title = (
                message.chat.title or group.title
            )

            group.username = getattr(
                message.chat,
                "username",
                group.username,
            )

            await session.commit()

        return group


# =========================================================
# CARD KEYBOARD
# =========================================================

def catch_keyboard(drop_id: int) -> InlineKeyboardMarkup:

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🎴 CATCH CARD",
                    callback_data=f"catchcard:{drop_id}",
                )
            ]
        ]
    )


# =========================================================
# HAREM KEYBOARD
# =========================================================

def harem_keyboard(
    page: int,
    total_pages: int,
) -> InlineKeyboardMarkup:

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
# CARD TEXT
# =========================================================

def card_caption(card: Card) -> str:

    premium = " 💎" if card.is_premium else ""
    limited = " 🔥" if card.is_limited else ""
    shiny = " ✨" if card.is_shiny else ""
    animated = " 🎞" if card.is_animated else ""

    text = (
        "╔══════════════════════╗\n"
        "       🎴 <b>CARD DROP</b>\n"
        "╚══════════════════════╝\n\n"
        f"🎴 <b>#{card.id:04d}</b>\n"
        f"✨ <b>{safe_text(card.name)}</b>\n\n"
        f"💠 Rarity: <b>{safe_text(card.rarity)}</b>"
        f"{premium}{limited}{shiny}{animated}\n\n"
        f"⚔️ ATK: <b>{card.attack}</b>\n"
        f"🛡 DEF: <b>{card.defense}</b>\n"
        f"❤️ HP: <b>{card.hp}</b>\n"
        f"💨 Speed: <b>{card.speed}</b>\n"
    )

    if card.element:
        text += (
            f"\n🌟 Element: "
            f"<b>{safe_text(card.element)}</b>\n"
        )

    if card.card_class:
        text += (
            f"🎭 Class: "
            f"<b>{safe_text(card.card_class)}</b>\n"
        )

    if card.description:
        text += (
            f"\n📝 {safe_text(card.description)}\n"
        )

    text += (
        "\n━━━━━━━━━━━━━━━━━━━━\n"
        "⚡ <b>First person to press CATCH gets this card!</b>"
    )

    return text


# =========================================================
# CHOOSE RANDOM CARD
# =========================================================

async def choose_random_card(
    high_quality: bool = False,
):
    async with SessionLocal() as session:

        result = await session.execute(
            select(Card)
        )

        cards = list(result.scalars().all())

        if not cards:
            return None

        # At 1000 messages prefer premium / legendary /
        # mythic / high rarity cards.
        if high_quality:

            preferred = [
                card
                for card in cards
                if card.is_premium
                or card.is_limited
                or card.rarity.lower()
                in {
                    "legendary",
                    "mythic",
                    "premium",
                    "secret",
                }
            ]

            if preferred:
                return random.choice(preferred)

        return random.choice(cards)


# =========================================================
# SEND DROP
# =========================================================

async def create_card_drop(
    message: Message,
    card: Card,
):

    group = await get_or_create_group(message)

    if group is None:
        return

    async with SessionLocal() as session:

        # Make previous active drops inactive.
        old_result = await session.execute(
            select(CardDrop).where(
                CardDrop.group_id == group.id,
                CardDrop.active == True,
            )
        )

        old_drops = old_result.scalars().all()

        for old_drop in old_drops:
            old_drop.active = False

        drop = CardDrop(
            group_id=group.id,
            card_id=card.id,
            message_id=0,
            active=True,
        )

        session.add(drop)

        await session.commit()
        await session.refresh(drop)

        caption = card_caption(card)

        sent_message = None

        if card.image_url:

            try:

                sent_message = await message.answer_photo(
                    photo=card.image_url,
                    caption=caption,
                    parse_mode="HTML",
                    reply_markup=catch_keyboard(drop.id),
                )

            except Exception:

                sent_message = await message.answer(
                    caption,
                    parse_mode="HTML",
                    reply_markup=catch_keyboard(drop.id),
                )

        else:

            sent_message = await message.answer(
                caption,
                parse_mode="HTML",
                reply_markup=catch_keyboard(drop.id),
            )

        drop.message_id = sent_message.message_id

        await session.commit()


# =========================================================
# AUTO DROP
# =========================================================

@router.message(
    F.chat.type.in_({"group", "supergroup"})
)
async def group_message_counter(message: Message):

    if message.from_user is None:
        return

    # Ignore bot messages.
    if message.from_user.is_bot:
        return

    group_id = message.chat.id

    group_message_counts[group_id] += 1

    current_count = group_message_counts[group_id]

    # Every 85 messages.
    if current_count < DROP_MESSAGE_COUNT:
        return

    # Reset counter immediately.
    group_message_counts[group_id] = 0

    high_quality = (
        current_count >= HIGH_DROP_MESSAGE_COUNT
    )

    card = await choose_random_card(
        high_quality=high_quality
    )

    if card is None:
        return

    await create_card_drop(
        message,
        card,
    )


# =========================================================
# MANUAL DROP
# =========================================================

@router.message(Command("dropcard"))
async def dropcard_command(message: Message):

    if message.from_user is None:
        return

    if not is_owner(message.from_user.id):

        await message.answer(
            "❌ <b>Owner Only</b>\n\n"
            "Only the bot owner can manually drop cards.",
            parse_mode="HTML",
        )

        return

    parts = message.text.split() if message.text else []

    if len(parts) < 2:

        await message.answer(
            "🎴 <b>Manual Card Drop</b>\n\n"
            "Usage:\n"
            "<code>/dropcard 21</code>\n\n"
            "You can drop any card ID.",
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
                f"❌ Card <code>{card_id:04d}</code> "
                "not found.",
                parse_mode="HTML",
            )

            return

    await create_card_drop(
        message,
        card,
    )


# =========================================================
# CATCH CARD
# =========================================================

@router.callback_query(
    F.data.startswith("catchcard:")
)
async def catch_card_callback(
    callback: CallbackQuery,
):

    if callback.message is None:
        await callback.answer()
        return

    try:
        drop_id = int(
            callback.data.split(":")[1]
        )
    except (ValueError, IndexError):

        await callback.answer(
            "❌ Invalid drop.",
            show_alert=True,
        )

        return

    if callback.from_user is None:
        await callback.answer()
        return

    telegram_id = callback.from_user.id

    async with SessionLocal() as session:

        # -------------------------------------------------
        # USER
        # -------------------------------------------------

        user_result = await session.execute(
            select(User).where(
                User.telegram_id == telegram_id
            )
        )

        user = user_result.scalar_one_or_none()

        if user is None:

            user = User(
                telegram_id=telegram_id,
                username=callback.from_user.username,
                first_name=(
                    callback.from_user.first_name
                    or "Player"
                ),
            )

            session.add(user)

            await session.flush()

        # -------------------------------------------------
        # DROP
        # -------------------------------------------------

        drop_result = await session.execute(
            select(CardDrop).where(
                CardDrop.id == drop_id
            )
        )

        drop = drop_result.scalar_one_or_none()

        if drop is None:

            await callback.answer(
                "❌ This drop no longer exists.",
                show_alert=True,
            )

            return

        # -------------------------------------------------
        # FIRST USER ONLY
        # -------------------------------------------------

        if not drop.active or drop.caught_by is not None:

            await callback.answer(
                "❌ Too late! Someone already caught it.",
                show_alert=True,
            )

            return

        # -------------------------------------------------
        # CARD
        # -------------------------------------------------

        card_result = await session.execute(
            select(Card).where(
                Card.id == drop.card_id
            )
        )

        card = card_result.scalar_one_or_none()

        if card is None:

            await callback.answer(
                "❌ Card not found.",
                show_alert=True,
            )

            return

        # -------------------------------------------------
        # CATCH
        # -------------------------------------------------

        drop.active = False
        drop.caught_by = user.id
        drop.caught_at = datetime.now(timezone.utc)

        # -------------------------------------------------
        # EXISTING USER CARD
        # -------------------------------------------------

        user_card_result = await session.execute(
            select(UserCard).where(
                UserCard.user_id == user.id,
                UserCard.card_id == card.id,
            )
        )

        user_card = (
            user_card_result.scalar_one_or_none()
        )

        duplicate = False

        if user_card is None:

            user_card = UserCard(
                user_id=user.id,
                card_id=card.id,
                level=1,
                xp=0,
                quantity=1,
            )

            session.add(user_card)

        else:

            user_card.quantity += 1
            duplicate = True

        # -------------------------------------------------
        # CATCH LOG
        # -------------------------------------------------

        catch_log = CatchLog(
            user_id=user.id,
            group_id=drop.group_id,
            card_id=card.id,
            rarity=card.rarity,
            is_duplicate=duplicate,
        )

        session.add(catch_log)

        await session.commit()

        # -------------------------------------------------
        # BUTTON DISABLE
        # -------------------------------------------------

        try:

            disabled_keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="✅ CAUGHT",
                            callback_data="catchcard:done",
                        )
                    ]
                ]
            )

            await callback.message.edit_reply_markup(
                reply_markup=disabled_keyboard
            )

        except Exception:
            pass

        # -------------------------------------------------
        # RESULT
        # -------------------------------------------------

        await callback.answer(
            f"🎴 {card.name} caught!",
            show_alert=False,
        )

        if duplicate:

            await callback.message.answer(
                "🎉 <b>CARD CAUGHT!</b>\n\n"
                f"👤 <b>{safe_text(user.first_name)}</b>\n"
                f"🎴 <b>#{card.id:04d}</b> "
                f"{safe_text(card.name)}\n"
                f"💠 {safe_text(card.rarity)}\n\n"
                f"📦 Duplicate!\n"
                f"Quantity: <b>×{user_card.quantity}</b>",
                parse_mode="HTML",
            )

        else:

            await callback.message.answer(
                "🎉 <b>CARD CAUGHT!</b>\n\n"
                f"👤 <b>{safe_text(user.first_name)}</b>\n"
                f"🎴 <b>#{card.id:04d}</b> "
                f"{safe_text(card.name)}\n"
                f"💠 {safe_text(card.rarity)}\n\n"
                "✨ Added to your Harem!",
                parse_mode="HTML",
            )


# =========================================================
# /ADDCard
#
# Usage:
# /addcard Name | Rarity | Attack | Defense | HP | Speed
#
# Then reply to a photo with:
# /addcard Name | Rarity | Attack | Defense | HP | Speed
#
# Example:
# /addcard Naruto | Legendary | 95 | 90 | 120 | 85
# =========================================================

@router.message(Command("addcard"))
async def addcard_command(message: Message):

    if message.from_user is None:
        return

    if not is_owner(message.from_user.id):

        await message.answer(
            "❌ <b>Admin / Owner Only</b>\n\n"
            "You don't have permission to add cards.",
            parse_mode="HTML",
        )

        return

    parts = message.text.split("|") if message.text else []

    if len(parts) < 6:

        await message.answer(
            "🎴 <b>ADD CARD</b>\n\n"
            "Reply to a card image and send:\n\n"
            "<code>"
            "/addcard Name | Rarity | ATK | DEF | HP | Speed"
            "</code>\n\n"
            "Example:\n"
            "<code>"
            "/addcard Naruto | Legendary | 95 | 90 | 120 | 85"
            "</code>\n\n"
            "The replied photo will become the card image.",
            parse_mode="HTML",
        )

        return

    try:

        name = parts[0].replace("/addcard", "").strip()
        rarity = parts[1].strip()
        attack = int(parts[2].strip())
        defense = int(parts[3].strip())
        hp = int(parts[4].strip())
        speed = int(parts[5].strip())

    except (ValueError, IndexError):

        await message.answer(
            "❌ Invalid card format.",
            parse_mode="HTML",
        )

        return

    if not name:

        await message.answer(
            "❌ Card name cannot be empty."
        )

        return

    # -----------------------------------------------------
    # IMAGE
    # -----------------------------------------------------

    image_url = None

    if message.reply_to_message:

        replied = message.reply_to_message

        if replied.photo:

            # Telegram file_id works as photo identifier.
            image_url = replied.photo[-1].file_id

        elif replied.document:

            mime = replied.document.mime_type or ""

            if mime.startswith("image/"):
                image_url = replied.document.file_id

    # -----------------------------------------------------
    # CARD TYPE
    # -----------------------------------------------------

    rarity_lower = rarity.lower()

    is_premium = (
        rarity_lower
        in {
            "premium",
            "premium edition",
        }
    )

    is_limited = (
        "limited" in rarity_lower
        or "event" in rarity_lower
    )

    is_shiny = (
        "shiny" in rarity_lower
    )

    is_animated = (
        "animated" in rarity_lower
        or "animation" in rarity_lower
    )

    async with SessionLocal() as session:

        card = Card(
            name=name,
            rarity=rarity,
            attack=attack,
            defense=defense,
            hp=hp,
            speed=speed,
            image_url=image_url,
            base_price=100,
            is_limited=is_limited,
            is_shiny=is_shiny,
            is_animated=is_animated,
            is_premium=is_premium,
        )

        session.add(card)

        await session.commit()
        await session.refresh(card)

    await message.answer(
        "✅ <b>CARD ADDED!</b>\n\n"
        f"🎴 ID: <code>{card.id:04d}</code>\n"
        f"✨ Name: <b>{safe_text(card.name)}</b>\n"
        f"💠 Rarity: <b>{safe_text(card.rarity)}</b>\n"
        f"⚔️ ATK: <b>{card.attack}</b>\n"
        f"🛡 DEF: <b>{card.defense}</b>\n"
        f"❤️ HP: <b>{card.hp}</b>\n"
        f"💨 Speed: <b>{card.speed}</b>\n"
        f"🖼 Image: "
        f"<b>{'YES' if image_url else 'NO'}</b>",
        parse_mode="HTML",
    )


# =========================================================
# /CHECK
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
        f"✨ Name: <b>{safe_text(card.name)}</b>\n"
        f"💠 Rarity: <b>{safe_text(card.rarity)}</b>\n\n"
        f"⚔️ ATK: <b>{card.attack}</b>\n"
        f"🛡 DEF: <b>{card.defense}</b>\n"
        f"❤️ HP: <b>{card.hp}</b>\n"
        f"💨 Speed: <b>{card.speed}</b>\n\n"
        f"🌟 Element: "
        f"<b>{safe_text(card.element or 'Unknown')}</b>\n"
        f"🎭 Class: "
        f"<b>{safe_text(card.card_class or 'Unknown')}</b>\n"
        f"💰 Base Price: "
        f"<b>{card.base_price:,}</b> Coins\n"
    )

    if card.description:

        text += (
            f"\n📝 <b>Description</b>\n"
            f"{safe_text(card.description)}\n"
        )

    if card.image_url:

        try:

            await message.answer_photo(
                photo=card.image_url,
                caption=text,
                parse_mode="HTML",
            )

            return

        except Exception:
            pass

    await message.answer(
        text,
        parse_mode="HTML",
    )


# =========================================================
# /HAREM
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
            select(
                func.count(UserCard.id)
            ).where(
                UserCard.user_id == user.id
            )
        )

        total = count_result.scalar() or 0

        if total == 0:

            await message.answer(
                "🎴 <b>YOUR HAREM</b>\n\n"
                "📭 You don't have any cards yet.\n\n"
                "✨ Wait for a card drop!",
                parse_mode="HTML",
            )

            return

        total_pages = max(
            1,
            (total + PAGE_SIZE - 1)
            // PAGE_SIZE,
        )

        page = max(
            1,
            min(page, total_pages),
        )

        offset = (
            page - 1
        ) * PAGE_SIZE

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
            f"👤 <b>{safe_text(user.first_name)}</b>",
            f"🃏 Cards: <b>{total}</b>",
            "",
        ]

        for user_card, card in rows:

            favorite = (
                " ❤️"
                if user_card.is_favorite
                else ""
            )

            locked = (
                " 🔒"
                if user_card.is_locked
                else ""
            )

            lines.append(
                f"🎴 <b>#{card.id:04d}</b> — "
                f"<b>{safe_text(card.name)}</b>"
            )

            lines.append(
                f"   ✦ {safe_text(card.rarity)}"
                f" • Lv.{user_card.level}"
                f" • ×{user_card.quantity}"
                f"{favorite}{locked}"
            )

            lines.append("")

        lines.append(
            "━━━━━━━━━━━━━━━━━━━━"
        )

        lines.append(
            f"📖 Page <b>{page}</b>/"
            f"<b>{total_pages}</b>"
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

        page = int(
            data.split(":")[1]
        )

    except (ValueError, IndexError):

        page = 1

    await update_harem_message(
        callback.message,
        callback.from_user.id,
        page,
    )


async def update_harem_message(
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
            select(
                func.count(UserCard.id)
            ).where(
                UserCard.user_id == user.id
            )
        )

        total = count_result.scalar() or 0

        if total == 0:

            await message.edit_text(
                "🎴 <b>YOUR HAREM</b>\n\n"
                "📭 Your collection is empty.",
                parse_mode="HTML",
            )

            return

        total_pages = max(
            1,
            (total + PAGE_SIZE - 1)
            // PAGE_SIZE,
        )

        page = max(
            1,
            min(page, total_pages),
        )

        offset = (
            page - 1
        ) * PAGE_SIZE

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
            f"👤 <b>{safe_text(user.first_name)}</b>",
            f"🃏 Cards: <b>{total}</b>",
            "",
        ]

        for user_card, card in rows:

            favorite = (
                " ❤️"
                if user_card.is_favorite
                else ""
            )

            locked = (
                " 🔒"
                if user_card.is_locked
                else ""
            )

            lines.append(
                f"🎴 <b>#{card.id:04d}</b> — "
                f"<b>{safe_text(card.name)}</b>"
            )

            lines.append(
                f"   ✦ {safe_text(card.rarity)}"
                f" • Lv.{user_card.level}"
                f" • ×{user_card.quantity}"
                f"{favorite}{locked}"
            )

            lines.append("")

        lines.append(
            "━━━━━━━━━━━━━━━━━━━━"
        )

        lines.append(
            f"📖 Page <b>{page}</b>/"
            f"<b>{total_pages}</b>"
        )

        await message.edit_text(
            "\n".join(lines),
            parse_mode="HTML",
            reply_markup=harem_keyboard(
                page,
                total_pages,
            ),
        )


# =========================================================
# /FAV
# =========================================================

@router.message(Command("fav"))
async def fav_command(message: Message):

    parts = message.text.split() if message.text else []

    if len(parts) < 2:

        await message.answer(
            "❤️ Usage: "
            "<code>/fav 0021</code>",
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

    if message.from_user is None:
        return

    async with SessionLocal() as session:

        user_result = await session.execute(
            select(User).where(
                User.telegram_id
                == message.from_user.id
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
        "added to favorites!",
        parse_mode="HTML",
    )


# =========================================================
# /UNFAV
# =========================================================

@router.message(Command("unfav"))
async def unfav_command(message: Message):

    parts = message.text.split() if message.text else []

    if len(parts) < 2:

        await message.answer(
            "Usage: "
            "<code>/unfav 0021</code>",
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

    if message.from_user is None:
        return

    async with SessionLocal() as session:

        user_result = await session.execute(
            select(User).where(
                User.telegram_id
                == message.from_user.id
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
# /UPGRADE
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

    if message.from_user is None:
        return

    async with SessionLocal() as session:

        user_result = await session.execute(
            select(User).where(
                User.telegram_id
                == message.from_user.id
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
                "❌ Not enough Coins.\n\n"
                f"💰 Required: "
                f"<b>{cost:,}</b>\n"
                f"🪙 Your Coins: "
                f"<b>{user.coins:,}</b>",
                parse_mode="HTML",
            )

            return

        user.coins -= cost
        user_card.level += 1
        user_card.xp = 0

        await session.commit()

        new_level = user_card.level

    await message.answer(
        "⬆️ <b>CARD UPGRADED!</b>\n\n"
        f"🎴 Card: "
        f"<code>{card_id:04d}</code>\n"
        f"⭐ New Level: "
        f"<b>{new_level}</b>\n"
        f"💰 Cost: "
        f"<b>{cost:,}</b> Coins",
        parse_mode="HTML",
    )


# =========================================================
# /RESET
# =========================================================

@router.message(Command("reset"))
async def reset_command(message: Message):

    await message.answer(
        "🔄 <b>Harem Reset</b>\n\n"
        "Your cards are not deleted.\n"
        "Your collection remains safe.",
        parse_mode="HTML",
    )


# =========================================================
# DISABLE FINISHED CATCH CALLBACK
# =========================================================

@router.callback_query(
    F.data == "catchcard:done"
)
async def finished_catch_callback(
    callback: CallbackQuery,
):

    await callback.answer(
        "✅ This card has already been caught.",
        show_alert=True,
    )
