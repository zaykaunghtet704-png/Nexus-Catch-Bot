# card_manager.py
# Nexus Catch Bot
# Persistent Card Management Core
#
# IMPORTANT:
# Persistent card data is stored in database.py / SQLite.
# Cards are NEVER physically deleted by this module.
#
# Supports:
# - 13 Editions
# - Photo / Video / Animation
# - Existing Card ID restore/reuse
# - Card editing
# - Card search
# - Collection
# - Favorites
# - EXP / Level
# - Card power
# - Drop weights
# - Top 15 card owners
# - Safe soft-delete / restore

from __future__ import annotations

from dataclasses import dataclass
from html import escape as _html_escape
from typing import Optional, Any


# ============================================================
# 13 EDITIONS
# ============================================================

EDITIONS = [
    "Common",
    "Uncommon",
    "Rare",
    "Legends",
    "Mythical",
    "Divine",
    "Crossverse",
    "Cataphract",
    "Supreme",
    "Celestial",
    "Immortal",
    "Eternal",
    "Premium",
]

PREMIUM_EDITION = "Premium"


# ============================================================
# EDITION EMOJIS
# ============================================================

EDITION_EMOJIS = {
    "Common": "⚪",
    "Uncommon": "🟢",
    "Rare": "🔵",
    "Legends": "🟣",
    "Mythical": "🌌",
    "Divine": "✨",
    "Crossverse": "🌠",
    "Cataphract": "⚔️",
    "Supreme": "👑",
    "Celestial": "☄️",
    "Immortal": "🔥",
    "Eternal": "♾️",
    "Premium": "💎",
}


# ============================================================
# EDITION DROP WEIGHTS
# ============================================================

EDITION_DROP_WEIGHTS = {
    "Common": 34.65,
    "Uncommon": 20.00,
    "Rare": 13.00,
    "Legends": 9.00,
    "Mythical": 7.00,
    "Divine": 5.00,
    "Crossverse": 3.50,
    "Cataphract": 2.50,
    "Supreme": 1.80,
    "Celestial": 1.20,
    "Immortal": 0.70,
    "Eternal": 0.60,
    "Premium": 0.05,
}


# ============================================================
# RARITIES
# ============================================================

RARITIES = [
    "Common",
    "Uncommon",
    "Rare",
    "Legends",
    "Mythical",
    "Divine",
    "Crossverse",
    "Cataphract",
    "Supreme",
    "Celestial",
    "Immortal",
    "Eternal",
    "Premium",
]


# ============================================================
# ELEMENTS
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


# ============================================================
# CLASSES
# ============================================================

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
# LEVEL SYSTEM
# ============================================================

MAX_CARD_LEVEL = 100
BASE_EXP_REQUIRED = 100
UPGRADE_EXP_MULTIPLIER = 1.25

MAX_ATK = 99999
MAX_DEF = 99999
MAX_HP = 999999
MAX_SPEED = 9999


# ============================================================
# PRICE SYSTEM
# ============================================================

MAX_CARD_PRICE = 15000

EDITION_MAX_PRICES = {
    "Common": 500,
    "Uncommon": 750,
    "Rare": 1200,
    "Legends": 2000,
    "Mythical": 3000,
    "Divine": 4500,
    "Crossverse": 6000,
    "Cataphract": 7500,
    "Supreme": 9000,
    "Celestial": 10500,
    "Immortal": 12000,
    "Eternal": 13500,
    "Premium": 15000,
}


# ============================================================
# MEDIA
# ============================================================

MEDIA_TYPES = {
    "photo",
    "video",
    "animation",
}


# ============================================================
# DATA CLASSES
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

    drop_weight: float = 1.0

    metadata: Optional[dict] = None


@dataclass
class UserCard:
    owner_id: int
    card_id: str

    quantity: int = 1

    level: int = 1
    exp: int = 0

    favorite: bool = False

    obtained_count: int = 1


# ============================================================
# DATABASE
# ============================================================

try:
    import database as _db
except Exception:
    _db = None


# ============================================================
# BASIC HELPERS
# ============================================================

def escape_html(value: Any) -> str:
    return _html_escape(str(value))


def normalize_card_id(card_id: Any) -> str:
    if card_id is None:
        raise ValueError("card_id is required")

    value = str(card_id).strip()

    if not value:
        raise ValueError("card_id cannot be empty")

    if value.isdigit():
        return value.zfill(4)

    return value


def _row_get(
    row: Any,
    key: str,
    default: Any = None,
) -> Any:

    if row is None:
        return default

    if isinstance(row, dict):
        return row.get(key, default)

    try:
        return row[key]
    except Exception:
        pass

    try:
        return getattr(row, key)
    except Exception:
        return default


def _safe_int(
    value: Any,
    default: int = 0,
) -> int:

    try:
        return int(value)
    except Exception:
        return default


def _safe_float(
    value: Any,
    default: float = 0.0,
) -> float:

    try:
        return float(value)
    except Exception:
        return default


