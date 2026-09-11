# ============================================================
# Nexus Catch Bot
# harem_system.py
# ============================================================

from __future__ import annotations

import math
from typing import Any

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

HAREM_PER_PAGE = 8


# ============================================================
# 13 EDITIONS
# ============================================================

EDITIONS = [
    "Common",
    "Uncommon",
    "Rare",
    "Legends",
    "Mythical",
    "Divine",
    "Crossverse",
    "Cataphract",
    "Supreme",
    "Celestial",
    "Immortal",
    "Eternal",
    "Premium",
]


# ============================================================
# EDITION ORDER
# ============================================================

EDITION_ORDER = {
    "common": 1,
    "uncommon": 2,
    "rare": 3,
    "legends": 4,
    "mythical": 5,
    "divine": 6,
    "crossverse": 7,
    "cataphract": 8,
    "supreme": 9,
    "celestial": 10,
    "immortal": 11,
    "eternal": 12,
    "premium": 13,
}


# ============================================================
# EDITION EMOJI
# ============================================================

EDITION_EMOJI = {
    "common": "⚪",
    "uncommon": "🟢",
    "rare": "🔵",
    "legends": "🟣",
    "mythical": "🌌",
    "divine": "✨",
    "crossverse": "🌠",
    "cataphract": "⚔️",
    "supreme": "👑",
    "celestial": "☄️",
    "immortal": "🔥",
    "eternal": "♾️",
    "premium": "💎",
}


# ============================================================
# USER HMODE
#
# user_id -> selected edition
# None = All Editions
# ============================================================

USER_HMODE: dict[int, str] = {}


# ============================================================
# SAFE ROW GET
# ============================================================

def row_get(
    row: Any,
    key: str,
    default: Any = None,
) -> Any:

    if row is None:
        return default

    if isinstance(row, dict):
        return row.get(key, default)

    try:
        return row[key]
    except Exception:
        pass

    try:
        return getattr(row, key)
    except Exception:
        return default


# ============================================================
# SAFE INT
# ============================================================

def safe_int(
    value: Any,
    default: int = 0,
) -> int:

    try:
        return int(value)
    except Exception:
        return default


# ============================================================
# NORMALIZE EDITION
# ============================================================

def normalize_edition(
    value: Any,
) -> str:

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
# CANONICAL EDITION
# ============================================================

def canonical_edition(
    value: Any,
) -> str:

    normalized = normalize_edition(value)

    for edition in EDITIONS:

        if normalize_edition(edition) == normalized:
            return edition

    return str(value).strip() if value else "Common"


# ============================================================
# CARD ID SORT VALUE
# ============================================================

def card_id_sort_value(
    card_id: Any,
) -> int:

    if card_id is None:
        return 999999999

    value = str(card_id).strip()

    # NXS001
    upper = value.upper()

    if upper.startswith("NXS"):
        value = value[3:]

    # Numeric only
    try:
        return int(value)
    except Exception:
        pass

    # Extract digits from mixed IDs
    digits = "".join(
        char
        for char in value
        if char.isdigit()
    )

    if digits:
        try:
            return int(digits)
        except Exception:
            pass

    return 999999999


# ============================================================
# NORMALIZE USER CARD
# ============================================================

def normalize_user_card(
    row: Any,
) -> dict | None:

    if row is None:
        return None

    char_id = row_get(
        row,
        "char_id",
        row_get(
            row,
            "card_id",
            "",
        ),
    )

    if not char_id:
        return None

    quantity = safe_int(
        row_get(
            row,
            "quantity",
            row_get(
                row,
                "count",
                1,
            ),
        ),
        1,
    )

    # Older database versions may store
    # one row per copy instead of quantity.
    if quantity <= 0:
        quantity = 1

    return {
        "char_id": str(char_id),
        "quantity": quantity,
        "level": safe_int(
            row_get(row, "level", 1),
            1,
        ),
        "exp": safe_int(
            row_get(row, "exp", 0),
        ),
        "favorite": bool(
            row_get(row, "favorite", 0)
        ),
    }


