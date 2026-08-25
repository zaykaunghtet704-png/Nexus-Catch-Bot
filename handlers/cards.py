from __future__ import annotations

import random
from datetime import datetime
from typing import Optional

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from aiogram.exceptions import TelegramBadRequest
from sqlalchemy import select, func

from database import (
    SessionLocal,
    User,
    UserCard,
    Card,
    Group,
    CardDrop,
    CatchLog,
)


router = Router()


# =========================================================
# CONFIG
# =========================================================

OWNER_ID = 7974865879

# Group message thresholds
NORMAL_DROP_MESSAGES = 85
RARE_DROP_MESSAGES = 1000

PAGE_SIZE = 5


# =========================================================
# IN-MEMORY GROUP MESSAGE COUNTER
# =========================================================
#
# 85 messages -> normal/good card
# 1000 messages -> better card
#
# NOTE:
# This counter resets if Render restarts the service.
# The card collection itself is stored permanently in DB.
#

group_message_counts: dict[int, int] = {}


# =========================================================
# RARITY SETTINGS
# =========================================================

RARITY_ORDER = [
    "Common",
    "Uncommon",
    "Rare",
    "Epic",
    "Legendary",
    "Mythic",
    "Premium Edition",
]


RARITY_WEIGHTS_NORMAL = {
    "Common": 55,
    "Uncommon": 25,
    "Rare": 12,
    "Epic": 6,
    "Legendary": 1.8,
    "Mythic": 0.2,
}


RARITY_WEIGHTS_RARE = {
    "Uncommon": 25,
    "Rare": 30,
    "Epic": 25,
    "Legendary": 15,
    "Mythic": 4,
    "Premium Edition": 1,
}


# =========================================================
# HELPERS
# =========================================================

def is_owner(user_id: int) -> bool:
    return user_id == OWNER_ID


def safe_html(text: Optional[str]) -> str:
    if not text:
        return "Unknown"

    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def drop_keyboard(drop_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🎴 GET CARD",
                    callback_data=f"carddrop:{drop_id}",
                )
            ]
        ]
    )


def harem_keyboard(
    page: int,
    total_pages: int,
) -> InlineKeyboardMarkup:

    buttons = []

    if page > 1:
        buttons.append(
            InlineKeyboardButton(
                text="◀️ Previous",
                callback_data=f"harem:{page - 1}",
            )
        )

    buttons.append(
        InlineKeyboardButton(
            text=f"📖 {page}/{total_pages}",
            callback_data="harem:current",
        )
    )

    if page < total_pages:
        buttons.append(
            InlineKeyboardButton(
                text="Next ▶️",
                callback_data=f"harem:{page + 1}",
            )
        )

    return InlineKeyboardMarkup(
        inline_keyboard=[
            buttons,
            [
                InlineKeyboardButton(
                    text="🔄 Refresh",
                    callback_data=f"harem:{page}",
                )
            ],
        ]
    )


def rarity_weight_table(rare: bool = False):
    if rare:
        return RARITY_WEIGHTS_RARE

    return RARITY_WEIGHTS_NORMAL


# =========================================================
# GET / CREATE USER
# =========================================================

async def get_or_create_user(
    telegram_id: int,
    username: Optional[str] = None,
    first_name: Optional[str] = None,
):
    async with SessionLocal() as session:

        result = await session.execute(
            select(User).where(
                User.telegram_id == telegram_id
            )
        )

        user = result.scalar_one_or_none()

        if user is None:

            user = User(
                telegram_id=telegram_id,
                username=username,
                first_name=first_name or "Player",
            )

            session.add(user)

            await session.commit()
            await session.refresh(user)

        else:

            changed = False

            if username is not None and user.username != username:
                user.username = username
                changed = True

            if first_name is not None and user.first_name != first_name:
                user.first_name = first_name
                changed = True

            if changed:
                await session.commit()

        return user


# =========================================================
# GET GROUP
# =========================================================

