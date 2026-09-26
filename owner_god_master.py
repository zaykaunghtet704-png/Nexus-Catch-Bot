import sys
import os
import io
import time
import json
import logging
import asyncio
import zipfile
import platform
import psutil
from datetime import datetime, timedelta
from html import escape

from telegram import Update, InputFile, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler
from telegram.error import TelegramError, Forbidden, BadRequest

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
    OWNER_ID = 123456789

logger = logging.getLogger(__name__)

# ── Helper Permission Checks ──────────────────────────────────────────────────

async def is_owner(user_id: int) -> bool:
    return user_id == OWNER_ID

async def is_admin_or_owner(user_id: int) -> bool:
    if user_id == OWNER_ID:
        return True
    sudo = await sudo_col.find_one({"user_id": user_id})
    return bool(sudo)

# ══════════════════════════════════════════════════════════════════════════════
# 1. DATABASE MAINTENANCE & ECONOMY MANAGEMENT
# ══════════════════════════════════════════════════════════════════════════════

async def clean_ghost_data(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Database ထဲတွင် မရှိတော့သော Card ID သို့မဟုတ် User မရှိတော့သော Inventory များကို ရှင်းလင်းရန်"""
    if not await is_admin_or_owner(update.effective_user.id): return

    msg = await update.message.reply_text("🧹 <b>Ghost Data & Orphan Records စစ်ဆေး ရှင်းလင်းနေပါသည်...</b>", parse_mode=ParseMode.HTML)

    valid_card_ids = set(await cards_col.distinct("card_id"))
    valid_ids_legacy = set(await cards_col.distinct("id"))
    all_valid = valid_card_ids.union(valid_ids_legacy)

    inv_cursor = inventory_col.find({})
    deleted_inv_count = 0
    orphan_ids = []

    async for item in inv_cursor:
        c_id = item.get("card_id") or item.get("id")
        if c_id not in all_valid:
            orphan_ids.append(item["_id"])

    if orphan_ids:
        res = await inventory_col.delete_many({"_id": {"$in": orphan_ids}})
        deleted_inv_count = res.deleted_count

    invalid_users = await users_col.delete_many({"user_id": {"$exists": False}})

    text = (
        "✅ <b>Database Clean-up ပြီးစီးပါပြီ!</b>\n\n"
        f"🗑️ ဖျက်ထုတ်လိုက်သော တည်ရှိမှုမရှိသည့် Inventory Cards: <b>{deleted_inv_count:,}</b>\n"
        f"🗑️ ရှင်းလင်းလိုက်သော ပျက်စီးနေသည့် User Records: <b>{invalid_users.deleted_count:,}</b>"
    )
    await msg.edit_text(text, parse_mode=ParseMode.HTML)

async def db_stats_detailed(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Database ၏ Rarity အလိုက်နှင့် Total Coin Economy Circulation များကို ထုတ်ကြည့်ရန်"""
    if not await is_admin_or_owner(update.effective_user.id): return

    msg = await update.message.reply_text("📊 <b>Economy Analytical Data များကို တွက်ချက်နေပါသည်...</b>", parse_mode=ParseMode.HTML)

    pipeline = [
        {"$group": {"_id": "$rarity", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}
    ]
    rarity_counts = await cards_col.aggregate(pipeline).to_list(length=None)
    rarity_str = "\n".join([f"  • {doc['_id']}: <b>{doc['count']:,}</b>" for doc in rarity_counts])

    coin_pipeline = [{"$group": {"_id": None, "total_coins": {"$sum": "$coins"}}}]
    coin_res = await users_col.aggregate(coin_pipeline).to_list(length=1)
    total_coins_in_game = coin_res[0]["total_coins"] if coin_res else 0

    text = (
        "📈 <b>Game Economy & Rarity Analytics</b>\n\n"
        f"💰 <b>Total Coins in Circulation:</b> <code>{total_coins_in_game:,}</code>\n\n"
        f"💎 <b>Card Rarity Distribution (Database):</b>\n{rarity_str if rarity_str else '  • Data မရှိပါ'}"
    )
    await msg.edit_text(text, parse_mode=ParseMode.HTML)

async def reset_economy(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """User အားလုံး၏ Coins များကို ပမာဏတစ်ခုအထိ လျှော့ချရန် (Inflation ထိန်းညှိခြင်း)"""
    if not await is_owner(update.effective_user.id): return
    if not context.args:
        await update.message.reply_text("အသုံးပြုပုံ: <code>/wipecoins [percentage_to_keep]</code>\nဥပမာ: <code>/wipecoins 50</code>", parse_mode=ParseMode.HTML)
        return

    try:
        pct = float(context.args[0]) / 100.0
        msg = await update.message.reply_text("⚠️ <b>Coins ပြန်လည် ထိန်းညှိနေပါသည်...</b>", parse_mode=ParseMode.HTML)
        
        users = await users_col.find({"coins": {"$gt": 0}}).to_list(length=None)
        updated = 0
        for u in users:
            new_coins = int(u.get("coins", 0) * pct)
            await users_col.update_one({"_id": u["_id"]}, {"$set": {"coins": new_coins}})
            updated += 1

        await msg.edit_text(f"✅ Users <b>{updated:,}</b> ဦး၏ Coins များကို <b>{context.args[0]}%</b> သို့ ပြန်လည် ထိန်းညှိလိုက်ပါပြီ။", parse_mode=ParseMode.HTML)
    except ValueError:
        await update.message.reply_text("❌ ရာခိုင်နှုန်းကို ဂဏန်းဖြင့်သာ ရိုက်ထည့်ပါ။")

async def set_custom_drop_rate(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Group သီးသန့် ကတ်ကျနိုင်ခြေ Rate (Percentage %) ကို ပြောင်းလဲရန်"""
    if not await is_admin_or_owner(update.effective_user.id): return
    if len(context.args) < 2:
        await update.message.reply_text("အသုံးပြုပုံ: <code>/setdroprate [chat_id] [rate_percentage (1-100)]</code>", parse_mode=ParseMode.HTML)
        return

    try:
        chat_id = int(context.args[0])
        rate = max(1, min(100, float(context.args[1])))

        await chats_col.update_one({"chat_id": chat_id}, {"$set": {"drop_rate": rate}}, upsert=True)
        await update.message.reply_text(f"🎯 Group <code>{chat_id}</code> ၏ Drop Rate ကို <b>{rate}%</b> ဟု သတ်မှတ်လိုက်ပါပြီ။", parse_mode=ParseMode.HTML)
    except ValueError:
        await update.message.reply_text("❌ Chat ID နှင့် Rate ဂဏန်း မှန်ကန်ပါစေ။")

async def transfer_inventory(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """User တစ်ဦး၏ Inventory နှင့် Coins များကို အခြား User ထံသို့ လွှဲပြောင်းပေးရန်"""
    if not await is_owner(update.effective_user.id): return
    if len(context.args) < 2:
        await update.message.reply_text("အသုံးပြုပုံ: <code>/transferinv [from_user_id] [to_user_id]</code>", parse_mode=ParseMode.HTML)
        return

    try:
        from_id = int(context.args[0])
        to_id = int(context.args[1])

        res = await inventory_col.update_many({"user_id": from_id}, {"$set": {"user_id": to_id}})
        from_user = await users_col.find_one({"user_id": from_id})
        if from_user:
            coins = from_user.get("coins", 0)
            xp = from_user.get("xp", 0)
            await users_col.update_one({"user_id": to_id}, {"$inc": {"coins": coins, "xp": xp}}, upsert=True)
            await users_col.update_one({"user_id": from_id}, {"$set": {"coins": 0, "xp": 0}})

        await update.message.reply_text(
            f"📦 <b>Inventory & Economy Transferred!</b>\n"
            f"👤 From: <code>{from_id}</code> ➔ To: <code>{to_id}</code>\n"
            f"🎴 ပြောင်းရွှေ့လိုက်သော ကတ်များ: <b>{res.modified_count:,}</b>",
            parse_mode=ParseMode.HTML
        )
    except ValueError:
        await update.message.reply_text("❌ User ID ဂဏန်း မှန်ကန်ပါစေ။")

# ══════════════════════════════════════════════════════════════════════════════
# 2. SECURITY, BLACKLISTS & EMERGENCY PROTOCOLS
# ══════════════════════════════════════════════════════════════════════════════

async def blacklist_user_global(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """User အား Bot စနစ်တစ်ခုလုံးမှ အပြီးအပိုင် ပိတ်ပင်ရန်"""
    if not await is_admin_or_owner(update.effective_user.id): return
    if not context.args:
        await update.message.reply_text("အသုံးပြုပုံ: <code>/blockuser [user_id] [reason]</code>", parse_mode=ParseMode.HTML)
        return

    try:
        target_id = int(context.args[0])
        reason = " ".join(context.args[1:]) if len(context.args) > 1 else "No reason provided."

        await blacklist_col.update_one(
            {"entity_id": target_id, "type": "user"},
            {"$set": {"reason": reason, "blocked_by": update.effective_user.id, "at": datetime.utcnow()}},
            upsert=True
        )
        await users_col.update_one({"user_id": target_id}, {"$set": {"is_banned": True}})

        await update.message.reply_text(f"🚫 User <code>{target_id}</code> အား Global Blacklisted လုပ်လိုက်ပါပြီ။", parse_mode=ParseMode.HTML)
    except ValueError:
        await update.message.reply_text("❌ User ID ဂဏန်းဖြစ်ရပါမည်။")

async def unblacklist_user_global(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """User အား Blacklist မှ ပြန်လည် ဖယ်ရှားပေးရန်"""
    if not await is_admin_or_owner(update.effective_user.id): return
    if not context.args:
        await update.message.reply_text("အသုံးပြုပုံ: <code>/unblockuser [user_id]</code>", parse_mode=ParseMode.HTML)
        return

    try:
        target_id = int(context.args[0])
        await blacklist_col.delete_one({"entity_id": target_id, "type": "user"})
        await users_col.update_one({"user_id": target_id}, {"$set": {"is_banned": False}})

        await update.message.reply_text(f"✅ User <code>{target_id}</code> အား Blacklist မှ ဖယ်ရှားလိုက်ပါပြီ။", parse_mode=ParseMode.HTML)
    except ValueError:
        await update.message.reply_text("❌ User ID ဂဏန်းဖြစ်ရပါမည်။")

async def blacklist_group(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Group အား Blacklist လုပ်ပြီး Bot ကို အလိုအလျောက် ထွက်ခွာစေရန်"""
    if not await is_admin_or_owner(update.effective_user.id): return
    if not context.args:
        await update.message.reply_text("အသုံးပြုပုံ: <code>/blockgroup [chat_id]</code>", parse_mode=ParseMode.HTML)
        return

    try:
        chat_id = int(context.args[0])
        await blacklist_col.update_one(
            {"entity_id": chat_id, "type": "group"},
            {"$set": {"blocked_by": update.effective_user.id, "at": datetime.utcnow()}},
            upsert=True
        )
        await chats_col.delete_one({"chat_id": chat_id})
        try:
            await context.bot.leave_chat(chat_id)
        except Exception:
            pass

        await update.message.reply_text(f"🚫 Group <code>{chat_id}</code> အား Blacklist လုပ်ပြီး ထွက်ခွာလိုက်ပါပြီ။", parse_mode=ParseMode.HTML)
    except ValueError:
        await update.message.reply_text("❌ Chat ID ဂဏန်း မှန်ကန်ပါစေ။")

async def emergency_lockdown(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """အရေးပေါ် အခြေအနေတွင် Bot Commands များကို ခဏတာ ပိတ်ပင်ရန်"""
    if not await is_owner(update.effective_user.id): return

    current = await system_col.find_one({"key": "lockdown"})
    new_state = not (current.get("status", False) if current else False)

    await system_col.update_one({"key": "lockdown"}, {"$set": {"status": new_state}}, upsert=True)
    state_msg = "🚨 <b>EMERGENCY LOCKDOWN ACTIVATED!</b>" if new_state else "✅ <b>LOCKDOWN LIFTED!</b>"
    await update.message.reply_text(state_msg, parse_mode=ParseMode.HTML)

# ══════════════════════════════════════════════════════════════════════════════
# 3. BACKUPS, ANALYTICS & CODE GENERATOR
# ══════════════════════════════════════════════════════════════════════════════

async def full_zip_backup(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Database Collections အားလုံးကို JSON ဖြင့် Zip ပြုလုပ်၍ ပို့ပေးရန်"""
    if not await is_owner(update.effective_user.id): return

    msg = await update.message.reply_text("📦 <b>Full Zip Backup ပြုလုပ်နေပါသည်...</b>", parse_mode=ParseMode.HTML)
    try:
        zip_buffer = io.BytesIO()
        collections_to_backup = {
            "users": users_col, "chats": chats_col, "cards": cards_col,
            "inventory": inventory_col, "codes": codes_col, "system": system_col
        }

        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            for name, col in collections_to_backup.items():
                data = await col.find({}, {"_id": 0}).to_list(length=None)
                json_str = json.dumps(data, indent=2, default=str, ensure_ascii=False)
                zip_file.writestr(f"{name}.json", json_str)

        zip_buffer.seek(0)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        await context.bot.send_document(
            chat_id=update.effective_chat.id,
            document=InputFile(zip_buffer, filename=f"bot_full_backup_{timestamp}.zip"),
            caption=f"📂 <b>Full System Backup Archive</b>\n⏱️ Date: <code>{timestamp}</code>",
            parse_mode=ParseMode.HTML
        )
        await msg.delete()
    except Exception as e:
        await msg.edit_text(f"❌ Backup Error: {e}")

async def active_users_stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Active Users နှင့် Retention Rate စစ်ဆေးရန်"""
    if not await is_admin_or_owner(update.effective_user.id): return

    now = datetime.utcnow()
    active_24h = await users_col.count_documents({"last_active": {"$gte": now - timedelta(hours=24)}})
    active_7d = await users_col.count_documents({"last_active": {"$gte": now - timedelta(days=7)}})
    total_users = await users_col.count_documents({})
    retention_rate = (active_7d / total_users * 100) if total_users > 0 else 0

    text = (
        "📊 <b>User Engagement & Activity Report</b>\n\n"
        f"👥 စုစုပေါင်း Users: <b>{total_users:,}</b>\n"
        f"⚡ Active (Last 24 Hours): <b>{active_24h:,}</b>\n"
        f"📅 Active (Last 7 Days): <b>{active_7d:,}</b>\n"
        f"🔥 7-Day Retention Rate: <b>{retention_rate:.2f}%</b>"
    )
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)

async def generate_gift_code(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Coins ပါဝင်သော Redeem Code ဖန်တီးရန်"""
    if not await is_admin_or_owner(update.effective_user.id): return
    if len(context.args) < 3:
        await update.message.reply_text("အသုံးပြုပုံ: <code>/gencode [code_name] [coins] [max_uses]</code>", parse_mode=ParseMode.HTML)
        return

    code_name = context.args[0].upper()
    try:
        coins = int(context.args[1])
        max_uses = int(context.args[2])

        await codes_col.update_one(
            {"code": code_name},
            {"$set": {"coins": coins, "max_uses": max_uses, "used_count": 0, "used_by": [], "created_at": datetime.utcnow()}},
            upsert=True
        )
        await update.message.reply_text(f"🎁 Redeem Code <code>{code_name}</code> (Coins: {coins:,}) ဖန်တီးပြီးပါပြီ။", parse_mode=ParseMode.HTML)
    except ValueError:
        await update.message.reply_text("❌ ဂဏန်းပမာဏ မှန်ကန်ပါစေ။")

# ══════════════════════════════════════════════════════════════════════════════
# 4. VPS MONITOR, LOGS, SHELL & BROADCAST PIN
# ══════════════════════════════════════════════════════════════════════════════

async def vps_status_monitor(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """VPS Hardware Status & Resource Monitor"""
    if not await is_admin_or_owner(update.effective_user.id): return

    cpu_usage = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    process = psutil.Process(os.getpid())
    bot_ram_mb = process.memory_info().rss / (1024 * 1024)
    uptime_sec = time.time() - psutil.boot_time()

    text = (
        "🖥️ <b>System Hardware & Performance Monitor</b>\n\n"
        f"⏱️ <b>Uptime:</b> <code>{str(timedelta(seconds=int(uptime_sec)))}</code>\n"
        f"💻 <b>CPU Usage:</b> <code>{cpu_usage}%</code>\n"
        f"🧠 <b>RAM Usage:</b> <code>{memory.percent}%</code> (<b>{memory.used // (1024**2):,} MB</b>)\n"
        f"🤖 <b>Bot RAM:</b> <code>{bot_ram_mb:.2f} MB</code>\n"
        f"💾 <b>Disk Free:</b> <code>{disk.free // (1024**3):,} GB</code>"
    )
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)

async def get_latest_error_logs(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Bot Error Logs များကို ဖတ်ရှုရန်"""
    if not await is_owner(update.effective_user.id): return

    for log_path in ["bot.log", "error.log", "logs/bot.log"]:
        if os.path.exists(log_path):
            with open(log_path, "r", encoding="utf-8") as f:
                log_text = "".join(f.readlines()[-30:])
            await update.message.reply_text(f"📄 <b>Logs ({log_path}):</b>\n\n<code>{escape(log_text[-3500:])}</code>", parse_mode=ParseMode.HTML)
            return
    await update.message.reply_text("❌ Log File များ မတွေ့ရှိပါ။")

async def broadcast_pin_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Groups များသို့ Pin ဖြင့် Broadcast ပို့ရန်"""
    if not await is_owner(update.effective_user.id): return
    if not update.message.reply_to_message:
        await update.message.reply_text("⚠️ Broadcast ပို့လိုသော စာကို Reply လုပ်ပြီး <code>/broadcastpin</code> ဟု ရိုက်ပါ။", parse_mode=ParseMode.HTML)
        return

    chats = await chats_col.find({}).to_list(length=None)
    msg = await update.message.reply_text(f"📢 <b>Groups {len(chats)} ခုသို့ Broadcast ပို့နေပါသည်...</b>", parse_mode=ParseMode.HTML)
    success, failed = 0, 0
    reply_msg = update.message.reply_to_message

    for chat in chats:
        c_id = chat.get("chat_id")
        try:
            sent = await reply_msg.copy(chat_id=c_id)
            try:
                await context.bot.pin_chat_message(chat_id=c_id, message_id=sent.message_id)
            except Exception:
                pass
            success += 1
            await asyncio.sleep(0.05)
        except Exception:
            failed += 1
            await chats_col.delete_one({"chat_id": c_id})

    await msg.edit_text(f"✅ Broadcast Complete!\n🟢 Success: <b>{success:,}</b> | 🔴 Failed: <b>{failed:,}</b>", parse_mode=ParseMode.HTML)

async def execute_shell_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """VPS Terminal Commands များကို Telegram မှ Run ရန်"""
    if not await is_owner(update.effective_user.id): return
    if not context.args:
        await update.message.reply_text("အသုံးပြုပုံ: <code>/shell [command]</code>", parse_mode=ParseMode.HTML)
        return

    cmd = " ".join(context.args)
    msg = await update.message.reply_text(f"⚡ <b>Executing:</b> <code>{escape(cmd)}</code>...", parse_mode=ParseMode.HTML)
    try:
        proc = await asyncio.create_subprocess_shell(cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
        stdout, stderr = await proc.communicate()
        output = stdout.decode().strip() or stderr.decode().strip() or "No Output."
        await msg.edit_text(f"🖥️ <b>Output:</b>\n\n<code>{escape(output[:3500])}</code>", parse_mode=ParseMode.HTML)
    except Exception as e:
        await msg.edit_text(f"❌ Error: {e}")

# ══════════════════════════════════════════════════════════════════════════════
# 5. INTERACTIVE ADMIN DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════

async def admin_dashboard(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Interactive Control Panel Dashboard"""
    if not await is_admin_or_owner(update.effective_user.id): return

    maint = await system_col.find_one({"key": "maintenance"})
    lock = await system_col.find_one({"key": "lockdown"})
    
    text = (
        "🛠️ <b>Bot Owner Master Control Panel</b>\n\n"
        f"🔧 Maintenance: <b>{'ON' if (maint and maint.get('value')) else 'OFF'}</b>\n"
        f"🚨 Lockdown: <b>{'ON' if (lock and lock.get('status')) else 'OFF'}</b>"
    )
    keyboard = [
        [InlineKeyboardButton("🛠️ Toggle Maint", callback_data="dash_maint"), InlineKeyboardButton("🚨 Toggle Lock", callback_data="dash_lock")],
        [InlineKeyboardButton("📊 Stats", callback_data="dash_stats"), InlineKeyboardButton("🧹 Clear Cache", callback_data="dash_cache")]
    ]
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)

async def dashboard_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if not await is_admin_or_owner(query.from_user.id):
        await query.answer("❌ ခွင့်ပြုချက်မရှိပါ။", show_alert=True)
        return
    await query.answer()

    if query.data == "dash_maint":
        cur = await system_col.find_one({"key": "maintenance"})
        val = not (cur.get("value", False) if cur else False)
        await system_col.update_one({"key": "maintenance"}, {"$set": {"value": val}}, upsert=True)
        await query.edit_message_text(f"🛠️ Maintenance Mode: <b>{'ON' if val else 'OFF'}</b>", parse_mode=ParseMode.HTML)
    elif query.data == "dash_lock":
        cur = await system_col.find_one({"key": "lockdown"})
        val = not (cur.get("status", False) if cur else False)
        await system_col.update_one({"key": "lockdown"}, {"$set": {"status": val}}, upsert=True)
        await query.edit_message_text(f"🚨 Lockdown Mode: <b>{'ON' if val else 'OFF'}</b>", parse_mode=ParseMode.HTML)
    elif query.data == "dash_stats":
        u = await users_col.count_documents({})
        g = await chats_col.count_documents({})
        await query.edit_message_text(f"📊 Stats — Users: <b>{u:,}</b> | Groups: <b>{g:,}</b>", parse_mode=ParseMode.HTML)
    elif query.data == "dash_cache":
        import gc
        await query.edit_message_text(f"🧹 Cache cleared. Objects: <b>{gc.collect()}</b>", parse_mode=ParseMode.HTML)

# ══════════════════════════════════════════════════════════════════════════════
# HANDLER REGISTRATION REGISTRY
# ══════════════════════════════════════════════════════════════════════════════

def get_master_owner_handlers():
    return [
        # Database & Economy
        CommandHandler("cleanghost", clean_ghost_data, block=False),
        CommandHandler("dbstats", db_stats_detailed, block=False),
        CommandHandler("wipecoins", reset_economy, block=False),
        CommandHandler("setdroprate", set_custom_drop_rate, block=False),
        CommandHandler("transferinv", transfer_inventory, block=False),

        # Security & Blacklists
        CommandHandler("blockuser", blacklist_user_global, block=False),
        CommandHandler("unblockuser", unblacklist_user_global, block=False),
        CommandHandler("blockgroup", blacklist_group, block=False),
        CommandHandler("lockdown", emergency_lockdown, block=False),

        # Backup, Analytics & Codes
        CommandHandler("zipbackup", full_zip_backup, block=False),
        CommandHandler("activeusers", active_users_stats, block=False),
        CommandHandler("gencode", generate_gift_code, block=False),

        # VPS, Logs, Shell & Broadcast
        CommandHandler("vps", vps_status_monitor, block=False),
        CommandHandler("sysinfo", vps_status_monitor, block=False),
        CommandHandler("logs", get_latest_error_logs, block=False),
        CommandHandler("broadcastpin", broadcast_pin_message, block=False),
        CommandHandler("shell", execute_shell_command, block=False),
        CommandHandler("exec", execute_shell_command, block=False),

        # Dashboard & Control Panel
        CommandHandler("admindash", admin_dashboard, block=False),
        CallbackQueryHandler(dashboard_callback, pattern="^dash_")
    ]
