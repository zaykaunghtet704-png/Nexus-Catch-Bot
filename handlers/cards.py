from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy import select

from database import SessionLocal, Card


router = Router()

ADMIN_IDS = {7974865879}

card_creation = {}


def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


@router.message(Command("addcard"))
async def addcard_command(message: Message):
    if message.from_user is None:
        return

    if not is_admin(message.from_user.id):
        await message.answer(
            "❌ Admin Only\n\n"
            "ဒီ command ကို Admin ပဲ အသုံးပြုနိုင်ပါတယ်။"
        )
        return

    card_creation[message.from_user.id] = {
        "step": "name"
    }

    await message.answer(
        "🎴 ADD NEW CARD\n\n"
        "Step 1/8\n\n"
        "📝 Card Name ကို ပို့ပါ။\n\n"
        "ဥပမာ - Naruto Uzumaki\n\n"
        "❌ ပယ်ဖျက်ရန် /cancelcard"
    )


@router.message(Command("cancelcard"))
async def cancelcard_command(message: Message):
    if message.from_user is None:
        return

    if not is_admin(message.from_user.id):
        return

    card_creation.pop(message.from_user.id, None)

    await message.answer(
        "❌ Card creation cancelled."
    )


@router.message(F.photo)
async def receive_card_photo(message: Message):
    if message.from_user is None:
        return

    user_id = message.from_user.id

    if not is_admin(user_id):
        return

    if user_id not in card_creation:
        return

    data = card_creation[user_id]

    if data.get("step") != "image":
        return

    photo = message.photo[-1]

    data["image_url"] = photo.file_id

    await save_card(message, data)

    card_creation.pop(user_id, None)


@router.message(F.text)
async def receive_card_text(message: Message):
    if message.from_user is None:
        return

    user_id = message.from_user.id

    if not is_admin(user_id):
        return

    if user_id not in card_creation:
        return

    data = card_creation[user_id]

    step = data.get("step")

    text = (message.text or "").strip()

    if not text:
        return

    if step == "name":

        data["name"] = text
        data["step"] = "rarity"

        await message.answer(
            "💠 Step 2/8\n\n"
            "Rarity ကို ပို့ပါ။\n\n"
            "ဥပမာ:\n"
            "Common\n"
            "Rare\n"
            "Epic\n"
            "Legendary\n"
            "Mythic\n"
            "Premium Edition"
        )

        return

    if step == "rarity":

        data["rarity"] = text
        data["step"] = "attack"

        await message.answer(
            "⚔️ Step 3/8\n\n"
            "Attack ကို နံပါတ်နဲ့ ပို့ပါ။\n\n"
            "ဥပမာ - 100"
        )

        return

    if step == "attack":

        try:
            data["attack"] = int(text)
        except ValueError:
            await message.answer(
                "❌ Attack က နံပါတ်ဖြစ်ရပါမယ်။"
            )
            return

        data["step"] = "defense"

        await message.answer(
            "🛡 Step 4/8\n\n"
            "Defense ကို ပို့ပါ။"
        )

        return

    if step == "defense":

        try:
            data["defense"] = int(text)
        except ValueError:
            await message.answer(
                "❌ Defense က နံပါတ်ဖြစ်ရပါမယ်။"
            )
            return

        data["step"] = "hp"

        await message.answer(
            "❤️ Step 5/8\n\n"
            "HP ကို ပို့ပါ။"
        )

        return

    if step == "hp":

        try:
            data["hp"] = int(text)
        except ValueError:
            await message.answer(
                "❌ HP က နံပါတ်ဖြစ်ရပါမယ်။"
            )
            return

        data["step"] = "speed"

        await message.answer(
            "💨 Step 6/8\n\n"
            "Speed ကို ပို့ပါ။"
        )

        return

    if step == "speed":

        try:
            data["speed"] = int(text)
        except ValueError:
            await message.answer(
                "❌ Speed က နံပါတ်ဖြစ်ရပါမယ်။"
            )
            return

        data["step"] = "description"

        await message.answer(
            "📝 Step 7/8\n\n"
            "Description ကို ပို့ပါ။\n\n"
            "မထည့်ချင်ရင် - လို့ပို့ပါ။"
        )

        return

    if step == "description":

        if text == "-":
            data["description"] = None
        else:
            data["description"] = text

        data["step"] = "image"

        await message.answer(
            "🖼 Step 8/8\n\n"
            "Card ပုံကို Photo အနေနဲ့ ပို့ပါ။\n\n"
            "ပုံမထည့်ချင်ရင် `skip` လို့ပို့ပါ။"
        )

        return

    if step == "image" and text.lower() == "skip":

        data["image_url"] = None

        await save_card(message, data)

        card_creation.pop(user_id, None)

        return


