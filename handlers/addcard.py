# Bot ထဲကနေ ပုံနဲ့ Card ထည့်ရန် `handlers/addcard.py`

```python
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy import select

from database import SessionLocal, Card, BotAdmin
from config import settings


router = Router()


# =========================================================
# ADMIN CHECK
# =========================================================

async def is_admin(telegram_id: int) -> bool:

    # Owner ID ရှိရင် Owner ကို အမြဲခွင့်ပြု
    owner_id = getattr(settings, "owner_id", None)

    if owner_id is not None:
        try:
            if int(owner_id) == telegram_id:
                return True
        except (ValueError, TypeError):
            pass

    # Database ထဲက BotAdmin ကို စစ်
    async with SessionLocal() as session:

        result = await session.execute(
            select(BotAdmin).where(
                BotAdmin.telegram_id == telegram_id,
                BotAdmin.active == True,
            )
        )

        admin = result.scalar_one_or_none()

        return admin is not None


# =========================================================
# ADD CARD
#
# ပုံ + Caption:
#
# /addcard 21 | Gojo Satoru | Legendary
#
# =========================================================

@router.message(Command("addcard"))
async def add_card_command(message: Message):

    if message.from_user is None:
        return

    # -----------------------------------------------------
    # ADMIN ONLY
    # -----------------------------------------------------

    if not await is_admin(message.from_user.id):
        await message.answer(
            "❌ ဒီ command ကို Admin ပဲ အသုံးပြုနိုင်ပါတယ်။"
        )
        return

    # -----------------------------------------------------
    # PHOTO CHECK
    # -----------------------------------------------------

    if not message.photo:

        await message.answer(
            "🎴 <b>Card ထည့်နည်း</b>\n\n"
            "Card ပုံကို ပို့ပြီး Caption မှာ ဒီလိုရေးပါ:\n\n"
            "<code>/addcard 21 | Gojo Satoru | Legendary</code>\n\n"
            "Format:\n"
            "<code>/addcard ID | NAME | RARITY</code>",
            parse_mode="HTML",
        )

        return

    # -----------------------------------------------------
    # CAPTION
    # -----------------------------------------------------

    caption = message.caption or ""

    if not caption.startswith("/addcard"):

        await message.answer(
            "❌ ပုံရဲ့ Caption မှာ ဒီလိုရေးပါ:\n\n"
            "<code>/addcard 21 | Gojo Satoru | Legendary</code>",
            parse_mode="HTML",
        )

        return

    # -----------------------------------------------------
    # REMOVE COMMAND
    # -----------------------------------------------------

    data = caption[len("/addcard"):].strip()

    parts = [x.strip() for x in data.split("|")]

    if len(parts) != 3:

        await message.answer(
            "❌ Format မှားနေပါတယ်။\n\n"
            "ဒီလိုရေးပါ:\n"
            "<code>/addcard 21 | Gojo Satoru | Legendary</code>",
            parse_mode="HTML",
        )

        return

    # -----------------------------------------------------
    # CARD ID
    # -----------------------------------------------------

    try:
        card_id = int(parts[0])

    except ValueError:

        await message.answer(
            "❌ Card ID က နံပါတ်ဖြစ်ရပါမယ်။\n\n"
            "ဥပမာ: <code>21</code>",
            parse_mode="HTML",
        )

        return

    if card_id <= 0:

        await message.answer(
            "❌ Card ID က 1 ထက်ကြီးရပါမယ်။"
        )

        return

    # -----------------------------------------------------
    # NAME
    # -----------------------------------------------------

    name = parts[1]

    if not name:

        await message.answer(
            "❌ Card Name မရှိပါဘူး။"
        )

        return

    # -----------------------------------------------------
    # RARITY
    # -----------------------------------------------------

    rarity = parts[2]

    if not rarity:

        await message.answer(
            "❌ Rarity မရှိပါဘူး။"
        )

        return

    # -----------------------------------------------------
    # TELEGRAM PHOTO
    # -----------------------------------------------------

    photo = message.photo[-1]

    # Telegram File ID ကိုသိမ်းမယ်
    image_url = photo.file_id

    # -----------------------------------------------------
    # DATABASE
    # -----------------------------------------------------

    async with SessionLocal() as session:

        # ID ရှိပြီးသားလား?
        result = await session.execute(
            select(Card).where(
                Card.id == card_id
            )
        )

        existing_card = result.scalar_one_or_none()

        if existing_card is not None:

            await message.answer(
                "❌ ဒီ Card ID ရှိပြီးသားပါ။\n\n"
                f"🆔 ID: <code>{card_id:04d}</code>\n"
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

            # Default Stats
            attack=10,
            defense=10,
            hp=100,
            speed=10,

            element=None,
            card_class=None,
            description=None,

            # Telegram Photo File ID
            image_url=image_url,

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
        "✅ <b>CARD ADDED SUCCESSFULLY!</b>\n\n"
        f"🆔 ID: <code>{card_id:04d}</code>\n"
        f"🎴 Name: <b>{name}</b>\n"
        f"💠 Rarity: <b>{rarity}</b>\n"
        "⚔️ ATK: <b>10</b>\n"
        "🛡 DEF: <b>10</b>\n"
        "❤️ HP: <b>100</b>\n"
        "💨 Speed: <b>10</b>\n\n"
        "🖼 Card image saved.\n"
        "🎉 ဒီ Card ကို /drop မှာ အသုံးပြုနိုင်ပါပြီ။",
        parse_mode="HTML",
    )
```
