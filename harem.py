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
    get_user_cards,
)


# ============================================================
# CONFIG
# ============================================================

HAREM_PER_PAGE = 8
HMODE_COUNT = 10


# ============================================================
# HMODE DATABASE
# ============================================================

def init_hmode_db():

    with get_db() as db:

        db.execute(
            """
            CREATE TABLE IF NOT EXISTS harem_modes (
                user_id INTEGER PRIMARY KEY,
                mode TEXT NOT NULL DEFAULT 'all'
            )
            """
        )


init_hmode_db()


# ============================================================
# GET MODE
# ============================================================

def get_hmode(user_id):

    with get_db() as db:

        row = db.execute(
            """
            SELECT mode
            FROM harem_modes
            WHERE user_id = ?
            """,
            (user_id,),
        ).fetchone()

    if not row:
        return "all"

    return row["mode"]


def set_hmode(
    user_id,
    char_id,
):

    with get_db() as db:

        db.execute(
            """
            INSERT INTO harem_modes (
                user_id,
                mode
            )
            VALUES (?, ?)

            ON CONFLICT(user_id)
            DO UPDATE SET mode = excluded.mode
            """,
            (
                user_id,
                str(char_id),
            ),
        )


def reset_hmode(user_id):

    with get_db() as db:

        db.execute(
            """
            DELETE FROM harem_modes
            WHERE user_id = ?
            """,
            (user_id,),
        )


# ============================================================
# SORT CARDS
# ============================================================

def sort_cards(cards):

    return sorted(
        cards,
        key=lambda c: (
            str(c["char_id"])
        ),
    )


# ============================================================
# APPLY HMODE
# ============================================================

def apply_hmode(
    user_id,
    cards,
):

    mode = get_hmode(
        user_id
    )

    if mode == "all":
        return cards

    filtered = []

    for card in cards:

        if str(card["char_id"]) == str(mode):

            filtered.append(card)

    return filtered


# ============================================================
# HAREM COMMAND
# ============================================================

async def harem_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    message = update.effective_message
    user = update.effective_user

    if not message or not user:
        return

    cards = get_user_cards(
        user.id
    )

    if not cards:

        await message.reply_text(
            "🎴 <b>YOUR HAREM</b>\n\n"
            "မင်းမှာ Card မရှိသေးပါ။\n\n"
            "🎁 /drop ကို စောင့်ပြီး Card ကောက်ပါ။",
            parse_mode="HTML",
        )

        return

    cards = sort_cards(cards)

    cards = apply_hmode(
        user.id,
        cards,
    )

    if not cards:

        await message.reply_text(
            "🎴 Harem Mode မှာ ပြသမယ့် Card မရှိပါ။\n\n"
            "🔄 <code>/reset</code> နဲ့ Harem Mode "
            "ပြန်ရှင်းနိုင်ပါတယ်။",
            parse_mode="HTML",
        )

        return

    page = 1

    if context.args:

        try:
            page = int(
                context.args[0]
            )
        except ValueError:
            page = 1

    total_pages = max(
        1,
        math.ceil(
            len(cards)
            / HAREM_PER_PAGE
        ),
    )

    page = max(
        1,
        min(page, total_pages),
    )

    await send_harem_page(
        message,
        user.id,
        cards,
        page,
    )


# ============================================================
# SEND HAREM PAGE
# ============================================================

