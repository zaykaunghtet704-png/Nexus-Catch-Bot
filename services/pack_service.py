import random

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


async def open_pack(
    telegram_id: int,
    pack_id: int | None = None,
):
    async with SessionLocal() as session:
        result = await session.execute(
            select(User).where(
                User.telegram_id == telegram_id
            )
        )
        user = result.scalar_one_or_none()

        if user is None:
            return {
                "success": False,
                "message": "User not found.",
            }

        if pack_id is None:
            result = await session.execute(
                select(Pack)
                .where(Pack.active.is_(True))
                .order_by(Pack.id)
            )
            pack = result.scalars().first()
        else:
            result = await session.execute(
                select(Pack).where(
                    Pack.id == pack_id,
                    Pack.active.is_(True),
                )
            )
            pack = result.scalar_one_or_none()

        if pack is None:
            return {
                "success": False,
                "message": "No active pack found.",
            }

        if user.coins < pack.price_coins:
            return {
                "success": False,
                "message": "Not enough coins.",
            }

        user.coins -= pack.price_coins

        received_cards = []

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

                return {
                    "success": False,
                    "message": "No cards available.",
                }

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

            opening = PackOpening(
                user_id=user.id,
                pack_id=pack.id,
                card_id=card.id,
                rarity=card.rarity,
            )
            session.add(opening)

            received_cards.append(card)

        await session.commit()

        return {
            "success": True,
            "pack": pack,
            "cards": received_cards,
        }
