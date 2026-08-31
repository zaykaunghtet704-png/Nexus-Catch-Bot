# trade_system.py
# Nexus Catch Bot
# Gift + Trade System
#
# This module is the transaction layer.
# It is intentionally independent from Telegram handlers.
# The bot.py layer will connect these functions to commands/buttons.

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from threading import RLock
from typing import Optional


# ============================================================
# CONFIG
# ============================================================

MAX_TRADE_CARDS = 1
MAX_GIFT_QUANTITY = 1

# By default, a card marked Favorite cannot be gifted/traded.
# This prevents accidental transfers.
PROTECT_FAVORITE = True


# ============================================================
# DATA
# ============================================================

@dataclass
class TransactionResult:
    success: bool
    message: str

    sender_id: Optional[int] = None
    receiver_id: Optional[int] = None

    sender_card_id: Optional[str] = None
    receiver_card_id: Optional[str] = None

    sender_quantity: int = 0
    receiver_quantity: int = 0

    created_at: datetime = None


# ============================================================
# STORAGE
# ============================================================

_TRANSACTION_HISTORY: list[TransactionResult] = []

_LOCK = RLock()


# ============================================================
# HELPERS
# ============================================================

def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def normalize_user_id(user_id) -> int:
    try:
        return int(user_id)
    except (TypeError, ValueError):
        raise ValueError("Invalid user ID.")


def normalize_card_id(card_id) -> str:
    if card_id is None:
        raise ValueError("Card ID is required.")

    value = str(card_id).strip()

    if not value:
        raise ValueError("Card ID is required.")

    if value.isdigit():
        return value.zfill(4)

    return value


# ============================================================
# OPTIONAL CARD-MANAGER INTEGRATION
# ============================================================

def _get_card_manager():
    """
    Load card_manager lazily.

    Lazy import prevents this module from crashing during
    startup when card_manager is temporarily unavailable.
    """

    try:
        import card_manager
        return card_manager
    except ImportError:
        return None


def _get_user_card(
    user_id: int,
    card_id: str,
):
    manager = _get_card_manager()

    if manager is None:
        return None

    try:
        return manager.get_user_card(
            user_id,
            card_id,
        )
    except Exception:
        return None


def _add_card(
    user_id: int,
    card_id: str,
    quantity: int = 1,
) -> bool:

    manager = _get_card_manager()

    if manager is None:
        return False

    try:
        manager.add_user_card(
            user_id=user_id,
            card_id=card_id,
            quantity=quantity,
        )

        return True

    except Exception:
        return False


def _remove_card(
    user_id: int,
    card_id: str,
    quantity: int = 1,
) -> bool:

    manager = _get_card_manager()

    if manager is None:
        return False

    try:
        return bool(
            manager.remove_user_card(
                user_id=user_id,
                card_id=card_id,
                quantity=quantity,
            )
        )

    except Exception:
        return False


# ============================================================
# OWNERSHIP
# ============================================================

def get_card_quantity(
    user_id: int,
    card_id: str,
) -> int:

    user_id = normalize_user_id(user_id)
    card_id = normalize_card_id(card_id)

    user_card = _get_user_card(
        user_id,
        card_id,
    )

    if user_card is None:
        return 0

    return max(
        0,
        int(
            getattr(
                user_card,
                "quantity",
                0,
            )
        ),
    )


def owns_card(
    user_id: int,
    card_id: str,
    quantity: int = 1,
) -> bool:

    if quantity <= 0:
        return False

    return (
        get_card_quantity(
            user_id,
            card_id,
        )
        >= quantity
    )


# ============================================================
# FAVORITE PROTECTION
# ============================================================

def is_favorite(
    user_id: int,
    card_id: str,
) -> bool:

    user_card = _get_user_card(
        user_id,
        card_id,
    )

    if user_card is None:
        return False

    return bool(
        getattr(
            user_card,
            "favorite",
            False,
        )
    )


def can_transfer_card(
    user_id: int,
    card_id: str,
    quantity: int = 1,
) -> tuple[bool, str]:

    if quantity <= 0:
        return (
            False,
            "❌ Quantity must be greater than 0.",
        )

    if quantity > MAX_GIFT_QUANTITY:
        return (
            False,
            (
                f"❌ Maximum quantity per transfer "
                f"is {MAX_GIFT_QUANTITY}."
            ),
        )

    if not owns_card(
        user_id,
        card_id,
        quantity,
    ):
        return (
            False,
            "❌ You don't own enough copies of this card.",
        )

    if (
        PROTECT_FAVORITE
        and is_favorite(
            user_id,
            card_id,
        )
    ):
        return (
            False,
            (
                "❤️ This card is marked as Favorite.\n"
                "Use /unfav first if you want to transfer it."
            ),
        )

    return (
        True,
        "OK",
    )


