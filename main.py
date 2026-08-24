import asyncio

from aiogram import Bot, Dispatcher, Router
from aiogram.filters import Command
from aiogram.types import Message
from fastapi import FastAPI
from sqlalchemy import select

from config import settings
from database import Card, User, UserCard, SessionLocal, init_db


router = Router()
app = FastAPI(title="Advanced Card Bot")


@router.message(Command("start"))
async def start_handler(message: Message):
    tg_user = message.from_user

    async with SessionLocal() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == tg_user.id)
        )

        user = result.scalar_one_or_none()

        if user is None:
            user = User(
                telegram_id=tg_user.id,
                username=tg_user.username,
                first_name=tg_user.first_name or "Player",
            )

            session.add(user)
            await session.commit()

            await message.answer(
                "🎉 Welcome to Advanced Card Game!\n\n"
                "🎁 Your account has been created.\n"
                "💰 Coins: 1,000\n"
                "💎 Gems: 100\n\n"
                "Use /profile to view your profile."
            )
        else:
            await message.answer(
                "👋 Welcome back!\n\n"
                "Use /profile to view your profile."
            )


@router.message(Command("profile"))
async def profile_handler(message: Message):
    async with SessionLocal() as session:
        result = await session.execute(
            select(User).where(
                User.telegram_id == message.from_user.id
            )
        )

        user = result.scalar_one_or_none()

        if user is None:
            await message.answer("❌ Please use /start first.")
            return

        card_result = await session.execute(
            select(UserCard).where(UserCard.user_id == user.id)
        )

        cards = card_result.scalars().all()
        total_cards = sum(card.quantity for card in cards)

        await message.answer(
            f"👤 {user.first_name}\n\n"
            f"⭐ Level: {user.level}\n"
            f"✨ XP: {user.xp}\n"
            f"💰 Coins: {user.coins:,}\n"
            f"💎 Gems: {user.gems:,}\n"
            f"🎴 Cards: {total_cards}"
        )


@router.message(Command("cards"))
async def cards_handler(message: Message):
    async with SessionLocal() as session:
        result = await session.execute(
            select(User).where(
                User.telegram_id == message.from_user.id
            )
        )

        user = result.scalar_one_or_none()

        if user is None:
            await message.answer("❌ Please use /start first.")
            return

        result = await session.execute(
            select(UserCard, Card)
            .join(Card, UserCard.card_id == Card.id)
            .where(UserCard.user_id == user.id)
        )

        rows = result.all()

        if not rows:
            await message.answer(
                "🎴 Your collection is empty.\n"
                "Pack system is coming next."
            )
            return

        text = "🎴 YOUR COLLECTION\n\n"

        for user_card, card in rows:
            text += (
                f"• {card.name}\n"
                f"  Rarity: {card.rarity}\n"
                f"  Lv.{user_card.level}\n"
                f"  Qty: {user_card.quantity}\n\n"
            )

        await message.answer(text)


@app.get("/")
async def health_check():
    return {
        "status": "online",
        "service": "Advanced Card Bot",
    }


async def run_bot():
    await init_db()

    bot = Bot(token=settings.bot_token)

    dp = Dispatcher()
    dp.include_router(router)

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(run_bot())
