# rendering.py
# ============================================================
# Nexus Catch Bot - Rendering / UI Helpers
# ============================================================

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable, Optional
import html
import math


# ============================================================
# CONSTANTS
# ============================================================

DEFAULT_PAGE_SIZE = 6
TOP_LIMIT = 15

RARITY_EMOJI = {
    "common": "⚪",
    "uncommon": "🟢",
    "rare": "🔵",
    "super rare": "🟣",
    "sr": "🟣",
    "epic": "🟠",
    "legendary": "🟡",
    "mythic": "🔴",
    "premium": "💎",
    "secret": "🌈",
}

EDITION_EMOJI = {
    "standard": "🎴",
    "bronze": "🥉",
    "silver": "🥈",
    "gold": "🥇",
    "premium": "💎",
    "limited": "🌟",
    "special": "✨",
}


# ============================================================
# DATA MODELS
# ============================================================

@dataclass
class CardView:
    card_id: str
    name: str

    rarity: str = "Common"
    edition: str = "Standard"

    atk: int = 0
    defense: int = 0
    hp: int = 0
    speed: int = 0

    element: str = ""
    card_class: str = ""

    description: str = ""

    image_url: Optional[str] = None
    video_url: Optional[str] = None

    premium: bool = False
    shiny: bool = False
    animated: bool = False
    limited: bool = False

    level: int = 1
    exp: int = 0

    owner_id: Optional[int] = None


@dataclass
class UserView:
    user_id: int
    name: str = "Unknown User"
    username: str = ""

    coins: int = 0
    level: int = 1
    exp: int = 0

    total_cards: int = 0
    unique_cards: int = 0

    rank: Optional[int] = None

    profile_photo: Optional[str] = None


@dataclass
class RankingView:
    rank: int
    user_id: int

    name: str = "Unknown User"

    total_cards: int = 0
    unique_cards: int = 0

    level: int = 1


# ============================================================
# SAFE HELPERS
# ============================================================

def safe_int(
    value: Any,
    default: int = 0,
) -> int:

    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def safe_float(
    value: Any,
    default: float = 0.0,
) -> float:

    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def clean_text(
    value: Any,
    default: str = "",
) -> str:

    if value is None:
        return default

    return html.escape(
        str(value)
    )


def normalize_key(
    value: Any,
) -> str:

    return str(
        value or ""
    ).strip().lower()


def rarity_emoji(
    rarity: str,
) -> str:

    key = normalize_key(
        rarity
    )

    return RARITY_EMOJI.get(
        key,
        "🎴",
    )


def edition_emoji(
    edition: str,
) -> str:

    key = normalize_key(
        edition
    )

    return EDITION_EMOJI.get(
        key,
        "🎴",
    )


# ============================================================
# OBJECT CONVERSION
# ============================================================

def _get(
    obj: Any,
    key: str,
    default: Any = None,
) -> Any:

    if obj is None:
        return default

    if isinstance(
        obj,
        dict,
    ):

        return obj.get(
            key,
            default,
        )

    return getattr(
        obj,
        key,
        default,
    )


def card_from_object(
    card: Any,
) -> CardView:

    if isinstance(
        card,
        CardView,
    ):
        return card

    return CardView(
        card_id=str(
            _get(
                card,
                "card_id",
                _get(
                    card,
                    "id",
                    "",
                ),
            )
        ),

        name=str(
            _get(
                card,
                "name",
                "Unknown Card",
            )
        ),

        rarity=str(
            _get(
                card,
                "rarity",
                "Common",
            )
        ),

        edition=str(
            _get(
                card,
                "edition",
                "Standard",
            )
        ),

        atk=safe_int(
            _get(
                card,
                "atk",
                _get(
                    card,
                    "attack",
                    0,
                ),
            )
        ),

        defense=safe_int(
            _get(
                card,
                "defense",
                _get(
                    card,
                    "def",
                    0,
                ),
            )
        ),

        hp=safe_int(
            _get(
                card,
                "hp",
                0,
            )
        ),

        speed=safe_int(
            _get(
                card,
                "speed",
                0,
            )
        ),

        element=str(
            _get(
                card,
                "element",
                "",
            )
        ),

        card_class=str(
            _get(
                card,
                "card_class",
                _get(
                    card,
                    "class_name",
                    "",
                ),
            )
        ),

        description=str(
            _get(
                card,
                "description",
                "",
            )
        ),

        image_url=_get(
            card,
            "image_url",
            _get(
                card,
                "image",
                None,
            ),
        ),

        video_url=_get(
            card,
            "video_url",
            _get(
                card,
                "video",
                None,
            ),
        ),

        premium=bool(
            _get(
                card,
                "premium",
                False,
            )
        ),

        shiny=bool(
            _get(
                card,
                "shiny",
                False,
            )
        ),

        animated=bool(
            _get(
                card,
                "animated",
                False,
            )
        ),

        limited=bool(
            _get(
                card,
                "limited",
                False,
            )
        ),

        level=max(
            1,
            safe_int(
                _get(
                    card,
                    "level",
                    1,
                ),
                1,
            ),
        ),

        exp=max(
            0,
            safe_int(
                _get(
                    card,
                    "exp",
                    0,
                )
            ),
        ),

        owner_id=_get(
            card,
            "owner_id",
            None,
        ),
    )


