import asyncio

from sqlalchemy import select

from database import (
    Card,
    Pack,
    PackRate,
    SessionLocal,
    init_db,
)
from rarities import RARITIES


CARDS = [
    {
        "name": "Flame Dragon",
        "rarity": "COMMON",
        "attack": 20,
        "defense": 15,
        "hp": 120,
        "speed": 12,
        "element": "Fire",
        "card_class": "Dragon",
        "description": "A young dragon with blazing flames.",
    },
    {
        "name": "Aqua Spirit",
        "rarity": "UNCOMMON",
        "attack": 25,
        "defense": 25,
        "hp": 140,
        "speed": 15,
        "element": "Water",
        "card_class": "Spirit",
        "description": "A mysterious spirit born from pure water.",
    },
    {
        "name": "Thunder Wolf",
        "rarity": "RARE",
        "attack": 40,
        "defense": 30,
        "hp": 180,
        "speed": 25,
        "element": "Thunder",
        "card_class": "Beast",
        "description": "A fast wolf surrounded by lightning.",
    },
    {
        "name": "Shadow Knight",
        "rarity": "EPIC",
        "attack": 60,
        "defense": 55,
        "hp": 250,
        "speed": 30,
        "element": "Dark",
        "card_class": "Knight",
        "description": "A legendary warrior from the shadows.",
    },
    {
        "name": "Celestial Phoenix",
        "rarity": "LEGENDARY",
        "attack": 90,
        "defense": 80,
        "hp": 400,
        "speed": 45,
        "element": "Light",
        "card_class": "Phoenix",
        "description": "A phoenix reborn from celestial fire.",
    },
    {
        "name": "Void Emperor",
        "rarity": "MYTHIC",
        "attack": 150,
        "defense": 130,
        "hp": 700,
        "speed": 60,
        "element": "Void",
        "card_class": "Emperor",
        "description": "An ancient ruler who commands the void.",
    },
]


PACKS = [
    {
        "name": "Starter Pack",
        "description": "A basic card pack for new players.",
        "price_coins": 500,
        "price_gems": 0,
        "opens_per_day": 10,
        "cards_per_open": 1,
    },
    {
        "name": "Premium Pack",
        "description": "A premium pack with better rarity rates.",
        "price_coins": 2000,
        "price_gems": 10,
        "opens_per_day": 20,
        "cards_per_open": 1,
    },
]


async def seed():
    await init_db()

    async with SessionLocal() as session:
        result = await session.execute(select(Card))
        existing_cards = result.scalars().first()

        if existing_cards is None:
            for card_data in CARDS:
                session.add(Card(**card_data))

        result = await session.execute(select(Pack))
        existing_packs = result.scalars().first()

        if existing_packs is None:
            for pack_data in PACKS:
                pack = Pack(**pack_data)
                session.add(pack)

                await session.flush()

                for rarity, data in RARITIES.items():
                    session.add(
                        PackRate(
                            pack_id=pack.id,
                            rarity=rarity,
                            rate=data["weight"],
                        )
                    )

        await session.commit()

    print("Database seed completed.")


if __name__ == "__main__":
    asyncio.run(seed())
