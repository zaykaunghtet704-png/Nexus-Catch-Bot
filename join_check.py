# join_check.py
# Nexus Catch Bot
# Required Group + Channel membership checker

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


# ============================================================
# DATA
# ============================================================

@dataclass
class JoinResult:
    """Result returned by membership checks."""

    group_joined: bool = False
    channel_joined: bool = False

    group_name: str = "Required Group"
    channel_name: str = "Required Channel"

    group_link: str = ""
    channel_link: str = ""

    error: Optional[str] = None

    @property
    def passed(self) -> bool:
        return self.group_joined and self.channel_joined


# ============================================================
# STATUS VALUES
# ============================================================

MEMBER_STATUSES = {
    "creator",
    "administrator",
    "member",
}

NOT_MEMBER_STATUSES = {
    "left",
    "kicked",
}


# ============================================================
# BASIC STATUS CHECK
# ============================================================

def is_member_status(status: str) -> bool:
    """
    Check whether a Telegram ChatMember status counts as joined.
    """

    if not status:
        return False

    return str(status).lower() in MEMBER_STATUSES


# ============================================================
# TELEGRAM MEMBERSHIP CHECK
# ============================================================

async def check_membership(
    bot,
    chat_id: int,
    user_id: int,
) -> bool:
    """
    Check whether a user has joined a Telegram group/channel.

    Returns False if:
        - user has left
        - user was kicked
        - Telegram request fails
    """

    try:
        member = await bot.get_chat_member(
            chat_id=chat_id,
            user_id=user_id,
        )

        status = getattr(member, "status", "")

        return is_member_status(status)

    except Exception:
        return False


# ============================================================
# GROUP + CHANNEL CHECK
# ============================================================

async def check_required_chats(
    bot,
    user_id: int,
    group_id: int,
    channel_id: int,
    group_link: str,
    channel_link: str,
    group_name: str = "Required Group",
    channel_name: str = "Required Channel",
) -> JoinResult:
    """
    Check both required Group and Channel.
    """

    result = JoinResult(
        group_name=group_name,
        channel_name=channel_name,
        group_link=group_link,
        channel_link=channel_link,
    )

    try:
        result.group_joined = await check_membership(
            bot,
            group_id,
            user_id,
        )

        result.channel_joined = await check_membership(
            bot,
            channel_id,
            user_id,
        )

    except Exception as exc:
        result.error = str(exc)

    return result


# ============================================================
# USER-FACING MESSAGE
# ============================================================

def build_join_message(
    result: JoinResult,
    language: str = "my",
) -> str:
    """
    Create a beautiful join-required message.

    language:
        my = Myanmar
        en = English
    """

    language = (language or "my").lower()

    if language.startswith("en"):
        return build_english_message(result)

    return build_myanmar_message(result)


def build_myanmar_message(result: JoinResult) -> str:
    """
    Myanmar join message.
    """

    lines = [
        "🔐 <b>အသုံးပြုခွင့်မရသေးပါ</b>",
        "",
        "Bot ကို အသုံးပြုရန် အောက်ပါ Group နှင့် Channel",
        "နှစ်ခုလုံးကို Join ထားရပါမယ်။",
        "",
    ]

    if result.group_joined:
        lines.append("✅ Group — Joined")
    else:
        lines.append("❌ Group — မ Join ရသေးပါ")

    if result.channel_joined:
        lines.append("✅ Channel — Joined")
    else:
        lines.append("❌ Channel — မ Join ရသေးပါ")

    lines.extend(
        [
            "",
            "👇 Join ပြီးပါက <b>CHECK</b> ကိုနှိပ်ပါ။",
        ]
    )

    return "\n".join(lines)


def build_english_message(result: JoinResult) -> str:
    """
    English join message.
    """

    lines = [
        "🔐 <b>Access Required</b>",
        "",
        "Please join both the required Group and Channel",
        "before using the bot.",
        "",
    ]

    if result.group_joined:
        lines.append("✅ Group — Joined")
    else:
        lines.append("❌ Group — Not Joined")

    if result.channel_joined:
        lines.append("✅ Channel — Joined")
    else:
        lines.append("❌ Channel — Not Joined")

    lines.extend(
        [
            "",
            "👇 Join them and press <b>CHECK</b>.",
        ]
    )

    return "\n".join(lines)


# ============================================================
# BUTTON DATA
# ============================================================

def get_join_buttons(
    result: JoinResult,
) -> list[list[dict]]:
    """
    Return Telegram InlineKeyboard-compatible button data.

    The actual Telegram InlineKeyboardMarkup is created by bot.py
    so this module stays independent from python-telegram-bot versions.
    """

    buttons: list[list[dict]] = []

    if result.group_link:
        buttons.append(
            [
                {
                    "text": f"👥 {result.group_name}",
                    "url": result.group_link,
                }
            ]
        )

    if result.channel_link:
        buttons.append(
            [
                {
                    "text": f"📢 {result.channel_name}",
                    "url": result.channel_link,
                }
            ]
        )

    buttons.append(
        [
            {
                "text": "🔄 CHECK",
                "callback_data": "joincheck",
            }
        ]
    )

    return buttons


# ============================================================
# CHECK AGAIN
# ============================================================

async def check_again(
    bot,
    user_id: int,
    group_id: int,
    channel_id: int,
) -> JoinResult:
    """
    Re-check membership after the user presses CHECK.

    Links/names can be filled by the caller if necessary.
    """

    result = JoinResult()

    result.group_joined = await check_membership(
        bot,
        group_id,
        user_id,
    )

    result.channel_joined = await check_membership(
        bot,
        channel_id,
        user_id,
    )

    return result


# ============================================================
# SIMPLE BOOLEAN CHECK
# ============================================================

async def is_user_allowed(
    bot,
    user_id: int,
    group_id: int,
    channel_id: int,
) -> bool:
    """
    Return True only when the user joined both chats.
    """

    group_ok = await check_membership(
        bot,
        group_id,
        user_id,
    )

    if not group_ok:
        return False

    channel_ok = await check_membership(
        bot,
        channel_id,
        user_id,
    )

    return channel_ok


# ============================================================
# COMMAND PROTECTION HELPER
# ============================================================

async def require_join(
    bot,
    user_id: int,
    group_id: int,
    channel_id: int,
) -> tuple[bool, JoinResult]:
    """
    Common helper for protected user commands.

    Example commands:
        /harem
        /search
        /profile
        /market
        /daily
        /Nexus
        etc.
    """

    result = await check_required_chats(
        bot=bot,
        user_id=user_id,
        group_id=group_id,
        channel_id=channel_id,
        group_link="",
        channel_link="",
    )

    return result.passed, result


# ============================================================
# EXPORT
# ============================================================

__all__ = [
    "JoinResult",
    "MEMBER_STATUSES",
    "NOT_MEMBER_STATUSES",

    "is_member_status",
    "check_membership",
    "check_required_chats",

    "build_join_message",
    "build_myanmar_message",
    "build_english_message",

    "get_join_buttons",

    "check_again",
    "is_user_allowed",
    "require_join",
]