# ============================================================
# LOAD USER CARDS
# ============================================================

def load_user_cards(
    user_id: int,
) -> list[dict]:

    try:
        rows = get_user_cards(
            int(user_id)
        )
    except Exception as exc:
        print(
            f"[HAREM DB ERROR] {exc}"
        )
        return []

    result = []

    for row in rows or []:

        card = normalize_user_card(row)

        if card is not None:
            result.append(card)

    return result


# ============================================================
# LOAD CARD DATA
# ============================================================

def load_card(
    char_id: str,
) -> dict | None:

    try:
        row = get_card(char_id)
    except Exception as exc:
        print(
            f"[HAREM CARD ERROR] {exc}"
        )
        return None

    if row is None:
        return None

    return {
        "char_id": str(
            row_get(
                row,
                "char_id",
                row_get(
                    row,
                    "card_id",
                    char_id,
                ),
            )
        ),
        "name": str(
            row_get(
                row,
                "name",
                "Unknown Card",
            )
        ),
        "edition": canonical_edition(
            row_get(
                row,
                "edition",
                "Common",
            )
        ),
        "rarity": str(
            row_get(
                row,
                "rarity",
                "Common",
            )
        ),
        "price": safe_int(
            row_get(
                row,
                "price",
                0,
            )
        ),
        "description": str(
            row_get(
                row,
                "description",
                "",
            )
            or ""
        ),
    }


# ============================================================
# BUILD HAREM CARD LIST
# ============================================================

def build_harem_cards(
    user_id: int,
) -> list[dict]:

    owned = load_user_cards(
        user_id
    )

    result = []

    for user_card in owned:

        card = load_card(
            user_card["char_id"]
        )

        if card is None:
            # Keep collection even if card
            # metadata is temporarily missing.
            card = {
                "char_id": user_card["char_id"],
                "name": "Unknown Card",
                "edition": "Common",
                "rarity": "Common",
                "price": 0,
                "description": "",
            }

        result.append({
            **card,
            "quantity": user_card["quantity"],
            "level": user_card["level"],
            "exp": user_card["exp"],
            "favorite": user_card["favorite"],
        })

    return sort_cards(result)


# ============================================================
# GET HMODE
# ============================================================

def get_hmode(
    user_id: int,
) -> str | None:

    return USER_HMODE.get(
        int(user_id)
    )


# ============================================================
# SET HMODE
# ============================================================

def set_hmode(
    user_id: int,
    edition: str | None,
) -> None:

    user_id = int(user_id)

    if edition is None:
        USER_HMODE.pop(
            user_id,
            None,
        )
        return

    canonical = canonical_edition(
        edition
    )

    if canonical in EDITIONS:

        USER_HMODE[user_id] = canonical


# ============================================================
# FILTER BY HMODE
# ============================================================

def filter_cards_by_hmode(
    cards: list[dict],
    user_id: int,
) -> list[dict]:

    selected = get_hmode(
        user_id
    )

    if not selected:
        return list(cards)

    selected_normalized = normalize_edition(
        selected
    )

    return [
        card
        for card in cards
        if normalize_edition(
            card.get(
                "edition",
                "Common",
            )
        )
        == selected_normalized
    ]


# ============================================================
# SORT CARDS
# ============================================================

def sort_cards(
    cards: list[dict],
) -> list[dict]:

    def sort_key(
        card: dict,
    ):

        edition = normalize_edition(
            card.get(
                "edition",
                "Common",
            )
        )

        return (
            EDITION_ORDER.get(
                edition,
                999,
            ),
            card_id_sort_value(
                card.get(
                    "char_id",
                    "",
                )
            ),
            str(
                card.get(
                    "name",
                    "",
                )
            ).lower(),
        )

    return sorted(
        cards,
        key=sort_key,
    )


# ============================================================
# EDITION BUTTON
# ============================================================