def user_from_object(
    user: Any,
) -> UserView:

    if isinstance(
        user,
        UserView,
    ):
        return user

    return UserView(
        user_id=safe_int(
            _get(
                user,
                "user_id",
                _get(
                    user,
                    "id",
                    0,
                ),
            )
        ),

        name=str(
            _get(
                user,
                "name",
                _get(
                    user,
                    "first_name",
                    "Unknown User",
                ),
            )
        ),

        username=str(
            _get(
                user,
                "username",
                "",
            )
        ),

        coins=safe_int(
            _get(
                user,
                "coins",
                0,
            )
        ),

        level=max(
            1,
            safe_int(
                _get(
                    user,
                    "level",
                    1,
                ),
                1,
            ),
        ),

        exp=max(
            0,
            safe_int(
                _get(
                    user,
                    "exp",
                    0,
                )
            ),
        ),

        total_cards=safe_int(
            _get(
                user,
                "total_cards",
                _get(
                    user,
                    "card_count",
                    0,
                ),
            )
        ),

        unique_cards=safe_int(
            _get(
                user,
                "unique_cards",
                0,
            )
        ),

        rank=_get(
            user,
            "rank",
            None,
        ),

        profile_photo=_get(
            user,
            "profile_photo",
            _get(
                user,
                "photo_url",
                None,
            ),
        ),
    )


def ranking_from_object(
    item: Any,
    rank: int,
) -> RankingView:

    if isinstance(
        item,
        RankingView,
    ):

        item.rank = rank
        return item

    return RankingView(
        rank=rank,

        user_id=safe_int(
            _get(
                item,
                "user_id",
                _get(
                    item,
                    "id",
                    0,
                ),
            )
        ),

        name=str(
            _get(
                item,
                "name",
                _get(
                    item,
                    "first_name",
                    "Unknown User",
                ),
            )
        ),

        total_cards=safe_int(
            _get(
                item,
                "total_cards",
                _get(
                    item,
                    "card_count",
                    0,
                ),
            )
        ),

        unique_cards=safe_int(
            _get(
                item,
                "unique_cards",
                0,
            )
        ),

        level=max(
            1,
            safe_int(
                _get(
                    item,
                    "level",
                    1,
                ),
                1,
            ),
        ),
    )


# ============================================================
# CARD BADGES
# ============================================================

def get_card_badges(
    card: Any,
) -> list[str]:

    card = card_from_object(
        card
    )

    badges = []

    if card.premium:
        badges.append(
            "💎 PREMIUM"
        )

    if card.shiny:
        badges.append(
            "✨ SHINY"
        )

    if card.animated:
        badges.append(
            "🎞️ ANIMATED"
        )

    if card.limited:
        badges.append(
            "🌟 LIMITED"
        )

    return badges


# ============================================================
# CARD TEXT
# ============================================================

def render_card(
    card: Any,
    *,
    language: str = "en",
    show_description: bool = True,
    show_stats: bool = True,
) -> str:

    card = card_from_object(
        card
    )

    rarity = rarity_emoji(
        card.rarity
    )

    edition = edition_emoji(
        card.edition
    )

    badges = get_card_badges(
        card
    )

    lines = [
        f"{edition} <b>{clean_text(card.name)}</b>",
        "",
        f"🆔 ID: <code>{clean_text(card.card_id)}</code>",
        (
            f"{rarity} Rarity: "
            f"<b>{clean_text(card.rarity)}</b>"
        ),
        (
            f"📚 Edition: "
            f"<b>{clean_text(card.edition)}</b>"
        ),
    ]

    if badges:

        lines.extend(
            [
                "",
                " ".join(
                    badges
                ),
            ]
        )

    if card.element:

        lines.append(
            f"🌈 Element: "
            f"<b>{clean_text(card.element)}</b>"
        )

    if card.card_class:

        lines.append(
            f"⚔️ Class: "
            f"<b>{clean_text(card.card_class)}</b>"
        )

    if show_stats:

        lines.extend(
            [
                "",
                "📊 <b>STATS</b>",
                (
                    f"⚔️ ATK: "
                    f"<b>{card.atk}</b>"
                ),
                (
                    f"🛡️ DEF: "
                    f"<b>{card.defense}</b>"
                ),
                (
                    f"❤️ HP: "
                    f"<b>{card.hp}</b>"
                ),
                (
                    f"💨 Speed: "
                    f"<b>{card.speed}</b>"
                ),
            ]
        )

    if card.level > 1 or card.exp > 0:

        lines.extend(
            [
                "",
                (
                    f"⭐ Level: "
                    f"<b>{card.level}</b>"
                ),
                (
                    f"✨ EXP: "
                    f"<b>{card.exp}</b>"
                ),
            ]
        )

    if (
        show_description
        and card.description
    ):

        lines.extend(
            [
                "",
                "📝 <b>Description</b>",
                clean_text(
                    card.description
                ),
            ]
        )

    if language.lower().startswith(
        "my"
    ):

        # Keep the card data itself
        # language-neutral.
        pass

    return "\n".join(
        lines
    )