# ============================================================
# GIFT
# ============================================================

def gift_card(
    sender_id: int,
    receiver_id: int,
    card_id: str,
    quantity: int = 1,
) -> TransactionResult:

    sender_id = normalize_user_id(sender_id)
    receiver_id = normalize_user_id(receiver_id)
    card_id = normalize_card_id(card_id)

    if sender_id == receiver_id:
        return TransactionResult(
            success=False,
            message="❌ You cannot gift a card to yourself.",
            sender_id=sender_id,
            receiver_id=receiver_id,
            sender_card_id=card_id,
            created_at=utc_now(),
        )

    valid, reason = can_transfer_card(
        sender_id,
        card_id,
        quantity,
    )

    if not valid:
        return TransactionResult(
            success=False,
            message=reason,
            sender_id=sender_id,
            receiver_id=receiver_id,
            sender_card_id=card_id,
            created_at=utc_now(),
        )

    # --------------------------------------------------------
    # ATOMIC TRANSFER
    # --------------------------------------------------------

    with _LOCK:

        # Check again while holding the lock.
        if not owns_card(
            sender_id,
            card_id,
            quantity,
        ):
            return TransactionResult(
                success=False,
                message="❌ Card is no longer available.",
                sender_id=sender_id,
                receiver_id=receiver_id,
                sender_card_id=card_id,
                created_at=utc_now(),
            )

        removed = _remove_card(
            sender_id,
            card_id,
            quantity,
        )

        if not removed:
            return TransactionResult(
                success=False,
                message="❌ Failed to remove the card.",
                sender_id=sender_id,
                receiver_id=receiver_id,
                sender_card_id=card_id,
                created_at=utc_now(),
            )

        added = _add_card(
            receiver_id,
            card_id,
            quantity,
        )

        # Rollback if receiver operation fails.
        if not added:

            _add_card(
                sender_id,
                card_id,
                quantity,
            )

            return TransactionResult(
                success=False,
                message="❌ Transfer failed. Your card was restored.",
                sender_id=sender_id,
                receiver_id=receiver_id,
                sender_card_id=card_id,
                created_at=utc_now(),
            )

        result = TransactionResult(
            success=True,
            message=(
                "🎁 <b>Card Gift Successful!</b>\n\n"
                f"🎴 Card ID: <code>{escape_html(card_id)}</code>\n"
                f"📦 Quantity: <b>{quantity}</b>\n"
                f"👤 From: <code>{sender_id}</code>\n"
                f"👤 To: <code>{receiver_id}</code>"
            ),
            sender_id=sender_id,
            receiver_id=receiver_id,
            sender_card_id=card_id,
            sender_quantity=quantity,
            created_at=utc_now(),
        )

        _TRANSACTION_HISTORY.append(result)

        return result


# ============================================================
# TRADE VALIDATION
# ============================================================

def validate_trade(
    user_a: int,
    card_a: str,
    user_b: int,
    card_b: str,
) -> tuple[bool, str]:

    user_a = normalize_user_id(user_a)
    user_b = normalize_user_id(user_b)

    card_a = normalize_card_id(card_a)
    card_b = normalize_card_id(card_b)

    if user_a == user_b:
        return (
            False,
            "❌ You cannot trade with yourself.",
        )

    valid, reason = can_transfer_card(
        user_a,
        card_a,
        1,
    )

    if not valid:
        return False, f"❌ User A: {reason}"

    valid, reason = can_transfer_card(
        user_b,
        card_b,
        1,
    )

    if not valid:
        return False, f"❌ User B: {reason}"

    return (
        True,
        "OK",
    )


# ============================================================
# TRADE
# ============================================================