async def get_or_create_group(
    telegram_group_id: int,
    title: str = "Telegram Group",
    username: Optional[str] = None,
):
    async with SessionLocal() as session:

        result = await session.execute(
            select(Group).where(
                Group.telegram_id == telegram_group_id
            )
        )

        group = result.scalar_one_or_none()

        if group is None:

            group = Group(
                telegram_id=telegram_group_id,
                title=title,
                username=username,
                enabled=True,
                drop_enabled=True,
            )

            session.add(group)

            await session.commit()
            await session.refresh(group)

        else:

            changed = False

            if title and group.title != title:
                group.title = title
                changed = True

            if username != group.username:
                group.username = username
                changed = True

            if not group.enabled:
                group.enabled = True
                changed = True

            if changed:
                await session.commit()

        return group


# =========================================================
# SELECT RANDOM CARD
# =========================================================

async def get_random_card(
    rare: bool = False,
):
    async with SessionLocal() as session:

        result = await session.execute(
            select(Card).where(
                Card.rarity.in_(
                    list(
                        rarity_weight_table(
                            rare
                        ).keys()
                    )
                )
            )
        )

        cards = result.scalars().all()

        if not cards:
            return None

        weights = rarity_weight_table(rare)

        weighted_cards = []
        weighted_values = []

        for card in cards:

            weighted_cards.append(card)
            weighted_values.append(
                weights.get(card.rarity, 0.1)
            )

        return random.choices(
            weighted_cards,
            weights=weighted_values,
            k=1,
        )[0]


# =========================================================
# ADD CARD TO USER
# =========================================================

async def give_card_to_user(
    telegram_id: int,
    card_id: int,
):
    async with SessionLocal() as session:

        user_result = await session.execute(
            select(User).where(
                User.telegram_id == telegram_id
            )
        )

        user = user_result.scalar_one_or_none()

        if user is None:

            user = User(
                telegram_id=telegram_id,
                first_name="Player",
            )

            session.add(user)
            await session.flush()

        card_result = await session.execute(
            select(Card).where(
                Card.id == card_id
            )
        )

        card = card_result.scalar_one_or_none()

        if card is None:
            return None, False

        user_card_result = await session.execute(
            select(UserCard).where(
                UserCard.user_id == user.id,
                UserCard.card_id == card.id,
            )
        )

        user_card = user_card_result.scalar_one_or_none()

        duplicate = user_card is not None

        if user_card is None:

            user_card = UserCard(
                user_id=user.id,
                card_id=card.id,
                level=1,
                xp=0,
                quantity=1,
                is_favorite=False,
                is_locked=False,
            )

            session.add(user_card)

        else:

            user_card.quantity += 1

        await session.commit()

        return card, duplicate


# =========================================================
# CARD TEXT
# =========================================================

def card_drop_text(
    card: Card,
    count: Optional[int] = None,
    rare: bool = False,
) -> str:

    rarity = safe_html(card.rarity)
    name = safe_html(card.name)

    if count is None:
        count_line = ""
    else:
        count_line = (
            f"\n💬 Messages: <b>{count:,}</b>"
        )

    if rare:
        title = "💎 <b>RARE CARD DROP!</b>"
    else:
        title = "🎴 <b>CARD DROP!</b>"

    premium = ""

    if card.is_premium:
        premium = "\n👑 <b>PREMIUM EDITION</b>"

    shiny = ""

    if card.is_shiny:
        shiny = " ✨ SHINY"

    animated = ""

    if card.is_animated:
        animated = " 🎞️ ANIMATED"

    return (
        f"{title}\n\n"
        f"🎴 <b>#{card.id:04d}</b>\n"
        f"✨ <b>{name}</b>\n"
        f"💠 Rarity: <b>{rarity}</b>"
        f"{shiny}{animated}"
        f"{premium}\n"
        f"⚔️ ATK: <b>{card.attack}</b>\n"
        f"🛡 DEF: <b>{card.defense}</b>\n"
        f"❤️ HP: <b>{card.hp}</b>\n"
        f"💨 Speed: <b>{card.speed}</b>"
        f"{count_line}\n\n"
        "⚡ <b>First person to press GET CARD wins!</b>"
    )


# =========================================================
# SEND CARD DROP
# =========================================================

