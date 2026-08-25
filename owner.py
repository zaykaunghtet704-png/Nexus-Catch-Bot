from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy import select, func

from config import settings
from database import (
    AuditLog,
    Card,
    Pack,
    SessionLocal,
    User,
)


router = Router()


def is_owner(message: Message) -> bool:
    return (
        message.from_user is not None
        and message.from_user.id == settings.owner_id
    )


@router.message(Command("owner"))
async def owner_command(message: Message):
    if not is_owner(message):
        await message.answer("❌ Owner only.")
        return

    await message.answer(
        "👑 <b>Owner Commands</b>\n\n"
        "/stats - Bot statistics\n"
        "/users - User count\n"
        "/cards - Card count\n"
        "/packs - Pack count\n"
        "/broadcast - Broadcast message"
    )


@router.message(Command("stats"))
async def stats_command(message: Message):
    if not is_owner(message):
        await message.answer("❌ Owner only.")
        return

    async with SessionLocal() as session:
        users = await session.scalar(
            select(func.count()).select_from(User)
        )
        cards = await session.scalar(
            select(func.count()).select_from(Card)
        )
        packs = await session.scalar(
            select(func.count()).select_from(Pack)
        )

    await message.answer(
        "📊 <b>Bot Statistics</b>\n\n"
        f"👤 Users: {users or 0}\n"
        f"🃏 Cards: {cards or 0}\n"
        f"🎁 Packs: {packs or 0}"
    )


@router.message(Command("users"))
async def users_command(message: Message):
    if not is_owner(message):
        await message.answer("❌ Owner only.")
        return

    async with SessionLocal() as session:
        count = await session.scalar(
            select(func.count()).select_from(User)
        )

    await message.answer(
        f"👥 Total users: <b>{count or 0}</b>"
    )


@router.message(Command("cards"))
async def cards_command(message: Message):
    if not is_owner(message):
        await message.answer("❌ Owner only.")
        return

    async with SessionLocal() as session:
        count = await session.scalar(
            select(func.count()).select_from(Card)
        )

    await message.answer(
        f"🃏 Total cards: <b>{count or 0}</b>"
    )


@router.message(Command("packs"))
async def packs_command(message: Message):
    if not is_owner(message):
        await message.answer("❌ Owner only.")
        return

    async with SessionLocal() as session:
        count = await session.scalar(
            select(func.count()).select_from(Pack)
        )

    await message.answer(
        f"🎁 Total packs: <b>{count or 0}</b>"
    )


@router.message(Command("ban"))
async def ban_command(message: Message):
    if not is_owner(message):
        await message.answer("❌ Owner only.")
        return

    if not message.reply_to_message:
        await message.answer(
            "Reply to a user's message with /ban."
        )
        return

    target = message.reply_to_message.from_user

    if target is None:
        await message.answer("❌ User not found.")
        return

    async with SessionLocal() as session:
        result = await session.execute(
            select(User).where(
                User.telegram_id == target.id
            )
        )
        user = result.scalar_one_or_none()

        if user is None:
            await message.answer("❌ User profile not found.")
            return

        user.is_banned = True

        session.add(
            AuditLog(
                actor_id=message.from_user.id,
                action="ban_user",
                target_id=target.id,
                details="User banned by owner",
            )
        )

        await session.commit()

    await message.answer(
        f"🚫 User <code>{target.id}</code> has been banned."
    )


@router.message(Command("unban"))
async def unban_command(message: Message):
    if not is_owner(message):
        await message.answer("❌ Owner only.")
        return

    if not message.reply_to_message:
        await message.answer(
            "Reply to a user's message with /unban."
        )
        return

    target = message.reply_to_message.from_user

    if target is None:
        await message.answer("❌ User not found.")
        return

    async with SessionLocal() as session:
        result = await session.execute(
            select(User).where(
                User.telegram_id == target.id
            )
        )
        user = result.scalar_one_or_none()

        if user is None:
            await message.answer("❌ User profile not found.")
            return

        user.is_banned = False

        session.add(
            AuditLog(
                actor_id=message.from_user.id,
                action="unban_user",
                target_id=target.id,
                details="User unbanned by owner",
            )
        )

        await session.commit()

    await message.answer(
        f"✅ User <code>{target.id}</code> has been unbanned."
    )
