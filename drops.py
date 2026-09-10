import logging
import random
import time

from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
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

    try:
        cards = get_all_cards()
    except Exception as exc:
        logger.exception(
            "get_all_cards failed: %s",
            exc,
        )
        return None

    if not cards:
        return None

    valid_cards = []
    weights = []

    for card in cards:

        try:
            weight = float(
                card["drop_weight"] or 1
            )
        except (TypeError, ValueError):
            weight = 1.0

        if weight <= 0:
            weight = 0.01

        valid_cards.append(card)
        weights.append(weight)

    if not valid_cards:
        return None

    try:
        return random.choices(
            valid_cards,
            weights=weights,
            k=1,
        )[0]
    except Exception as exc:
        logger.exception(
            "Random card selection failed: %s",
            exc,
        )
        return None


# ============================================================
# CREATE DROP
# ============================================================

async def create_drop(
    message,
    context: ContextTypes.DEFAULT_TYPE = None,
    notify_errors=True,
):
    """
    Create a new card drop.

    Card is NOT given immediately.

    First user pressing GET CARD wins.

    notify_errors=True
        Used by manual /drop.

    notify_errors=False
        Used by auto-drop so normal group messages
        are NEVER replied to because of drop errors.
    """

    if not message or not message.chat:
        return None

    chat = message.chat

    # --------------------------------------------------------
    # SELECT CARD
    # --------------------------------------------------------

    card = choose_random_card()

    if not card:

        logger.warning(
            "DROP SKIPPED — no active cards | chat=%s",
            chat.id,
        )

        if notify_errors:
            try:
                await message.reply_text(
                    "❌ Card database ထဲမှာ "
                    "အသုံးပြုလို့ရတဲ့ Card မရှိသေးပါ။"
                )
            except Exception:
                pass

        return None

    char_id = str(
        card["char_id"]
    )

    now = time.time()

    # --------------------------------------------------------
    # CREATE DATABASE DROP
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

    except Exception as exc:

        logger.exception(
            "Failed to create drop record | chat=%s",
            chat.id,
        )

        if notify_errors:
            try:
                await message.reply_text(
                    "❌ Drop ဖန်တီးရာမှာ "
                    "Error ဖြစ်သွားပါတယ်။"
                )
            except Exception:
                pass

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
    # DROP MESSAGE
    # --------------------------------------------------------

    text = (
        f"✨ <b>{BOT_NAME} CARD DROP!</b> ✨\n\n"
        f"🎴 <b>A mysterious card has appeared!</b>\n\n"
        f"⚡ First person to press "
        f"<b>GET CARD</b> wins!\n\n"
        f"⏳ <b>Be quick!</b>"
    )

    sent = None

    # --------------------------------------------------------
    # VIDEO
    # --------------------------------------------------------

    media_type = str(
        card["media_type"] or ""
    ).lower()

    video_file_id = (
        card["video_file_id"]
        or ""
    )

    image_file_id = (
        card["image_file_id"]
        or ""
    )

    if (
        media_type == "video"
        and video_file_id
    ):

        try:

            sent = await message.reply_video(
                video=video_file_id,
                caption=text,
                reply_markup=keyboard,
                parse_mode="HTML",
            )

        except Exception as exc:

            logger.warning(
                "Video drop send failed | drop=%s | %s",
                drop_id,
                exc,
            )

    # --------------------------------------------------------
    # PHOTO
    # --------------------------------------------------------

    if sent is None and image_file_id:

        try:

            sent = await message.reply_photo(
                photo=image_file_id,
                caption=text,
                reply_markup=keyboard,
                parse_mode="HTML",
            )

        except Exception as exc:

            logger.warning(
                "Photo drop send failed | drop=%s | %s",
                drop_id,
                exc,
            )

    # --------------------------------------------------------
    # TEXT FALLBACK
    # --------------------------------------------------------

    if sent is None:

        try:

            sent = await message.reply_text(
                text,
                reply_markup=keyboard,
                parse_mode="HTML",
            )

        except Exception as exc:

            logger.exception(
                "Drop message send failed | drop=%s",
                drop_id,
            )

            cancel_drop(
                drop_id
            )

            if notify_errors:
                try:
                    await message.reply_text(
                        "❌ Card Drop လုပ်မရပါ။"
                    )
                except Exception:
                    pass

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

    except Exception as exc:

        logger.exception(
            "Failed to save drop message ID | drop=%s",
            drop_id,
        )

        # Message already exists, therefore keep drop alive.
        # Claim callback can still work using drop_id.

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

    data = query.data or ""

    if not data.startswith("drop:"):
        return

    # --------------------------------------------------------
    # DROP ID
    # --------------------------------------------------------

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

    user_id = user.id

    # --------------------------------------------------------
    # CHECK DROP
    # --------------------------------------------------------

    try:

        with get_db() as db:

            drop = db.execute(
                """
                SELECT *
                FROM drops
                WHERE id = ?
                LIMIT 1
                """,
                (drop_id,),
            ).fetchone()

    except Exception as exc:

        logger.exception(
            "Drop lookup failed | drop=%s",
            drop_id,
        )

        await query.answer(
            "❌ Database Error ဖြစ်သွားပါတယ်။",
            show_alert=True,
        )

        return

    if not drop:

        await query.answer(
            "❌ ဒီ Drop မရှိတော့ပါ။",
            show_alert=True,
        )

        return

    # --------------------------------------------------------
    # ALREADY CLAIMED
    # --------------------------------------------------------

    if int(
        drop["claimed"] or 0
    ) == 1:

        await query.answer(
            "😢 နောက်ကျသွားပါပြီ!\n"
            "ဒီ Card ကို တစ်ယောက်ယောက် ရသွားပါပြီ။",
            show_alert=True,
        )

        return

    # --------------------------------------------------------
    # EXPIRATION
    # --------------------------------------------------------

    created_at = float(
        drop["created_at"] or 0
    )

    if (
        created_at > 0
        and time.time() - created_at
        >= DEFAULT_DROP_EXPIRE
    ):

        cancel_drop(
            drop_id
        )

        await query.answer(
            "⏰ ဒီ Card Drop သက်တမ်းကုန်သွားပါပြီ။",
            show_alert=True,
        )

        try:

            if query.message:

                if query.message.caption:

                    await query.edit_message_caption(
                        caption=(
                            "⏰ <b>CARD DROP EXPIRED</b>\n\n"
                            "ဒီ Drop ရဲ့ သက်တမ်းကုန်သွားပါပြီ။"
                        ),
                        reply_markup=None,
                        parse_mode="HTML",
                    )

                else:

                    await query.edit_message_text(
                        text=(
                            "⏰ <b>CARD DROP EXPIRED</b>\n\n"
                            "ဒီ Drop ရဲ့ သက်တမ်းကုန်သွားပါပြီ။"
                        ),
                        reply_markup=None,
                        parse_mode="HTML",
                    )

        except Exception:
            pass

        return

    char_id = str(
        drop["char_id"]
    )

    # --------------------------------------------------------
    # VERIFY CARD STILL EXISTS
    # --------------------------------------------------------

    card = get_card(
        char_id
    )

    if not card:

        cancel_drop(
            drop_id
        )

        await query.answer(
            "❌ Card data မတွေ့ပါ။",
            show_alert=True,
        )

        return

    # --------------------------------------------------------
    # ATOMIC CLAIM
    # --------------------------------------------------------
    #
    # Only ONE user can change:
    #
    # claimed = 0
    #
    # into:
    #
    # claimed = 1
    #
    # This prevents two users winning the same drop.
    # --------------------------------------------------------

    try:

        with get_db() as db:

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

            won = (
                cursor.rowcount == 1
            )

    except Exception as exc:

        logger.exception(
            "Atomic claim failed | drop=%s | user=%s",
            drop_id,
            user_id,
        )

        await query.answer(
            "❌ Database Error ဖြစ်သွားပါတယ်။",
            show_alert=True,
        )

        return

    # --------------------------------------------------------
    # SOMEONE ELSE WON
    # --------------------------------------------------------

    if not won:

        await query.answer(
            "😢 နောက်ကျသွားပါပြီ!\n"
            "ဒီ Card ကို တစ်ယောက်ယောက် ရသွားပါပြီ။",
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

    except Exception as exc:

        logger.exception(
            "Failed to give card | drop=%s | user=%s | card=%s",
            drop_id,
            user_id,
            char_id,
        )

        # Restore the drop only if it still belongs
        # to this same user.
        try:

            with get_db() as db:

                db.execute(
                    """
                    UPDATE drops
                    SET
                        claimed = 0,
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

        except Exception:
            logger.exception(
                "Failed to rollback drop claim | drop=%s",
                drop_id,
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

        winner_name = (
            f"@{user.username}"
        )

    elif user.first_name:

        winner_name = (
            user.first_name
        )

    else:

        winner_name = str(
            user.id
        )

    # --------------------------------------------------------
    # PRICE
    # --------------------------------------------------------

    try:

        price = int(
            card["price"] or 0
        )

    except (
        TypeError,
        ValueError,
    ):

        price = 0

    # --------------------------------------------------------
    # RESULT
    # --------------------------------------------------------

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

    except Exception as exc:

        logger.warning(
            "Could not edit claimed drop message | drop=%s | %s",
            drop_id,
            exc,
        )

    # --------------------------------------------------------
    # CALLBACK SUCCESS
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

def get_drop_card(
    drop_id,
):

    try:

        with get_db() as db:

            return db.execute(
                """
                SELECT *
                FROM drops
                WHERE id = ?
                LIMIT 1
                """,
                (drop_id,),
            ).fetchone()

    except Exception as exc:

        logger.exception(
            "get_drop_card failed: %s",
            exc,
        )

        return None


# ============================================================
# GET ACTIVE DROP
# ============================================================

def get_active_drop(
    group_id,
):

    now = time.time()

    try:

        with get_db() as db:

            # Automatically expire old unclaimed drops.
            db.execute(
                """
                UPDATE drops
                SET claimed = 1
                WHERE group_id = ?
                  AND claimed = 0
                  AND created_at > 0
                  AND created_at < ?
                """,
                (
                    group_id,
                    now - DEFAULT_DROP_EXPIRE,
                ),
            )

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

    except Exception as exc:

        logger.exception(
            "get_active_drop failed | group=%s",
            group_id,
        )

        return None


# ============================================================
# CANCEL DROP
# ============================================================

def cancel_drop(
    drop_id,
):

    try:

        with get_db() as db:

            cursor = db.execute(
                """
                UPDATE drops
                SET
                    claimed = 1,
                    claimed_by = 0
                WHERE id = ?
                  AND claimed = 0
                """,
                (drop_id,),
            )

        return cursor.rowcount

    except Exception as exc:

        logger.exception(
            "cancel_drop failed | drop=%s",
            drop_id,
        )

        return 0


# ============================================================
# CLEAN OLD DROPS
# ============================================================

def cleanup_old_drops(
    max_age_seconds=DEFAULT_DROP_EXPIRE,
):

    cutoff = (
        time.time()
        - max_age_seconds
    )

    try:

        with get_db() as db:

            cursor = db.execute(
                """
                UPDATE drops
                SET
                    claimed = 1,
                    claimed_by = 0
                WHERE claimed = 0
                  AND created_at < ?
                """,
                (cutoff,),
            )

        return cursor.rowcount

    except Exception as exc:

        logger.exception(
            "cleanup_old_drops failed: %s",
            exc,
        )

        return 0


# ============================================================
# DROP STATUS
# ============================================================

def drop_is_active(
    drop_id,
):

    try:

        with get_db() as db:

            row = db.execute(
                """
                SELECT
                    claimed,
                    created_at
                FROM drops
                WHERE id = ?
                LIMIT 1
                """,
                (drop_id,),
            ).fetchone()

    except Exception as exc:

        logger.exception(
            "drop_is_active failed | drop=%s",
            drop_id,
        )

        return False

    if not row:
        return False

    if int(
        row["claimed"] or 0
    ) == 1:
        return False

    created_at = float(
        row["created_at"] or 0
    )

    if (
        created_at > 0
        and time.time() - created_at
        >= DEFAULT_DROP_EXPIRE
    ):

        cancel_drop(
            drop_id
        )

        return False

    return True