async def send_card_drop(
    message: Message,
    card: Card,
    group_id: int,
    rare: bool = False,
    count: Optional[int] = None,
):
    async with SessionLocal() as session:

        drop = CardDrop(
            group_id=group_id,
            card_id=card.id,
            message_id=0,
            active=True,
            caught_by=None,
            caught_at=None,
        )

        session.add(drop)

        await session.commit()
        await session.refresh(drop)

        text = card_drop_text(
            card,
            count=count,
            rare=rare,
        )

        keyboard = drop_keyboard(drop.id)

        try:

            if card.image_url:

                sent = await message.answer_photo(
                    photo=card.image_url,
                    caption=text,
                    parse_mode="HTML",
                    reply_markup=keyboard,
                )

            else:

                sent = await message.answer(
                    text,
                    parse_mode="HTML",
                    reply_markup=keyboard,
                )

            drop.message_id = sent.message_id

            await session.commit()

        except Exception:

            drop.active = False

            await session.commit()

            raise

        return drop


# =========================================================
# /addcard
#
# Text:
# /addcard Name | Rarity | ATK | DEF | HP | SPEED | ELEMENT | CLASS | PRICE | IMAGE_URL
#
# Or send:
# /addcard Name | Rarity | ATK | DEF | HP | SPEED | ELEMENT | CLASS | PRICE
# as a reply to a Telegram photo.
# =========================================================

@router.message(Command("addcard"))
async def addcard_command(message: Message):

    if message.from_user is None:
        return

    if not is_owner(message.from_user.id):

        await message.answer(
            "❌ <b>Owner Only</b>\n\n"
            "ဒီ command ကို bot owner ပဲ သုံးနိုင်ပါတယ်။",
            parse_mode="HTML",
        )

        return

    text = message.text or ""

    raw = text.partition(" ")[2].strip()

    if not raw:

        await message.answer(
            "➕ <b>ADD CARD</b>\n\n"
            "Format:\n\n"
            "<code>/addcard Name | Rarity | ATK | DEF | HP | SPEED | ELEMENT | CLASS | PRICE | IMAGE_URL</code>\n\n"
            "ဥပမာ:\n"
            "<code>/addcard Naruto | Legendary | 95 | 90 | 100 | 88 | Fire | Ninja | 50000 | https://example.com/naruto.jpg</code>\n\n"
            "🖼️ Photo နဲ့ထည့်ချင်ရင် photo ကို reply လုပ်ပြီး "
            "IMAGE_URL မထည့်လည်းရပါတယ်။",
            parse_mode="HTML",
        )

        return

    parts = [
        x.strip()
        for x in raw.split("|")
    ]

    if len(parts) < 9:

        await message.answer(
            "❌ Format မပြည့်စုံပါဘူး။\n\n"
            "လိုအပ်တာ:\n"
            "Name | Rarity | ATK | DEF | HP | SPEED | ELEMENT | CLASS | PRICE | IMAGE_URL",
        )

        return

    name = parts[0]
    rarity = parts[1]

    try:
        attack = int(parts[2])
        defense = int(parts[3])
        hp = int(parts[4])
        speed = int(parts[5])
        base_price = int(parts[8])
    except ValueError:

        await message.answer(
            "❌ ATK / DEF / HP / SPEED / PRICE တွေက number ဖြစ်ရပါမယ်။"
        )

        return

    element = parts[6] or None
    card_class = parts[7] or None

    image_url = None

    if len(parts) >= 10 and parts[9]:
        image_url = parts[9]

    # If command is a reply to photo
    if (
        image_url is None
        and message.reply_to_message is not None
        and message.reply_to_message.photo
    ):

        image_url = (
            message.reply_to_message
            .photo[-1]
            .file_id
        )

    async with SessionLocal() as session:

        card = Card(
            name=name,
            rarity=rarity,
            attack=attack,
            defense=defense,
            hp=hp,
            speed=speed,
            element=element,
            card_class=card_class,
            description=None,
            image_url=image_url,
            base_price=base_price,
            is_limited=False,
            is_shiny=False,
            is_animated=False,
            is_premium=(
                rarity.lower()
                == "premium edition".lower()
            ),
        )

        session.add(card)

        await session.commit()
        await session.refresh(card)

        await message.answer(
            "✅ <b>CARD ADDED!</b>\n\n"
            f"🆔 ID: <code>{card.id:04d}</code>\n"
            f"🎴 Name: <b>{safe_html(card.name)}</b>\n"
            f"💠 Rarity: <b>{safe_html(card.rarity)}</b>\n"
            f"⚔️ ATK: <b>{card.attack}</b>\n"
            f"🛡 DEF: <b>{card.defense}</b>\n"
            f"❤️ HP: <b>{card.hp}</b>\n"
            f"💨 Speed: <b>{card.speed}</b>\n"
            f"🖼️ Image: "
            f"<b>{'YES' if card.image_url else 'NO'}</b>",
            parse_mode="HTML",
        )