def edition_button_text(
    edition: str,
    selected: str | None,
) -> str:

    emoji = EDITION_EMOJI.get(
        normalize_edition(edition),
        "🎴",
    )

    if (
        selected
        and normalize_edition(selected)
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
    user_id: int,
) -> InlineKeyboardMarkup:

    selected = get_hmode(
        user_id
    )

    keyboard = []

    # 13 editions
    for index in range(
        0,
        len(EDITIONS),
        2,
    ):

        row = []

        first = EDITIONS[index]

        row.append(
            InlineKeyboardButton(
                edition_button_text(
                    first,
                    selected,
                ),
                callback_data=(
                    f"hmode_set:"
                    f"{user_id}:"
                    f"{first}"
                ),
            )
        )

        if index + 1 < len(EDITIONS):

            second = EDITIONS[
                index + 1
            ]

            row.append(
                InlineKeyboardButton(
                    edition_button_text(
                        second,
                        selected,
                    ),
                    callback_data=(
                        f"hmode_set:"
                        f"{user_id}:"
                        f"{second}"
                    ),
                )
            )

        keyboard.append(row)

    # All
    all_text = (
        "♾️ All Editions"
    )

    if selected is None:
        all_text = (
            "✅ ♾️ All Editions"
        )

    keyboard.append([
        InlineKeyboardButton(
            all_text,
            callback_data=(
                f"hmode_set:"
                f"{user_id}:ALL"
            ),
        )
    ])

    # Close
    keyboard.append([
        InlineKeyboardButton(
            "❌ Close",
            callback_data=(
                f"hmode_close:"
                f"{user_id}"
            ),
        )
    ])

    return InlineKeyboardMarkup(
        keyboard
    )


# ============================================================
# HMODE TEXT
# ============================================================

def hmode_text(
    user_id: int,
) -> str:

    selected = get_hmode(
        user_id
    )

    if selected:

        emoji = EDITION_EMOJI.get(
            normalize_edition(selected),
            "🎴",
        )

        current = (
            f"{emoji} <b>{selected}</b>"
        )

    else:

        current = (
            "♾️ <b>All Editions</b>"
        )

    return (
        "╔════════════════════╗\n"
        "     🎛 <b>NEXUS HMODE</b>\n"
        "╚════════════════════╝\n\n"

        f"📌 Current Mode: {current}\n\n"

        "🎴 <b>13 CARD EDITIONS</b>\n\n"

        "⚪ Common\n"
        "🟢 Uncommon\n"
        "🔵 Rare\n"
        "🟣 Legends\n"
        "🌌 Mythical\n"
        "✨ Divine\n"
        "🌠 Crossverse\n"
        "⚔️ Cataphract\n"
        "👑 Supreme\n"
        "☄️ Celestial\n"
        "🔥 Immortal\n"
        "♾️ Eternal\n"
        "💎 Premium\n\n"

        "👇 Harem မှာ ကြည့်ချင်တဲ့ "
        "<b>Edition</b> ကို ရွေးပါ။"
    )


# ============================================================
# CARD LINE
# ============================================================

def format_harem_card(
    card: dict,
    number: int,
) -> str:

    edition = canonical_edition(
        card.get(
            "edition",
            "Common",
        )
    )

    emoji = EDITION_EMOJI.get(
        normalize_edition(edition),
        "🎴",
    )

    name = str(
        card.get(
            "name",
            "Unknown Card",
        )
    )

    char_id = str(
        card.get(
            "char_id",
            "",
        )
    )

    quantity = safe_int(
        card.get(
            "quantity",
            1,
        ),
        1,
    )

    favorite = (
        " ❤️"
        if card.get(
            "favorite",
            False,
        )
        else ""
    )

    return (
        f"<b>{number}</b> | "
        f"{emoji} | "
        f"<b>{name}</b> "
        f"[<code>{char_id}</code>] "
        f"<b>(x{quantity:,})</b>"
        f"{favorite}"
    )


# ============================================================
# HAREM HEADER
# ============================================================

