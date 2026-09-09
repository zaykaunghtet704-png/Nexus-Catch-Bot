import random
import time

from database import (
    get_db,
    add_card as db_add_card,
    get_card as db_get_card,
    get_all_cards as db_get_all_cards,
    search_cards as db_search_cards,
    update_card_price as db_update_card_price,
    delete_card as db_delete_card,
)


# ============================================================
# 13 CARD EDITIONS
# ============================================================

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


# ============================================================
# DEFAULT PRICES
# ============================================================

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

    # Premium maximum / default sale value
    "Premium Edition": 15_000,
}


# ============================================================
# DEFAULT DROP RATES
# ============================================================

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


# ============================================================
# EDITION EMOJIS
# ============================================================

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


# ============================================================
# EDITION HELPERS
# ============================================================

def get_edition_emoji(edition: str) -> str:
    return EDITION_EMOJIS.get(
        normalize_edition(edition) or edition,
        "🎴"
    )


def normalize_edition(value: str):
    if not value:
        return None

    value = str(value).strip().lower()

    # Exact full name
    for edition in EDITIONS:
        if edition.lower() == value:
            return edition

    # Allow "Common" instead of "Common Edition"
    value_without_edition = value.replace(" edition", "").strip()

    for edition in EDITIONS:
        short_name = edition.replace(" Edition", "").lower()

        if short_name == value_without_edition:
            return edition

    return None


def get_default_price(edition: str) -> int:
    edition = normalize_edition(edition)

    if not edition:
        return 0

    return DEFAULT_PRICES.get(edition, 0)


def get_default_drop_rate(edition: str) -> float:
    edition = normalize_edition(edition)

    if not edition:
        return 0.0

    return DEFAULT_DROP_RATES.get(edition, 0.0)


# ============================================================
# CARD CREATION
# ============================================================

def create_card(
    char_id,
    name,
    edition="Common Edition",
    rarity=1,
    price=None,
    image_file_id="",
    video_file_id="",
    media_type="photo",
    description="",
    drop_weight=None,
    exp_reward=0,
):
    """
    Create a new card.

    Returns:
        True  -> successfully created
        False -> char_id already exists / invalid edition
    """

    char_id = str(char_id).strip()
    name = str(name).strip()

    if not char_id or not name:
        return False

    edition = normalize_edition(edition)

    if not edition:
        return False

    # Automatic defaults
    if price is None:
        price = get_default_price(edition)

    if drop_weight is None:
        drop_weight = get_default_drop_rate(edition)

    try:
        rarity = int(rarity)
    except (TypeError, ValueError):
        rarity = 1

    try:
        price = int(price)
    except (TypeError, ValueError):
        price = get_default_price(edition)

    try:
        drop_weight = float(drop_weight)
    except (TypeError, ValueError):
        drop_weight = get_default_drop_rate(edition)

    try:
        exp_reward = int(exp_reward)
    except (TypeError, ValueError):
        exp_reward = 0

    try:
        db_add_card(
            char_id=char_id,
            name=name,
            edition=edition,
            rarity=rarity,
            price=price,
            image_file_id=image_file_id or "",
            video_file_id=video_file_id or "",
            media_type=media_type or "photo",
            description=description or "",
            drop_weight=drop_weight,
            exp_reward=exp_reward,
        )

        return True

    except Exception:
        return False


# ============================================================
# CARD UPDATE
# ============================================================