# =========================================================
# /drop
#
# Owner only.
#
# /drop
# -> random normal/good card
#
# /drop 0021
# -> specific card
#
# /drop premium
# -> random Premium Edition
#
# /drop 0021 @username
# -> card is directly assigned to mentioned user
#
# =========================================================

@router.message(Command("drop"))
async def drop_command(message: Message):

    if message.from_user is None:
        return

    if not is_owner(message.from_user.id):

        await message.answer(
            "❌ <b>Owner Only</b>\n\n"
            "Card drop ကို owner ပဲလုပ်နိုင်ပါတယ်။",
            parse_mode="HTML",
        )

        return

    if message.chat.type not in (
        "group",
        "supergroup",
    ):

        await message.answer(
            "❌ /drop ကို group ထဲမှာပဲ သုံးပါ။"
        )

        return

    parts = (
        message.text.split()
        if message.text
        else []
    )

    card = None

    if len(parts) >= 2:

        value = parts[1].strip()

        if value.lower() == "premium":

            async with SessionLocal() as session:

                result = await session.execute(
                    select(Card).where(
                        Card.rarity
                        == "Premium Edition"
                    )
                )

                cards = result.scalars().all()

                if cards:
                    card = random.choice(cards)

        else:

            try:
                card_id = int(value)
            except ValueError:
                card_id = 0

            if card_id:

                async with SessionLocal() as session:

                    result = await session.execute(
                        select(Card).where(
                            Card.id == card_id
                        )
                    )

                    card = result.scalar_one_or_none()

    else:

        card = await get_random_card(
            rare=False
        )

    if card is None:

        await message.answer(
            "❌ Drop လုပ်ဖို့ card မရှိသေးပါဘူး။\n\n"
            "အရင်ဆုံး /addcard နဲ့ card ထည့်ပါ။"
        )

        return

    group = await get_or_create_group(
        telegram_group_id=message.chat.id,
        title=message.chat.title or "Telegram Group",
        username=message.chat.username,
    )

    await send_card_drop(
        message=message,
        card=card,
        group_id=group.id,
        rare=(
            card.rarity in (
                "Legendary",
                "Mythic",
                "Premium Edition",
            )
        ),
    )


# =========================================================
# CARD DROP BUTTON
#
# FIRST CLICK WINS
# =========================================================