def _bool(value: Any) -> bool:

    if isinstance(value, str):
        return value.lower().strip() in {
            "1",
            "true",
            "yes",
            "on",
        }

    return bool(value)


# ============================================================
# VALIDATION
# ============================================================

def validate_edition(edition: str) -> bool:
    return str(edition).strip() in EDITIONS


def validate_rarity(rarity: str) -> bool:
    return str(rarity).strip() in RARITIES


def validate_element(element: str) -> bool:
    return str(element).strip() in ELEMENTS


def validate_class(card_class: str) -> bool:
    return str(card_class).strip() in CLASSES


def validate_media_type(
    media_type: Optional[str],
) -> bool:

    if media_type is None:
        return True

    return (
        str(media_type).lower().strip()
        in MEDIA_TYPES
    )


# ============================================================
# EDITION NORMALIZATION
# ============================================================

def normalize_edition(
    value: Optional[str],
) -> str:

    if not value:
        return "Common"

    raw = str(value).strip()

    if raw in EDITIONS:
        return raw

    aliases = {
        "common edition": "Common",
        "uncommon edition": "Uncommon",
        "rare edition": "Rare",

        "super rare": "Legends",
        "super rare edition": "Legends",

        "legendary": "Legends",
        "legendary edition": "Legends",

        "ultra rare": "Mythical",
        "ultra rare edition": "Mythical",

        "epic": "Mythical",
        "epic edition": "Mythical",

        "mythic": "Mythical",
        "mythic edition": "Mythical",

        "divine edition": "Divine",
        "crossverse edition": "Crossverse",
        "cataphract edition": "Cataphract",
        "supreme edition": "Supreme",
        "celestial edition": "Celestial",
        "immortal edition": "Immortal",
        "eternal edition": "Eternal",
        "premium edition": "Premium",
    }

    return aliases.get(
        raw.lower(),
        raw,
    )


# ============================================================
# RARITY NORMALIZATION
# ============================================================

def normalize_rarity(
    value: Any,
) -> str:

    if isinstance(value, int):
        rarity_names = {
            1: "Common",
            2: "Uncommon",
            3: "Rare",
            4: "Legends",
            5: "Mythical",
            6: "Divine",
            7: "Crossverse",
            8: "Cataphract",
            9: "Supreme",
            10: "Celestial",
            11: "Immortal",
            12: "Eternal",
            13: "Premium",
        }

        return rarity_names.get(
            value,
            "Common",
        )

    raw = str(value or "").strip()

    if raw in RARITIES:
        return raw

    aliases = {
        "sr": "Legends",
        "ssr": "Mythical",
        "ur": "Divine",
        "legendary": "Legends",
        "mythic": "Mythical",
        "epic": "Mythical",
    }

    return aliases.get(
        raw.lower(),
        "Common",
    )


# ============================================================
# CARD ROW -> CARD
# ============================================================

def _row_to_card(
    row: Any,
) -> Optional[Card]:

    if row is None:
        return None

    card_id = _row_get(
        row,
        "char_id",
        _row_get(
            row,
            "card_id",
            _row_get(
                row,
                "id",
                "",
            ),
        ),
    )

    name = _row_get(
        row,
        "name",
        "",
    )

    if not card_id or not name:
        return None

    edition = normalize_edition(
        _row_get(
            row,
            "edition",
            "Common",
        )
    )

    rarity = normalize_rarity(
        _row_get(
            row,
            "rarity",
            "Common",
        )
    )

    media_type = _row_get(
        row,
        "media_type",
        None,
    )

    image_file_id = _row_get(
        row,
        "image_file_id",
        "",
    )

    video_file_id = _row_get(
        row,
        "video_file_id",
        "",
    )

    media_id = _row_get(
        row,
        "media_id",
        None,
    )

    if not media_id:
        if (
            str(media_type or "").lower()
            == "video"
        ):
            media_id = video_file_id
        else:
            media_id = image_file_id

    return Card(
        card_id=normalize_card_id(card_id),
        name=str(name),

        edition=edition,
        rarity=rarity,

        atk=_safe_int(
            _row_get(
                row,
                "atk",
                0,
            )
        ),

        defense=_safe_int(
            _row_get(
                row,
                "defense",
                _row_get(
                    row,
                    "def",
                    0,
                ),
            )
        ),

        hp=_safe_int(
            _row_get(
                row,
                "hp",
                0,
            )
        ),

        speed=_safe_int(
            _row_get(
                row,
                "speed",
                0,
            )
        ),

        element=str(
            _row_get(
                row,
                "element",
                "Neutral",
            )
        ),

        card_class=str(
            _row_get(
                row,
                "card_class",
                _row_get(
                    row,
                    "class",
                    "Special",
                ),
            )
        ),

        description=str(
            _row_get(
                row,
                "description",
                "",
            )
            or ""
        ),

        media_type=(
            str(media_type).lower()
            if media_type
            else None
        ),

        media_id=media_id,

        price=_safe_int(
            _row_get(
                row,
                "price",
                0,
            )
        ),

        shiny=_bool(
            _row_get(
                row,
                "shiny",
                False,
            )
        ),

        limited=_bool(
            _row_get(
                row,
                "limited",
                False,
            )
        ),

        animated=_bool(
            _row_get(
                row,
                "animated",
                False,
            )
        ),

        level=_safe_int(
            _row_get(
                row,
                "level",
                1,
            ),
            1,
        ),

        exp=_safe_int(
            _row_get(
                row,
                "exp",
                0,
            )
        ),

        enabled=_bool(
            _row_get(
                row,
                "active",
                _row_get(
                    row,
                    "enabled",
                    1,
                ),
            )
        ),

        drop_weight=_safe_float(
            _row_get(
                row,
                "drop_weight",
                1.0,
            ),
            1.0,
        ),

        metadata={},
    )


