
import random

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy import select

from database import (
    SessionLocal,
    User,
    Group,
    Card,
    UserCard,
    CatchLog,
)


router = Router()


# =========================================================
# CATCH SETTINGS
# =========================================================

CATCH_COOLDOWN = 3


# =========================================================
# GET USER
# =========================================================

async def get_user(telegram_id: int):
    async with SessionLocal() as session:
        result = await session.execute(
            select(User).where(
                User.telegram_id == telegram_id
            )
        )

        return result.scalar_one_or_none()


# =========================================================
# GET RANDOM CARD
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
# /catch
# =========================================================

@router.message(Command("catch"))
async def catch_command(message: Message):

    if message.from_user is None:
        return

    # -----------------------------------------------------
    # MUST BE GROUP
    # -----------------------------------------------------

    if message.chat.type not in (
        "group",
        "supergroup",
    ):
        await message.answer(
            "❌ <b>Catch can only be used in a group.</b>\n\n"
            "🎴 Go to a group where Nexus Catch is enabled.",
            parse_mode="HTML",
        )
        return

    telegram_user_id = message.from_user.id
    telegram_group_id = message.chat.id

    async with SessionLocal() as session:

        # =================================================
        # USER
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
                username=message.from_user.username,
                first_name=message.from_user.first_name or "Player",
            )

            session.add(user)
            await session.flush()

        # =================================================
        # CHECK BAN
        # =================================================

        if user.is_banned:
            await message.answer(
                "🚫 <b>You are banned from using Nexus Catch.</b>",
                parse_mode="HTML",
            )
            return

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

        # =================================================
        # GROUP ENABLE CHECK
        # =================================================

        if not group.enabled:
            await message.answer(
                "❌ <b>Nexus Catch is disabled in this group.</b>",
                parse_mode="HTML",
            )
            return

        if not group.drop_enabled:
            await message.answer(
                "⏸️ <b>Card drops are currently disabled.</b>",
                parse_mode="HTML",
            )
            return

        # =================================================
        # RANDOM CARD
        # =================================================

        card = await get_random_card(session)

        if card is None:
            await message.answer(
                "❌ <b>No cards are available.</b>\n\n"
                "Admin needs to add cards first.",
                parse_mode="HTML",
            )
            return

        # =================================================
        # CREATE CATCH LOG
        # =================================================

        catch_log = CatchLog(
            user_id=user.id,
            group_id=group.id,
            card_id=card.id,
            rarity=card.rarity,
            is_duplicate=False,
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

        user_card = user_card_result.scalar_one_or_none()

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

        else:

            user_card.quantity += 1

            is_duplicate = True

        catch_log.is_duplicate = is_duplicate

        session.add(catch_log)

        # =================================================
        # XP REWARD
        # =================================================

        xp_reward = 10

        user.xp += xp_reward

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
        # RESPONSE
        # =================================================

        if is_duplicate:

            text = (
                "🎴 <b>CARD CAUGHT!</b>\n\n"
                f"👤 <b>{user.first_name}</b>\n"
                f"🎴 <b>{card.name}</b>\n"
                f"💠 Rarity: <b>{card.rarity}</b>\n\n"
                f"🔁 Duplicate Card\n"
                f"🃏 Quantity: <b>{user_card.quantity}</b>\n\n"
                f"✨ +{xp_reward} XP"
            )

        else:

            text = (
                "🎉 <b>CARD CAUGHT!</b>\n\n"
                f"👤 <b>{user.first_name}</b>\n\n"
                f"🎴 <b>#{card.id:04d}</b>\n"
                f"✨ <b>{card.name}</b>\n"
                f"💠 Rarity: <b>{card.rarity}</b>\n\n"
                "🏆 <b>NEW CARD!</b>\n"
                f"✨ +{xp_reward} XP"
            )

        if level_up:
            text += (
                "\n\n"
                "🎊 <b>LEVEL UP!</b>\n"
                f"⭐ Level <b>{user.level}</b>"
            )

        await message.answer(
            text,
            parse_mode="HTML",
        )
