# admin.py
# Nexus Catch Bot - Owner / Admin System
# Python 3.10+
#
# This module provides:
# - Owner checks
# - Bot admin management
# - Group approval management
# - Ban / unban
# - Maintenance mode
# - Broadcast permission helpers
# - Admin command permission helpers
#
# Database-specific operations are intentionally kept out of this file
# so it can be connected safely to your existing database.py later.

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Set
from threading import RLock


# ============================================================
# ADMIN DATA
# ============================================================

@dataclass
class AdminData:
    """In-memory administrative state."""

    admins: Set[int] = field(default_factory=set)
    approved_groups: Set[int] = field(default_factory=set)
    banned_users: Set[int] = field(default_factory=set)
    banned_groups: Set[int] = field(default_factory=set)

    # Global bot maintenance mode
    maintenance: bool = False

    # Commands disabled globally
    disabled_commands: Set[str] = field(default_factory=set)


# Global state
_STATE = AdminData()
_LOCK = RLock()


# ============================================================
# NORMALIZERS
# ============================================================

def normalize_command(command: str) -> str:
    """
    Normalize a command.

    Examples:
        '/givecoins' -> 'givecoins'
        'givecoins'  -> 'givecoins'
    """
    if not command:
        return ""

    command = str(command).strip().lower()

    if command.startswith("/"):
        command = command[1:]

    # Telegram command may contain @BotUsername
    if "@" in command:
        command = command.split("@", 1)[0]

    return command


def normalize_id(value) -> Optional[int]:
    """Safely convert a Telegram ID to int."""
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


# ============================================================
# OWNER
# ============================================================

def is_owner(user_id: int, owner_id: int) -> bool:
    """
    Check whether a Telegram user is the bot owner.
    """
    uid = normalize_id(user_id)
    oid = normalize_id(owner_id)

    if uid is None or oid is None:
        return False

    return uid == oid


# ============================================================
# ADMIN MANAGEMENT
# ============================================================

def add_admin(user_id: int) -> bool:
    """
    Add a user to bot admins.

    Returns:
        True  -> added
        False -> already admin / invalid ID
    """
    uid = normalize_id(user_id)

    if uid is None:
        return False

    with _LOCK:
        if uid in _STATE.admins:
            return False

        _STATE.admins.add(uid)
        return True


def remove_admin(user_id: int) -> bool:
    """
    Remove a user from bot admins.
    """
    uid = normalize_id(user_id)

    if uid is None:
        return False

    with _LOCK:
        if uid not in _STATE.admins:
            return False

        _STATE.admins.remove(uid)
        return True


def is_admin(user_id: int, owner_id: int) -> bool:
    """
    Owner automatically has admin permissions.
    """
    uid = normalize_id(user_id)

    if uid is None:
        return False

    if is_owner(uid, owner_id):
        return True

    with _LOCK:
        return uid in _STATE.admins


def get_admins() -> list[int]:
    """Return all configured admin IDs."""
    with _LOCK:
        return sorted(_STATE.admins)


# ============================================================
# BAN SYSTEM
# ============================================================

def ban_user(user_id: int) -> bool:
    """Ban a user."""
    uid = normalize_id(user_id)

    if uid is None:
        return False

    with _LOCK:
        if uid in _STATE.banned_users:
            return False

        _STATE.banned_users.add(uid)
        return True


def unban_user(user_id: int) -> bool:
    """Remove a user ban."""
    uid = normalize_id(user_id)

    if uid is None:
        return False

    with _LOCK:
        if uid not in _STATE.banned_users:
            return False

        _STATE.banned_users.remove(uid)
        return True


def is_user_banned(user_id: int) -> bool:
    """Check whether a user is banned."""
    uid = normalize_id(user_id)

    if uid is None:
        return False

    with _LOCK:
        return uid in _STATE.banned_users


def get_banned_users() -> list[int]:
    with _LOCK:
        return sorted(_STATE.banned_users)


