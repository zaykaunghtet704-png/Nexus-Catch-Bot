# group_system.py
# Nexus Catch Bot
# Group registration / approval / member check / bot admin check

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional
from datetime import datetime, timezone
import asyncio


# ============================================================
# CONSTANTS
# ============================================================

MIN_GROUP_MEMBERS = 50


# ============================================================
# DATA MODEL
# ============================================================

@dataclass
class GroupInfo:
    chat_id: int
    title: str = ""
    username: Optional[str] = None
    invite_link: Optional[str] = None

    added_by: Optional[int] = None
    member_count: int = 0

    bot_is_admin: bool = False
    approved: bool = False
    banned: bool = False

    created_at: str = ""

    @property
    def public_link(self) -> Optional[str]:
        """
        Return public group link if available.
        Otherwise return invite link.
        """
        if self.username:
            return f"https://t.me/{self.username}"

        return self.invite_link


# ============================================================
# RUNTIME STORAGE
# ============================================================

GROUPS: dict[int, GroupInfo] = {}


# ============================================================
# BASIC HELPERS
# ============================================================

def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def get_group(chat_id: int) -> Optional[GroupInfo]:
    try:
        chat_id = int(chat_id)
    except (TypeError, ValueError):
        return None

    return GROUPS.get(chat_id)


def register_group(
    chat_id: int,
    title: str = "",
    username: Optional[str] = None,
    added_by: Optional[int] = None,
) -> GroupInfo:

    chat_id = int(chat_id)

    group = GROUPS.get(chat_id)

    if group is None:
        group = GroupInfo(
            chat_id=chat_id,
            title=title or "",
            username=username,
            added_by=added_by,
            created_at=utc_now(),
        )

        GROUPS[chat_id] = group

    else:
        if title:
            group.title = title

        if username:
            group.username = username

        if added_by is not None:
            group.added_by = added_by

    return group


# ============================================================
# GROUP LINK
# ============================================================

def get_public_group_link(username: Optional[str]) -> Optional[str]:
    """
    Generate a public Telegram group link.

    Example:
        @mygroup -> https://t.me/mygroup
    """

    if not username:
        return None

    username = username.strip()

    if username.startswith("@"):
        username = username[1:]

    if not username:
        return None

    return f"https://t.me/{username}"


async def get_group_link(bot, chat_id: int) -> Optional[str]:
    """
    Try to obtain the group's Telegram link.

    Priority:
        1. Public username
        2. Bot's exported invite link
        3. None

    The bot must have sufficient permissions for invite-link access.
    """

    try:
        chat = await bot.get_chat(chat_id)
    except Exception:
        return None

    # Public group
    username = getattr(chat, "username", None)

    public_link = get_public_group_link(username)

    if public_link:
        return public_link

    # Private group
    try:
        invite_link = await bot.create_chat_invite_link(
            chat_id=chat_id,
            name="Nexus Catch Bot"
        )

        link = getattr(invite_link, "invite_link", None)

        if link:
            return link

    except Exception:
        pass

    # Some Telegram versions expose invite_link directly
    try:
        link = getattr(chat, "invite_link", None)

        if link:
            return link

    except Exception:
        pass

    return None


# ============================================================
# BOT ADMIN CHECK
# ============================================================

async def check_bot_admin(bot, chat_id: int) -> bool:
    """
    Check whether the bot is an administrator in the group.
    """

    try:
        me = await bot.get_me()

        member = await bot.get_chat_member(
            chat_id=chat_id,
            user_id=me.id,
        )

        status = getattr(member, "status", "")

        return status in {
            "administrator",
            "creator",
        }

    except Exception:
        return False


# ============================================================
# MEMBER COUNT
# ============================================================

async def get_member_count(bot, chat_id: int) -> int:
    """
    Get current group member count.
    """

    try:
        count = await bot.get_chat_member_count(chat_id)

        return int(count)

    except Exception:
        return 0


async def update_member_count(bot, chat_id: int) -> int:
    count = await get_member_count(bot, chat_id)

    group = get_group(chat_id)

    if group:
        group.member_count = count

    return count


# ============================================================
# GROUP REQUIREMENTS
# ============================================================

def has_minimum_members(member_count: int) -> bool:
    try:
        return int(member_count) >= MIN_GROUP_MEMBERS
    except (TypeError, ValueError):
        return False


def group_requirements_met(group: GroupInfo) -> bool:
    """
    Check basic requirements:

    - At least 50 members
    - Bot must be admin
    - Group must not be banned
    - Group must be approved
    """

    if group.banned:
        return False

    if not has_minimum_members(group.member_count):
        return False

    if not group.bot_is_admin:
        return False

    if not group.approved:
        return False

    return True


# ============================================================
# GROUP APPROVAL
# ============================================================

def approve_group(chat_id: int) -> bool:
    group = get_group(chat_id)

    if group is None:
        return False

    if group.banned:
        return False

    group.approved = True

    return True


def reject_group(chat_id: int) -> bool:
    group = get_group(chat_id)

    if group is None:
        return False

    group.approved = False

    return True


def is_group_approved(chat_id: int) -> bool:
    group = get_group(chat_id)

    if group is None:
        return False

    return group.approved


# ============================================================
# BAN
# ============================================================

def ban_group(chat_id: int) -> bool:
    group = get_group(chat_id)

    if group is None:
        return False

    group.banned = True
    group.approved = False

    return True


def unban_group(chat_id: int) -> bool:
    group = get_group(chat_id)

    if group is None:
        return False

    group.banned = False

    return True


def is_group_banned(chat_id: int) -> bool:
    group = get_group(chat_id)

    if group is None:
        return False

    return group.banned


