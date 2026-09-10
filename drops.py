# ============================================================
# Nexus Catch Bot - drop.py
# Main SQLite Drop System
# Manual Drop / Auto Drop / Weighted Drop / First Click Claim
# ============================================================

from __future__ import annotations

import random
import time
from typing import Optional

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from config import BOT_NAME
from database import (
    get_all_cards,
    get_card,
    add_user_card,
    get_db,
)


# ============================================================
# DEFAULT SETTINGS
# ============================================================

DEFAULT_DROP_TIME = 85
BETTER_DROP_TIME = 1000
DROP_EXPIRE_SECONDS = 120


# ============================================================
# IN-MEMORY SETTINGS
# ============================================================

_drop_time = DEFAULT_DROP_TIME
_better_drop_time = BETTER_DROP_TIME


# ============================================================
# HELPERS
# ============================================================

def get_drop_time() -> int:
    return _drop_time


def get_better_drop_time() -> int:
    return _better_drop_time


def set_drop_time(seconds: int) -> int:
    global _drop_time

    seconds = max(1, int(seconds))
    _drop_time = seconds

    return _drop_time


def set_better_drop_time(seconds: int) -> int:
    global _better_drop_time

    seconds = max(
        _drop_time,
        int(seconds),
    )

    _better_drop_time = seconds

    return _better_drop_time


def reset_drop_time() -> None:
    global _drop_time
    global _better_drop_time

    _drop_time = DEFAULT_DROP_TIME
    _better_drop_time = BETTER_DROP_TIME


