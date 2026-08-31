# card_manager.py
# Nexus Catch Bot
# Card Management Core
#
# Features:
# - 13 Editions
# - Premium as highest Edition
# - Card attributes
# - Price system
# - Photo / Video / Animation support
# - Shiny / Limited / Animated tags
# - Search
# - Add / Edit / Delete
# - User collection
# - Favorite
# - Level / EXP
# - Upgrade
# - Card statistics
#
# Persistent SQLite saving will be connected through database.py.

from __future__ import annotations

from dataclasses import dataclass, field
from threading import RLock
from typing import Optional
import math


# ============================================================
# EDITIONS
# ============================================================

EDITIONS = [
    "Common",
    "Uncommon",
    "Rare",
    "Super Rare",
    "Ultra Rare",
    "Epic",
    "Legendary",
    "Mythic",
    "Divine",
    "Celestial",
    "Immortal",
    "Exclusive",
    "Premium",
]

PREMIUM_EDITION = "Premium"


# ============================================================
# RARITIES
# ============================================================

RARITIES = [
    "Common",
    "Uncommon",
    "Rare",
    "SR",
    "SSR",
    "UR",
    "Legendary",
]


# ============================================================
# ELEMENTS / CLASSES
# ============================================================

ELEMENTS = [
    "Fire",
    "Water",
    "Wind",
    "Earth",
    "Light",
    "Dark",
    "Arcane",
    "Void",
    "Neutral",
]


CLASSES = [
    "Warrior",
    "Mage",
    "Assassin",
    "Tank",
    "Support",
    "Ranger",
    "Berserker",
    "Guardian",
    "Special",
]


# ============================================================
# LEVEL CONFIG
# ============================================================

MAX_CARD_LEVEL = 100

BASE_EXP_REQUIRED = 100

UPGRADE_EXP_MULTIPLIER = 1.25

MAX_ATK = 99999
MAX_DEF = 99999
MAX_HP = 999999
MAX_SPEED = 9999


# ============================================================
# PRICE CONFIG
# ============================================================

MAX_CARD_PRICE = 15000

EDITION_MAX_PRICES = {
    "Common": 500,
    "Uncommon": 750,
    "Rare": 1200,
    "Super Rare": 2000,
    "Ultra Rare": 3000,
    "Epic": 4500,
    "Legendary": 6000,
    "Mythic": 7500,
    "Divine": 9000,
    "Celestial": 10500,
    "Immortal": 12000,
    "Exclusive": 13500,
    "Premium": 15000,
}


# ============================================================
# MEDIA TYPES
# ============================================================

MEDIA_TYPES = {
    "photo",
    "video",
    "animation",
}


# ============================================================
# CARD DATACLASS
# ============================================================

@dataclass
class Card:
    card_id: str

    name: str

    edition: str = "Common"

    rarity: str = "Common"

    atk: int = 0
    defense: int = 0
    hp: int = 0
    speed: int = 0

    element: str = "Neutral"
    card_class: str = "Special"

    description: str = ""

    media_type: Optional[str] = None
    media_id: Optional[str] = None

    price: int = 0

    shiny: bool = False
    limited: bool = False
    animated: bool = False

    level: int = 1
    exp: int = 0

    enabled: bool = True

    metadata: dict = field(default_factory=dict)


# ============================================================
# USER CARD
# ============================================================

@dataclass
class UserCard:
    """
    A user's owned copy of a card.

    The original card definition is stored separately.
    """

    owner_id: int

    card_id: str

    quantity: int = 1

    level: int = 1
    exp: int = 0

    favorite: bool = False

    obtained_count: int = 1


# ============================================================
# STORAGE
# ============================================================

_CARDS: dict[str, Card] = {}

_USER_CARDS: dict[tuple[int, str], UserCard] = {}

_LOCK = RLock()


# ============================================================
# ID HELPERS
# ============================================================