# ============================================================
# CARD CREATION / RESTORE
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
    drop_weight: float = 1.0,
) -> Card:

    if _db is None:
        raise RuntimeError(
            "database.py could not be imported."
        )

    cid = normalize_card_id(card_id)

    name = str(name).strip()

    if not name:
        raise ValueError(
            "Card name is required."
        )

    edition = normalize_edition(
        edition
    )

    rarity = normalize_rarity(
        rarity
    )

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

    if not validate_media_type(
        media_type
    ):
        raise ValueError(
            f"Invalid media type: {media_type}"
        )

    max_price = EDITION_MAX_PRICES.get(
        edition,
        MAX_CARD_PRICE,
    )

    price = max(
        0,
        min(
            int(price),
            max_price,
        ),
    )

    drop_weight = max(
        0.0,
        float(drop_weight),
    )

    # --------------------------------------------------------
    # Existing Card ID:
    #
    # database.add_card() should UPDATE / RESTORE the existing
    # row rather than create a duplicate.
    # --------------------------------------------------------

    image_file_id = ""
    video_file_id = ""

    if (
        media_type
        and str(media_type).lower()
        == "video"
    ):
        video_file_id = media_id or ""
    else:
        image_file_id = media_id or ""

    if not hasattr(
        _db,
        "add_card",
    ):
        raise RuntimeError(
            "database.py does not contain add_card()."
        )

    row = None

    try:
        row = _db.add_card(
            char_id=cid,
            name=name,
            edition=edition,
            rarity=rarity,
            price=price,
            image_file_id=image_file_id,
            video_file_id=video_file_id,
            media_type=(
                media_type or "photo"
            ),
            description=description or "",
            drop_weight=drop_weight,
            active=1,
        )

    except TypeError:

        try:
            row = _db.add_card(
                cid,
                name,
                edition,
                rarity,
                price,
                image_file_id,
                video_file_id,
                media_type or "photo",
                description or "",
                drop_weight,
            )

        except TypeError:

            row = _db.add_card(
                cid,
                name,
                edition,
                rarity,
                price,
                image_file_id,
                video_file_id,
                media_type or "photo",
                description or "",
            )

    # Restore old card ID if it was soft deleted.
    if hasattr(
        _db,
        "restore_card",
    ):
        try:
            _db.restore_card(cid)
        except Exception:
            pass

    card = get_card_any(cid)

    if card is None:

        card = Card(
            card_id=cid,
            name=name,
            edition=edition,
            rarity=rarity,

            atk=max(
                0,
                int(atk),
            ),

            defense=max(
                0,
                int(defense),
            ),

            hp=max(
                0,
                int(hp),
            ),

            speed=max(
                0,
                int(speed),
            ),

            element=element,
            card_class=card_class,

            description=description or "",

            media_type=(
                media_type or "photo"
            ),

            media_id=media_id,

            price=price,

            shiny=bool(shiny),
            limited=bool(limited),
            animated=bool(animated),

            drop_weight=drop_weight,

            metadata=dict(
                metadata or {}
            ),
        )

    else:

        update_card(
            cid,

            name=name,
            edition=edition,
            rarity=rarity,

            atk=atk,
            defense=defense,
            hp=hp,
            speed=speed,

            element=element,
            card_class=card_class,

            description=description or "",

            media_type=(
                media_type
                or card.media_type
            ),

            media_id=media_id,

            price=price,

            shiny=shiny,
            limited=limited,
            animated=animated,

            drop_weight=drop_weight,

            active=1,
        )

        card = (
            get_card_any(cid)
            or card
        )

    return card


# ============================================================
# GET CARD
# ============================================================

def get_card(
    card_id,
) -> Optional[Card]:

    if _db is None:
        return None

    try:
        cid = normalize_card_id(
            card_id
        )
    except Exception:
        return None

    row = None

    if hasattr(
        _db,
        "get_card",
    ):
        try:
            row = _db.get_card(cid)
        except Exception:
            row = None

    if row is None:
        if hasattr(
            _db,
            "get_card_any",
        ):
            try:
                row = _db.get_card_any(
                    cid
                )
            except Exception:
                row = None

    return _row_to_card(row)


