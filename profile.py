import math

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import ContextTypes

from database import (
    get_db,
    get_balance,
    get_user_cards,
    get_all_cards,
)


# ============================================================
# CONFIG
# ============================================================

CARDS_PER_PAGE = 8


# ============================================================
# HELPERS
# ============================================================

def get_user_rank(user_id):

    with get_db() as db:

        rows = db.execute(
            """
            SELECT
                user_id,
                COUNT(*) AS total
            FROM user_cards
            GROUP BY user_id
            ORDER BY total DESC
            """
        ).fetchall()

    rank = 0

    for index, row in enumerate(rows, start=1):

        if row["user_id"] == user_id:
            rank = index
            break

    return rank


def get_collection_count(user_id):

    cards = get_user_cards(user_id)

    return len(cards)


def get_total_card_count():

    cards = get_all_cards()

    return len(cards)


def get_user_favorites(user_id):

    with get_db() as db:

        return db.execute(
            """
            SELECT *
            FROM user_cards
            WHERE user_id = ?
              AND favorite = 1
            ORDER BY char_id
            """,
            (user_id,),
        ).fetchall()


def get_user_exp(user_id):

    with get_db() as db:

        row = db.execute(
            """
            SELECT
                COALESCE(SUM(exp), 0) AS total_exp
            FROM user_cards
            WHERE user_id = ?
            """,
            (user_id,),
        ).fetchone()

    return int(row["total_exp"] or 0)


def get_user_level(user_id):

    exp = get_user_exp(user_id)

    # Simple global level formula
    level = 1 + int(
        math.sqrt(exp / 100)
    )

    return max(1, level)


# ============================================================
# PROFILE
# ============================================================

async def profile_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    message = update.effective_message
    requester = update.effective_user

    if not message or not requester:
        return

    # --------------------------------------------------------
    # Determine target user
    # --------------------------------------------------------

    target = requester

    # /profile when replying to someone
    if message.reply_to_message:

        replied_user = (
            message.reply_to_message.from_user
        )

        if replied_user:
            target = replied_user

    # /profile USER_ID
    elif context.args:

        try:

            target_id = int(
                context.args[0]
            )

            try:

                target = await context.bot.get_chat(
                    target_id
                )

            except Exception:

                await message.reply_text(
                    "❌ User ကို ရှာမတွေ့ပါ။"
                )

                return

        except ValueError:

            await message.reply_text(
                "❌ User ID မှားနေပါတယ်။"
            )

            return

    user_id = target.id

    # --------------------------------------------------------
    # User information
    # --------------------------------------------------------

    first_name = (
        target.first_name
        or "Unknown"
    )

    username = (
        f"@{target.username}"
        if getattr(
            target,
            "username",
            None,
        )
        else "No Username"
    )

    cards = get_user_cards(
        user_id
    )

    card_count = len(cards)

    total_cards = (
        get_total_card_count()
    )

    balance = get_balance(
        user_id
    )

    level = get_user_level(
        user_id
    )

    exp = get_user_exp(
        user_id
    )

    rank = get_user_rank(
        user_id
    )

    favorites = get_user_favorites(
        user_id
    )

    # --------------------------------------------------------
    # Collection percentage
    # --------------------------------------------------------

    if total_cards > 0:

        collection_percent = (
            card_count
            / total_cards
            * 100
        )

    else:

        collection_percent = 0

    # --------------------------------------------------------
    # Profile text
    # --------------------------------------------------------

    rank_text = (
        f"#{rank}"
        if rank > 0
        else "Unranked"
    )

    text = (
        "👤 <b>NEXUS PROFILE</b>\n\n"

        f"🧑 Name: <b>{first_name}</b>\n"
        f"🔗 Username: {username}\n"
        f"🆔 ID: <code>{user_id}</code>\n\n"

        "📊 <b>ACCOUNT</b>\n"
        f"💰 Coins: <b>{balance:,}</b>\n"
        f"🎖 Level: <b>{level}</b>\n"
        f"✨ EXP: <b>{exp:,}</b>\n\n"

        "🎴 <b>COLLECTION</b>\n"
        f"📦 Cards: <b>{card_count}</b>"
        f" / {total_cards}\n"
        f"📈 Progress: <b>{collection_percent:.1f}%</b>\n"
        f"❤️ Favorites: <b>{len(favorites)}</b>\n\n"

        "🏆 <b>GLOBAL RANK</b>\n"
        f"🌎 Rank: <b>{rank_text}</b>"
    )

    # --------------------------------------------------------
    # Buttons
    # --------------------------------------------------------

    keyboard = [
        [
            InlineKeyboardButton(
                "🎴 My Harem",
                callback_data=f"profile_harem:{user_id}",
            ),
            InlineKeyboardButton(
                "❤️ Favorites",
                callback_data=f"profile_fav:{user_id}",
            ),
        ],
    ]

    # --------------------------------------------------------
    # Profile photo
    # --------------------------------------------------------

    try:

        photos = await context.bot.get_user_profile_photos(
            user_id=user_id,
            limit=1,
        )

        if photos.total_count > 0:

            photo = photos.photos[0][-1]

            await message.reply_photo(
                photo=photo.file_id,
                caption=text,
                reply_markup=InlineKeyboardMarkup(
                    keyboard
                ),
                parse_mode="HTML",
            )

            return

    except Exception:
        pass

    # --------------------------------------------------------
    # No profile photo
    # --------------------------------------------------------

    await message.reply_text(
        text,
        reply_markup=InlineKeyboardMarkup(
            keyboard
        ),
        parse_mode="HTML",
    )