def normalize_card_id(card_id) -> str:
    """
    Normalize card ID.

    Examples:
        21 -> 0021
        "21" -> 0021
        "0021" -> 0021
    """

    if card_id is None:
        raise ValueError("card_id is required")

    value = str(card_id).strip()

    if not value:
        raise ValueError("card_id cannot be empty")

    if value.isdigit():
        return value.zfill(4)

    return value


# ============================================================
# VALIDATION
# ============================================================

def validate_edition(edition: str) -> bool:
    if not edition:
        return False

    return edition in EDITIONS


def validate_rarity(rarity: str) -> bool:
    if not rarity:
        return False

    return rarity in RARITIES


def validate_element(element: str) -> bool:
    if not element:
        return False

    return element in ELEMENTS


def validate_class(card_class: str) -> bool:
    if not card_class:
        return False

    return card_class in CLASSES


def validate_media_type(
    media_type: Optional[str],
) -> bool:

    if media_type is None:
        return True

    return media_type.lower() in MEDIA_TYPES


# ============================================================
# CARD CREATION
# ============================================================

def create_card(
    card_id,
    name: str,
    edition: str = "Common",
    rarity: str = "Common",
    atk: int = 0,
    defense: int = 0,
    hp: int = 0,
    speed: int = 0,
    element: str = "Neutral",
    card_class: str = "Special",
    description: str = "",
    media_type: Optional[str] = None,
    media_id: Optional[str] = None,
    price: int = 0,
    shiny: bool = False,
    limited: bool = False,
    animated: bool = False,
    metadata: Optional[dict] = None,
) -> Card:

    cid = normalize_card_id(card_id)

    if not name or not name.strip():
        raise ValueError("Card name is required")

    if not validate_edition(edition):
        raise ValueError(
            f"Invalid edition: {edition}"
        )

    if not validate_rarity(rarity):
        raise ValueError(
            f"Invalid rarity: {rarity}"
        )

    if not validate_element(element):
        raise ValueError(
            f"Invalid element: {element}"
        )

    if not validate_class(card_class):
        raise ValueError(
            f"Invalid class: {card_class}"
        )

    if not validate_media_type(media_type):
        raise ValueError(
            f"Invalid media type: {media_type}"
        )

    if edition == PREMIUM_EDITION:
        price = min(
            max(int(price), 0),
            MAX_CARD_PRICE,
        )
    else:
        price = min(
            max(int(price), 0),
            EDITION_MAX_PRICES.get(
                edition,
                MAX_CARD_PRICE,
            ),
        )

    card = Card(
        card_id=cid,
        name=name.strip(),
        edition=edition,
        rarity=rarity,
        atk=max(0, int(atk)),
        defense=max(0, int(defense)),
        hp=max(0, int(hp)),
        speed=max(0, int(speed)),
        element=element,
        card_class=card_class,
        description=description or "",
        media_type=media_type,
        media_id=media_id,
        price=price,
        shiny=bool(shiny),
        limited=bool(limited),
        animated=bool(animated),
        metadata=dict(metadata or {}),
    )

    with _LOCK:

        if cid in _CARDS:
            raise ValueError(
                f"Card ID already exists: {cid}"
            )

        _CARDS[cid] = card

    return card


# ============================================================
# GET CARD
# ============================================================

def get_card(card_id) -> Optional[Card]:

    try:
        cid = normalize_card_id(card_id)
    except ValueError:
        return None

    with _LOCK:
        return _CARDS.get(cid)


def card_exists(card_id) -> bool:
    return get_card(card_id) is not None


# ============================================================
# EDIT CARD
# ============================================================

