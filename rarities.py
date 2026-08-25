RARITIES = {
    "Common": {
        "tier": 1,
        "weight": 40.00,
        "price": 50,
    },
    "Uncommon": {
        "tier": 2,
        "weight": 25.00,
        "price": 100,
    },
    "Rare": {
        "tier": 3,
        "weight": 14.00,
        "price": 200,
    },
    "Elite": {
        "tier": 4,
        "weight": 8.00,
        "price": 350,
    },
    "Epic": {
        "tier": 5,
        "weight": 5.00,
        "price": 550,
    },
    "Legend": {
        "tier": 6,
        "weight": 2.50,
        "price": 800,
    },
    "Mythic": {
        "tier": 7,
        "weight": 1.50,
        "price": 1200,
    },
    "Celestial": {
        "tier": 8,
        "weight": 0.80,
        "price": 1800,
    },
    "Astral": {
        "tier": 9,
        "weight": 0.50,
        "price": 2700,
    },
    "Eternal": {
        "tier": 10,
        "weight": 0.30,
        "price": 4000,
    },
    "Transcendent": {
        "tier": 11,
        "weight": 0.20,
        "price": 6000,
    },
    "Immortal": {
        "tier": 12,
        "weight": 0.15,
        "price": 9000,
    },
    "Premium Edition": {
        "tier": 13,
        "weight": 0.05,
        "price": 15000,
    },
}


def get_rarity_price(rarity: str) -> int:
    data = RARITIES.get(rarity)

    if data is None:
        return 0

    return data["price"]


def get_rarity_tier(rarity: str) -> int:
    data = RARITIES.get(rarity)

    if data is None:
        return 0

    return data["tier"]