# ============================================================
# GROUP BAN SYSTEM
# ============================================================

def ban_group(chat_id: int) -> bool:
    """Ban a group from using the bot."""
    cid = normalize_id(chat_id)

    if cid is None:
        return False

    with _LOCK:
        if cid in _STATE.banned_groups:
            return False

        _STATE.banned_groups.add(cid)
        return True


def unban_group(chat_id: int) -> bool:
    """Remove a group ban."""
    cid = normalize_id(chat_id)

    if cid is None:
        return False

    with _LOCK:
        if cid not in _STATE.banned_groups:
            return False

        _STATE.banned_groups.remove(cid)
        return True


def is_group_banned(chat_id: int) -> bool:
    cid = normalize_id(chat_id)

    if cid is None:
        return False

    with _LOCK:
        return cid in _STATE.banned_groups


# ============================================================
# GROUP APPROVAL
# ============================================================

def approve_group(chat_id: int) -> bool:
    """
    Approve a group for bot usage.
    """
    cid = normalize_id(chat_id)

    if cid is None:
        return False

    with _LOCK:
        if cid in _STATE.approved_groups:
            return False

        _STATE.approved_groups.add(cid)
        return True


def reject_group(chat_id: int) -> bool:
    """
    Remove a group from approved groups.
    """
    cid = normalize_id(chat_id)

    if cid is None:
        return False

    with _LOCK:
        if cid not in _STATE.approved_groups:
            return False

        _STATE.approved_groups.remove(cid)
        return True


def is_group_approved(chat_id: int) -> bool:
    """
    Check group approval status.
    """
    cid = normalize_id(chat_id)

    if cid is None:
        return False

    with _LOCK:
        return cid in _STATE.approved_groups


def get_approved_groups() -> list[int]:
    with _LOCK:
        return sorted(_STATE.approved_groups)


# ============================================================
# MAINTENANCE MODE
# ============================================================

def set_maintenance(enabled: bool) -> None:
    """
    Enable/disable global maintenance mode.
    """
    with _LOCK:
        _STATE.maintenance = bool(enabled)


def is_maintenance() -> bool:
    with _LOCK:
        return _STATE.maintenance


# ============================================================
# COMMAND DISABLE SYSTEM
# ============================================================

def disable_command(command: str) -> bool:
    """
    Disable a command globally.
    """
    cmd = normalize_command(command)

    if not cmd:
        return False

    with _LOCK:
        if cmd in _STATE.disabled_commands:
            return False

        _STATE.disabled_commands.add(cmd)
        return True


def enable_command(command: str) -> bool:
    """
    Enable a previously disabled command.
    """
    cmd = normalize_command(command)

    if not cmd:
        return False

    with _LOCK:
        if cmd not in _STATE.disabled_commands:
            return False

        _STATE.disabled_commands.remove(cmd)
        return True


def is_command_disabled(command: str) -> bool:
    cmd = normalize_command(command)

    if not cmd:
        return False

    with _LOCK:
        return cmd in _STATE.disabled_commands


def get_disabled_commands() -> list[str]:
    with _LOCK:
        return sorted(_STATE.disabled_commands)


# ============================================================
# PERMISSION HELPERS
# ============================================================

def can_use_admin_command(
    user_id: int,
    owner_id: int,
) -> bool:
    """
    Check whether the user can use an admin command.
    """
    return is_admin(user_id, owner_id)


def can_use_owner_command(
    user_id: int,
    owner_id: int,
) -> bool:
    """
    Check whether the user is the owner.
    """
    return is_owner(user_id, owner_id)


def can_use_command(
    user_id: int,
    command: str,
    owner_id: int,
) -> bool:
    """
    General command permission helper.

    Returns False if:
        - user is banned
        - command is disabled
        - user doesn't have admin permission for admin commands
    """

    uid = normalize_id(user_id)
    cmd = normalize_command(command)

    if uid is None or not cmd:
        return False

    if is_user_banned(uid):
        return False

    if is_command_disabled(cmd):
        return False

    return True