def _safe_int(value, default=0):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _safe_float(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _card_value(card, key, default=None):
    try:
        return card[key]
    except Exception:
        return default


# ============================================================
# CARD SELECTION
# ============================================================

def choose_random_card(
    better: bool = False,
):
    """
    Select a card using drop_weight.

    Better drops slightly increase the chance of higher-value
    editions without removing normal cards completely.
    """

    cards = get_all_cards()

    if not cards:
        return None

    valid_cards = []

    for card in cards:

        try:
            active = card["active"]
        except Exception:
            active = 1

        if active == 0:
            continue

        valid_cards.append(card)

    if not valid_cards:
        return None

    weighted_cards = []
    weights = []

    for card in valid_cards:

        rarity = str(
            _card_value(card, "rarity", "Common")
        ).strip().lower()

        edition = str(
            _card_value(card, "edition", "Common")
        ).strip().lower()

        base_weight = max(
            0.01,
            _safe_float(
                _card_value(
                    card,
                    "drop_weight",
                    1,
                ),
                1,
            ),
        )

        # Better drop modifier.
        if better:

            if (
                rarity in {
                    "premium",
                    "eternal",
                    "immortal",
                    "celestial",
                    "supreme",
                    "cataphract",
                    "crossverse",
                    "divine",
                    "mythical",
                    "legends",
                }
                or edition in {
                    "premium",
                    "eternal",
                    "immortal",
                    "celestial",
                    "supreme",
                    "cataphract",
                    "crossverse",
                    "divine",
                    "mythical",
                    "legends",
                }
            ):
                base_weight *= 4.0

            elif rarity in {
                "rare",
                "uncommon",
            }:
                base_weight *= 2.0

        weighted_cards.append(card)
        weights.append(base_weight)

    if not weighted_cards:
        return None

    try:
        return random.choices(
            weighted_cards,
            weights=weights,
            k=1,
        )[0]
    except Exception:
        return random.choice(
            weighted_cards
        )


# ============================================================
# CREATE DROP DATABASE RECORD
# ============================================================

def _create_drop_record(
    chat_id: int,
    char_id: str,
) -> Optional[int]:

    with get_db() as db:

        cursor = db.execute(
            """
            INSERT INTO drops (
                group_id,
                char_id,
                message_id,
                claimed_by,
                claimed,
                created_at
            )
            VALUES (?, ?, 0, 0, 0, ?)
            """,
            (
                int(chat_id),
                str(char_id),
                time.time(),
            ),
        )

        return cursor.lastrowid


# ============================================================
# CREATE DROP
# ============================================================

async def create_drop(
    message,
    context: Optional[ContextTypes.DEFAULT_TYPE] = None,
    *,
    card_id: Optional[str] = None,
    better: bool = False,
    expire_seconds: int = DROP_EXPIRE_SECONDS,
):
    """
    Send a card drop.

    Card is NOT immediately given to the command sender.

    The first user who successfully presses GET CARD wins.
    """

    if message is None:
        return None

    chat = message.chat

    if chat is None:
        return None

    # --------------------------------------------------------
    # SELECT CARD
    # --------------------------------------------------------

    if card_id:

        card = get_card(
            str(card_id).strip()
        )

        if not card:

            await message.reply_text(
                "❌ ဒီ Card ID ကို မတွေ့ပါ။"
            )

            return None

    else:

        card = choose_random_card(
            better=better
        )

    if not card:

        await message.reply_text(
            "❌ Card database ထဲမှာ Drop လုပ်လို့ရတဲ့ Card မရှိသေးပါ။"
        )

        return None

    char_id = str(
        _card_value(
            card,
            "char_id",
            "",
        )
    )

    if not char_id:

        await message.reply_text(
            "❌ Card ID မရှိတဲ့ Card ဖြစ်နေပါတယ်။"
        )

        return None

    # --------------------------------------------------------
    # CREATE DATABASE DROP
    # --------------------------------------------------------

    drop_id = _create_drop_record(
        chat.id,
        char_id,
    )

    if not drop_id:

        await message.reply_text(
            "❌ Drop record ဖန်တီးလို့မရပါ။"
        )

        return None

    # --------------------------------------------------------
    # BUTTON
    # --------------------------------------------------------

    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "🎴 GET CARD",
                    callback_data=f"drop:{drop_id}",
                )
            ]
        ]
    )

    # --------------------------------------------------------
    # TEXT
    # --------------------------------------------------------

    name = str(
        _card_value(
            card,
            "name",
            "Unknown",
        )
    )

    edition = str(
        _card_value(
            card,
            "edition",
            "Common",
        )
    )

    rarity = str(
        _card_value(
            card,
            "rarity",
            "Common",
        )
    )

    atk = _safe_int(
        _card_value(card, "atk", 0)
    )

    defense = _safe_int(
        _card_value(card, "defense", 0)
    )

    hp = _safe_int(
        _card_value(card, "hp", 0)
    )

    speed = _safe_int(
        _card_value(card, "speed", 0)
    )

    description = str(
        _card_value(
            card,
            "description",
            "",
        )
        or ""
    )

    text = (
        f"✨ <b>{BOT_NAME} CARD DROP!</b> ✨\n\n"
        f"🎴 <b>{name}</b>\n"
        f"🆔 <code>{char_id}</code>\n"
        f"💎 Edition: <b>{edition}</b>\n"
        f"⭐ Rarity: <b>{rarity}</b>\n\n"
        f"⚔️ ATK: <b>{atk}</b>\n"
        f"🛡️ DEF: <b>{defense}</b>\n"
        f"❤️ HP: <b>{hp}</b>\n"
        f"💨 Speed: <b>{speed}</b>\n"
    )

    if description:
        text += (
            f"\n📖 {description}\n"
        )

    text += (
        "\n⚡ <b>FIRST CLICK WINS!</b>\n"
        "🎴 GET CARD ကို အမြန်နှိပ်ပါ!\n"
        f"⏳ Drop Time: <b>{expire_seconds}s</b>"
    )

    # --------------------------------------------------------
    # SEND TELEGRAM MESSAGE
    # --------------------------------------------------------

    sent = None

    media_type = str(
        _card_value(
            card,
            "media_type",
            "photo",
        )
        or "photo"
    ).lower()

    video_file_id = (
        _card_value(
            card,
            "video_file_id",
            "",
        )
        or ""
    )

    image_file_id = (
        _card_value(
            card,
            "image_file_id",
            "",
        )
        or ""
    )

    try:

        if (
            media_type == "video"
            and video_file_id
        ):

            sent = await message.reply_video(
                video=video_file_id,
                caption=text,
                reply_markup=keyboard,
                parse_mode="HTML",
            )

        elif image_file_id:

            sent = await message.reply_photo(
                photo=image_file_id,
                caption=text,
                reply_markup=keyboard,
                parse_mode="HTML",
            )

        else:

            sent = await message.reply_text(
                text,
                reply_markup=keyboard,
                parse_mode="HTML",
            )

    except Exception as exc:

        # Telegram send failed.
        # Remove unused drop record.
        with get_db() as db:

            db.execute(
                """
                DELETE FROM drops
                WHERE id = ?
                  AND claimed = 0
                """,
                (drop_id,),
            )

        await message.reply_text(
            "❌ Drop ပို့ရာမှာ Error ဖြစ်သွားပါတယ်။"
        )

        print(
            f"[DROP SEND ERROR] {exc}"
        )

        return None

    # --------------------------------------------------------
    # SAVE MESSAGE ID
    # --------------------------------------------------------

    if sent:

        with get_db() as db:

            db.execute(
                """
                UPDATE drops
                SET message_id = ?
                WHERE id = ?
                """,
                (
                    sent.message_id,
                    drop_id,
                ),
            )

    return drop_id


