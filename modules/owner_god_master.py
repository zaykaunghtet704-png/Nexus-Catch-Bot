"""
NEXUS CATCH BOT
modules/owner_god_master.py

Owner & Sudo Admin Commands
"""

import os
import io
import json
import logging
import asyncio
import zipfile

from datetime import datetime
from html import escape

from telegram import Update, InputFile
from telegram.constants import ParseMode
from telegram.ext import (
    ContextTypes,
    CommandHandler,
)

from database import (
    db,
    users_col,
    chats_col,
    inventory_col,
    cards_col,
    codes_col,
    sudo_col,
)

logger = logging.getLogger(__name__)

# ==========================================
# OPTIONAL DEPENDENCIES
# ==========================================

try:
    import psutil
except ImportError:
    psutil = None


# ==========================================
# OWNER CONFIGURATION
# ==========================================

try:
    from config import OWNER_ID as CONFIG_OWNER_ID
except (ImportError, AttributeError):
    CONFIG_OWNER_ID = os.getenv("OWNER_ID", "0")

try:
    OWNER_ID = int(CONFIG_OWNER_ID)
except (TypeError, ValueError):
    OWNER_ID = 0

if OWNER_ID <= 0:
    logger.warning(
        "OWNER_ID မမှန်ပါ။ Render Environment Variables ကို စစ်ပါ။"
    )


# ==========================================
# COLLECTIONS
# ==========================================

system_col = db["system"]
blacklist_col = db["blacklist"]


# ==========================================
# HELPERS
# ==========================================

def safe_int(value, default=0):
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def safe_html(value, default="Unknown"):
    if value is None:
        value = default
    return escape(str(value))


def get_message(update: Update):
    return update.effective_message


def get_user_id(update: Update):
    user = update.effective_user
    return user.id if user else None


async def is_owner(user_id: int) -> bool:
    return bool(OWNER_ID and user_id == OWNER_ID)


async def is_admin_or_owner(user_id: int) -> bool:
    if await is_owner(user_id):
        return True

    try:
        return bool(sudo_col.find_one({"user_id": int(user_id)}))
    except Exception:
        logger.exception("Sudo permission check failed")
        return False


async def deny_access(update: Update):
    message = get_message(update)

    if message:
        await message.reply_text(
            "⛔ ဒီ Command ကို အသုံးပြုခွင့် မရှိပါ။"
        )


async def require_admin(update: Update) -> bool:
    user_id = get_user_id(update)

    if user_id is None:
        return False

    if not await is_admin_or_owner(user_id):
        await deny_access(update)
        return False

    return True


async def require_owner(update: Update) -> bool:
    user_id = get_user_id(update)

    if user_id is None:
        return False

    if not await is_owner(user_id):
        await deny_access(update)
        return False

    return True


async def send_html(update: Update, text: str):
    message = get_message(update)

    if message:
        await message.reply_text(
            text,
            parse_mode=ParseMode.HTML,
        )


# ==========================================
# OWNER HELP
# ==========================================

async def owner_help_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if not await require_admin(update):
        return

    text = (
        "👑 <b>NEXUS OWNER CONTROL PANEL</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"

        "🎴 <b>CARD MANAGEMENT</b>\n"
        "<code>/addcard [id] [name] | [anime] | [rarity]</code>\n"
        "<code>/delcard [card_id]</code>\n"
        "<code>/cardinfo [card_id]</code>\n\n"

        "💰 <b>ECONOMY</b>\n"
        "<code>/addcoins [user_id] [amount]</code>\n"
        "<code>/rmcoins [user_id] [amount]</code>\n"
        "<code>/addgems [user_id] [amount]</code>\n"
        "<code>/rmgems [user_id] [amount]</code>\n\n"

        "🎁 <b>INVENTORY</b>\n"
        "<code>/givecard [user_id] [card_id]</code>\n"
        "<code>/takecard [user_id] [card_id]</code>\n"
        "<code>/transferinv [from_id] [to_id]</code>\n\n"

        "👑 <b>SUDO MANAGEMENT</b>\n"
        "<code>/addsudo [user_id]</code>\n"
        "<code>/delsudo [user_id]</code>\n"
        "<code>/sudolist</code>\n\n"

        "🌟 <b>VIP MANAGEMENT</b>\n"
        "<code>/setvip [user_id]</code>\n"
        "<code>/unsetvip [user_id]</code>\n"
        "<code>/viplist</code>\n\n"

        "🚫 <b>SECURITY</b>\n"
        "<code>/blockuser [user_id] [reason]</code>\n"
        "<code>/unblockuser [user_id]</code>\n"
        "<code>/blockgroup [chat_id]</code>\n"
        "<code>/lockdown</code>\n\n"

        "📦 <b>MAINTENANCE</b>\n"
        "<code>/gencode [code] [coins] [max_uses]</code>\n"
        "<code>/cleanghost</code>\n"
        "<code>/dbstats</code>\n"
        "<code>/zipbackup</code>\n\n"

        "🖥️ <b>SERVER</b>\n"
        "<code>/vps</code>\n"
        "<code>/broadcast</code> (Reply to message)\n\n"

        "━━━━━━━━━━━━━━━━━━━━\n"
        "💗 Nexus Owner System"
    )

    await send_html(update, text)


