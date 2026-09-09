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

# ============================================================
# 13 EDITIONS
# ============================================================

EDITIONS = [
    "Common",
    "Uncommon",
    "Rare",
    "Super Rare",
    "Epic",
    "Ultra",
    "Elite",
    "Master",
    "Grandmaster",
    "Mythic",
    "Legendary",
    "Ultimate",
    "Premium",
]


# ============================================================
# EDITION ORDER
# ============================================================

EDITION_ORDER = {
    "common": 1,
    "uncommon": 2,
    "rare": 3,
    "super rare": 4,
    "epic": 5,
    "ultra": 6,
    "elite": 7,
    "master": 8,
    "grandmaster": 9,
    "mythic": 10,
    "legendary": 11,
    "ultimate": 12,
    "premium": 13,
}


# ============================================================
# USER HMODE
#
# user_id -> selected edition
#
# None = All Editions
# ============================================================

USER_HMODE = {}


# ============================================================
# EDITION EMOJI
# ============================================================

EDITION_EMOJI = {
    "common": "⚪",
    "uncommon": "🟢",
    "rare": "🔵",
    "super rare": "🟣",
    "epic": "🟠",
    "ultra": "🔴",
    "elite": "💠",
    "master": "🔷",
    "grandmaster": "🔶",
    "mythic": "🌌",
    "legendary": "🌟",
    "ultimate": "💫",
    "premium": "💎",
}


# ============================================================
# NORMALIZE EDITION
# ============================================================

def normalize_edition(value):

    if value is None:
        return ""

    return (
        str(value)
        .strip()
        .lower()
        .replace("_", " ")
        .replace("-", " ")
    )


# ============================================================
# GET HMODE
# ============================================================

def get_hmode(user_id):

    return USER_HMODE.get(
        user_id,
        None,
    )


# ============================================================
# SET HMODE
# ============================================================

def set_hmode(
    user_id,
    edition,
):

    if edition is None:

        USER_HMODE.pop(
            user_id,
            None,
        )

        return

    edition_normalized = normalize_edition(
        edition
    )

    for valid_edition in EDITIONS:

        if normalize_edition(
            valid_edition
        ) == edition_normalized:

            USER_HMODE[user_id] = valid_edition

            return


# ============================================================
# FILTER CARDS BY EDITION
# ============================================================

def filter_cards_by_hmode(
    cards,
    user_id,
):

    selected = get_hmode(
        user_id
    )

    # --------------------------------------------------------
    # All Editions
    # --------------------------------------------------------

    if not selected:

        return list(cards)

    selected_normalized = normalize_edition(
        selected
    )

    filtered = []

    for card in cards:

        card_edition = normalize_edition(
            card["edition"]
        )

        if card_edition == selected_normalized:

            filtered.append(card)

    return filtered


# ============================================================
# CARD SORT
# ============================================================

def sort_cards(cards):

    def sort_key(card):

        edition = normalize_edition(
            card["edition"]
        )

        try:

            char_id = int(
                str(card["char_id"])
            )

        except (
            ValueError,
            TypeError,
        ):

            char_id = 999999999

        return (
            EDITION_ORDER.get(
                edition,
                999,
            ),
            char_id,
        )

    return sorted(
        cards,
        key=sort_key,
    )


# ============================================================
# EDITION BUTTON
# ============================================================

def edition_button_text(
    edition,
    selected,
):

    emoji = EDITION_EMOJI.get(
        normalize_edition(edition),
        "🎴",
    )

    if selected and (
        normalize_edition(selected)
        == normalize_edition(edition)
    ):

        return (
            f"✅ {emoji} {edition}"
        )

    return (
        f"{emoji} {edition}"
    )


# ============================================================
# HMODE KEYBOARD
# ============================================================

