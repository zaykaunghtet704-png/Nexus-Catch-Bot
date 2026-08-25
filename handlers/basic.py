from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy import select

from database import SessionLocal, User


router = Router()


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

        await message.answer(
            f"👋 Welcome, <b>{user.first_name}</b>!\n\n"
            f"💰 Coins: {user.coins}\n"
            f"💎 Gems: {user.gems}\n"
            f"⭐ Level: {user.level}\n"
            f"✨ XP: {user.xp}"
        )


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
                "❌ You don't have a profile yet.\n"
                "Use /start first."
            )
            return

        await message.answer(
            f"👤 <b>{user.first_name}</b>\n\n"
            f"⭐ Level: {user.level}\n"
            f"✨ XP: {user.xp}\n"
            f"💰 Coins: {user.coins}\n"
            f"💎 Gems: {user.gems}"
        )
