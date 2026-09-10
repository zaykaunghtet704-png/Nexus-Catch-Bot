"""
NEXUS CARD BOT
Search System
V5

/search
/search <card name>
/search <card id>

Flow:
    /search Naruto
          ↓
    Search Result
          ↓
    🔎 Open Cards
          ↓
    Card list + pagination
          ↓
    Select Card
          ↓
    Card Image + Details
          ↓
    Global Top 15 + Group Top 15
"""

import math
from html import escape

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


# ============================================================
# CONFIG
# ============================================================

SEARCH_PER_PAGE = 5
TOP_LIMIT = 15


# ============================================================
# SAFE VALUE
# ============================================================

def safe_int(value, default=0):
    try:
        return int(value or 0)
    except (ValueError, TypeError):
        return default


def safe_text(value, default=""):
    if value is None:
        return default

    return str(value)


# ============================================================
# SEARCH DATABASE
# ============================================================

def search_cards(search_text=None):
    """
    Search active cards by:

        - char_id
        - name
        - edition
        - rarity

    Only active cards are shown.
    """

    query = ""

    if search_text is not None:
        query = str(search_text).strip()

    with get_db() as db:

        if query:

            value = f"%{query}%"

            rows = db.execute(
                """
                SELECT
                    id,
                    char_id,
                    name,
                    edition,
                    rarity,
                    price,
                    image_file_id,
                    video_file_id,
                    media_type,
                    description,
                    drop_weight,
                    exp_reward,
                    active
                FROM cards
                WHERE active = 1
                  AND (
                        LOWER(char_id) LIKE LOWER(?)
                     OR LOWER(name) LIKE LOWER(?)
                     OR LOWER(edition) LIKE LOWER(?)
                     OR CAST(rarity AS TEXT) LIKE ?
                  )
                ORDER BY
                    CAST(
                        CASE
                            WHEN char_id GLOB 'NXS[0-9]*'
                            THEN SUBSTR(char_id, 4)
                            ELSE char_id
                        END
                        AS INTEGER
                    ),
                    char_id ASC
                """,
                (
                    value,
                    value,
                    value,
                    value,
                ),
            ).fetchall()

        else:

            rows = db.execute(
                """
                SELECT
                    id,
                    char_id,
                    name,
                    edition,
                    rarity,
                    price,
                    image_file_id,
                    video_file_id,
                    media_type,
                    description,
                    drop_weight,
                    exp_reward,
                    active
                FROM cards
                WHERE active = 1
                ORDER BY
                    CAST(
                        CASE
                            WHEN char_id GLOB 'NXS[0-9]*'
                            THEN SUBSTR(char_id, 4)
                            ELSE char_id
                        END
                        AS INTEGER
                    ),
                    char_id ASC
                """
            ).fetchall()

    return rows


# ============================================================
# GET ONE CARD
# ============================================================

def get_card_full(char_id):
    """
    Get complete active card information.
    """

    with get_db() as db:

        row = db.execute(
            """
            SELECT
                id,
                char_id,
                name,
                edition,
                rarity,
                price,
                image_file_id,
                video_file_id,
                media_type,
                description,
                drop_weight,
                exp_reward,
                active
            FROM cards
            WHERE char_id = ?
              AND active = 1
            LIMIT 1
            """,
            (str(char_id),),
        ).fetchone()

    return row


# ============================================================
# CARD OWNERS
# ============================================================

def get_global_card_owners(char_id, limit=TOP_LIMIT):
    """
    Global Top owners of a specific card.

    Quantity is calculated from user_cards rows.
    """

    with get_db() as db:

        rows = db.execute(
            """
            SELECT
                uc.user_id,
                COUNT(*) AS quantity
            FROM user_cards uc
            WHERE uc.char_id = ?
            GROUP BY uc.user_id
            ORDER BY quantity DESC, uc.user_id ASC
            LIMIT ?
            """,
            (
                str(char_id),
                int(limit),
            ),
        ).fetchall()

    return rows


