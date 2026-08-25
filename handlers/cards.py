

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from sqlalchemy import select

from database import SessionLocal, Card

router = Router()

=========================================================

ADMIN

=========================================================

ADMIN_IDS = {
7974865879,
}

def is_admin(user_id: int) -> bool:
return user_id in ADMIN_IDS

=========================================================

TEMP CARD CREATION

=========================================================

card_creation = {}

=========================================================

/addcard

=========================================================

@router.message(Command("addcard"))
async def addcard_command(message: Message):

if message.from_user is None:
    return

if not is_admin(message.from_user.id):
    await message.answer(
        "❌ <b>Admin Only</b>\n\n"
        "ဒီ command ကို Admin ပဲ အသုံးပြုနိုင်ပါတယ်။",
        parse_mode="HTML",
    )
    return

card_creation[message.from_user.id] = {
    "step": "name"
}

await message.answer(
    "🎴 <b>ADD NEW CARD</b>\n\n"
    "Step 1/8\n\n"
    "📝 Card Name ကို ပို့ပါ။",
    parse_mode="HTML",
)

=========================================================

CANCEL

=========================================================

@router.message(Command("cancelcard"))
async def cancel_card(message: Message):

if message.from_user is None:
    return

if not is_admin(message.from_user.id):
    return

card_creation.pop(message.from_user.id, None)

await message.answer(
    "❌ Card creation cancelled."
)

=========================================================

CARD CREATION FLOW

=========================================================

@router.message(F.text)
async def card_creation_text(message: Message):

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

# -----------------------------------------------------
# NAME
# -----------------------------------------------------

if step == "name":

    data["name"] = text
    data["step"] = "rarity"

    await message.answer(
        "Step 2/8\n\n"
        "💠 Rarity ကို ပို့ပါ။\n\n"
        "ဥပမာ:\n"
        "<code>Common</code>\n"
        "<code>Rare</code>\n"
        "<code>Epic</code>\n"
        "<code>Legendary</code>\n"
        "<code>Mythic</code>\n"
        "<code>Premium Edition</code>",
        parse_mode="HTML",
    )
    return

# -----------------------------------------------------
# RARITY
# -----------------------------------------------------

if step == "rarity":

    data["rarity"] = text
    data["step"] = "attack"

    await message.answer(
        "Step 3/8\n\n"
        "⚔️ Attack ကို နံပါတ်နဲ့ ပို့ပါ။\n\n"
        "ဥပမာ: <code>100</code>",
        parse_mode="HTML",
    )
    return

# -----------------------------------------------------
# ATTACK
# -----------------------------------------------------

if step == "attack":

    try:
        attack = int(text)
    except ValueError:
        await message.answer(
            "❌ Attack က နံပါတ်ဖြစ်ရပါမယ်။\n"
            "ဥပမာ: <code>100</code>",
            parse_mode="HTML",
        )
        return

    data["attack"] = attack
    data["step"] = "defense"

    await message.answer(
        "Step 4/8\n\n"
        "🛡 Defense ကို ပို့ပါ။",
        parse_mode="HTML",
    )
    return

# -----------------------------------------------------
# DEFENSE
# -----------------------------------------------------

if step == "defense":

    try:
        defense = int(text)
    except ValueError:
        await message.answer(
            "❌ Defense က နံပါတ်ဖြစ်ရပါမယ်။"
        )
        return

    data["defense"] = defense
    data["step"] = "hp"

    await message.answer(
        "Step 5/8\n\n"
        "❤️ HP ကို ပို့ပါ။",
    )
    return

# -----------------------------------------------------
# HP
# -----------------------------------------------------

if step == "hp":

    try:
        hp = int(text)
    except ValueError:
        await message.answer(
            "❌ HP က နံပါတ်ဖြစ်ရပါမယ်။"
        )
        return

    data["hp"] = hp
    data["step"] = "speed"

    await message.answer(
        "Step 6/8\n\n"
        "💨 Speed ကို ပို့ပါ။",
    )
    return

# -----------------------------------------------------
# SPEED
# -----------------------------------------------------

if step == "speed":

    try:
        speed = int(text)
    except ValueError:
        await message.answer(
            "❌ Speed က နံပါတ်ဖြစ်ရပါမယ်။"
        )
        return

    data["speed"] = speed
    data["step"] = "description"

    await message.answer(
        "Step 7/8\n\n"
        "📝 Card Description ကို ပို့ပါ။\n\n"
        "မထည့်ချင်ရင် <code>-</code> ပို့ပါ။",
        parse_mode="HTML",
    )
    return

