
import random
from datetime import datetime, timezone

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)

from sqlalchemy import select

from database import (
    SessionLocal,
    User,
    Group,
    Card,
    UserCard,
    CatchLog,
    CardDrop,
)


router = Router()


# =========================================================
# SETTINGS
# =========================================================

XP_REWARD = 10


# =========================================================
# RANDOM CARD
# =========================================================

async def get_random_card(session):
    result = await session.execute(
        select(Card)
    )

    cards = result.scalars().all()

    if not cards:
        return None

    return random.choice(cards)


# =========================================================
# CATCH BUTTON
# =========================================================

def catch_keyboard(drop_id: int):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🎴 CATCH",
                    callback_data=f"catch:{drop_id}",
                )
            ]
        ]
    )


# =========================================================
# /DROP
# =========================================================

@router.message(Command("drop"))
async def drop_command(message: Message):

    if message.from_user is None:
        return

    # -----------------------------------------------------
    # GROUP ONLY
    # -----------------------------------------------------

    if message.chat.type not in (
        "group",
        "supergroup",
    ):
        await message.answer(
            "❌ <b>Card drops can only be used in groups.</b>",
            parse_mode="HTML",
        )
        return

    telegram_group_id = message.chat.id

    async with SessionLocal() as session:

        # =================================================
        # GROUP
        # =================================================

        group_result = await session.execute(
            select(Group).where(
                Group.telegram_id == telegram_group_id
            )
        )

        group = group_result.scalar_one_or_none()

        if group is None:

            group = Group(
                telegram_id=telegram_group_id,
                title=message.chat.title or "Telegram Group",
                username=message.chat.username,
                enabled=True,
                drop_enabled=True,
            )

            session.add(group)
            await session.flush()

        if not group.enabled:

            await message.answer(
                "❌ <b>Nexus Catch is disabled in this group.</b>",
                parse_mode="HTML",
            )
            return

        if not group.drop_enabled:

            await message.answer(
                "⏸️ <b>Card drops are disabled.</b>",
                parse_mode="HTML",
            )
            return

        # =================================================
        # CHECK EXISTING ACTIVE DROP
        # =================================================

        active_result = await session.execute(
            select(CardDrop).where(
                CardDrop.group_id == group.id,
                CardDrop.active.is_(True),
            )
        )

        active_drop = active_result.scalar_one_or_none()

        if active_drop is not None:

            await message.answer(
                "🎴 <b>There is already a card waiting!</b>\n\n"
                "👆 Use the <b>CATCH</b> button first.",
                parse_mode="HTML",
            )
            return

        # =================================================
        # RANDOM CARD
        # =================================================

        card = await get_random_card(session)

        if card is None:

            await message.answer(
                "❌ <b>No cards available.</b>\n\n"
                "Admin needs to add cards first.",
                parse_mode="HTML",
            )
            return

        # =================================================
        # SEND DROP MESSAGE
        # =================================================

        text = (
            "╔══════════════════════════╗\n"
            "        🎴 <b>CARD DROP!</b>\n"
            "╚══════════════════════════╝\n\n"
            "🔥 <b>A new card has appeared!</b>\n\n"
            f"✨ <b>{card.name}</b>\n"
            f"💠 Rarity: <b>{card.rarity}</b>\n\n"
            "🏃 <b>Be the first to catch it!</b>"
        )

        sent_message = await message.answer(
            text,
            parse_mode="HTML",
            reply_markup=catch_keyboard(0),
        )

        # =================================================
        # CREATE DROP
        # =================================================

        drop = CardDrop(
            group_id=group.id,
            card_id=card.id,
            message_id=sent_message.message_id,
            active=True,
        )

        session.add(drop)

        await session.flush()

        # =================================================
        # UPDATE BUTTON WITH REAL DROP ID
        # =================================================

        await sent_message.edit_reply_markup(
            reply_markup=catch_keyboard(drop.id)
        )

        await session.commit()


# =========================================================
# CATCH BUTTON
# =========================================================