def get_group_card_owners(
    char_id,
    group_id,
    limit=TOP_LIMIT,
):
    """
    Group Top owners of a specific card.

    A user is considered a group owner when
    that user is a member of the current Telegram group.
    """

    if not group_id:
        return []

    with get_db() as db:

        # ----------------------------------------------------
        # First try users who are registered in this group.
        #
        # This supports databases where group membership
        # is tracked through a groups table.
        # ----------------------------------------------------

        try:

            rows = db.execute(
                """
                SELECT
                    uc.user_id,
                    COUNT(*) AS quantity
                FROM user_cards uc
                INNER JOIN users u
                    ON u.user_id = uc.user_id
                INNER JOIN groups g
                    ON g.group_id = ?
                WHERE uc.char_id = ?
                GROUP BY uc.user_id
                ORDER BY quantity DESC, uc.user_id ASC
                LIMIT ?
                """,
                (
                    str(group_id),
                    str(char_id),
                    int(limit),
                ),
            ).fetchall()

            if rows:
                return rows

        except Exception:
            pass

        # ----------------------------------------------------
        # Fallback:
        #
        # If the database doesn't keep per-group membership,
        # use users who have a stored group_id.
        # ----------------------------------------------------

        try:

            rows = db.execute(
                """
                SELECT
                    uc.user_id,
                    COUNT(*) AS quantity
                FROM user_cards uc
                INNER JOIN users u
                    ON u.user_id = uc.user_id
                WHERE uc.char_id = ?
                  AND (
                        u.group_id = ?
                     OR u.last_group_id = ?
                  )
                GROUP BY uc.user_id
                ORDER BY quantity DESC, uc.user_id ASC
                LIMIT ?
                """,
                (
                    str(char_id),
                    str(group_id),
                    str(group_id),
                    int(limit),
                ),
            ).fetchall()

            return rows

        except Exception:

            return []


# ============================================================
# USER DISPLAY NAME
# ============================================================

async def get_user_display_name(
    context,
    user_id,
):
    """
    Try to get Telegram display name.

    If the user cannot be fetched, show user ID.
    """

    try:

        user = await context.bot.get_chat(
            chat_id=int(user_id)
        )

        if getattr(user, "username", None):

            return f"@{user.username}"

        full_name = getattr(
            user,
            "full_name",
            None,
        )

        if full_name:
            return full_name

    except Exception:
        pass

    return f"User {user_id}"


# ============================================================
# CARD LIST TEXT
# ============================================================

def format_card_list_item(
    card,
    number,
):
    name = escape(
        safe_text(
            card["name"],
            "Unknown",
        )
    )

    char_id = escape(
        safe_text(
            card["char_id"],
            "-",
        )
    )

    edition = escape(
        safe_text(
            card["edition"],
            "Common",
        )
    )

    rarity = escape(
        safe_text(
            card["rarity"],
            "1",
        )
    )

    price = safe_int(
        card["price"]
    )

    return (
        f"<b>{number}.</b> 🎴 "
        f"<b>{name}</b>\n"
        f"   🆔 <code>{char_id}</code>\n"
        f"   ✨ Edition: <b>{edition}</b>\n"
        f"   ⭐ Rarity: <b>{rarity}</b>\n"
        f"   🪙 Price: <b>{price:,}</b> Coins\n"
    )


# ============================================================
# CARD DETAIL TEXT
# ============================================================

