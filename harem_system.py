import math

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import ContextTypes

from database import (
    get_card,
    get_user_cards,
)


# ============================================================
# CONFIG
# ============================================================

HAREM_PER_PAGE = 6

DEFAULT_HMODE_LIMIT = 10

# Edition priority
EDITION_ORDER = {
    "premium": 1,
    "legendary": 2,
    "mythic": 3,
    "epic": 4,
    "rare": 5,
    "uncommon": 6,
    "common": 7,
}


# ============================================================
# USER HMODE MEMORY
#
# Temporary in-memory setting.
# Later database.py မှာ persistent storage ထည့်နိုင်မယ်။
# ============================================================

USER_HMODE = {}


# ============================================================
# CARD SORT
# ============================================================

def sort_cards(cards):

    def sort_key(card):

        edition = str(
            card["edition"] or ""
        ).lower()

        try:
            char_id = int(
                str(card["char_id"])
            )
        except (ValueError, TypeError):
            char_id = 999999999

        return (
            EDITION_ORDER.get(
                edition,
                99,
            ),
            char_id,
        )

    return sorted(
        cards,
        key=sort_key,
    )


# ============================================================
# GET HMODE
# ============================================================

def get_hmode(user_id):

    return USER_HMODE.get(
        user_id,
        DEFAULT_HMODE_LIMIT,
    )


def set_hmode(
    user_id,
    limit,
):

    USER_HMODE[user_id] = limit


# ============================================================
# CARD TEXT
# ============================================================

def format_card(
    card,
    number,
):

    return (
        f"<b>{number}.</b> "
        f"🎴 <b>{card['name']}</b>\n"
        f"   🆔 <code>{card['char_id']}</code>\n"
        f"   ✨ Edition: <b>{card['edition']}</b>\n"
        f"   ⭐ Rarity: <b>{card['rarity']}</b>\n"
        f"   💰 Price: <b>{int(card['price'] or 0):,}</b>\n"
    )


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

    target_user_id = user.id

    # --------------------------------------------------------
    # Reply user → view their Harem
    # --------------------------------------------------------

    if message.reply_to_message:

        replied_user = (
            message.reply_to_message.from_user
        )

        if replied_user:
            target_user_id = replied_user.id

    cards = get_user_cards(
        target_user_id
    )

    cards = sort_cards(
        cards
    )

    if not cards:

        await message.reply_text(
            "🎴 <b>NEXUS HAREM</b>\n\n"
            "📭 ဒီ User မှာ Card မရှိသေးပါ။\n\n"
            "✨ Card ရလာတဲ့အခါ "
            "<code>/harem</code> နဲ့ ပြန်ကြည့်နိုင်ပါတယ်။",
            parse_mode="HTML",
        )

        return

    # HMODE
    hmode_limit = get_hmode(
        target_user_id
    )

    # Only selected number of cards
    visible_cards = cards[
        :hmode_limit
    ]

    await send_harem_page(
        message,
        target_user_id,
        visible_cards,
        1,
        total_cards=len(cards),
    )


# ============================================================
# SEND HAREM PAGE
# ============================================================

