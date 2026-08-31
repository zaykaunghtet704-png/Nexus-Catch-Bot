# claim_system.py
# Nexus Catch Bot
# First-click Card Claim System
#
# Features:
# - First-click winner
# - One claim per drop
# - 12-hour cooldown
# - Maximum 2 claimed cards per rolling 24 hours
# - Expired drops
# - Photo / Video media support
# - Thread-safe claim handling
# - Telegram InlineKeyboard-compatible button data
#
# NOTE:
# This module stores runtime state in memory.
# Persistent SQLite integration will be connected through database.py.

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from threading import RLock
from typing import Optional
import secrets


# ============================================================
# CONFIGURATION
# ============================================================

CLAIM_COOLDOWN_HOURS = 12
MAX_CLAIMS_24H = 2

DEFAULT_DROP_TIMEOUT_SECONDS = 60 * 60  # 1 hour


# ============================================================
# DATA CLASSES
# ============================================================

@dataclass
class ClaimRecord:
    user_id: int
    drop_id: str
    card_id: str
    claimed_at: datetime


@dataclass
class DropState:
    drop_id: str
    card_id: str

    # Optional card information
    card_name: str = ""
    edition: str = ""
    rarity: str = ""

    # Media
    media_type: Optional[str] = None
    media_id: Optional[str] = None

    # Drop owner/admin who created the drop
    created_by: Optional[int] = None

    # Group where the drop happened
    chat_id: Optional[int] = None

    # Drop status
    claimed: bool = False
    claimed_by: Optional[int] = None
    claimed_at: Optional[datetime] = None

    # Expiration
    created_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    expires_at: Optional[datetime] = None

    # Optional metadata
    metadata: dict = field(default_factory=dict)


# ============================================================
# STORAGE
# ============================================================

_DROPS: dict[str, DropState] = {}

_CLAIM_HISTORY: list[ClaimRecord] = []

_LOCK = RLock()


# ============================================================
# TIME HELPERS
# ============================================================

def utc_now() -> datetime:
    """Return timezone-aware UTC time."""
    return datetime.now(timezone.utc)


def normalize_datetime(value: datetime) -> datetime:
    """
    Convert a datetime to timezone-aware UTC.
    """
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)

    return value.astimezone(timezone.utc)


# ============================================================
# DROP ID
# ============================================================

def generate_drop_id() -> str:
    """
    Generate a short unique drop ID.
    """
    while True:
        drop_id = secrets.token_hex(6)

        with _LOCK:
            if drop_id not in _DROPS:
                return drop_id


# ============================================================
# CREATE DROP
# ============================================================

def create_drop(
    card_id: str,
    card_name: str = "",
    edition: str = "",
    rarity: str = "",
    media_type: Optional[str] = None,
    media_id: Optional[str] = None,
    created_by: Optional[int] = None,
    chat_id: Optional[int] = None,
    timeout_seconds: int = DEFAULT_DROP_TIMEOUT_SECONDS,
    metadata: Optional[dict] = None,
) -> DropState:
    """
    Create a new card drop.

    media_type:
        photo
        video
        animation
        None
    """

    if not card_id:
        raise ValueError("card_id is required")

    try:
        timeout_seconds = int(timeout_seconds)
    except (TypeError, ValueError):
        timeout_seconds = DEFAULT_DROP_TIMEOUT_SECONDS

    if timeout_seconds <= 0:
        timeout_seconds = DEFAULT_DROP_TIMEOUT_SECONDS

    now = utc_now()

    drop = DropState(
        drop_id=generate_drop_id(),
        card_id=str(card_id),
        card_name=card_name or "",
        edition=edition or "",
        rarity=rarity or "",
        media_type=media_type,
        media_id=media_id,
        created_by=created_by,
        chat_id=chat_id,
        created_at=now,
        expires_at=now + timedelta(
            seconds=timeout_seconds
        ),
        metadata=dict(metadata or {}),
    )

    with _LOCK:
        _DROPS[drop.drop_id] = drop

    return drop


# ============================================================
# DROP LOOKUP
# ============================================================