# ============================================================
# MANUAL DROP
# ============================================================

async def manual_drop(
    message,
    card_id: Optional[str] = None,
    better: bool = False,
):
    return await create_drop(
        message,
        None,
        card_id=card_id,
        better=better,
    )


# ============================================================
# FIRST CLICK CLAIM
# ============================================================

async def claim_drop_callback(
    update,
    context: ContextTypes.DEFAULT_TYPE,
):

    query = update.callback_query

    if not query:
        return

    data = query.data or ""

    if not data.startswith(
        "drop:"
    ):
        return

    try:

        drop_id = int(
            data.split(
                ":",
                1,
            )[1]
        )

    except (
        ValueError,
        IndexError,
    ):

        await query.answer(
            "❌ Invalid Drop.",
            show_alert=True,
        )

        return

    user = query.from_user

    if not user:

        await query.answer(
            "❌ User not found.",
            show_alert=True,
        )

        return

    user_id = int(
        user.id
    )

    chat_id = (
        query.message.chat.id
        if query.message
        else None
    )

    # --------------------------------------------------------
    # ATOMIC FIRST CLICK
    # --------------------------------------------------------

    with get_db() as db:

        drop = db.execute(
            """
            SELECT *
            FROM drops
            WHERE id = ?
            """,
            (drop_id,),
        ).fetchone()

        if not drop:

            await query.answer(
                "❌ ဒီ Drop မရှိတော့ပါ။",
                show_alert=True,
            )

            return

        # Group protection
        if (
            chat_id is not None
            and int(drop["group_id"])
            != int(chat_id)
        ):

            await query.answer(
                "❌ ဒီ Drop က ဒီ Group အတွက်မဟုတ်ပါ။",
                show_alert=True,
            )

            return

        # Expiry
        created_at = _safe_float(
            drop["created_at"],
            time.time(),
        )

        if (
            time.time()
            - created_at
            > DROP_EXPIRE_SECONDS
        ):

            db.execute(
                """
                UPDATE drops
                SET claimed = 1
                WHERE id = ?
                  AND claimed = 0
                """,
                (drop_id,),
            )

            await query.answer(
                "⏰ Drop Expired!",
                show_alert=True,
            )

            return

        # Already claimed
        if int(
            drop["claimed"] or 0
        ):

            await query.answer(
                "😢 နောက်ကျသွားပါပြီ!\n"
                "ဒီ Card ကို တစ်ယောက်ယောက် ရသွားပါပြီ။",
                show_alert=True,
            )

            return

        # ----------------------------------------------------
        # ATOMIC UPDATE
        # ----------------------------------------------------

        cursor = db.execute(
            """
            UPDATE drops
            SET claimed = 1,
                claimed_by = ?
            WHERE id = ?
              AND claimed = 0
            """,
            (
                user_id,
                drop_id,
            ),
        )

        # Only one callback can reach here.
        if cursor.rowcount != 1:

            await query.answer(
                "😢 နောက်ကျသွားပါပြီ!",
                show_alert=True,
            )

            return

        char_id = str(
            drop["char_id"]
        )

    # --------------------------------------------------------
    # GET CARD
    # --------------------------------------------------------

    card = get_card(
        char_id
    )

    if not card:

        # Roll back if card somehow disappeared.
        with get_db() as db:

            db.execute(
                """
                UPDATE drops
                SET claimed = 0,
                    claimed_by = 0
                WHERE id = ?
                  AND claimed = 1
                """,
                (drop_id,),
            )

        await query.answer(
            "❌ Card data မတွေ့ပါ။",
            show_alert=True,
        )

        return

    # --------------------------------------------------------
    # ADD TO USER COLLECTION
    # --------------------------------------------------------

    try:

        add_user_card(
            user_id,
            char_id,
        )

    except Exception as exc:

        # Rollback claim if collection insert fails.
        with get_db() as db:

            db.execute(
                """
                UPDATE drops
                SET claimed = 0,
                    claimed_by = 0
                WHERE id = ?
                  AND claimed = 1
                  AND claimed_by = ?
                """,
                (
                    drop_id,
                    user_id,
                ),
            )

        print(
            f"[DROP CLAIM ERROR] {exc}"
        )

        await query.answer(
            "❌ Card သိမ်းရာမှာ Error ဖြစ်သွားပါတယ်။",
            show_alert=True,
        )

        return

    # --------------------------------------------------------
    # WINNER NAME
    # --------------------------------------------------------

    if user.username:

        winner_name = (
            f"@{user.username}"
        )

    else:

        winner_name = (
            user.first_name
            or "Unknown"
        )

    name = str(
        _card_value(
            card,
            "name",
            "Unknown",
        )
    )

    edition = str(
        _card_value(
            card,
            "edition",
            "Common",
        )
    )

    rarity = str(
        _card_value(
            card,
            "rarity",
            "Common",
        )
    )

    price = _safe_int(
        _card_value(
            card,
            "price",
            0,
        )
    )

    # --------------------------------------------------------
    # RESULT MESSAGE
    # --------------------------------------------------------

    result_text = (
        "🎉 <b>CARD CLAIMED!</b>\n\n"
        f"👤 Winner: <b>{winner_name}</b>\n\n"
        f"🎴 <b>{name}</b>\n"
        f"🆔 <code>{char_id}</code>\n"
        f"💎 Edition: <b>{edition}</b>\n"
        f"⭐ Rarity: <b>{rarity}</b>\n"
        f"💰 Price: <b>{price:,}</b> Coins\n\n"
        "🏆 Congratulations!\n"
        "✨ Card has been added to your collection."
    )

    # --------------------------------------------------------
    # REMOVE GET CARD BUTTON
    # --------------------------------------------------------

    try:

        if query.message:

            # Photo / video messages use caption.
            if (
                query.message.photo
                or query.message.video
            ):

                await query.edit_message_caption(
                    caption=result_text,
                    reply_markup=None,
                    parse_mode="HTML",
                )

            else:

                await query.edit_message_text(
                    text=result_text,
                    reply_markup=None,
                    parse_mode="HTML",
                )

    except Exception as exc:

        print(
            f"[DROP EDIT ERROR] {exc}"
        )

    await query.answer(
        "🎉 Card ရပါပြီ!",
        show_alert=True,
    )