# ============================================================
# CARD SHORT VIEW
# ============================================================

def render_card_short(
    card: Any,
    quantity: int = 1,
) -> str:

    card = card_from_object(
        card
    )

    return (
        f"{rarity_emoji(card.rarity)} "
        f"<b>{clean_text(card.name)}</b> "
        f"<code>#{clean_text(card.card_id)}</code>"
        f" ×{max(1, safe_int(quantity, 1))}"
    )


# ============================================================
# HAREM
# ============================================================

def normalize_collection(
    cards: Iterable[Any],
) -> list[tuple[CardView, int]]:

    result = []

    if cards is None:
        return result

    if isinstance(
        cards,
        dict,
    ):

        for card, quantity in cards.items():

            result.append(
                (
                    card_from_object(card),
                    max(
                        1,
                        safe_int(
                            quantity,
                            1,
                        ),
                    ),
                )
            )

        return result

    for item in cards:

        if isinstance(
            item,
            tuple,
        ) and len(item) >= 2:

            result.append(
                (
                    card_from_object(
                        item[0]
                    ),
                    max(
                        1,
                        safe_int(
                            item[1],
                            1,
                        ),
                    ),
                )
            )

        else:

            result.append(
                (
                    card_from_object(
                        item
                    ),
                    1,
                )
            )

    return result


def filter_harem(
    collection: Iterable[Any],
    *,
    rarity: Optional[str] = None,
    edition: Optional[str] = None,
    search: Optional[str] = None,
) -> list[tuple[CardView, int]]:

    cards = normalize_collection(
        collection
    )

    rarity_key = (
        normalize_key(rarity)
        if rarity
        else None
    )

    edition_key = (
        normalize_key(edition)
        if edition
        else None
    )

    search_key = (
        normalize_key(search)
        if search
        else None
    )

    result = []

    for card, quantity in cards:

        if (
            rarity_key
            and normalize_key(
                card.rarity
            ) != rarity_key
        ):
            continue

        if (
            edition_key
            and normalize_key(
                card.edition
            ) != edition_key
        ):
            continue

        if search_key:

            haystack = " ".join(
                [
                    card.name,
                    card.card_id,
                    card.rarity,
                    card.edition,
                    card.element,
                    card.card_class,
                ]
            ).lower()

            if search_key not in haystack:
                continue

        result.append(
            (
                card,
                quantity,
            )
        )

    return result


def sort_harem(
    collection: Iterable[Any],
    mode: str = "id",
) -> list[tuple[CardView, int]]:

    cards = normalize_collection(
        collection
    )

    mode = normalize_key(
        mode
    )

    if mode == "rarity":

        return sorted(
            cards,
            key=lambda item: (
                normalize_key(
                    item[0].rarity
                ),
                item[0].card_id,
            ),
        )

    if mode == "name":

        return sorted(
            cards,
            key=lambda item: (
                normalize_key(
                    item[0].name
                ),
                item[0].card_id,
            ),
        )

    if mode == "level":

        return sorted(
            cards,
            key=lambda item: (
                -item[0].level,
                item[0].card_id,
            ),
        )

    return sorted(
        cards,
        key=lambda item: item[0].card_id
    )


def render_harem_page(
    collection: Iterable[Any],
    *,
    page: int = 1,
    page_size: int = DEFAULT_PAGE_SIZE,
    mode: str = "id",
    title: str = "YOUR HAREM",
) -> tuple[str, int, int]:

    page_size = max(
        1,
        safe_int(
            page_size,
            DEFAULT_PAGE_SIZE,
        ),
    )

    cards = sort_harem(
        collection,
        mode=mode,
    )

    total = len(
        cards
    )

    total_pages = max(
        1,
        math.ceil(
            total / page_size
        ),
    )

    page = max(
        1,
        min(
            safe_int(page, 1),
            total_pages,
        ),
    )

    start = (
        page - 1
    ) * page_size

    end = (
        start + page_size
    )

    current = cards[
        start:end
    ]

    lines = [
        f"🃏 <b>{clean_text(title)}</b>",
        "",
        (
            f"📦 Total Unique: "
            f"<b>{total}</b>"
        ),
    ]

    if not current:

        lines.extend(
            [
                "",
                "📭 No cards found.",
            ]
        )

    else:

        lines.append("")

        for index, (
            card,
            quantity,
        ) in enumerate(
            current,
            start=start + 1,
        ):

            lines.append(
                f"<b>{index}.</b> "
                f"{render_card_short(card, quantity)}"
            )

    lines.extend(
        [
            "",
            (
                f"📄 Page "
                f"<b>{page}/{total_pages}</b>"
            ),
        ]
    )

    return (
        "\n".join(lines),
        page,
        total_pages,
    )


