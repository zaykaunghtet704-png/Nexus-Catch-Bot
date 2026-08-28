"""
NEXUS CARD BOT
Access Control System
Version 4

Rules:
- Group must have at least 50 members
- Bot must be an administrator
- Group must be approved by Owner
- Required Group + Channel join
- Group installation logging
- Myanmar / English messages
"""

import sqlite3
from datetime import datetime, timezone
from html import escape

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import ContextTypes

from config import (
    DATABASE_PATH,
    OWNER_ID,
    ADMIN_IDS,
    MIN_GROUP_MEMBERS,
    BOT_MUST_BE_ADMIN,
    GROUP_OWNER_APPROVAL_REQUIRED,
    REQUIRED_GROUP_LINK,
    REQUIRED_CHANNEL_LINK,
    GROUP_LOG_CHAT_ID,
    OWNER_LOG_CHAT_ID,
)


# ============================================================
# DATABASE
# ============================================================

def connect_db():
    return sqlite3.connect(
        DATABASE_PATH
    )


def init_access_database():
    """
    Create access-control tables.
    """

    db = connect_db()

    try:

        db.execute(
            """
            CREATE TABLE IF NOT EXISTS group_access (
                chat_id INTEGER PRIMARY KEY,
                title TEXT,
                username TEXT,
                added_by INTEGER,
                added_by_name TEXT,
                member_count INTEGER DEFAULT 0,
                status TEXT DEFAULT 'pending',
                created_at TEXT,
                approved_at TEXT,
                approved_by INTEGER
            )
            """
        )

        db.commit()

    finally:
        db.close()


# ============================================================
# INITIALIZE
# ============================================================

init_access_database()


# ============================================================
# TIME
# ============================================================

def now_utc():
    return datetime.now(
        timezone.utc
    ).isoformat()


# ============================================================
# OWNER / ADMIN
# ============================================================

def is_owner(user_id):
    try:
        return int(user_id) == int(OWNER_ID)
    except (TypeError, ValueError):
        return False


def is_admin(user_id):
    try:
        return (
            int(user_id) in ADMIN_IDS
        )
    except (TypeError, ValueError):
        return False


def is_owner_or_admin(user_id):
    return (
        is_owner(user_id)
        or is_admin(user_id)
    )


# ============================================================
# GROUP STATUS
# ============================================================

def get_group_access(chat_id):

    db = connect_db()

    try:

        row = db.execute(
            """
            SELECT
                chat_id,
                title,
                username,
                added_by,
                added_by_name,
                member_count,
                status,
                created_at,
                approved_at,
                approved_by
            FROM group_access
            WHERE chat_id = ?
            """,
            (int(chat_id),),
        ).fetchone()

        if not row:
            return None

        return {
            "chat_id": row[0],
            "title": row[1],
            "username": row[2],
            "added_by": row[3],
            "added_by_name": row[4],
            "member_count": row[5],
            "status": row[6],
            "created_at": row[7],
            "approved_at": row[8],
            "approved_by": row[9],
        }

    finally:
        db.close()


# ============================================================
# REGISTER GROUP
# ============================================================

