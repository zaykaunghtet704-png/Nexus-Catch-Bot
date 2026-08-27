import math
from datetime import datetime, timezone

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import ContextTypes

from database import get_db


# ============================================================
# CONFIG
# ============================================================

GLOBAL_TOP_LIMIT = 15
RANKING_PER_PAGE = 10
TODAY_TOP_LIMIT = 15


# ============================================================
# HELPERS
# ============================================================

def get_global_rankings():

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

    return rows


def get_group_rankings(
    chat_id,
):

    with get_db() as db:

        rows = db.execute(
            """
            SELECT
                uc.user_id,
                COUNT(*) AS total_cards
            FROM user_cards uc
            INNER JOIN group_members gm
                ON gm.user_id = uc.user_id
            WHERE gm.chat_id = ?
            GROUP BY uc.user_id
            ORDER BY total_cards DESC, uc.user_id ASC
            """,
            (chat_id,),
        ).fetchall()

    return rows


def get_today_rankings():

    today = datetime.now(
        timezone.utc
    ).strftime(
        "%Y-%m-%d"
    )

    with get_db() as db:

        rows = db.execute(
            """
            SELECT
                user_id,
                COUNT(*) AS total_cards
            FROM user_cards
            WHERE DATE(caught_at) = ?
            GROUP BY user_id
            ORDER BY total_cards DESC, user_id ASC
            """,
            (today,),
        ).fetchall()

    return rows


async def get_display_name(
    context,
    user_id,
):

    try:

        user = await context.bot.get_chat(
            user_id
        )

        if getattr(
            user,
            "username",
            None,
        ):

            return (
                f"@{user.username}"
            )

        return (
            user.first_name
            or "Unknown User"
        )

    except Exception:

        return (
            f"User {user_id}"
        )


def medal(index):

    if index == 1:
        return "🥇"

    if index == 2:
        return "🥈"

    if index == 3:
        return "🥉"

    return f"{index}."


# ============================================================
# GLOBAL TOP 15
# ============================================================

async def top_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    message = update.effective_message

    if not message:
        return

    rows = get_global_rankings()

    if not rows:

        await message.reply_text(
            "🏆 <b>GLOBAL TOP</b>\n\n"
            "📭 Ranking data မရှိသေးပါ။",
            parse_mode="HTML",
        )

        return

    rows = rows[
        :GLOBAL_TOP_LIMIT
    ]

    text = (
        "🏆 <b>NEXUS GLOBAL TOP 15</b>\n\n"
        "🎴 Card အများဆုံးပိုင်ဆိုင်ထားသူများ\n\n"
    )

    for index, row in enumerate(
        rows,
        start=1,
    ):

        name = await get_display_name(
            context,
            row["user_id"],
        )

        text += (
            f"{medal(index)} "
            f"<b>{name}</b>\n"
            f"   🎴 {row['total_cards']} Cards\n\n"
        )

    keyboard = [
        [
            InlineKeyboardButton(
                "🌎 Full Rankings",
                callback_data="ranking_global:1",
            )
        ]
    ]

    await message.reply_text(
        text,
        reply_markup=InlineKeyboardMarkup(
            keyboard
        ),
        parse_mode="HTML",
    )


# ============================================================
# RANKINGS
# ============================================================

async def rankings_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    message = update.effective_message

    if not message:
        return

    rows = get_global_rankings()

    if not rows:

        await message.reply_text(
            "🌎 <b>GLOBAL RANKINGS</b>\n\n"
            "📭 Ranking data မရှိသေးပါ။",
            parse_mode="HTML",
        )

        return

    await send_global_page(
        message,
        context,
        rows,
        1,
    )