async def send_harem_page(
    message,
    user_id,
    cards,
    page,
):

    total_pages = max(
        1,
        math.ceil(
            len(cards)
            / HAREM_PER_PAGE
        ),
    )

    start = (
        (page - 1)
        * HAREM_PER_PAGE
    )

    end = (
        start
        + HAREM_PER_PAGE
    )

    page_cards = cards[
        start:end
    ]

    text = (
        "🎴 <b>NEXUS HAREM</b>\n\n"
        f"👤 User ID: <code>{user_id}</code>\n"
        f"📦 Cards: <b>{len(cards)}</b>\n"
        f"📄 Page: <b>{page}/{total_pages}</b>\n\n"
    )

    for index, owned in enumerate(
        page_cards,
        start=start + 1,
    ):

        card = get_card(
            owned["char_id"]
        )

        if not card:
            continue

        favorite = (
            " ❤️"
            if owned["favorite"]
            else ""
        )

        level = owned["level"]

        exp = owned["exp"]

        text += (
            f"<b>{index}.</b> "
            f"🎴 {card['name']}{favorite}\n"
            f"   🆔 <code>{card['char_id']}</code> "
            f"• ✨ {card['edition']}\n"
            f"   ⭐ {card['rarity']} "
            f"• 🎖 Lv.{level} "
            f"• EXP {exp}\n"
            f"   💰 {card['price']:,} Coins\n\n"
        )

    buttons = []

    navigation = []

    if page > 1:

        navigation.append(
            InlineKeyboardButton(
                "⬅️",
                callback_data=(
                    f"harem:{user_id}:{page - 1}"
                ),
            )
        )

    navigation.append(
        InlineKeyboardButton(
            f"📄 {page}/{total_pages}",
            callback_data="harem_noop",
        )
    )

    if page < total_pages:

        navigation.append(
            InlineKeyboardButton(
                "➡️",
                callback_data=(
                    f"harem:{user_id}:{page + 1}"
                ),
            )
        )

    buttons.append(
        navigation
    )

    buttons.append([
        InlineKeyboardButton(
            "🎛 HMODE",
            callback_data=f"hmode:{user_id}",
        ),
        InlineKeyboardButton(
            "🔄 Reset",
            callback_data=f"hreset:{user_id}",
        ),
    ])

    await message.reply_text(
        text,
        reply_markup=InlineKeyboardMarkup(
            buttons
        ),
        parse_mode="HTML",
    )


# ============================================================
# HAREM CALLBACK
# ============================================================