def update_card(
    card_id,
    **changes,
) -> Optional[Card]:

    cid = normalize_card_id(card_id)

    with _LOCK:

        card = _CARDS.get(cid)

        if card is None:
            return None

        allowed_fields = {
            "name",
            "edition",
            "rarity",
            "atk",
            "defense",
            "hp",
            "speed",
            "element",
            "card_class",
            "description",
            "media_type",
            "media_id",
            "price",
            "shiny",
            "limited",
            "animated",
            "enabled",
            "metadata",
        }

        for key, value in changes.items():

            if key not in allowed_fields:
                continue

            if key == "edition":

                if not validate_edition(value):
                    raise ValueError(
                        "Invalid edition"
                    )

            elif key == "rarity":

                if not validate_rarity(value):
                    raise ValueError(
                        "Invalid rarity"
                    )

            elif key == "element":

                if not validate_element(value):
                    raise ValueError(
                        "Invalid element"
                    )

            elif key == "card_class":

                if not validate_class(value):
                    raise ValueError(
                        "Invalid class"
                    )

            elif key == "media_type":

                if not validate_media_type(value):
                    raise ValueError(
                        "Invalid media type"
                    )

            elif key == "price":

                value = max(
                    0,
                    int(value),
                )

                max_price = EDITION_MAX_PRICES.get(
                    card.edition,
                    MAX_CARD_PRICE,
                )

                value = min(
                    value,
                    max_price,
                )

            elif key in {
                "atk",
                "defense",
                "hp",
                "speed",
            }:

                value = max(
                    0,
                    int(value),
                )

            setattr(card, key, value)

        return card


# ============================================================
# DELETE CARD
# ============================================================

def delete_card(card_id) -> bool:

    cid = normalize_card_id(card_id)

    with _LOCK:

        if cid not in _CARDS:
            return False

        del _CARDS[cid]

        return True


# ============================================================
# ENABLE / DISABLE
# ============================================================

def enable_card(card_id) -> bool:

    card = get_card(card_id)

    if card is None:
        return False

    card.enabled = True

    return True


def disable_card(card_id) -> bool:

    card = get_card(card_id)

    if card is None:
        return False

    card.enabled = False

    return True


# ============================================================
# CARD LIST
# ============================================================

def get_all_cards(
    include_disabled: bool = False,
) -> list[Card]:

    with _LOCK:

        cards = list(_CARDS.values())

    if not include_disabled:
        cards = [
            card
            for card in cards
            if card.enabled
        ]

    return sorted(
        cards,
        key=lambda card: card.card_id,
    )


def get_card_count(
    include_disabled: bool = False,
) -> int:

    return len(
        get_all_cards(
            include_disabled=include_disabled
        )
    )


# ============================================================
# SEARCH
# ============================================================

def search_cards(
    query: str,
    include_disabled: bool = False,
) -> list[Card]:

    if not query:
        return []

    q = query.strip().lower()

    results = []

    for card in get_all_cards(
        include_disabled=include_disabled
    ):

        searchable = " ".join(
            [
                card.card_id,
                card.name,
                card.edition,
                card.rarity,
                card.element,
                card.card_class,
                card.description,
            ]
        ).lower()

        if q in searchable:
            results.append(card)

    return results


# ============================================================
# FILTER
# ============================================================

def get_cards_by_edition(
    edition: str,
) -> list[Card]:

    return [
        card
        for card in get_all_cards()
        if card.edition == edition
    ]


def get_cards_by_rarity(
    rarity: str,
) -> list[Card]:

    return [
        card
        for card in get_all_cards()
        if card.rarity == rarity
    ]


def get_premium_cards() -> list[Card]:

    return get_cards_by_edition(
        PREMIUM_EDITION
    )


def get_limited_cards() -> list[Card]:

    return [
        card
        for card in get_all_cards()
        if card.limited
    ]


def get_shiny_cards() -> list[Card]:

    return [
        card
        for card in get_all_cards()
        if card.shiny
    ]


def get_animated_cards() -> list[Card]:

    return [
        card
        for card in get_all_cards()
        if card.animated
    ]


# ============================================================
# USER COLLECTION
# ============================================================

