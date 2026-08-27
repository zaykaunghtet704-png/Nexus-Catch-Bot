import time

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import ContextTypes

from database import (
    get_db,
    get_card,
    get_user_cards,
    add_user_card,
)


# ============================================================
# CONFIG
# ============================================================

TRADE_EXPIRE_SECONDS = 300


# ============================================================
# HELPERS
# ============================================================

def owns_card(user_id, char_id):

    cards = get_user_cards(user_id)

    for card in cards:
        if str(card["char_id"]) == str(char_id):
            return True

    return False


def transfer_card(
    from_user,
    to_user,
    char_id,
):

    with get_db() as db:

        owner = db.execute(
            """
            SELECT *
            FROM user_cards
            WHERE user_id = ?
              AND char_id = ?
            LIMIT 1
            """,
            (
                from_user,
                char_id,
            ),
        ).fetchone()

        if not owner:
            return False

        db.execute(
            """
            DELETE FROM user_cards
            WHERE id = ?
            """,
            (owner["id"],),
        )

    add_user_card(
        to_user,
        char_id,
    )

    return True


# ============================================================
# GIFT
# ============================================================

async def gift_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    user = update.effective_user
    message = update.effective_message

    if not user or not message:
        return

    # Must reply to target user
    if not message.reply_to_message:

        await message.reply_text(
            "🎁 <b>Gift Usage</b>\n\n"
            "Card ပေးမယ့် User ရဲ့ message ကို "
            "Reply လုပ်ပြီး\n\n"
            "<code>/gift CHAR_ID</code>\n\n"
            "အသုံးပြုပါ။",
            parse_mode="HTML",
        )

        return

    target = message.reply_to_message.from_user

    if not target:

        await message.reply_text(
            "❌ Target user မတွေ့ပါ။"
        )

        return

    if target.id == user.id:

        await message.reply_text(
            "❌ ကိုယ့်ကိုယ်ကို Card ပေးလို့မရပါ။"
        )

        return

    if target.is_bot:

        await message.reply_text(
            "❌ Bot ကို Card ပေးလို့မရပါ။"
        )

        return

    if len(context.args) != 1:

        await message.reply_text(
            "🎁 Usage:\n"
            "<code>/gift CHAR_ID</code>\n\n"
            "Example:\n"
            "<code>/gift 0021</code>",
            parse_mode="HTML",
        )

        return

    char_id = context.args[0]

    card = get_card(char_id)

    if not card:

        await message.reply_text(
            "❌ Card ID မတွေ့ပါ။"
        )

        return

    if not owns_card(
        user.id,
        char_id,
    ):

        await message.reply_text(
            "❌ ဒီ Card ကို မင်းမပိုင်ပါ။"
        )

        return

    # Transfer
    success = transfer_card(
        user.id,
        target.id,
        char_id,
    )

    if not success:

        await message.reply_text(
            "❌ Card transfer မအောင်မြင်ပါ။"
        )

        return

    sender_name = (
        f"@{user.username}"
        if user.username
        else user.first_name
    )

    receiver_name = (
        f"@{target.username}"
        if target.username
        else target.first_name
    )

    await message.reply_text(
        "🎁 <b>CARD GIFTED!</b>\n\n"
        f"👤 From: <b>{sender_name}</b>\n"
        f"➡️ To: <b>{receiver_name}</b>\n\n"
        f"🎴 <b>{card['name']}</b>\n"
        f"🆔 <code>{card['char_id']}</code>\n"
        f"✨ {card['edition']}\n\n"
        "💖 Gift completed!",
        parse_mode="HTML",
    )


# ============================================================
# TRADE DATABASE
# ============================================================

def init_trade_db():

    with get_db() as db:

        db.execute(
            """
            CREATE TABLE IF NOT EXISTS trade_offers (
                trade_id INTEGER PRIMARY KEY AUTOINCREMENT,

                sender_id INTEGER NOT NULL,
                receiver_id INTEGER NOT NULL,

                sender_card TEXT NOT NULL,
                receiver_card TEXT NOT NULL,

                status TEXT NOT NULL DEFAULT 'pending',

                created_at REAL NOT NULL
            )
            """
        )


init_trade_db()


# ============================================================
# CREATE TRADE
# ============================================================

