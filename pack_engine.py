import random

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import (
    Card,
    EconomyTransaction,
    Pack,
    PackOpening,
    PackRate,
    PityCounter,
    User,
    UserCard,
)
from rarities import RARITIES


RARITY_ORDER = {
    rarity.name: rarity.order
    for rarity in RARITIES
}


def choose_rarity(rates: list[PackRate]) -> str:
    if not rates:
        return "Common"

    total = sum(rate.rate for rate in rates)

    if total <= 0:
        return "Common"

    roll = random.uniform(0, total)
    current = 0.0

    for rate in rates:
        current += rate.rate

        if roll <= current:
            return rate.rarity

    return rates[-1].rarity


async def get_or_create_pity(
    session: AsyncSession,
    user_id: int,
    pack_id: int,
) -> PityCounter:

    result = await session.execute(
        select(PityCounter).where(
            PityCounter.user_id == user_id,
            PityCounter.pack_id == pack_id,
        )
    )

    pity = result.scalar_one_or_none()

    if pity is None:
        pity = PityCounter(
            user_id=user_id,
            pack_id=pack_id,
            pulls=0,
        )

        session.add(pity)
        await session.flush()

    return pity


async def select_card(
    session: AsyncSession,
    rarity: str,
) -> Card | None:

    result = await session.execute(
        select(Card).where(Card.rarity == rarity)
    )

    cards = result.scalars().all()

    if not cards:
        return None

    return random.choice(cards)


async def add_card_to_inventory(
    session: AsyncSession,
    user: User,
    card: Card,
):
    result = await session.execute(
        select(UserCard).where(
            UserCard.user_id == user.id,
            UserCard.card_id == card.id,
        )
    )

    user_card = result.scalar_one_or_none()

    if user_card:
        user_card.quantity += 1
    else:
        user_card = UserCard(
            user_id=user.id,
            card_id=card.id,
            level=1,
            xp=0,
            quantity=1,
        )

        session.add(user_card)


async def open_pack(
    session: AsyncSession,
    user: User,
    pack: Pack,
) -> dict:

    if not pack.active:
        raise ValueError("This pack is not available.")

    if user.coins < pack.price_coins:
        raise ValueError("Not enough coins.")

    user.coins -= pack.price_coins

    session.add(
        EconomyTransaction(
            user_id=user.id,
            transaction_type="PACK_PURCHASE",
            currency="coins",
            amount=-pack.price_coins,
            description=f"Opened {pack.name}",
        )
    )

    rates_result = await session.execute(
        select(PackRate).where(
            PackRate.pack_id == pack.id
        )
    )

    rates = rates_result.scalars().all()

    pity = await get_or_create_pity(
        session,
        user.id,
        pack.id,
    )

    results = []

    for _ in range(pack.cards_per_open):

        pity.pulls += 1

        rarity = choose_rarity(rates)

        # Legendary pity
        if pity.pulls >= pity.legendary_pity:
            high_rarities = [
                name
                for name, order in RARITY_ORDER.items()
                if order >= 6
            ]

            rarity = random.choice(high_rarities)
            pity.pulls = 0

        # Mythic+ pity
        if pity.pulls >= pity.mythic_pity:
            mythic_rarities = [
                name
                for name, order in RARITY_ORDER.items()
                if order >= 7
            ]

            rarity = random.choice(mythic_rarities)
            pity.pulls = 0

        card = await select_card(
            session,
            rarity,
        )

        # If a rarity has no cards yet,
        # safely fall back to the highest
        # available rarity.
        if card is None:
            available_result = await session.execute(
                select(Card)
            )

            available_cards = (
                available_result.scalars().all()
            )

            if not available_cards:
                raise ValueError(
                    "No cards have been created yet."
                )

            card = random.choice(available_cards)
            rarity = card.rarity

        await add_card_to_inventory(
            session,
            user,
            card,
        )

        opening = PackOpening(
            user_id=user.id,
            pack_id=pack.id,
            card_id=card.id,
            rarity=rarity,
        )

        session.add(opening)

        results.append(card)

    await session.commit()

    return {
        "pack": pack,
        "cards": results,
    }
