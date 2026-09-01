# admin_system.py
# Nexus Catch Bot
# Owner / Admin Management System
#
# Features:
# - Owner permission
# - Admin management
# - User ban / unban
# - Coin management
# - Card management
# - EXP / Level management
# - Group approval
# - Maintenance mode
# - Broadcast permission
# - Bot statistics
#
# This module intentionally does NOT import database.py
# so it will not break if your existing database API is different.

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from threading import RLock
from typing import Any, Optional
import os


# ============================================================
# CONFIG
# ============================================================

OWNER_ID = int(
    os.getenv(
        "OWNER_ID",
        "0",
    )
)

MAX_ADMINS = int(
    os.getenv(
        "MAX_ADMINS",
        "20",
    )
)


# ============================================================
# LOCK
# ============================================================

_LOCK = RLock()


# ============================================================
# DATA MODELS
# ============================================================

@dataclass
class AdminUser:
    user_id: int

    role: str = "admin"

    active: bool = True

    added_at: str = ""

    added_by: int = 0


@dataclass
class ManagedUser:
    user_id: int

    coins: int = 0

    exp: int = 0

    level: int = 1

    banned: bool = False

    ban_reason: str = ""

    cards: dict[str, int] = field(
        default_factory=dict
    )


@dataclass
class ManagedCard:
    card_id: str

    name: str

    rarity: str = "Common"

    edition: str = "Standard"

    image_url: Optional[str] = None

    video_url: Optional[str] = None

    active: bool = True


@dataclass
class GroupApproval:
    chat_id: int

    approved: bool = False

    rejected: bool = False

    approved_by: int = 0

    approved_at: str = ""

    reason: str = ""


# ============================================================
# IN-MEMORY STATE
# ============================================================

_ADMINS: dict[int, AdminUser] = {}

_USERS: dict[int, ManagedUser] = {}

_CARDS: dict[str, ManagedCard] = {}

_GROUP_APPROVALS: dict[int, GroupApproval] = {}

_BOT_SETTINGS: dict[str, Any] = {
    "maintenance": False,
    "broadcast_enabled": True,
    "drops_enabled": True,
    "registration_enabled": True,
}


# ============================================================
# HELPERS
# ============================================================

def now_utc() -> str:

    return datetime.now(
        timezone.utc
    ).strftime(
        "%Y-%m-%d %H:%M:%S"
    )


def normalize_user_id(
    user_id: Any,
) -> int:

    try:
        return int(user_id)
    except (
        TypeError,
        ValueError,
    ):
        raise ValueError(
            "Invalid user ID."
        )


def normalize_chat_id(
    chat_id: Any,
) -> int:

    try:
        return int(chat_id)
    except (
        TypeError,
        ValueError,
    ):
        raise ValueError(
            "Invalid chat ID."
        )


def normalize_card_id(
    card_id: Any,
) -> str:

    if card_id is None:
        raise ValueError(
            "Card ID is required."
        )

    value = str(
        card_id
    ).strip()

    if not value:
        raise ValueError(
            "Card ID is required."
        )

    if value.isdigit():
        return value.zfill(4)

    return value


# ============================================================
# PERMISSION SYSTEM
# ============================================================

def is_owner(
    user_id: int,
) -> bool:

    user_id = normalize_user_id(
        user_id
    )

    if OWNER_ID == 0:
        return False

    return user_id == OWNER_ID


def is_admin(
    user_id: int,
) -> bool:

    user_id = normalize_user_id(
        user_id
    )

    if is_owner(user_id):
        return True

    with _LOCK:

        admin = _ADMINS.get(
            user_id
        )

        return bool(
            admin
            and admin.active
        )


def has_permission(
    user_id: int,
    permission: str = "admin",
) -> bool:

    if is_owner(user_id):
        return True

    if permission == "owner":
        return False

    return is_admin(user_id)


def require_owner(
    user_id: int,
) -> None:

    if not is_owner(user_id):

        raise PermissionError(
            "Owner permission required."
        )


def require_admin(
    user_id: int,
) -> None:

    if not is_admin(user_id):

        raise PermissionError(
            "Admin permission required."
        )