async def trade_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    user = update.effective_user
    message = update.effective_message

    if not user or not message:
        return

    if len(context.args) != 2:

        await message.reply_text(
            "🤝 <b>Trade Usage</b>\n\n"
            "<code>/trade YOUR_ID THEIR_ID</code>\n\n"
            "Example:\n"
            "<code>/trade 0021 0099</code>",
            parse_mode="HTML",
        )

        return

    your_card = context.args[0]
    their_card = context.args[1]

    # Card existence
    first_card = get_card(your_card)
    second_card = get_card(their_card)

    if not first_card:

        await message.reply_text(
            f"❌ Your Card <code>{your_card}</code> မတွေ့ပါ။",
            parse_mode="HTML",
        )

        return

    if not second_card:

        await message.reply_text(
            f"❌ Target Card <code>{their_card}</code> မတွေ့ပါ။",
            parse_mode="HTML",
        )

        return

    # Must reply to target user
    if not message.reply_to_message:

        await message.reply_text(
            "🤝 Trade လုပ်မယ့် User ရဲ့ message ကို "
            "Reply လုပ်ပြီး command သုံးပါ။\n\n"
            "Example:\n"
            "<code>/trade 0021 0099</code>",
            parse_mode="HTML",
        )

        return

    target = message.reply_to_message.from_user

    if not target:

        await message.reply_text(
            "❌ Target user မတွေ့ပါ။"
        )

        return

    if target.id == user.id:

        await message.reply_text(
            "❌ ကိုယ့်ကိုယ်ကို Trade မလုပ်နိုင်ပါ။"
        )

        return

    # Ownership checks
    if not owns_card(
        user.id,
        your_card,
    ):

        await message.reply_text(
            f"❌ Card <code>{your_card}</code> ကို "
            "မင်းမပိုင်ပါ။",
            parse_mode="HTML",
        )

        return

    if not owns_card(
        target.id,
        their_card,
    ):

        await message.reply_text(
            f"❌ Target user မှာ Card "
            f"<code>{their_card}</code> မရှိပါ။",
            parse_mode="HTML",
        )

        return

    now = time.time()

    with get_db() as db:

        cursor = db.execute(
            """
            INSERT INTO trade_offers (
                sender_id,
                receiver_id,
                sender_card,
                receiver_card,
                status,
                created_at
            )
            VALUES (?, ?, ?, ?, 'pending', ?)
            """,
            (
                user.id,
                target.id,
                your_card,
                their_card,
                now,
            ),
        )

        trade_id = cursor.lastrowid

    keyboard = [
        [
            InlineKeyboardButton(
                "✅ ACCEPT",
                callback_data=f"trade_accept:{trade_id}",
            ),
            InlineKeyboardButton(
                "❌ DECLINE",
                callback_data=f"trade_decline:{trade_id}",
            ),
        ]
    ]

    sender_name = (
        f"@{user.username}"
        if user.username
        else user.first_name
    )

    receiver_name = (
        f"@{target.username}"
        if target.username
        else target.first_name
    )

    await message.reply_text(
        "🤝 <b>TRADE OFFER</b>\n\n"
        f"👤 From: <b>{sender_name}</b>\n"
        f"👤 To: <b>{receiver_name}</b>\n\n"
        f"🎴 {sender_name} offers:\n"
        f"<code>{your_card}</code> — "
        f"{first_card['name']}\n\n"
        f"🎴 {receiver_name} offers:\n"
        f"<code>{their_card}</code> — "
        f"{second_card['name']}\n\n"
        "⏳ Offer expires in 5 minutes.",
        reply_markup=InlineKeyboardMarkup(
            keyboard
        ),
        parse_mode="HTML",
    )


# ============================================================
# ACCEPT TRADE
# ============================================================

