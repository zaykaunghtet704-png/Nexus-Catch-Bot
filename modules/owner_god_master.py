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
    OWNER_ID = 123456789  # Fallback Owner ID

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
        f"🗑️ ဖျက်ထုတ်လိုက်သော Inventory Cards: <b>{deleted_inv_count:,}</b>\n"
        f"🗑️ ရှင်းလင်းလိုက်သော User Records: <b>{invalid_users.deleted_count:,}</b>"
    )
    await msg.edit_text(text, parse_mode=ParseMode.HTML)

async def db_stats_detailed(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await is_admin_or_owner(update.effective_user.id): return
    msg = await update.message.reply_text("📊 <b>Economy Analytical Data များကို တွက်ချက်နေပါသည်...</b>", parse_mode=ParseMode.HTML)

    pipeline = [{"$group": {"_id": "$rarity", "count": {"$sum": 1}}}, {"$sort": {"count": -1}}]
    rarity_counts = await cards_col.aggregate(pipeline).to_list(length=None)
    rarity_str = "\n".join([f"  • {doc['_id']}: <b>{doc['count']:,}</b>" for doc in rarity_counts])

    coin_pipeline = [{"$group": {"_id": None, "total_coins": {"$sum": "$coins"}}}]
    coin_res = await users_col.aggregate(coin_pipeline).to_list(length=1)
    total_coins = coin_res[0]["total_coins"] if coin_res else 0

    text = (
        "📈 <b>Game Economy & Rarity Analytics</b>\n\n"
        f"💰 <b>Total Coins in Circulation:</b> <code>{total_coins:,}</code>\n\n"
        f"💎 <b>Card Rarity Distribution:</b>\n{rarity_str if rarity_str else '  • Data မရှိပါ'}"
    )
    await msg.edit_text(text, parse_mode=ParseMode.HTML)

async def reset_economy(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await is_owner(update.effective_user.id): return
    if not context.args:
        await update.message.reply_text("အသုံးပြုပုံ: <code>/wipecoins [percentage_to_keep]</code>", parse_mode=ParseMode.HTML)
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
        await msg.edit_text(f"✅ Users <b>{updated:,}</b> ဦး၏ Coins များကို ထိန်းညှိပြီးပါပြီ။", parse_mode=ParseMode.HTML)
    except ValueError:
        await update.message.reply_text("❌ ရာခိုင်နှုန်းကို ဂဏန်းဖြင့်သာ ရိုက်ထည့်ပါ။")

async def set_custom_drop_rate(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await is_admin_or_owner(update.effective_user.id): return
    if len(context.args) < 2:
        await update.message.reply_text("အသုံးပြုပုံ: <code>/setdroprate [chat_id] [rate]</code>", parse_mode=ParseMode.HTML)
        return
    try:
        chat_id = int(context.args[0])
        rate = max(1, min(100, float(context.args[1])))
        await chats_col.update_one({"chat_id": chat_id}, {"$set": {"drop_rate": rate}}, upsert=True)
        await update.message.reply_text(f"🎯 Group <code>{chat_id}</code> Drop Rate: <b>{rate}%</b>", parse_mode=ParseMode.HTML)
    except ValueError:
        await update.message.reply_text("❌ Chat ID နှင့် Rate ဂဏန်း မှန်ကန်ပါစေ။")

async def transfer_inventory(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await is_owner(update.effective_user.id): return
    if len(context.args) < 2:
        await update.message.reply_text("အသုံးပြုပုံ: <code>/transferinv [from_user_id] [to_user_id]</code>", parse_mode=ParseMode.HTML)
        return
    try:
        from_id, to_id = int(context.args[0]), int(context.args[1])
        res = await inventory_col.update_many({"user_id": from_id}, {"$set": {"user_id": to_id}})
        from_user = await users_col.find_one({"user_id": from_id})
        if from_user:
            await users_col.update_one({"user_id": to_id}, {"$inc": {"coins": from_user.get("coins", 0), "xp": from_user.get("xp", 0)}}, upsert=True)
            await users_col.update_one({"user_id": from_id}, {"$set": {"coins": 0, "xp": 0}})
        await update.message.reply_text(f"📦 Inventory Transferred! Moved Cards: <b>{res.modified_count:,}</b>", parse_mode=ParseMode.HTML)
    except ValueError:
        await update.message.reply_text("❌ User ID ဂဏန်း မှန်ကန်ပါစေ။")

# ══════════════════════════════════════════════════════════════════════════════
# 2. SECURITY, SUDOS & BLACKLISTS
# ══════════════════════════════════════════════════════════════════════════════

async def add_sudo_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await is_owner(update.effective_user.id): return
    if not context.args:
        await update.message.reply_text("အသုံးပြုပုံ: <code>/addsudo [user_id]</code>", parse_mode=ParseMode.HTML)
        return
    try:
        user_id = int(context.args[0])
        await sudo_col.update_one({"user_id": user_id}, {"$set": {"added_at": datetime.utcnow()}}, upsert=True)
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
        await sudo_col.delete_one({"user_id": user_id})
        await update.message.reply_text(f"🗑️ User <code>{user_id}</code> အား Sudo စာရင်းမှ ဖယ်ရှားလိုက်ပါပြီ။", parse_mode=ParseMode.HTML)
    except ValueError:
        await update.message.reply_text("❌ User ID ဂဏန်းဖြစ်ရပါမည်။")

async def list_sudo_users(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await is_admin_or_owner(update.effective_user.id): return
    sudos = await sudo_col.find({}).to_list(length=None)
    sudo_list_str = "\n".join([f"  • <code>{s['user_id']}</code>" for s in sudos])
    text = f"👑 <b>Sudo Admins List</b>\n\n{sudo_list_str if sudo_list_str else '  • Sudo Admin မရှိသေးပါ။'}"
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)

async def blacklist_user_global(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await is_admin_or_owner(update.effective_user.id): return
    if not context.args:
        await update.message.reply_text("အသုံးပြုပုံ: <code>/blockuser [user_id] [reason]</code>", parse_mode=ParseMode.HTML)
        return
    try:
        target_id = int(context.args[0])
        reason = " ".join(context.args[1:]) if len(context.args) > 1 else "No reason provided."
        await blacklist_col.update_one({"entity_id": target_id, "type": "user"}, {"$set": {"reason": reason, "blocked_by": update.effective_user.id, "at": datetime.utcnow()}}, upsert=True)
        await users_col.update_one({"user_id": target_id}, {"$set": {"is_banned": True}})
        await update.message.reply_text(f"🚫 User <code>{target_id}</code> Blacklisted.", parse_mode=ParseMode.HTML)
    except ValueError:
        await update.message.reply_text("❌ User ID ဂဏန်းဖြစ်ရပါမည်။")

async def unblacklist_user_global(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await is_admin_or_owner(update.effective_user.id): return
    if not context.args:
        await update.message.reply_text("အသုံးပြုပုံ: <code>/unblockuser [user_id]</code>", parse_mode=ParseMode.HTML)
        return
    try:
        target_id = int(context.args[0])
        await blacklist_col.delete_one({"entity_id": target_id, "type": "user"})
        await users_col.update_one({"user_id": target_id}, {"$set": {"is_banned": False}})
        await update.message.reply_text(f"✅ User <code>{target_id}</code> Unblocked.", parse_mode=ParseMode.HTML)
    except ValueError:
        await update.message.reply_text("❌ User ID ဂဏန်းဖြစ်ရပါမည်။")

async def blacklist_group(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await is_admin_or_owner(update.effective_user.id): return
    if not context.args:
        await update.message.reply_text("အသုံးပြုပုံ: <code>/blockgroup [chat_id]</code>", parse_mode=ParseMode.HTML)
        return
    try:
        chat_id = int(context.args[0])
        await blacklist_col.update_one({"entity_id": chat_id, "type": "group"}, {"$set": {"blocked_by": update.effective_user.id, "at": datetime.utcnow()}}, upsert=True)
        await chats_col.delete_one({"chat_id": chat_id})
        try: await context.bot.leave_chat(chat_id)
        except Exception: pass
        await update.message.reply_text(f"🚫 Group <code>{chat_id}</code> Blocked & Left.", parse_mode=ParseMode.HTML)
    except ValueError:
        await update.message.reply_text("❌ Chat ID ဂဏန်း မှန်ကန်ပါစေ။")

async def emergency_lockdown(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await is_owner(update.effective_user.id): return
    current = await system_col.find_one({"key": "lockdown"})
    new_state = not (current.get("status", False) if current else False)
    await system_col.update_one({"key": "lockdown"}, {"$set": {"status": new_state}}, upsert=True)
    await update.message.reply_text("🚨 <b>EMERGENCY LOCKDOWN ACTIVATED!</b>" if new_state else "✅ <b>LOCKDOWN LIFTED!</b>", parse_mode=ParseMode.HTML)

# ══════════════════════════════════════════════════════════════════════════════
# 3. BACKUPS, CODES & REDEEM LOGIC
# ══════════════════════════════════════════════════════════════════════════════

async def full_zip_backup(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await is_owner(update.effective_user.id): return
    msg = await update.message.reply_text("📦 <b>Full Zip Backup ပြုလုပ်နေပါသည်...</b>", parse_mode=ParseMode.HTML)
    try:
        zip_buffer = io.BytesIO()
        cols = {"users": users_col, "chats": chats_col, "cards": cards_col, "inventory": inventory_col, "codes": codes_col, "system": system_col}
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            for name, col in cols.items():
                data = await col.find({}, {"_id": 0}).to_list(length=None)
                zip_file.writestr(f"{name}.json", json.dumps(data, indent=2, default=str, ensure_ascii=False))
        zip_buffer.seek(0)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        await context.bot.send_document(chat_id=update.effective_chat.id, document=InputFile(zip_buffer, filename=f"backup_{timestamp}.zip"))
        await msg.delete()
    except Exception as e:
        await msg.edit_text(f"❌ Backup Error: {e}")

async def generate_gift_code(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await is_admin_or_owner(update.effective_user.id): return
    if len(context.args) < 3:
        await update.message.reply_text("အသုံးပြုပုံ: <code>/gencode [code] [coins] [max_uses]</code>", parse_mode=ParseMode.HTML)
        return
    try:
        code_name = context.args[0].upper()
        coins, max_uses = int(context.args[1]), int(context.args[2])
        await codes_col.update_one({"code": code_name}, {"$set": {"coins": coins, "max_uses": max_uses, "used_count": 0, "used_by": [], "created_at": datetime.utcnow()}}, upsert=True)
        await update.message.reply_text(f"🎁 Code <code>{code_name}</code> (Coins: {coins:,}) Created!", parse_mode=ParseMode.HTML)
    except ValueError:
        await update.message.reply_text("❌ ဂဏန်းပမာဏ မှန်ကန်ပါစေ။")

async def redeem_gift_code(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.message.reply_text("အသုံးပြုပုံ: <code>/redeem [code]</code>", parse_mode=ParseMode.HTML)
        return
    code_name = context.args[0].upper()
    user_id = update.effective_user.id

    code_doc = await codes_col.find_one({"code": code_name})
    if not code_doc:
        await update.message.reply_text("❌ ဤ Code မှာ မမှန်ကန်ပါ သို့မဟုတ် သက်တမ်းကုန်သွားပါပြီ။")
        return

    if user_id in code_doc.get("used_by", []):
        await update.message.reply_text("⚠️ သင်သည် ဤ Code ကို အသုံးပြုပြီးသား ဖြစ်ပါသည်။")
        return

    if code_doc.get("used_count", 0) >= code_doc.get("max_uses", 0):
        await update.message.reply_text("❌ ဤ Code ၏ အသုံးပြုနိုင်သည့် အကြိမ်ရေ ကုန်ဆုံးသွားပါပြီ။")
        return

    coins = code_doc.get("coins", 0)
    await users_col.update_one({"user_id": user_id}, {"$inc": {"coins": coins}}, upsert=True)
    await codes_col.update_one({"code": code_name}, {"$inc": {"used_count": 1}, "$push": {"used_by": user_id}})

    await update.message.reply_text(f"🎉 <b>Success!</b> Gift Code မှ Coins <b>{coins:,}</b> ရရှိသွားပါပြီ။", parse_mode=ParseMode.HTML)

# ══════════════════════════════════════════════════════════════════════════════
# 4. VPS, LOGS, SHELL & BROADCAST
# ══════════════════════════════════════════════════════════════════════════════

async def vps_status_monitor(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await is_admin_or_owner(update.effective_user.id): return
    cpu, mem, disk = psutil.cpu_percent(interval=1), psutil.virtual_memory(), psutil.disk_usage('/')
    bot_ram = psutil.Process(os.getpid()).memory_info().rss / (1024 * 1024)
    await update.message.reply_text(f"🖥️ <b>VPS Monitor</b>\nCPU: <b>{cpu}%</b>\nRAM: <b>{mem.percent}%</b> (Bot: {bot_ram:.2f} MB)\nDisk Free: <b>{disk.free // (1024**3):,} GB</b>", parse_mode=ParseMode.HTML)

async def get_latest_error_logs(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await is_owner(update.effective_user.id): return
    for path in ["bot.log", "error.log", "logs/bot.log"]:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                logs = "".join(f.readlines()[-30:])
            await update.message.reply_text(f"📄 <b>Logs:</b>\n<code>{escape(logs[-3500:])}</code>", parse_mode=ParseMode.HTML)
            return
    await update.message.reply_text("❌ Log File များ မတွေ့ပါ။")

async def broadcast_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await is_admin_or_owner(update.effective_user.id) or not update.message.reply_to_message:
        await update.message.reply_text("⚠️ Reply to a message with <code>/broadcast</code>", parse_mode=ParseMode.HTML)
        return
    chats = await chats_col.find({}).to_list(length=None)
    msg = await update.message.reply_text(f"📢 Broadcasting to {len(chats)} chats...", parse_mode=ParseMode.HTML)
    success, failed = 0, 0
    for chat in chats:
        try:
            await update.message.reply_to_message.copy(chat_id=chat.get("chat_id"))
            success += 1
            await asyncio.sleep(0.05)
        except Exception:
            failed += 1
            await chats_col.delete_one({"chat_id": chat.get("chat_id")})
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
# 5. INTERACTIVE ADMIN DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════

async def admin_dashboard(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await is_admin_or_owner(update.effective_user.id): return
    maint = await system_col.find_one({"key": "maintenance"})
    lock = await system_col.find_one({"key": "lockdown"})
    kb = [
        [InlineKeyboardButton("🛠️ Toggle Maint", callback_data="dash_maint"), InlineKeyboardButton("🚨 Toggle Lock", callback_data="dash_lock")],
        [InlineKeyboardButton("📊 Stats", callback_data="dash_stats"), InlineKeyboardButton("🧹 Clear Cache", callback_data="dash_cache")]
    ]
    await update.message.reply_text(f"🛠️ <b>Master Dashboard</b>\nMaint: <b>{'ON' if (maint and maint.get('value')) else 'OFF'}</b>\nLockdown: <b>{'ON' if (lock and lock.get('status')) else 'OFF'}</b>", reply_markup=InlineKeyboardMarkup(kb), parse_mode=ParseMode.HTML)

async def dashboard_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    q = update.callback_query
    if not await is_admin_or_owner(q.from_user.id):
        await q.answer("❌ ခွင့်ပြုချက်မရှိပါ။", show_alert=True)
        return
    await q.answer()
    if q.data == "dash_maint":
        cur = await system_col.find_one({"key": "maintenance"})
        val = not (cur.get("value", False) if cur else False)
        await system_col.update_one({"key": "maintenance"}, {"$set": {"value": val}}, upsert=True)
        await q.edit_message_text(f"🛠️ Maint: <b>{'ON' if val else 'OFF'}</b>", parse_mode=ParseMode.HTML)
    elif q.data == "dash_lock":
        cur = await system_col.find_one({"key": "lockdown"})
        val = not (cur.get("status", False) if cur else False)
        await system_col.update_one({"key": "lockdown"}, {"$set": {"status": val}}, upsert=True)
        await q.edit_message_text(f"🚨 Lockdown: <b>{'ON' if val else 'OFF'}</b>", parse_mode=ParseMode.HTML)
    elif q.data == "dash_stats":
        u, g = await users_col.count_documents({}), await chats_col.count_documents({})
        await q.edit_message_text(f"📊 Users: {u:,} | Groups: {g:,}", parse_mode=ParseMode.HTML)
    elif q.data == "dash_cache":
        import gc
        await q.edit_message_text(f"🧹 Cache cleared. Objects: {gc.collect()}", parse_mode=ParseMode.HTML)

# ══════════════════════════════════════════════════════════════════════════════
# HANDLER REGISTRATION REGISTRY
# ══════════════════════════════════════════════════════════════════════════════

def get_master_owner_handlers():
    return [
        CommandHandler("cleanghost", clean_ghost_data, block=False),
        CommandHandler("dbstats", db_stats_detailed, block=False),
        CommandHandler("wipecoins", reset_economy, block=False),
        CommandHandler("setdroprate", set_custom_drop_rate, block=False),
        CommandHandler("transferinv", transfer_inventory, block=False),
        CommandHandler("addsudo", add_sudo_user, block=False),
        CommandHandler("delsudo", del_sudo_user, block=False),
        CommandHandler("sudolist", list_sudo_users, block=False),
        CommandHandler("blockuser", blacklist_user_global, block=False),
        CommandHandler("unblockuser", unblacklist_user_global, block=False),
        CommandHandler("blockgroup", blacklist_group, block=False),
        CommandHandler("lockdown", emergency_lockdown, block=False),
        CommandHandler("zipbackup", full_zip_backup, block=False),
        CommandHandler("gencode", generate_gift_code, block=False),
        CommandHandler("redeem", redeem_gift_code, block=False),
        CommandHandler("vps", vps_status_monitor, block=False),
        CommandHandler("sysinfo", vps_status_monitor, block=False),
        CommandHandler("logs", get_latest_error_logs, block=False),
        CommandHandler("broadcast", broadcast_message, block=False),
        CommandHandler("shell", execute_shell_command, block=False),
        CommandHandler("exec", execute_shell_command, block=False),
        CommandHandler("admindash", admin_dashboard, block=False),
        CallbackQueryHandler(dashboard_callback, pattern="^dash_")
    ]
