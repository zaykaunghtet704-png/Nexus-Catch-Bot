import random
import time
import logging

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from config import BOT_NAME
from database import (
    get_all_cards,
    get_card,
    add_user_card,
    get_db,
)

logger = logging.getLogger(__name__)


# ============================================================
# CONSTANTS
# ============================================================

DEFAULT_DROP_EXPIRE = 3600


# ============================================================
# CARD SELECTION
# ============================================================

def choose_random_card():
    """
    Select one active card using drop_weight.

    Existing cards are preserved.
    """

    cards = get_all_cards()

    if not cards:
        return None

    valid_cards = []
    weights = []

    for card in cards:
        try:
            weight = float(card["drop_weight"])
        except (TypeError, ValueError):
            weight = 1.0

        if weight <= 0:
            weight = 0.01

        valid_cards.append(card)
        weights.append(weight)

    if not valid_cards:
        return None

    return random.choices(
        valid_cards,
        weights=weights,
        k=1,
    )[0]


# ============================================================
# CREATE DROP
# ============================================================

async def create_drop(
    message,
    context: ContextTypes.DEFAULT_TYPE = None,
):
    """
    Create a new card drop.

    Card is NOT immediately given to anyone.

    The first user who presses GET CARD wins.
    """

    if not message or not message.chat:
        return None

    chat = message.chat

    # --------------------------------------------------------
    # GET RANDOM CARD
    # --------------------------------------------------------

    card = choose_random_card()

    if not card:
        await message.reply_text(
            "❌ Card database ထဲမှာ အသုံးပြုလို့ရတဲ့ Card မရှိသေးပါ။"
        )
        return None

    char_id = str(card["char_id"])
    now = time.time()

    # --------------------------------------------------------
    # CREATE DROP RECORD
    # --------------------------------------------------------

    try:
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
                VALUES (?, ?, ?, 0, 0, ?)
                """,
                (
                    chat.id,
                    char_id,
                    0,
                    now,
                ),
            )

            drop_id = cursor.lastrowid

    except Exception as e:

        logger.exception(
            "Failed to create drop record: %s",
            e,
        )

        await message.reply_text(
            "❌ Drop ဖန်တီးရာမှာ Error ဖြစ်သွားပါတယ်။"
        )

        return None

    # --------------------------------------------------------
    # KEYBOARD
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
    # DROP MESSAGE
    # --------------------------------------------------------

    text = (
        f"✨ <b>{BOT_NAME} CARD DROP!</b> ✨\n\n"
        f"🎴 <b>A mysterious card has appeared!</b>\n\n"
        f"⚡ First person to press "
        f"<b>GET CARD</b> wins!\n\n"
        f"⏳ Be quick!"
    )

    sent = None

    # --------------------------------------------------------
    # SEND VIDEO
    # --------------------------------------------------------

    if (
        str(card["media_type"]).lower() == "video"
        and card["video_file_id"]
    ):

        try:

            sent = await message.reply_video(
                video=card["video_file_id"],
                caption=text,
                reply_markup=keyboard,
                parse_mode="HTML",
            )

        except Exception as e:

            logger.warning(
                "Video send failed, trying photo/text: %s",
                e,
            )

    # --------------------------------------------------------
    # SEND PHOTO
    # --------------------------------------------------------

    if sent is None and card["image_file_id"]:

        try:

            sent = await message.reply_photo(
                photo=card["image_file_id"],
                caption=text,
                reply_markup=keyboard,
                parse_mode="HTML",
            )

        except Exception as e:

            logger.warning(
                "Photo send failed, trying text: %s",
                e,
            )

    # --------------------------------------------------------
    # SEND TEXT
    # --------------------------------------------------------

    if sent is None:

        try:

            sent = await message.reply_text(
                text,
                reply_markup=keyboard,
                parse_mode="HTML",
            )

        except Exception as e:

            logger.exception(
                "Failed to send drop message: %s",
                e,
            )

            # Message failed, mark drop as cancelled.
            cancel_drop(drop_id)

            return None

    # --------------------------------------------------------
    # SAVE TELEGRAM MESSAGE ID
    # --------------------------------------------------------

    try:

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

    except Exception as e:

        logger.exception(
            "Failed to save drop message ID: %s",
            e,
        )

    logger.info(
        "DROP CREATED | chat=%s | drop_id=%s | card=%s",
        chat.id,
        drop_id,
        char_id,
    )

    return drop_id


# ============================================================
# CLAIM DROP
# ============================================================

async def claim_drop_callback(
    update,
    context: ContextTypes.DEFAULT_TYPE = None,
):

    query = update.callback_query

    if not query:
        return

    # --------------------------------------------------------
    # CHECK CALLBACK
    # --------------------------------------------------------

    data = query.data or ""

    if not data.startswith("drop:"):
        return

    try:

        drop_id = int(
            data.split(":", 1)[1]
        )

    except (ValueError, IndexError):

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

    user_id = user.id

    # --------------------------------------------------------
    # ATOMIC CLAIM
    # --------------------------------------------------------
    #
    # SQLite UPDATE WHERE claimed = 0
    #
    # Only the first successful request changes:
    #
    # 0 -> 1
    #
    # Therefore only one person wins.
    # --------------------------------------------------------

    try:

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

            if int(drop["claimed"] or 0) == 1:

                await query.answer(
                    "😢 နောက်ကျသွားပါပြီ!\n"
                    "ဒီ Card ကို တစ်ယောက်ယောက် ရသွားပါပြီ။",
                    show_alert=True,
                )

                return

            # ------------------------------------------------
            # ATOMIC UPDATE
            # ------------------------------------------------

            cursor = db.execute(
                """
                UPDATE drops
                SET
                    claimed = 1,
                    claimed_by = ?
                WHERE id = ?
                  AND claimed = 0
                """,
                (
                    user_id,
                    drop_id,
                ),
            )

            if cursor.rowcount != 1:

                await query.answer(
                    "😢 နောက်ကျသွားပါပြီ!\n"
                    "ဒီ Card ကို တစ်ယောက်ယောက် ရသွားပါပြီ။",
                    show_alert=True,
                )

                return

            char_id = str(drop["char_id"])

    except Exception as e:

        logger.exception(
            "Claim drop database error: %s",
            e,
        )

        await query.answer(
            "❌ Database Error ဖြစ်သွားပါတယ်။",
            show_alert=True,
        )

        return

    # --------------------------------------------------------
    # GET CARD
    # --------------------------------------------------------

    card = get_card(char_id)

    if not card:

        # Card unexpectedly unavailable.
        with get_db() as db:

            db.execute(
                """
                UPDATE drops
                SET
                    claimed = 0,
                    claimed_by = 0
                WHERE id = ?
                """,
                (drop_id,),
            )

        await query.answer(
            "❌ Card data မတွေ့ပါ။",
            show_alert=True,
        )

        return

    # --------------------------------------------------------
    # GIVE CARD
    # --------------------------------------------------------

    try:

        add_user_card(
            user_id,
            char_id,
        )

    except Exception as e:

        logger.exception(
            "Failed to give card %s to user %s: %s",
            char_id,
            user_id,
            e,
        )

        # Rollback claim if adding card failed.
        with get_db() as db:

            db.execute(
                """
                UPDATE drops
                SET
                    claimed = 0,
                    claimed_by = 0
                WHERE id = ?
                """,
                (drop_id,),
            )

        await query.answer(
            "❌ Card ထည့်ပေးရာမှာ Error ဖြစ်သွားပါတယ်။",
            show_alert=True,
        )

        return

    # --------------------------------------------------------
    # WINNER NAME
    # --------------------------------------------------------

    if user.username:

        winner_name = f"@{user.username}"

    elif user.first_name:

        winner_name = user.first_name

    else:

        winner_name = str(user.id)

    # --------------------------------------------------------
    # RESULT
    # --------------------------------------------------------

    try:
        price = int(card["price"] or 0)
    except (TypeError, ValueError):
        price = 0

    result_text = (
        f"🎉 <b>CARD CLAIMED!</b>\n\n"
        f"👤 Winner: <b>{winner_name}</b>\n\n"
        f"🎴 <b>{card['name']}</b>\n"
        f"🆔 <code>{card['char_id']}</code>\n"
        f"✨ Edition: <b>{card['edition']}</b>\n"
        f"⭐ Rarity: <b>{card['rarity']}</b>\n"
        f"💰 Price: <b>{price:,}</b> Coins\n\n"
        f"🏆 Congratulations! 🎊"
    )

    # --------------------------------------------------------
    # REMOVE GET CARD BUTTON
    # --------------------------------------------------------

    try:

        if query.message:

            if query.message.caption:

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

    except Exception as e:

        logger.warning(
            "Could not edit claimed drop message: %s",
            e,
        )

    # --------------------------------------------------------
    # ANSWER CALLBACK
    # --------------------------------------------------------

    await query.answer(
        "🎉 Card ရပါပြီ!",
        show_alert=True,
    )

    logger.info(
        "DROP CLAIMED | drop_id=%s | user=%s | card=%s",
        drop_id,
        user_id,
        char_id,
    )


# ============================================================
# GET DROP
# ============================================================

def get_drop_card(drop_id):

    with get_db() as db:

        return db.execute(
            """
            SELECT *
            FROM drops
            WHERE id = ?
            """,
            (drop_id,),
        ).fetchone()


# ============================================================
# GET ACTIVE DROP
# ============================================================

def get_active_drop(group_id):

    with get_db() as db:

        return db.execute(
            """
            SELECT *
            FROM drops
            WHERE group_id = ?
              AND claimed = 0
            ORDER BY id DESC
            LIMIT 1
            """,
            (group_id,),
        ).fetchone()


# ============================================================
# CANCEL DROP
# ============================================================

def cancel_drop(drop_id):

    with get_db() as db:

        db.execute(
            """
            UPDATE drops
            SET claimed = 1
            WHERE id = ?
              AND claimed = 0
            """,
            (drop_id,),
        )


# ============================================================
# CLEAN OLD DROPS
# ============================================================

def cleanup_old_drops(
    max_age_seconds=DEFAULT_DROP_EXPIRE,
):

    cutoff = time.time() - max_age_seconds

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
# DROP STATUS
# ============================================================

def drop_is_active(drop_id):

    with get_db() as db:

        row = db.execute(
            """
            SELECT claimed
            FROM drops
            WHERE id = ?
            """,
            (drop_id,),
        ).fetchone()

    if not row:
        return False

    return int(row["claimed"] or 0) == 0
