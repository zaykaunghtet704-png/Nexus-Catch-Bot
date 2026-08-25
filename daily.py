from datetime import datetime, timedelta, timezone

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy import select

from database import DailyReward, SessionLocal, User


router = Router()


@router.message(Command("daily"))
async def daily_command(message: Message):
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

        result = await session.execute(
            select(DailyReward).where(
                DailyReward.user_id == user.id
            )
        )
        reward = result.scalar_one_or_none()

        now = datetime.now(timezone.utc)

        if reward is None:
            reward = DailyReward(
                user_id=user.id,
                streak=1,
                last_claimed_at=now,
            )
            session.add(reward)

            coins = 500
            user.coins += coins

            await session.commit()

            await message.answer(
                "🎁 <b>Daily Reward!</b>\n\n"
                f"🔥 Streak: 1 day\n"
                f"💰 +{coins} coins"
            )
            return

        if reward.last_claimed_at is not None:
            next_claim = reward.last_claimed_at + timedelta(days=1)

            if now < next_claim:
                remaining = next_claim - now
                hours = int(
                    remaining.total_seconds() // 3600
                )
                minutes = int(
                    (remaining.total_seconds() % 3600) // 60
                )

                await message.answer(
                    "⏳ You already claimed today's reward.\n"
                    f"Come back in {hours}h {minutes}m."
                )
                return

        if (
            reward.last_claimed_at is not None
            and now - reward.last_claimed_at <= timedelta(days=2)
        ):
            reward.streak += 1
        else:
            reward.streak = 1

        coins = 500 + min(reward.streak, 7) * 100

        user.coins += coins
        reward.last_claimed_at = now

        await session.commit()

        await message.answer(
            "🎁 <b>Daily Reward!</b>\n\n"
            f"🔥 Streak: {reward.streak} days\n"
            f"💰 +{coins} coins"
        )
