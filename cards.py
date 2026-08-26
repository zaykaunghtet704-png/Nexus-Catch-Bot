import random


EDITIONS = [
    "Common Edition",
    "Uncommon Edition",
    "Rare Edition",
    "Super Rare Edition",
    "Epic Edition",
    "Ultra Edition",
    "Elite Edition",
    "Master Edition",
    "Grandmaster Edition",
    "Mythic Edition",
    "Legendary Edition",
    "Ultimate Edition",
    "Premium Edition",
]


DEFAULT_PRICES = {
    "Common Edition": 100,
    "Uncommon Edition": 250,
    "Rare Edition": 500,
    "Super Rare Edition": 1_000,
    "Epic Edition": 2_500,
    "Ultra Edition": 5_000,
    "Elite Edition": 10_000,
    "Master Edition": 25_000,
    "Grandmaster Edition": 50_000,
    "Mythic Edition": 100_000,
    "Legendary Edition": 250_000,
    "Ultimate Edition": 500_000,
    "Premium Edition": 1_000_000,
}


DEFAULT_DROP_RATES = {
    "Common Edition": 35.00,
    "Uncommon Edition": 20.00,
    "Rare Edition": 13.00,
    "Super Rare Edition": 9.00,
    "Epic Edition": 7.00,
    "Ultra Edition": 5.00,
    "Elite Edition": 3.50,
    "Master Edition": 2.50,
    "Grandmaster Edition": 1.80,
    "Mythic Edition": 1.20,
    "Legendary Edition": 0.70,
    "Ultimate Edition": 0.55,
    "Premium Edition": 0.05,
}


EDITION_EMOJIS = {
    "Common Edition": "⚪",
    "Uncommon Edition": "🟢",
    "Rare Edition": "🔵",
    "Super Rare Edition": "🔷",
    "Epic Edition": "🟣",
    "Ultra Edition": "💠",
    "Elite Edition": "🔶",
    "Master Edition": "🟠",
    "Grandmaster Edition": "🔴",
    "Mythic Edition": "🌌",
    "Legendary Edition": "🌟",
    "Ultimate Edition": "👑",
    "Premium Edition": "💎",
}


def get_edition_emoji(edition: str) -> str:
    return EDITION_EMOJIS.get(edition, "🎴")


def normalize_edition(value: str):
    value = value.strip().lower()

    for edition in EDITIONS:
        if edition.lower() == value:
            return edition

    return None


def choose_weighted_card(cards):
    """
    cards:
        [
            (
                id,
                name,
                edition,
                price,
                drop_rate,
                description,
                media_type,
                file_id
            ),
            ...
        ]
    """

    if not cards:
        return None

    valid_cards = []
    weights = []

    for card in cards:
        try:
            rate = float(card[4])
        except (ValueError, TypeError):
            rate = 0

        if rate > 0:
            valid_cards.append(card)
            weights.append(rate)

    if not valid_cards:
        return random.choice(cards)

    return random.choices(
        valid_cards,
        weights=weights,
        k=1
    )[0]