async def accept_trade(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    trade_id: int,
):

    query = update.callback_query
    user = query.from_user

    with get_db() as db:

        trade = db.execute(
            """
            SELECT *
            FROM trade_offers
            WHERE trade_id = ?
            """,
            (trade_id,),
        ).fetchone()

        if not trade:

            await query.answer(
                "❌ Trade မတွေ့ပါ။",
                show_alert=True,
            )

            return

        if trade["status"] != "pending":

            await query.answer(
                "⚠️ ဒီ Trade က အသုံးမပြုနိုင်တော့ပါ။",
                show_alert=True,
            )

            return

        if trade["receiver_id"] != user.id:

            await query.answer(
                "🚫 ဒီ Trade ကို လက်ခံနိုင်သူ မင်းမဟုတ်ပါ။",
                show_alert=True,
            )

            return

        if (
            time.time()
            - trade["created_at"]
            > TRADE_EXPIRE_SECONDS
        ):

            db.execute(
                """
                UPDATE trade_offers
                SET status = 'expired'
                WHERE trade_id = ?
                """,
                (trade_id,),
            )

            await query.answer(
                "⏳ Trade သက်တမ်းကုန်သွားပါပြီ။",
                show_alert=True,
            )

            return

        sender_id = trade["sender_id"]
        receiver_id = trade["receiver_id"]

        sender_card = trade["sender_card"]
        receiver_card = trade["receiver_card"]

        # Re-check ownership
        sender_has = db.execute(
            """
            SELECT id
            FROM user_cards
            WHERE user_id = ?
              AND char_id = ?
            LIMIT 1
            """,
            (
                sender_id,
                sender_card,
            ),
        ).fetchone()

        receiver_has = db.execute(
            """
            SELECT id
            FROM user_cards
            WHERE user_id = ?
              AND char_id = ?
            LIMIT 1
            """,
            (
                receiver_id,
                receiver_card,
            ),
        ).fetchone()

        if not sender_has:

            db.execute(
                """
                UPDATE trade_offers
                SET status = 'cancelled'
                WHERE trade_id = ?
                """,
                (trade_id,),
            )

            await query.answer(
                "❌ Sender မှာ Card မရှိတော့ပါ။",
                show_alert=True,
            )

            return

        if not receiver_has:

            db.execute(
                """
                UPDATE trade_offers
                SET status = 'cancelled'
                WHERE trade_id = ?
                """,
                (trade_id,),
            )

            await query.answer(
                "❌ Target Card မရှိတော့ပါ။",
                show_alert=True,
            )

            return

        # Remove both cards
        db.execute(
            """
            DELETE FROM user_cards
            WHERE id = ?
            """,
            (sender_has["id"],),
        )

        db.execute(
            """
            DELETE FROM user_cards
            WHERE id = ?
            """,
            (receiver_has["id"],),
        )

        # Add exchanged cards
        db.execute(
            """
            INSERT INTO user_cards (
                user_id,
                char_id,
                acquired_at,
                level,
                exp,
                favorite
            )
            VALUES (?, ?, ?, 1, 0, 0)
            """,
            (
                receiver_id,
                sender_card,
                time.time(),
            ),
        )

        db.execute(
            """
            INSERT INTO user_cards (
                user_id,
                char_id,
                acquired_at,
                level,
                exp,
                favorite
            )
            VALUES (?, ?, ?, 1, 0, 0)
            """,
            (
                sender_id,
                receiver_card,
                time.time(),
            ),
        )

        # Complete
        db.execute(
            """
            UPDATE trade_offers
            SET status = 'completed'
            WHERE trade_id = ?
            """,
            (trade_id,),
        )

    sender_card_info = get_card(
        sender_card
    )

    receiver_card_info = get_card(
        receiver_card
    )

    await query.answer(
        "🤝 Trade အောင်မြင်ပါပြီ!",
        show_alert=True,
    )

    try:

        await query.edit_message_text(
            "🤝 <b>TRADE COMPLETED!</b>\n\n"
            f"🎴 Sender → Receiver\n"
            f"{sender_card_info['name']}\n\n"
            f"🎴 Receiver → Sender\n"
            f"{receiver_card_info['name']}\n\n"
            "✨ Trade completed successfully!",
            parse_mode="HTML",
        )

    except Exception:
        pass


# ============================================================
# DECLINE TRADE
# ============================================================

async def decline_trade(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    trade_id: int,
):

    query = update.callback_query
    user = query.from_user

    with get_db() as db:

        trade = db.execute(
            """
            SELECT *
            FROM trade_offers
            WHERE trade_id = ?
            """,
            (trade_id,),
        ).fetchone()

        if not trade:

            await query.answer(
                "❌ Trade မတွေ့ပါ။",
                show_alert=True,
            )

            return

        if trade["receiver_id"] != user.id:

            await query.answer(
                "🚫 ဒီ Trade ကို Decline လုပ်ခွင့်မရှိပါ။",
                show_alert=True,
            )

            return

        if trade["status"] != "pending":

            await query.answer(
                "⚠️ Trade မရှိတော့ပါ။",
                show_alert=True,
            )

            return

        db.execute(
            """
            UPDATE trade_offers
            SET status = 'declined'
            WHERE trade_id = ?
            """,
            (trade_id,),
        )

    await query.answer(
        "Trade Declined.",
        show_alert=True,
    )

    try:

        await query.edit_message_text(
            "❌ <b>TRADE DECLINED</b>",
            parse_mode="HTML",
        )

    except Exception:
        pass


# ============================================================
# CALLBACK ROUTER
# ============================================================

async def trade_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    query = update.callback_query

    data = query.data or ""

    if data.startswith(
        "trade_accept:"
    ):

        try:
            trade_id = int(
                data.split(":", 1)[1]
            )
        except ValueError:
            await query.answer(
                "Invalid trade.",
                show_alert=True,
            )
            return

        await accept_trade(
            update,
            context,
            trade_id,
        )

        return

    if data.startswith(
        "trade_decline:"
    ):

        try:
            trade_id = int(
                data.split(":", 1)[1]
            )
        except ValueError:
            await query.answer(
                "Invalid trade.",
                show_alert=True,
            )
            return

        await decline_trade(
            update,
            context,
            trade_id,
        )

        return

    await query.answer()


# ============================================================
# CLEANUP
# ============================================================

def cleanup_trade_offers():

    cutoff = (
        time.time()
        - TRADE_EXPIRE_SECONDS
    )

    with get_db() as db:

        db.execute(
            """
            UPDATE trade_offers
            SET status = 'expired'
            WHERE status = 'pending'
              AND created_at < ?
            """,
            (cutoff,),
        )
