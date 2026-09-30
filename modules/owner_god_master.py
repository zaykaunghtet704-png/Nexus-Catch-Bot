"""
modules/owner_god_master.py - Admin, Owner & System Management
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
        await msg.reply_text(
            "⚠️ <b>ကျေးဇူးပြု၍ ကတ်ပုံရိပ် (Photo) ကို Reply လုပ်ပြီးမှ Command ရိုက်ပါ!</b>\n\n"
            "<b>အသုံးပြုပုံ:</b>\n<code>/addcard [card_id] [name] | [anime] | [rarity]</code>\n\n"
            "<b>ဥပမာ:</b>\n<code>/addcard c001 Rem | Re:Zero | ⚪ Common</code>",
            parse_mode=ParseMode.HTML
        )
        return

    text_args = " ".join(context.args)
    if not text_args or "|" not in text_args:
        await msg.reply_text(
            "❌ <b>Format မမှန်ပါ။</b>\n\n"
            "<b>အသုံးပြုပုံ:</b> <code>/addcard [card_id] [name] | [anime] | [rarity]</code>\n"
            "<b>ဥပမာ:</b> <code>/addcard c001 Rem | Re:Zero | ⚪ Common</code>",
            parse_mode=ParseMode.HTML
        )
        return

    try:
        parts = text_args.split("|")
        first_part = parts[0].strip().split(maxsplit=1)
        if len(first_part) < 2:
            await msg.reply_text("❌ Card ID နှင့် Name ကို သီးခြားခွဲရေးပေးပါ။ (ဥပမာ: <code>c001 Rem</code>)", parse_mode=ParseMode.HTML)
            return

        card_id = first_part[0].strip()
        card_name = first_part[1].strip()
        anime = parts[1].strip() if len(parts) > 1 else "Unknown Anime"
        rarity = parts[2].strip() if len(parts) > 2 else "⚪ Common"

        existing = cards_col.find_one({"$or": [{"card_id": card_id}, {"id": card_id}]})
        if existing:
            await msg.reply_text(f"⚠️ Card ID <code>{card_id}</code> မှာ Database ထဲတွင် ရှိပြီးသားဖြစ်ပါသည်။", parse_mode=ParseMode.HTML)
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
            f"🎉 <b>ကတ်အသစ် အောင်မြင်စွာ ထည့်သွင်းလိုက်ပါပြီ!</b>\n\n"
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
        await update.message.reply_text(f"🗑️ Card ID <code>{card_id}</code> ကို Database မှ ဖျက်လိုက်ပါပြီ။", parse_mode=ParseMode.HTML)
    else:
        await update.message.reply_text(f"❌ Card ID <code>{card_id}</code> ကို ရှာမတွေ့ပါ။", parse_mode=ParseMode.HTML)

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
# 2. SYSTEM & ECONOMY MANAGEMENT
# ══════════════════════════════════════════════════════════════════════════════

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
        f"🗑️ ဖျက်ထုတ်လိုက်သော Inventory Cards: <b>{deleted_inv_count:,}</b>\n"
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

# ══════════════════════════════════════════════════════════════════════════════
# 3. SECURITY, SUDOS, VIP & BLACKLISTS
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
        await update.message.reply_text(f"🗑️ User <code>{user_id}</code> အား Sudo စာရင်းမှ ဖယ်ရှားလိုက်ပါပြီ။", parse_mode=ParseMode.HTML)
    except ValueError:
        await update.message.reply_text("❌ User ID ဂဏန်းဖြစ်ရပါမည်။")

async def list_sudo_users(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await is_admin_or_owner(update.effective_user.id): return
    sudos = list(sudo_col.find({}))
    sudo_list_str = "\n".join([f"  • <code>{s['user_id']}</code>" for s in sudos])
    text = f"👑 <b>Sudo Admins List</b>\n\n{sudo_list_str if sudo_list_str else '  • Sudo Admin မရှိသေးပါ။'}"
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)

# ══════════════════════════════════════════════════════════════════════════════
# 4. BACKUPS & TOOLS
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

# ══════════════════════════════════════════════════════════════════════════════
# HANDLER REGISTRATION REGISTRY
# ══════════════════════════════════════════════════════════════════════════════

def get_master_owner_handlers():
    return [
        # Card Management Handlers
        CommandHandler("addcard", add_card_command),
        CommandHandler("delcard", delete_card_command),
        CommandHandler("cardinfo", card_info_command),

        # System & Economy
        CommandHandler("cleanghost", clean_ghost_data),
        CommandHandler("dbstats", db_stats_detailed),

        # Sudo
        CommandHandler("addsudo", add_sudo_user),
        CommandHandler("delsudo", del_sudo_user),
        CommandHandler("sudolist", list_sudo_users),

        # VPS & Broadcast
        CommandHandler("vps", vps_status_monitor),
        CommandHandler("broadcast", broadcast_message),
    ]