# ============================================================
# GET DROP
# ============================================================

def get_drop_card(
    drop_id: int,
):

    with get_db() as db:

        return db.execute(
            """
            SELECT *
            FROM drops
            WHERE id = ?
            """,
            (int(drop_id),),
        ).fetchone()


# ============================================================
# CANCEL DROP
# ============================================================

def cancel_drop(
    drop_id: int,
) -> bool:

    with get_db() as db:

        cursor = db.execute(
            """
            UPDATE drops
            SET claimed = 1
            WHERE id = ?
              AND claimed = 0
            """,
            (int(drop_id),),
        )

        return cursor.rowcount == 1


# ============================================================
# CLEAN OLD DROPS
# ============================================================

def cleanup_old_drops(
    max_age_seconds: int = 3600,
) -> int:

    cutoff = (
        time.time()
        - max(
            1,
            int(max_age_seconds),
        )
    )

    with get_db() as db:

        cursor = db.execute(
            """
            UPDATE drops
            SET claimed = 1
            WHERE claimed = 0
              AND created_at < ?
            """,
            (cutoff,),
        )

        return cursor.rowcount


# ============================================================
# AUTO DROP MESSAGE COUNTER
# ============================================================

def get_message_count(
    chat_id: int,
) -> int:

    """
    Message counter is stored in memory.

    bot.py should call increment_message_count()
    for every normal group message.
    """

    if not hasattr(
        get_message_count,
        "_counts",
    ):
        get_message_count._counts = {}

    return get_message_count._counts.get(
        int(chat_id),
        0,
    )