def format_card_detail(card):

    name = escape(
        safe_text(
            card["name"],
            "Unknown",
        )
    )

    char_id = escape(
        safe_text(
            card["char_id"],
            "-",
        )
    )

    edition = escape(
        safe_text(
            card["edition"],
            "Common",
        )
    )

    rarity = escape(
        safe_text(
            card["rarity"],
            "1",
        )
    )

    description = escape(
        safe_text(
            card["description"],
            "",
        )
    ).strip()

    price = safe_int(
        card["price"]
    )

    exp_reward = safe_int(
        card["exp_reward"]
    )

    text = (
        "🎴 <b>NEXUS CARD</b>\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
        f"🎴 <b>{name}</b>\n\n"
        f"🆔 ID: <code>{char_id}</code>\n"
        f"✨ Edition: <b>{edition}</b>\n"
        f"⭐ Rarity: <b>{rarity}</b>\n"
        f"🪙 Price: <b>{price:,}</b> Coins\n"
        f"⚡ EXP: <b>{exp_reward:,}</b>\n"
    )

    if description:

        text += (
            "\n📝 <b>Description</b>\n"
            f"{description}\n"
        )

    text += (
        "\n━━━━━━━━━━━━━━━━━━"
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

    search_text = None

    if context.args:

        search_text = " ".join(
            context.args
        ).strip()

    # --------------------------------------------------------
    # No argument = all cards
    # --------------------------------------------------------

    cards = search_cards(
        search_text
    )

    if not cards:

        if search_text:

            text = (
                "🔎 <b>NEXUS SEARCH</b>\n\n"
                f"❌ <b>{escape(search_text)}</b>\n"
                "နဲ့ ကိုက်ညီတဲ့ Card မတွေ့ပါ။\n\n"
                "💡 Card Name / ID / Edition / "
                "Rarity နဲ့ ပြန်ရှာကြည့်ပါ။"
            )

        else:

            text = (
                "🔎 <b>NEXUS CARD DATABASE</b>\n\n"
                "📭 Bot ထဲမှာ Card မရှိသေးပါ။"
            )

        await message.reply_text(
            text,
            parse_mode="HTML",
        )

        return

    # --------------------------------------------------------
    # Search result first
    # --------------------------------------------------------

    query_display = (
        search_text
        if search_text
        else "All Cards"
    )

    result_text = (
        "🔎 <b>NEXUS SEARCH RESULT</b>\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
        f"🔍 Search: <code>"
        f"{escape(query_display)}</code>\n"
        f"🎴 Found: <b>{len(cards)}</b> Cards\n\n"
        "👇 အောက်က button ကိုနှိပ်ပြီး\n"
        "Card List ကိုကြည့်ပါ။"
    )

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "🔎  OPEN CARD LIST",
                callback_data=(
                    f"search_open:"
                    f"{'_' if not search_text else '1'}"
                ),
            )
        ]
    ])

    await message.reply_text(
        result_text,
        reply_markup=keyboard,
        parse_mode="HTML",
    )


# ============================================================
# BUILD PAGE
# ============================================================

