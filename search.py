import math

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import ContextTypes

from database import (
    get_db,
    get_card,
    get_all_cards,
)


# ============================================================
# CONFIG
# ============================================================

SEARCH_PER_PAGE = 5


# ============================================================
# SEARCH DATABASE
# ============================================================

def search_cards(query):

    query = str(query).strip()

    if not query:
        return []

    with get_db() as db:

        rows = db.execute(
            """
            SELECT *
            FROM cards
            WHERE
                LOWER(char_id) LIKE LOWER(?)
                OR LOWER(name) LIKE LOWER(?)
                OR LOWER(edition) LIKE LOWER(?)
                OR LOWER(rarity) LIKE LOWER(?)
            ORDER BY char_id
            """,
            (
                f"%{query}%",
                f"%{query}%",
                f"%{query}%",
                f"%{query}%",
            ),
        ).fetchall()

    return rows


# ============================================================
# CARD TEXT
# ============================================================

def card_text(card, number=None):

    prefix = ""

    if number is not None:
        prefix = f"<b>{number}.</b> "

    return (
        f"{prefix}🎴 <b>{card['name']}</b>\n"
        f"🆔 <code>{card['char_id']}</code>\n"
        f"✨ Edition: <b>{card['edition']}</b>\n"
        f"⭐ Rarity: <b>{card['rarity']}</b>\n"
        f"💰 Price: <b>{card['price']:,}</b> Coins\n"
    )


# ============================================================
# SEARCH COMMAND
# ============================================================

async def search_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    message = update.effective_message

    if not message:
        return

    if not context.args:

        await message.reply_text(
            "🔎 <b>NEXUS CARD SEARCH</b>\n\n"
            "Card Name ဒါမှမဟုတ် Card ID နဲ့ ရှာနိုင်ပါတယ်။\n\n"
            "📌 Usage:\n"
            "<code>/search CARD_NAME</code>\n"
            "<code>/search CARD_ID</code>\n\n"
            "💡 Example:\n"
            "<code>/search Naruto</code>\n"
            "<code>/search 0021</code>\n"
            "<code>/search Premium</code>",
            parse_mode="HTML",
        )

        return

    query = " ".join(
        context.args
    ).strip()

    results = search_cards(
        query
    )

    if not results:

        await message.reply_text(
            "🔎 <b>NO RESULTS</b>\n\n"
            f"❌ <code>{query}</code> နဲ့ "
            "ကိုက်ညီတဲ့ Card မတွေ့ပါ။",
            parse_mode="HTML",
        )

        return

    await send_search_page(
        message,
        query,
        results,
        1,
    )


# ============================================================
# SEND SEARCH PAGE
# ============================================================