@router.callback_query(
    F.data.startswith("carddrop:")
)
async def carddrop_callback(
    callback: CallbackQuery,
):

    if callback.message is None:
        await callback.answer()
        return

    try:

        drop_id = int(
            callback.data.split(":")[1]
        )

    except (
        ValueError,
        IndexError,
    ):

        await callback.answer(
            "❌ Invalid drop.",
            show_alert=True,
        )

        return

    telegram_id = callback.from_user.id

    async with SessionLocal() as session:

        # Lock the drop row where supported.
        result = await session.execute(
            select(CardDrop)
            .where(
                CardDrop.id == drop_id
            )
            .with_for_update()
        )

        drop = result.scalar_one_or_none()

        if drop is None:

            await callback.answer(
                "❌ Card drop မတွေ့ပါဘူး။",
                show_alert=True,
            )

            return

        if not drop.active:

            await callback.answer(
                "😢 ဒီ card ကို တစ်ယောက်ယောက် ရပြီးပါပြီ။",
                show_alert=True,
            )

            return

        user_result = await session.execute(
            select(User).where(
                User.telegram_id == telegram_id
            )
        )

        user = user_result.scalar_one_or_none()

        if user is None:

            user = User(
                telegram_id=telegram_id,
                username=callback.from_user.username,
                first_name=(
                    callback.from_user.first_name
                    or "Player"
                ),
            )

            session.add(user)

            await session.flush()

        card_result = await session.execute(
            select(Card).where(
                Card.id == drop.card_id
            )
        )

        card = card_result.scalar_one_or_none()

        if card is None:

            drop.active = False

            await session.commit()

            await callback.answer(
                "❌ Card မတွေ့ပါဘူး။",
                show_alert=True,
            )

            return

        # ---------------------------------------------
        # GIVE CARD
        # ---------------------------------------------

        user_card_result = await session.execute(
            select(UserCard).where(
                UserCard.user_id == user.id,
                UserCard.card_id == card.id,
            )
        )

        user_card = (
            user_card_result.scalar_one_or_none()
        )

        duplicate = False

        if user_card is None:

            user_card = UserCard(
                user_id=user.id,
                card_id=card.id,
                level=1,
                xp=0,
                quantity=1,
                is_favorite=False,
                is_locked=False,
            )

            session.add(user_card)

        else:

            user_card.quantity += 1
            duplicate = True

        # ---------------------------------------------
        # MARK DROP AS CAUGHT
        # ---------------------------------------------

        drop.active = False
        drop.caught_by = user.id
        drop.caught_at = datetime.utcnow()

        catch_log = CatchLog(
            user_id=user.id,
            group_id=drop.group_id,
            card_id=card.id,
            rarity=card.rarity,
            is_duplicate=duplicate,
        )

        session.add(catch_log)

        await session.commit()

        # ---------------------------------------------
        # SUCCESS MESSAGE
        # ---------------------------------------------

        await callback.answer(
            "🎉 You got the card!",
            show_alert=False,
        )

        text = (
            "╔══════════════════════════╗\n"
            "       🎉 <b>CARD CLAIMED!</b>\n"
            "╚══════════════════════════╝\n\n"
            f"👤 <b>{safe_html(user.first_name)}</b>\n"
            f"🎴 <b>#{card.id:04d}</b>\n"
            f"✨ <b>{safe_html(card.name)}</b>\n"
            f"💠 Rarity: <b>{safe_html(card.rarity)}</b>\n\n"
        )

        if duplicate:

            text += (
                "♻️ <b>DUPLICATE!</b>\n"
                "ဒီ card ကို collection ထဲမှာရှိပြီးသားမို့ "
                "quantity +1 ဖြစ်သွားပါတယ်။\n"
            )

        else:

            text += (
                "🆕 <b>NEW CARD!</b>\n"
                "သင့် collection ထဲ ထည့်ပြီးပါပြီ။\n"
            )

        try:

            await callback.message.edit_caption(
                caption=text,
                parse_mode="HTML",
            )

        except TelegramBadRequest:

            try:

                await callback.message.edit_text(
                    text,
                    parse_mode="HTML",
                )

            except TelegramBadRequest:
                pass


# =========================================================
# AUTO DROP MESSAGE COUNTER
#
# IMPORTANT:
# This handler must be registered in cards.py.
#
# Every group message increments counter.
#
# 85 -> drop
# 170 -> drop
# ...
#
# 1000 -> better card
#
# =========================================================

@router.message(
    F.chat.type.in_(
        {
            "group",
            "supergroup",
        }
    )
)
async def group_message_counter(
    message: Message,
):

    # Commands should not count.
    if message.text and message.text.startswith("/"):
        return

    if message.from_user is None:
        return

    group_id = message.chat.id

    current = group_message_counts.get(
        group_id,
        0,
    )

    current += 1

    group_message_counts[group_id] = current

    # ---------------------------------------------
    # 1000 MESSAGE SPECIAL DROP
    # ---------------------------------------------

    if current >= RARE_DROP_MESSAGES:

        group_message_counts[group_id] = 0

        async with SessionLocal() as session:

            group_result = await session.execute(
                select(Group).where(
                    Group.telegram_id == group_id
                )
            )

            group = (
                group_result.scalar_one_or_none()
            )

            if group is None:

                group = Group(
                    telegram_id=group_id,
                    title=(
                        message.chat.title
                        or "Telegram Group"
                    ),
                    username=message.chat.username,
                    enabled=True,
                    drop_enabled=True,
                )

                session.add(group)

                await session.commit()
                await session.refresh(group)

        card = await get_random_card(
            rare=True
        )

        if card is not None:

            await send_card_drop(
                message=message,
                card=card,
                group_id=group.id,
                rare=True,
                count=current,
            )

        return

    # ---------------------------------------------
    # NORMAL 85 MESSAGE DROP
    # ---------------------------------------------

    if current >= NORMAL_DROP_MESSAGES:

        group_message_counts[group_id] = 0

        async with SessionLocal() as session:

            group_result = await session.execute(
                select(Group).where(
                    Group.telegram_id == group_id
                )
            )

            group = (
                group_result.scalar_one_or_none()
            )

            if group is None:

                group = Group(
                    telegram_id=group_id,
                    title=(
                        message.chat.title
                        or "Telegram Group"
                    ),
                    username=message.chat.username,
                    enabled=True,
                    drop_enabled=True,
                )

                session.add(group)

                await session.commit()
                await session.refresh(group)

            if not group.drop_enabled:
                return

        card = await get_random_card(
            rare=False
        )

        if card is not None:

            await send_card_drop(
                message=message,
                card=card,
                group_id=group.id,
                rare=False,
                count=current,
            )


