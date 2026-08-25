RARITIES = {
    "COMMON": {
        "name": "Common",
        "weight": 60.0,
    },
    "UNCOMMON": {
        "name": "Uncommon",
        "weight": 25.0,
    },
    "RARE": {
        "name": "Rare",
        "weight": 10.0,
    },
    "EPIC": {
        "name": "Epic",
        "weight": 3.5,
    },
    "LEGENDARY": {
        "name": "Legendary",
        "weight": 1.2,
    },
    "MYTHIC": {
        "name": "Mythic",
        "weight": 0.3,
    },
}


RARITY_ORDER = [
    "COMMON",
    "UNCOMMON",
    "RARE",
    "EPIC",
    "LEGENDARY",
    "MYTHIC",
]


def get_rarity(rarity: str) -> dict:
    return RARITIES.get(
        rarity.upper(),
        RARITIES["COMMON"],
    )


def get_rarity_weight(rarity: str) -> float:
    return get_rarity(rarity)["weight"]