def get_drop(drop_id: str) -> Optional[DropState]:
    if not drop_id:
        return None

    with _LOCK:
        return _DROPS.get(str(drop_id))


def drop_exists(drop_id: str) -> bool:
    return get_drop(drop_id) is not None


# ============================================================
# EXPIRATION
# ============================================================

def is_drop_expired(drop: DropState) -> bool:
    if drop.expires_at is None:
        return False

    return utc_now() >= normalize_datetime(
        drop.expires_at
    )


def expire_drop(drop_id: str) -> bool:
    """
    Mark a drop as unavailable by removing it.

    Returns True when a drop existed.
    """

    with _LOCK:
        return _DROPS.pop(str(drop_id), None) is not None


# ============================================================
# CLAIM HISTORY
# ============================================================

def _recent_claims(
    user_id: int,
    hours: int = 24,
) -> list[ClaimRecord]:

    now = utc_now()
    cutoff = now - timedelta(hours=hours)

    with _LOCK:
        return [
            record
            for record in _CLAIM_HISTORY
            if record.user_id == int(user_id)
            and normalize_datetime(record.claimed_at) >= cutoff
        ]


def get_claim_count_24h(user_id: int) -> int:
    return len(
        _recent_claims(
            user_id=user_id,
            hours=24,
        )
    )


# ============================================================
# COOLDOWN
# ============================================================

def get_last_claim(user_id: int) -> Optional[ClaimRecord]:
    """
    Return user's latest claim.
    """

    uid = int(user_id)

    with _LOCK:
        records = [
            record
            for record in _CLAIM_HISTORY
            if record.user_id == uid
        ]

    if not records:
        return None

    return max(
        records,
        key=lambda record: normalize_datetime(
            record.claimed_at
        ),
    )


def get_cooldown_remaining(
    user_id: int,
    cooldown_hours: int = CLAIM_COOLDOWN_HOURS,
) -> timedelta:
    """
    Return remaining cooldown.

    Zero timedelta means no cooldown.
    """

    last_claim = get_last_claim(user_id)

    if last_claim is None:
        return timedelta(0)

    next_allowed = (
        normalize_datetime(last_claim.claimed_at)
        + timedelta(hours=cooldown_hours)
    )

    remaining = next_allowed - utc_now()

    if remaining.total_seconds() <= 0:
        return timedelta(0)

    return remaining


def is_on_cooldown(
    user_id: int,
    cooldown_hours: int = CLAIM_COOLDOWN_HOURS,
) -> bool:

    return (
        get_cooldown_remaining(
            user_id,
            cooldown_hours,
        ).total_seconds()
        > 0
    )


# ============================================================
# CLAIM LIMIT
# ============================================================

def has_claim_limit(
    user_id: int,
    max_claims: int = MAX_CLAIMS_24H,
) -> bool:

    return get_claim_count_24h(user_id) >= max_claims


def can_claim(
    user_id: int,
    cooldown_hours: int = CLAIM_COOLDOWN_HOURS,
    max_claims_24h: int = MAX_CLAIMS_24H,
) -> tuple[bool, str]:

    uid = int(user_id)

    cooldown = get_cooldown_remaining(
        uid,
        cooldown_hours,
    )

    if cooldown.total_seconds() > 0:
        return (
            False,
            format_cooldown(cooldown),
        )

    count = get_claim_count_24h(uid)

    if count >= max_claims_24h:
        return (
            False,
            (
                f"❌ You have reached the "
                f"{max_claims_24h}-card limit "
                f"for the last 24 hours."
            ),
        )

    return (
        True,
        "OK",
    )


# ============================================================
# FIRST CLICK CLAIM
# ============================================================