# =========================================================
# /harem
# =========================================================

@router.message(Command("harem"))
async def harem_command(
    message: Message,
):

    if message.from_user is None:
        return

    await show_harem(
        message,
        message.from_user.id,
        1,
    )


# =========================================================
# SHOW HAREM
# =========================================================

async def show_harem(
    message: Message,
    telegram_id: int,
    page: int,
):

    async with SessionLocal() as session:

        user_result = await session.execute(
            select(User).where(
                User.telegram_id == telegram_id
            )
        )

        user = user_result.scalar_one_or_none()

        if user is None:

            await message.answer(
                "❌ Please use /start first."
            )

            return

        count_result = await session.execute(
            select(
                func.count(UserCard.id)
            ).where(
                UserCard.user_id == user.id
            )
        )

        total = count_result.scalar() or 0

        if total == 0:

            await message.answer(
                "🎴 <b>YOUR HAREM</b>\n\n"
                "📭 You don't have any cards yet.\n\n"
                "✨ Wait for a card drop!",
                parse_mode="HTML",
            )

            return

        total_pages = max(
            1,
            (total + PAGE_SIZE - 1)
            // PAGE_SIZE,
        )

        page = max(
            1,
            min(page, total_pages),
        )

        offset = (
            page - 1
        ) * PAGE_SIZE

        result = await session.execute(
            select(UserCard, Card)
            .join(
                Card,
                UserCard.card_id
                == Card.id,
            )
            .where(
                UserCard.user_id
                == user.id
            )
            .order_by(
                Card.id.asc()
            )
            .offset(offset)
            .limit(PAGE_SIZE)
        )

        rows = result.all()

        lines = [
            "╔══════════════════════════╗",
            "        🎴 <b>HAREM</b>",
            "╚══════════════════════════╝",
            "",
            f"👤 <b>{safe_html(user.first_name)}</b>",
            f"🃏 Cards: <b>{total}</b>",
            "",
        ]

        for user_card, card in rows:

            favorite = (
                " ❤️"
                if user_card.is_favorite
                else ""
            )

            locked = (
                " 🔒"
                if user_card.is_locked
                else ""
            )

            lines.append(
                f"🎴 <b>#{card.id:04d}</b> — "
                f"<b>{safe_html(card.name)}</b>"
            )

            lines.append(
                f"   ✦ {safe_html(card.rarity)}"
                f" • Lv.{user_card.level}"
                f" • ×{user_card.quantity}"
                f"{favorite}{locked}"
            )

            lines.append("")

        lines.append(
            "━━━━━━━━━━━━━━━━━━━━"
        )

        lines.append(
            f"📖 Page <b>{page}</b>/"
            f"<b>{total_pages}</b>"
        )

        await message.answer(
            "\n".join(lines),
            parse_mode="HTML",
            reply_markup=harem_keyboard(
                page,
                total_pages,
            ),
        )


# =========================================================
# HAREM PAGINATION
# =========================================================

