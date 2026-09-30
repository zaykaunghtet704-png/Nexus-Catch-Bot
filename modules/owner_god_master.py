"""
modules/owner_god_master.py - Full Admin & Owner Commands with Help Menu
"""
import sys
import os
import io
import json
import logging
import asyncio
import zipfile
import psutil
from datetime import datetime
from html import escape

from telegram import Update, InputFile, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler

# Database Collections & Config Imports
from database import (
    users_col,
    chats_col,
    inventory_col,
    cards_col,
    system_col,
    codes_col,
    sudo_col,
    blacklist_col
)

try:
    from config import OWNER_ID
except ImportError:
    OWNER_ID = int(os.getenv("OWNER_ID", "123456789"))

logger = logging.getLogger(__name__)

# ── Helper Permission Checks ──────────────────────────────────────────────────

async def is_owner(user_id: int) -> bool:
    return user_id == OWNER_ID

async def is_admin_or_owner(user_id: int) -> bool:
    if user_id == OWNER_ID:
        return True
    sudo = sudo_col.find_one({"user_id": user_id})
    return bool(sudo)

# ══════════════════════════════════════════════════════════════════════════════
# 0. OWNER HELP MENU
# ══════════════════════════════════════════════════════════════════════════════

async def owner_help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Owner & Admin Commands များအားလုံး၏ လမ်းညွှန် Menu"""
    if not await is_admin_or_owner(update.effective_user.id):
        return

    text = (
        "👑 <b>OWNER & ADMIN CONTROL PANEL</b>\n"
        "─────────────────────────\n\n"
        "🎴 <b>Card Management</b>\n"
        "• <code>/addcard [id] [name] | [anime] | [rarity]</code> (Reply photo)\n"
        "• <code>/delcard [card_id]</code> - ကတ်ဖျက်ရန်\n"
        "• <code>/cardinfo [card_id]</code> - ကတ်အချက်အလက် စစ်ရန်\n\n"

        "💰 <b>Economy & User Management</b>\n"
        "• <code>/addcoins [user_id] [amount]</code> - Coin ပေးရန်\n"
        "• <code>/rmcoins [user_id] [amount]</code> - Coin နှုတ်ရန်\n"
        "• <code>/addgems [user_id] [amount]</code> - Gem ပေးရန်\n"
        "• <code>/rmgems [user_id] [amount]</code> - Gem နှုတ်ရန်\n"
        "• <code>/givecard [user_id] [card_id]</code> - User ထံ ကတ်တိုက်ရိုက်ပေးရန်\n"
        "• <code>/takecard [user_id] [card_id]</code> - User ထံမှ ကတ်ပြန်သိမ်းရန်\n"
        "• <code>/transferinv [from_id] [to_id]</code> - Inventory တစ်ခုလုံး လွှဲရန်\n\n"

        "👑 <b>Sudo & VIP Control</b>\n"
        "• <code>/addsudo [user_id]</code> - Sudo Admin တိုးရန်\n"
        "• <code>/delsudo [user_id]</code> - Sudo ဖျက်ရန်\n"
        "• <code>/sudolist</code> - Sudo များကြည့်ရန်\n"
        "• <code>/setvip [user_id]</code> - VIP သတ်မှတ်ရန်\n"
        "• <code>/unsetvip [user_id]</code> - VIP ဖြုတ်ရန်\n"
        "• <code>/viplist</code> - VIP များကြည့်ရန်\n\n"

        "🚫 <b>Blacklist & Security</b>\n"
        "• <code>/blockuser [user_id] [reason]</code> - User Ban ရန်\n"
        "• <code>/unblockuser [user_id]</code> - User Unban ရန်\n"
        "• <code>/blockgroup [chat_id]</code> - Group Block ရန်\n"
        "• <code>/lockdown</code> - Emergency Lockdown ဖွင့်/ပိတ်\n\n"

        "📦 <b>Codes & Maintenance</b>\n"
        "• <code>/gencode [code] [coins] [max_uses]</code> - Gift Code ထုတ်ရန်\n"
        "• <code>/cleanghost</code> - Ghost Data များ ရှင်းရန်\n"
        "• <code>/dbstats</code> - Database Stats ကြည့်ရန်\n"
        "• <code>/zipbackup</code> - Database Backup ZIP ဒေါင်းရန်\n\n"

        "🖥️ <b>Server & Utilities</b>\n"
        "• <code>/vps</code> - VPS CPU / RAM / Disk စစ်ရန်\n"
        "• <code>/broadcast</code> - Message ကို Group များသို့ ပို့ရန် (Reply message)\n"
        "• <code>/shell [command]</code> - VPS Terminal Command ရိုက်ရန်\n"
        "• <code>/eval [code]</code> - Python Code စမ်းရန်"
    )
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)

# ══════════════════════════════════════════════════════════════════════════════
# 1. CARD MANAGEMENT
# ══════════════════════════════════════════════════════════════════════════════

async def add_card_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await is_admin_or_owner(update.effective_user.id): return

    msg = update.message
    photo_id = None

    if msg.reply_to_message and msg.reply_to_message.photo:
        photo_id = msg.reply_to_message.photo[-1].file_id
    elif msg.photo:
        photo_id = msg.photo[-1].file_id

    if not photo_id:
        await msg.reply_text("⚠️ <b>ပုံကို Reply လုပ်ပြီး /addcard ရိုက်ပါ!</b>", parse_mode=ParseMode.HTML)
        return

    text_args = " ".join(context.args)
    if not text_args or "|" not in text_args:
        await msg.reply_text("❌ <code>/addcard [card_id] [name] | [anime] | [rarity]</code>", parse_mode=ParseMode.HTML)
        return

    try:
        parts = text_args.split("|")
        first_part = parts[0].strip().split(maxsplit=1)
        if len(first_part) < 2:
            await msg.reply_text("❌ Card ID နှင့် Name ကို သီးခြားခွဲရေးပေးပါ။", parse_mode=ParseMode.HTML)
            return

        card_id, card_name = first_part[0].strip(), first_part[1].strip()
        anime = parts[1].strip() if len(parts) > 1 else "Unknown Anime"
        rarity = parts[2].strip() if len(parts) > 2 else "⚪ Common"

        if cards_col.find_one({"$or": [{"card_id": card_id}, {"id": card_id}]}):
            await msg.reply_text(f"⚠️ Card ID <code>{card_id}</code> ရှိပြီးသား ဖြစ်ပါသည်။", parse_mode=ParseMode.HTML)
            return

        card_data = {
            "card_id": card_id,
            "id": card_id,
            "name": card_name,
            "anime": anime,
            "rarity": rarity,
            "img_url": photo_id,
            "created_at": datetime.utcnow()
        }
        cards_col.insert_one(card_data)
        
        caption = (
            f"🎉 <b>ကတ်အသစ် ထည့်ပြီးပါပြီ!</b>\n\n"
            f"🆔 <b>Card ID:</b> <code>{card_id}</code>\n"
            f"👤 <b>Name:</b> {escape(card_name)}\n"
            f"📺 <b>Anime:</b> {escape(anime)}\n"
            f"💎 <b>Rarity:</b> {escape(rarity)}"
        )
        await msg.reply_photo(photo=photo_id, caption=caption, parse_mode=ParseMode.HTML)

    except Exception as e:
        await msg.reply_text(f"❌ Error adding card: {e}")

async def delete_card_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await is_admin_or_owner(update.effective_user.id): return
    if not context.args:
        await update.message.reply_text("အသုံးပြုပုံ: <code>/delcard [card_id]</code>", parse_mode=ParseMode.HTML)
        return

    card_id = context.args[0].strip()
    res = cards_col.delete_one({"$or": [{"card_id": card_id}, {"id": card_id}]})
    if res.deleted_count > 0:
        await update.message.reply_text(f"🗑️ Card ID <code>{card_id}</code> ကို ဖျက်လိုက်ပါပြီ။", parse_mode=ParseMode.HTML)
    else:
        await update.message.reply_text(f"❌ Card ID <code>{card_id}</code> မရှိပါ။", parse_mode=ParseMode.HTML)

async def card_info_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await is_admin_or_owner(update.effective_user.id): return
    if not context.args:
        await update.message.reply_text("အသုံးပြုပုံ: <code>/cardinfo [card_id]</code>", parse_mode=ParseMode.HTML)
        return

    card_id = context.args[0].strip()
    card = cards_col.find_one({"$or": [{"card_id": card_id}, {"id": card_id}]})
    if not card:
        await update.message.reply_text(f"❌ Card ID <code>{card_id}</code> မရှိပါ။", parse_mode=ParseMode.HTML)
        return

    caption = (
        f"🎴 <b>Card Information</b>\n\n"
        f"🆔 <b>Card ID:</b> <code>{card.get('card_id') or card.get('id')}</code>\n"
        f"👤 <b>Name:</b> {escape(card.get('name', ''))}\n"
        f"📺 <b>Anime:</b> {escape(card.get('anime', ''))}\n"
        f"💎 <b>Rarity:</b> {escape(card.get('rarity', ''))}"
    )
    img_url = card.get('img_url') or card.get('image')
    if img_url:
        try:
            await update.message.reply_photo(photo=img_url, caption=caption, parse_mode=ParseMode.HTML)
        except Exception:
            await update.message.reply_text(caption, parse_mode=ParseMode.HTML)
    else:
        await update.message.reply_text(caption, parse_mode=ParseMode.HTML)

# ══════════════════════════════════════════════════════════════════════════════
# 2. ECONOMY & USER MANAGEMENT
# ══════════════════════════════════════════════════════════════════════════════

async def add_coins_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await is_admin_or_owner(update.effective_user.id): return
    if len(context.args) < 2:
        await update.message.reply_text("အသုံးပြုပုံ: <code>/addcoins [user_id] [amount]</code>", parse_mode=ParseMode.HTML)
        return
    try:
        user_id, amount = int(context.args[0]), int(context.args[1])
        users_col.update_one({"user_id": user_id}, {"$inc": {"balance": amount}}, upsert=True)
        await update.message.reply_text(f"💰 User <code>{user_id}</code> ထံ <b>+{amount:,} Coins</b> ထည့်ပေးလိုက်ပါပြီ။", parse_mode=ParseMode.HTML)
    except ValueError:
        await update.message.reply_text("❌ User ID နှင့် Amount ဂဏန်း မှန်ပါစေ။")

async def remove_coins_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await is_admin_or_owner(update.effective_user.id): return
    if len(context.args) < 2:
        await update.message.reply_text("အသုံးပြုပုံ: <code>/rmcoins [user_id] [amount]</code>", parse_mode=ParseMode.HTML)
        return
    try:
        user_id, amount = int(context.args[0]), int(context.args[1])
        users_col.update_one({"user_id": user_id}, {"$inc": {"balance": -amount}}, upsert=True)
        await update.message.reply_text(f"💸 User <code>{user_id}</code> ထံမှ <b>-{amount:,} Coins</b> နှုတ်လိုက်ပါပြီ။", parse_mode=ParseMode.HTML)
    except ValueError:
        await update.message.reply_text("❌ User ID နှင့် Amount ဂဏန်း မှန်ပါစေ။")

async def add_gems_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await is_admin_or_owner(update.effective_user.id): return
    if len(context.args) < 2:
        await update.message.reply_text("အသုံးပြုပုံ: <code>/addgems [user_id] [amount]</code>", parse_mode=ParseMode.HTML)
        return
    try:
        user_id, amount = int(context.args[0]), int(context.args[1])
        users_col.update_one({"user_id": user_id}, {"$inc": {"gems": amount}}, upsert=True)
        await update.message.reply_text(f"💎 User <code>{user_id}</code> ထံ <b>+{amount:,} Gems</b> ထည့်ပေးလိုက်ပါပြီ။", parse_mode=ParseMode.HTML)
    except ValueError:
        await update.message.reply_text("❌ User ID နှင့် Amount ဂဏန်း မှန်ပါစေ။")

async def give_card_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await is_admin_or_owner(update.effective_user.id): return
    if len(context.args) < 2:
        await update.message.reply_text("အသုံးပြုပုံ: <code>/givecard [user_id] [card_id]</code>", parse_mode=ParseMode.HTML)
        return
    try:
        user_id, card_id = int(context.args[0]), context.args[1].strip()
        card = cards_col.find_one({"$or": [{"card_id": card_id}, {"id": card_id}]})
        if not card:
            await update.message.reply_text(f"❌ Card ID <code>{card_id}</code> မရှိပါ။", parse_mode=ParseMode.HTML)
            return

        inventory_col.insert_one({
            "user_id": user_id,
            "card_id": card.get("card_id") or card.get("id"),
            "name": card.get("name"),
            "anime": card.get("anime"),
            "rarity": card.get("rarity"),
            "img_url": card.get("img_url"),
            "obtained_at": datetime.utcnow()
        })
        await update.message.reply_text(f"🎁 User <code>{user_id}</code> ထံ ကတ် <b>{card.get('name')}</b> ပေးလိုက်ပါပြီ။", parse_mode=ParseMode.HTML)
    except ValueError:
        await update.message.reply_text("❌ User ID မှန်ကန်ပါစေ။")

async def take_card_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await is_admin_or_owner(update.effective_user.id): return
    if len(context.args) < 2:
        await update.message.reply_text("အသုံးပြုပုံ: <code>/takecard [user_id] [card_id]</code>", parse_mode=ParseMode.HTML)
        return
    try:
        user_id, card_id = int(context.args[0]), context.args[1].strip()
        res = inventory_col.delete_one({"user_id": user_id, "$or": [{"card_id": card_id}, {"id": card_id}]})
        if res.deleted_count > 0:
            await update.message.reply_text(f"🗑️ User <code>{user_id}</code> ထံမှ Card ID <code>{card_id}</code> ပြန်သိမ်းလိုက်ပါပြီ။", parse_mode=ParseMode.HTML)
        else:
            await update.message.reply_text("❌ အဆိုပါ ကတ်ကို မတွေ့ပါ။", parse_mode=ParseMode.HTML)
    except ValueError:
        await update.message.reply_text("❌ User ID မှန်ကန်ပါစေ။")

async def transfer_inventory(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await is_owner(update.effective_user.id): return
    if len(context.args) < 2:
        await update.message.reply_text("အသုံးပြုပုံ: <code>/transferinv [from_user_id] [to_user_id]</code>", parse_mode=ParseMode.HTML)
        return
    try:
        from_id, to_id = int(context.args[0]), int(context.args[1])
        res = inventory_col.update_many({"user_id": from_id}, {"$set": {"user_id": to_id}})
        await update.message.reply_text(f"📦 Inventory Transferred! Total Cards Moved: <b>{res.modified_count:,}</b>", parse_mode=ParseMode.HTML)
    except ValueError:
        await update.message.reply_text("❌ User ID ဂဏန်း မှန်ကန်ပါစေ။")

# ══════════════════════════════════════════════════════════════════════════════
# 3. SECURITY, SUDO, VIP & BLACKLISTS
# ══════════════════════════════════════════════════════════════════════════════

async def add_sudo_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await is_owner(update.effective_user.id): return
    if not context.args:
        await update.message.reply_text("အသုံးပြုပုံ: <code>/addsudo [user_id]</code>", parse_mode=ParseMode.HTML)
        return
    try:
        user_id = int(context.args[0])
        sudo_col.update_one({"user_id": user_id}, {"$set": {"added_at": datetime.utcnow()}}, upsert=True)
        await update.message.reply_text(f"👑 User <code>{user_id}</code> အား Sudo Admin အဖြစ် သတ်မှတ်လိုက်ပါပြီ။", parse_mode=ParseMode.HTML)
    except ValueError:
        await update.message.reply_text("❌ User ID ဂဏန်းဖြစ်ရပါမည်။")

async def del_sudo_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await is_owner(update.effective_user.id): return
    if not context.args:
        await update.message.reply_text("အသုံးပြုပုံ: <code>/delsudo [user_id]</code>", parse_mode=ParseMode.HTML)
        return
    try:
        user_id = int(context.args[0])
        sudo_col.delete_one({"user_id": user_id})
        await update.message.reply_text(f"🗑️ User <code>{user_id}</code> အား Sudo မှ ဖယ်ရှားလိုက်ပါပြီ။", parse_mode=ParseMode.HTML)
    except ValueError:
        await update.message.reply_text("❌ User ID ဂဏန်းဖြစ်ရပါမည်။")

async def list_sudo_users(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await is_admin_or_owner(update.effective_user.id): return
    sudos = list(sudo_col.find({}))
    sudo_list_str = "\n".join([f"  • <code>{s['user_id']}</code>" for s in sudos])
    text = f"👑 <b>Sudo Admins List</b>\n\n{sudo_list_str if sudo_list_str else '  • Sudo Admin မရှိသေးပါ။'}"
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)

async def set_vip_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await is_admin_or_owner(update.effective_user.id): return
    if not context.args:
        await update.message.reply_text("အသုံးပြုပုံ: <code>/setvip [user_id]</code>", parse_mode=ParseMode.HTML)
        return
    try:
        user_id = int(context.args[0])
        users_col.update_one({"user_id": user_id}, {"$set": {"is_vip": True}}, upsert=True)
        await update.message.reply_text(f"🌟 User <code>{user_id}</code> အား VIP သတ်မှတ်လိုက်ပါပြီ။", parse_mode=ParseMode.HTML)
    except ValueError:
        await update.message.reply_text("❌ User ID ဂဏန်းဖြစ်ရပါမည်။")

async def unset_vip_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await is_admin_or_owner(update.effective_user.id): return
    if not context.args:
        await update.message.reply_text("အသုံးပြုပုံ: <code>/unsetvip [user_id]</code>", parse_mode=ParseMode.HTML)
        return
    try:
        user_id = int(context.args[0])
        users_col.update_one({"user_id": user_id}, {"$set": {"is_vip": False}})
        await update.message.reply_text(f"⚪ User <code>{user_id}</code> ၏ VIP Status ကို ရုပ်သိမ်းလိုက်ပါပြီ။", parse_mode=ParseMode.HTML)
    except ValueError:
        await update.message.reply_text("❌ User ID ဂဏန်းဖြစ်ရပါမည်။")

async def list_vip_users(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await is_admin_or_owner(update.effective_user.id): return
    vips = list(users_col.find({"is_vip": True}))
    vip_str = "\n".join([f"  • <code>{v.get('user_id')}</code>" for v in vips])
    text = f"🌟 <b>VIP Users List ({len(vips)}):</b>\n\n{vip_str if vip_str else '  • VIP User မရှိသေးပါ။'}"
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)

async def blacklist_user_global(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await is_admin_or_owner(update.effective_user.id): return
    if not context.args:
        await update.message.reply_text("အသုံးပြုပုံ: <code>/blockuser [user_id] [reason]</code>", parse_mode=ParseMode.HTML)
        return
    try:
        target_id = int(context.args[0])
        reason = " ".join(context.args[1:]) if len(context.args) > 1 else "No reason provided."
        blacklist_col.update_one({"entity_id": target_id, "type": "user"}, {"$set": {"reason": reason, "blocked_by": update.effective_user.id, "at": datetime.utcnow()}}, upsert=True)
        users_col.update_one({"user_id": target_id}, {"$set": {"is_gbanned": True}})
        await update.message.reply_text(f"🚫 User <code>{target_id}</code> ကို Blacklist ပြုလုပ်လိုက်ပါပြီ။", parse_mode=ParseMode.HTML)
    except ValueError:
        await update.message.reply_text("❌ User ID ဂဏန်းဖြစ်ရပါမည်။")

async def unblacklist_user_global(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await is_admin_or_owner(update.effective_user.id): return
    if not context.args:
        await update.message.reply_text("အသုံးပြုပုံ: <code>/unblockuser [user_id]</code>", parse_mode=ParseMode.HTML)
        return
    try:
        target_id = int(context.args[0])
        blacklist_col.delete_one({"entity_id": target_id, "type": "user"})
        users_col.update_one({"user_id": target_id}, {"$set": {"is_gbanned": False}})
        await update.message.reply_text(f"✅ User <code>{target_id}</code> Unblocked ဖြစ်သွားပါပြီ။", parse_mode=ParseMode.HTML)
    except ValueError:
        await update.message.reply_text("❌ User ID ဂဏန်းဖြစ်ရပါမည်။")

async def blacklist_group(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await is_admin_or_owner(update.effective_user.id): return
    if not context.args:
        await update.message.reply_text("အသုံးပြုပုံ: <code>/blockgroup [chat_id]</code>", parse_mode=ParseMode.HTML)
        return
    try:
        chat_id = int(context.args[0])
        blacklist_col.update_one({"entity_id": chat_id, "type": "group"}, {"$set": {"blocked_by": update.effective_user.id, "at": datetime.utcnow()}}, upsert=True)
        chats_col.delete_one({"chat_id": chat_id})
        try:
            await context.bot.leave_chat(chat_id)
        except Exception:
            pass
        await update.message.reply_text(f"🚫 Group <code>{chat_id}</code> ကို Blocked & Left ပြုလုပ်လိုက်ပါပြီ။", parse_mode=ParseMode.HTML)
    except ValueError:
        await update.message.reply_text("❌ Chat ID ဂဏန်း မှန်ကန်ပါစေ။")

async def emergency_lockdown(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await is_owner(update.effective_user.id): return
    current = system_col.find_one({"key": "lockdown"})
    new_state = not (current.get("status", False) if current else False)
    system_col.update_one({"key": "lockdown"}, {"$set": {"status": new_state}}, upsert=True)
    await update.message.reply_text("🚨 <b>EMERGENCY LOCKDOWN ACTIVATED!</b>" if new_state else "✅ <b>LOCKDOWN LIFTED!</b>", parse_mode=ParseMode.HTML)

# ══════════════════════════════════════════════════════════════════════════════
# 4. MAINTENANCE, CODES & BACKUP
# ══════════════════════════════════════════════════════════════════════════════

async def generate_gift_code(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await is_admin_or_owner(update.effective_user.id): return
    if len(context.args) < 3:
        await update.message.reply_text("အသုံးပြုပုံ: <code>/gencode [code] [coins] [max_uses]</code>", parse_mode=ParseMode.HTML)
        return
    try:
        code_name = context.args[0].upper()
        coins, max_uses = int(context.args[1]), int(context.args[2])
        codes_col.update_one({"code": code_name}, {"$set": {"coins": coins, "max_uses": max_uses, "used_count": 0, "used_by": [], "created_at": datetime.utcnow()}}, upsert=True)
        await update.message.reply_text(f"🎁 Code <code>{code_name}</code> (Coins: {coins:,} | Max Uses: {max_uses}) ထုတ်ပြီးပါပြီ!", parse_mode=ParseMode.HTML)
    except ValueError:
        await update.message.reply_text("❌ ဂဏန်းပမာဏ မှန်ကန်ပါစေ။")

async def clean_ghost_data(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await is_admin_or_owner(update.effective_user.id): return
    msg = await update.message.reply_text("🧹 <b>Ghost Data စစ်ဆေးနေပါသည်...</b>", parse_mode=ParseMode.HTML)

    valid_card_ids = set(cards_col.distinct("card_id"))
    valid_ids_legacy = set(cards_col.distinct("id"))
    all_valid = valid_card_ids.union(valid_ids_legacy)

    inv_cursor = inventory_col.find({})
    deleted_inv_count = 0
    orphan_ids = []

    for item in inv_cursor:
        c_id = item.get("card_id") or item.get("id")
        if c_id not in all_valid:
            orphan_ids.append(item["_id"])

    if orphan_ids:
        res = inventory_col.delete_many({"_id": {"$in": orphan_ids}})
        deleted_inv_count = res.deleted_count

    invalid_users = users_col.delete_many({"user_id": {"$exists": False}})

    text = (
        "✅ <b>Database Clean-up ပြီးစီးပါပြီ!</b>\n\n"
        f"🗑️️ ဖျက်ထုတ်လိုက်သော Inventory Cards: <b>{deleted_inv_count:,}</b>\n"
        f"🗑️ ရှင်းလင်းလိုက်သော User Records: <b>{invalid_users.deleted_count:,}</b>"
    )
    await msg.edit_text(text, parse_mode=ParseMode.HTML)

async def db_stats_detailed(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await is_admin_or_owner(update.effective_user.id): return
    msg = await update.message.reply_text("📊 <b>Economy Data တွက်ချက်နေပါသည်...</b>", parse_mode=ParseMode.HTML)

    pipeline = [{"$group": {"_id": "$rarity", "count": {"$sum": 1}}}, {"$sort": {"count": -1}}]
    rarity_counts = list(cards_col.aggregate(pipeline))
    rarity_str = "\n".join([f"  • {doc['_id']}: <b>{doc['count']:,}</b>" for doc in rarity_counts])

    coin_pipeline = [{"$group": {"_id": None, "total_coins": {"$sum": "$balance"}}}]
    coin_res = list(users_col.aggregate(coin_pipeline))
    total_coins = coin_res[0]["total_coins"] if coin_res else 0

    text = (
        "📈 <b>Game Economy Analytics</b>\n\n"
        f"💰 <b>Total Coins:</b> <code>{total_coins:,}</code>\n\n"
        f"💎 <b>Card Rarity Distribution:</b>\n{rarity_str if rarity_str else '  • Data မရှိပါ'}"
    )
    await msg.edit_text(text, parse_mode=ParseMode.HTML)

async def full_zip_backup(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await is_owner(update.effective_user.id): return
    msg = await update.message.reply_text("📦 <b>Full Zip Backup ပြုလုပ်နေပါသည်...</b>", parse_mode=ParseMode.HTML)
    try:
        zip_buffer = io.BytesIO()
        cols = {"users": users_col, "chats": chats_col, "cards": cards_col, "inventory": inventory_col, "codes": codes_col}
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            for name, col in cols.items():
                data = list(col.find({}, {"_id": 0}))
                zip_file.writestr(f"{name}.json", json.dumps(data, indent=2, default=str, ensure_ascii=False))
        zip_buffer.seek(0)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        await context.bot.send_document(chat_id=update.effective_chat.id, document=InputFile(zip_buffer, filename=f"backup_{timestamp}.zip"))
        await msg.delete()
    except Exception as e:
        await msg.edit_text(f"❌ Backup Error: {e}")

# ══════════════════════════════════════════════════════════════════════════════
# 5. VPS, LOGS, SHELL & BROADCAST
# ══════════════════════════════════════════════════════════════════════════════

async def vps_status_monitor(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await is_admin_or_owner(update.effective_user.id): return
    cpu, mem, disk = psutil.cpu_percent(interval=1), psutil.virtual_memory(), psutil.disk_usage('/')
    bot_ram = psutil.Process(os.getpid()).memory_info().rss / (1024 * 1024)
    await update.message.reply_text(f"🖥️ <b>VPS Monitor</b>\nCPU: <b>{cpu}%</b>\nRAM: <b>{mem.percent}%</b> (Bot: {bot_ram:.2f} MB)\nDisk Free: <b>{disk.free // (1024**3):,} GB</b>", parse_mode=ParseMode.HTML)

async def broadcast_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await is_admin_or_owner(update.effective_user.id) or not update.message.reply_to_message:
        await update.message.reply_text("⚠️ Reply to a message with <code>/broadcast</code>", parse_mode=ParseMode.HTML)
        return
    chats = list(chats_col.find({}))
    msg = await update.message.reply_text(f"📢 Broadcasting to {len(chats)} chats...", parse_mode=ParseMode.HTML)
    success, failed = 0, 0
    for chat in chats:
        try:
            await update.message.reply_to_message.copy(chat_id=chat.get("chat_id"))
            success += 1
            await asyncio.sleep(0.05)
        except Exception:
            failed += 1
            chats_col.delete_one({"chat_id": chat.get("chat_id")})
    await msg.edit_text(f"✅ Complete! Success: {success} | Failed: {failed}", parse_mode=ParseMode.HTML)

async def execute_shell_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await is_owner(update.effective_user.id) or not context.args: return
    cmd = " ".join(context.args)
    msg = await update.message.reply_text(f"⚡ Executing: <code>{escape(cmd)}</code>...", parse_mode=ParseMode.HTML)
    try:
        proc = await asyncio.create_subprocess_shell(cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        stdout, stderr = await proc.communicate()
        out = stdout.decode().strip() or stderr.decode().strip() or "No Output."
        await msg.edit_text(f"🖥️ <b>Output:</b>\n<code>{escape(out[:3500])}</code>", parse_mode=ParseMode.HTML)
    except Exception as e:
        await msg.edit_text(f"❌ Error: {e}")

# ══════════════════════════════════════════════════════════════════════════════
# HANDLER REGISTRATION REGISTRY
# ══════════════════════════════════════════════════════════════════════════════

def get_master_owner_handlers():
    return [
        # Owner Help
        CommandHandler("ownerhelp", owner_help_command),
        CommandHandler("adminhelp", owner_help_command),

        # Card Management Handlers
        CommandHandler("addcard", add_card_command),
        CommandHandler("delcard", delete_card_command),
        CommandHandler("cardinfo", card_info_command),

        # Economy & Users
        CommandHandler("addcoins", add_coins_command),
        CommandHandler("rmcoins", remove_coins_command),
        CommandHandler("addgems", add_gems_command),
        CommandHandler("givecard", give_card_command),
        CommandHandler("takecard", take_card_command),
        CommandHandler("transferinv", transfer_inventory),

        # Sudo & VIP
        CommandHandler("addsudo", add_sudo_user),
        CommandHandler("delsudo", del_sudo_user),
        CommandHandler("sudolist", list_sudo_users),
        CommandHandler("setvip", set_vip_user),
        CommandHandler("unsetvip", unset_vip_user),
        CommandHandler("viplist", list_vip_users),

        # Blacklist & Lockdown
        CommandHandler("blockuser", blacklist_user_global),
        CommandHandler("unblockuser", unblacklist_user_global),
        CommandHandler("blockgroup", blacklist_group),
        CommandHandler("lockdown", emergency_lockdown),

        # Maintenance & Backup
        CommandHandler("gencode", generate_gift_code),
        CommandHandler("cleanghost", clean_ghost_data),
        CommandHandler("dbstats", db_stats_detailed),
        CommandHandler("zipbackup", full_zip_backup),

        # VPS, Broadcast & Shell
        CommandHandler("vps", vps_status_monitor),
        CommandHandler("broadcast", broadcast_message),
        CommandHandler("shell", execute_shell_command),
    ]
