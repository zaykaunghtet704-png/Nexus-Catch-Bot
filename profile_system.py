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
)


# ============================================================
# CONFIG
# ============================================================

CARDS_PER_PAGE = 6


# ============================================================
# USER INFORMATION
# ============================================================

def get_user_stats(user_id):

    with get_db() as db:

        row = db.execute(
            """
            SELECT
                COUNT(*) AS total_cards
            FROM user_cards
            WHERE user_id = ?
            """,
            (user_id,),
        ).fetchone()

    return int(
        row["total_cards"] or 0
    )


def get_global_rank(user_id):

    with get_db() as db:

        rows = db.execute(
            """
            SELECT
                user_id,
                COUNT(*) AS total_cards
            FROM user_cards
            GROUP BY user_id
            ORDER BY total_cards DESC, user_id ASC
            """
        ).fetchall()

    for index, row in enumerate(
        rows,
        start=1,
    ):

        if int(
            row["user_id"]
        ) == int(user_id):

            return index

    return None


# ============================================================
# CARD SORTING
# ============================================================

def sort_cards(cards):

    edition_order = {
        "premium": 1,
        "legendary": 2,
        "mythic": 3,
        "epic": 4,
        "rare": 5,
        "uncommon": 6,
        "common": 7,
    }

    def sort_key(card):

        edition = str(
            card["edition"]
        ).lower()

        return (
            edition_order.get(
                edition,
                99,
            ),
            str(
                card["char_id"]
            ),
        )

    return sorted(
        cards,
        key=sort_key,
    )


# ============================================================
# CARD LINE
# ============================================================

def card_line(
    index,
    card,
):

    return (
        f"<b>{index}.</b> "
        f"🎴 <b>{card['name']}</b>\n"
        f"   🆔 <code>{card['char_id']}</code>\n"
        f"   ✨ {card['edition']} • "
        f"⭐ {card['rarity']}\n"
    )


# ============================================================
# PROFILE COMMAND
# ============================================================

async def profile_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    message = update.effective_message
    user = update.effective_user

    if not message or not user:
        return

    target = user

    # --------------------------------------------------------
    # Reply-to-user profile
    # --------------------------------------------------------

    if message.reply_to_message:

        replied_user = (
            message.reply_to_message.from_user
        )

        if replied_user:

            target = replied_user

    total_cards = get_user_stats(
        target.id
    )

    balance = get_balance(
        target.id
    )

    rank = get_global_rank(
        target.id
    )

    username = (
        f"@{target.username}"
        if target.username
        else "No Username"
    )

    rank_text = (
        f"#{rank}"
        if rank
        else "Unranked"
    )

    text = (
        "👤 <b>NEXUS PROFILE</b>\n\n"
        f"🧑 Name: <b>{target.first_name}</b>\n"
        f"🔗 Username: <b>{username}</b>\n"
        f"🆔 ID: <code>{target.id}</code>\n\n"
        "🎴 <b>COLLECTION</b>\n"
        f"📦 Total Cards: <b>{total_cards}</b>\n"
        f"🏆 Global Rank: <b>{rank_text}</b>\n\n"
        "💰 <b>WALLET</b>\n"
        f"🪙 Coins: <b>{balance:,}</b>\n\n"
        "📖 အောက်က Button ကနေ "
        "သင့် Collection ကို ကြည့်နိုင်ပါတယ်။"
    )

    keyboard = [
        [
            InlineKeyboardButton(
                "🎴 My Harem",
                callback_data=(
                    f"profile_harem:"
                    f"{target.id}:1"
                ),
            )
        ],
        [
            InlineKeyboardButton(
                "🏆 Global Rank",
                callback_data="profile_ranking",
            )
        ],
    ]

    reply_markup = InlineKeyboardMarkup(
        keyboard
    )

    # --------------------------------------------------------
    # Profile photo
    # --------------------------------------------------------

    try:

        photos = await context.bot.get_user_profile_photos(
            user_id=target.id,
            limit=1,
        )

        if photos.total_count > 0:

            photo = (
                photos.photos[0][-1]
            )

            await message.reply_photo(
                photo=photo.file_id,
                caption=text,
                reply_markup=reply_markup,
                parse_mode="HTML",
            )

            return

    except Exception:
        pass

    await message.reply_text(
        text,
        reply_markup=reply_markup,
        parse_mode="HTML",
    )


# ============================================================
# HAREM PAGE FROM PROFILE
# ============================================================