def increment_message_count(
    chat_id: int,
) -> int:

    if not hasattr(
        get_message_count,
        "_counts",
    ):
        get_message_count._counts = {}

    chat_id = int(chat_id)

    count = (
        get_message_count._counts.get(
            chat_id,
            0,
        )
        + 1
    )

    get_message_count._counts[
        chat_id
    ] = count

    return count


def reset_message_count(
    chat_id: int,
) -> None:

    if not hasattr(
        get_message_count,
        "_counts",
    ):
        get_message_count._counts = {}

    get_message_count._counts[
        int(chat_id)
    ] = 0


# ============================================================
# AUTO DROP PROCESS
# ============================================================

async def process_auto_drop(
    message,
    context: Optional[
        ContextTypes.DEFAULT_TYPE
    ] = None,
):
    """
    Call this for each group message.

    85 messages  -> normal drop
    1000 messages -> better drop

    After a drop happens, counter resets.
    """

    if message is None:
        return None

    chat = message.chat

    if not chat:
        return None

    # Only groups/supergroups.
    if chat.type not in {
        "group",
        "supergroup",
    }:
        return None

    count = increment_message_count(
        chat.id
    )

    # Better drop first.
    if (
        count >= _better_drop_time
    ):

        reset_message_count(
            chat.id
        )

        return await create_drop(
            message,
            context,
            better=True,
        )

    # Normal drop.
    if (
        count >= _drop_time
    ):

        reset_message_count(
            chat.id
        )

        return await create_drop(
            message,
            context,
            better=False,
        )

    return None


# ============================================================
# CHANGE TIME
# ============================================================

def change_time(
    normal: int,
    better: Optional[int] = None,
):
    """
    Change auto-drop message thresholds.

    Example:
        change_time(50)
        change_time(50, 500)
    """

    global _drop_time
    global _better_drop_time

    normal = max(
        1,
        int(normal),
    )

    if better is None:

        better = max(
            normal + 1,
            normal * 10,
        )

    better = max(
        normal,
        int(better),
    )

    _drop_time = normal
    _better_drop_time = better

    return (
        _drop_time,
        _better_drop_time,
    )


# ============================================================
# ADMIN ALIASES
# ============================================================

def set_drop_threshold(
    normal: int,
    better: Optional[int] = None,
):
    return change_time(
        normal,
        better,
    )


def admin_set_drop_threshold(
    normal_threshold: int,
    better_threshold: int,
):
    return change_time(
        normal_threshold,
        better_threshold,
    )


async def admin_force_drop(
    message,
    card_id: str,
):
    return await create_drop(
        message,
        None,
        card_id=card_id,
    )


# ============================================================
# DROP STATUS
# ============================================================

def get_drop_status() -> dict:

    return {
        "normal_drop": _drop_time,
        "better_drop": _better_drop_time,
        "expire_seconds": DROP_EXPIRE_SECONDS,
    }


def get_status_text() -> str:

    return (
        "🎴 <b>NEXUS DROP STATUS</b>\n\n"
        f"💬 Normal Drop: "
        f"<b>{_drop_time}</b> messages\n"
        f"🔥 Better Drop: "
        f"<b>{_better_drop_time}</b> messages\n"
        f"⏳ Expiry: "
        f"<b>{DROP_EXPIRE_SECONDS}s</b>"
    )


# ============================================================
# EXPORTS
# ============================================================

__all__ = [
    "DEFAULT_DROP_TIME",
    "BETTER_DROP_TIME",
    "DROP_EXPIRE_SECONDS",

    "get_drop_time",
    "get_better_drop_time",
    "set_drop_time",
    "set_better_drop_time",
    "reset_drop_time",

    "choose_random_card",

    "create_drop",
    "manual_drop",
    "claim_drop_callback",

    "get_drop_card",
    "cancel_drop",
    "cleanup_old_drops",

    "get_message_count",
    "increment_message_count",
    "reset_message_count",

    "process_auto_drop",

    "change_time",
    "set_drop_threshold",
    "admin_set_drop_threshold",
    "admin_force_drop",

    "get_drop_status",
    "get_status_text",
]
