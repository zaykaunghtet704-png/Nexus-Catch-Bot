"""
NEXUS CARD BOT
Search System
Version 4

Commands:
    /search
    /search <name>
    /search <card_id>
"""

import math
import sqlite3
from html import escape

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import ContextTypes

from config import (
    DATABASE_PATH,
    SEARCH_PER_PAGE,
)


# ============================================================
# DATABASE HELPERS
# ============================================================

def connect_db():
    return sqlite3.connect(
        DATABASE_PATH
    )


def get_table_columns(
    connection,
    table_name,
):
    """
    Read table columns so this module can work with
    common card-table structures.
    """

    try:
        rows = connection.execute(
            f"PRAGMA table_info({table_name})"
        ).fetchall()

        return {
            row[1]
            for row in rows
        }

    except Exception:
        return set()


def find_card_table(
    connection,
):
    """
    Detect the card table.

    Supported common names:
        cards
        characters
        card
        character
    """

    possible_tables = [
        "cards",
        "characters",
        "card",
        "character",
    ]

    for table in possible_tables:

        try:

            row = connection.execute(
                """
                SELECT name
                FROM sqlite_master
                WHERE type='table'
                AND name=?
                """,
                (table,),
            ).fetchone()

            if row:
                return table

        except Exception:
            continue

    return None


# ============================================================
# COLUMN HELPERS
# ============================================================

def pick_column(
    columns,
    possible,
):

    for name in possible:

        if name in columns:
            return name

    return None


# ============================================================
# SEARCH CARDS
# ============================================================

def search_cards(
    search_text=None,
):
    """
    Search cards by:
        - name
        - character name
        - card id
        - char id
        - edition
        - rarity
    """

    connection = connect_db()

    try:

        table = find_card_table(
            connection
        )

        if not table:
            return []

        columns = get_table_columns(
            connection,
            table,
        )

        id_col = pick_column(
            columns,
            [
                "id",
                "char_id",
                "card_id",
                "character_id",
            ],
        )

        name_col = pick_column(
            columns,
            [
                "name",
                "card_name",
                "character_name",
            ],
        )

        edition_col = pick_column(
            columns,
            [
                "edition",
            ],
        )

        rarity_col = pick_column(
            columns,
            [
                "rarity",
                "rank",
            ],
        )

        price_col = pick_column(
            columns,
            [
                "price",
                "sell_price",
                "value",
            ],
        )

        image_col = pick_column(
            columns,
            [
                "image",
                "image_url",
                "photo",
                "photo_id",
                "file_id",
            ],
        )

        if not id_col:
            return []

        select_parts = [
            f'"{id_col}" AS char_id'
        ]

        if name_col:
            select_parts.append(
                f'"{name_col}" AS name'
            )
        else:
            select_parts.append(
                "'Unknown' AS name"
            )

        if edition_col:
            select_parts.append(
                f'"{edition_col}" AS edition'
            )
        else:
            select_parts.append(
                "'Common' AS edition"
            )

        if rarity_col:
            select_parts.append(
                f'"{rarity_col}" AS rarity'
            )
        else:
            select_parts.append(
                "'Common' AS rarity"
            )

        if price_col:
            select_parts.append(
                f'"{price_col}" AS price'
            )
        else:
            select_parts.append(
                "0 AS price"
            )

        if image_col:
            select_parts.append(
                f'"{image_col}" AS image'
            )
        else:
            select_parts.append(
                "NULL AS image"
            )

        sql = (
            "SELECT "
            + ", ".join(select_parts)
            + f' FROM "{table}"'
        )

        params = []

        # ----------------------------------------------------
        # Search
        # ----------------------------------------------------

        if search_text:

            conditions = []

            search_columns = []

            if id_col:
                search_columns.append(
                    f'CAST("{id_col}" AS TEXT) LIKE ?'
                )

            if name_col:
                search_columns.append(
                    f'"{name_col}" LIKE ? COLLATE NOCASE'
                )

            if edition_col:
                search_columns.append(
                    f'"{edition_col}" LIKE ? COLLATE NOCASE'
                )

            if rarity_col:
                search_columns.append(
                    f'"{rarity_col}" LIKE ? COLLATE NOCASE'
                )

            if search_columns:

                conditions.append(
                    "("
                    + " OR ".join(
                        search_columns
                    )
                    + ")"
                )

                value = (
                    "%"
                    + str(search_text)
                    + "%"
                )

                params = [
                    value
                    for _ in search_columns
                ]

            if conditions:

                sql += (
                    " WHERE "
                    + " AND ".join(
                        conditions
                    )
                )

        # ----------------------------------------------------
        # Sorting
        # ----------------------------------------------------

        if name_col:

            sql += (
                f' ORDER BY "{name_col}" COLLATE NOCASE ASC'
            )

        else:

            sql += (
                f' ORDER BY "{id_col}" ASC'
            )

        rows = connection.execute(
            sql,
            params,
        ).fetchall()

        result = []

        for row in rows:

            result.append({
                "char_id": row[0],
                "name": row[1],
                "edition": row[2],
                "rarity": row[3],
                "price": row[4],
                "image": row[5],
            })

        return result

    finally:

        connection.close()