def add_user_card(
    user_id: int,
    card_id,
    quantity: int = 1,
) -> UserCard:

    if quantity <= 0:
        raise ValueError(
            "quantity must be greater than zero"
        )

    cid = normalize_card_id(card_id)

    if not card_exists(cid):
        raise ValueError(
            f"Card does not exist: {cid}"
        )

    key = (
        int(user_id),
        cid,
    )

    with _LOCK:

        user_card = _USER_CARDS.get(key)

        if user_card is None:

            user_card = UserCard(
                owner_id=int(user_id),
                card_id=cid,
                quantity=int(quantity),
                obtained_count=int(quantity),
            )

            _USER_CARDS[key] = user_card

        else:

            user_card.quantity += int(quantity)

            user_card.obtained_count += int(
                quantity
            )

        return user_card


# ============================================================
# REMOVE USER CARD
# ============================================================

def remove_user_card(
    user_id: int,
    card_id,
    quantity: int = 1,
) -> bool:

    if quantity <= 0:
        return False

    cid = normalize_card_id(card_id)

    key = (
        int(user_id),
        cid,
    )

    with _LOCK:

        user_card = _USER_CARDS.get(key)

        if user_card is None:
            return False

        if user_card.quantity < quantity:
            return False

        user_card.quantity -= quantity

        if user_card.quantity <= 0:
            del _USER_CARDS[key]

        return True


# ============================================================
# USER CARD LOOKUP
# ============================================================

def get_user_card(
    user_id: int,
    card_id,
) -> Optional[UserCard]:

    cid = normalize_card_id(card_id)

    return _USER_CARDS.get(
        (
            int(user_id),
            cid,
        )
    )


def has_user_card(
    user_id: int,
    card_id,
) -> bool:

    user_card = get_user_card(
        user_id,
        card_id,
    )

    return (
        user_card is not None
        and user_card.quantity > 0
    )


def get_user_cards(
    user_id: int,
) -> list[UserCard]:

    uid = int(user_id)

    with _LOCK:

        cards = [
            user_card
            for (
                owner_id,
                _,
            ), user_card in _USER_CARDS.items()
            if owner_id == uid
            and user_card.quantity > 0
        ]

    return sorted(
        cards,
        key=lambda item: item.card_id,
    )


def get_user_unique_card_count(
    user_id: int,
) -> int:

    return len(
        get_user_cards(user_id)
    )


def get_user_total_card_count(
    user_id: int,
) -> int:

    return sum(
        card.quantity
        for card in get_user_cards(user_id)
    )


# ============================================================
# FAVORITE
# ============================================================

def set_favorite(
    user_id: int,
    card_id,
    value: bool = True,
) -> bool:

    user_card = get_user_card(
        user_id,
        card_id,
    )

    if user_card is None:
        return False

    user_card.favorite = bool(value)

    return True


def favorite_card(
    user_id: int,
    card_id,
) -> bool:

    return set_favorite(
        user_id,
        card_id,
        True,
    )


def unfavorite_card(
    user_id: int,
    card_id,
) -> bool:

    return set_favorite(
        user_id,
        card_id,
        False,
    )


def get_favorite_cards(
    user_id: int,
) -> list[UserCard]:

    return [
        user_card
        for user_card in get_user_cards(user_id)
        if user_card.favorite
    ]


# ============================================================
# EXP SYSTEM
# ============================================================

def exp_required_for_level(
    level: int,
) -> int:

    level = max(
        1,
        int(level),
    )

    return int(
        BASE_EXP_REQUIRED
        * (
            UPGRADE_EXP_MULTIPLIER
            ** (level - 1)
        )
    )


def get_level_progress(
    level: int,
    exp: int,
) -> dict:

    level = max(
        1,
        int(level),
    )

    exp = max(
        0,
        int(exp),
    )

    if level >= MAX_CARD_LEVEL:

        return {
            "level": MAX_CARD_LEVEL,
            "exp": exp,
            "required": 0,
            "progress": 100.0,
            "max_level": True,
        }

    required = exp_required_for_level(level)

    progress = (
        exp / required * 100
        if required > 0
        else 100.0
    )

    return {
        "level": level,
        "exp": exp,
        "required": required,
        "progress": min(
            100.0,
            progress,
        ),
        "max_level": False,
    }


