```python
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy import select

from database import (
    SessionLocal,
    Card,
)


router = Router()


# =========================================================
# OWNER
# =========================================================

OWNER_ID = 7974865879


# =========================================================
# ADMIN CHECK
# =========================================================

def is_admin(telegram_id: int) -> bool:
    return telegram_id == OWNER_ID


# =========================================================
# /cards
# =========================================================

@router.message(Command("cards"))
async def cards_command(message: Message):

    async with SessionLocal() as session:

        result = await session.execute(
            select(Card)
            .order_by(Card.id.asc())
        )

        cards = result.scalars().all()

        if not cards:
            await message.answer(
                "🎴 <b>CARDS</b>\n\n"
                "📭 No cards have been added yet.",
                parse_mode="HTML",
            )
            return

        lines = [
            "╔══════════════════════════╗",
            "        🎴 <b>CARDS</b>",
            "╚══════════════════════════╝",
            "",
            f"🃏 Total: <b>{len(cards)}</b>",
            "",
        ]

        for card in cards:

            lines.append(
                f"🎴 <b>#{card.id:04d}</b> — "
                f"<b>{card.name}</b>"
            )

            lines.append(
                f"   💠 {card.rarity}"
            )

            lines.append("")

        await message.answer(
            "\n".join(lines),
            parse_mode="HTML",
        )


# =========================================================
# /cardcount
# =========================================================

@router.message(Command("cardcount"))
async def card_count(message: Message):

    async with SessionLocal() as session:

        result = await session.execute(
            select(Card)
        )

        cards = result.scalars().all()

    await message.answer(
        "🎴 <b>CARD DATABASE</b>\n\n"
        f"🃏 Total Cards: <b>{len(cards)}</b>",
        parse_mode="HTML",
    )


# =========================================================
# /check
# =========================================================

@router.message(Command("check"))
async def check_card(message: Message):

    parts = message.text.split() if message.text else []

    if len(parts) < 2:

        await message.answer(
            "🎴 <b>Card Check</b>\n\n"
            "အသုံးပြုပုံ:\n"
            "<code>/check 001</code>",
            parse_mode="HTML",
        )
        return

    try:
        card_id = int(parts[1])

    except ValueError:

        await message.answer(
            "❌ Card ID က နံပါတ်ဖြစ်ရပါမယ်။"
        )
        return

    async with SessionLocal() as session:

        result = await session.execute(
            select(Card).where(
                Card.id == card_id
            )
        )

        card = result.scalar_one_or_none()

        if card is None:

            await message.answer(
                "❌ ဒီ Card မရှိသေးပါဘူး။"
            )
            return

        text = (
            "╔══════════════════════════╗\n"
            "        🎴 <b>CARD</b>\n"
            "╚══════════════════════════╝\n\n"

            f"🆔 ID: <code>{card.id:04d}</code>\n"
            f"✨ Name: <b>{card.name}</b>\n"
            f"💠 Rarity: <b>{card.rarity}</b>\n\n"

            f"⚔️ ATK: <b>{card.attack}</b>\n"
            f"🛡 DEF: <b>{card.defense}</b>\n"
            f"❤️ HP: <b>{card.hp}</b>\n"
            f"💨 Speed: <b>{card.speed}</b>\n\n"

            f"🌟 Element: "
            f"<b>{card.element or 'Unknown'}</b>\n"

            f"🎭 Class: "
            f"<b>{card.card_class or 'Unknown'}</b>\n"

            f"💰 Price: "
            f"<b>{card.base_price:,}</b> Coins"
        )

        if card.description:

            text += (
                "\n\n📝 <b>Description</b>\n"
                f"{card.description}"
            )

        if card.image_url:

            await message.answer_photo(
                photo=card.image_url,
                caption=text,
                parse_mode="HTML",
            )

        else:

            await message.answer(
                text,
                parse_mode="HTML",
            )


# =========================================================
# /addcard
# =========================================================

@router.message(Command("addcard"))
async def addcard_command(message: Message):

    if message.from_user is None:
        return

    if not is_admin(message.from_user.id):

        await message.answer(
            "🚫 <b>Admin only.</b>",
            parse_mode="HTML",
        )
        return

    await message.answer(
        "🎴 <b>ADD CARD</b>\n\n"

        "Card ပုံကို ပို့ပြီး "
        "Caption ထဲမှာ ဒီလိုရေးပါ:\n\n"

        "<code>001 | Naruto | Legendary</code>\n\n"

        "📌 Format:\n"
        "<code>ID | Name | Rarity</code>\n\n"

        "ဥပမာ:\n"
        "<code>1 | Naruto | Legendary</code>\n"
        "<code>2 | Sasuke | Epic</code>\n"
        "<code>3 | Sakura | Rare</code>",
        parse_mode="HTML",
    )


# =========================================================
# PHOTO + CAPTION = ADD CARD
# =========================================================

@router.message(F.photo)
async def add_card_from_photo(message: Message):

    if message.from_user is None:
        return

    # Owner only
    if not is_admin(message.from_user.id):
        return

    caption = message.caption

    if not caption:

        await message.answer(
            "❌ Caption မပါပါဘူး။\n\n"

            "ပုံပေါ်မှာ Caption ကို ဒီလိုရေးပါ:\n"
            "<code>001 | Naruto | Legendary</code>",
            parse_mode="HTML",
        )

        return

    # -----------------------------------------------------
    # PARSE CAPTION
    # -----------------------------------------------------

    parts = [
        item.strip()
        for item in caption.split("|")
    ]

    if len(parts) < 3:

        await message.answer(
            "❌ Format မှားနေပါတယ်။\n\n"

            "မှန်ကန်တဲ့ Format:\n"
            "<code>ID | Name | Rarity</code>\n\n"

            "ဥပမာ:\n"
            "<code>001 | Naruto | Legendary</code>",
            parse_mode="HTML",
        )

        return

    try:

        card_id = int(parts[0])

    except ValueError:

        await message.answer(
            "❌ Card ID က နံပါတ်ဖြစ်ရပါမယ်။\n\n"
            "ဥပမာ: <code>001</code>",
            parse_mode="HTML",
        )

        return

    name = parts[1]
    rarity = parts[2]

    if not name:

        await message.answer(
            "❌ Card Name မပါပါဘူး။"
        )
        return

    if not rarity:

        await message.answer(
            "❌ Rarity မပါပါဘူး။"
        )
        return

    # -----------------------------------------------------
    # TELEGRAM PHOTO FILE ID
    # -----------------------------------------------------

    photo = message.photo[-1]

    image_file_id = photo.file_id

    # -----------------------------------------------------
    # DATABASE
    # -----------------------------------------------------

    async with SessionLocal() as session:

        result = await session.execute(
            select(Card).where(
                Card.id == card_id
            )
        )

        existing_card = result.scalar_one_or_none()

        if existing_card is not None:

            await message.answer(
                "❌ ဒီ Card ID ရှိပြီးသားပါ။\n\n"

                f"🆔 ID: <code>{existing_card.id:04d}</code>\n"
                f"🎴 Name: <b>{existing_card.name}</b>\n"
                f"💠 Rarity: <b>{existing_card.rarity}</b>",
                parse_mode="HTML",
            )

            return

        # -------------------------------------------------
        # CREATE CARD
        # -------------------------------------------------

        card = Card(
            id=card_id,

            name=name,

            rarity=rarity,

            attack=10,

            defense=10,

            hp=100,

            speed=10,

            element=None,

            card_class=None,

            description=None,

            image_url=image_file_id,

            base_price=100,

            is_limited=False,

            is_shiny=False,

            is_animated=False,

            is_premium=False,
        )

        session.add(card)

        await session.commit()

    # -----------------------------------------------------
    # SUCCESS
    # -----------------------------------------------------

    await message.answer(
        "✅ <b>CARD ADDED!</b>\n\n"

        f"🆔 ID: <code>{card_id:04d}</code>\n"
        f"🎴 Name: <b>{name}</b>\n"
        f"💠 Rarity: <b>{rarity}</b>\n"
        "🖼️ Image: ✅\n\n"

        "🎉 Database ထဲကို Card ထည့်ပြီးပါပြီ။\n"
        "🎲 /drop မှာ ဒီ Card ကို အသုံးပြုနိုင်ပါပြီ။",
        parse_mode="HTML",
    )


# =========================================================
# /deletecard
# =========================================================

@router.message(Command("deletecard"))
async def delete_card(message: Message):

    if message.from_user is None:
        return

    if not is_admin(message.from_user.id):

        await message.answer(
            "🚫 <b>Admin only.</b>",
            parse_mode="HTML",
        )
        return

    parts = message.text.split() if message.text else []

    if len(parts) < 2:

        await message.answer(
            "🗑️ အသုံးပြုပုံ:\n\n"
            "<code>/deletecard 001</code>",
            parse_mode="HTML",
        )
        return

    try:

        card_id = int(parts[1])

    except ValueError:

        await message.answer(
            "❌ Invalid Card ID."
        )
        return

    async with SessionLocal() as session:

        result = await session.execute(
            select(Card).where(
                Card.id == card_id
            )
        )

        card = result.scalar_one_or_none()

        if card is None:

            await message.answer(
                "❌ ဒီ Card မတွေ့ပါဘူး။"
            )
            return

        card_name = card.name

        await session.delete(card)

        await session.commit()

    await message.answer(
        "🗑️ <b>CARD DELETED</b>\n\n"

        f"🆔 ID: <code>{card_id:04d}</code>\n"
        f"🎴 Name: <b>{card_name}</b>",
        parse_mode="HTML",
    )
```