# ============================================================
# HMODE
# ============================================================

def render_hmode(
    collection: Iterable[Any],
    *,
    title: str = "SELECT HAREM MODE",
) -> str:

    cards = normalize_collection(
        collection
    )

    cards = sorted(
        cards,
        key=lambda item: (
            -item[0].level,
            -item[0].atk,
            -item[0].hp,
        ),
    )

    cards = cards[:10]

    lines = [
        f"🎛️ <b>{clean_text(title)}</b>",
        "",
        "Choose one of the 10 modes:",
        "",
    ]

    modes = [
        (
            "id",
            "🆔 Card ID",
        ),
        (
            "name",
            "🔤 Name",
        ),
        (
            "rarity",
            "💎 Rarity",
        ),
        (
            "edition",
            "📚 Edition",
        ),
        (
            "level",
            "⭐ Level",
        ),
        (
            "atk",
            "⚔️ ATK",
        ),
        (
            "def",
            "🛡️ DEF",
        ),
        (
            "hp",
            "❤️ HP",
        ),
        (
            "speed",
            "💨 Speed",
        ),
        (
            "recent",
            "🆕 Recent",
        ),
    ]

    for index, (
        mode_id,
        label,
    ) in enumerate(
        modes,
        start=1,
    ):

        lines.append(
            f"{index}. {label} "
            f"<code>{mode_id}</code>"
        )

    return "\n".join(
        lines
    )


# ============================================================
# SEARCH
# ============================================================

def search_cards(
    cards: Iterable[Any],
    query: str,
) -> list[CardView]:

    query = normalize_key(
        query
    )

    if not query:
        return []

    result = []

    for item in cards:

        card = card_from_object(
            item
        )

        searchable = " ".join(
            [
                card.card_id,
                card.name,
                card.rarity,
                card.edition,
                card.element,
                card.card_class,
                card.description,
            ]
        ).lower()

        if query in searchable:

            result.append(
                card
            )

    return result


def render_search_page(
    cards: Iterable[Any],
    query: str,
    *,
    page: int = 1,
    page_size: int = DEFAULT_PAGE_SIZE,
) -> tuple[str, int, int]:

    results = search_cards(
        cards,
        query,
    )

    total = len(
        results
    )

    page_size = max(
        1,
        safe_int(
            page_size,
            DEFAULT_PAGE_SIZE,
        ),
    )

    total_pages = max(
        1,
        math.ceil(
            total / page_size
        ),
    )

    page = max(
        1,
        min(
            safe_int(page, 1),
            total_pages,
        ),
    )

    start = (
        page - 1
    ) * page_size

    current = results[
        start:start + page_size
    ]

    lines = [
        "🔎 <b>CARD SEARCH</b>",
        "",
        (
            f"Query: "
            f"<code>{clean_text(query)}</code>"
        ),
        (
            f"Results: "
            f"<b>{total}</b>"
        ),
        "",
    ]

    if not current:

        lines.append(
            "❌ No cards found."
        )

    else:

        for index, card in enumerate(
            current,
            start=start + 1,
        ):

            lines.append(
                f"<b>{index}.</b> "
                f"{rarity_emoji(card.rarity)} "
                f"<b>{clean_text(card.name)}</b> "
                f"<code>{clean_text(card.card_id)}</code>"
            )

    lines.extend(
        [
            "",
            (
                f"📄 Page "
                f"<b>{page}/{total_pages}</b>"
            ),
        ]
    )

    return (
        "\n".join(lines),
        page,
        total_pages,
    )


# ============================================================
# PROFILE
# ============================================================

def render_profile(
    user: Any,
    *,
    language: str = "en",
) -> str:

    user = user_from_object(
        user
    )

    rank_text = (
        f"#{user.rank}"
        if user.rank is not None
        else "N/A"
    )

    username = (
        f"@{clean_text(user.username)}"
        if user.username
        else "Not set"
    )

    if language.lower().startswith(
        "my"
    ):

        return (
            "👤 <b>USER PROFILE</b>\n\n"
            f"🪪 Name: <b>{clean_text(user.name)}</b>\n"
            f"🔗 Username: {username}\n"
            f"🆔 ID: <code>{user.user_id}</code>\n\n"
            f"🪙 Coins: <b>{user.coins:,}</b>\n"
            f"⭐ Level: <b>{user.level}</b>\n"
            f"✨ EXP: <b>{user.exp:,}</b>\n\n"
            f"🎴 Total Cards: <b>{user.total_cards:,}</b>\n"
            f"📚 Unique Cards: <b>{user.unique_cards:,}</b>\n"
            f"🏆 Global Rank: <b>{rank_text}</b>"
        )

    return (
        "👤 <b>USER PROFILE</b>\n\n"
        f"🪪 Name: <b>{clean_text(user.name)}</b>\n"
        f"🔗 Username: {username}\n"
        f"🆔 ID: <code>{user.user_id}</code>\n\n"
        f"🪙 Coins: <b>{user.coins:,}</b>\n"
        f"⭐ Level: <b>{user.level}</b>\n"
        f"✨ EXP: <b>{user.exp:,}</b>\n\n"
        f"🎴 Total Cards: <b>{user.total_cards:,}</b>\n"
        f"📚 Unique Cards: <b>{user.unique_cards:,}</b>\n"
        f"🏆 Global Rank: <b>{rank_text}</b>"
    )


