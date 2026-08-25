import random

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy import select

from database import (
    Card,
    Pack,
    PackOpening,
    SessionLocal,
    User,
    UserCard,
)
from rarities import RARITIES


router = Router()


def choose_rarity() -> str:
    names = list(RARITIES.keys())
    weights = [
        RARITIES[name]["weight"]
        for name in names
    ]

    return random.choices(
        names,
        weights=weights,
        k=1,
    )[0]


@router.message(Command("pack"))
async def pack_command(message: Message):
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
            select(Pack)
            .where(Pack.active.is_(True))
            .order_by(Pack.id)
        )
        pack = result.scalars().first()

        if pack is None:
            await message.answer(
                "❌ No active packs are available."
            )
            return

        if user.coins < pack.price_coins:
            await message.answer(
                "❌ Not enough coins.\n"
                f"Required: {pack.price_coins:,}\n"
                f"Your coins: {user.coins:,}"
            )
            return

        user.coins -= pack.price_coins

        cards_received = []

        for _ in range(pack.cards_per_open):
            rarity = choose_rarity()

            result = await session.execute(
                select(Card).where(
                    Card.rarity == rarity
                )
            )
            cards = result.scalars().all()

            if not cards:
                result = await session.execute(
                    select(Card)
                )
                cards = result.scalars().all()

            if not cards:
                await session.rollback()
                await message.answer(
                    "❌ No cards have been added yet."
                )
                return

            card = random.choice(cards)

            result = await session.execute(
                select(UserCard).where(
                    UserCard.user_id == user.id,
                    UserCard.card_id == card.id,
                )
            )
            user_card = result.scalar_one_or_none()

            if user_card is None:
                user_card = UserCard(
                    user_id=user.id,
                    card_id=card.id,
                    quantity=1,
                )
                session.add(user_card)
            else:
                user_card.quantity += 1

            session.add(
                PackOpening(
                    user_id=user.id,
                    pack_id=pack.id,
                    card_id=card.id,
                    rarity=card.rarity,
                )
            )

            cards_received.append(card)

        await session.commit()

        lines = [
            f"🎁 <b>{pack.name}</b>",
            "",
            f"💰 Cost: {pack.price_coins:,} coins",
            "",
        ]

        for card in cards_received:
            lines.append(
                f"🃏 <b>{card.name}</b>\n"
                f"✨ Rarity: {card.rarity}\n"
                f"⚔️ ATK: {card.attack}  "
                f"🛡 DEF: {card.defense}\n"
                f"❤️ HP: {card.hp}"
            )

        await message.answer(
            "\n".join(lines)
        )