async def send_harem_page(
    message,
    user_id,
    cards,
    page,
    total_cards=None,
):

    if not cards:

        await message.reply_text(
            "📭 Harem empty.",
            parse_mode="HTML",
        )

        return

    if total_cards is None:
        total_cards = len(cards)

    total_pages = max(
        1,
        math.ceil(
            len(cards)
            / HAREM_PER_PAGE
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
        f"📦 Collection: <b>{total_cards}</b> Cards\n"
        f"🎛 HMode: <b>{len(cards)}</b> Cards\n"
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
    # CARD BUTTONS
    # --------------------------------------------------------

    for card in page_cards:

        keyboard.append([
            InlineKeyboardButton(
                f"🎴 {card['name']}",
                callback_data=(
                    f"harem_card:"
                    f"{user_id}:"
                    f"{card['char_id']}"
                ),
            )
        ])

    # --------------------------------------------------------
    # PAGINATION
    # --------------------------------------------------------

    navigation = []

    if page > 1:

        navigation.append(
            InlineKeyboardButton(
                "⬅️",
                callback_data=(
                    f"harem_page:"
                    f"{user_id}:"
                    f"{page - 1}"
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
                    f"harem_page:"
                    f"{user_id}:"
                    f"{page + 1}"
                ),
            )
        )

    keyboard.append(
        navigation
    )

    # --------------------------------------------------------
    # HMODE / RESET
    # --------------------------------------------------------

    keyboard.append([
        InlineKeyboardButton(
            "🎛 HMode",
            callback_data=(
                f"harem_hmode:"
                f"{user_id}"
            ),
        ),
        InlineKeyboardButton(
            "🔄 Reset",
            callback_data=(
                f"harem_reset:"
                f"{user_id}"
            ),
        ),
    ])

    try:

        await message.reply_text(
            text,
            reply_markup=InlineKeyboardMarkup(
                keyboard
            ),
            parse_mode="HTML",
        )

    except Exception:

        pass


# ============================================================
# HMODE COMMAND
# ============================================================

async def hmode_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    message = update.effective_message
    user = update.effective_user

    if not message or not user:
        return

    current = get_hmode(
        user.id
    )

    await message.reply_text(
        "🎛 <b>NEXUS HMODE</b>\n\n"
        f"📌 လက်ရှိ Mode: <b>{current}</b> Cards\n\n"
        "Harem မှာ အရင်ဆုံးပြချင်တဲ့ "
        "Card အရေအတွက်ကို ရွေးပါ။",
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "5️⃣ 5 Cards",
                    callback_data=f"hmode_set:{user.id}:5",
                ),
                InlineKeyboardButton(
                    "🔟 10 Cards",
                    callback_data=f"hmode_set:{user.id}:10",
                ),
            ],
            [
                InlineKeyboardButton(
                    "1️⃣5️⃣ 15 Cards",
                    callback_data=f"hmode_set:{user.id}:15",
                ),
                InlineKeyboardButton(
                    "2️⃣0️⃣ 20 Cards",
                    callback_data=f"hmode_set:{user.id}:20",
                ),
            ],
            [
                InlineKeyboardButton(
                    "♾️ All Cards",
                    callback_data=f"hmode_set:{user.id}:999999",
                ),
            ],
        ]),
        parse_mode="HTML",
    )


# ============================================================
# RESET COMMAND
# ============================================================

async def reset_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    message = update.effective_message
    user = update.effective_user

    if not message or not user:
        return

    USER_HMODE.pop(
        user.id,
        None,
    )

    await message.reply_text(
        "🔄 <b>HAREM RESET</b>\n\n"
        "✅ Harem filter ပြန်ရှင်းပြီးပါပြီ။\n"
        "🎴 Card အားလုံးကို ပြန်ကြည့်နိုင်ပါပြီ။\n\n"
        "📌 <code>/harem</code> ကို ပြန်သုံးပါ။",
        parse_mode="HTML",
    )


# ============================================================
# CALLBACK
# ============================================================