# ============================================================
# ADD EXP
# ============================================================

def add_card_exp(
    user_id: int,
    card_id,
    amount: int,
) -> tuple[bool, int, int]:

    if amount <= 0:
        return (
            False,
            0,
            0,
        )

    user_card = get_user_card(
        user_id,
        card_id,
    )

    if user_card is None:
        return (
            False,
            0,
            0,
        )

    if user_card.level >= MAX_CARD_LEVEL:
        return (
            True,
            user_card.level,
            user_card.exp,
        )

    user_card.exp += int(amount)

    while (
        user_card.level < MAX_CARD_LEVEL
    ):

        required = exp_required_for_level(
            user_card.level
        )

        if user_card.exp < required:
            break

        user_card.exp -= required

        user_card.level += 1

    return (
        True,
        user_card.level,
        user_card.exp,
    )


# ============================================================
# UPGRADE
# ============================================================

def upgrade_card(
    user_id: int,
    card_id,
) -> tuple[bool, str]:

    user_card = get_user_card(
        user_id,
        card_id,
    )

    if user_card is None:
        return (
            False,
            "❌ You do not own this card.",
        )

    if user_card.level >= MAX_CARD_LEVEL:
        return (
            False,
            "✨ This card is already MAX level.",
        )

    required = exp_required_for_level(
        user_card.level
    )

    if user_card.exp < required:
        missing = required - user_card.exp

        return (
            False,
            (
                f"❌ Not enough EXP.\n"
                f"Need <b>{missing}</b> more EXP."
            ),
        )

    user_card.exp -= required

    user_card.level += 1

    return (
        True,
        (
            f"🎉 Card Level Up!\n"
            f"🎴 <b>{card_id}</b>\n"
            f"⭐ Level: <b>{user_card.level}</b>"
        ),
    )


# ============================================================
# CARD POWER
# ============================================================

def calculate_card_power(
    card: Card,
    level: int = 1,
) -> int:

    level = max(
        1,
        int(level),
    )

    multiplier = 1.0 + (
        (level - 1) * 0.05
    )

    base = (
        card.atk
        + card.defense
        + card.hp // 10
        + card.speed
    )

    return int(
        base * multiplier
    )


def calculate_user_card_power(
    user_card: UserCard,
) -> int:

    card = get_card(
        user_card.card_id
    )

    if card is None:
        return 0

    return calculate_card_power(
        card,
        user_card.level,
    )


# ============================================================
# PRICE
# ============================================================

def get_card_max_price(
    card_id,
) -> int:

    card = get_card(card_id)

    if card is None:
        return 0

    return EDITION_MAX_PRICES.get(
        card.edition,
        MAX_CARD_PRICE,
    )


def get_sell_price(
    card_id,
) -> int:

    card = get_card(card_id)

    if card is None:
        return 0

    return max(
        0,
        min(
            card.price,
            get_card_max_price(
                card.card_id
            ),
        ),
    )


def set_card_price(
    card_id,
    price: int,
) -> bool:

    card = get_card(card_id)

    if card is None:
        return False

    max_price = get_card_max_price(
        card.card_id
    )

    price = max(
        0,
        min(
            int(price),
            max_price,
        ),
    )

    card.price = price

    return True


# ============================================================
# CARD FORMATTING
# ============================================================

def get_card_tags(
    card: Card,
) -> list[str]:

    tags = []

    if card.shiny:
        tags.append("✨ Shiny")

    if card.limited:
        tags.append("⏳ Limited")

    if card.animated:
        tags.append("🎞️ Animated")

    if card.edition == PREMIUM_EDITION:
        tags.append("💎 Premium")

    return tags