async def harem_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    query = update.callback_query
    user = query.from_user

    data = query.data or ""

    # --------------------------------------------------------
    # NO OP
    # --------------------------------------------------------

    if data == "harem_noop":

        await query.answer()

        return

    # --------------------------------------------------------
    # PAGE
    # --------------------------------------------------------

    if data.startswith("harem:"):

        parts = data.split(":")

        if len(parts) != 3:

            await query.answer(
                "Invalid page.",
                show_alert=True,
            )

            return

        try:

            owner_id = int(
                parts[1]
            )

            page = int(
                parts[2]
            )

        except ValueError:

            await query.answer(
                "Invalid page.",
                show_alert=True,
            )

            return

        # Only owner can control own harem
        if owner_id != user.id:

            await query.answer(
                "🚫 ဒီ Harem ကို မင်းကြည့်လို့မရပါ။",
                show_alert=True,
            )

            return

        cards = get_user_cards(
            user.id
        )

        cards = sort_cards(
            cards
        )

        cards = apply_hmode(
            user.id,
            cards,
        )

        if not cards:

            await query.answer(
                "Card မရှိတော့ပါ။",
                show_alert=True,
            )

            return

        total_pages = max(
            1,
            math.ceil(
                len(cards)
                / HAREM_PER_PAGE
            ),
        )

        page = max(
            1,
            min(page, total_pages),
        )

        start = (
            (page - 1)
            * HAREM_PER_PAGE
        )

        end = (
            start
            + HAREM_PER_PAGE
        )

        page_cards = cards[
            start:end
        ]

        text = (
            "🎴 <b>NEXUS HAREM</b>\n\n"
            f"👤 User ID: <code>{user.id}</code>\n"
            f"📦 Cards: <b>{len(cards)}</b>\n"
            f"📄 Page: <b>{page}/{total_pages}</b>\n\n"
        )

        for index, owned in enumerate(
            page_cards,
            start=start + 1,
        ):

            card = get_card(
                owned["char_id"]
            )

            if not card:
                continue

            favorite = (
                " ❤️"
                if owned["favorite"]
                else ""
            )

            text += (
                f"<b>{index}.</b> "
                f"🎴 {card['name']}{favorite}\n"
                f"   🆔 <code>{card['char_id']}</code>\n"
                f"   ✨ {card['edition']} "
                f"• ⭐ {card['rarity']}\n"
                f"   🎖 Lv.{owned['level']} "
                f"• EXP {owned['exp']}\n"
                f"   💰 {card['price']:,} Coins\n\n"
            )

        buttons = []

        navigation = []

        if page > 1:

            navigation.append(
                InlineKeyboardButton(
                    "⬅️",
                    callback_data=(
                        f"harem:{user.id}:{page - 1}"
                    ),
                )
            )

        navigation.append(
            InlineKeyboardButton(
                f"📄 {page}/{total_pages}",
                callback_data="harem_noop",
            )
        )

        if page < total_pages:

            navigation.append(
                InlineKeyboardButton(
                    "➡️",
                    callback_data=(
                        f"harem:{user.id}:{page + 1}"
                    ),
                )
            )

        buttons.append(
            navigation
        )

        buttons.append([
            InlineKeyboardButton(
                "🎛 HMODE",
                callback_data=f"hmode:{user.id}",
            ),
            InlineKeyboardButton(
                "🔄 Reset",
                callback_data=f"hreset:{user.id}",
            ),
        ])

        await query.answer()

        try:

            await query.edit_message_text(
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
    # HMODE
    # --------------------------------------------------------

    if data.startswith("hmode:"):

        try:

            owner_id = int(
                data.split(":", 1)[1]
            )

        except ValueError:

            await query.answer(
                "Invalid user.",
                show_alert=True,
            )

            return

        if owner_id != user.id:

            await query.answer(
                "🚫 ဒီ Harem ကို မင်းပြင်လို့မရပါ။",
                show_alert=True,
            )

            return

        cards = sort_cards(
            get_user_cards(
                user.id
            )
        )

        if not cards:

            await query.answer(
                "🎴 Card မရှိသေးပါ။",
                show_alert=True,
            )

            return

        # Show first 10 cards
        preview = cards[
            :HMODE_COUNT
        ]

        text = (
            "🎛 <b>HAREM MODE</b>\n\n"
            "Harem မှာ အမြဲပြချင်တဲ့ Card ကို "
            "ရွေးပါ။\n\n"
            f"🎴 ပထမဆုံး {len(preview)} ခုကို ပြထားပါတယ်။\n"
            "👇 Card တစ်ခုကို နှိပ်ပြီး Select လုပ်ပါ။"
        )

        buttons = []

        for card in preview:

            buttons.append([
                InlineKeyboardButton(
                    f"🎴 {card['name']} "
                    f"[{card['char_id']}]",
                    callback_data=(
                        f"hselect:{user.id}:"
                        f"{card['char_id']}"
                    ),
                )
            ])

        buttons.append([
            InlineKeyboardButton(
                "⬅️ Back",
                callback_data=(
                    f"hmode_back:{user.id}"
                ),
            )
        ])

        await query.answer()

        try:

            await query.edit_message_text(
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
    # SELECT CARD
    # --------------------------------------------------------

    if data.startswith("hselect:"):

        parts = data.split(":")

        if len(parts) != 3:

            await query.answer(
                "Invalid card.",
                show_alert=True,
            )

            return

        try:

            owner_id = int(
                parts[1]
            )

        except ValueError:

            await query.answer(
                "Invalid user.",
                show_alert=True,
            )

            return

        char_id = parts[2]

        if owner_id != user.id:

            await query.answer(
                "🚫 ဒီ Card ကို ရွေးခွင့်မရှိပါ။",
                show_alert=True,
            )

            return

        if not get_card(char_id):

            await query.answer(
                "❌ Card မတွေ့ပါ။",
                show_alert=True,
            )

            return

        owned = get_user_cards(
            user.id
        )

        if not any(
            str(c["char_id"])
            == str(char_id)
            for c in owned
        ):

            await query.answer(
                "❌ ဒီ Card ကို မင်းမပိုင်ပါ။",
                show_alert=True,
            )

            return

        set_hmode(
            user.id,
            char_id,
        )

        card = get_card(
            char_id
        )

        await query.answer(
            f"🎴 {card['name']} ကို "
            "Harem Mode ရွေးပြီးပါပြီ!",
            show_alert=True,
        )

        text = (
            "✅ <b>HAREM MODE UPDATED!</b>\n\n"
            f"🎴 <b>{card['name']}</b>\n"
            f"🆔 <code>{card['char_id']}</code>\n"
            f"✨ {card['edition']}\n"
            f"⭐ {card['rarity']}\n\n"
            "ဒီ Card ကို Harem Mode မှာ "
            "ရွေးထားပါပြီ။\n\n"
            "🎴 /harem → ရွေးထားတဲ့ Card ကိုကြည့်ပါ။\n"
            "🔄 /reset → Mode ပြန်ရှင်းပါ။"
        )

        buttons = [
            [
                InlineKeyboardButton(
                    "🎴 View Harem",
                    callback_data=(
                        f"hmode_back:{user.id}"
                    ),
                )
            ]
        ]

        try:

            await query.edit_message_text(
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
    # HMODE BACK
    # --------------------------------------------------------

    if data.startswith(
        "hmode_back:"
    ):

        try:

            owner_id = int(
                data.split(":", 1)[1]
            )

        except ValueError:

            await query.answer(
                "Invalid user.",
                show_alert=True,
            )

            return

        if owner_id != user.id:

            await query.answer(
                "🚫 Not your harem.",
                show_alert=True,
            )

            return

        cards = sort_cards(
            get_user_cards(
                user.id
            )
        )

        cards = apply_hmode(
            user.id,
            cards,
        )

        if not cards:

            await query.answer(
                "Card မရှိပါ။",
                show_alert=True,
            )

            return

        await query.answer()

        await rebuild_harem_message(
            query,
            user.id,
            cards,
            1,
        )

        return

    # --------------------------------------------------------
    # RESET
    # --------------------------------------------------------

    if data.startswith(
        "hreset:"
    ):

        try:

            owner_id = int(
                data.split(":", 1)[1]
            )

        except ValueError:

            await query.answer(
                "Invalid user.",
                show_alert=True,
            )

            return

        if owner_id != user.id:

            await query.answer(
                "🚫 Not your harem.",
                show_alert=True,
            )

            return

        reset_hmode(
            user.id
        )

        await query.answer(
            "🔄 Harem Mode Reset!",
            show_alert=True,
        )

        cards = sort_cards(
            get_user_cards(
                user.id
            )
        )

        await rebuild_harem_message(
            query,
            user.id,
            cards,
            1,
        )

        return

    await query.answer()


# ============================================================
# REBUILD HAREM MESSAGE
# ============================================================

async def rebuild_harem_message(
    query,
    user_id,
    cards,
    page,
):

    total_pages = max(
        1,
        math.ceil(
            len(cards)
            / HAREM_PER_PAGE
        ),
    )

    page = max(
        1,
        min(page, total_pages),
    )

    start = (
        (page - 1)
        * HAREM_PER_PAGE
    )

    end = (
        start
        + HAREM_PER_PAGE
    )

    page_cards = cards[
        start:end
    ]

    text = (
        "🎴 <b>NEXUS HAREM</b>\n\n"
        f"👤 User ID: <code>{user_id}</code>\n"
        f"📦 Cards: <b>{len(cards)}</b>\n"
        f"📄 Page: <b>{page}/{total_pages}</b>\n\n"
    )

    for index, owned in enumerate(
        page_cards,
        start=start + 1,
    ):

        card = get_card(
            owned["char_id"]
        )

        if not card:
            continue

        favorite = (
            " ❤️"
            if owned["favorite"]
            else ""
        )

        text += (
            f"<b>{index}.</b> "
            f"🎴 {card['name']}{favorite}\n"
            f"   🆔 <code>{card['char_id']}</code>\n"
            f"   ✨ {card['edition']} "
            f"• ⭐ {card['rarity']}\n"
            f"   🎖 Lv.{owned['level']} "
            f"• EXP {owned['exp']}\n"
            f"   💰 {card['price']:,} Coins\n\n"
        )

    buttons = []

    navigation = []

    if page > 1:

        navigation.append(
            InlineKeyboardButton(
                "⬅️",
                callback_data=(
                    f"harem:{user_id}:{page - 1}"
                ),
            )
        )

    navigation.append(
        InlineKeyboardButton(
            f"📄 {page}/{total_pages}",
            callback_data="harem_noop",
        )
    )

    if page < total_pages:

        navigation.append(
            InlineKeyboardButton(
                "➡️",
                callback_data=(
                    f"harem:{user_id}:{page + 1}"
                ),
            )
        )

    buttons.append(
        navigation
    )

    buttons.append([
        InlineKeyboardButton(
            "🎛 HMODE",
            callback_data=f"hmode:{user_id}",
        ),
        InlineKeyboardButton(
            "🔄 Reset",
            callback_data=f"hreset:{user_id}",
        ),
    ])

    try:

        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(
                buttons
            ),
            parse_mode="HTML",
        )

    except Exception:
        pass