def get_card_any(
    card_id,
) -> Optional[Card]:

    if _db is None:
        return None

    try:
        cid = normalize_card_id(
            card_id
        )
    except Exception:
        return None

    row = None

    if hasattr(
        _db,
        "get_card_any",
    ):
        try:
            row = _db.get_card_any(
                cid
            )
        except Exception:
            row = None

    if row is None:
        if hasattr(
            _db,
            "get_card",
        ):
            try:
                row = _db.get_card(
                    cid
                )
            except Exception:
                row = None

    return _row_to_card(row)


def card_exists(
    card_id,
) -> bool:

    return (
        get_card_any(card_id)
        is not None
    )


# ============================================================
# EDIT CARD
# ============================================================

def update_card(
    card_id,
    **changes,
) -> Optional[Card]:

    if _db is None:
        return None

    cid = normalize_card_id(
        card_id
    )

    card = get_card_any(cid)

    if card is None:
        return None

    if "edition" in changes:
        changes["edition"] = (
            normalize_edition(
                changes["edition"]
            )
        )

        if not validate_edition(
            changes["edition"]
        ):
            raise ValueError(
                "Invalid edition."
            )

    if "rarity" in changes:
        changes["rarity"] = (
            normalize_rarity(
                changes["rarity"]
            )
        )

        if not validate_rarity(
            changes["rarity"]
        ):
            raise ValueError(
                "Invalid rarity."
            )

    if "element" in changes:

        if not validate_element(
            changes["element"]
        ):
            raise ValueError(
                "Invalid element."
            )

    if "card_class" in changes:

        if not validate_class(
            changes["card_class"]
        ):
            raise ValueError(
                "Invalid class."
            )

    if "media_type" in changes:

        if not validate_media_type(
            changes["media_type"]
        ):
            raise ValueError(
                "Invalid media type."
            )

        changes["media_type"] = (
            str(
                changes["media_type"]
            ).lower()
        )

    if "price" in changes:

        edition = changes.get(
            "edition",
            card.edition,
        )

        max_price = (
            EDITION_MAX_PRICES.get(
                edition,
                MAX_CARD_PRICE,
            )
        )

        changes["price"] = max(
            0,
            min(
                int(changes["price"]),
                max_price,
            ),
        )

    if "drop_weight" in changes:

        changes["drop_weight"] = max(
            0.0,
            float(
                changes[
                    "drop_weight"
                ]
            ),
        )

    if "atk" in changes:
        changes["atk"] = max(
            0,
            min(
                int(changes["atk"]),
                MAX_ATK,
            ),
        )

    if "defense" in changes:
        changes["defense"] = max(
            0,
            min(
                int(changes["defense"]),
                MAX_DEF,
            ),
        )

    if "hp" in changes:
        changes["hp"] = max(
            0,
            min(
                int(changes["hp"]),
                MAX_HP,
            ),
        )

    if "speed" in changes:
        changes["speed"] = max(
            0,
            min(
                int(changes["speed"]),
                MAX_SPEED,
            ),
        )

    # --------------------------------------------------------
    # Map media_id into existing DB columns when necessary.
    # --------------------------------------------------------

    if "media_id" in changes:

        media_id = (
            changes.pop("media_id")
            or ""
        )

        media_type = str(
            changes.get(
                "media_type",
                card.media_type or "photo",
            )
        ).lower()

        if media_type == "video":

            changes[
                "video_file_id"
            ] = media_id

            changes[
                "image_file_id"
            ] = ""

        else:

            changes[
                "image_file_id"
            ] = media_id

            if media_type == "photo":
                changes[
                    "video_file_id"
                ] = ""

    if "name" in changes:
        changes["name"] = str(
            changes["name"]
        ).strip()

    if "active" in changes:
        changes["active"] = (
            1 if changes["active"]
            else 0
        )

    if hasattr(
        _db,
        "update_card",
    ):

        try:

            _db.update_card(
                cid,
                **changes,
            )

        except TypeError:

            try:

                _db.update_card(
                    char_id=cid,
                    **changes,
                )

            except Exception:
                pass

    return get_card_any(cid)


# ============================================================
# SOFT DELETE
# ============================================================

def delete_card(
    card_id,
) -> bool:

    if _db is None:
        return False

    cid = normalize_card_id(
        card_id
    )

    # IMPORTANT:
    # Never physically delete the card row.

    if hasattr(
        _db,
        "delete_card",
    ):

        try:
            return bool(
                _db.delete_card(cid)
            )
        except Exception:
            pass

    if hasattr(
        _db,
        "update_card",
    ):

        try:
            _db.update_card(
                cid,
                active=0,
            )

            return True

        except Exception:
            pass

    return False


# ============================================================
# RESTORE
# ============================================================

def restore_card(
    card_id,
) -> bool:

    if _db is None:
        return False

    cid = normalize_card_id(
        card_id
    )

    if hasattr(
        _db,
        "restore_card",
    ):

        try:
            return bool(
                _db.restore_card(cid)
            )
        except Exception:
            pass

    if hasattr(
        _db,
        "update_card",
    ):

        try:

            _db.update_card(
                cid,
                active=1,
            )

            return True

        except Exception:
            pass

    return False