def claim_drop(
    drop_id: str,
    user_id: int,
    cooldown_hours: int = CLAIM_COOLDOWN_HOURS,
    max_claims_24h: int = MAX_CLAIMS_24H,
) -> tuple[bool, Optional[DropState], str]:

    """
    Atomically claim a drop.

    IMPORTANT:
    The lock guarantees that two simultaneous requests
    handled by this process cannot both win.

    Returns:
        (success, drop, message)
    """

    try:
        uid = int(user_id)
    except (TypeError, ValueError):
        return (
            False,
            None,
            "❌ Invalid user ID.",
        )

    if not drop_id:
        return (
            False,
            None,
            "❌ Invalid drop ID.",
        )

    with _LOCK:

        drop = _DROPS.get(str(drop_id))

        if drop is None:
            return (
                False,
                None,
                "❌ This card drop no longer exists.",
            )

        # ----------------------------------------------------
        # EXPIRED
        # ----------------------------------------------------

        if is_drop_expired(drop):
            del _DROPS[str(drop_id)]

            return (
                False,
                drop,
                "⏰ This card drop has expired.",
            )

        # ----------------------------------------------------
        # ALREADY CLAIMED
        # ----------------------------------------------------

        if drop.claimed:
            return (
                False,
                drop,
                "😢 Too late! Another user claimed this card first.",
            )

        # ----------------------------------------------------
        # USER COOLDOWN
        # ----------------------------------------------------

        cooldown = get_cooldown_remaining(
            uid,
            cooldown_hours,
        )

        if cooldown.total_seconds() > 0:
            return (
                False,
                drop,
                format_cooldown(cooldown),
            )

        # ----------------------------------------------------
        # 24-HOUR LIMIT
        # ----------------------------------------------------

        recent_count = len(
            [
                record
                for record in _CLAIM_HISTORY
                if (
                    record.user_id == uid
                    and normalize_datetime(
                        record.claimed_at
                    )
                    >= utc_now()
                    - timedelta(hours=24)
                )
            ]
        )

        if recent_count >= max_claims_24h:
            return (
                False,
                drop,
                (
                    f"❌ You already claimed "
                    f"{max_claims_24h} cards in the last 24 hours."
                ),
            )

        # ----------------------------------------------------
        # WINNER
        # ----------------------------------------------------

        now = utc_now()

        drop.claimed = True
        drop.claimed_by = uid
        drop.claimed_at = now

        _CLAIM_HISTORY.append(
            ClaimRecord(
                user_id=uid,
                drop_id=drop.drop_id,
                card_id=drop.card_id,
                claimed_at=now,
            )
        )

        # Remove from active drops.
        _DROPS.pop(str(drop_id), None)

        return (
            True,
            drop,
            "🎉 Card claimed successfully!",
        )


# ============================================================
# USER CLAIM HISTORY
# ============================================================

def get_user_claims(
    user_id: int,
) -> list[ClaimRecord]:

    uid = int(user_id)

    with _LOCK:
        records = [
            record
            for record in _CLAIM_HISTORY
            if record.user_id == uid
        ]

    return sorted(
        records,
        key=lambda record: normalize_datetime(
            record.claimed_at
        ),
        reverse=True,
    )


def get_all_claim_history() -> list[ClaimRecord]:
    with _LOCK:
        return list(_CLAIM_HISTORY)


# ============================================================
# BUTTON
# ============================================================

def get_claim_button(
    drop_id: str,
    text: str = "🎴 GET CARD",
) -> dict:

    return {
        "text": text,
        "callback_data": f"claim:{drop_id}",
    }


def get_claim_keyboard(
    drop_id: str,
) -> list[list[dict]]:

    return [
        [
            get_claim_button(
                drop_id=drop_id,
                text="🎴 GET CARD",
            )
        ]
    ]


# ============================================================
# DROP MESSAGE
# ============================================================

def build_drop_text(
    drop: DropState,
) -> str:

    name = drop.card_name or "Unknown Character"
    card_id = drop.card_id
    edition = drop.edition or "Unknown"
    rarity = drop.rarity or "Unknown"

    return (
        "✨ <b>NEW CARD DROP!</b> ✨\n\n"
        f"🎴 <b>{escape_html(name)}</b>\n"
        f"🆔 ID: <code>{escape_html(card_id)}</code>\n"
        f"💎 Edition: <b>{escape_html(edition)}</b>\n"
        f"⭐ Rarity: <b>{escape_html(rarity)}</b>\n\n"
        "⚡ <b>First click wins!</b>\n"
        "🏃 Be quick and press the button below!"
    )