# ============================================================
# GLOBAL TOP
# ============================================================

def sort_rankings(
    users: Iterable[Any],
) -> list[RankingView]:

    converted = []

    for user in users:

        converted.append(
            ranking_from_object(
                user,
                0,
            )
        )

    converted.sort(
        key=lambda user: (
            -user.total_cards,
            -user.unique_cards,
            -user.level,
            user.user_id,
        )
    )

    for index, user in enumerate(
        converted,
        start=1,
    ):

        user.rank = index

    return converted


def render_top(
    users: Iterable[Any],
    *,
    limit: int = TOP_LIMIT,
    title: str = "GLOBAL TOP 15",
) -> str:

    limit = max(
        1,
        safe_int(
            limit,
            TOP_LIMIT,
        ),
    )

    rankings = sort_rankings(
        users
    )[:limit]

    lines = [
        f"🏆 <b>{clean_text(title)}</b>",
        "",
    ]

    if not rankings:

        lines.append(
            "📭 No ranking data yet."
        )

        return "\n".join(
            lines
        )

    medals = {
        1: "🥇",
        2: "🥈",
        3: "🥉",
    }

    for user in rankings:

        prefix = medals.get(
            user.rank,
            f"{user.rank}.",
        )

        lines.append(
            f"{prefix} "
            f"<b>{clean_text(user.name)}</b>\n"
            f"   🎴 {user.total_cards:,} cards "
            f"• 📚 {user.unique_cards:,} unique "
            f"• ⭐ Lv.{user.level}"
        )

    lines.extend(
        [
            "",
            "🌍 Global Ranking",
        ]
    )

    return "\n".join(
        lines
    )


# ============================================================
# GROUP TOP
# ============================================================

def render_ctop(
    users: Iterable[Any],
    *,
    limit: int = TOP_LIMIT,
    group_name: str = "GROUP",
) -> str:

    rankings = sort_rankings(
        users
    )[:max(
        1,
        safe_int(
            limit,
            TOP_LIMIT,
        ),
    )]

    lines = [
        "👥 <b>GROUP TOP</b>",
        "",
        (
            f"🏠 Group: "
            f"<b>{clean_text(group_name)}</b>"
        ),
        "",
    ]

    if not rankings:

        lines.append(
            "📭 No ranking data yet."
        )

        return "\n".join(
            lines
        )

    medals = {
        1: "🥇",
        2: "🥈",
        3: "🥉",
    }

    for user in rankings:

        prefix = medals.get(
            user.rank,
            f"{user.rank}.",
        )

        lines.append(
            f"{prefix} "
            f"<b>{clean_text(user.name)}</b> "
            f"— 🎴 <b>{user.total_cards:,}</b>"
        )

    return "\n".join(
        lines
    )


# ============================================================
# RANKINGS
# ============================================================

def render_rankings(
    users: Iterable[Any],
) -> str:

    return render_top(
        users,
        limit=TOP_LIMIT,
        title="RANKINGS",
    )


# ============================================================
# DAILY / BALANCE
# ============================================================

def render_balance(
    user: Any,
) -> str:

    user = user_from_object(
        user
    )

    return (
        "💰 <b>YOUR BALANCE</b>\n\n"
        f"👤 {clean_text(user.name)}\n"
        f"🪙 Coins: <b>{user.coins:,}</b>"
    )


def render_daily(
    amount: int = 500,
) -> str:

    amount = max(
        0,
        safe_int(
            amount,
            500,
        ),
    )

    return (
        "🎁 <b>DAILY REWARD</b>\n\n"
        f"🪙 You received "
        f"<b>{amount:,} Coins</b>!\n\n"
        "⏰ Come back tomorrow for another reward."
    )


# ============================================================
# SELL PRICE
# ============================================================

def render_sell_price(
    card: Any,
    price: int,
) -> str:

    card = card_from_object(
        card
    )

    price = max(
        0,
        safe_int(
            price
        ),
    )

    return (
        "💰 <b>CARD SELL PRICE</b>\n\n"
        f"🎴 {clean_text(card.name)}\n"
        f"🆔 <code>{clean_text(card.card_id)}</code>\n"
        f"{rarity_emoji(card.rarity)} "
        f"{clean_text(card.rarity)}\n"
        f"📚 {clean_text(card.edition)}\n\n"
        f"🪙 Price: <b>{price:,} Coins</b>"
    )


# ============================================================
# MARKET
# ============================================================