# ============================================================
# ADMIN MANAGEMENT
# ============================================================

def add_admin(
    actor_id: int,
    target_user_id: int,
    role: str = "admin",
) -> AdminUser:

    require_owner(
        actor_id
    )

    actor_id = normalize_user_id(
        actor_id
    )

    target_user_id = normalize_user_id(
        target_user_id
    )

    if target_user_id == OWNER_ID:

        raise ValueError(
            "Owner cannot be added as an admin."
        )

    with _LOCK:

        active_admins = sum(
            1
            for admin in _ADMINS.values()
            if admin.active
        )

        existing = _ADMINS.get(
            target_user_id
        )

        if (
            existing is None
            and active_admins >= MAX_ADMINS
        ):

            raise ValueError(
                "Maximum admin limit reached."
            )

        admin = AdminUser(
            user_id=target_user_id,
            role=role or "admin",
            active=True,
            added_at=now_utc(),
            added_by=actor_id,
        )

        _ADMINS[
            target_user_id
        ] = admin

        return admin


def remove_admin(
    actor_id: int,
    target_user_id: int,
) -> bool:

    require_owner(
        actor_id
    )

    target_user_id = normalize_user_id(
        target_user_id
    )

    if target_user_id == OWNER_ID:

        raise ValueError(
            "Owner cannot be removed."
        )

    with _LOCK:

        admin = _ADMINS.get(
            target_user_id
        )

        if admin is None:
            return False

        admin.active = False

        return True


def restore_admin(
    actor_id: int,
    target_user_id: int,
) -> bool:

    require_owner(
        actor_id
    )

    target_user_id = normalize_user_id(
        target_user_id
    )

    with _LOCK:

        admin = _ADMINS.get(
            target_user_id
        )

        if admin is None:
            return False

        admin.active = True

        return True


def get_admin(
    user_id: int,
) -> Optional[AdminUser]:

    user_id = normalize_user_id(
        user_id
    )

    with _LOCK:

        return _ADMINS.get(
            user_id
        )


def get_admins(
    include_inactive: bool = False,
) -> list[AdminUser]:

    with _LOCK:

        if include_inactive:

            return list(
                _ADMINS.values()
            )

        return [
            admin
            for admin in _ADMINS.values()
            if admin.active
        ]


# ============================================================
# USER MANAGEMENT
# ============================================================

def ensure_managed_user(
    user_id: int,
) -> ManagedUser:

    user_id = normalize_user_id(
        user_id
    )

    with _LOCK:

        user = _USERS.get(
            user_id
        )

        if user is None:

            user = ManagedUser(
                user_id=user_id
            )

            _USERS[
                user_id
            ] = user

        return user


def get_managed_user(
    user_id: int,
) -> Optional[ManagedUser]:

    user_id = normalize_user_id(
        user_id
    )

    with _LOCK:

        return _USERS.get(
            user_id
        )


# ============================================================
# BAN / UNBAN
# ============================================================

def ban_user(
    actor_id: int,
    target_user_id: int,
    reason: str = "",
) -> ManagedUser:

    require_admin(
        actor_id
    )

    actor_id = normalize_user_id(
        actor_id
    )

    target_user_id = normalize_user_id(
        target_user_id
    )

    if target_user_id == OWNER_ID:

        raise PermissionError(
            "Owner cannot be banned."
        )

    if (
        is_admin(target_user_id)
        and not is_owner(actor_id)
    ):

        raise PermissionError(
            "Only the owner can ban another admin."
        )

    with _LOCK:

        user = ensure_managed_user(
            target_user_id
        )

        user.banned = True

        user.ban_reason = (
            reason or "No reason provided."
        )

        return user


def unban_user(
    actor_id: int,
    target_user_id: int,
) -> bool:

    require_admin(
        actor_id
    )

    target_user_id = normalize_user_id(
        target_user_id
    )

    with _LOCK:

        user = ensure_managed_user(
            target_user_id
        )

        user.banned = False
        user.ban_reason = ""

        return True


def is_banned(
    user_id: int,
) -> bool:

    user = get_managed_user(
        user_id
    )

    if user is None:
        return False

    return user.banned