# ============================================================
# MEDIA HELPERS
# ============================================================

def is_supported_media_type(
    media_type: Optional[str],
) -> bool:

    if media_type is None:
        return True

    return str(media_type).lower() in {
        "photo",
        "video",
        "animation",
    }


def get_media_payload(
    drop: DropState,
) -> Optional[dict]:

    if not drop.media_id:
        return None

    if not is_supported_media_type(
        drop.media_type
    ):
        return None

    return {
        "type": drop.media_type,
        "media": drop.media_id,
    }


# ============================================================
# FORMATTING
# ============================================================

def format_cooldown(
    remaining: timedelta,
) -> str:

    seconds = max(
        0,
        int(remaining.total_seconds()),
    )

    hours, remainder = divmod(
        seconds,
        3600,
    )

    minutes, seconds = divmod(
        remainder,
        60,
    )

    if hours:
        return (
            f"⏳ Cooldown active.\n"
            f"Try again in <b>{hours}h "
            f"{minutes}m</b>."
        )

    if minutes:
        return (
            f"⏳ Cooldown active.\n"
            f"Try again in <b>{minutes}m "
            f"{seconds}s</b>."
        )

    return (
        f"⏳ Cooldown active.\n"
        f"Try again in <b>{seconds}s</b>."
    )


def escape_html(value: str) -> str:

    return (
        str(value)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


# ============================================================
# CLEANUP
# ============================================================

def cleanup_expired_drops() -> int:
    """
    Remove expired active drops.

    Returns number removed.
    """

    removed = 0
    now = utc_now()

    with _LOCK:

        expired_ids = []

        for drop_id, drop in _DROPS.items():

            if drop.expires_at is None:
                continue

            if normalize_datetime(
                drop.expires_at
            ) <= now:
                expired_ids.append(drop_id)

        for drop_id in expired_ids:
            _DROPS.pop(drop_id, None)
            removed += 1

    return removed


# ============================================================
# ACTIVE DROPS
# ============================================================

def get_active_drops() -> list[DropState]:

    cleanup_expired_drops()

    with _LOCK:
        return list(_DROPS.values())


def get_active_drop_count() -> int:

    cleanup_expired_drops()

    with _LOCK:
        return len(_DROPS)


# ============================================================
# ADMIN CANCEL
# ============================================================

def cancel_drop(
    drop_id: str,
) -> bool:

    with _LOCK:
        return _DROPS.pop(
            str(drop_id),
            None,
        ) is not None


# ============================================================
# RESET
# ============================================================

def reset_claim_runtime() -> None:
    """
    Clear runtime state.

    This is intended for development/testing.
    """

    with _LOCK:
        _DROPS.clear()
        _CLAIM_HISTORY.clear()


# ============================================================
# STATISTICS
# ============================================================

def get_claim_statistics() -> dict:

    with _LOCK:

        return {
            "active_drops": len(_DROPS),
            "total_claims": len(_CLAIM_HISTORY),
            "unique_claimers": len(
                {
                    record.user_id
                    for record in _CLAIM_HISTORY
                }
            ),
        }


# ============================================================
# EXPORTS
# ============================================================

__all__ = [
    "CLAIM_COOLDOWN_HOURS",
    "MAX_CLAIMS_24H",
    "DEFAULT_DROP_TIMEOUT_SECONDS",

    "ClaimRecord",
    "DropState",

    "create_drop",
    "get_drop",
    "drop_exists",

    "is_drop_expired",
    "expire_drop",

    "get_claim_count_24h",
    "get_last_claim",
    "get_cooldown_remaining",
    "is_on_cooldown",

    "has_claim_limit",
    "can_claim",

    "claim_drop",

    "get_user_claims",
    "get_all_claim_history",

    "get_claim_button",
    "get_claim_keyboard",

    "build_drop_text",

    "is_supported_media_type",
    "get_media_payload",

    "format_cooldown",
    "escape_html",

    "cleanup_expired_drops",

    "get_active_drops",
    "get_active_drop_count",

    "cancel_drop",

    "reset_claim_runtime",
    "get_claim_statistics",
]