# ==========================================
# CARD MANAGEMENT
# ==========================================

async def add_card_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if not await require_admin(update):
        return

    msg = get_message(update)

    if not msg:
        return

    photo_id = None

    if msg.reply_to_message and msg.reply_to_message.photo:
        photo_id = msg.reply_to_message.photo[-1].file_id
    elif msg.photo:
        photo_id = msg.photo[-1].file_id

    if not photo_id:
        await msg.reply_text(
            "⚠️ Card ပုံကို Reply လုပ်ပြီး ဒီပုံစံနဲ့ ရိုက်ပါ။\n\n"
            "<code>/addcard ID Name | Anime | Rarity</code>",
            parse_mode=ParseMode.HTML,
        )
        return

    raw = " ".join(context.args).strip()

    if "|" not in raw:
        await msg.reply_text(
            "❌ အသုံးပြုပုံ:\n"
            "<code>/addcard ID Name | Anime | Rarity</code>",
            parse_mode=ParseMode.HTML,
        )
        return

    try:
        parts = [part.strip() for part in raw.split("|")]

        first = parts[0].split(maxsplit=1)

        if len(first) != 2:
            await msg.reply_text(
                "❌ Card ID နဲ့ Name ကို ထည့်ပေးပါ။"
            )
            return

        card_id, card_name = first

        anime = parts[1] if len(parts) > 1 else "Unknown Anime"
        rarity = parts[2] if len(parts) > 2 else "Common"

        existing = cards_col.find_one({
            "$or": [
                {"card_id": card_id},
                {"id": card_id},
            ]
        })

        if existing:
            await msg.reply_text(
                "⚠️ ဒီ Card ID ရှိပြီးသားပါ။"
            )
            return

        card_data = {
            "card_id": card_id,
            "id": card_id,
            "name": card_name,
            "anime": anime,
            "rarity": rarity,
            "img_url": photo_id,
            "created_at": datetime.utcnow(),
        }

        cards_col.insert_one(card_data)

        caption = (
            "🎉 <b>Card Added Successfully!</b>\n\n"
            f"🆔 ID: <code>{safe_html(card_id)}</code>\n"
            f"🎴 Name: <b>{safe_html(card_name)}</b>\n"
            f"📺 Anime: {safe_html(anime)}\n"
            f"💎 Rarity: {safe_html(rarity)}"
        )

        await msg.reply_photo(
            photo=photo_id,
            caption=caption,
            parse_mode=ParseMode.HTML,
        )

    except Exception:
        logger.exception("Add card failed")
        await msg.reply_text(
            "❌ Card ထည့်ရာတွင် Error ဖြစ်နေပါသည်။"
        )


async def delete_card_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if not await require_admin(update):
        return

    if not context.args:
        await send_html(
            update,
            "အသုံးပြုပုံ: <code>/delcard [card_id]</code>",
        )
        return

    card_id = context.args[0].strip()

    result = cards_col.delete_one({
        "$or": [
            {"card_id": card_id},
            {"id": card_id},
        ]
    })

    if result.deleted_count:
        await send_html(
            update,
            f"🗑️ Card <code>{safe_html(card_id)}</code> ဖျက်ပြီးပါပြီ။",
        )
    else:
        await send_html(
            update,
            f"❌ Card <code>{safe_html(card_id)}</code> မတွေ့ပါ။",
        )