# ============================================================
# FORMAT CARD
# ============================================================

def format_card(
    card,
    number,
):

    char_id = escape(
        str(card["char_id"])
    )

    name = escape(
        str(card["name"] or "Unknown")
    )

    edition = escape(
        str(card["edition"] or "Common")
    )

    rarity = escape(
        str(card["rarity"] or "Common")
    )

    try:
        price = int(
            card["price"] or 0
        )
    except (
        ValueError,
        TypeError,
    ):
        price = 0

    return (
        f"<b>{number}.</b> "
        f"🎴 <b>{name}</b>\n"
        f"   🆔 <code>{char_id}</code>\n"
        f"   ✨ {edition}\n"
        f"   ⭐ {rarity}\n"
        f"   💰 {price:,} Coins\n"
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

    # --------------------------------------------------------
    # Get search text
    # --------------------------------------------------------

    search_text = None

    if context.args:

        search_text = " ".join(
            context.args
        ).strip()

    cards = search_cards(
        search_text
    )

    if not cards:

        if search_text:

            text = (
                "🔎 <b>NEXUS SEARCH</b>\n\n"
                f"❌ <b>{escape(search_text)}</b> "
                "နဲ့ ကိုက်ညီတဲ့ Card မတွေ့ပါ။\n\n"
                "💡 Card Name / ID / Edition / "
                "Rarity နဲ့ ပြန်ရှာကြည့်ပါ။"
            )

        else:

            text = (
                "🔎 <b>NEXUS SEARCH</b>\n\n"
                "📭 Bot ထဲမှာ Card မရှိသေးပါ။"
            )

        await message.reply_text(
            text,
            parse_mode="HTML",
        )

        return

    await send_search_page(
        message=message,
        cards=cards,
        page=1,
        search_text=search_text,
    )


# ============================================================
# SEND SEARCH PAGE
# ============================================================

async def send_search_page(
    message,
    cards,
    page,
    search_text=None,
):

    total = len(cards)

    total_pages = max(
        1,
        math.ceil(
            total
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

    page_cards = cards[
        start:end
    ]

    if search_text:

        title = (
            "🔎 <b>NEXUS SEARCH</b>\n"
            f"🔍 Query: <code>{escape(search_text)}</code>\n"
        )

    else:

        title = (
            "🔎 <b>NEXUS CARD DATABASE</b>\n"
        )

    text = (
        title
        + "\n"
        f"🎴 Results: <b>{total}</b>\n"
        f"📄 Page: <b>{page}/{total_pages}</b>\n\n"
    )

    for index, card in enumerate(
        page_cards,
        start=start + 1,
    ):

        text += (
            format_card(
                card,
                index,
            )
            + "\n"
        )

    keyboard = []

    # --------------------------------------------------------
    # Card buttons
    # --------------------------------------------------------

    for card in page_cards:

        name = str(
            card["name"]
            or "Card"
        )

        # Telegram callback data has a size limit.
        # Keep ID short.
        callback_id = str(
            card["char_id"]
        )

        keyboard.append([
            InlineKeyboardButton(
                f"🎴 {name[:35]}",
                callback_data=(
                    f"search_card:"
                    f"{callback_id}"
                ),
            )
        ])

    # --------------------------------------------------------
    # Pagination
    # --------------------------------------------------------

    navigation = []

    query_value = (
        search_text
        if search_text
        else "_"
    )

    # Keep callback reasonably short
    query_value = str(
        query_value
    )[:25]

    if page > 1:

        navigation.append(
            InlineKeyboardButton(
                "⬅️",
                callback_data=(
                    f"search_page:"
                    f"{page - 1}:"
                    f"{query_value}"
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
                    f"{page + 1}:"
                    f"{query_value}"
                ),
            )
        )

    keyboard.append(
        navigation
    )

    await message.reply_text(
        text,
        reply_markup=InlineKeyboardMarkup(
            keyboard
        ),
        parse_mode="HTML",
    )


# ============================================================
# CALLBACK
# ============================================================

async def search_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    query = update.callback_query

    data = query.data or ""

    # ========================================================
    # NO OP
    # ========================================================

    if data == "search_noop":

        await query.answer()

        return

    # ========================================================
    # CARD DETAIL
    # ========================================================

    if data.startswith(
        "search_card:"
    ):

        char_id = data.split(
            ":",
            1,
        )[1]

        cards = search_cards(
            char_id
        )

        card = None

        for item in cards:

            if str(
                item["char_id"]
            ) == str(char_id):

                card = item
                break

        if not card:

            await query.answer(
                "❌ Card မတွေ့ပါ။",
                show_alert=True,
            )

            return

        name = escape(
            str(
                card["name"]
                or "Unknown"
            )
        )

        edition = escape(
            str(
                card["edition"]
                or "Common"
            )
        )

        rarity = escape(
            str(
                card["rarity"]
                or "Common"
            )
        )

        try:

            price = int(
                card["price"]
                or 0
            )

        except (
            ValueError,
            TypeError,
        ):

            price = 0

        text = (
            "🎴 <b>CARD INFORMATION</b>\n\n"
            f"🎴 Name: <b>{name}</b>\n"
            f"🆔 ID: <code>{escape(str(char_id))}</code>\n\n"
            f"✨ Edition: <b>{edition}</b>\n"
            f"⭐ Rarity: <b>{rarity}</b>\n"
            f"💰 Price: <b>{price:,} Coins</b>\n\n"
            "🔎 Search Result"
        )

        keyboard = [
            [
                InlineKeyboardButton(
                    "⬅️ Search",
                    callback_data="search_back",
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

    # ========================================================
    # SEARCH BACK
    # ========================================================

    if data == "search_back":

        await query.answer()

        try:

            await query.edit_message_text(
                "🔎 <b>NEXUS SEARCH</b>\n\n"
                "💡 Search ပြန်လုပ်ရန်\n"
                "<code>/search CardName</code>\n\n"
                "🆔 ID နဲ့လည်း ရှာနိုင်ပါတယ်။",
                parse_mode="HTML",
            )

        except Exception:
            pass

        return

    # ========================================================
    # PAGINATION
    # ========================================================

    if data.startswith(
        "search_page:"
    ):

        parts = data.split(
            ":",
            2,
        )

        if len(parts) != 3:

            await query.answer(
                "Invalid page.",
                show_alert=True,
            )

            return

        try:

            page = int(
                parts[1]
            )

        except ValueError:

            await query.answer(
                "Invalid page.",
                show_alert=True,
            )

            return

        search_text = parts[2]

        if search_text == "_":
            search_text = None

        cards = search_cards(
            search_text
        )

        if not cards:

            await query.answer(
                "❌ Results မတွေ့ပါ။",
                show_alert=True,
            )

            return

        total = len(cards)

        total_pages = max(
            1,
            math.ceil(
                total
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

        page_cards = cards[
            start:end
        ]

        if search_text:

            title = (
                "🔎 <b>NEXUS SEARCH</b>\n"
                f"🔍 Query: "
                f"<code>{escape(search_text)}</code>\n"
            )

        else:

            title = (
                "🔎 <b>NEXUS CARD DATABASE</b>\n"
            )

        text = (
            title
            + "\n"
            f"🎴 Results: <b>{total}</b>\n"
            f"📄 Page: <b>{page}/{total_pages}</b>\n\n"
        )

        for index, card in enumerate(
            page_cards,
            start=start + 1,
        ):

            text += (
                format_card(
                    card,
                    index,
                )
                + "\n"
            )

        keyboard = []

        for card in page_cards:

            name = str(
                card["name"]
                or "Card"
            )

            keyboard.append([
                InlineKeyboardButton(
                    f"🎴 {name[:35]}",
                    callback_data=(
                        f"search_card:"
                        f"{card['char_id']}"
                    ),
                )
            ])

        navigation = []

        query_value = (
            search_text
            if search_text
            else "_"
        )

        query_value = str(
            query_value
        )[:25]

        if page > 1:

            navigation.append(
                InlineKeyboardButton(
                    "⬅️",
                    callback_data=(
                        f"search_page:"
                        f"{page - 1}:"
                        f"{query_value}"
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
                        f"{page + 1}:"
                        f"{query_value}"
                    ),
                )
            )

        keyboard.append(
            navigation
        )

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

    await query.answer()
