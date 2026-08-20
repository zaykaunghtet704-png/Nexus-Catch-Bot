import os
from config import OWNER_IDS
from models import AdminRole, BotConfig, CardBase, ChatSettings, SessionLocal, User, UserCard
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes


def is_owner(user_id: int) -> bool:
    return user_id in OWNER_IDS


def is_admin(user_id: int) -> bool:
    if is_owner(user_id):
        return True
    session = SessionLocal()
    try:
        adm = (
            session.query(AdminRole)
            .filter(AdminRole.user_id == str(user_id))
            .first()
        )
        return adm is not None
    finally:
        session.close()


async def adminpanel_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    keyboard = [
        [
            InlineKeyboardButton("🃏 Card Base", callback_data="adm_cards"),
            InlineKeyboardButton("👤 User Control", callback_data="adm_users"),
        ],
        [
            InlineKeyboardButton("⚙️ Maintenance", callback_data="adm_maint"),
            InlineKeyboardButton("📊 Stats", callback_data="adm_stats"),
        ],
        [InlineKeyboardButton("❌ Close", callback_data="adm_close")],
    ]
    markup = InlineKeyboardMarkup(keyboard)
    text = "👑 **ADMIN DASHBOARD**\nလုပ်ဆောင်လိုသည့် Menu ကို ရွေးပါ:"

    if update.callback_query:
        await update.callback_query.edit_message_text(
            text, reply_markup=markup, parse_mode="Markdown"
        )
    else:
        await update.message.reply_text(
            text, reply_markup=markup, parse_mode="Markdown"
        )


async def admin_callback_handler(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    query = update.callback_query
    if not is_admin(query.from_user.id):
        await query.answer("❌ Admin access required.", show_alert=True)
        return

    data = query.data
    await query.answer()

    if data == "adm_close":
        await query.message.delete()
    elif data == "adm_cards":
        text = "🃏 **CARD COMMANDS:**\n\n• `/addcard id | name | rarity | img_url`\n• `/listcards [page]`"
        await query.message.edit_text(text, parse_mode="Markdown")
    elif data == "adm_users":
        text = "👤 **USER COMMANDS:**\n\n• `/givecoins <uid> <amt>`\n• `/banuser <uid>`\n• `/unbanuser <uid>`"
        await query.message.edit_text(text, parse_mode="Markdown")
    elif data == "adm_maint":
        session = SessionLocal()
        try:
            cfg = (
                session.query(BotConfig)
                .filter(BotConfig.key == "maintenance_mode")
                .first()
            )
            if not cfg:
                cfg = BotConfig(key="maintenance_mode", value="true")
                session.add(cfg)
                st = "ENABLED 🚧"
            else:
                cfg.value = "false" if cfg.value == "true" else "true"
                st = "ENABLED 🚧" if cfg.value == "true" else "DISABLED ✅"
            session.commit()
            await query.message.edit_text(
                f"⚙️ Maintenance Status: **{st}**", parse_mode="Markdown"
            )
        finally:
            session.close()
    elif data == "adm_stats":
        session = SessionLocal()
        try:
            u_cnt = session.query(User).count()
            c_cnt = session.query(CardBase).count()
            await query.message.edit_text(
                f"📊 **STATS:**\n• Users: `{u_cnt}`\n• Cards: `{c_cnt}`",
                parse_mode="Markdown",
            )
        finally:
            session.close()


async def addcard_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    raw = " ".join(context.args).split("|")
    if len(raw) < 4:
        await update.message.reply_text(
            "❌ Format: `/addcard id | name | rarity | image_url`",
            parse_mode="Markdown",
        )
        return

    cid, name, rarity, img = (
        raw[0].strip(),
        raw[1].strip(),
        raw[2].strip(),
        raw[3].strip(),
    )
    session = SessionLocal()
    try:
        if session.query(CardBase).filter(CardBase.id == cid).first():
            await update.message.reply_text(
                "❌ Card ID ရှိပြီးသားဖြစ်ပါသည်။"
            )
            return

        session.add(CardBase(id=cid, name=name, rarity=rarity, image_url=img))
        session.commit()
        await update.message.reply_text(
            f"✅ Card `{name}` ထည့်ပြီးပါပြီ။", parse_mode="Markdown"
        )
    finally:
        session.close()


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
    try:
        user = session.query(User).filter(User.id == uid).first()
        if user:
            user.coins += amount
            session.commit()
            await update.message.reply_text(
                f"✅ User `{uid}` ထံသို့ Coins `{amount}` ထည့်ပြီးပါပြီ။",
                parse_mode="Markdown",
            )
    finally:
        session.close()


async def setspawn_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    if not context.args or not context.args[0].isdigit():
        await update.message.reply_text(
            "❌ Format: `/setspawn <number>`", parse_mode="Markdown"
        )
        return

    new_limit = int(context.args[0])
    chat_id = str(update.effective_chat.id)

    session = SessionLocal()
    try:
        setting = (
            session.query(ChatSettings)
            .filter(ChatSettings.chat_id == chat_id)
            .first()
        )
        if not setting:
            setting = ChatSettings(
                chat_id=chat_id, spawn_threshold=new_limit, current_msg_count=0
            )
            session.add(setting)
        else:
            setting.spawn_threshold = new_limit

        session.commit()
        await update.message.reply_text(
            f"⚙️ **Spawn Limit ပြောင်းလဲပြီးပါပြီ!**\nယခု Group ၏ Threshold: `{new_limit}` စာစောင်",
            parse_mode="Markdown",
        )
    finally:
        session.close()


async def incspawn_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    amount = (
        int(context.args[0])
        if context.args and context.args[0].isdigit()
        else 5
    )
    chat_id = str(update.effective_chat.id)

    session = SessionLocal()
    try:
        setting = (
            session.query(ChatSettings)
            .filter(ChatSettings.chat_id == chat_id)
            .first()
        )
        if not setting:
            setting = ChatSettings(
                chat_id=chat_id,
                spawn_threshold=30 + amount,
                current_msg_count=0,
            )
            session.add(setting)
        else:
            setting.spawn_threshold += amount

        session.commit()
        await update.message.reply_text(
            f"📈 Spawn Threshold ကို `{amount}` တိုးလိုက်ပါပြီ။ (လက်ရှိ: `{setting.spawn_threshold}`)",
            parse_mode="Markdown",
        )
    finally:
        session.close()


async def decspawn_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    amount = (
        int(context.args[0])
        if context.args and context.args[0].isdigit()
        else 5
    )
    chat_id = str(update.effective_chat.id)

    session = SessionLocal()
    try:
        setting = (
            session.query(ChatSettings)
            .filter(ChatSettings.chat_id == chat_id)
            .first()
        )
        if not setting:
            setting = ChatSettings(
                chat_id=chat_id,
                spawn_threshold=max(5, 30 - amount),
                current_msg_count=0,
            )
            session.add(setting)
        else:
            setting.spawn_threshold = max(5, setting.spawn_threshold - amount)

        session.commit()
        await update.message.reply_text(
            f"📉 Spawn Threshold ကို `{amount}` လျှော့လိုက်ပါပြီ။ (လက်ရှိ: `{setting.spawn_threshold}`)",
            parse_mode="Markdown",
        )
    finally:
        session.close()


async def backup_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id):
        return
    db_path = "bot_database.db"
    if os.path.exists(db_path):
        await context.bot.send_document(
            chat_id=update.effective_user.id,
            document=open(db_path, "rb"),
            caption="📦 Database Backup",
        )