def build_search_page(
    cards,
    page,
    search_text=None,
):
    total = len(cards)

    total_pages = max(
        1,
        math.ceil(
            total / SEARCH_PER_PAGE
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

    query_display = (
        search_text
        if search_text
        else "All Cards"
    )

    text = (
        "🎴 <b>NEXUS CARD DATABASE</b>\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
        f"🔍 Search: <code>"
        f"{escape(query_display)}</code>\n"
        f"📦 Total: <b>{total}</b>\n"
        f"📄 Page: <b>{page}/{total_pages}</b>\n\n"
    )

    for index, card in enumerate(
        page_cards,
        start=start + 1,
    ):

        text += (
            format_card_list_item(
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

        name = safe_text(
            card["name"],
            "Card",
        )

        char_id = safe_text(
            card["char_id"],
            "",
        )

        keyboard.append([
            InlineKeyboardButton(
                f"🎴 {name[:35]}",
                callback_data=(
                    f"search_card:{char_id}"
                ),
            )
        ])

    # --------------------------------------------------------
    # Pagination
    # --------------------------------------------------------

    navigation = []

    if page > 1:

        navigation.append(
            InlineKeyboardButton(
                "⬅️",
                callback_data=(
                    f"search_page:"
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
                    f"{page + 1}"
                ),
            )
        )

    if navigation:

        keyboard.append(
            navigation
        )

    # --------------------------------------------------------
    # Back to search result
    # --------------------------------------------------------

    keyboard.append([
        InlineKeyboardButton(
            "🔎 Back to Search",
            callback_data="search_back",
        )
    ])

    return (
        text,
        InlineKeyboardMarkup(keyboard),
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

    text, markup = build_search_page(
        cards=cards,
        page=page,
        search_text=search_text,
    )

    await message.reply_text(
        text,
        reply_markup=markup,
        parse_mode="HTML",
    )


# ============================================================
# SEND CARD MEDIA
# ============================================================

async def send_card_media(
    query,
    context,
    card,
    text,
    keyboard,
):
    """
    Send/edit card media.

    If card has Telegram file_id:
        photo -> send_photo
        video -> send_video

    Otherwise:
        edit current message text.
    """

    media_type = safe_text(
        card["media_type"],
        "photo",
    ).lower()

    image_file_id = safe_text(
        card["image_file_id"]
    ).strip()

    video_file_id = safe_text(
        card["video_file_id"]
    ).strip()

    markup = InlineKeyboardMarkup(
        keyboard
    )

    # --------------------------------------------------------
    # PHOTO
    # --------------------------------------------------------

    if image_file_id:

        try:

            await query.message.delete()

        except Exception:
            pass

        try:

            await context.bot.send_photo(
                chat_id=query.message.chat_id,
                photo=image_file_id,
                caption=text,
                reply_markup=markup,
                parse_mode="HTML",
            )

            return True

        except Exception:
            pass

    # --------------------------------------------------------
    # VIDEO
    # --------------------------------------------------------

    if video_file_id:

        try:

            await query.message.delete()

        except Exception:
            pass

        try:

            await context.bot.send_video(
                chat_id=query.message.chat_id,
                video=video_file_id,
                caption=text,
                reply_markup=markup,
                parse_mode="HTML",
            )

            return True

        except Exception:
            pass

    # --------------------------------------------------------
    # FALLBACK TEXT
    # --------------------------------------------------------

    try:

        await query.edit_message_text(
            text,
            reply_markup=markup,
            parse_mode="HTML",
        )

        return True

    except Exception:

        return False


# ============================================================
# CARD TOP TEXT
# ============================================================

async def build_card_ranking_text(
    context,
    char_id,
    group_id=None,
):
    """
    Build Global Top 15 + Group Top 15.
    """

    global_rows = get_global_card_owners(
        char_id,
        TOP_LIMIT,
    )

    group_rows = []

    if group_id:

        group_rows = get_group_card_owners(
            char_id,
            group_id,
            TOP_LIMIT,
        )

    text = ""

    # ========================================================
    # GLOBAL
    # ========================================================

    text += (
        "\n\n🌍 <b>GLOBAL TOP 15 OWNERS</b>\n"
        "━━━━━━━━━━━━━━━━━━\n"
    )

    if not global_rows:

        text += (
            "📭 ဒီ Card ကို ပိုင်ဆိုင်သူ မရှိသေးပါ။\n"
        )

    else:

        for index, row in enumerate(
            global_rows,
            start=1,
        ):

            user_id = row[0]
            quantity = safe_int(
                row[1]
            )

            display_name = (
                await get_user_display_name(
                    context,
                    user_id,
                )
            )

            display_name = escape(
                display_name
            )

            if index == 1:
                medal = "🥇"

            elif index == 2:
                medal = "🥈"

            elif index == 3:
                medal = "🥉"

            else:
                medal = f"<b>{index}.</b>"

            text += (
                f"{medal} {display_name}"
                f" — <b>{quantity}x</b>\n"
            )

    # ========================================================
    # GROUP
    # ========================================================

    text += (
        "\n👥 <b>GROUP TOP 15 OWNERS</b>\n"
        "━━━━━━━━━━━━━━━━━━\n"
    )

    if not group_id:

        text += (
            "ℹ️ Group ထဲမှာကြည့်ရင် "
            "Group Ranking ပေါ်ပါမယ်။\n"
        )

    elif not group_rows:

        text += (
            "📭 ဒီ Group ထဲမှာ "
            "ဒီ Card ပိုင်ဆိုင်သူ မရှိသေးပါ။\n"
        )

    else:

        for index, row in enumerate(
            group_rows,
            start=1,
        ):

            user_id = row[0]
            quantity = safe_int(
                row[1]
            )

            display_name = (
                await get_user_display_name(
                    context,
                    user_id,
                )
            )

            display_name = escape(
                display_name
            )

            if index == 1:
                medal = "🥇"

            elif index == 2:
                medal = "🥈"

            elif index == 3:
                medal = "🥉"

            else:
                medal = f"<b>{index}.</b>"

            text += (
                f"{medal} {display_name}"
                f" — <b>{quantity}x</b>\n"
            )

    return text


# ============================================================
# CALLBACK
# ============================================================

async def search_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    query = update.callback_query

    if not query:
        return

    data = query.data or ""

    # ========================================================
    # NO OP
    # ========================================================

    if data == "search_noop":

        await query.answer()

        return

    # ========================================================
    # OPEN CARD LIST
    # ========================================================

    if data.startswith(
        "search_open:"
    ):

        await query.answer()

        cards = search_cards()

        if not cards:

            await query.answer(
                "❌ Card မရှိသေးပါ။",
                show_alert=True,
            )

            return

        text, markup = build_search_page(
            cards=cards,
            page=1,
            search_text=None,
        )

        try:

            await query.edit_message_text(
                text,
                reply_markup=markup,
                parse_mode="HTML",
            )

        except Exception:
            pass

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

        card = get_card_full(
            char_id
        )

        if not card:

            await query.answer(
                "❌ Card မတွေ့ပါ။",
                show_alert=True,
            )

            return

        # ----------------------------------------------------
        # Card detail
        # ----------------------------------------------------

        text = format_card_detail(
            card
        )

        # ----------------------------------------------------
        # Ranking
        # ----------------------------------------------------

        group_id = None

        if query.message:

            chat = query.message.chat

            if chat.type in (
                "group",
                "supergroup",
            ):

                group_id = chat.id

        ranking_text = (
            await build_card_ranking_text(
                context=context,
                char_id=char_id,
                group_id=group_id,
            )
        )

        text += ranking_text

        # ----------------------------------------------------
        # Back
        # ----------------------------------------------------

        keyboard = [
            [
                InlineKeyboardButton(
                    "⬅️ Card List",
                    callback_data="search_back_list",
                )
            ],
            [
                InlineKeyboardButton(
                    "🔎 Search",
                    callback_data="search_back",
                )
            ],
        ]

        await query.answer()

        await send_card_media(
            query=query,
            context=context,
            card=card,
            text=text,
            keyboard=keyboard,
        )

        return

    # ========================================================
    # BACK TO CARD LIST
    # ========================================================

    if data == "search_back_list":

        await query.answer()

        cards = search_cards()

        if not cards:

            try:

                await query.edit_message_text(
                    "📭 Card မရှိသေးပါ။",
                    parse_mode="HTML",
                )

            except Exception:
                pass

            return

        text, markup = build_search_page(
            cards=cards,
            page=1,
            search_text=None,
        )

        # ----------------------------------------------------
        # If previous message was media, edit won't work.
        # Send a fresh page instead.
        # ----------------------------------------------------

        try:

            await query.message.delete()

        except Exception:
            pass

        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text=text,
            reply_markup=markup,
            parse_mode="HTML",
        )

        return

    # ========================================================
    # SEARCH BACK
    # ========================================================

    if data == "search_back":

        await query.answer()

        try:

            await query.edit_message_text(
                "🔎 <b>NEXUS CARD SEARCH</b>\n"
                "━━━━━━━━━━━━━━━━━━\n\n"
                "Card Name / ID / Edition / "
                "Rarity နဲ့ Search လုပ်နိုင်ပါတယ်။\n\n"
                "📌 Example:\n"
                "<code>/search Naruto</code>\n"
                "<code>/search NXS001</code>\n"
                "<code>/search Premium</code>",
                parse_mode="HTML",
            )

        except Exception:

            try:

                await context.bot.send_message(
                    chat_id=query.message.chat_id,
                    text=(
                        "🔎 <b>NEXUS CARD SEARCH</b>\n\n"
                        "📌 <code>/search CardName</code>"
                    ),
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

            await query.answer(
                "Invalid page.",
                show_alert=True,
            )

            return

        cards = search_cards()

        if not cards:

            await query.answer(
                "❌ Card မရှိတော့ပါ။",
                show_alert=True,
            )

            return

        text, markup = build_search_page(
            cards=cards,
            page=page,
            search_text=None,
        )

        await query.answer()

        try:

            await query.edit_message_text(
                text,
                reply_markup=markup,
                parse_mode="HTML",
            )

        except Exception:
            pass

        return

    # ========================================================
    # UNKNOWN
    # ========================================================

    await query.answer()