def register_group(
    chat_id,
    title,
    username,
    added_by,
    added_by_name,
    member_count,
):

    db = connect_db()

    try:

        existing = db.execute(
            """
            SELECT chat_id
            FROM group_access
            WHERE chat_id = ?
            """,
            (int(chat_id),),
        ).fetchone()

        if existing:

            db.execute(
                """
                UPDATE group_access
                SET
                    title = ?,
                    username = ?,
                    added_by = ?,
                    added_by_name = ?,
                    member_count = ?
                WHERE chat_id = ?
                """,
                (
                    title,
                    username,
                    added_by,
                    added_by_name,
                    member_count,
                    int(chat_id),
                ),
            )

        else:

            db.execute(
                """
                INSERT INTO group_access (
                    chat_id,
                    title,
                    username,
                    added_by,
                    added_by_name,
                    member_count,
                    status,
                    created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    int(chat_id),
                    title,
                    username,
                    added_by,
                    added_by_name,
                    member_count,
                    "pending",
                    now_utc(),
                ),
            )

        db.commit()

    finally:
        db.close()


# ============================================================
# UPDATE MEMBER COUNT
# ============================================================

def update_member_count(
    chat_id,
    member_count,
):

    db = connect_db()

    try:

        db.execute(
            """
            UPDATE group_access
            SET member_count = ?
            WHERE chat_id = ?
            """,
            (
                int(member_count),
                int(chat_id),
            ),
        )

        db.commit()

    finally:
        db.close()


# ============================================================
# APPROVE GROUP
# ============================================================

def approve_group(
    chat_id,
    approved_by,
):

    db = connect_db()

    try:

        db.execute(
            """
            UPDATE group_access
            SET
                status = 'approved',
                approved_at = ?,
                approved_by = ?
            WHERE chat_id = ?
            """,
            (
                now_utc(),
                int(approved_by),
                int(chat_id),
            ),
        )

        db.commit()

    finally:
        db.close()


# ============================================================
# REJECT GROUP
# ============================================================

def reject_group(
    chat_id,
    rejected_by,
):

    db = connect_db()

    try:

        db.execute(
            """
            UPDATE group_access
            SET
                status = 'rejected',
                approved_at = NULL,
                approved_by = ?
            WHERE chat_id = ?
            """,
            (
                int(rejected_by),
                int(chat_id),
            ),
        )

        db.commit()

    finally:
        db.close()


# ============================================================
# DISABLE GROUP
# ============================================================

def disable_group(
    chat_id,
):

    db = connect_db()

    try:

        db.execute(
            """
            UPDATE group_access
            SET status = 'disabled'
            WHERE chat_id = ?
            """,
            (int(chat_id),),
        )

        db.commit()

    finally:
        db.close()


# ============================================================
# ENABLE GROUP
# ============================================================

def enable_group(
    chat_id,
):

    db = connect_db()

    try:

        db.execute(
            """
            UPDATE group_access
            SET status = 'approved'
            WHERE chat_id = ?
            """,
            (int(chat_id),),
        )

        db.commit()

    finally:
        db.close()


# ============================================================
# IS APPROVED
# ============================================================

def is_group_approved(
    chat_id,
):

    data = get_group_access(
        chat_id
    )

    if not data:
        return False

    return data["status"] == "approved"


# ============================================================
# CHECK BOT ADMIN
# ============================================================

async def bot_is_admin(
    context,
    chat_id,
):

    try:

        me = await context.bot.get_me()

        member = await context.bot.get_chat_member(
            chat_id,
            me.id,
        )

        return member.status in (
            "administrator",
            "creator",
        )

    except Exception:

        return False


# ============================================================
# CHECK USER JOIN
# ============================================================

async def user_joined_chat(
    context,
    chat_id,
    user_id,
):

    try:

        member = await context.bot.get_chat_member(
            chat_id,
            user_id,
        )

        return member.status not in (
            "left",
            "kicked",
        )

    except Exception:

        return False


# ============================================================
# REQUIRED JOIN CHECK
# ============================================================

async def check_required_joins(
    context,
    user_id,
):

    """
    REQUIRED_GROUP_ID / REQUIRED_CHANNEL_ID
    can be added to config later.

    If IDs are not configured, this check returns True
    instead of breaking the whole bot.
    """

    try:

        from config import (
            REQUIRED_GROUP_ID,
            REQUIRED_CHANNEL_ID,
        )

    except ImportError:

        return True

    # --------------------------------------------------------
    # Group
    # --------------------------------------------------------

    if REQUIRED_GROUP_ID:

        group_ok = await user_joined_chat(
            context,
            REQUIRED_GROUP_ID,
            user_id,
        )

        if not group_ok:
            return False

    # --------------------------------------------------------
    # Channel
    # --------------------------------------------------------

    if REQUIRED_CHANNEL_ID:

        channel_ok = await user_joined_chat(
            context,
            REQUIRED_CHANNEL_ID,
            user_id,
        )

        if not channel_ok:
            return False

    return True


# ============================================================
# GROUP MEMBER COUNT
# ============================================================

async def get_group_member_count(
    context,
    chat_id,
):

    try:

        return await context.bot.get_chat_member_count(
            chat_id
        )

    except Exception:

        return 0


# ============================================================
# COMPLETE GROUP CHECK
# ============================================================

async def check_group_access(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    message = update.effective_message

    if not message:
        return False

    chat = update.effective_chat
    user = update.effective_user

    if not chat or not user:
        return False

    # Private chat doesn't need group rules
    if chat.type == "private":
        return True

    if chat.type not in (
        "group",
        "supergroup",
    ):
        return False

    chat_id = chat.id

    # --------------------------------------------------------
    # Member count
    # --------------------------------------------------------

    member_count = await get_group_member_count(
        context,
        chat_id,
    )

    update_member_count(
        chat_id,
        member_count,
    )

    if member_count < MIN_GROUP_MEMBERS:

        await message.reply_text(
            "🚫 <b>NEXUS CARD BOT</b>\n\n"
            f"👥 ဒီ Group မှာ Member "
            f"အနည်းဆုံး <b>{MIN_GROUP_MEMBERS}</b> ယောက် "
            "ရှိရပါမယ်။\n\n"
            f"📊 လက်ရှိ Member: <b>{member_count}</b>",
            parse_mode="HTML",
        )

        return False

    # --------------------------------------------------------
    # Bot admin
    # --------------------------------------------------------

    if BOT_MUST_BE_ADMIN:

        admin_ok = await bot_is_admin(
            context,
            chat_id,
        )

        if not admin_ok:

            await message.reply_text(
                "🤖 <b>NEXUS CARD BOT</b>\n\n"
                "🚫 Bot ကို ဒီ Group မှာ "
                "<b>Administrator</b> ပေးထားရပါမယ်။\n\n"
                "ပြီးရင် Command ကို ပြန်အသုံးပြုပါ။",
                parse_mode="HTML",
            )

            return False

    # --------------------------------------------------------
    # Database registration
    # --------------------------------------------------------

    username = getattr(
        chat,
        "username",
        None,
    )

    register_group(
        chat_id=chat_id,
        title=chat.title or "Unknown Group",
        username=username,
        added_by=user.id,
        added_by_name=(
            user.full_name
            or "Unknown"
        ),
        member_count=member_count,
    )

    # --------------------------------------------------------
    # Approval
    # --------------------------------------------------------

    if GROUP_OWNER_APPROVAL_REQUIRED:

        if not is_group_approved(
            chat_id
        ):

            await message.reply_text(
                "🔒 <b>NEXUS CARD BOT</b>\n\n"
                "⏳ ဒီ Group ကို Owner က "
                "<b>Approve</b> လုပ်ပေးပြီးမှ "
                "Bot ကို အသုံးပြုနိုင်ပါတယ်။\n\n"
                "📩 Owner ကို အကြောင်းကြားပေးပါ။",
                parse_mode="HTML",
            )

            return False

    # --------------------------------------------------------
    # Required joins
    # --------------------------------------------------------

    joined = await check_required_joins(
        context,
        user.id,
    )

    if not joined:

        keyboard = [
            [
                InlineKeyboardButton(
                    "👥 Join Group",
                    url=REQUIRED_GROUP_LINK,
                )
            ],
            [
                InlineKeyboardButton(
                    "📢 Join Channel",
                    url=REQUIRED_CHANNEL_LINK,
                )
            ],
            [
                InlineKeyboardButton(
                    "✅ Check Again",
                    callback_data=(
                        f"access_check:{user.id}"
                    ),
                )
            ],
        ]

        await message.reply_text(
            "🔐 <b>NEXUS CARD BOT</b>\n\n"
            "Bot ကို အသုံးပြုရန် "
            "အောက်ပါ Group နှင့် Channel ကို "
            "<b>Join</b> လုပ်ထားရပါမယ်။\n\n"
            "1️⃣ Group Join\n"
            "2️⃣ Channel Join\n"
            "3️⃣ ပြီးရင် Check Again နှိပ်ပါ။",
            reply_markup=InlineKeyboardMarkup(
                keyboard
            ),
            parse_mode="HTML",
        )

        return False

    return True


# ============================================================
# BOT ADDED TO GROUP
# ============================================================

async def handle_bot_added_to_group(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    message = update.effective_message

    if not message:
        return

    chat = update.effective_chat

    if not chat:
        return

    if chat.type not in (
        "group",
        "supergroup",
    ):
        return

    # --------------------------------------------------------
    # Find who added bot
    # --------------------------------------------------------

    added_by = None

    if message.new_chat_members:

        for member in message.new_chat_members:

            try:

                me = await context.bot.get_me()

                if member.id == me.id:

                    added_by = (
                        message.from_user
                    )

                    break

            except Exception:
                pass

    if not added_by:
        return

    # --------------------------------------------------------
    # Member count
    # --------------------------------------------------------

    member_count = await get_group_member_count(
        context,
        chat.id,
    )

    # --------------------------------------------------------
    # Register
    # --------------------------------------------------------

    register_group(
        chat_id=chat.id,
        title=chat.title or "Unknown Group",
        username=getattr(
            chat,
            "username",
            None,
        ),
        added_by=added_by.id,
        added_by_name=(
            added_by.full_name
            or "Unknown"
        ),
        member_count=member_count,
    )

    # --------------------------------------------------------
    # Group message
    # --------------------------------------------------------

    await message.reply_text(
        "🎴 <b>NEXUS CARD BOT</b>\n\n"
        "👋 Hello! ကျွန်တော်ကို "
        "ဒီ Group ထဲ ထည့်ပေးလိုက်ပါပြီ။\n\n"
        f"👥 Members: <b>{member_count}</b>\n"
        f"📌 လိုအပ်ချက်: <b>{MIN_GROUP_MEMBERS}</b> Members\n\n"
        "🤖 Bot ကို Administrator ပေးထားရပါမယ်။\n"
        "🔐 Owner Approval ရပြီးမှ "
        "Card System ကို အသုံးပြုနိုင်ပါမယ်။\n\n"
        "📩 Owner ကို အကြောင်းကြားပေးပါ။",
        parse_mode="HTML",
    )

    # --------------------------------------------------------
    # Owner / Log notification
    # --------------------------------------------------------

    await send_group_install_log(
        context,
        chat,
        added_by,
        member_count,
    )


# ============================================================
# INSTALL LOG
# ============================================================

async def send_group_install_log(
    context,
    chat,
    added_by,
    member_count,
):

    title = escape(
        chat.title
        or "Unknown Group"
    )

    username = getattr(
        chat,
        "username",
        None,
    )

    username_text = (
        f"@{escape(username)}"
        if username
        else "Private Group"
    )

    user_name = escape(
        added_by.full_name
        or "Unknown"
    )

    user_id = added_by.id

    text = (
        "🚨 <b>NEXUS BOT INSTALLED</b>\n\n"
        f"👥 Group: <b>{title}</b>\n"
        f"🆔 Group ID: <code>{chat.id}</code>\n"
        f"🔗 Username: {username_text}\n\n"
        f"👤 Added By: <b>{user_name}</b>\n"
        f"🆔 User ID: <code>{user_id}</code>\n\n"
        f"👥 Members: <b>{member_count}</b>\n"
        f"📌 Required: <b>{MIN_GROUP_MEMBERS}</b>\n"
        f"🔐 Status: <b>Pending Approval</b>"
    )

    destinations = set()

    if GROUP_LOG_CHAT_ID:
        destinations.add(
            int(GROUP_LOG_CHAT_ID)
        )

    if OWNER_LOG_CHAT_ID:
        destinations.add(
            int(OWNER_LOG_CHAT_ID)
        )

    if OWNER_ID:
        destinations.add(
            int(OWNER_ID)
        )

    for destination in destinations:

        try:

            await context.bot.send_message(
                chat_id=destination,
                text=text,
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton(
                            "✅ Approve",
                            callback_data=(
                                f"approve_group:{chat.id}"
                            ),
                        ),
                        InlineKeyboardButton(
                            "❌ Reject",
                            callback_data=(
                                f"reject_group:{chat.id}"
                            ),
                        ),
                    ],
                    [
                        InlineKeyboardButton(
                            "🚫 Disable",
                            callback_data=(
                                f"disable_group:{chat.id}"
                            ),
                        ),
                    ],
                ]),
            )

        except Exception:
            pass


# ============================================================
# OWNER: GROUP LIST
# ============================================================

async def groups_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    user = update.effective_user
    message = update.effective_message

    if not user or not message:
        return

    if not is_owner_or_admin(
        user.id
    ):

        await message.reply_text(
            "🚫 Owner/Admin only."
        )

        return

    db = connect_db()

    try:

        rows = db.execute(
            """
            SELECT
                chat_id,
                title,
                member_count,
                status
            FROM group_access
            ORDER BY created_at DESC
            """
        ).fetchall()

    finally:
        db.close()

    if not rows:

        await message.reply_text(
            "📭 Registered Group မရှိသေးပါ။"
        )

        return

    text = (
        "👥 <b>NEXUS GROUPS</b>\n\n"
    )

    for index, row in enumerate(
        rows,
        start=1,
    ):

        chat_id = row[0]
        title = escape(
            row[1] or "Unknown"
        )
        members = row[2]
        status = row[3]

        if status == "approved":
            icon = "🟢"
        elif status == "pending":
            icon = "🟡"
        elif status == "rejected":
            icon = "🔴"
        else:
            icon = "⚫"

        text += (
            f"{index}. {icon} <b>{title}</b>\n"
            f"   🆔 <code>{chat_id}</code>\n"
            f"   👥 {members} members\n"
            f"   📌 {status}\n\n"
        )

    await message.reply_text(
        text,
        parse_mode="HTML",
    )


# ============================================================
# OWNER CALLBACK
# ============================================================

async def access_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    query = update.callback_query

    if not query:
        return

    user = query.from_user

    data = query.data or ""

    # --------------------------------------------------------
    # Check join
    # --------------------------------------------------------

    if data.startswith(
        "access_check:"
    ):

        try:

            owner_id = int(
                data.split(
                    ":",
                    1,
                )[1]
            )

        except ValueError:

            await query.answer(
                "Invalid request.",
                show_alert=True,
            )

            return

        if user.id != owner_id:

            await query.answer(
                "🚫 ဒီ button ကို မင်းသုံးလို့မရပါ။",
                show_alert=True,
            )

            return

        joined = await check_required_joins(
            context,
            user.id,
        )

        if joined:

            await query.answer(
                "✅ Verified!",
            )

            try:

                await query.edit_message_text(
                    "✅ <b>Verified Successfully!</b>\n\n"
                    "🎴 Nexus Card Bot ကို "
                    "ဆက်လက်အသုံးပြုနိုင်ပါပြီ။",
                    parse_mode="HTML",
                )

            except Exception:
                pass

        else:

            await query.answer(
                "❌ Join မပြီးသေးပါ။",
                show_alert=True,
            )

        return

    # --------------------------------------------------------
    # Owner check
    # --------------------------------------------------------

    if not is_owner_or_admin(
        user.id
    ):

        await query.answer(
            "🚫 Owner/Admin only.",
            show_alert=True,
        )

        return

    # --------------------------------------------------------
    # Approve
    # --------------------------------------------------------

    if data.startswith(
        "approve_group:"
    ):

        try:

            chat_id = int(
                data.split(
                    ":",
                    1,
                )[1]
            )

        except ValueError:

            await query.answer(
                "Invalid group.",
                show_alert=True,
            )

            return

        approve_group(
            chat_id,
            user.id,
        )

        await query.answer(
            "✅ Group approved!",
        )

        try:

            await context.bot.send_message(
                chat_id=chat_id,
                text=(
                    "🎉 <b>NEXUS CARD BOT</b>\n\n"
                    "✅ ဒီ Group ကို Owner က "
                    "<b>APPROVE</b> လုပ်ပေးပြီးပါပြီ။\n\n"
                    "🎴 Card System ကို စတင်အသုံးပြုနိုင်ပါပြီ။\n"
                    "📖 <code>/help</code> ကိုနှိပ်ပြီး "
                    "Commands အားလုံးကြည့်နိုင်ပါတယ်။"
                ),
                parse_mode="HTML",
            )

        except Exception:
            pass

        try:

            await query.edit_message_reply_markup(
                reply_markup=None
            )

        except Exception:
            pass

        return

    # --------------------------------------------------------
    # Reject
    # --------------------------------------------------------

    if data.startswith(
        "reject_group:"
    ):

        try:

            chat_id = int(
                data.split(
                    ":",
                    1,
                )[1]
            )

        except ValueError:

            await query.answer(
                "Invalid group.",
                show_alert=True,
            )

            return

        reject_group(
            chat_id,
            user.id,
        )

        await query.answer(
            "❌ Group rejected.",
        )

        try:

            await context.bot.send_message(
                chat_id=chat_id,
                text=(
                    "❌ <b>NEXUS CARD BOT</b>\n\n"
                    "ဒီ Group ရဲ့ Bot အသုံးပြုခွင့်ကို "
                    "Owner မှ <b>REJECT</b> လုပ်ထားပါတယ်။"
                ),
                parse_mode="HTML",
            )

        except Exception:
            pass

        try:

            await query.edit_message_reply_markup(
                reply_markup=None
            )

        except Exception:
            pass

        return

    # --------------------------------------------------------
    # Disable
    # --------------------------------------------------------

    if data.startswith(
        "disable_group:"
    ):

        try:

            chat_id = int(
                data.split(
                    ":",
                    1,
                )[1]
            )

        except ValueError:

            await query.answer(
                "Invalid group.",
                show_alert=True,
            )

            return

        disable_group(
            chat_id
        )

        await query.answer(
            "🚫 Group disabled.",
        )

        try:

            await context.bot.send_message(
                chat_id=chat_id,
                text=(
                    "🚫 <b>NEXUS CARD BOT</b>\n\n"
                    "ဒီ Group မှာ Bot အသုံးပြုခွင့်ကို "
                    "<b>DISABLED</b> လုပ်ထားပါတယ်။"
                ),
                parse_mode="HTML",
            )

        except Exception:
            pass

        try:

            await query.edit_message_reply_markup(
                reply_markup=None
            )

        except Exception:
            pass

        return

    await query.answer()
