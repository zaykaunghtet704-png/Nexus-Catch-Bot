"""
modules/admin.py - Admin Control Panel
"""
import os
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes
from database import cards_col, chats_col, inventory_col, users_col

OWNER_ID = int(os.getenv("OWNER_ID", "7974865879"))

def is_admin(user_id: int) -> bool:
    return user_id == OWNER_ID

async def admin_panel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    keyboard = [[InlineKeyboardButton("📊 System Stats", callback_data="admin_stats")]]
    await update.message.reply_text("👑 <b>ADMIN CONTROL PANEL</b>", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)

async def admin_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not is_admin(query.from_user.id):
        return
    await query.answer()
    if query.data == "admin_stats":
        u_count = users_col.count_documents({})
        c_count = cards_col.count_documents({})
        await query.edit_message_text(f"📊 <b>Stats:</b>\nUsers: {u_count}\nCards: {c_count}", parse_mode=ParseMode.HTML)

async def gban_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id) or not context.args:
        return
    target_id = int(context.args[0])
    users_col.update_one({"user_id": target_id}, {"$set": {"is_gbanned": True}}, upsert=True)
    await update.message.reply_text(f"🚨 User <code>{target_id}</code> ကို Global Ban လိုက်ပါပြီ။", parse_mode=ParseMode.HTML)