async def card_info_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if not await require_admin(update):
        return

    if not context.args:
        await send_html(
            update,
            "အသုံးပြုပုံ: <code>/cardinfo [card_id]</code>",
        )
        return

    card_id = context.args[0].strip()

    card = cards_col.find_one({
        "$or": [
            {"card_id": card_id},
            {"id": card_id},
        ]
    })

    if not card:
        await send_html(
            update,
            f"❌ Card <code>{safe_html(card_id)}</code> မတွေ့ပါ။",
        )
        return

    text = (
        "🎴 <b>CARD INFORMATION</b>\n\n"
        f"🆔 ID: <code>{safe_html(card.get('card_id') or card.get('id'))}</code>\n"
        f"👤 Name: <b>{safe_html(card.get('name'))}</b>\n"
        f"📺 Anime: {safe_html(card.get('anime'))}\n"
        f"💎 Rarity: {safe_html(card.get('rarity'))}"
    )

    image = card.get("img_url") or card.get("image")

    if image:
        try:
            await get_message(update).reply_photo(
                photo=image,
                caption=text,
                parse_mode=ParseMode.HTML,
            )
            return
        except Exception:
            logger.exception("Card image send failed")

    await send_html(update, text)


# ==========================================
# COINS AND GEMS
# ==========================================

async def add_coins_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if not await require_admin(update):
        return

    if len(context.args) < 2:
        await send_html(
            update,
            "အသုံးပြုပုံ: <code>/addcoins [user_id] [amount]</code>",
        )
        return

    try:
        user_id = int(context.args[0])
        amount = int(context.args[1])

        if user_id <= 0 or amount <= 0:
            raise ValueError

        users_col.update_one(
            {"user_id": user_id},
            {"$inc": {"coins": amount}},
            upsert=True,
        )

        await send_html(
            update,
            f"💰 User <code>{user_id}</code> ကို "
            f"<b>+{amount:,} Coins</b> ပေးပြီးပါပြီ။",
        )

    except ValueError:
        await send_html(
            update,
            "❌ User ID နဲ့ Amount ကို မှန်ကန်တဲ့ အပေါင်းကိန်း ထည့်ပါ။",
        )
    except Exception:
        logger.exception("Add coins failed")
        await send_html(update, "❌ Coins ထည့်ရာတွင် Error ဖြစ်နေပါသည်။")


async def remove_coins_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if not await require_admin(update):
        return

    if len(context.args) < 2:
        await send_html(
            update,
            "အသုံးပြုပုံ: <code>/rmcoins [user_id] [amount]</code>",
        )
        return

    try:
        user_id = int(context.args[0])
        amount = int(context.args[1])

        if user_id <= 0 or amount <= 0:
            raise ValueError

        result = users_col.update_one(
            {
                "user_id": user_id,
                "coins": {"$gte": amount},
            },
            {"$inc": {"coins": -amount}},
        )

        if result.modified_count == 0:
            await send_html(
                update,
                "❌ User မရှိပါ သို့မဟုတ် Coins မလုံလောက်ပါ။",
            )
            return

        await send_html(
            update,
            f"💸 User <code>{user_id}</code> ထံမှ "
            f"<b>{amount:,} Coins</b> နှုတ်ပြီးပါပြီ။",
        )

    except ValueError:
        await send_html(
            update,
            "❌ User ID နဲ့ Amount ကို မှန်ကန်တဲ့ အပေါင်းကိန်း ထည့်ပါ။",
        )
    except Exception:
        logger.exception("Remove coins failed")
        await send_html(update, "❌ Coins နှုတ်ရာတွင် Error ဖြစ်နေပါသည်။")


async def add_gems_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if not await require_admin(update):
        return

    if len(context.args) < 2:
        await send_html(
            update,
            "အသုံးပြုပုံ: <code>/addgems [user_id] [amount]</code>",
        )
        return

    try:
        user_id = int(context.args[0])
        amount = int(context.args[1])

        if user_id <= 0 or amount <= 0:
            raise ValueError

        users_col.update_one(
            {"user_id": user_id},
            {"$inc": {"gems": amount}},
            upsert=True,
        )

        await send_html(
            update,
            f"💎 User <code>{user_id}</code> ကို "
            f"<b>+{amount:,} Gems</b> ပေးပြီးပါပြီ။",
        )

    except ValueError:
        await send_html(update, "❌ User ID / Amount မှားနေပါသည်။")
    except Exception:
        logger.exception("Add gems failed")
        await send_html(update, "❌ Gems ထည့်ရာတွင် Error ဖြစ်နေပါသည်။")