def render_market_listing(
    card: Any,
    listing_id: Any,
    price: int,
    seller_name: str = "",
) -> str:

    card = card_from_object(
        card
    )

    seller = (
        clean_text(seller_name)
        if seller_name
        else "Unknown Seller"
    )

    return (
        f"🎴 <b>{clean_text(card.name)}</b>\n"
        f"🆔 Card ID: "
        f"<code>{clean_text(card.card_id)}</code>\n"
        f"📋 Listing ID: "
        f"<code>{clean_text(listing_id)}</code>\n"
        f"{rarity_emoji(card.rarity)} "
        f"{clean_text(card.rarity)}\n"
        f"🪙 Price: <b>{max(0, safe_int(price)):,}</b>\n"
        f"👤 Seller: <b>{seller}</b>"
    )


def render_market_page(
    listings: Iterable[Any],
    *,
    page: int = 1,
    page_size: int = DEFAULT_PAGE_SIZE,
) -> tuple[str, int, int]:

    items = list(
        listings or []
    )

    page_size = max(
        1,
        safe_int(
            page_size,
            DEFAULT_PAGE_SIZE,
        ),
    )

    total = len(
        items
    )

    total_pages = max(
        1,
        math.ceil(
            total / page_size
        ),
    )

    page = max(
        1,
        min(
            safe_int(page, 1),
            total_pages,
        ),
    )

    start = (
        page - 1
    ) * page_size

    current = items[
        start:start + page_size
    ]

    lines = [
        "🏪 <b>MARKET</b>",
        "",
    ]

    if not current:

        lines.append(
            "📭 Market is empty."
        )

    else:

        for index, listing in enumerate(
            current,
            start=start + 1,
        ):

            card = _get(
                listing,
                "card",
                listing,
            )

            card = card_from_object(
                card
            )

            listing_id = _get(
                listing,
                "listing_id",
                _get(
                    listing,
                    "id",
                    index,
                ),
            )

            price = safe_int(
                _get(
                    listing,
                    "price",
                    0,
                )
            )

            seller = str(
                _get(
                    listing,
                    "seller_name",
                    _get(
                        listing,
                        "seller",
                        "",
                    ),
                )
            )

            lines.extend(
                [
                    (
                        f"<b>{index}.</b> "
                        f"{rarity_emoji(card.rarity)} "
                        f"<b>{clean_text(card.name)}</b>"
                    ),
                    (
                        f"   🆔 "
                        f"<code>{clean_text(card.card_id)}</code> "
                        f"| 📋 "
                        f"<code>{clean_text(listing_id)}</code>"
                    ),
                    (
                        f"   🪙 <b>{price:,}</b> Coins "
                        f"| 👤 {clean_text(seller)}"
                    ),
                    "",
                ]
            )

    lines.append(
        f"📄 Page <b>{page}/{total_pages}</b>"
    )

    return (
        "\n".join(lines),
        page,
        total_pages,
    )


# ============================================================
# DROP MESSAGE
# ============================================================

def render_drop(
    card: Any,
    *,
    better: bool = False,
) -> str:

    card = card_from_object(
        card
    )

    heading = (
        "💎 <b>BETTER CARD DROP!</b>"
        if better
        else "🎴 <b>NEW CARD DROP!</b>"
    )

    badges = get_card_badges(
        card
    )

    lines = [
        heading,
        "",
        f"✨ <b>{clean_text(card.name)}</b>",
        (
            f"🆔 ID: "
            f"<code>{clean_text(card.card_id)}</code>"
        ),
        (
            f"{rarity_emoji(card.rarity)} "
            f"Rarity: <b>{clean_text(card.rarity)}</b>"
        ),
        (
            f"{edition_emoji(card.edition)} "
            f"Edition: <b>{clean_text(card.edition)}</b>"
        ),
    ]

    if badges:

        lines.extend(
            [
                "",
                " ".join(
                    badges
                ),
            ]
        )

    lines.extend(
        [
            "",
            "⚡ <b>First click gets the card!</b>",
        ]
    )

    return "\n".join(
        lines
    )


# ============================================================
# CLAIM
# ============================================================

def render_claim_success(
    card: Any,
    user_name: str,
) -> str:

    card = card_from_object(
        card
    )

    return (
        "🎉 <b>CARD CLAIMED!</b>\n\n"
        f"👤 <b>{clean_text(user_name)}</b>\n"
        f"🎴 {clean_text(card.name)}\n"
        f"🆔 <code>{clean_text(card.card_id)}</code>\n"
        f"{rarity_emoji(card.rarity)} "
        f"{clean_text(card.rarity)}\n\n"
        "✅ The card has been added to your harem!"
    )


def render_claim_failed(
    reason: str = "already_claimed",
) -> str:

    reason = normalize_key(
        reason
    )

    if reason == "cooldown":

        return (
            "⏳ <b>CLAIM COOLDOWN</b>\n\n"
            "You are still on cooldown."
        )

    if reason == "limit":

        return (
            "🚫 <b>DAILY CLAIM LIMIT</b>\n\n"
            "You have reached today's claim limit."
        )

    if reason == "already_claimed":

        return (
            "❌ <b>TOO LATE!</b>\n\n"
            "Another user claimed this card first."
        )

    return (
        "❌ <b>CLAIM FAILED</b>\n\n"
        "This card cannot be claimed."
    )