async def send_profile_harem(
    query,
    context,
    user_id,
    page,
):

    cards = get_user_cards(
        user_id
    )

    cards = sort_cards(
        cards
    )

    if not cards:

        await query.answer(
            "🎴 Harem ထဲမှာ Card မရှိသေးပါ။",
            show_alert=True,
        )

        return

    total_pages = max(
        1,
        math.ceil(
            len(cards)
            / CARDS_PER_PAGE
        ),
    )

    page = max(
        1,
        min(
            page,
            total_pages,
        ),
    )

    start = (
        (page - 1)
        * CARDS_PER_PAGE
    )

    end = (
        start
        + CARDS_PER_PAGE
    )

    page_cards = cards[
        start:end
    ]

    text = (
        "🎴 <b>MY HAREM</b>\n\n"
        f"📦 Total Cards: <b>{len(cards)}</b>\n"
        f"📄 Page: <b>{page}/{total_pages}</b>\n\n"
    )

    for index, card in enumerate(
        page_cards,
        start=start + 1,
    ):

        text += (
            card_line(
                index,
                card,
            )
            + "\n"
        )

    navigation = []

    if page > 1:

        navigation.append(
            InlineKeyboardButton(
                "⬅️",
                callback_data=(
                    f"profile_harem:"
                    f"{user_id}:"
                    f"{page - 1}"
                ),
            )
        )

    navigation.append(
        InlineKeyboardButton(
            f"📄 {page}/{total_pages}",
            callback_data="profile_noop",
        )
    )

    if page < total_pages:

        navigation.append(
            InlineKeyboardButton(
                "➡️",
                callback_data=(
                    f"profile_harem:"
                    f"{user_id}:"
                    f"{page + 1}"
                ),
            )
        )

    keyboard = [
        navigation,
        [
            InlineKeyboardButton(
                "👤 Profile",
                callback_data=(
                    f"profile_back:"
                    f"{user_id}"
                ),
            )
        ],
    ]

    await query.answer()

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


# ============================================================
# CALLBACK
# ============================================================

async def profile_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    query = update.callback_query

    data = query.data or ""

    # --------------------------------------------------------
    # NO OP
    # --------------------------------------------------------

    if data == "profile_noop":

        await query.answer()

        return

    # --------------------------------------------------------
    # HAREM
    # --------------------------------------------------------

    if data.startswith(
        "profile_harem:"
    ):

        parts = data.split(
            ":"
        )

        if len(parts) != 3:

            await query.answer(
                "Invalid request.",
                show_alert=True,
            )

            return

        try:

            user_id = int(
                parts[1]
            )

            page = int(
                parts[2]
            )

        except ValueError:

            await query.answer(
                "Invalid request.",
                show_alert=True,
            )

            return

        await send_profile_harem(
            query,
            context,
            user_id,
            page,
        )

        return

    # --------------------------------------------------------
    # PROFILE BACK
    # --------------------------------------------------------

    if data.startswith(
        "profile_back:"
    ):

        try:

            user_id = int(
                data.split(
                    ":",
                    1,
                )[1]
            )

        except ValueError:

            await query.answer(
                "Invalid user.",
                show_alert=True,
            )

            return

        total_cards = get_user_stats(
            user_id
        )

        balance = get_balance(
            user_id
        )

        rank = get_global_rank(
            user_id
        )

        try:

            chat = await context.bot.get_chat(
                user_id
            )

            name = (
                chat.first_name
                or "Unknown"
            )

            username = (
                f"@{chat.username}"
                if getattr(
                    chat,
                    "username",
                    None,
                )
                else "No Username"
            )

        except Exception:

            name = "Unknown"
            username = "No Username"

        rank_text = (
            f"#{rank}"
            if rank
            else "Unranked"
        )

        text = (
            "👤 <b>NEXUS PROFILE</b>\n\n"
            f"🧑 Name: <b>{name}</b>\n"
            f"🔗 Username: <b>{username}</b>\n"
            f"🆔 ID: <code>{user_id}</code>\n\n"
            "🎴 <b>COLLECTION</b>\n"
            f"📦 Total Cards: <b>{total_cards}</b>\n"
            f"🏆 Global Rank: <b>{rank_text}</b>\n\n"
            "💰 <b>WALLET</b>\n"
            f"🪙 Coins: <b>{balance:,}</b>"
        )

        keyboard = [
            [
                InlineKeyboardButton(
                    "🎴 My Harem",
                    callback_data=(
                        f"profile_harem:"
                        f"{user_id}:1"
                    ),
                )
            ]
        ]

        await query.answer()

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
    # GLOBAL RANK
    # --------------------------------------------------------

    if data == "profile_ranking":

        await query.answer()

        try:

            await query.message.reply_text(
                "🏆 Global Ranking ကို "
                "<code>/top</code> နဲ့ ကြည့်နိုင်ပါတယ်။",
                parse_mode="HTML",
            )

        except Exception:
            pass

        return

    await query.answer()
