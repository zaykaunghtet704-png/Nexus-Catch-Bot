import math
import html
import logging

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import ContextTypes

from database import (
    get_db,
    get_card,
)

logger = logging.getLogger(__name__)


# ============================================================
# CONFIG
# ============================================================

CARDS_PER_PAGE = 5
TOP_LIMIT = 15


# ============================================================
# HTML ESCAPE
# ============================================================

def esc(value):
    return html.escape(
        str(value or "")
    )


# ============================================================
# SEARCH CARDS
# ============================================================

def search_cards(query):

    query = str(query).strip()

    if not query:
        return []

    try:

        with get_db() as db:

            rows = db.execute(
                """
                SELECT *
                FROM cards
                WHERE active = 1
                  AND (
                    LOWER(char_id) LIKE LOWER(?)
                    OR LOWER(name) LIKE LOWER(?)
                    OR LOWER(edition) LIKE LOWER(?)
                    OR CAST(rarity AS TEXT) LIKE ?
                  )
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

    except Exception as e:

        logger.exception(
            "search_cards error: %s",
            e,
        )

        return []


# ============================================================
# GET ALL ACTIVE CARDS
# ============================================================

def get_all_stored_cards():

    try:

        with get_db() as db:

            rows = db.execute(
                """
                SELECT *
                FROM cards
                WHERE active = 1
                ORDER BY char_id
                """
            ).fetchall()

        return rows

    except Exception as e:

        logger.exception(
            "get_all_stored_cards error: %s",
            e,
        )

        return []


# ============================================================
# CARD SHORT TEXT
# ============================================================

def card_short_text(
    card,
    number=None,
):

    prefix = ""

    if number is not None:
        prefix = (
            f"<b>{number}.</b> "
        )

    try:
        price = int(
            card["price"] or 0
        )
    except Exception:
        price = 0

    return (
        f"{prefix}🎴 "
        f"<b>{esc(card['name'])}</b>\n"
        f"   🆔 <code>{esc(card['char_id'])}</code>\n"
        f"   ✨ {esc(card['edition'])} "
        f"• ⭐ {esc(card['rarity'])}\n"
        f"   💰 <b>{price:,}</b> Coins\n"
    )


# ============================================================
# CARD DETAIL TEXT
# ============================================================

def build_card_detail(
    card,
):

    try:
        price = int(
            card["price"] or 0
        )
    except Exception:
        price = 0

    description = ""

    try:
        description = (
            card["description"]
            or ""
        )
    except Exception:
        pass

    text = (
        "╔══════════════════════╗\n"
        "       🎴 <b>NEXUS CARD</b>\n"
        "╚══════════════════════╝\n\n"

        f"🎴 <b>{esc(card['name'])}</b>\n\n"

        f"🆔 Card ID: "
        f"<code>{esc(card['char_id'])}</code>\n"

        f"✨ Edition: "
        f"<b>{esc(card['edition'])}</b>\n"

        f"⭐ Rarity: "
        f"<b>{esc(card['rarity'])}</b>\n"

        f"💰 Price: "
        f"<b>{price:,}</b> Coins\n"
    )

    if description:

        text += (
            "\n📖 <b>Description</b>\n"
            f"{esc(description)}\n"
        )

    return text


# ============================================================
# GET GLOBAL TOP 15
# ============================================================

def get_global_card_top(
    char_id,
):

    try:

        with get_db() as db:

            rows = db.execute(
                """
                SELECT
                    user_id,
                    COUNT(*) AS quantity
                FROM user_cards
                WHERE char_id = ?
                GROUP BY user_id
                ORDER BY quantity DESC,
                         user_id ASC
                LIMIT ?
                """,
                (
                    char_id,
                    TOP_LIMIT,
                ),
            ).fetchall()

        return rows

    except Exception as e:

        logger.exception(
            "get_global_card_top error: %s",
            e,
        )

        return []


# ============================================================
# GET GROUP TOP 15
# ============================================================

def get_group_card_top(
    char_id,
    group_id,
):

    if not group_id:
        return []

    try:

        with get_db() as db:

            rows = db.execute(
                """
                SELECT
                    uc.user_id,
                    COUNT(*) AS quantity
                FROM user_cards uc
                INNER JOIN users u
                    ON u.user_id = uc.user_id
                WHERE uc.char_id = ?
                GROUP BY uc.user_id
                ORDER BY quantity DESC,
                         uc.user_id ASC
                LIMIT ?
                """,
                (
                    char_id,
                    TOP_LIMIT,
                ),
            ).fetchall()

        return rows

    except Exception as e:

        logger.exception(
            "get_group_card_top error: %s",
            e,
        )

        return []


# ============================================================
# USER DISPLAY NAME
# ============================================================

def get_user_display_name(
    user_id,
):

    try:

        with get_db() as db:

            row = db.execute(
                """
                SELECT *
                FROM users
                WHERE user_id = ?
                LIMIT 1
                """,
                (user_id,),
            ).fetchone()

    except Exception:

        row = None

    if not row:

        return (
            f"User {user_id}"
        )

    try:

        keys = row.keys()

        for key in (
            "username",
            "first_name",
            "name",
            "full_name",
        ):

            if key in keys:

                value = row[key]

                if value:

                    value = str(
                        value
                    ).strip()

                    if key == "username":

                        if value.startswith("@"):
                            return value

                        return (
                            f"@{value}"
                        )

                    return value

    except Exception:
        pass

    return (
        f"User {user_id}"
    )


# ============================================================
# BUILD TOP LIST
# ============================================================

def build_top_lists(
    char_id,
    group_id=None,
):

    text = ""

    # --------------------------------------------------------
    # GLOBAL
    # --------------------------------------------------------

    global_rows = (
        get_global_card_top(
            char_id
        )
    )

    text += (
        "\n🌍 <b>GLOBAL TOP 15 OWNERS</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
    )

    if not global_rows:

        text += (
            "No one owns this card yet.\n"
        )

    else:

        medals = {
            1: "🥇",
            2: "🥈",
            3: "🥉",
        }

        for index, row in enumerate(
            global_rows,
            start=1,
        ):

            user_id = int(
                row["user_id"]
            )

            quantity = int(
                row["quantity"] or 0
            )

            rank = medals.get(
                index,
                f"#{index}",
            )

            name = esc(
                get_user_display_name(
                    user_id
                )
            )

            text += (
                f"{rank} "
                f"<b>{name}</b> — "
                f"🎴 <b>{quantity}</b>\n"
            )

    # --------------------------------------------------------
    # GROUP
    # --------------------------------------------------------

    text += (
        "\n👥 <b>GROUP TOP 15 OWNERS</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
    )

    if not group_id:

        text += (
            "Group ranking is available "
            "inside a group.\n"
        )

    else:

        group_rows = (
            get_group_card_top(
                char_id,
                group_id,
            )
        )

        if not group_rows:

            text += (
                "No owner found.\n"
            )

        else:

            medals = {
                1: "🥇",
                2: "🥈",
                3: "🥉",
            }

            for index, row in enumerate(
                group_rows,
                start=1,
            ):

                user_id = int(
                    row["user_id"]
                )

                quantity = int(
                    row["quantity"] or 0
                )

                rank = medals.get(
                    index,
                    f"#{index}",
                )

                name = esc(
                    get_user_display_name(
                        user_id
                    )
                )

                text += (
                    f"{rank} "
                    f"<b>{name}</b> — "
                    f"🎴 <b>{quantity}</b>\n"
                )

    return text


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
    # NO QUERY
    # --------------------------------------------------------

    if not context.args:

        keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "📚 VIEW ALL CARDS",
                        callback_data=(
                            "search_catalog:1"
                        ),
                    )
                ]
            ]
        )

        await message.reply_text(
            "╔══════════════════════╗\n"
            "       🔎 <b>NEXUS SEARCH</b>\n"
            "╚══════════════════════╝\n\n"

            "Card Name / Card ID နဲ့ "
            "ရှာနိုင်ပါတယ်။\n\n"

            "📌 <b>Usage</b>\n"
            "<code>/search CARD_NAME</code>\n"
            "<code>/search CARD_ID</code>\n\n"

            "💡 <b>Example</b>\n"
            "<code>/search Naruto</code>\n"
            "<code>/search NXS001</code>\n"
            "<code>/search Premium</code>\n\n"

            "👇 Bot ထဲမှာ သိမ်းထားတဲ့ "
            "Card အားလုံးကို ကြည့်ချင်ရင် "
            "အောက်က Button ကိုနှိပ်ပါ။",

            reply_markup=keyboard,
            parse_mode="HTML",
        )

        return

    # --------------------------------------------------------
    # QUERY
    # --------------------------------------------------------

    query = " ".join(
        context.args
    ).strip()

    results = search_cards(
        query
    )

    # --------------------------------------------------------
    # NO RESULT
    # --------------------------------------------------------

    if not results:

        keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "📚 VIEW ALL CARDS",
                        callback_data=(
                            "search_catalog:1"
                        ),
                    )
                ]
            ]
        )

        await message.reply_text(
            "🔎 <b>SEARCH RESULT</b>\n\n"
            f"🔍 Query: "
            f"<code>{esc(query)}</code>\n\n"

            "❌ ကိုက်ညီတဲ့ Card မတွေ့ပါ။\n\n"

            "👇 Stored Cards အားလုံးကို "
            "ကြည့်နိုင်ပါတယ်။",

            reply_markup=keyboard,
            parse_mode="HTML",
        )

        return

    # --------------------------------------------------------
    # RESULT + BUTTON
    # --------------------------------------------------------

    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "📚 VIEW ALL STORED CARDS",
                    callback_data=(
                        "search_catalog:1"
                    ),
                )
            ],
            [
                InlineKeyboardButton(
                    f"🔍 {len(results)} CARDS FOUND",
                    callback_data="search_noop",
                )
            ],
        ]
    )

    await message.reply_text(
        "╔══════════════════════╗\n"
        "       🔎 <b>SEARCH RESULT</b>\n"
        "╚══════════════════════╝\n\n"

        f"🔍 Query: "
        f"<code>{esc(query)}</code>\n"

        f"🎴 Found: "
        f"<b>{len(results)}</b> Cards\n\n"

        "👇 အောက်က Button ကိုနှိပ်ပြီး "
        "Stored Cards တွေထဲက Card ကိုရွေးပါ။",

        reply_markup=keyboard,
        parse_mode="HTML",
    )


# ============================================================
# BUILD CARD CATALOG
# ============================================================

def build_catalog(
    cards,
    page,
):

    total = len(cards)

    total_pages = max(
        1,
        math.ceil(
            total
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
        "╔══════════════════════╗\n"
        "      📚 <b>NEXUS CARD LIST</b>\n"
        "╚══════════════════════╝\n\n"

        f"🎴 Total Cards: "
        f"<b>{total}</b>\n"

        f"📄 Page: "
        f"<b>{page}/{total_pages}</b>\n\n"

        "👇 Card တစ်ခုရွေးပါ။\n\n"
    )

    buttons = []

    for index, card in enumerate(
        page_cards,
        start=start + 1,
    ):

        text += (
            card_short_text(
                card,
                index,
            )
            + "\n"
        )

        buttons.append(
            [
                InlineKeyboardButton(
                    f"🎴 {card['name']}",
                    callback_data=(
                        f"search_card:"
                        f"{card['char_id']}"
                    ),
                )
            ]
        )

    # --------------------------------------------------------
    # NAVIGATION
    # --------------------------------------------------------

    navigation = []

    if page > 1:

        navigation.append(
            InlineKeyboardButton(
                "⬅️ PREV",
                callback_data=(
                    f"search_catalog:"
                    f"{page - 1}"
                ),
            )
        )

    navigation.append(
        InlineKeyboardButton(
            f"📄 {page}/{total_pages}",
            callback_data=(
                "search_noop"
            ),
        )
    )

    if page < total_pages:

        navigation.append(
            InlineKeyboardButton(
                "NEXT ➡️",
                callback_data=(
                    f"search_catalog:"
                    f"{page + 1}"
                ),
            )
        )

    buttons.append(
        navigation
    )

    return (
        text,
        InlineKeyboardMarkup(
            buttons
        ),
    )


# ============================================================
# SHOW CARD DETAIL
# ============================================================

async def show_card_detail(
    query_obj,
    card,
):

    message = (
        query_obj.message
    )

    if not message:
        return

    group_id = (
        message.chat_id
    )

    text = (
        build_card_detail(
            card
        )
        + build_top_lists(
            str(card["char_id"]),
            group_id,
        )
    )

    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "⬅️ BACK TO CARD LIST",
                    callback_data=(
                        "search_catalog:1"
                    ),
                )
            ]
        ]
    )

    await query_obj.answer()

    image_file_id = ""

    video_file_id = ""

    media_type = ""

    try:
        image_file_id = (
            card["image_file_id"]
            or ""
        )
    except Exception:
        pass

    try:
        video_file_id = (
            card["video_file_id"]
            or ""
        )
    except Exception:
        pass

    try:
        media_type = str(
            card["media_type"]
            or ""
        ).lower()
    except Exception:
        pass

    # --------------------------------------------------------
    # EDIT EXISTING MEDIA MESSAGE
    # --------------------------------------------------------

    try:

        if (
            message.photo
            and image_file_id
        ):

            await message.edit_caption(
                caption=text,
                reply_markup=keyboard,
                parse_mode="HTML",
            )

            return

        if (
            message.video
            and video_file_id
        ):

            await message.edit_caption(
                caption=text,
                reply_markup=keyboard,
                parse_mode="HTML",
            )

            return

    except Exception as e:

        logger.warning(
            "edit media detail failed: %s",
            e,
        )

    # --------------------------------------------------------
    # SEND PHOTO
    # --------------------------------------------------------

    if image_file_id:

        try:

            await message.reply_photo(
                photo=image_file_id,
                caption=text,
                reply_markup=keyboard,
                parse_mode="HTML",
            )

            return

        except Exception as e:

            logger.warning(
                "send card photo failed: %s",
                e,
            )

    # --------------------------------------------------------
    # SEND VIDEO
    # --------------------------------------------------------

    if (
        media_type == "video"
        and video_file_id
    ):

        try:

            await message.reply_video(
                video=video_file_id,
                caption=text,
                reply_markup=keyboard,
                parse_mode="HTML",
            )

            return

        except Exception as e:

            logger.warning(
                "send card video failed: %s",
                e,
            )

    # --------------------------------------------------------
    # TEXT FALLBACK
    # --------------------------------------------------------

    try:

        await message.reply_text(
            text,
            reply_markup=keyboard,
            parse_mode="HTML",
        )

    except Exception as e:

        logger.exception(
            "card detail send failed: %s",
            e,
        )


# ============================================================
# CALLBACK
# ============================================================

async def search_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    query_obj = (
        update.callback_query
    )

    if not query_obj:
        return

    data = (
        query_obj.data
        or ""
    )

    # ========================================================
    # NO OP
    # ========================================================

    if data == "search_noop":

        await query_obj.answer()

        return

    # ========================================================
    # CARD CATALOG
    # ========================================================

    if data.startswith(
        "search_catalog:"
    ):

        try:

            page = int(
                data.split(
                    ":",
                    1,
                )[1]
            )

        except (
            ValueError,
            IndexError,
        ):

            page = 1

        cards = (
            get_all_stored_cards()
        )

        if not cards:

            await query_obj.answer(
                "❌ Stored Card မရှိသေးပါ။",
                show_alert=True,
            )

            return

        text, markup = (
            build_catalog(
                cards,
                page,
            )
        )

        await query_obj.answer()

        try:

            message = (
                query_obj.message
            )

            if (
                message
                and (
                    message.photo
                    or message.video
                )
            ):

                await query_obj.edit_message_caption(
                    caption=text,
                    reply_markup=markup,
                    parse_mode="HTML",
                )

            else:

                await query_obj.edit_message_text(
                    text=text,
                    reply_markup=markup,
                    parse_mode="HTML",
                )

        except Exception as e:

            logger.warning(
                "catalog edit failed: %s",
                e,
            )

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

        card = get_card(
            char_id
        )

        if not card:

            await query_obj.answer(
                "❌ Card မတွေ့ပါ။",
                show_alert=True,
            )

            return

        await show_card_detail(
            query_obj,
            card,
        )

        return

    # ========================================================
    # BACK
    # ========================================================

    if data == "search_back":

        await query_obj.answer()

        try:

            await query_obj.edit_message_text(
                "🔎 <b>NEXUS CARD SEARCH</b>\n\n"
                "Card Name / Card ID နဲ့ "
                "Search ပြန်လုပ်နိုင်ပါတယ်။\n\n"
                "📌 <code>/search CARD_NAME</code>\n"
                "📌 <code>/search CARD_ID</code>",
                parse_mode="HTML",
            )

        except Exception:
            pass

        return

    # ========================================================
    # UNKNOWN SEARCH CALLBACK
    # ========================================================

    await query_obj.answer()