def trade_cards(
    user_a: int,
    card_a: str,
    user_b: int,
    card_b: str,
) -> TransactionResult:

    user_a = normalize_user_id(user_a)
    user_b = normalize_user_id(user_b)

    card_a = normalize_card_id(card_a)
    card_b = normalize_card_id(card_b)

    valid, reason = validate_trade(
        user_a,
        card_a,
        user_b,
        card_b,
    )

    if not valid:
        return TransactionResult(
            success=False,
            message=reason,
            sender_id=user_a,
            receiver_id=user_b,
            sender_card_id=card_a,
            receiver_card_id=card_b,
            created_at=utc_now(),
        )

    # --------------------------------------------------------
    # ATOMIC SWAP
    # --------------------------------------------------------

    with _LOCK:

        # Re-check ownership.
        if not owns_card(
            user_a,
            card_a,
            1,
        ):
            return TransactionResult(
                success=False,
                message="❌ User A no longer owns the offered card.",
                sender_id=user_a,
                receiver_id=user_b,
                sender_card_id=card_a,
                receiver_card_id=card_b,
                created_at=utc_now(),
            )

        if not owns_card(
            user_b,
            card_b,
            1,
        ):
            return TransactionResult(
                success=False,
                message="❌ User B no longer owns the offered card.",
                sender_id=user_a,
                receiver_id=user_b,
                sender_card_id=card_a,
                receiver_card_id=card_b,
                created_at=utc_now(),
            )

        # Remove A's card.
        removed_a = _remove_card(
            user_a,
            card_a,
            1,
        )

        if not removed_a:
            return TransactionResult(
                success=False,
                message="❌ Failed to remove User A's card.",
                sender_id=user_a,
                receiver_id=user_b,
                sender_card_id=card_a,
                receiver_card_id=card_b,
                created_at=utc_now(),
            )

        # Remove B's card.
        removed_b = _remove_card(
            user_b,
            card_b,
            1,
        )

        if not removed_b:

            _add_card(
                user_a,
                card_a,
                1,
            )

            return TransactionResult(
                success=False,
                message="❌ Trade failed. Cards were restored.",
                sender_id=user_a,
                receiver_id=user_b,
                sender_card_id=card_a,
                receiver_card_id=card_b,
                created_at=utc_now(),
            )

        # Add B's card to A.
        added_to_a = _add_card(
            user_a,
            card_b,
            1,
        )

        if not added_to_a:

            _add_card(
                user_a,
                card_a,
                1,
            )

            _add_card(
                user_b,
                card_b,
                1,
            )

            return TransactionResult(
                success=False,
                message="❌ Trade failed. Cards were restored.",
                sender_id=user_a,
                receiver_id=user_b,
                sender_card_id=card_a,
                receiver_card_id=card_b,
                created_at=utc_now(),
            )

        # Add A's card to B.
        added_to_b = _add_card(
            user_b,
            card_a,
            1,
        )

        if not added_to_b:

            # Roll back everything.
            _remove_card(
                user_a,
                card_b,
                1,
            )

            _add_card(
                user_a,
                card_a,
                1,
            )

            _add_card(
                user_b,
                card_b,
                1,
            )

            return TransactionResult(
                success=False,
                message="❌ Trade failed. Cards were restored.",
                sender_id=user_a,
                receiver_id=user_b,
                sender_card_id=card_a,
                receiver_card_id=card_b,
                created_at=utc_now(),
            )

        result = TransactionResult(
            success=True,
            message=(
                "🔄 <b>TRADE SUCCESSFUL!</b>\n\n"
                f"👤 User A gave: "
                f"<code>{escape_html(card_a)}</code>\n"
                f"👤 User B gave: "
                f"<code>{escape_html(card_b)}</code>\n\n"
                "✨ Both cards have been exchanged."
            ),
            sender_id=user_a,
            receiver_id=user_b,
            sender_card_id=card_a,
            receiver_card_id=card_b,
            sender_quantity=1,
            receiver_quantity=1,
            created_at=utc_now(),
        )

        _TRANSACTION_HISTORY.append(result)

        return result


# ============================================================
# TRADE FROM COMMAND
# ============================================================

def parse_trade_command(
    user_id: int,
    args: list[str],
    replied_user_id: Optional[int] = None,
) -> tuple[bool, dict, str]:

    """
    Supported format:

        /trade YOUR_ID THEIR_ID

    Or when replying to another user:

        /trade YOUR_ID THEIR_ID

    Telegram handler can pass the replied user's ID.
    """

    if not args:
        return (
            False,
            {},
            (
                "❌ Usage:\n"
                "<code>/trade YOUR_ID THEIR_ID</code>"
            ),
        )

    if len(args) < 2:
        return (
            False,
            {},
            (
                "❌ Usage:\n"
                "<code>/trade YOUR_ID THEIR_ID</code>"
            ),
        )

    your_card_id = args[0]
    their_card_id = args[1]

    if replied_user_id is None:
        return (
            False,
            {},
            (
                "❌ Please reply to the user "
                "you want to trade with."
            ),
        )

    data = {
        "user_a": int(user_id),
        "user_b": int(replied_user_id),
        "card_a": normalize_card_id(
            your_card_id
        ),
        "card_b": normalize_card_id(
            their_card_id
        ),
    }

    return (
        True,
        data,
        "OK",
    )