# ============================================================
# DUEL
# ============================================================

def render_duel_start(
    user1: Any,
    user2: Any,
) -> str:

    u1 = user_from_object(
        user1
    )

    u2 = user_from_object(
        user2
    )

    return (
        "⚔️ <b>CARD DUEL</b>\n\n"
        f"👤 <b>{clean_text(u1.name)}</b>\n"
        f"⭐ Level {u1.level}\n\n"
        "        VS\n\n"
        f"👤 <b>{clean_text(u2.name)}</b>\n"
        f"⭐ Level {u2.level}\n\n"
        "🔥 The battle begins!"
    )


def render_duel_result(
    winner_name: str,
    loser_name: str,
    coins: int,
    exp: int,
) -> str:

    return (
        "🏆 <b>DUEL RESULT</b>\n\n"
        f"🥇 Winner: "
        f"<b>{clean_text(winner_name)}</b>\n"
        f"💥 Defeated: "
        f"<b>{clean_text(loser_name)}</b>\n\n"
        f"🪙 Coins Won: <b>{max(0, safe_int(coins)):,}</b>\n"
        f"✨ EXP Won: <b>{max(0, safe_int(exp)):,}</b>"
    )


# ============================================================
# TRADE / GIFT
# ============================================================

def render_gift(
    sender_name: str,
    receiver_name: str,
    card: Any,
    quantity: int = 1,
) -> str:

    card = card_from_object(
        card
    )

    quantity = max(
        1,
        safe_int(
            quantity,
            1,
        ),
    )

    return (
        "🎁 <b>CARD GIFT</b>\n\n"
        f"👤 From: <b>{clean_text(sender_name)}</b>\n"
        f"👤 To: <b>{clean_text(receiver_name)}</b>\n\n"
        f"🎴 <b>{clean_text(card.name)}</b>\n"
        f"🆔 <code>{clean_text(card.card_id)}</code>\n"
        f"📦 Quantity: <b>{quantity}</b>"
    )


def render_trade(
    user1_name: str,
    user2_name: str,
    card1: Any,
    card2: Any,
) -> str:

    c1 = card_from_object(
        card1
    )

    c2 = card_from_object(
        card2
    )

    return (
        "🔄 <b>CARD TRADE</b>\n\n"
        f"👤 <b>{clean_text(user1_name)}</b>\n"
        f"🎴 {clean_text(c1.name)} "
        f"<code>{clean_text(c1.card_id)}</code>\n\n"
        "        ⇅\n\n"
        f"👤 <b>{clean_text(user2_name)}</b>\n"
        f"🎴 {clean_text(c2.name)} "
        f"<code>{clean_text(c2.card_id)}</code>"
    )


# ============================================================
# FAVORITE
# ============================================================

def render_favorite(
    card: Any,
    added: bool = True,
) -> str:

    card = card_from_object(
        card
    )

    if added:

        return (
            "❤️ <b>FAVORITE ADDED</b>\n\n"
            f"🎴 {clean_text(card.name)}\n"
            f"🆔 <code>{clean_text(card.card_id)}</code>"
        )

    return (
        "💔 <b>FAVORITE REMOVED</b>\n\n"
        f"🎴 {clean_text(card.name)}\n"
        f"🆔 <code>{clean_text(card.card_id)}</code>"
    )


# ============================================================
# UPGRADE
# ============================================================

def render_upgrade(
    card: Any,
    old_level: int,
    new_level: int,
) -> str:

    card = card_from_object(
        card
    )

    return (
        "⬆️ <b>CARD UPGRADED!</b>\n\n"
        f"🎴 <b>{clean_text(card.name)}</b>\n"
        f"🆔 <code>{clean_text(card.card_id)}</code>\n\n"
        f"⭐ Level: "
        f"<b>{max(1, safe_int(old_level, 1))}</b>"
        f" → "
        f"<b>{max(1, safe_int(new_level, 1))}</b>\n\n"
        "🔥 Your card became stronger!"
    )


# ============================================================
# PAGINATION
# ============================================================

def pagination_data(
    page: int,
    total_pages: int,
) -> dict[str, bool]:

    page = max(
        1,
        safe_int(
            page,
            1,
        ),
    )

    total_pages = max(
        1,
        safe_int(
            total_pages,
            1,
        ),
    )

    return {
        "has_previous": page > 1,
        "has_next": page < total_pages,
        "is_first": page == 1,
        "is_last": page == total_pages,
    }