def format_card(
    card: Card,
) -> str:

    tags = get_card_tags(card)

    tag_text = ""

    if tags:
        tag_text = (
            "\n🏷️ "
            + " • ".join(tags)
        )

    return (
        "🎴 <b>CARD INFORMATION</b>\n\n"
        f"🆔 ID: <code>{escape_html(card.card_id)}</code>\n"
        f"👤 Name: <b>{escape_html(card.name)}</b>\n"
        f"💎 Edition: <b>{escape_html(card.edition)}</b>\n"
        f"⭐ Rarity: <b>{escape_html(card.rarity)}</b>\n"
        f"🔥 ATK: <b>{card.atk}</b>\n"
        f"🛡️ DEF: <b>{card.defense}</b>\n"
        f"❤️ HP: <b>{card.hp}</b>\n"
        f"⚡ Speed: <b>{card.speed}</b>\n"
        f"🌌 Element: <b>{escape_html(card.element)}</b>\n"
        f"⚔️ Class: <b>{escape_html(card.card_class)}</b>\n"
        f"💰 Price: <b>{card.price:,}</b> Coins"
        f"{tag_text}\n\n"
        f"📝 {escape_html(card.description)}"
    )


def format_user_card(
    user_card: UserCard,
) -> str:

    card = get_card(
        user_card.card_id
    )

    if card is None:
        return (
            f"🎴 Card "
            f"<code>{escape_html(user_card.card_id)}</code>"
        )

    power = calculate_user_card_power(
        user_card
    )

    favorite = (
        "❤️ Favorite"
        if user_card.favorite
        else ""
    )

    return (
        f"🎴 <b>{escape_html(card.name)}</b>\n"
        f"🆔 <code>{escape_html(card.card_id)}</code>\n"
        f"💎 {escape_html(card.edition)}\n"
        f"⭐ {escape_html(card.rarity)}\n"
        f"📊 Level: <b>{user_card.level}</b>\n"
        f"✨ EXP: <b>{user_card.exp}</b>\n"
        f"📦 Quantity: <b>{user_card.quantity}</b>\n"
        f"⚔️ Power: <b>{power:,}</b>\n"
        f"{favorite}"
    )


# ============================================================
# MEDIA
# ============================================================

def get_card_media(
    card_id,
) -> Optional[dict]:

    card = get_card(card_id)

    if card is None:
        return None

    if not card.media_id:
        return None

    if not validate_media_type(
        card.media_type
    ):
        return None

    return {
        "type": card.media_type,
        "media_id": card.media_id,
    }


# ============================================================
# STATISTICS
# ============================================================

def get_card_statistics(
    card_id,
) -> dict:

    card = get_card(card_id)

    if card is None:
        return {}

    owners = 0
    total_quantity = 0

    with _LOCK:

        for (
            _user_id,
            owned_card_id,
        ), user_card in _USER_CARDS.items():

            if owned_card_id != card.card_id:
                continue

            if user_card.quantity <= 0:
                continue

            owners += 1
            total_quantity += user_card.quantity

    return {
        "card_id": card.card_id,
        "name": card.name,
        "edition": card.edition,
        "rarity": card.rarity,
        "owners": owners,
        "total_quantity": total_quantity,
        "price": card.price,
    }


# ============================================================
# GLOBAL CARD STATISTICS
# ============================================================

def get_global_statistics() -> dict:

    with _LOCK:

        cards = list(
            _CARDS.values()
        )

        user_cards = list(
            _USER_CARDS.values()
        )

    return {
        "total_cards": len(cards),
        "enabled_cards": sum(
            1
            for card in cards
            if card.enabled
        ),
        "premium_cards": sum(
            1
            for card in cards
            if card.edition == PREMIUM_EDITION
        ),
        "limited_cards": sum(
            1
            for card in cards
            if card.limited
        ),
        "shiny_cards": sum(
            1
            for card in cards
            if card.shiny
        ),
        "animated_cards": sum(
            1
            for card in cards
            if card.animated
        ),
        "owned_copies": sum(
            item.quantity
            for item in user_cards
        ),
    }