async def send_global_page(
    message,
    context,
    rows,
    page,
):

    total_pages = max(
        1,
        math.ceil(
            len(rows)
            / RANKING_PER_PAGE
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
        * RANKING_PER_PAGE
    )

    end = (
        start
        + RANKING_PER_PAGE
    )

    page_rows = rows[
        start:end
    ]

    text = (
        "🌎 <b>NEXUS GLOBAL RANKINGS</b>\n\n"
        f"👥 Total Ranked Users: <b>{len(rows)}</b>\n"
        f"📄 Page: <b>{page}/{total_pages}</b>\n\n"
    )

    for index, row in enumerate(
        page_rows,
        start=start + 1,
    ):

        name = await get_display_name(
            context,
            row["user_id"],
        )

        text += (
            f"{medal(index)} "
            f"<b>{name}</b>\n"
            f"   🎴 {row['total_cards']} Cards\n"
            f"   🆔 <code>{row['user_id']}</code>\n\n"
        )

    buttons = []

    navigation = []

    if page > 1:

        navigation.append(
            InlineKeyboardButton(
                "⬅️",
                callback_data=(
                    f"ranking_global:{page - 1}"
                ),
            )
        )

    navigation.append(
        InlineKeyboardButton(
            f"📄 {page}/{total_pages}",
            callback_data="ranking_noop",
        )
    )

    if page < total_pages:

        navigation.append(
            InlineKeyboardButton(
                "➡️",
                callback_data=(
                    f"ranking_global:{page + 1}"
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
# GROUP TOP
# ============================================================

async def ctop_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    message = update.effective_message
    chat = update.effective_chat

    if not message or not chat:
        return

    if chat.type not in (
        "group",
        "supergroup",
    ):

        await message.reply_text(
            "👥 <b>/ctop</b> ကို Group ထဲမှာပဲ "
            "အသုံးပြုနိုင်ပါတယ်။",
            parse_mode="HTML",
        )

        return

    rows = get_group_rankings(
        chat.id
    )

    if not rows:

        await message.reply_text(
            "👥 <b>GROUP TOP</b>\n\n"
            "📭 ဒီ Group မှာ Ranking data မရှိသေးပါ။",
            parse_mode="HTML",
        )

        return

    rows = rows[
        :GLOBAL_TOP_LIMIT
    ]

    text = (
        "👥 <b>NEXUS GROUP TOP</b>\n\n"
        f"💬 Group: <b>{chat.title or 'Group'}</b>\n\n"
    )

    for index, row in enumerate(
        rows,
        start=1,
    ):

        name = await get_display_name(
            context,
            row["user_id"],
        )

        text += (
            f"{medal(index)} "
            f"<b>{name}</b>\n"
            f"   🎴 {row['total_cards']} Cards\n\n"
        )

    await message.reply_text(
        text,
        parse_mode="HTML",
    )


# ============================================================
# TODAY NEXUS CATCH
# ============================================================

async def today_nexus_catch_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    message = update.effective_message

    if not message:
        return

    rows = get_today_rankings()

    if not rows:

        await message.reply_text(
            "⚡ <b>TODAY NEXUS CATCH</b>\n\n"
            "📭 ဒီနေ့ Card ကောက်ထားသူ မရှိသေးပါ။",
            parse_mode="HTML",
        )

        return

    rows = rows[
        :TODAY_TOP_LIMIT
    ]

    text = (
        "⚡ <b>TODAY NEXUS CATCH</b>\n\n"
        "🎴 ဒီနေ့ Card ကောက်ရရှိမှုအများဆုံးသူများ\n\n"
    )

    for index, row in enumerate(
        rows,
        start=1,
    ):

        name = await get_display_name(
            context,
            row["user_id"],
        )

        text += (
            f"{medal(index)} "
            f"<b>{name}</b>\n"
            f"   🎴 Today: <b>{row['total_cards']}</b> Cards\n\n"
        )

    await message.reply_text(
        text,
        parse_mode="HTML",
    )


# ============================================================
# CALLBACK
# ============================================================

async def ranking_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    query = update.callback_query

    data = query.data or ""

    # --------------------------------------------------------
    # NO OP
    # --------------------------------------------------------

    if data == "ranking_noop":

        await query.answer()

        return

    # --------------------------------------------------------
    # GLOBAL PAGE
    # --------------------------------------------------------

    if data.startswith(
        "ranking_global:"
    ):

        try:

            page = int(
                data.split(
                    ":",
                    1,
                )[1]
            )

        except ValueError:

            await query.answer(
                "Invalid page.",
                show_alert=True,
            )

            return

        rows = get_global_rankings()

        if not rows:

            await query.answer(
                "Ranking မရှိပါ။",
                show_alert=True,
            )

            return

        total_pages = max(
            1,
            math.ceil(
                len(rows)
                / RANKING_PER_PAGE
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
            * RANKING_PER_PAGE
        )

        end = (
            start
            + RANKING_PER_PAGE
        )

        page_rows = rows[
            start:end
        ]

        text = (
            "🌎 <b>NEXUS GLOBAL RANKINGS</b>\n\n"
            f"👥 Total Ranked Users: <b>{len(rows)}</b>\n"
            f"📄 Page: <b>{page}/{total_pages}</b>\n\n"
        )

        for index, row in enumerate(
            page_rows,
            start=start + 1,
        ):

            name = await get_display_name(
                context,
                row["user_id"],
            )

            text += (
                f"{medal(index)} "
                f"<b>{name}</b>\n"
                f"   🎴 {row['total_cards']} Cards\n"
                f"   🆔 <code>{row['user_id']}</code>\n\n"
            )

        navigation = []

        if page > 1:

            navigation.append(
                InlineKeyboardButton(
                    "⬅️",
                    callback_data=(
                        f"ranking_global:{page - 1}"
                    ),
                )
            )

        navigation.append(
            InlineKeyboardButton(
                f"📄 {page}/{total_pages}",
                callback_data="ranking_noop",
            )
        )

        if page < total_pages:

            navigation.append(
                InlineKeyboardButton(
                    "➡️",
                    callback_data=(
                        f"ranking_global:{page + 1}"
                    ),
                )
            )

        await query.answer()

        try:

            await query.edit_message_text(
                text,
                reply_markup=InlineKeyboardMarkup(
                    [navigation]
                ),
                parse_mode="HTML",
            )

        except Exception:
            pass

        return

    await query.answer()