def build_harem_header(
    user_id: int,
    page: int,
    total_pages: int,
    total_unique: int,
    total_quantity: int,
    showing: int,
) -> str:

    selected = get_hmode(
        user_id
    )

    if selected:

        emoji = EDITION_EMOJI.get(
            normalize_edition(selected),
            "🎴",
        )

        mode = (
            f"{emoji} {selected}"
        )

    else:

        mode = (
            "♾️ All Editions"
        )

    return (
        "╔══════════════════════════╗\n"
        "       🎴 <b>NEXUS HAREM</b>\n"
        "╚══════════════════════════╝\n\n"

        f"🎛 HMode : <b>{mode}</b>\n"
        f"📦 Cards : <b>{total_unique}</b> "
        f"Unique • <b>{total_quantity}</b> Total\n"
        f"📋 Showing : <b>{showing}</b>\n"
        f"📄 Page : <b>{page}/{total_pages}</b>\n\n"
    )


# ============================================================
# HAREM VIEW
# ============================================================

def build_harem_view(
    user_id: int,
    cards: list[dict],
    page: int,
    total_collection: int,
):

    total_cards = len(
        cards
    )

    total_quantity = sum(
        safe_int(
            card.get(
                "quantity",
                1,
            ),
            1,
        )
        for card in cards
    )

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
            int(page),
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

    text = build_harem_header(
        user_id,
        page,
        total_pages,
        total_collection,
        total_quantity,
        len(page_cards),
    )

    if not page_cards:

        text += (
            "📭 <b>No Cards</b>\n\n"
            "ဒီ HMode မှာ Card မရှိသေးပါ။"
        )

    else:

        # Screenshot-style separator
        text += (
            "━━━━━━━━━━━━━━━━━━\n"
        )

        for index, card in enumerate(
            page_cards,
            start=start + 1,
        ):

            text += (
                format_harem_card(
                    card,
                    index,
                )
                + "\n"
            )

            text += (
                "━━━━━━━━━━━━━━━━━━\n"
            )

    keyboard = []

    # ========================================================
    # CARD BUTTONS
    # ========================================================

    for card in page_cards:

        char_id = str(
            card.get(
                "char_id",
                "",
            )
        )

        name = str(
            card.get(
                "name",
                "Card",
            )
        )

        # Telegram callback limit protection
        button_name = name[:28]

        keyboard.append([
            InlineKeyboardButton(
                f"🎴 {button_name}",
                callback_data=(
                    f"harem_card:"
                    f"{user_id}:"
                    f"{char_id}"
                ),
            )
        ])

    # ========================================================
    # PAGINATION
    # ========================================================

    navigation = []

    if page > 1:

        navigation.append(
            InlineKeyboardButton(
                "⬅️ Previous",
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
                "Next ➡️",
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

    # ========================================================
    # HMODE / RESET
    # ========================================================

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

    # Reply to another user's message
    if message.reply_to_message:

        replied_user = (
            message.reply_to_message.from_user
        )

        if replied_user:
            target_user_id = replied_user.id

    all_cards = build_harem_cards(
        target_user_id
    )

    if not all_cards:

        await message.reply_text(
            "╔════════════════════╗\n"
            "     🎴 <b>NEXUS HAREM</b>\n"
            "╚════════════════════╝\n\n"
            "📭 ဒီ User မှာ Card မရှိသေးပါ။\n\n"
            "✨ Card ရလာတဲ့အခါ "
            "<code>/harem</code> နဲ့ "
            "ပြန်ကြည့်နိုင်ပါတယ်။",
            parse_mode="HTML",
        )

        return

    total_unique = len(
        all_cards
    )

    cards = filter_cards_by_hmode(
        all_cards,
        target_user_id,
    )

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
            "📭 ဒီ Edition မှာ Card မရှိသေးပါ။",
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
        total_unique,
    )

    try:

        await message.reply_text(
            text,
            reply_markup=keyboard,
            parse_mode="HTML",
        )

    except Exception as exc:

        print(
            f"[HAREM ERROR] {exc}"
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
    # PAGE
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

        if query.from_user.id != owner_id:

            await query.answer(
                "🚫 ဒီ Harem ကို မင်းမပိုင်ပါ။",
                show_alert=True,
            )
            return

        all_cards = build_harem_cards(
            owner_id
        )

        total_unique = len(
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
            total_unique,
        )

        await query.answer()

        try:

            await query.edit_message_text(
                text,
                reply_markup=keyboard,
                parse_mode="HTML",
            )

        except Exception as exc:

            print(
                f"[HAREM PAGE ERROR] {exc}"
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

        owned_cards = build_harem_cards(
            owner_id
        )

        owned = None

        for item in owned_cards:

            if str(
                item.get(
                    "char_id",
                    "",
                )
            ) == str(char_id):

                owned = item
                break

        if owned is None:

            await query.answer(
                "❌ ဒီ Card ကို မင်းမပိုင်ပါ။",
                show_alert=True,
            )
            return

        card = load_card(
            char_id
        )

        if card is None:

            await query.answer(
                "❌ Card မတွေ့ပါ။",
                show_alert=True,
            )
            return

        emoji = EDITION_EMOJI.get(
            normalize_edition(
                card["edition"]
            ),
            "🎴",
        )

        description = (
            card["description"]
            or "No description."
        )

        text = (
            "╔════════════════════╗\n"
            "       🎴 <b>CARD DETAIL</b>\n"
            "╚════════════════════╝\n\n"

            f"{emoji} <b>{card['name']}</b>\n\n"

            f"🆔 ID : "
            f"<code>{card['char_id']}</code>\n"

            f"💎 Edition : "
            f"<b>{card['edition']}</b>\n"

            f"⭐ Rarity : "
            f"<b>{card['rarity']}</b>\n"

            f"💰 Price : "
            f"<b>{card['price']:,}</b> Coins\n\n"

            f"📦 Quantity : "
            f"<b>{owned['quantity']:,}</b>\n"

            f"📊 Level : "
            f"<b>{owned['level']}</b>\n\n"

            f"📝 <i>{description}</i>"
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

        except Exception as exc:

            print(
                f"[CARD DETAIL ERROR] {exc}"
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
                hmode_text(
                    owner_id
                ),
                reply_markup=build_hmode_keyboard(
                    owner_id
                ),
                parse_mode="HTML",
            )

        except Exception as exc:

            print(
                f"[HMODE MENU ERROR] {exc}"
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

        # ALL
        if normalize_edition(
            selected
        ) == "all":

            set_hmode(
                owner_id,
                None,
            )

            await query.answer(
                "✅ All Editions selected!",
                show_alert=False,
            )

        else:

            selected_canonical = None

            for edition in EDITIONS:

                if (
                    normalize_edition(
                        edition
                    )
                    == normalize_edition(
                        selected
                    )
                ):

                    selected_canonical = edition
                    break

            if selected_canonical is None:

                await query.answer(
                    "❌ Invalid Edition.",
                    show_alert=True,
                )
                return

            set_hmode(
                owner_id,
                selected_canonical,
            )

            await query.answer(
                f"✅ {selected_canonical} selected!",
                show_alert=False,
            )

        # Refresh
        all_cards = build_harem_cards(
            owner_id
        )

        total_unique = len(
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
                    normalize_edition(
                        current
                    ),
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

            except Exception as exc:

                print(
                    f"[HMODE EMPTY ERROR] {exc}"
                )

            return

        text, keyboard = build_harem_view(
            owner_id,
            cards,
            1,
            total_unique,
        )

        try:

            await query.edit_message_text(
                text,
                reply_markup=keyboard,
                parse_mode="HTML",
            )

        except Exception as exc:

            print(
                f"[HMODE SET ERROR] {exc}"
            )

        return

    # ========================================================
    # CLOSE
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
                "သို့မဟုတ် <code>/hmode</code> ကို "
                "ပြန်သုံးနိုင်ပါတယ်။",
                parse_mode="HTML",
            )

        except Exception as exc:

            print(
                f"[HMODE CLOSE ERROR] {exc}"
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
                "📌 <code>/harem</code> ကို "
                "ပြန်သုံးပါ။",
                parse_mode="HTML",
            )

        except Exception as exc:

            print(
                f"[HAREM RESET ERROR] {exc}"
            )

        return

    # Unknown
    await query.answer()