@router.callback_query(
    F.data.startswith("harem:")
)
async def harem_callback(
    callback: CallbackQuery,
):

    if callback.message is None:
        await callback.answer()
        return

    data = callback.data

    if data == "harem:current":

        await callback.answer()
        return

    try:

        page = int(
            data.split(":")[1]
        )

    except (
        ValueError,
        IndexError,
    ):

        page = 1

    telegram_id = callback.from_user.id

    async with SessionLocal() as session:

        user_result = await session.execute(
            select(User).where(
                User.telegram_id == telegram_id
            )
        )

        user = user_result.scalar_one_or_none()

        if user is None:

            await callback.answer(
                "❌ Please use /start first.",
                show_alert=True,
            )

            return

        count_result = await session.execute(
            select(
                func.count(UserCard.id)
            ).where(
                UserCard.user_id == user.id
            )
        )

        total = count_result.scalar() or 0

        if total == 0:

            try:

                await callback.message.edit_text(
                    "🎴 <b>YOUR HAREM</b>\n\n"
                    "📭 Your collection is empty.",
                    parse_mode="HTML",
                )

            except TelegramBadRequest:
                pass

            await callback.answer()
            return

        total_pages = max(
            1,
            (total + PAGE_SIZE - 1)
            // PAGE_SIZE,
        )

        page = max(
            1,
            min(page, total_pages),
        )

        offset = (
            page - 1
        ) * PAGE_SIZE

        result = await session.execute(
            select(UserCard, Card)
            .join(
                Card,
                UserCard.card_id
                == Card.id,
            )
            .where(
                UserCard.user_id
                == user.id
            )
            .order_by(
                Card.id.asc()
            )
            .offset(offset)
            .limit(PAGE_SIZE)
        )

        rows = result.all()

        lines = [
            "╔══════════════════════════╗",
            "        🎴 <b>HAREM</b>",
            "╚══════════════════════════╝",
            "",
            f"👤 <b>{safe_html(user.first_name)}</b>",
            f"🃏 Cards: <b>{total}</b>",
            "",
        ]

        for user_card, card in rows:

            favorite = (
                " ❤️"
                if user_card.is_favorite
                else ""
            )

            locked = (
                " 🔒"
                if user_card.is_locked
                else ""
            )

            lines.append(
                f"🎴 <b>#{card.id:04d}</b> — "
                f"<b>{safe_html(card.name)}</b>"
            )

            lines.append(
                f"   ✦ {safe_html(card.rarity)}"
                f" • Lv.{user_card.level}"
                f" • ×{user_card.quantity}"
                f"{favorite}{locked}"
            )

            lines.append("")

        lines.append(
            "━━━━━━━━━━━━━━━━━━━━"
        )

        lines.append(
            f"📖 Page <b>{page}</b>/"
            f"<b>{total_pages}</b>"
        )

        new_text = "\n".join(lines)

        try:

            await callback.message.edit_text(
                new_text,
                parse_mode="HTML",
                reply_markup=harem_keyboard(
                    page,
                    total_pages,
                ),
            )

        except TelegramBadRequest as e:

            # Fix:
            # TelegramBadRequest:
            # message is not modified
            if "message is not modified" not in str(e):
                raise

    await callback.answer()


# =========================================================
# /check
# =========================================================