# ============================================================
# ADMIN COMMAND LIST
# ============================================================

OWNER_COMMANDS = {
    "addadmin",
    "deladmin",
    "admins",

    "approve",
    "reject",
    "approvedgroups",

    "ban",
    "unban",
    "banned",

    "bangroup",
    "unbangroup",

    "maintenance",

    "broadcast",

    "botstats",
    "groups",
    "users",

    "shutdown",
    "restart",
}


ADMIN_COMMANDS = {
    "addcard",
    "editcard",
    "delcard",

    "givecard",
    "takecard",

    "givecoins",
    "takecoins",

    "drop",
    "setdrop",

    "changetime",

    "checkuser",
    "usercards",

    "marketclear",
    "clearcache",

    "setlang",
}


def is_owner_command(command: str) -> bool:
    return normalize_command(command) in OWNER_COMMANDS


def is_admin_command(command: str) -> bool:
    return normalize_command(command) in ADMIN_COMMANDS


def has_command_permission(
    user_id: int,
    command: str,
    owner_id: int,
) -> bool:
    """
    Final permission checker.

    Owner:
        Can use everything.

    Admin:
        Can use ADMIN_COMMANDS.

    Normal user:
        Cannot use owner/admin commands.
    """

    uid = normalize_id(user_id)
    cmd = normalize_command(command)
    oid = normalize_id(owner_id)

    if uid is None or oid is None or not cmd:
        return False

    if is_user_banned(uid):
        return False

    if is_command_disabled(cmd):
        return False

    # Owner has full access.
    if uid == oid:
        return True

    # Owner-only command.
    if cmd in OWNER_COMMANDS:
        return False

    # Admin command.
    if cmd in ADMIN_COMMANDS:
        return is_admin(uid, oid)

    # Normal command.
    return True


# ============================================================
# RESET
# ============================================================

def reset_admin_state() -> None:
    """
    Reset in-memory admin state.

    IMPORTANT:
    This only clears this module's runtime state.
    A persistent database should be connected later.
    """
    with _LOCK:
        _STATE.admins.clear()
        _STATE.approved_groups.clear()
        _STATE.banned_users.clear()
        _STATE.banned_groups.clear()
        _STATE.disabled_commands.clear()
        _STATE.maintenance = False


# ============================================================
# STATUS
# ============================================================

def get_admin_status(owner_id: int) -> dict:
    """
    Return a safe summary for /botstats or admin panels.
    """
    with _LOCK:
        return {
            "owner_id": normalize_id(owner_id),
            "admins": len(_STATE.admins),
            "approved_groups": len(_STATE.approved_groups),
            "banned_users": len(_STATE.banned_users),
            "banned_groups": len(_STATE.banned_groups),
            "disabled_commands": len(_STATE.disabled_commands),
            "maintenance": _STATE.maintenance,
        }


__all__ = [
    "AdminData",

    "OWNER_COMMANDS",
    "ADMIN_COMMANDS",

    "normalize_command",
    "normalize_id",

    "is_owner",
    "is_admin",
    "add_admin",
    "remove_admin",
    "get_admins",

    "ban_user",
    "unban_user",
    "is_user_banned",
    "get_banned_users",

    "ban_group",
    "unban_group",
    "is_group_banned",

    "approve_group",
    "reject_group",
    "is_group_approved",
    "get_approved_groups",

    "set_maintenance",
    "is_maintenance",

    "disable_command",
    "enable_command",
    "is_command_disabled",
    "get_disabled_commands",

    "can_use_admin_command",
    "can_use_owner_command",
    "can_use_command",

    "is_owner_command",
    "is_admin_command",
    "has_command_permission",

    "reset_admin_state",
    "get_admin_status",
]