# ============================================================
# ADMIN BULK GIVE
# ============================================================

def give_card_to_user(
    user_id: int,
    card_id,
    quantity: int = 1,
) -> tuple[bool, str]:

    try:

        user_card = add_user_card(
            user_id=user_id,
            card_id=card_id,
            quantity=quantity,
        )

        return (
            True,
            (
                f"🎁 Card given successfully!\n"
                f"🎴 ID: <code>{escape_html(user_card.card_id)}</code>\n"
                f"📦 Quantity: <b>{quantity}</b>"
            ),
        )

    except Exception as exc:

        return (
            False,
            f"❌ {escape_html(str(exc))}",
        )


def remove_card_from_user(
    user_id: int,
    card_id,
    quantity: int = 1,
) -> tuple[bool, str]:

    success = remove_user_card(
        user_id=user_id,
        card_id=card_id,
        quantity=quantity,
    )

    if not success:
        return (
            False,
            "❌ User does not have enough copies.",
        )

    return (
        True,
        "✅ Card removed successfully.",
    )


# ============================================================
# BULK USER COLLECTION
# ============================================================

def get_user_collection_with_cards(
    user_id: int,
) -> list[tuple[Card, UserCard]]:

    result = []

    for user_card in get_user_cards(
        user_id
    ):

        card = get_card(
            user_card.card_id
        )

        if card is not None:
            result.append(
                (
                    card,
                    user_card,
                )
            )

    return result


# ============================================================
# RESET
# ============================================================

def clear_cards() -> None:

    with _LOCK:
        _CARDS.clear()
        _USER_CARDS.clear()


# ============================================================
# HTML ESCAPE
# ============================================================

def escape_html(
    value: str,
) -> str:

    return (
        str(value)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


# ============================================================
# EXPORT
# ============================================================

__all__ = [

    # Config
    "EDITIONS",
    "PREMIUM_EDITION",
    "RARITIES",
    "ELEMENTS",
    "CLASSES",

    "MAX_CARD_LEVEL",
    "MAX_CARD_PRICE",

    "EDITION_MAX_PRICES",

    # Data
    "Card",
    "UserCard",

    # Validation
    "normalize_card_id",
    "validate_edition",
    "validate_rarity",
    "validate_element",
    "validate_class",
    "validate_media_type",

    # Card CRUD
    "create_card",
    "get_card",
    "card_exists",
    "update_card",
    "delete_card",

    "enable_card",
    "disable_card",

    # Card lists
    "get_all_cards",
    "get_card_count",

    # Search
    "search_cards",

    # Filters
    "get_cards_by_edition",
    "get_cards_by_rarity",
    "get_premium_cards",
    "get_limited_cards",
    "get_shiny_cards",
    "get_animated_cards",

    # User collection
    "add_user_card",
    "remove_user_card",
    "get_user_card",
    "has_user_card",
    "get_user_cards",
    "get_user_unique_card_count",
    "get_user_total_card_count",

    # Favorite
    "set_favorite",
    "favorite_card",
    "unfavorite_card",
    "get_favorite_cards",

    # EXP / Level
    "exp_required_for_level",
    "get_level_progress",
    "add_card_exp",
    "upgrade_card",

    # Power
    "calculate_card_power",
    "calculate_user_card_power",

    # Price
    "get_card_max_price",
    "get_sell_price",
    "set_card_price",

    # Formatting
    "get_card_tags",
    "format_card",
    "format_user_card",

    # Media
    "get_card_media",

    # Statistics
    "get_card_statistics",
    "get_global_statistics",

    # Admin
    "give_card_to_user",
    "remove_card_from_user",

    # Collection
    "get_user_collection_with_cards",

    # Reset
    "clear_cards",

    # Utils
    "escape_html",
]