def make_pagination_buttons(
    page: int,
    total_pages: int,
    prefix: str,
) -> list[list[dict[str, str]]]:

    page = max(
        1,
        safe_int(
            page,
            1,
        ),
    )

    total_pages = max(
        1,
        safe_int(
            total_pages,
            1,
        ),
    )

    buttons = []

    if page > 1:

        buttons.append(
            {
                "text": "⬅️",
                "callback_data": (
                    f"{prefix}:page:{page - 1}"
                ),
            }
        )

    buttons.append(
        {
            "text": (
                f"📄 {page}/{total_pages}"
            ),
            "callback_data": (
                f"{prefix}:current:{page}"
            ),
        }
    )

    if page < total_pages:

        buttons.append(
            {
                "text": "➡️",
                "callback_data": (
                    f"{prefix}:page:{page + 1}"
                ),
            }
        )

    return [
        buttons
    ]


# ============================================================
# START MESSAGE
# ============================================================

def render_start(
    user_name: str = "",
    *,
    language: str = "en",
) -> str:

    name = (
        clean_text(
            user_name
        )
        if user_name
        else "Player"
    )

    if language.lower().startswith(
        "my"
    ):

        return (
            "🎴 <b>NEXUS CATCH</b>\n\n"
            f"မင်္ဂလာပါ <b>{name}</b> 👋\n\n"
            "Anime Card Collection Bot မှာ "
            "Card တွေကို စုဆောင်းပြီး "
            "Level / EXP / Coin / Ranking "
            "စနစ်တွေနဲ့ ကစားနိုင်ပါတယ်။\n\n"
            "📖 အသုံးပြုနည်းကို သိချင်ရင် "
            "<b>/help</b> ကိုနှိပ်ပါ။"
        )

    return (
        "🎴 <b>NEXUS CATCH</b>\n\n"
        f"Welcome <b>{name}</b> 👋\n\n"
        "Collect anime cards, level them up, "
        "earn Coins and compete on the "
        "global rankings.\n\n"
        "📖 Use <b>/help</b> to learn how "
        "everything works."
    )


# ============================================================
# HELP
# ============================================================

def render_help_page(
    page: int = 1,
    language: str = "en",
) -> tuple[str, int]:

    pages = []

    if language.lower().startswith(
        "my"
    ):

        pages = [
            (
                "📖 <b>HELP • PAGE 1</b>\n\n"
                "🎴 <b>Card Collection</b>\n\n"
                "/harem — ကိုယ်ပိုင် Card Collection\n"
                "/search — Card ရှာရန်\n"
                "/check [id] — Card အသေးစိတ်\n"
                "/Nexus [Card_Name] — Card ရယူရန်\n"
                "/fav [id] — Favorite ထားရန်\n"
                "/unfav [id] — Favorite ဖြုတ်ရန်"
            ),
            (
                "📖 <b>HELP • PAGE 2</b>\n\n"
                "💰 <b>Economy</b>\n\n"
                "/daily — 500 Coins ရယူရန်\n"
                "/balance — Coin လက်ကျန်ကြည့်ရန်\n"
                "/sellprice — Card စျေးကြည့်ရန်\n"
                "/market — Market ကြည့်ရန်\n"
                "/sell [id] [price] — Card ရောင်းရန်\n"
                "/buy [listing_id] — Card ဝယ်ရန်\n"
                "/delist [listing_id] — Listing ဖြုတ်ရန်"
            ),
            (
                "📖 <b>HELP • PAGE 3</b>\n\n"
                "⚔️ <b>Social / Battle</b>\n\n"
                "/gift [char_id] — Card လက်ဆောင်ပေးရန်\n"
                "/trade — Card Trade\n"
                "/duel — Card Battle\n"
                "/upgrade — Card Level Up\n"
                "/hmode — Harem Mode ရွေးရန်"
            ),
            (
                "📖 <b>HELP • PAGE 4</b>\n\n"
                "🏆 <b>Rankings</b>\n\n"
                "/profile — Profile ကြည့်ရန်\n"
                "/top — Global Top 15\n"
                "/ctop — Group Top\n"
                "/rankings — Ranking ကြည့်ရန်\n"
                "/todayNexusCatch — ဒီနေ့ Card Catch Top\n"
                "/reset — Harem View Reset"
            ),
            (
                "📖 <b>HELP • PAGE 5</b>\n\n"
                "🎁 <b>Claim System</b>\n\n"
                "/claim — Claim ပြုလုပ်ရန်\n\n"
                "⏰ Claim Cooldown: 12 Hours\n"
                "🎴 24 Hours အတွင်း အများဆုံး 2 Cards\n\n"
                "⚡ Drop ပေါ်လာတဲ့အခါ "
                "ပထမဆုံး Claim လုပ်သူက Card ရပါမယ်။"
            ),
        ]

    else:

        pages = [
            (
                "📖 <b>HELP • PAGE 1</b>\n\n"
                "🎴 <b>Card Collection</b>\n\n"
                "/harem — Your card collection\n"
                "/search — Search cards\n"
                "/check [id] — Card details\n"
                "/Nexus [Card_Name] — Get a card\n"
                "/fav [id] — Add favorite\n"
                "/unfav [id]