async def remove_gems_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if not await require_admin(update):
        return

    if len(context.args) < 2:
        await send_html(
            update,
            "အသုံးပြုပုံ: <code>/rmgems [user_id] [amount]</code>",
        )
        return

    try:
        user_id = int(context.args[0])
        amount = int(context.args[1])

        if user_id <= 0 or amount <= 0:
            raise ValueError

        result = users_col.update_one(
            {
                "user_id": user_id,
                "gems": {"$gte": amount},
            },
            {"$inc": {"gems": -amount}},
        )

        if result.modified_count == 0:
            await send_html(
                update,
                "❌ User မရှိပါ သို့မဟုတ် Gems မလုံလောက်ပါ။",
            )
            return

        await send_html(
            update,
            f"💎 User <code>{user_id}</code> ထံမှ "
            f"<b>{amount:,} Gems</b> နှုတ်ပြီးပါပြီ။",
        )

    except ValueError:
        await send_html(update, "❌ User ID / Amount မှားနေပါသည်။")
    except Exception:
        logger.exception("Remove gems failed")
        await send_html(update, "❌ Gems နှုတ်ရာတွင် Error ဖြစ်နေပါသည်။")


# ==========================================
# INVENTORY
# ==========================================

async def give_card_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if not await require_admin(update):
        return

    if len(context.args) < 2:
        await send_html(
            update,
            "အသုံးပြုပုံ: <code>/givecard [user_id] [card_id]</code>",
        )
        return

    try:
        user_id = int(context.args[0])
        card_id = context.args[1].strip()

        card = cards_col.find_one({
            "$or": [
                {"card_id": card_id},
                {"id": card_id},
            ]
        })

        if not card:
            await send_html(update, "❌ Card ID မတွေ့ပါ။")
            return

        inventory_col.insert_one({
            "user_id": user_id,
            "card_id": card.get("card_id") or card.get("id"),
            "name": card.get("name"),
            "anime": card.get("anime"),
            "rarity": card.get("rarity"),
            "img_url": card.get("img_url"),
            "obtained_at": datetime.utcnow(),
        })

        await send_html(
            update,
            f"🎁 User <code>{user_id}</code> ထံ "
            f"<b>{safe_html(card.get('name'))}</b> ပေးပြီးပါပြီ။",
        )

    except ValueError:
        await send_html(update, "❌ User ID မှားနေပါသည်။")
    except Exception:
        logger.exception("Give card failed")
        await send_html(update, "❌ Card ပေးရာတွင် Error ဖြစ်နေပါသည်။")


async def take_card_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if not await require_admin(update):
        return

    if len(context.args) < 2:
        await send_html(
            update,
            "အသုံးပြုပုံ: <code>/takecard [user_id] [card_id]</code>",
        )
        return

    try:
        user_id = int(context.args[0])
        card_id = context.args[1].strip()

        result = inventory_col.delete_one({
            "user_id": user_id,
            "$or": [
                {"card_id": card_id},
                {"id": card_id},
            ],
        })

        if result.deleted_count:
            await send_html(
                update,
                f"🗑️ User <code>{user_id}</code> ထံမှ "
                f"Card <code>{safe_html(card_id)}</code> သိမ်းပြီးပါပြီ။",
            )
        else:
            await send_html(update, "❌ User ထံမှာ အဲဒီ Card မရှိပါ။")

    except ValueError:
        await send_html(update, "❌ User ID မှားနေပါသည်။")
    except Exception:
        logger.exception("Take card failed")
        await send_html(update, "❌ Card သိမ်းရာတွင် Error ဖြစ်နေပါသည်။")