def enable_card(
    card_id,
) -> bool:

    return restore_card(
        card_id
    )


def disable_card(
    card_id,
) -> bool:

    if _db is None:
        return False

    cid = normalize_card_id(
        card_id
    )

    if hasattr(
        _db,
        "update_card",
    ):

        try:

            _db.update_card(
                cid,
                active=0,
            )

            return True

        except Exception:
            pass

    return False


# ============================================================
# ALL CARDS
# ============================================================

def get_all_cards(
    include_disabled: bool = False,
) -> list[Card]:

    if _db is None:
        return []

    rows = []

    if (
        include_disabled
        and hasattr(
            _db,
            "get_all_cards_including_inactive",
        )
    ):

        try:
            rows = (
                _db
                .get_all_cards_including_inactive()
            )
        except Exception:
            rows = []

    elif hasattr(
        _db,
        "get_all_cards",
    ):

        try:
            rows = _db.get_all_cards(
                include_disabled
            )

        except TypeError:

            try:
                rows = (
                    _db.get_all_cards()
                )
            except Exception:
                rows = []

    cards = []

    for row in rows or []:

        card = _row_to_card(row)

        if card is None:
            continue

        if (
            not include_disabled
            and not card.enabled
        ):
            continue

        cards.append(card)

    return sorted(
        cards,
        key=lambda c: c.card_id,
    )