# ============================================================
# TRANSACTION HISTORY
# ============================================================

def get_transaction_history(
    limit: int = 50,
) -> list[TransactionResult]:

    limit = max(
        1,
        int(limit),
    )

    with _LOCK:
        return list(
            reversed(
                _TRANSACTION_HISTORY[-limit:]
            )
        )


def get_user_transactions(
    user_id: int,
    limit: int = 50,
) -> list[TransactionResult]:

    user_id = int(user_id)

    transactions = [
        transaction
        for transaction in get_transaction_history(
            limit=100000
        )
        if (
            transaction.sender_id == user_id
            or transaction.receiver_id == user_id
        )
    ]

    return transactions[:max(1, int(limit))]


# ============================================================
# FORMAT
# ============================================================

def format_gift_confirmation(
    card_id: str,
    receiver_id: int,
) -> str:

    return (
        "🎁 <b>CONFIRM GIFT</b>\n\n"
        f"🎴 Card: <code>{escape_html(card_id)}</code>\n"
        f"👤 Receiver: <code>{receiver_id}</code>\n\n"
        "⚠️ This action cannot be undone."
    )


def format_trade_confirmation(
    user_a: int,
    card_a: str,
    user_b: int,
    card_b: str,
) -> str:

    return (
        "🔄 <b>CONFIRM TRADE</b>\n\n"
        f"👤 User A: <code>{user_a}</code>\n"
        f"🎴 Gives: <code>{escape_html(card_a)}</code>\n\n"
        f"👤 User B: <code>{user_b}</code>\n"
        f"🎴 Gives: <code>{escape_html(card_b)}</code>\n\n"
        "⚠️ Confirm only if both users agree."
    )


# ============================================================
# ADMIN
# ============================================================

def admin_force_gift(
    sender_id: int,
    receiver_id: int,
    card_id: str,
    quantity: int = 1,
) -> TransactionResult:

    """
    Admin version bypasses Favorite protection.

    Ownership is still required.
    """

    sender_id = normalize_user_id(sender_id)
    receiver_id = normalize_user_id(receiver_id)
    card_id = normalize_card_id(card_id)

    if sender_id == receiver_id:
        return TransactionResult(
            success=False,
            message="❌ Sender and receiver cannot be the same.",
            created_at=utc_now(),
        )

    if not owns_card(
        sender_id,
        card_id,
        quantity,
    ):
        return TransactionResult(
            success=False,
            message="❌ Sender does not own enough cards.",
            created_at=utc_now(),
        )

    with _LOCK:

        if not _remove_card(
            sender_id,
            card_id,
            quantity,
        ):
            return TransactionResult(
                success=False,
                message="❌ Could not remove card.",
                created_at=utc_now(),
            )

        if not _add_card(
            receiver_id,
            card_id,
            quantity,
        ):

            _add_card(
                sender_id,
                card_id,
                quantity,
            )

            return TransactionResult(
                success=False,
                message="❌ Transfer failed. Card restored.",
                created_at=utc_now(),
            )

        result = TransactionResult(
            success=True,
            message=(
                "🛡️ <b>ADMIN CARD TRANSFER</b>\n\n"
                f"🎴 Card: <code>{escape_html(card_id)}</code>\n"
                f"📦 Quantity: <b>{quantity}</b>\n"
                f"👤 From: <code>{sender_id}</code>\n"
                f"👤 To: <code>{receiver_id}</code>"
            ),
            sender_id=sender_id,
            receiver_id=receiver_id,
            sender_card_id=card_id,
            sender_quantity=quantity,
            created_at=utc_now(),
        )

        _TRANSACTION_HISTORY.append(result)

        return result


# ============================================================
# RESET
# ============================================================

def clear_transaction_history() -> None:

    with _LOCK:
        _TRANSACTION_HISTORY.clear()


# ============================================================
# HTML
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
# EXPORTS
# ============================================================

__all__ = [
    "MAX_TRADE_CARDS",
    "MAX_GIFT_QUANTITY",
    "PROTECT_FAVORITE",

    "TransactionResult",

    "utc_now",
    "normalize_user_id",
    "normalize_card_id",

    "get_card_quantity",
    "owns_card",

    "is_favorite",
    "can_transfer_card",

    "gift_card",

    "validate_trade",
    "trade_cards",

    "parse_trade_command",

    "get_transaction_history",
    "get_user_transactions",

    "format_gift_confirmation",
    "format_trade_confirmation",

    "admin_force_gift",

    "clear_transaction_history",

    "escape_html",
]