async def harem_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    query = update.callback_query
    data = query.data or ""

    # ========================================================
    # NO OP
    # ========================================================

    if data == "harem_noop":

        await query.answer()

        return

    # ========================================================
    # HAREM PAGE
    # ========================================================

    if data.startswith(
        "harem_page:"
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

            owner_id = int(
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

        # ----------------------------------------------------
        # Security:
        # Only owner can navigate his own Harem buttons
        # ----------------------------------------------------

        if query.from_user.id != owner_id:

            await query.answer(
                "🚫 ဒီ Harem ကို မင်းမပိုင်ပါ။",
                show_alert=True,
            )

            return

        cards = get_user_cards(
            owner_id
        )

        cards = sort_cards(
            cards
        )

        hmode_limit = get_hmode(
            owner_id
        )

        cards = cards[
            :hmode_limit
        ]

        if not cards:

            await query.answer(
                "📭 Harem empty.",
                show_alert=True,
            )

            return

        total_cards = len(
            get_user_cards(
                owner_id
            )
        )

        total_pages = max(
            1,
            math.ceil(
                len(cards)
                / HAREM_PER_PAGE
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
            f"📦 Collection: <b>{total_cards}</b> Cards\n"
            f"🎛 HMode: <b>{len(cards)}</b> Cards\n"
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

            keyboard.append([
                InlineKeyboardButton(
                    f"🎴 {card['name']}",
                    callback_data=(
                        f"harem_card:"
                        f"{owner_id}:"
                        f"{card['char_id']}"
                    ),
                )
            ])

        navigation = []

        if page > 1:

            navigation.append(
                InlineKeyboardButton(
                    "⬅️",
                    callback_data=(
                        f"harem_page:"
                        f"{owner_id}:"
                        f"{page - 1}"
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
                        f"harem_page:"
                        f"{owner_id}:"
                        f"{page + 1}"
                    ),
                )
            )

        keyboard.append(
            navigation
        )

        keyboard.append([
            InlineKeyboardButton(
                "🎛 HMode",
                callback_data=(
                    f"harem_hmode:"
                    f"{owner_id}"
                ),
            ),
            InlineKeyboardButton(
                "🔄 Reset",
                callback_data=(
                    f"harem_reset:"
                    f"{owner_id}"
                ),
            ),
        ])

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
    # CARD DETAIL
    # ========================================================

    if data.startswith(
        "harem_card:"
    ):

        parts = data.split(
            ":",
            2,
        )

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
                "Invalid owner.",
                show_alert=True,
            )

            return

        char_id = parts[2]

        if query.from_user.id != owner_id:

            await query.answer(
                "🚫 ဒီ Card Detail ကို "
                "ပိုင်ရှင်ပဲ ကြည့်နိုင်ပါတယ်။",
                show_alert=True,
            )

            return

        card = get_card(
            char_id
        )

        if not card:

            await query.answer(
                "❌ Card မတွေ့ပါ။",
                show_alert=True,
            )

            return

        text = (
            "🎴 <b>CARD DETAIL</b>\n\n"
            f"🎴 Name: <b>{card['name']}</b>\n"
            f"🆔 ID: <code>{card['char_id']}</code>\n\n"
            f"✨ Edition: <b>{card['edition']}</b>\n"
            f"⭐ Rarity: <b>{card['rarity']}</b>\n"
            f"💰 Price: <b>{int(card['price'] or 0):,}</b> Coins\n"
        )

        keyboard = [
            [
                InlineKeyboardButton(
                    "⬅️ Harem",
                    callback_data=(
                        f"harem_page:"
                        f"{owner_id}:1"
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

    # ========================================================
    # HMODE MENU
    # ========================================================

    if data.startswith(
        "harem_hmode:"
    ):

        try:

            owner_id = int(
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

        if query.from_user.id != owner_id:

            await query.answer(
                "🚫 ဒီ HMode ကို မင်းမပြောင်းနိုင်ပါ။",
                show_alert=True,
            )

            return

        current = get_hmode(
            owner_id
        )

        await query.answer()

        try:

            await query.edit_message_text(
                "🎛 <b>NEXUS HMODE</b>\n\n"
                f"📌 Current: <b>{current}</b>\n\n"
                "Harem မှာ ပြချင်တဲ့ Card အရေအတွက် ရွေးပါ။",
                reply_markup=InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton(
                            "5️⃣ 5",
                            callback_data=f"hmode_set:{owner_id}:5",
                        ),
                        InlineKeyboardButton(
                            "🔟 10",
                            callback_data=f"hmode_set:{owner_id}:10",
                        ),
                    ],
                    [
                        InlineKeyboardButton(
                            "1️⃣5️⃣ 15",
                            callback_data=f"hmode_set:{owner_id}:15",
                        ),
                        InlineKeyboardButton(
                            "2️⃣0️⃣ 20",
                            callback_data=f"hmode_set:{owner_id}:20",
                        ),
                    ],
                    [
                        InlineKeyboardButton(
                            "♾️ All",
                            callback_data=f"hmode_set:{owner_id}:999999",
                        ),
                    ],
                ]),
                parse_mode="HTML",
            )

        except Exception:
            pass

        return

    # ========================================================
    # SET HMODE
    # ========================================================

    if data.startswith(
        "hmode_set:"
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

            owner_id = int(
                parts[1]
            )

            limit = int(
                parts[2]
            )

        except ValueError:

            await query.answer(
                "Invalid setting.",
                show_alert=True,
            )

            return

        if query.from_user.id != owner_id:

            await query.answer(
                "🚫 ကိုယ့် HMode ကိုပဲ ပြောင်းနိုင်ပါတယ်။",
                show_alert=True,
            )

            return

        set_hmode(
            owner_id,
            limit,
        )

        await query.answer(
            "✅ HMode updated!",
            show_alert=False,
        )

        # Show first page again
        cards = get_user_cards(
            owner_id
        )

        cards = sort_cards(
            cards
        )

        cards = cards[
            :limit
        ]

        if not cards:

            await query.edit_message_text(
                "📭 Harem empty.",
                parse_mode="HTML",
            )

            return

        total_cards = len(
            get_user_cards(
                owner_id
            )
        )

        total_pages = max(
            1,
            math.ceil(
                len(cards)
                / HAREM_PER_PAGE
            ),
        )

        page_cards = cards[
            :HAREM_PER_PAGE
        ]

        text = (
            "🎴 <b>NEXUS HAREM</b>\n\n"
            f"📦 Collection: <b>{total_cards}</b> Cards\n"
            f"🎛 HMode: <b>{len(cards)}</b> Cards\n"
            f"📄 Page: <b>1/{total_pages}</b>\n\n"
        )

        for index, card in enumerate(
            page_cards,
            start=1,
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

            keyboard.append([
                InlineKeyboardButton(
                    f"🎴 {card['name']}",
                    callback_data=(
                        f"harem_card:"
                        f"{owner_id}:"
                        f"{card['char_id']}"
                    ),
                )
            ])

        navigation = [
            InlineKeyboardButton(
                "📄 1/"
                f"{total_pages}",
                callback_data="harem_noop",
            )
        ]

        if total_pages > 1:

            navigation.append(
                InlineKeyboardButton(
                    "➡️",
                    callback_data=(
                        f"harem_page:"
                        f"{owner_id}:2"
                    ),
                )
            )

        keyboard.append(
            navigation
        )

        keyboard.append([
            InlineKeyboardButton(
                "🎛 HMode",
                callback_data=(
                    f"harem_hmode:"
                    f"{owner_id}"
                ),
            ),
            InlineKeyboardButton(
                "🔄 Reset",
                callback_data=(
                    f"harem_reset:"
                    f"{owner_id}"
                ),
            ),
        ])

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
    # RESET
    # ========================================================

    if data.startswith(
        "harem_reset:"
    ):

        try:

            owner_id = int(
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

        if query.from_user.id != owner_id:

            await query.answer(
                "🚫 ကိုယ့် Harem ကိုပဲ Reset လုပ်နိုင်ပါတယ်။",
                show_alert=True,
            )

            return

        USER_HMODE.pop(
            owner_id,
            None,
        )

        await query.answer(
            "✅ Harem reset!",
        )

        try:

            await query.edit_message_text(
                "🔄 <b>HAREM RESET</b>\n\n"
                "✅ Filter အားလုံး ပြန်ရှင်းပြီးပါပြီ။\n"
                "🎴 Card အားလုံး ပြန်ကြည့်နိုင်ပါပြီ။\n\n"
                "📌 <code>/harem</code> ကို ပြန်ခေါ်ပါ။",
                parse_mode="HTML",
            )

        except Exception:
            pass

        return

    await query.answer()