async def send_search_page(
    message,
    query,
    results,
    page,
):

    total_pages = max(
        1,
        math.ceil(
            len(results)
            / SEARCH_PER_PAGE
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
        * SEARCH_PER_PAGE
    )

    end = (
        start
        + SEARCH_PER_PAGE
    )

    page_results = results[
        start:end
    ]

    text = (
        "🔎 <b>NEXUS SEARCH</b>\n\n"
        f"🔍 Query: <code>{query}</code>\n"
        f"📦 Results: <b>{len(results)}</b>\n"
        f"📄 Page: <b>{page}/{total_pages}</b>\n\n"
    )

    buttons = []

    for index, card in enumerate(
        page_results,
        start=start + 1,
    ):

        text += (
            card_text(
                card,
                index,
            )
            + "\n"
        )

        buttons.append([
            InlineKeyboardButton(
                f"🎴 {card['name']}",
                callback_data=(
                    f"search_card:{card['char_id']}"
                ),
            )
        ])

    navigation = []

    if page > 1:

        navigation.append(
            InlineKeyboardButton(
                "⬅️",
                callback_data=(
                    f"search_page:"
                    f"{query}:"
                    f"{page - 1}"
                ),
            )
        )

    navigation.append(
        InlineKeyboardButton(
            f"📄 {page}/{total_pages}",
            callback_data="search_noop",
        )
    )

    if page < total_pages:

        navigation.append(
            InlineKeyboardButton(
                "➡️",
                callback_data=(
                    f"search_page:"
                    f"{query}:"
                    f"{page + 1}"
                ),
            )
        )

    buttons.append(
        navigation
    )

    await message.reply_text(
        text,
        reply_markup=InlineKeyboardMarkup(
            buttons
        ),
        parse_mode="HTML",
    )


# ============================================================
# SEARCH CALLBACK
# ============================================================

async def search_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    query_obj = update.callback_query

    data = query_obj.data or ""

    # --------------------------------------------------------
    # NO OP
    # --------------------------------------------------------

    if data == "search_noop":

        await query_obj.answer()

        return

    # --------------------------------------------------------
    # CARD DETAIL
    # --------------------------------------------------------

    if data.startswith(
        "search_card:"
    ):

        char_id = data.split(
            ":",
            1,
        )[1]

        card = get_card(
            char_id
        )

        if not card:

            await query_obj.answer(
                "❌ Card မတွေ့ပါ။",
                show_alert=True,
            )

            return

        text = (
            "🎴 <b>CARD DETAILS</b>\n\n"
            f"🎴 Name: <b>{card['name']}</b>\n"
            f"🆔 ID: <code>{card['char_id']}</code>\n\n"
            f"✨ Edition: <b>{card['edition']}</b>\n"
            f"⭐ Rarity: <b>{card['rarity']}</b>\n"
            f"💰 Price: <b>{card['price']:,}</b> Coins\n"
        )

        keyboard = [
            [
                InlineKeyboardButton(
                    "⬅️ Back",
                    callback_data=(
                        "search_back"
                    ),
                )
            ]
        ]

        await query_obj.answer()

        try:

            await query_obj.edit_message_text(
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
    # SEARCH PAGE
    # --------------------------------------------------------

    if data.startswith(
        "search_page:"
    ):

        parts = data.split(
            ":",
            2,
        )

        if len(parts) != 3:

            await query_obj.answer(
                "Invalid page.",
                show_alert=True,
            )

            return

        search_query = parts[1]

        try:

            page = int(
                parts[2]
            )

        except ValueError:

            await query_obj.answer(
                "Invalid page.",
                show_alert=True,
            )

            return

        results = search_cards(
            search_query
        )

        if not results:

            await query_obj.answer(
                "❌ Results မရှိတော့ပါ။",
                show_alert=True,
            )

            return

        total_pages = max(
            1,
            math.ceil(
                len(results)
                / SEARCH_PER_PAGE
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
            * SEARCH_PER_PAGE
        )

        end = (
            start
            + SEARCH_PER_PAGE
        )

        page_results = results[
            start:end
        ]

        text = (
            "🔎 <b>NEXUS SEARCH</b>\n\n"
            f"🔍 Query: <code>{search_query}</code>\n"
            f"📦 Results: <b>{len(results)}</b>\n"
            f"📄 Page: <b>{page}/{total_pages}</b>\n\n"
        )

        buttons = []

        for index, card in enumerate(
            page_results,
            start=start + 1,
        ):

            text += (
                card_text(
                    card,
                    index,
                )
                + "\n"
            )

            buttons.append([
                InlineKeyboardButton(
                    f"🎴 {card['name']}",
                    callback_data=(
                        f"search_card:{card['char_id']}"
                    ),
                )
            ])

        navigation = []

        if page > 1:

            navigation.append(
                InlineKeyboardButton(
                    "⬅️",
                    callback_data=(
                        f"search_page:"
                        f"{search_query}:"
                        f"{page - 1}"
                    ),
                )
            )

        navigation.append(
            InlineKeyboardButton(
                f"📄 {page}/{total_pages}",
                callback_data="search_noop",
            )
        )

        if page < total_pages:

            navigation.append(
                InlineKeyboardButton(
                    "➡️",
                    callback_data=(
                        f"search_page:"
                        f"{search_query}:"
                        f"{page + 1}"
                    ),
                )
            )

        buttons.append(
            navigation
        )

        await query_obj.answer()

        try:

            await query_obj.edit_message_text(
                text,
                reply_markup=InlineKeyboardMarkup(
                    buttons
                ),
                parse_mode="HTML",
            )

        except Exception:
            pass

        return

    # --------------------------------------------------------
    # BACK
    # --------------------------------------------------------

    if data == "search_back":

        await query_obj.answer()

        await query_obj.edit_message_text(
            "🔎 <b>NEXUS CARD SEARCH</b>\n\n"
            "Card Name / ID နဲ့ Search ပြန်လုပ်နိုင်ပါတယ်။\n\n"
            "📌 Usage:\n"
            "<code>/search CARD_NAME</code>\n"
            "<code>/search CARD_ID</code>",
            parse_mode="HTML",
        )

        return

    await query_obj.answer()