def update_card(
    char_id,
    name=None,
    edition=None,
    rarity=None,
    price=None,
    image_file_id=None,
    video_file_id=None,
    media_type=None,
    description=None,
    drop_weight=None,
    exp_reward=None,
):
    """
    Update an existing card.

    Only supplied values are changed.
    """

    char_id = str(char_id).strip()

    if not char_id:
        return False

    existing = db_get_card(char_id)

    if not existing:
        return False

    fields = []
    values = []

    if name is not None:
        fields.append("name = ?")
        values.append(str(name).strip())

    if edition is not None:
        edition = normalize_edition(edition)

        if not edition:
            return False

        fields.append("edition = ?")
        values.append(edition)

    if rarity is not None:
        try:
            rarity = int(rarity)
        except (TypeError, ValueError):
            return False

        fields.append("rarity = ?")
        values.append(rarity)

    if price is not None:
        try:
            price = int(price)
        except (TypeError, ValueError):
            return False

        fields.append("price = ?")
        values.append(price)

    if image_file_id is not None:
        fields.append("image_file_id = ?")
        values.append(str(image_file_id))

    if video_file_id is not None:
        fields.append("video_file_id = ?")
        values.append(str(video_file_id))

    if media_type is not None:
        fields.append("media_type = ?")
        values.append(str(media_type))

    if description is not None:
        fields.append("description = ?")
        values.append(str(description))

    if drop_weight is not None:
        try:
            drop_weight = float(drop_weight)
        except (TypeError, ValueError):
            return False

        fields.append("drop_weight = ?")
        values.append(drop_weight)

    if exp_reward is not None:
        try:
            exp_reward = int(exp_reward)
        except (TypeError, ValueError):
            return False

        fields.append("exp_reward = ?")
        values.append(exp_reward)

    if not fields:
        return True

    values.append(char_id)

    with get_db() as db:
        db.execute(
            f"""
            UPDATE cards
            SET {", ".join(fields)}
            WHERE char_id = ?
            """,
            values,
        )

    return True


# ============================================================
# GET CARD
# ============================================================

def get_card(char_id):
    return db_get_card(char_id)


def get_all_cards():
    return db_get_all_cards()


def search_cards(keyword):
    if not keyword:
        return []

    return db_search_cards(str(keyword).strip())


# ============================================================
# DELETE CARD
# ============================================================

def delete_card(char_id):
    char_id = str(char_id).strip()

    if not char_id:
        return False

    card = db_get_card(char_id)

    if not card:
        return False

    db_delete_card(char_id)

    return True


# ============================================================
# PRICE
# ============================================================

def update_card_price(char_id, price):
    try:
        price = int(price)
    except (TypeError, ValueError):
        return False

    if price < 0:
        return False

    card = db_get_card(char_id)

    if not card:
        return False

    db_update_card_price(char_id, price)

    return True


# ============================================================
# DROP WEIGHT
# ============================================================

def update_card_drop_weight(char_id, drop_weight):
    char_id = str(char_id).strip()

    try:
        drop_weight = float(drop_weight)
    except (TypeError, ValueError):
        return False

    if drop_weight < 0:
        return False

    card = db_get_card(char_id)

    if not card:
        return False

    with get_db() as db:
        db.execute(
            """
            UPDATE cards
            SET drop_weight = ?
            WHERE char_id = ?
            """,
            (drop_weight, char_id),
        )

    return True


# ============================================================
# CARD MEDIA
# ============================================================

def attach_card_photo(char_id, file_id):
    char_id = str(char_id).strip()

    if not file_id:
        return False

    card = db_get_card(char_id)

    if not card:
        return False

    with get_db() as db:
        db.execute(
            """
            UPDATE cards
            SET image_file_id = ?,
                media_type = 'photo'
            WHERE char_id = ?
            """,
            (str(file_id), char_id),
        )

    return True


def attach_card_video(char_id, file_id):
    char_id = str(char_id).strip()

    if not file_id:
        return False

    card = db_get_card(char_id)

    if not card:
        return False

    with get_db() as db:
        db.execute(
            """
            UPDATE cards
            SET video_file_id = ?,
                media_type = 'video'
            WHERE char_id = ?
            """,
            (str(file_id), char_id),
        )

    return True


# ============================================================
# CARDS BY EDITION
# ============================================================

def get_cards_by_edition(edition):
    edition = normalize_edition(edition)

    if not edition:
        return []

    with get_db() as db:
        return db.execute(
            """
            SELECT *
            FROM cards
            WHERE active = 1
              AND edition = ?
            ORDER BY id ASC
            """,
            (edition,),
        ).fetchall()


