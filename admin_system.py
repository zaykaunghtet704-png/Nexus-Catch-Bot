import os

from config import OWNER_IDS
from models import AdminRole, BotConfig, CardBase, SessionLocal, User, UserCard
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes


def is_owner(user_id: int) -> bool:
    return user_id in OWNER_IDS


def is_admin(user_id: int) -> bool:
    if is_owner(user_id):
        return True
    session = SessionLocal()
    adm = (
        session.query(AdminRole)
        .filter(AdminRole.user_id == str(user_id))
        .first()
    )
    session.close()
    return adm is not None


async def adminpanel_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    keyboard = [
        [
            InlineKeyboardButton("🃏 Card Base", callback_data="adm_cards"),
            InlineKeyboardButton("👤 User Control", callback_data="adm_users"),
        ],
        [
            InlineKeyboardButton(
                "⚙️ Maintenance", callback_data="adm_maint"
            ),
            InlineKeyboardButton("📊 Analytics", callback_data="adm_stats"),
        ],
        [InlineKeyboardButton("❌ Close Panel", callback_data="adm_close")],
    ]
    await update.message.reply_text(
        "👑 **ADMIN CONTROL DASHBOARD**",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown",
    )


async def givecoins_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    if len(context.args) < 2:
        await update.message.reply_text(
            "❌ Format: `/givecoins <user_id> <amount>`", parse_mode="Markdown"
        )
        return
    uid, amount = context.args[0], int(context.args[1])

    session = SessionLocal()
    user = session.query(User).filter(User.id == uid).first()
    if user:
        user.coins += amount
        session.commit()
        await update.message.reply_text(
            f"✅ User `{uid}` ထံသို့ Coins `{amount}` ထည့်ပေးပြီးပါပြီ။",
            parse_mode="Markdown",
        )
    session.close()


async def forcespawn_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    # Triggers manual spawn directly into chat
    from main import trigger_manual_spawn

    await trigger_manual_spawn(update.effective_chat.id, context)


async def backup_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id):
        return
    db_path = "bot_database.db"
    if os.path.exists(db_path):
        await context.bot.send_document(
            chat_id=update.effective_user.id,
            document=open(db_path, "rb"),
            caption="📦 Database Backup Document",
        )