# ============================================================
# COIN MANAGEMENT
# ============================================================

def add_coins(
    actor_id: int,
    target_user_id: int,
    amount: int,
) -> ManagedUser:

    require_admin(
        actor_id
    )

    amount = int(
        amount
    )

    if amount <= 0:

        raise ValueError(
            "Amount must be greater than zero."
        )

    target_user_id = normalize_user_id(
        target_user_id
    )

    with _LOCK:

        user = ensure_managed_user(
            target_user_id
        )

        user.coins += amount

        return user


def remove_coins(
    actor_id: int,
    target_user_id: int,
    amount: int,
) -> ManagedUser:

    require_admin(
        actor_id
    )

    amount = int(
        amount
    )

    if amount <= 0:

        raise ValueError(
            "Amount must be greater than zero."
        )

    target_user_id = normalize_user_id(
        target_user_id
    )

    with _LOCK:

        user = ensure_managed_user(
            target_user_id
        )

        user.coins = max(
            0,
            user.coins - amount,
        )

        return user


def set_coins(
    actor_id: int,
    target_user_id: int,
    amount: int,
) -> ManagedUser:

    require_admin(
        actor_id
    )

    amount = max(
        0,
        int(amount),
    )

    with _LOCK:

        user = ensure_managed_user(
            target_user_id
        )

        user.coins = amount

        return user


def get_coins(
    user_id: int,
) -> int:

    user = get_managed_user(
        user_id
    )

    if user is None:
        return 0

    return user.coins


# ============================================================
# EXP / LEVEL MANAGEMENT
# ============================================================

