import random
import time

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
# DROP SYSTEM
# ============================================================

async def create_drop(
    message,
    context: ContextTypes.DEFAULT_TYPE,
):
    """
    Drop a random card.

    IMPORTANT:
    The card is NOT given when /drop is sent.
    It is given only to the first user who presses
    the GET CARD button.
    """

    chat = message.chat

    if not chat:
        return

    cards = get_all_cards()

    if not cards:
        await message.reply_text(
            "❌ Card database ထဲမှာ Card မရှိသေးပါ။"
        )
        return

    # Random card using drop weight
    card = random.choices(
        cards,
        weights=[
            max(0.01, float(c["drop_weight"]))
            for c in cards
        ],
        k=1,
    )[0]

    now = time.time()

    # Create a drop record.
    # claimed = 0 means nobody has claimed it yet.
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
                card["char_id"],
                0,
                now,
            ),
        )

        drop_id = cursor.lastrowid

    keyboard = [
        [
            InlineKeyboardButton(
                "🎴 GET CARD",
                callback_data=f"drop:{drop_id}",
            )
        ]
    ]

    text = (
        f"✨ <b>{BOT_NAME} CARD DROP!</b> ✨\n\n"
        f"🎴 A mysterious card has appeared!\n\n"
        f"⚡ <b>First person to press GET CARD wins!</b>\n\n"
        f"⏳ Be quick!"
    )

    sent = None

    # Send media if available
    if (
        card["media_type"] == "video"
        and card["video_file_id"]
    ):

        sent = await message.reply_video(
            video=card["video_file_id"],
            caption=text,
            reply_markup=InlineKeyboardMarkup(
                keyboard
            ),
            parse_mode="HTML",
        )

    elif card["image_file_id"]:

        sent = await message.reply_photo(
            photo=card["image_file_id"],
            caption=text,
            reply_markup=InlineKeyboardMarkup(
                keyboard
            ),
            parse_mode="HTML",
        )

    else:

        sent = await message.reply_text(
            text,
            reply_markup=InlineKeyboardMarkup(
                keyboard
            ),
            parse_mode="HTML",
        )

    # Save the real Telegram message ID.
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


# ============================================================
# CLAIM DROP
# ============================================================

async def claim_drop_callback(
    update,
    context: ContextTypes.DEFAULT_TYPE,
):

    query = update.callback_query

    if not query.data:
        return

    if not query.data.startswith("drop:"):
        return

    try:
        drop_id = int(
            query.data.split(":", 1)[1]
        )
    except (ValueError, IndexError):

        await query.answer(
            "❌ Invalid drop.",
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

    # ========================================================
    # ATOMIC FIRST-CLICK CLAIM
    # ========================================================
    #
    # The important part is:
    #
    # UPDATE drops
    # SET claimed = 1
    # WHERE id = ? AND claimed = 0
    #
    # Only ONE request can change claimed from 0 -> 1.
    # Therefore only the first successful callback wins.
    #

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

        if drop["claimed"]:

            await query.answer(
                "😢 နောက်ကျသွားပါပြီ!\n"
                "ဒီ Card ကို တစ်ယောက်ယောက် ရသွားပါပြီ။",
                show_alert=True,
            )

            return

        # Atomic claim
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

        # Another user won milliseconds earlier.
        if cursor.rowcount != 1:

            await query.answer(
                "😢 နောက်ကျသွားပါပြီ!\n"
                "ဒီ Card ကို တစ်ယောက်ယောက် ရသွားပါပြီ။",
                show_alert=True,
            )

            return

        char_id = drop["char_id"]

    # ========================================================
    # GIVE CARD TO WINNER
    # ========================================================

    card = get_card(char_id)

    if not card:

        # Safety rollback if card disappeared
        with get_db() as db:

            db.execute(
                """
                UPDATE drops
                SET claimed = 0,
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

    add_user_card(
        user_id,
        char_id,
    )

    # ========================================================
    # REMOVE BUTTON
    # ========================================================

    winner_name = (
        f"@{user.username}"
        if user.username
        else user.first_name
    )

    result_text = (
        f"🎉 <b>CARD CLAIMED!</b>\n\n"
        f"👤 Winner: <b>{winner_name}</b>\n\n"
        f"🎴 <b>{card['name']}</b>\n"
        f"🆔 <code>{card['char_id']}</code>\n"
        f"✨ Edition: <b>{card['edition']}</b>\n"
        f"⭐ Rarity: <b>{card['rarity']}</b>\n"
        f"💰 Price: <b>{card['price']:,}</b> Coins\n\n"
        f"🏆 Congratulations!"
    )

    try:

        await query.edit_message_caption(
            caption=result_text,
            reply_markup=None,
            parse_mode="HTML",
        )

    except Exception:

        try:

            await query.edit_message_text(
                text=result_text,
                reply_markup=None,
                parse_mode="HTML",
            )

        except Exception:
            pass

    await query.answer(
        "🎉 Card ရပါပြီ!",
        show_alert=True,
    )


# ============================================================
# DROP PREVIEW
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
# CANCEL DROP
# ============================================================

def cancel_drop(drop_id):
    """
    Owner/Admin can use this later to cancel a drop.
    """

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
    max_age_seconds=3600,
):
    """
    Marks old unclaimed drops as expired.
    """

    cutoff = time.time() - max_age_seconds

    with get_db() as db:

        db.execute(
            """
            UPDATE drops
            SET claimed = 1
            WHERE claimed = 0
              AND created_at < ?
            """,
            (cutoff,),
        )