async def transfer_inventory(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if not await require_owner(update):
        return

    if len(context.args) < 2:
        await send_html(
            update,
            "အသုံးပြုပုံ: <code>/transferinv [from_id] [to_id]</code>",
        )
        return

    try:
        from_id = int(context.args[0])
        to_id = int(context.args[1])

        if from_id <= 0 or to_id <= 0 or from_id == to_id:
            raise ValueError

        result = inventory_col.update_many(
            {"user_id": from_id},
            {"$set": {"user_id": to_id}},
        )

        await send_html(
            update,
            f"📦 Inventory လွှဲပြီးပါပြီ။\n"
            f"From: <code>{from_id}</code>\n"
            f"To: <code>{to_id}</code>\n"
            f"Cards: <b>{result.modified_count:,}</b>",
        )

    except ValueError:
        await send_html(update, "❌ User ID နှစ်ခု မှန်ကန်စွာ ထည့်ပါ။")
    except Exception:
        logger.exception("Transfer inventory failed")
        await send_html(update, "❌ Inventory လွှဲရာတွင် Error ဖြစ်နေပါသည်။")


# ==========================================
# SUDO
# ==========================================

async def add_sudo_user(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if not await require_owner(update):
        return

    if not context.args:
        await send_html(update, "အသုံးပြုပုံ: <code>/addsudo [user_id]</code>")
        return

    try:
        user_id = int(context.args[0])

        if user_id <= 0 or user_id == OWNER_ID:
            raise ValueError

        sudo_col.update_one(
            {"user_id": user_id},
            {"$set": {"added_at": datetime.utcnow()}},
            upsert=True,
        )

        await send_html(
            update,
            f"👑 User <code>{user_id}</code> ကို Sudo ပေးပြီးပါပြီ။",
        )

    except ValueError:
        await send_html(update, "❌ User ID မှားနေပါသည်။")
    except Exception:
        logger.exception("Add sudo failed")
        await send_html(update, "❌ Sudo ထည့်ရာတွင် Error ဖြစ်နေပါသည်။")


async def del_sudo_user(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if not await require_owner(update):
        return

    if not context.args:
        await send_html(update, "အသုံးပြုပုံ: <code>/delsudo [user_id]</code>")
        return

    try:
        user_id = int(context.args[0])

        result = sudo_col.delete_one({"user_id": user_id})

        await send_html(
            update,
            "🗑️ Sudo ဖယ်ရှားပြီးပါပြီ။"
            if result.deleted_count
            else "❌ Sudo User မတွေ့ပါ။",
        )

    except ValueError:
        await send_html(update, "❌ User ID မှားနေပါသည်။")
    except Exception:
        logger.exception("Delete sudo failed")
        await send_html(update, "❌ Sudo ဖယ်ရှားရာတွင် Error ဖြစ်နေပါသည်။")


async def list_sudo_users(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if not await require_admin(update):
        return

    sudos = list(sudo_col.find({}).limit(100))

    lines = [
        f"• <code>{safe_html(item.get('user_id'))}</code>"
        for item in sudos
    ]

    await send_html(
        update,
        "👑 <b>SUDO ADMINS</b>\n\n"
        + ("\n".join(lines) if lines else "Sudo မရှိသေးပါ။"),
    )


# ==========================================
# VIP
# ==========================================

async def set_vip_user(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if not await require_admin(update):
        return

    if not context.args:
        await send_html(update, "အသုံးပြုပုံ: <code>/setvip [user_id]</code>")
        return

    try:
        user_id = int(context.args[0])

        users_col.update_one(
            {"user_id": user_id},
            {
                "$set": {
                    "is_vip": True,
                    "vip_status": "VIP",
                }
            },
            upsert=True,
        )

        await send_html(
            update,
            f"🌟 User <code>{user_id}</code> ကို VIP သတ်မှတ်ပြီးပါပြီ။",
        )

    except ValueError:
        await send_html(update, "❌ User ID မှားနေပါသည်။")
    except Exception:
        logger.exception("Set VIP failed")
        await send_html(update, "❌ VIP သတ်မှတ်ရာတွင် Error ဖြစ်နေပါသည်။")


async def unset_vip_user(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if not await require_admin(update):
        return

    if not context.args:
        await send_html(update, "အသုံးပြုပုံ: <code>/unsetvip [user_id]</code>")
        return

    try:
        user_id = int(context.args[0])

        users_col.update_one(
            {"user_id": user_id},
            {
                "$set": {
                    "is_vip": False,
                    "vip_status": "None",
                }
            },
        )

        await send_html(
            update,
            f"⚪ User <code>{user_id}</code> ၏ VIP ကို ဖြုတ်ပြီးပါပြီ။",
        )

    except ValueError:
        await send_html(update, "❌ User ID မှားနေပါသည်။")
    except Exception:
        logger.exception("Unset VIP failed")
        await send_html(update, "❌ VIP ဖြုတ်ရာတွင် Error ဖြစ်နေပါသည်။")


async def list_vip_users(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if not await require_admin(update):
        return

    vips = list(users_col.find({"is_vip": True}).limit(100))

    lines = [
        f"• <code>{safe_html(item.get('user_id'))}</code>"
        for item in vips
    ]

    await send_html(
        update,
        f"🌟 <b>VIP USERS ({len(vips)})</b>\n\n"
        + ("\n".join(lines) if lines else "VIP User မရှိသေးပါ။"),
    )


# ==========================================
# BLACKLIST
# ==========================================

async def blacklist_user_global(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if not await require_admin(update):
        return

    if not context.args:
        await send_html(
            update,
            "အသုံးပြုပုံ: <code>/blockuser [user_id] [reason]</code>",
        )
        return

    try:
        target_id = int(context.args[0])
        reason = " ".join(context.args[1:]) or "No reason provided"

        blacklist_col.update_one(
            {"entity_id": target_id, "type": "user"},
            {
                "$set": {
                    "reason": reason,
                    "blocked_by": get_user_id(update),
                    "at": datetime.utcnow(),
                }
            },
            upsert=True,
        )

        users_col.update_one(
            {"user_id": target_id},
            {"$set": {"is_gbanned": True}},
            upsert=True,
        )

        await send_html(
            update,
            f"🚫 User <code>{target_id}</code> ကို Block လုပ်ပြီးပါပြီ။",
        )

    except ValueError:
        await send_html(update, "❌ User ID မှားနေပါသည်။")
    except Exception:
        logger.exception("Block user failed")
        await send_html(update, "❌ User Block လုပ်ရာတွင် Error ဖြစ်နေပါသည်။")


async def unblacklist_user_global(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if not await require_admin(update):
        return

    if not context.args:
        await send_html(
            update,
            "အသုံးပြုပုံ: <code>/unblockuser [user_id]</code>",
        )
        return

    try:
        target_id = int(context.args[0])

        blacklist_col.delete_one({
            "entity_id": target_id,
            "type": "user",
        })

        users_col.update_one(
            {"user_id": target_id},
            {"$set": {"is_gbanned": False}},
        )

        await send_html(
            update,
            f"✅ User <code>{target_id}</code> Unblock ပြီးပါပြီ။",
        )

    except ValueError:
        await send_html(update, "❌ User ID မှားနေပါသည်။")
    except Exception:
        logger.exception("Unblock user failed")
        await send_html(update, "❌ Unblock လုပ်ရာတွင် Error ဖြစ်နေပါသည်။")


async def blacklist_group(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if not await require_admin(update):
        return

    if not context.args:
        await send_html(
            update,
            "အသုံးပြုပုံ: <code>/blockgroup [chat_id]</code>",
        )
        return

    try:
        chat_id = int(context.args[0])

        blacklist_col.update_one(
            {"entity_id": chat_id, "type": "group"},
            {
                "$set": {
                    "blocked_by": get_user_id(update),
                    "at": datetime.utcnow(),
                }
            },
            upsert=True,
        )

        chats_col.delete_one({"chat_id": chat_id})

        try:
            await context.bot.leave_chat(chat_id)
        except Exception:
            logger.warning("Could not leave blocked group %s", chat_id)

        await send_html(
            update,
            f"🚫 Group <code>{chat_id}</code> ကို Block ပြီးပါပြီ။",
        )

    except ValueError:
        await send_html(update, "❌ Chat ID မှားနေပါသည်။")
    except Exception:
        logger.exception("Block group failed")
        await send_html(update, "❌ Group Block လုပ်ရာတွင် Error ဖြစ်နေပါသည်။")


# ==========================================
# LOCKDOWN
# ==========================================

async def emergency_lockdown(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if not await require_owner(update):
        return

    current = system_col.find_one({"key": "lockdown"}) or {}
    new_state = not bool(current.get("status", False))

    system_col.update_one(
        {"key": "lockdown"},
        {"$set": {"status": new_state}},
        upsert=True,
    )

    await send_html(
        update,
        "🚨 <b>LOCKDOWN ACTIVATED</b>"
        if new_state
        else "✅ <b>LOCKDOWN LIFTED</b>",
    )


# ==========================================
# GIFT CODES
# ==========================================

async def generate_gift_code(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if not await require_admin(update):
        return

    if len(context.args) < 3:
        await send_html(
            update,
            "အသုံးပြုပုံ: <code>/gencode [code] [coins] [max_uses]</code>",
        )
        return

    try:
        code = context.args[0].upper()
        coins = int(context.args[1])
        max_uses = int(context.args[2])

        if coins <= 0 or max_uses <= 0:
            raise ValueError

        codes_col.update_one(
            {"code": code},
            {
                "$set": {
                    "coins": coins,
                    "max_uses": max_uses,
                    "used_count": 0,
                    "used_by": [],
                    "created_at": datetime.utcnow(),
                }
            },
            upsert=True,
        )

        await send_html(
            update,
            f"🎁 Code <code>{safe_html(code)}</code> ထုတ်ပြီးပါပြီ။\n"
            f"💰 Coins: <b>{coins:,}</b>\n"
            f"👥 Uses: <b>{max_uses}</b>",
        )

    except ValueError:
        await send_html(update, "❌ Coins / Max Uses မှန်ကန်တဲ့ အပေါင်းကိန်းဖြစ်ရပါမည်။")
    except Exception:
        logger.exception("Generate code failed")
        await send_html(update, "❌ Code ထုတ်ရာတွင် Error ဖြစ်နေပါသည်။")


# ==========================================
# CLEAN GHOST DATA
# ==========================================

async def clean_ghost_data(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if not await require_admin(update):
        return

    msg = await get_message(update).reply_text(
        "🧹 Ghost Data စစ်ဆေးနေပါသည်..."
    )

    try:
        valid_ids = set(cards_col.distinct("card_id"))
        valid_ids.update(cards_col.distinct("id"))

        orphan_ids = []

        for item in inventory_col.find({}, {"card_id": 1, "id": 1}):
            card_id = item.get("card_id") or item.get("id")

            if card_id not in valid_ids:
                orphan_ids.append(item["_id"])

        deleted_count = 0

        if orphan_ids:
            result = inventory_col.delete_many({
                "_id": {"$in": orphan_ids}
            })
            deleted_count = result.deleted_count

        invalid_users = users_col.delete_many({
            "user_id": {"$exists": False}
        })

        await msg.edit_text(
            "✅ <b>Cleanup Completed</b>\n\n"
            f"🗑️ Removed Cards: <b>{deleted_count:,}</b>\n"
            f"🗑️ Removed Invalid Users: "
            f"<b>{invalid_users.deleted_count:,}</b>",
            parse_mode=ParseMode.HTML,
        )

    except Exception:
        logger.exception("Ghost cleanup failed")
        await msg.edit_text("❌ Cleanup Error ဖြစ်နေပါသည်။")


# ==========================================
# DATABASE STATS
# ==========================================

async def db_stats_detailed(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if not await require_admin(update):
        return

    try:
        total_users = users_col.count_documents({})
        total_cards = cards_col.count_documents({})
        total_inventory = inventory_col.count_documents({})
        total_groups = chats_col.count_documents({})

        pipeline = [
            {
                "$group": {
                    "_id": None,
                    "coins": {"$sum": "$coins"},
                    "gems": {"$sum": "$gems"},
                }
            }
        ]

        result = list(users_col.aggregate(pipeline))
        totals = result[0] if result else {}

        coins = safe_int(totals.get("coins", 0))
        gems = safe_int(totals.get("gems", 0))

        text = (
            "📊 <b>NEXUS DATABASE STATS</b>\n\n"
            f"👥 Users: <b>{total_users:,}</b>\n"
            f"👥 Groups: <b>{total_groups:,}</b>\n"
            f"🎴 Cards: <b>{total_cards:,}</b>\n"
            f"🎒 Inventory: <b>{total_inventory:,}</b>\n\n"
            f"💰 Total Coins: <b>{coins:,}</b>\n"
            f"💎 Total Gems: <b>{gems:,}</b>"
        )

        await send_html(update, text)

    except Exception:
        logger.exception("DB stats failed")
        await send_html(update, "❌ Database Stats ဖတ်မရပါ။")


# ==========================================
# ZIP BACKUP
# ==========================================

async def full_zip_backup(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if not await require_owner(update):
        return

    msg = await get_message(update).reply_text(
        "📦 Backup ပြုလုပ်နေပါသည်..."
    )

    try:
        buffer = io.BytesIO()

        collections = {
            "users": users_col,
            "chats": chats_col,
            "cards": cards_col,
            "inventory": inventory_col,
            "codes": codes_col,
            "sudo": sudo_col,
            "system": system_col,
            "blacklist": blacklist_col,
        }

        with zipfile.ZipFile(
            buffer,
            "w",
            zipfile.ZIP_DEFLATED,
        ) as archive:
            for name, collection in collections.items():
                documents = list(
                    collection.find({}, {"_id": 0})
                )

                archive.writestr(
                    f"{name}.json",
                    json.dumps(
                        documents,
                        indent=2,
                        default=str,
                        ensure_ascii=False,
                    ),
                )

        buffer.seek(0)

        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")

        await context.bot.send_document(
            chat_id=update.effective_chat.id,
            document=InputFile(
                buffer,
                filename=f"nexus_backup_{timestamp}.zip",
            ),
        )

        await msg.delete()

    except Exception:
        logger.exception("Backup failed")
        await msg.edit_text("❌ Backup ပြုလုပ်ရာတွင် Error ဖြစ်နေပါသည်။")


# ==========================================
# VPS STATUS
# ==========================================

async def vps_status_monitor(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if not await require_admin(update):
        return

    if psutil is None:
        await send_html(
            update,
            "❌ psutil မရှိပါ။ Requirements ထဲတွင် psutil ထည့်သွင်းပါ။",
        )
        return

    try:
        cpu = psutil.cpu_percent(interval=0.5)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage("/")
        bot_ram = (
            psutil.Process(os.getpid()).memory_info().rss
            / (1024 * 1024)
        )

        text = (
            "🖥️ <b>SERVER STATUS</b>\n\n"
            f"⚙️ CPU: <b>{cpu}%</b>\n"
            f"🧠 RAM: <b>{memory.percent}%</b>\n"
            f"🤖 Bot RAM: <b>{bot_ram:.2f} MB</b>\n"
            f"💾 Disk Used: <b>{disk.percent}%</b>\n"
            f"📦 Disk Free: <b>{disk.free // (1024 ** 3)} GB</b>"
        )

        await send_html(update, text)

    except Exception:
        logger.exception("VPS status failed")
        await send_html(update, "❌ Server Status စစ်မရပါ။")


# ==========================================
# BROADCAST
# ==========================================

async def broadcast_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if not await require_admin(update):
        return

    message = get_message(update)

    if not message.reply_to_message:
        await send_html(
            update,
            "⚠️ ပို့လိုသော Message ကို Reply လုပ်ပြီး <code>/broadcast</code> ရိုက်ပါ။",
        )
        return

    chats = list(chats_col.find({}))
    status = await message.reply_text(
        f"📢 Broadcasting to {len(chats)} chats..."
    )

    success = 0
    failed = 0

    for chat in chats:
        chat_id = chat.get("chat_id")

        if not chat_id:
            failed += 1
            continue

        try:
            await message.reply_to_message.copy(chat_id=chat_id)
            success += 1
            await asyncio.sleep(0.05)

        except Exception:
            failed += 1
            logger.exception("Broadcast failed for chat %s", chat_id)

    await status.edit_text(
        f"✅ Broadcast Completed\n\n"
        f"Success: {success}\n"
        f"Failed: {failed}"
    )


# ==========================================
# HANDLER REGISTRATION
# ==========================================

def get_master_owner_handlers():
    return [
        CommandHandler(["ownerhelp", "adminhelp"], owner_help_command),

        # Cards
        CommandHandler("addcard", add_card_command),
        CommandHandler("delcard", delete_card_command),
        CommandHandler("cardinfo", card_info_command),

        # Economy
        CommandHandler("addcoins", add_coins_command),
        CommandHandler("rmcoins", remove_coins_command),
        CommandHandler("addgems", add_gems_command),
        CommandHandler("rmgems", remove_gems_command),

        # Inventory
        CommandHandler("givecard", give_card_command),
        CommandHandler("takecard", take_card_command),
        CommandHandler("transferinv", transfer_inventory),

        # Sudo
        CommandHandler("addsudo", add_sudo_user),
        CommandHandler("delsudo", del_sudo_user),
        CommandHandler("sudolist", list_sudo_users),

        # VIP
        CommandHandler("setvip", set_vip_user),
        CommandHandler("unsetvip", unset_vip_user),
        CommandHandler("viplist", list_vip_users),

        # Security
        CommandHandler("blockuser", blacklist_user_global),
        CommandHandler("unblockuser", unblacklist_user_global),
        CommandHandler("blockgroup", blacklist_group),
        CommandHandler("lockdown", emergency_lockdown),

        # Maintenance
        CommandHandler("gencode", generate_gift_code),
        CommandHandler("cleanghost", clean_ghost_data),
        CommandHandler("dbstats", db_stats_detailed),
        CommandHandler("zipbackup", full_zip_backup),

        # Server
        CommandHandler("vps", vps_status_monitor),
        CommandHandler("broadcast", broadcast_message),
    ]