def calculate_level(
    exp: int,
) -> int:

    exp = max(
        0,
        int(exp),
    )

    # Simple progression.
    # 100 EXP per level.
    return max(
        1,
        (exp // 100) + 1,
    )


def add_exp(
    actor_id: int,
    target_user_id: int,
    amount: int,
) -> ManagedUser:

    require_admin(
        actor_id
    )

    amount = int(
        amount
    )

    if amount <= 0:

        raise ValueError(
            "EXP must be greater than zero."
        )

    with _LOCK:

        user = ensure_managed_user(
            target_user_id
        )

        user.exp += amount

        user.level = calculate_level(
            user.exp
        )

        return user


def set_exp(
    actor_id: int,
    target_user_id: int,
    amount: int,
) -> ManagedUser:

    require_admin(
        actor_id
    )

    with _LOCK:

        user = ensure_managed_user(
            target_user_id
        )

        user.exp = max(
            0,
            int(amount),
        )

        user.level = calculate_level(
            user.exp
        )

        return user


def set_level(
    actor_id: int,
    target_user_id: int,
    level: int,
) -> ManagedUser:

    require_admin(
        actor_id
    )

    level = max(
        1,
        int(level),
    )

    with _LOCK:

        user = ensure_managed_user(
            target_user_id
        )

        user.level = level

        return user


# ============================================================
# CARD MANAGEMENT
# ============================================================

def add_card(
    actor_id: int,
    card_id: str,
    name: str,
    rarity: str = "Common",
    edition: str = "Standard",
    image_url: Optional[str] = None,
    video_url: Optional[str] = None,
) -> ManagedCard:

    require_admin(
        actor_id
    )

    card_id = normalize_card_id(
        card_id
    )

    name = str(
        name
    ).strip()

    if not name:

        raise ValueError(
            "Card name is required."
        )

    with _LOCK:

        card = ManagedCard(
            card_id=card_id,
            name=name,
            rarity=(
                rarity
                or "Common"
            ),
            edition=(
                edition
                or "Standard"
            ),
            image_url=image_url,
            video_url=video_url,
            active=True,
        )

        _CARDS[
            card_id
        ] = card

        return card


def update_card(
    actor_id: int,
    card_id: str,
    **changes,
) -> Optional[ManagedCard]:

    require_admin(
        actor_id
    )

    card_id = normalize_card_id(
        card_id
    )

    with _LOCK:

        card = _CARDS.get(
            card_id
        )

        if card is None:
            return None

        allowed = {
            "name",
            "rarity",
            "edition",
            "image_url",
            "video_url",
            "active",
        }

        for key, value in changes.items():

            if key in allowed:

                setattr(
                    card,
                    key,
                    value,
                )

        return card


def remove_card(
    actor_id: int,
    card_id: str,
) -> bool:

    require_admin(
        actor_id
    )

    card_id = normalize_card_id(
        card_id
    )

    with _LOCK:

        card = _CARDS.get(
            card_id
        )

        if card is None:
            return False

        card.active = False

        return True


def get_card(
    card_id: str,
) -> Optional[ManagedCard]:

    card_id = normalize_card_id(
        card_id
    )

    with _LOCK:

        return _CARDS.get(
            card_id
        )


def get_cards(
    active_only: bool = True,
) -> list[ManagedCard]:

    with _LOCK:

        if not active_only:

            return list(
                _CARDS.values()
            )

        return [
            card
            for card in _CARDS.values()
            if card.active
        ]


# ============================================================
# USER CARD MANAGEMENT
# ============================================================

def give_card(
    actor_id: int,
    target_user_id: int,
    card_id: str,
    quantity: int = 1,
) -> ManagedUser:

    require_admin(
        actor_id
    )

    card_id = normalize_card_id(
        card_id
    )

    quantity = int(
        quantity
    )

    if quantity <= 0:

        raise ValueError(
            "Quantity must be greater than zero."
        )

    with _LOCK:

        if card_id not in _CARDS:

            raise ValueError(
                "Card does not exist."
            )

        user = ensure_managed_user(
            target_user_id
        )

        user.cards[card_id] = (
            user.cards.get(
                card_id,
                0,
            )
            + quantity
        )

        return user


def take_card(
    actor_id: int,
    target_user_id: int,
    card_id: str,
    quantity: int = 1,
) -> ManagedUser:

    require_admin(
        actor_id
    )

    card_id = normalize_card_id(
        card_id
    )

    quantity = max(
        1,
        int(quantity),
    )

    with _LOCK:

        user = ensure_managed_user(
            target_user_id
        )

        current = user.cards.get(
            card_id,
            0,
        )

        new_quantity = max(
            0,
            current - quantity,
        )

        if new_quantity == 0:

            user.cards.pop(
                card_id,
                None,
            )

        else:

            user.cards[
                card_id
            ] = new_quantity

        return user


def get_user_cards(
    user_id: int,
) -> dict[str, int]:

    user = get_managed_user(
        user_id
    )

    if user is None:

        return {}

    with _LOCK:

        return dict(
            user.cards
        )


# ============================================================
# GROUP APPROVAL
# ============================================================

def approve_group(
    actor_id: int,
    chat_id: int,
) -> GroupApproval:

    require_owner(
        actor_id
    )

    chat_id = normalize_chat_id(
        chat_id
    )

    with _LOCK:

        approval = GroupApproval(
            chat_id=chat_id,
            approved=True,
            rejected=False,
            approved_by=normalize_user_id(
                actor_id
            ),
            approved_at=now_utc(),
            reason="",
        )

        _GROUP_APPROVALS[
            chat_id
        ] = approval

        return approval


def reject_group(
    actor_id: int,
    chat_id: int,
    reason: str = "",
) -> GroupApproval:

    require_owner(
        actor_id
    )

    chat_id = normalize_chat_id(
        chat_id
    )

    with _LOCK:

        approval = GroupApproval(
            chat_id=chat_id,
            approved=False,
            rejected=True,
            approved_by=normalize_user_id(
                actor_id
            ),
            approved_at=now_utc(),
            reason=(
                reason
                or "Rejected by owner."
            ),
        )

        _GROUP_APPROVALS[
            chat_id
        ] = approval

        return approval


def is_group_approved(
    chat_id: int,
) -> bool:

    chat_id = normalize_chat_id(
        chat_id
    )

    with _LOCK:

        approval = _GROUP_APPROVALS.get(
            chat_id
        )

        return bool(
            approval
            and approval.approved
        )


def get_pending_groups() -> list[
    GroupApproval
]:

    with _LOCK:

        return [
            approval
            for approval
            in _GROUP_APPROVALS.values()
            if not approval.approved
            and not approval.rejected
        ]


# ============================================================
# BOT SETTINGS
# ============================================================

def set_setting(
    actor_id: int,
    key: str,
    value: Any,
) -> Any:

    require_owner(
        actor_id
    )

    key = str(
        key
    ).strip()

    if not key:

        raise ValueError(
            "Setting key is required."
        )

    with _LOCK:

        _BOT_SETTINGS[
            key
        ] = value

        return value


def get_setting(
    key: str,
    default: Any = None,
) -> Any:

    with _LOCK:

        return _BOT_SETTINGS.get(
            key,
            default,
        )


def is_maintenance() -> bool:

    return bool(
        get_setting(
            "maintenance",
            False,
        )
    )


def set_maintenance(
    actor_id: int,
    enabled: bool,
) -> bool:

    require_owner(
        actor_id
    )

    with _LOCK:

        _BOT_SETTINGS[
            "maintenance"
        ] = bool(enabled)

        return bool(enabled)


def set_drops_enabled(
    actor_id: int,
    enabled: bool,
) -> bool:

    require_admin(
        actor_id
    )

    with _LOCK:

        _BOT_SETTINGS[
            "drops_enabled"
        ] = bool(enabled)

        return bool(enabled)


# ============================================================
# BROADCAST
# ============================================================

def can_broadcast(
    user_id: int,
) -> bool:

    return (
        is_admin(user_id)
        and bool(
            get_setting(
                "broadcast_enabled",
                True,
            )
        )
    )


def set_broadcast_enabled(
    actor_id: int,
    enabled: bool,
) -> bool:

    require_owner(
        actor_id
    )

    with _LOCK:

        _BOT_SETTINGS[
            "broadcast_enabled"
        ] = bool(enabled)

        return bool(enabled)


# ============================================================
# USER INFORMATION
# ============================================================

def get_user_admin_view(
    actor_id: int,
    target_user_id: int,
) -> dict[str, Any]:

    require_admin(
        actor_id
    )

    user = ensure_managed_user(
        target_user_id
    )

    with _LOCK:

        return {
            "user_id": user.user_id,
            "coins": user.coins,
            "exp": user.exp,
            "level": user.level,
            "banned": user.banned,
            "ban_reason": user.ban_reason,
            "cards": dict(
                user.cards
            ),
            "card_count": sum(
                user.cards.values()
            ),
        }


# ============================================================
# STATISTICS
# ============================================================

def get_statistics(
    actor_id: int,
) -> dict[str, Any]:

    require_admin(
        actor_id
    )

    with _LOCK:

        total_users = len(
            _USERS
        )

        banned_users = sum(
            1
            for user in _USERS.values()
            if user.banned
        )

        total_cards = len(
            [
                card
                for card
                in _CARDS.values()
                if card.active
            ]
        )

        admin_count = len(
            [
                admin
                for admin
                in _ADMINS.values()
                if admin.active
            ]
        )

        approved_groups = len(
            [
                group
                for group
                in _GROUP_APPROVALS.values()
                if group.approved
            ]
        )

        total_coins = sum(
            user.coins
            for user in _USERS.values()
        )

        total_owned_cards = sum(
            sum(
                user.cards.values()
            )
            for user in _USERS.values()
        )

        return {
            "users": total_users,
            "banned_users": banned_users,
            "cards": total_cards,
            "admins": admin_count,
            "approved_groups": approved_groups,
            "total_coins": total_coins,
            "total_owned_cards": total_owned_cards,
            "maintenance": is_maintenance(),
            "drops_enabled": bool(
                get_setting(
                    "drops_enabled",
                    True,
                )
            ),
        }


# ============================================================
# RESET / DANGEROUS OPERATIONS
# ============================================================

def reset_user_data(
    actor_id: int,
    target_user_id: int,
) -> bool:

    require_owner(
        actor_id
    )

    target_user_id = normalize_user_id(
        target_user_id
    )

    if target_user_id == OWNER_ID:

        raise PermissionError(
            "Owner data cannot be reset."
        )

    with _LOCK:

        _USERS.pop(
            target_user_id,
            None,
        )

        return True


def clear_all_admins(
    actor_id: int,
) -> int:

    require_owner(
        actor_id
    )

    with _LOCK:

        count = len(
            _ADMINS
        )

        _ADMINS.clear()

        return count


# ============================================================
# FORMATTING
# ============================================================

def format_admin_list() -> str:

    admins = get_admins()

    if not admins:

        return (
            "👑 <b>ADMIN LIST</b>\n\n"
            "No admins."
        )

    lines = [
        "👑 <b>ADMIN LIST</b>",
        "",
    ]

    for index, admin in enumerate(
        admins,
        start=1,
    ):

        lines.append(
            f"{index}. "
            f"<code>{admin.user_id}</code> "
            f"— <b>{admin.role}</b>"
        )

    return "\n".join(
        lines
    )


def format_statistics(
    actor_id: int,
) -> str:

    stats = get_statistics(
        actor_id
    )

    return (
        "📊 <b>BOT STATISTICS</b>\n\n"
        f"👤 Users: <b>{stats['users']}</b>\n"
        f"🚫 Banned: <b>{stats['banned_users']}</b>\n"
        f"🎴 Cards: <b>{stats['cards']}</b>\n"
        f"👑 Admins: <b>{stats['admins']}</b>\n"
        f"👥 Approved Groups: <b>{stats['approved_groups']}</b>\n"
        f"🪙 Total Coins: <b>{stats['total_coins']}</b>\n"
        f"🎴 Owned Cards: <b>{stats['total_owned_cards']}</b>\n"
        f"🔧 Maintenance: "
        f"<b>{'ON' if stats['maintenance'] else 'OFF'}</b>\n"
        f"🎁 Drops: "
        f"<b>{'ON' if stats['drops_enabled'] else 'OFF'}</b>"
    )


def format_user_admin_view(
    actor_id: int,
    target_user_id: int,
) -> str:

    data = get_user_admin_view(
        actor_id,
        target_user_id,
    )

    return (
        "👤 <b>USER ADMIN VIEW</b>\n\n"
        f"🆔 ID: <code>{data['user_id']}</code>\n"
        f"🪙 Coins: <b>{data['coins']}</b>\n"
        f"⭐ EXP: <b>{data['exp']}</b>\n"
        f"📈 Level: <b>{data['level']}</b>\n"
        f"🎴 Cards: <b>{data['card_count']}</b>\n"
        f"🚫 Banned: "
        f"<b>{'YES' if data['banned'] else 'NO'}</b>"
    )


# ============================================================
# EXPORTS
# ============================================================

__all__ = [

    # Models
    "AdminUser",
    "ManagedUser",
    "ManagedCard",
    "GroupApproval",

    # Permission
    "is_owner",
    "is_admin",
    "has_permission",
    "require_owner",
    "require_admin",

    # Admin
    "add_admin",
    "remove_admin",
    "restore_admin",
    "get_admin",
    "get_admins",

    # Users
    "ensure_managed_user",
    "get_managed_user",

    # Ban
    "ban_user",
    "unban_user",
    "is_banned",

    # Coins
    "add_coins",
    "remove_coins",
    "set_coins",
    "get_coins",

    # EXP
    "calculate_level",
    "add_exp",
    "set_exp",
    "set_level",

    # Cards
    "add_card",
    "update_card",
    "remove_card",
    "get_card",
    "get_cards",

    # User cards
    "give_card",
    "take_card",
    "get_user_cards",

    # Groups
    "approve_group",
    "reject_group",
    "is_group_approved",
    "get_pending_groups",

    # Settings
    "set_setting",
    "get_setting",
    "is_maintenance",
    "set_maintenance",
    "set_drops_enabled",

    # Broadcast
    "can_broadcast",
    "set_broadcast_enabled",

    # Information
    "get_user_admin_view",
    "get_statistics",

    # Reset
    "reset_user_data",
    "clear_all_admins",

    # Formatting
    "format_admin_list",
    "format_statistics",
    "format_user_admin_view",
]