def get_card_count(
    include_disabled: bool = False,
) -> int:

    return len(
        get_all_cards(
            include_disabled
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

    q = str(
        query
    ).strip().lower()

    if not q:
        return []

    if (
        _db is not None
        and hasattr(
            _db,
            "search_cards",
        )
    ):

        try:

            rows = _db.search_cards(
                q
            )

            result = []

            for row in rows or []:

                card = _row_to_card(
                    row
                )

                if card is None:
                    continue

                if (
                    not include_disabled
                    and not card.enabled
                ):
                    continue

                result.append(card)

            if result:
                return result

        except Exception:
            pass

    result = []

    for card in get_all_cards(
        include_disabled
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
            result.append(card)

    return result


# ============================================================
# EDITION FILTER
# ============================================================

def get_cards_by_edition(
    edition: str,
) -> list[Card]:

    edition = normalize_edition(
        edition
    )

    return [
        card
        for card in get_all_cards()
        if card.edition == edition
    ]


def get_cards_by_rarity(
    rarity: str,
) -> list[Card]:

    rarity = normalize_rarity(
        rarity
    )

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
# DROP WEIGHT
# ============================================================

def get_edition_drop_weight(
    edition: str,
) -> float:

    edition = normalize_edition(
        edition
    )

    return float(
        EDITION_DROP_WEIGHTS.get(
            edition,
            0.0,
        )
    )


def get_card_drop_weight(
    card_id,
) -> float:

    card = get_card(
        card_id
    )

    if card is None:
        return 0.0

    return max(
        0.0,
        float(
            card.drop_weight
        ),
    )


def set_card_drop_weight(
    card_id,
    weight: float,
) -> bool:

    if _db is None:
        return False

    cid = normalize_card_id(
        card_id
    )

    weight = max(
        0.0,
        float(weight),
    )

    if hasattr(
        _db,
        "update_card_drop_weight",
    ):

        try:

            return bool(
                _db.update_card_drop_weight(
                    cid,
                    weight,
                )
            )

        except Exception:
            pass

    if hasattr(
        _db,
        "update_card",
    ):

        try:

            _db.update_card(
                cid,
                drop_weight=weight,
            )

            return True

        except Exception:
            pass

    return False


# ============================================================
# USER COLLECTION
# ============================================================

def add_user_card(
    user_id: int,
    card_id,
    quantity: int = 1,
) -> UserCard:

    if _db is None:
        raise RuntimeError(
            "database.py unavailable."
        )

    quantity = int(quantity)

    if quantity <= 0:
        raise ValueError(
            "quantity must be greater than zero."
        )

    cid = normalize_card_id(
        card_id
    )

    if not card_exists(cid):
        raise ValueError(
            f"Card does not exist: {cid}"
        )

    if not hasattr(
        _db,
        "add_user_card",
    ):
        raise RuntimeError(
            "database.py missing add_user_card()."
        )

    row = _db.add_user_card(
        int(user_id),
        cid,
        quantity,
    )

    if isinstance(
        row,
        UserCard,
    ):
        return row

    return UserCard(
        owner_id=int(user_id),
        card_id=cid,

        quantity=_safe_int(
            _row_get(
                row,
                "quantity",
                quantity,
            ),
            quantity,
        ),

        level=_safe_int(
            _row_get(
                row,
                "level",
                1,
            ),
            1,
        ),

        exp=_safe_int(
            _row_get(
                row,
                "exp",
                0,
            )
        ),

        favorite=_bool(
            _row_get(
                row,
                "favorite",
                0,
            )
        ),

        obtained_count=_safe_int(
            _row_get(
                row,
                "obtained_count",
                quantity,
            ),
            quantity,
        ),
    )


def remove_user_card(
    user_id: int,
    card_id,
    quantity: int = 1,
) -> bool:

    if _db is None:
        return False

    cid = normalize_card_id(
        card_id
    )

    if hasattr(
        _db,
        "remove_user_card",
    ):

        try:

            return bool(
                _db.remove_user_card(
                    int(user_id),
                    cid,
                    int(quantity),
                )
            )

        except Exception:
            pass

    return False


def get_user_card(
    user_id: int,
    card_id,
) -> Optional[UserCard]:

    if _db is None:
        return None

    cid = normalize_card_id(
        card_id
    )

    if not hasattr(
        _db,
        "get_user_card",
    ):
        return None

    try:

        row = _db.get_user_card(
            int(user_id),
            cid,
        )

    except Exception:
        return None

    if row is None:
        return None

    if isinstance(
        row,
        UserCard,
    ):
        return row

    return UserCard(
        owner_id=int(user_id),
        card_id=cid,

        quantity=_safe_int(
            _row_get(
                row,
                "quantity",
                0,
            )
        ),

        level=_safe_int(
            _row_get(
                row,
                "level",
                1,
            ),
            1,
        ),

        exp=_safe_int(
            _row_get(
                row,
                "exp",
                0,
            )
        ),

        favorite=_bool(
            _row_get(
                row,
                "favorite",
                0,
            )
        ),

        obtained_count=_safe_int(
            _row_get(
                row,
                "obtained_count",
                0,
            )
        ),
    )


def has_user_card(
    user_id: int,
    card_id,
) -> bool:

    card = get_user_card(
        user_id,
        card_id,
    )

    return (
        card is not None
        and card.quantity > 0
    )


def get_user_cards(
    user_id: int,
) -> list[UserCard]:

    if _db is None:
        return []

    if not hasattr(
        _db,
        "get_user_cards",
    ):
        return []

    try:

        rows = _db.get_user_cards(
            int(user_id)
        )

    except Exception:
        return []

    result = []

    for row in rows or []:

        if isinstance(
            row,
            UserCard,
        ):
            result.append(row)
            continue

        cid = _row_get(
            row,
            "char_id",
            _row_get(
                row,
                "card_id",
                "",
            ),
        )

        if not cid:
            continue

        result.append(
            UserCard(
                owner_id=int(
                    user_id
                ),

                card_id=normalize_card_id(
                    cid
                ),

                quantity=_safe_int(
                    _row_get(
                        row,
                        "quantity",
                        0,
                    )
                ),

                level=_safe_int(
                    _row_get(
                        row,
                        "level",
                        1,
                    ),
                    1,
                ),

                exp=_safe_int(
                    _row_get(
                        row,
                        "exp",
                        0,
                    )
                ),

                favorite=_bool(
                    _row_get(
                        row,
                        "favorite",
                        0,
                    )
                ),

                obtained_count=_safe_int(
                    _row_get(
                        row,
                        "obtained_count",
                        0,
                    )
                ),
            )
        )

    return [
        item
        for item in result
        if item.quantity > 0
    ]


def get_user_unique_card_count(
    user_id: int,
) -> int:

    return len(
        get_user_cards(
            user_id
        )
    )


def get_user_total_card_count(
    user_id: int,
) -> int:

    return sum(
        card.quantity
        for card in get_user_cards(
            user_id
        )
    )


# ============================================================
# FAVORITE
# ============================================================

def set_favorite(
    user_id: int,
    card_id,
    value: bool = True,
) -> bool:

    if _db is None:
        return False

    cid = normalize_card_id(
        card_id
    )

    if not has_user_card(
        user_id,
        cid,
    ):
        return False

    if hasattr(
        _db,
        "set_favorite",
    ):

        try:

            return bool(
                _db.set_favorite(
                    int(user_id),
                    cid,
                    bool(value),
                )
            )

        except Exception:
            pass

    return False


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
        card
        for card in get_user_cards(
            user_id
        )
        if card.favorite
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

    required = exp_required_for_level(
        level
    )

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


def add_card_exp(
    user_id: int,
    card_id,
    amount: int,
) -> tuple[bool, int, int]:

    amount = int(amount)

    if amount <= 0:
        return False, 0, 0

    user_card = get_user_card(
        user_id,
        card_id,
    )

    if user_card is None:
        return False, 0, 0

    if hasattr(
        _db,
        "add_card_exp",
    ):

        try:

            result = _db.add_card_exp(
                int(user_id),
                normalize_card_id(
                    card_id
                ),
                amount,
            )

            if result:
                return result

        except Exception:
            pass

    return (
        False,
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

        missing = (
            required
            - user_card.exp
        )

        return (
            False,
            (
                "❌ Not enough EXP.\n"
                f"Need <b>{missing}</b> more EXP."
            ),
        )

    if hasattr(
        _db,
        "upgrade_card",
    ):

        try:

            return _db.upgrade_card(
                int(user_id),
                normalize_card_id(
                    card_id
                ),
            )

        except Exception:
            pass

    return (
        False,
        "❌ Unable to upgrade this card.",
    )


# ============================================================
# POWER
# ============================================================

def calculate_card_power(
    card: Card,
    level: int = 1,
) -> int:

    level = max(
        1,
        int(level),
    )

    multiplier = (
        1.0
        + (
            (level - 1)
            * 0.05
        )
    )

    base = (
        card.atk
        + card.defense
        + (
            card.hp // 10
        )
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

    card = get_card_any(
        card_id
    )

    if card is None:
        return 0

    return EDITION_MAX_PRICES.get(
        card.edition,
        MAX_CARD_PRICE,
    )


def get_sell_price(
    card_id,
) -> int:

    card = get_card_any(
        card_id
    )

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

    card = get_card_any(
        card_id
    )

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

    updated = update_card(
        card.card_id,
        price=price,
    )

    return updated is not None


# ============================================================
# TAGS
# ============================================================

def get_card_tags(
    card: Card,
) -> list[str]:

    tags = []

    if card.shiny:
        tags.append(
            "✨ Shiny"
        )

    if card.limited:
        tags.append(
            "⏳ Limited"
        )

    if card.animated:
        tags.append(
            "🎞️ Animated"
        )

    if card.edition == PREMIUM_EDITION:
        tags.append(
            "💎 Premium"
        )

    return tags


# ============================================================
# CARD FORMAT
# ============================================================

def format_card(
    card: Card,
) -> str:

    emoji = EDITION_EMOJIS.get(
        card.edition,
        "🎴",
    )

    tags = get_card_tags(
        card
    )

    tag_text = ""

    if tags:
        tag_text = (
            "\n🏷️ "
            + " • ".join(tags)
        )

    description = (
        card.description.strip()
        if card.description
        else "No description."
    )

    return (
        "╔══════════════════╗\n"
        f"   {emoji} <b>NEXUS CARD</b>\n"
        "╚══════════════════╝\n\n"

        f"🆔 ID        : "
        f"<code>{escape_html(card.card_id)}</code>\n"

        f"👤 Name      : "
        f"<b>{escape_html(card.name)}</b>\n"

        f"{emoji} Edition   : "
        f"<b>{escape_html(card.edition)}</b>\n"

        f"⭐ Rarity    : "
        f"<b>{escape_html(card.rarity)}</b>\n\n"

        f"⚔️ ATK       : "
        f"<b>{card.atk:,}</b>\n"

        f"🛡️ DEF       : "
        f"<b>{card.defense:,}</b>\n"

        f"❤️ HP        : "
        f"<b>{card.hp:,}</b>\n"

        f"⚡ Speed     : "
        f"<b>{card.speed:,}</b>\n\n"

        f"🌌 Element   : "
        f"<b>{escape_html(card.element)}</b>\n"

        f"⚔️ Class     : "
        f"<b>{escape_html(card.card_class)}</b>\n"

        f"🪙 Price     : "
        f"<b>{card.price:,}</b> Coins"

        f"{tag_text}\n\n"

        f"📝 <i>"
        f"{escape_html(description)}"
        f"</i>"
    )


def format_user_card(
    user_card: UserCard,
) -> str:

    card = get_card_any(
        user_card.card_id
    )

    if card is None:

        return (
            "🎴 Card\n"
            f"🆔 <code>"
            f"{escape_html(user_card.card_id)}"
            f"</code>"
        )

    power = (
        calculate_user_card_power(
            user_card
        )
    )

    favorite = (
        " ❤️ Favorite"
        if user_card.favorite
        else ""
    )

    emoji = EDITION_EMOJIS.get(
        card.edition,
        "🎴",
    )

    return (
        f"{emoji} "
        f"<b>{escape_html(card.name)}</b>"
        f"{favorite}\n\n"

        f"🆔 <code>"
        f"{escape_html(card.card_id)}"
        f"</code>\n"

        f"💎 "
        f"{escape_html(card.edition)}\n"

        f"⭐ "
        f"{escape_html(card.rarity)}\n\n"

        f"📊 Level    : "
        f"<b>{user_card.level}</b>\n"

        f"✨ EXP      : "
        f"<b>{user_card.exp:,}</b>\n"

        f"📦 Quantity : "
        f"<b>{user_card.quantity:,}</b>\n"

        f"⚔️ Power    : "
        f"<b>{power:,}</b>"
    )


# ============================================================
# MEDIA
# ============================================================

def get_card_media(
    card_id,
) -> Optional[dict]:

    card = get_card_any(
        card_id
    )

    if card is None:
        return None

    if not card.media_id:
        return None

    media_type = (
        card.media_type
        or "photo"
    ).lower()

    if media_type not in MEDIA_TYPES:
        media_type = "photo"

    return {
        "type": media_type,
        "media_id": card.media_id,
    }


# ============================================================
# CARD STATISTICS
# ============================================================

def get_card_statistics(
    card_id,
) -> dict:

    card = get_card_any(
        card_id
    )

    if card is None:
        return {}

    owners = 0
    total_quantity = 0

    rows = get_card_top_owners(
        card.card_id,
        15,
    )

    for row in rows:

        quantity = _safe_int(
            _row_get(
                row,
                "quantity",
                _row_get(
                    row,
                    "count",
                    0,
                ),
            )
        )

        if quantity > 0:
            owners += 1
            total_quantity += quantity

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
# TOP 15 CARD OWNERS
# ============================================================

def get_card_top_owners(
    card_id,
    limit: int = 15,
) -> list:

    if _db is None:
        return []

    cid = normalize_card_id(
        card_id
    )

    limit = max(
        1,
        min(
            int(limit),
            100,
        ),
    )

    if hasattr(
        _db,
        "get_card_top_owners",
    ):

        try:

            return list(
                _db.get_card_top_owners(
                    cid,
                    limit,
                )
                or []
            )

        except Exception:
            return []

    return []


# ============================================================
# GLOBAL STATISTICS
# ============================================================

def get_global_statistics() -> dict:

    cards = get_all_cards(
        include_disabled=True
    )

    premium = 0
    limited = 0
    shiny = 0
    animated = 0

    for card in cards:

        if (
            card.edition
            == PREMIUM_EDITION
        ):
            premium += 1

        if card.limited:
            limited += 1

        if card.shiny:
            shiny += 1

        if card.animated:
            animated += 1

    return {
        "total_cards": len(cards),

        "enabled_cards": sum(
            1
            for card in cards
            if card.enabled
        ),

        "premium_cards": premium,

        "limited_cards": limited,

        "shiny_cards": shiny,

        "animated_cards": animated,
    }


# ============================================================
# ADMIN GIVE
# ============================================================

def give_card_to_user(
    user_id: int,
    card_id,
    quantity: int = 1,
) -> tuple[bool, str]:

    try:

        user_card = add_user_card(
            user_id,
            card_id,
            quantity,
        )

        return (
            True,
            (
                "🎁 <b>CARD ADDED</b>\n\n"
                f"🎴 ID: "
                f"<code>"
                f"{escape_html(user_card.card_id)}"
                f"</code>\n"

                f"📦 Quantity: "
                f"<b>{quantity:,}</b>"
            ),
        )

    except Exception as exc:

        return (
            False,
            (
                "❌ "
                + escape_html(
                    str(exc)
                )
            ),
        )


def remove_card_from_user(
    user_id: int,
    card_id,
    quantity: int = 1,
) -> tuple[bool, str]:

    success = remove_user_card(
        user_id,
        card_id,
        quantity,
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
# COLLECTION WITH CARD DATA
# ============================================================

def get_user_collection_with_cards(
    user_id: int,
) -> list[tuple[Card, UserCard]]:

    result = []

    for user_card in get_user_cards(
        user_id
    ):

        card = get_card_any(
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
# SAFE CLEAR
# ============================================================

def clear_cards() -> None:
    """
    Compatibility function only.

    IMPORTANT:
    This function intentionally does NOTHING.

    Persistent cards in SQLite must never be deleted
    accidentally by old code.
    """

    return None


# ============================================================
# EXPORT
# ============================================================

__all__ = [

    # Editions
    "EDITIONS",
    "PREMIUM_EDITION",
    "EDITION_EMOJIS",
    "EDITION_DROP_WEIGHTS",

    # Types
    "RARITIES",
    "ELEMENTS",
    "CLASSES",
    "MEDIA_TYPES",

    # Level
    "MAX_CARD_LEVEL",
    "BASE_EXP_REQUIRED",
    "UPGRADE_EXP_MULTIPLIER",

    # Prices
    "MAX_CARD_PRICE",
    "EDITION_MAX_PRICES",

    # Data
    "Card",
    "UserCard",

    # Utils
    "escape_html",
    "normalize_card_id",
    "normalize_edition",
    "normalize_rarity",

    # Validation
    "validate_edition",
    "validate_rarity",
    "validate_element",
    "validate_class",
    "validate_media_type",

    # CRUD
    "create_card",
    "get_card",
    "get_card_any",
    "card_exists",
    "update_card",
    "delete_card",
    "restore_card",
    "enable_card",
    "disable_card",

    # Lists
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

    # Drop
    "get_edition_drop_weight",
    "get_card_drop_weight",
    "set_card_drop_weight",

    # Collection
    "add_user_card",
    "remove_user_card",
    "get_user_card",
    "has_user_card",
    "get_user_cards",
    "get_user_unique_card_count",
    "get_user_total_card_count",

    # Favorites
    "set_favorite",
    "favorite_card",
    "unfavorite_card",
    "get_favorite_cards",

    # EXP
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
    "get_card_top_owners",
    "get_global_statistics",

    # Admin
    "give_card_to_user",
    "remove_card_from_user",

    # Collection
    "get_user_collection_with_cards",

    # Compatibility
    "clear_cards",
]
