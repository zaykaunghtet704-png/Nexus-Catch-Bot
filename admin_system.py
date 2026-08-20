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


# --- လိုအပ်ချက်များအတွက် ADMIN COMMAND သစ်များ ---


async def usercards_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """User ထဲမှာ Card ဘယ်လောက်ရှိလဲ စစ်ဆေးသည့် Command"""
    if not is_admin(update.effective_user.id):
        return
    if not context.args:
        await update.message.reply_text(
            "❌ Format: `/usercards <user_id>`", parse_mode="Markdown"
        )
        return

    target_uid = context.args[0]
    session = SessionLocal()
    try:
        user = session.query(User).filter(User.id == target_uid).first()
        if not user:
            await update.message.reply_text("❌ User မတွေ့ပါ။")
            return

        cards = (
            session.query(UserCard).filter(UserCard.user_id == target_uid).all()
        )
        count = len(cards)

        text = f"👤 **USER CARD AUDIT:**\n\n"
        text += f"• User: **{user.first_name}** (`{user.id}`)\n"
        text += f"• Total Cards Held: `{count}` 🃏\n\n"

        if cards:
            text += "**Card List (Top 10):**\n"
            for c in cards[:10]:
                text += f"- `{c.uuid}` | {c.card_info.name} ({c.card_info.rarity})\n"

        await update.message.reply_text(text, parse_mode="Markdown")
    finally:
        session.close()


async def givecards_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """User တစ်ယောက်ထံ Multi Cards (ကော်မာခြား၍) တစ်ခါတည်း ပေးသည့် Command"""
    if not is_admin(update.effective_user.id):
        return
    if len(context.args) < 2:
        await update.message.reply_text(
            "❌ Format: `/givecards <user_id> <card_id1,card_id2,card_id3>`\nဥပမာ: `/givecards 12345678 card1,card2,card3`",
            parse_mode="Markdown",
        )
        return

    target_uid = context.args[0]
    card_ids = [c.strip() for c in context.args[1].split(",") if c.strip()]

    session = SessionLocal()
    try:
        user = session.query(User).filter(User.id == target_uid).first()
        if not user:
            await update.message.reply_text("❌ User မတွေ့ပါ။")
            return

        added_list = []
        failed_list = []

        for cid in card_ids:
            card_base = (
                session.query(CardBase).filter(CardBase.id == cid).first()
            )
            if card_base:
                card_base.total_prints += 1
                new_uc = UserCard(
                    user_id=target_uid,
                    card_id=card_base.id,
                    print_number=card_base.total_prints,
                )
                session.add(new_uc)
                added_list.append(card_base.name)
            else:
                failed_list.append(cid)

        session.commit()

        res = f"✅ **MULTI-CARDS ADDED!**\n\n"
        res += f"👤 User: `{target_uid}`\n"
        res += f"🃏 ထည့်သွင်းပြီးသော Cards ({len(added_list)}): {', '.join(added_list)}\n"
        if failed_list:
            res += f"⚠️ မတွေ့ရှိသော Card IDs: {', '.join(failed_list)}"

        await update.message.reply_text(res, parse_mode="Markdown")
    finally:
        session.close()


# --- ပုံမှန် ADMIN COMMANDS ---


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
    await update.message.reply_text(
        "👑 **ADMIN DASHBOARD**\nလုပ်ဆောင်လိုသည့် Menu ကို ရွေးပါ:",
        reply_markup=markup,
        parse_mode="Markdown",
    )


async def admin_callback_handler(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    query = update.callback_query
    if not is_admin(query.from_user.id):
        await query.answer("❌ Admin access required.", show_alert=True)
        return
    await query.answer()

    if query.data == "adm_close":
        await query.message.delete()
    elif query.data == "adm_cards":
        text = "🃏 **CARD COMMANDS:**\n\n• `/addcard id | name | rarity | img_url`\n• `/givecards <uid> <id1,id2>`"
        await query.message.edit_text(text, parse_mode="Markdown")
    elif query.data == "adm_users":
        text = "👤 **USER AUDIT COMMANDS:**\n\n• `/usercards <uid>`\n• `/givecoins <uid> <amt>`"
        await query.message.edit_text(text, parse_mode="Markdown")


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
                f"✅ Coins `{amount}` ထည့်ပြီးပါပြီ။", parse_mode="Markdown"
            )
    finally:
        session.close()


async def setspawn_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    if not context.args or not context.args[0].isdigit():
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
            f"⚙️ Group Threshold Limit: `{new_limit}`", parse_mode="Markdown"
        )
    finally:
        session.close()