# ============================================================
# PROFILE CALLBACK
# ============================================================

async def profile_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    query = update.callback_query

    data = query.data or ""

    # --------------------------------------------------------
    # HAREM BUTTON
    # --------------------------------------------------------

    if data.startswith(
        "profile_harem:"
    ):

        try:

            user_id = int(
                data.split(":", 1)[1]
            )

        except ValueError:

            await query.answer(
                "Invalid user.",
                show_alert=True,
            )

            return

        cards = get_user_cards(
            user_id
        )

        if not cards:

            await query.answer(
                "🎴 Card မရှိသေးပါ။",
                show_alert=True,
            )

            return

        text = (
            "🎴 <b>MY HAREM</b>\n\n"
            f"👤 User ID: <code>{user_id}</code>\n"
            f"📦 Total: <b>{len(cards)}</b>\n\n"
        )

        for index, card in enumerate(
            cards[:CARDS_PER_PAGE],
            start=1,
        ):

            text += (
                f"{index}. "
                f"<code>{card['char_id']}</code>\n"
            )

        text += (
            "\n💡 Full collection ကို "
            "/harem နဲ့ ကြည့်နိုင်ပါတယ်။"
        )

        keyboard = [
            [
                InlineKeyboardButton(
                    "⬅️ Back",
                    callback_data=f"profile_back:{user_id}",
                )
            ]
        ]

        await query.answer()

        try:

            await query.edit_message_caption(
                caption=text,
                reply_markup=InlineKeyboardMarkup(
                    keyboard
                ),
                parse_mode="HTML",
            )

        except Exception:

            try:

                await query.edit_message_text(
                    text,
                    reply_markup=InlineKeyboardMarkup(
                        keyboard
                    ),
                    parse_mode="HTML",
                )

            except Exception:
                pass

        return

    # --------------------------------------------------------
    # FAVORITES
    # --------------------------------------------------------

    if data.startswith(
        "profile_fav:"
    ):

        try:

            user_id = int(
                data.split(":", 1)[1]
            )

        except ValueError:

            await query.answer(
                "Invalid user.",
                show_alert=True,
            )

            return

        favorites = get_user_favorites(
            user_id
        )

        if not favorites:

            await query.answer(
                "❤️ Favorite Card မရှိသေးပါ။",
                show_alert=True,
            )

            return

        text = (
            "❤️ <b>FAVORITE CARDS</b>\n\n"
        )

        for index, card in enumerate(
            favorites,
            start=1,
        ):

            text += (
                f"{index}. "
                f"<code>{card['char_id']}</code>\n"
            )

        keyboard = [
            [
                InlineKeyboardButton(
                    "⬅️ Back",
                    callback_data=f"profile_back:{user_id}",
                )
            ]
        ]

        await query.answer()

        try:

            await query.edit_message_caption(
                caption=text,
                reply_markup=InlineKeyboardMarkup(
                    keyboard
                ),
                parse_mode="HTML",
            )

        except Exception:

            try:

                await query.edit_message_text(
                    text,
                    reply_markup=InlineKeyboardMarkup(
                        keyboard
                    ),
                    parse_mode="HTML",
                )

            except Exception:
                pass

        return

    # --------------------------------------------------------
    # BACK
    # --------------------------------------------------------

    if data.startswith(
        "profile_back:"
    ):

        await query.answer()

        user_id = int(
            data.split(":", 1)[1]
        )

        balance = get_balance(
            user_id
        )

        cards = get_user_cards(
            user_id
        )

        total_cards = get_total_card_count()

        rank = get_user_rank(
            user_id
        )

        exp = get_user_exp(
            user_id
        )

        level = get_user_level(
            user_id
        )

        percent = (
            (
                len(cards)
                / total_cards
                * 100
            )
            if total_cards
            else 0
        )

        rank_text = (
            f"#{rank}"
            if rank
            else "Unranked"
        )

        text = (
            "👤 <b>NEXUS PROFILE</b>\n\n"
            f"🆔 ID: <code>{user_id}</code>\n\n"

            "📊 <b>ACCOUNT</b>\n"
            f"💰 Coins: <b>{balance:,}</b>\n"
            f"🎖 Level: <b>{level}</b>\n"
            f"✨ EXP: <b>{exp:,}</b>\n\n"

            "🎴 <b>COLLECTION</b>\n"
            f"📦 Cards: <b>{len(cards)}</b>"
            f" / {total_cards}\n"
            f"📈 Progress: <b>{percent:.1f}%</b>\n\n"

            "🏆 <b>GLOBAL RANK</b>\n"
            f"🌎 Rank: <b>{rank_text}</b>"
        )

        keyboard = [
            [
                InlineKeyboardButton(
                    "🎴 My Harem",
                    callback_data=f"profile_harem:{user_id}",
                ),
                InlineKeyboardButton(
                    "❤️ Favorites",
                    callback_data=f"profile_fav:{user_id}",
                ),
            ]
        ]

        try:

            await query.edit_message_caption(
                caption=text,
                reply_markup=InlineKeyboardMarkup(
                    keyboard
                ),
                parse_mode="HTML",
            )

        except Exception:

            try:

                await query.edit_message_text(
                    text,
                    reply_markup=InlineKeyboardMarkup(
                        keyboard
                    ),
                    parse_mode="HTML",
                )

            except Exception:
                pass

        return

    await query.answer()