@router.message(Command("check"))
async def check_command(
    message: Message,
):

    parts = (
        message.text.split()
        if message.text
        else []
    )

    if len(parts) < 2:

        await message.answer(
            "🎴 <b>Card Check</b>\n\n"
            "Usage:\n"
            "<code>/check 0021</code>",
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
                "❌ Card not found."
            )

            return

        text = (
            "╔══════════════════════════╗\n"
            "        🎴 <b>CARD</b>\n"
            "╚══════════════════════════╝\n\n"
            f"🆔 ID: <code>{card.id:04d}</code>\n"
            f"✨ Name: <b>{safe_html(card.name)}</b>\n"
            f"💠 Rarity: <b>{safe_html(card.rarity)}</b>\n\n"
            f"⚔️ ATK: <b>{card.attack}</b>\n"
            f"🛡 DEF: <b>{card.defense}</b>\n"
            f"❤️ HP: <b>{card.hp}</b>\n"
            f"💨 Speed: <b>{card.speed}</b>\n\n"
            f"🌟 Element: <b>{safe_html(card.element)}</b>\n"
            f"🎭 Class: <b>{safe_html(card.card_class)}</b>\n"
            f"💰 Base Price: <b>{card.base_price:,}</b> Coins\n"
        )

        if card.is_premium:

            text += (
                "\n👑 <b>PREMIUM EDITION</b>\n"
            )

        if card.is_shiny:

            text += (
                "✨ <b>SHINY</b>\n"
            )

        if card.is_animated:

            text += (
                "🎞️ <b>ANIMATED</b>\n"
            )

        if card.description:

            text += (
                f"\n📝 <b>Description</b>\n"
                f"{safe_html(card.description)}\n"
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
# /fav
# =========================================================

@router.message(Command("fav"))
async def fav_command(
    message: Message,
):

    if message.from_user is None:
        return

    parts = (
        message.text.split()
        if message.text
        else []
    )

    if len(parts) < 2:

        await message.answer(
            "❤️ Usage: <code>/fav 0021</code>",
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

        user_result = await session.execute(
            select(User).where(
                User.telegram_id
                == message.from_user.id
            )
        )

        user = user_result.scalar_one_or_none()

        if user is None:

            await message.answer(
                "❌ Please use /start first."
            )

            return

        result = await session.execute(
            select(UserCard).where(
                UserCard.user_id == user.id,
                UserCard.card_id == card_id,
            )
        )

        user_card = result.scalar_one_or_none()

        if user_card is None:

            await message.answer(
                "❌ You don't own this card."
            )

            return

        user_card.is_favorite = True

        await session.commit()

        await message.answer(
            f"❤️ Card <code>{card_id:04d}</code> "
            "has been added to your favorites!",
            parse_mode="HTML",
        )


# =========================================================
# /unfav
# =========================================================

@router.message(Command("unfav"))
async def unfav_command(
    message: Message,
):

    if message.from_user is None:
        return

    parts = (
        message.text.split()
        if message.text
        else []
    )

    if len(parts) < 2:

        await message.answer(
            "Usage: <code>/unfav 0021</code>",
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

        user_result = await session.execute(
            select(User).where(
                User.telegram_id
                == message.from_user.id
            )
        )

        user = user_result.scalar_one_or_none()

        if user is None:

            await message.answer(
                "❌ Please use /start first."
            )

            return

        result = await session.execute(
            select(UserCard).where(
                UserCard.user_id == user.id,
                UserCard.card_id == card_id,
            )
        )

        user_card = result.scalar_one_or_none()

        if user_card is None:

            await message.answer(
                "❌ You don't own this card."
            )

            return

        user_card.is_favorite = False

        await session.commit()

        await message.answer(
            f"💔 Card <code>{card_id:04d}</code> "
            "removed from favorites.",
            parse_mode="HTML",
        )


# =========================================================
# /upgrade
# =========================================================

@router.message(Command("upgrade"))
async def upgrade_command(
    message: Message,
):

    if message.from_user is None:
        return

    parts = (
        message.text.split()
        if message.text
        else []
    )

    if len(parts) < 2:

        await message.answer(
            "⬆️ <b>Card Upgrade</b>\n\n"
            "Usage:\n"
            "<code>/upgrade 0021</code>",
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

        user_result = await session.execute(
            select(User).where(
                User.telegram_id
                == message.from_user.id
            )
        )

        user = user_result.scalar_one_or_none()

        if user is None:

            await message.answer(
                "❌ Please use /start first."
            )

            return

        result = await session.execute(
            select(UserCard).where(
                UserCard.user_id == user.id,
                UserCard.card_id == card_id,
            )
        )

        user_card = result.scalar_one_or_none()

        if user_card is None:

            await message.answer(
                "❌ You don't own this card."
            )

            return

        cost = user_card.level * 500

        if user.coins < cost:

            await message.answer(
                "❌ Not enough Coins.\n\n"
                f"💰 Required: <b>{cost:,}</b>\n"
                f"🪙 Your Coins: <b>{user.coins:,}</b>",
                parse_mode="HTML",
            )

            return

        user.coins -= cost
        user_card.level += 1
        user_card.xp = 0

        await session.commit()

        await message.answer(
            "⬆️ <b>CARD UPGRADED!</b>\n\n"
            f"🎴 Card: <code>{card_id:04d}</code>\n"
            f"⭐ New Level: <b>{user_card.level}</b>\n"
            f"💰 Cost: <b>{cost:,}</b> Coins",
            parse_mode="HTML",
        )


# =========================================================
# /hmode
# =========================================================

@router.message(Command("hmode"))
async def hmode_command(
    message: Message,
):

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="⭐ Highest Level",
                    callback_data="hmode:level",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="💠 Rarity",
                    callback_data="hmode:rarity",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="🆕 Newest",
                    callback_data="hmode:newest",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="🔢 Card ID",
                    callback_data="hmode:id",