# ============================================================
# WEIGHTED RANDOM CARD
# ============================================================

def choose_weighted_card(cards):
    """
    Weighted card selection.

    Supported card row format:
        SQLite Row
        tuple/list

    Expected:
        drop_weight at database column index 10
    """

    if not cards:
        return None

    valid_cards = []
    weights = []

    for card in cards:

        try:
            # SQLite Row supports key access.
            if hasattr(card, "keys"):
                rate = float(card["drop_weight"])
            else:
                # Original tuple format:
                # id, char_id, name, edition, rarity, price,
                # image_file_id, video_file_id, media_type,
                # description, drop_weight, exp_reward, ...
                rate = float(card[10])

        except (ValueError, TypeError, KeyError, IndexError):
            rate = 0.0

        if rate > 0:
            valid_cards.append(card)
            weights.append(rate)

    if not valid_cards:
        return random.choice(cards)

    return random.choices(
        valid_cards,
        weights=weights,
        k=1,
    )[0]


# ============================================================
# RANDOM CARD
# ============================================================

def choose_random_card():
    cards = get_all_cards()

    if not cards:
        return None

    return choose_weighted_card(cards)


# ============================================================
# RANDOM CARD BY EDITION
# ============================================================

def choose_random_card_by_edition(edition):
    cards = get_cards_by_edition(edition)

    if not cards:
        return None

    return choose_weighted_card(cards)


# ============================================================
# CARD COUNT
# ============================================================

def card_count():
    with get_db() as db:
        result = db.execute(
            """
            SELECT COUNT(*) AS total
            FROM cards
            WHERE active = 1
            """
        ).fetchone()

        return int(result["total"])


def edition_card_count(edition):
    edition = normalize_edition(edition)

    if not edition:
        return 0

    with get_db() as db:
        result = db.execute(
            """
            SELECT COUNT(*) AS total
            FROM cards
            WHERE active = 1
              AND edition = ?
            """,
            (edition,),
        ).fetchone()

        return int(result["total"])


# ============================================================
# CARD DISPLAY DATA
# ============================================================

def card_to_dict(card):
    """
    Convert SQLite Row / tuple into a normal dictionary.
    """

    if card is None:
        return None

    if hasattr(card, "keys"):
        return {
            key: card[key]
            for key in card.keys()
        }

    return {
        "id": card[0],
        "char_id": card[1],
        "name": card[2],
        "edition": card[3],
        "rarity": card[4],
        "price": card[5],
        "image_file_id": card[6],
        "video_file_id": card[7],
        "media_type": card[8],
        "description": card[9],
        "drop_weight": card[10],
        "exp_reward": card[11],
    }


# ============================================================
# VALIDATION
# ============================================================

def validate_card_data(
    char_id,
    name,
    edition,
    rarity=1,
    price=0,
    drop_weight=1,
):
    errors = []

    if not str(char_id).strip():
        errors.append("Card ID မရှိပါ။")

    if not str(name).strip():
        errors.append("Card Name မရှိပါ။")

    normalized = normalize_edition(edition)

    if not normalized:
        errors.append("Edition မမှန်ပါ။")

    try:
        rarity = int(rarity)

        if rarity < 1:
            errors.append("Rarity သည် 1 အောက်မဖြစ်ရပါ။")

    except (TypeError, ValueError):
        errors.append("Rarity မမှန်ပါ။")

    try:
        price = int(price)

        if price < 0:
            errors.append("Price သည် 0 အောက်မဖြစ်ရပါ။")

    except (TypeError, ValueError):
        errors.append("Price မမှန်ပါ။")

    try:
        drop_weight = float(drop_weight)

        if drop_weight < 0:
            errors.append("Drop Weight သည် 0 အောက်မဖြစ်ရပါ။")

    except (TypeError, ValueError):
        errors.append("Drop Weight မမှန်ပါ။")

    return errors