# -----------------------------------------------------
# DESCRIPTION
# -----------------------------------------------------

if step == "description":

    data["description"] = (
        None if text == "-" else text
    )

    data["step"] = "image"

    await message.answer(
        "Step 8/8\n\n"
        "🖼 <b>Card ပုံကို ပို့ပါ။</b>\n\n"
        "ပုံမထည့်ချင်ရင် <code>skip</code> လို့ပို့ပါ။",
        parse_mode="HTML",
    )
    return

=========================================================

CARD IMAGE

=========================================================

@router.message(F.photo)
async def card_image(message: Message):

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

# Telegram file_id
data["image_url"] = photo.file_id

await create_card(
    message,
    user_id,
    data,
)

=========================================================

SKIP IMAGE

=========================================================

@router.message(F.text.casefold() == "skip")
async def skip_image(message: Message):

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

data["image_url"] = None

await create_card(
    message,
    user_id,
    data,
)

=========================================================

CREATE CARD

=========================================================

async def create_card(
message: Message,
user_id: int,
data: dict,
):

async with SessionLocal() as session:

    card = Card(
        name=data["name"],
        rarity=data["rarity"],
        attack=data["attack"],
        defense=data["defense"],
        hp=data["hp"],
        speed=data["speed"],
        description=data.get("description"),
        image_url=data.get("image_url"),
        element=None,
        card_class=None,
        base_price=100,
        is_limited=False,
        is_shiny=False,
        is_animated=False,
        is_premium=(
            data["rarity"].lower()
            == "premium edition"
        ),
    )

    session.add(card)

    await session.commit()
    await session.refresh(card)

    card_id = card.id

card_creation.pop(user_id, None)

image_status = (
    "🖼 Image: <b>Added</b>"
    if data.get("image_url")
    else "🖼 Image: <b>None</b>"
)

await message.answer(
    "╔══════════════════════════╗\n"
    "      🎴 <b>CARD CREATED!</b>\n"
    "╚══════════════════════════╝\n\n"
    f"🆔 ID: <code>{card_id:04d}</code>\n"
    f"🎴 Name: <b>{data['name']}</b>\n"
    f"💠 Rarity: <b>{data['rarity']}</b>\n\n"
    f"⚔️ ATK: <b>{data['attack']}</b>\n"
    f"🛡 DEF: <b>{data['defense']}</b>\n"
    f"❤️ HP: <b>{data['hp']}</b>\n"
    f"💨 Speed: <b>{data['speed']}</b>\n\n"
    f"{image_status}\n\n"
    "✅ Database ထဲမှာ Card ထည့်ပြီးပါပြီ။",
    parse_mode="HTML",
)

=========================================================

/cards

=========================================================

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
        "📭 Card database ထဲမှာ Card မရှိသေးပါ။"
    )
    return

lines = [
    "🎴 <b>CARD DATABASE</b>",
    "",
]

for card in cards:

    premium = (
        " 👑"
        if card.is_premium
        else ""
    )

    image = (
        " 🖼"
        if card.image_url
        else ""
    )

    lines.append(
        f"🎴 <code>{card.id:04d}</code> "
        f"<b>{card.name}</b>{premium}{image}"
    )

    lines.append(
        f"   💠 {card.rarity}"
    )

await message.answer(
    "\n".join(lines),
    parse_mode="HTML",
)

=========================================================

/check

=========================================================

@router.message(Command("cardinfo"))
async def cardinfo_command(message: Message):

parts = message.text.split() if message.text else []

if len(parts) < 2:
    await message.answer(
        "🎴 Usage:\n"
        "<code>/cardinfo 1</code>",
        parse_mode="HTML",
    )
    return

try:
    card_id = int(parts[1])
except ValueError:
    await message.answer(
        "❌ Invalid card ID."
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

premium = (
    " 👑 Premium"
    if card.is_premium
    else ""
)

text = (
    "╔══════════════════════════╗\n"
    "        🎴 <b>CARD</b>\n"
    "╚══════════════════════════╝\n\n"
    f"🆔 ID: <code>{card.id:04d}</code>\n"
    f"🎴 Name: <b>{card.name}</b>\n"
    f"💠 Rarity: <b>{card.rarity}</b>{premium}\n\n"
    f"⚔️ ATK: <b>{card.attack}</b>\n"
    f"🛡 DEF: <b>{card.defense}</b>\n"
    f"❤️ HP: <b>{card.hp}</b>\n"
    f"💨 Speed: <b>{card.speed}</b>\n"
)

if card.description:
    text += (
        f"\n📝 <b>Description</b>\n"
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