@router.callback_query(
    F.data.startswith("catch:")
)
async def catch_callback(
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
            "❌ Invalid catch.",
            show_alert=True,
        )
        return

    telegram_user_id = callback.from_user.id

    async with SessionLocal() as session:

        # =================================================
        # GET USER
        # =================================================

        user_result = await session.execute(
            select(User).where(
                User.telegram_id == telegram_user_id
            )
        )

        user = user_result.scalar_one_or_none()

        if user is None:

            user = User(
                telegram_id=telegram_user_id,
                username=callback.from_user.username,
                first_name=(
                    callback.from_user.first_name
                    or "Player"
                ),
            )

            session.add(user)

            await session.flush()

        # =================================================
        # BAN CHECK
        # =================================================

        if user.is_banned:

            await callback.answer(
                "🚫 You are banned.",
                show_alert=True,
            )
            return

        # =================================================
        # LOCK DROP
        # =================================================

        result = await session.execute(
            select(CardDrop)
            .where(
                CardDrop.id == drop_id
            )
            .with_for_update()
        )

        drop = result.scalar_one_or_none()

        if drop is None:

            await callback.answer(
                "❌ This card drop does not exist.",
                show_alert=True,
            )
            return

        # =================================================
        # ALREADY CAUGHT
        # =================================================

        if not drop.active:

            await callback.answer(
                "❌ Too late! This card has already been caught.",
                show_alert=True,
            )
            return

        # =================================================
        # GET CARD
        # =================================================

        card_result = await session.execute(
            select(Card).where(
                Card.id == drop.card_id
            )
        )

        card = card_result.scalar_one_or_none()

        if card is None:

            drop.active = False

            await session.commit()

            await callback.answer(
                "❌ Card no longer exists.",
                show_alert=True,
            )
            return

        # =================================================
        # MARK AS CAUGHT
        # =================================================

        drop.active = False
        drop.caught_by = user.id
        drop.caught_at = datetime.now(
            timezone.utc
        )

        # =================================================
        # USER CARD
        # =================================================

        user_card_result = await session.execute(
            select(UserCard).where(
                UserCard.user_id == user.id,
                UserCard.card_id == card.id,
            )
        )

        user_card = (
            user_card_result.scalar_one_or_none()
        )

        if user_card is None:

            user_card = UserCard(
                user_id=user.id,
                card_id=card.id,
                level=1,
                xp=0,
                quantity=1,
                is_favorite=False,
                is_locked=False,
            )

            session.add(user_card)

            is_duplicate = False
            quantity = 1

        else:

            user_card.quantity += 1

            is_duplicate = True
            quantity = user_card.quantity

        # =================================================
        # CATCH LOG
        # =================================================

        catch_log = CatchLog(
            user_id=user.id,
            group_id=drop.group_id,
            card_id=card.id,
            rarity=card.rarity,
            is_duplicate=is_duplicate,
        )

        session.add(catch_log)

        # =================================================
        # XP
        # =================================================

        user.xp += XP_REWARD

        # =================================================
        # LEVEL UP
        # =================================================

        level_up = False

        xp_required = user.level * 100

        if user.xp >= xp_required:

            user.xp -= xp_required
            user.level += 1

            level_up = True

        # =================================================
        # COMMIT
        # =================================================

        await session.commit()

        # =================================================
        # REMOVE CATCH BUTTON
        # =================================================

        try:

            await callback.message.edit_reply_markup(
                reply_markup=None
            )

        except Exception:
            pass

        # =================================================
        # SUCCESS MESSAGE
        # =================================================

        text = (
            "╔══════════════════════════╗\n"
            "      🏆 <b>CARD CAUGHT!</b>\n"
            "╚══════════════════════════╝\n\n"
            f"👤 <b>{user.first_name}</b>\n\n"
            f"🎴 <b>#{card.id:04d}</b>\n"
            f"✨ <b>{card.name}</b>\n"
            f"💠 Rarity: <b>{card.rarity}</b>\n\n"
            "🥇 <b>You were the FIRST to catch it!</b>\n"
            f"🃏 Quantity: <b>{quantity}</b>\n"
            f"✨ +{XP_REWARD} XP"
        )

        if level_up:

            text += (
                "\n\n"
                "🎊 <b>LEVEL UP!</b>\n"
                f"⭐ Level <b>{user.level}</b>"
            )

        await callback.message.edit_text(
            text,
            parse_mode="HTML",
        )

        await callback.answer(
            "🏆 You caught the card!",
        )