def build_hmode_keyboard(
    user_id,
):

    selected = get_hmode(
        user_id
    )

    keyboard = []

    # --------------------------------------------------------
    # 13 EDITIONS
    # --------------------------------------------------------

    # Row 1
    keyboard.append([
        InlineKeyboardButton(
            edition_button_text(
                "Common",
                selected,
            ),
            callback_data=f"hmode_set:{user_id}:Common",
        ),
        InlineKeyboardButton(
            edition_button_text(
                "Uncommon",
                selected,
            ),
            callback_data=f"hmode_set:{user_id}:Uncommon",
        ),
    ])

    # Row 2
    keyboard.append([
        InlineKeyboardButton(
            edition_button_text(
                "Rare",
                selected,
            ),
            callback_data=f"hmode_set:{user_id}:Rare",
        ),
        InlineKeyboardButton(
            edition_button_text(
                "Super Rare",
                selected,
            ),
            callback_data=f"hmode_set:{user_id}:Super Rare",
        ),
    ])

    # Row 3
    keyboard.append([
        InlineKeyboardButton(
            edition_button_text(
                "Epic",
                selected,
            ),
            callback_data=f"hmode_set:{user_id}:Epic",
        ),
        InlineKeyboardButton(
            edition_button_text(
                "Ultra",
                selected,
            ),
            callback_data=f"hmode_set:{user_id}:Ultra",
        ),
    ])

    # Row 4
    keyboard.append([
        InlineKeyboardButton(
            edition_button_text(
                "Elite",
                selected,
            ),
            callback_data=f"hmode_set:{user_id}:Elite",
        ),
        InlineKeyboardButton(
            edition_button_text(
                "Master",
                selected,
            ),
            callback_data=f"hmode_set:{user_id}:Master",
        ),
    ])

    # Row 5
    keyboard.append([
        InlineKeyboardButton(
            edition_button_text(
                "Grandmaster",
                selected,
            ),
            callback_data=f"hmode_set:{user_id}:Grandmaster",
        ),
        InlineKeyboardButton(
            edition_button_text(
                "Mythic",
                selected,
            ),
            callback_data=f"hmode_set:{user_id}:Mythic",
        ),
    ])

    # Row 6
    keyboard.append([
        InlineKeyboardButton(
            edition_button_text(
                "Legendary",
                selected,
            ),
            callback_data=f"hmode_set:{user_id}:Legendary",
        ),
        InlineKeyboardButton(
            edition_button_text(
                "Ultimate",
                selected,
            ),
            callback_data=f"hmode_set:{user_id}:Ultimate",
        ),
    ])

    # Row 7
    keyboard.append([
        InlineKeyboardButton(
            edition_button_text(
                "Premium",
                selected,
            ),
            callback_data=f"hmode_set:{user_id}:Premium",
        ),
        InlineKeyboardButton(
            "♾️ All Editions",
            callback_data=f"hmode_set:{user_id}:ALL",
        ),
    ])

    # Close
    keyboard.append([
        InlineKeyboardButton(
            "❌ Close",
            callback_data=f"hmode_close:{user_id}",
        )
    ])

    return InlineKeyboardMarkup(
        keyboard
    )


# ============================================================
# HMODE TEXT
# ============================================================

def hmode_text(user_id):

    selected = get_hmode(
        user_id
    )

    if selected:

        emoji = EDITION_EMOJI.get(
            normalize_edition(selected),
            "🎴",
        )

        current_text = (
            f"{emoji} <b>{selected}</b>"
        )

    else:

        current_text = (
            "♾️ <b>All Editions</b>"
        )

    return (
        "🎛 <b>NEXUS HMODE</b>\n\n"
        f"📌 Current Mode: {current_text}\n\n"
        "🎴 Harem မှာ ကြည့်ချင်တဲ့ "
        "Card Edition ကို ရွေးပါ။\n\n"
        "ရွေးထားတဲ့ Edition ရဲ့ Card တွေကိုပဲ "
        "<code>/harem</code> မှာ ပြပေးပါမယ်။"
    )


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
# HAREM TEXT + KEYBOARD
# ============================================================

