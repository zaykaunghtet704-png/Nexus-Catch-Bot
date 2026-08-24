from dataclasses import dataclass


@dataclass(frozen=True)
class Rarity:
    name: str
    order: int
    drop_rate: float


RARITIES = [
    Rarity("Common", 1, 55.0),
    Rarity("Uncommon", 2, 20.0),
    Rarity("Rare", 3, 10.0),
    Rarity("Epic", 4, 5.0),
    Rarity("Ultra", 5, 3.0),
    Rarity("Legendary", 6, 2.0),
    Rarity("Mythic", 7, 1.2),
    Rarity("Divine", 8, 0.8),
    Rarity("Eternal", 9, 0.5),
    Rarity("Celestial", 10, 0.3),
    Rarity("Immortal", 11, 0.15),
    Rarity("Supreme", 12, 0.04),
    Rarity("Premium Edition", 13, 0.01),
]


RARITY_MAP = {rarity.name: rarity for rarity in RARITIES}