async def save_card(
    message: Message,
    data: dict,
):

    rarity = data["rarity"]

    is_premium = (
        rarity.lower() == "premium edition"
    )

    async with SessionLocal() as session:

        card = Card(
            name=data["name"],
            rarity=data["rarity"],
            attack=data["attack"],
            defense=data["defense"],
            hp=data["hp"],
            speed=data["speed"],
            element=None,
            card_class=None,
            description=data.get("description"),
            image_url=data.get("image_url"),
            base_price=100,
            is_limited=False,
            is_shiny=False,
            is_animated=False,
            is_premium=is_premium,
        )

        session.add(card)

        await session.commit()

        await session.refresh(card)

        card_id = card.id

    image_text = (
        "🖼 ပုံပါသည်"
        if data.get("image_url")
        else "🖼 ပုံမပါပါ"
    )

    await message.answer(
        "╔══════════════════════════╗\n"
        "       🎴 CARD CREATED\n"
        "╚══════════════════════════╝\n\n"
        f"🆔 ID: <code>{card_id:04d}</code>\n"
        f"🎴 Name: <b>{data['name']}</b>\n"
        f"💠 Rarity: <b>{data['rarity']}</b>\n\n"
        f"⚔️ ATK: <b>{data['attack']}</b>\n"
        f"🛡 DEF: <b>{data['defense']}</b>\n"
        f"❤️ HP: <b>{data['hp']}</b>\n"
        f"💨 Speed: <b>{data['speed']}</b>\n\n"
        f"{image_text}\n\n"
        "✅ Card database ထဲ ထည့်ပြီးပါပြီ။",
        parse_mode="HTML",
    )


@router.message(Command("cards"))
async def cards_command(message: Message):

    async with SessionLocal() as session:

        result = await session.execute(
            select(Card)
            .order_by(Card.id.desc())
            .limit(20)
        )

        cards = result.scalars().all()

    if not cards:
        await message.answer(
            "📭 Card မရှိသေးပါ။"
        )
        return

    lines = [
        "🎴 <b>CARD DATABASE</b>",
        ""
    ]

    for card in cards:

        image = " 🖼️" if card.image_url else ""

        premium = (
            " 👑"
            if card.is_premium
            else ""
        )

        lines.append(
            f"🎴 <code>{card.id:04d}</code> "
            f"<b>{card.name}</b>"
            f"{premium}{image}"
        )

        lines.append(
            f"   💠 {card.rarity}"
        )

    await message.answer(
        "\n".join(lines),
        parse_mode="HTML",
    )


@router.message(Command("cardinfo"))
async def cardinfo_command(message: Message):

    parts = (
        message.text.split()
        if message.text
        else []
    )

    if len(parts) < 2:

        await message.answer(
            "🎴 Usage:\n"
            "/cardinfo 1"
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
            "❌ Card မတွေ့ပါ။"
        )

        return

    text = (
        "╔══════════════════════════╗\n"
        "          🎴 CARD\n"
        "╚══════════════════════════╝\n\n"
        f"🆔 ID: <code>{card.id:04d}</code>\n"
        f"🎴 Name: <b>{card.name}</b>\n"
        f"💠 Rarity: <b>{card.rarity}</b>\n\n"
        f"⚔️ ATK: <b>{card.attack}</b>\n"
        f"🛡 DEF: <b>{card.defense}</b>\n"
        f"❤️ HP: <b>{card.hp}</b>\n"
        f"💨 Speed: <b>{card.speed}</b>\n"
    )

    if card.description:

        text += (
            "\n📝 <b>Description</b>\n"
            f"{card.description}\n"
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