# ============================================================
# FULL GROUP REFRESH
# ============================================================

async def refresh_group(bot, chat_id: int) -> Optional[GroupInfo]:
    """
    Refresh all important group information.
    """

    try:
        chat_id = int(chat_id)
    except (TypeError, ValueError):
        return None

    try:
        chat = await bot.get_chat(chat_id)
    except Exception:
        return None

    title = getattr(chat, "title", "") or ""
    username = getattr(chat, "username", None)

    group = register_group(
        chat_id=chat_id,
        title=title,
        username=username,
    )

    # Member count
    try:
        group.member_count = await get_member_count(
            bot,
            chat_id,
        )
    except Exception:
        group.member_count = 0

    # Bot admin
    group.bot_is_admin = await check_bot_admin(
        bot,
        chat_id,
    )

    # Group link
    group.invite_link = await get_group_link(
        bot,
        chat_id,
    )

    return group


# ============================================================
# ACCESS CHECK
# ============================================================

async def can_use_bot_in_group(
    bot,
    chat_id: int,
) -> tuple[bool, str]:

    group = await refresh_group(
        bot,
        chat_id,
    )

    if group is None:
        return (
            False,
            "❌ Unable to read this group."
        )

    if group.banned:
        return (
            False,
            "🚫 This group has been blocked by the bot owner."
        )

    if not group.bot_is_admin:
        return (
            False,
            "🤖 Please make the bot an administrator first."
        )

    if group.member_count < MIN_GROUP_MEMBERS:
        return (
            False,
            f"👥 This bot requires at least "
            f"{MIN_GROUP_MEMBERS} members."
        )

    if not group.approved:
        return (
            False,
            "⏳ This group has not been approved by the owner yet."
        )

    return (
        True,
        "✅ Group is approved and ready."
    )


# ============================================================
# GROUP INFORMATION TEXT
# ============================================================

def format_group_info(group: GroupInfo) -> str:
    link = group.public_link

    if link:
        link_text = link
    else:
        link_text = "Private / unavailable"

    added_by = (
        str(group.added_by)
        if group.added_by is not None
        else "Unknown"
    )

    return (
        "🏠 <b>Group Information</b>\n\n"
        f"📌 <b>Name:</b> {escape_html(group.title)}\n"
        f"🆔 <b>ID:</b> <code>{group.chat_id}</code>\n"
        f"👥 <b>Members:</b> {group.member_count}\n"
        f"🔗 <b>Link:</b> {escape_html(link_text)}\n"
        f"👤 <b>Added by:</b> <code>{added_by}</code>\n\n"
        f"🤖 <b>Bot Admin:</b> "
        f"{'✅ Yes' if group.bot_is_admin else '❌ No'}\n"
        f"👑 <b>Owner Approved:</b> "
        f"{'✅ Yes' if group.approved else '⏳ Pending'}\n"
        f"🚫 <b>Banned:</b> "
        f"{'❌ Yes' if group.banned else '✅ No'}"
    )


def escape_html(value: str) -> str:
    """
    Escape Telegram HTML special characters.
    """
    value = str(value)

    return (
        value
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


# ============================================================
# OWNER NOTIFICATION DATA
# ============================================================

def build_group_join_notification(
    group: GroupInfo,
) -> str:
    """
    Message for owner/channel notification when a new group
    adds the bot.
    """

    link = group.public_link or "Private / unavailable"

    added_by = (
        f"<code>{group.added_by}</code>"
        if group.added_by is not None
        else "Unknown"
    )

    return (
        "🚨 <b>New Group Added</b>\n\n"
        f"🏠 <b>Group:</b> "
        f"{escape_html(group.title)}\n"
        f"🆔 <b>Group ID:</b> "
        f"<code>{group.chat_id}</code>\n"
        f"👥 <b>Members:</b> "
        f"{group.member_count}\n"
        f"🔗 <b>Link:</b> "
        f"{escape_html(link)}\n"
        f"👤 <b>Added by:</b> "
        f"{added_by}\n\n"
        f"🤖 <b>Bot Admin:</b> "
        f"{'✅' if group.bot_is_admin else '❌'}\n"
        f"👑 <b>Approval:</b> "
        f"{'✅ Approved' if group.approved else '⏳ Pending'}"
    )


# ============================================================
# GROUP LIST
# ============================================================

def get_all_groups() -> list[GroupInfo]:
    return list(GROUPS.values())


def get_approved_group_list() -> list[GroupInfo]:
    return [
        group
        for group in GROUPS.values()
        if group.approved and not group.banned
    ]


def get_pending_groups() -> list[GroupInfo]:
    return [
        group
        for group in GROUPS.values()
        if not group.approved and not group.banned
    ]


# ============================================================
# REMOVE GROUP
# ============================================================

def remove_group(chat_id: int) -> bool:
    try:
        chat_id = int(chat_id)
    except (TypeError, ValueError):
        return False

    if chat_id not in GROUPS:
        return False

    del GROUPS[chat_id]

    return True


# ============================================================
# EXPORT
# ============================================================

__all__ = [
    "MIN_GROUP_MEMBERS",
    "GroupInfo",
    "GROUPS",

    "register_group",
    "get_group",

    "get_public_group_link",
    "get_group_link",

    "check_bot_admin",
    "get_member_count",
    "update_member_count",

    "has_minimum_members",
    "group_requirements_met",

    "approve_group",
    "reject_group",
    "is_group_approved",

    "ban_group",
    "unban_group",
    "is_group_banned",

    "refresh_group",
    "can_use_bot_in_group",

    "format_group_info",
    "build_group_join_notification",

    "get_all_groups",
    "get_approved_group_list",
    "get_pending_groups",

    "remove_group",
]