def build_harem_view(
    user_id,
    cards,
    page,
    total_collection,
):

    total_cards = len(cards)

    total_pages = max(
        1,
        math.ceil(
            total_cards
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

    selected = get_hmode(
        user_id
    )

    if selected:

        emoji = EDITION_EMOJI.get(
            normalize_edition(selected),
            "🎴",
        )

        mode_text = (
            f"{emoji} {selected}"
        )

    else:

        mode_text = (
            "♾️ All Editions"
        )

    text = (
        "🎴 <b>NEXUS HAREM</b>\n\n"
        f"📦 Total Collection: "
        f"<b>{total_collection}</b>\n"
        f"🎛 HMode: <b>{mode_text}</b>\n"
        f"🎴 Showing: <b>{total_cards}</b> Cards\n"
        f"📄 Page: <b>{page}/{total_pages}</b>\n\n"
    )

    if not page_cards:

        text += (
            "📭 ဒီ Edition မှာ "
            "Card မရှိသေးပါ။\n"
        )

    else:

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

    return (
        text,
        InlineKeyboardMarkup(
            keyboard
        ),
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
    # Reply User → View Their Harem
    # --------------------------------------------------------

    if message.reply_to_message:

        replied_user = (
            message.reply_to_message.from_user
        )

        if replied_user:

            target_user_id = (
                replied_user.id
            )

    all_cards = get_user_cards(
        target_user_id
    )

    all_cards = sort_cards(
        all_cards
    )

    total_collection = len(
        all_cards
    )

    if not all_cards:

        await message.reply_text(
            "🎴 <b>NEXUS HAREM</b>\n\n"
            "📭 ဒီ User မှာ Card မရှိသေးပါ။\n\n"
            "✨ Card ရလာတဲ့အခါ "
            "<code>/harem</code> နဲ့ "
            "ပြန်ကြည့်နိုင်ပါတယ်။",
            parse_mode="HTML",
        )

        return

    # --------------------------------------------------------
    # APPLY HMODE
    # --------------------------------------------------------

    cards = filter_cards_by_hmode(
        all_cards,
        target_user_id,
    )

    # --------------------------------------------------------
    # Selected Edition Has No Cards
    # --------------------------------------------------------

    if not cards:

        selected = get_hmode(
            target_user_id
        )

        emoji = EDITION_EMOJI.get(
            normalize_edition(selected),
            "🎴",
        )

        await message.reply_text(
            "🎴 <b>NEXUS HAREM</b>\n\n"
            f"{emoji} Selected Edition: "
            f"<b>{selected}</b>\n\n"
            "📭 ဒီ Edition မှာ "
            "Card မရှိသေးပါ။\n\n"
            "🎛 HMode ကနေ "
            "တခြား Edition ကို ရွေးနိုင်ပါတယ်။",
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton(
                        "🎛 Change HMode",
                        callback_data=(
                            f"harem_hmode:"
                            f"{target_user_id}"
                        ),
                    ),
                    InlineKeyboardButton(
                        "🔄 Reset",
                        callback_data=(
                            f"harem_reset:"
                            f"{target_user_id}"
                        ),
                    ),
                ]
            ]),
            parse_mode="HTML",
        )

        return

    text, keyboard = build_harem_view(
        target_user_id,
        cards,
        1,
        total_collection,
    )

    try:

        await message.reply_text(
            text,
            reply_markup=keyboard,
            parse_mode="HTML",
        )

    except Exception as e:

        print(
            f"[HAREM ERROR] {e}"
        )


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

    await message.reply_text(
        hmode_text(user.id),
        reply_markup=build_hmode_keyboard(
            user.id
        ),
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
        "✅ HMode filter ပြန်ရှင်းပြီးပါပြီ။\n"
        "🎴 Edition အားလုံးကို ပြန်ကြည့်နိုင်ပါပြီ။\n\n"
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

    if not query:
        return

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
            ":",
            2,
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
        # Security
        # ----------------------------------------------------

        if query.from_user.id != owner_id:

            await query.answer(
                "🚫 ဒီ Harem ကို မင်းမပိုင်ပါ။",
                show_alert=True,
            )

            return

        all_cards = get_user_cards(
            owner_id
        )

        all_cards = sort_cards(
            all_cards
        )

        total_collection = len(
            all_cards
        )

        cards = filter_cards_by_hmode(
            all_cards,
            owner_id,
        )

        if not cards:

            await query.answer(
                "📭 ဒီ Edition မှာ Card မရှိပါ။",
                show_alert=True,
            )

            return

        text, keyboard = build_harem_view(
            owner_id,
            cards,
            page,
            total_collection,
        )

        await query.answer()

        try:

            await query.edit_message_text(
                text,
                reply_markup=keyboard,
                parse_mode="HTML",
            )

        except Exception as e:

            print(
                f"[HAREM PAGE ERROR] {e}"
            )

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

        # ----------------------------------------------------
        # Make sure card is actually in owner's harem
        # ----------------------------------------------------

        owned_cards = get_user_cards(
            owner_id
        )

        owned = False

        for owned_card in owned_cards:

            if str(
                owned_card["char_id"]
            ) == str(char_id):

                owned = True

                break

        if not owned:

            await query.answer(
                "❌ ဒီ Card ကို မင်းမပိုင်ပါ။",
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
            f"💰 Price: "
            f"<b>{int(card['price'] or 0):,}</b> Coins\n"
        )

        keyboard = [
            [
                InlineKeyboardButton(
                    "⬅️ Harem",
                    callback_data=(
                        f"harem_page:"
                        f"{owner_id}:1"
                    ),
                ),
                InlineKeyboardButton(
                    "🎛 HMode",
                    callback_data=(
                        f"harem_hmode:"
                        f"{owner_id}"
                    ),
                ),
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

        except Exception as e:

            print(
                f"[CARD DETAIL ERROR] {e}"
            )

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

        await query.answer()

        try:

            await query.edit_message_text(
                hmode_text(owner_id),
                reply_markup=build_hmode_keyboard(
                    owner_id
                ),
                parse_mode="HTML",
            )

        except Exception as e:

            print(
                f"[HMODE MENU ERROR] {e}"
            )

        return

    # ========================================================
    # SET HMODE
    # ========================================================

    if data.startswith(
        "hmode_set:"
    ):

        parts = data.split(
            ":",
            2,
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

        except ValueError:

            await query.answer(
                "Invalid user.",
                show_alert=True,
            )

            return

        if query.from_user.id != owner_id:

            await query.answer(
                "🚫 ကိုယ့် HMode ကိုပဲ ပြောင်းနိုင်ပါတယ်။",
                show_alert=True,
            )

            return

        selected = parts[2]

        # ----------------------------------------------------
        # ALL
        # ----------------------------------------------------

        if normalize_edition(selected) == "all":

            set_hmode(
                owner_id,
                None,
            )

            await query.answer(
                "✅ All Editions selected!",
                show_alert=False,
            )

        else:

            valid = False

            for edition in EDITIONS:

                if (
                    normalize_edition(edition)
                    == normalize_edition(selected)
                ):

                    selected = edition
                    valid = True
                    break

            if not valid:

                await query.answer(
                    "❌ Invalid Edition.",
                    show_alert=True,
                )

                return

            set_hmode(
                owner_id,
                selected,
            )

            await query.answer(
                f"✅ {selected} selected!",
                show_alert=False,
            )

        # ----------------------------------------------------
        # Refresh Harem
        # ----------------------------------------------------

        all_cards = get_user_cards(
            owner_id
        )

        all_cards = sort_cards(
            all_cards
        )

        total_collection = len(
            all_cards
        )

        cards = filter_cards_by_hmode(
            all_cards,
            owner_id,
        )

        if not cards:

            current = get_hmode(
                owner_id
            )

            if current:

                emoji = EDITION_EMOJI.get(
                    normalize_edition(current),
                    "🎴",
                )

                text = (
                    "🎴 <b>NEXUS HAREM</b>\n\n"
                    f"{emoji} Selected: "
                    f"<b>{current}</b>\n\n"
                    "📭 ဒီ Edition မှာ "
                    "Card မရှိသေးပါ။"
                )

            else:

                text = (
                    "🎴 <b>NEXUS HAREM</b>\n\n"
                    "📭 Harem မှာ Card မရှိသေးပါ။"
                )

            keyboard = InlineKeyboardMarkup([
                [
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
                ]
            ])

            try:

                await query.edit_message_text(
                    text,
                    reply_markup=keyboard,
                    parse_mode="HTML",
                )

            except Exception as e:

                print(
                    f"[HMODE EMPTY ERROR] {e}"
                )

            return

        text, keyboard = build_harem_view(
            owner_id,
            cards,
            1,
            total_collection,
        )

        try:

            await query.edit_message_text(
                text,
                reply_markup=keyboard,
                parse_mode="HTML",
            )

        except Exception as e:

            print(
                f"[HMODE SET ERROR] {e}"
            )

        return

    # ========================================================
    # HMODE CLOSE
    # ========================================================

    if data.startswith(
        "hmode_close:"
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
                "🚫 ဒီ Menu ကို မင်းပိတ်လို့မရပါ။",
                show_alert=True,
            )

            return

        await query.answer()

        try:

            await query.edit_message_text(
                "🎛 <b>HMODE</b>\n\n"
                "Menu ပိတ်လိုက်ပါပြီ။\n\n"
                "📌 <code>/harem</code> "
                "သို့မဟုတ် <code>/hmode</code> ကို ပြန်သုံးနိုင်ပါတယ်။",
                parse_mode="HTML",
            )

        except Exception as e:

            print(
                f"[HMODE CLOSE ERROR] {e}"
            )

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
            show_alert=False,
        )

        try:

            await query.edit_message_text(
                "🔄 <b>HAREM RESET</b>\n\n"
                "✅ HMode filter ပြန်ရှင်းပြီးပါပြီ။\n"
                "🎴 Edition အားလုံးကို ပြန်ကြည့်နိုင်ပါပြီ။\n\n"
                "📌 <code>/harem</code> ကို ပြန်သုံးပါ။",
                parse_mode="HTML",
            )

        except Exception as e:

            print(
                f"[HAREM RESET ERROR] {e}"
            )

        return

    # ========================================================
    # UNKNOWN CALLBACK
    # ========================================================

    await query.answer()
