from config import LOG_CHANNEL_ID, OWNER_IDS
from models import AdminRole, CardBase, ChatSettings, SessionLocal, User, UserCard
from telegram import Update
from telegram.ext import ContextTypes


def is_owner(user_id: int) -> bool:
    return user_id in OWNER_IDS


def is_admin(user_id: int) -> bool:
    if is_owner(user_id):
        return True
    session = SessionLocal()
    try:
        adm = session.query(AdminRole).filter(AdminRole.user_id == str(user_id)).first()
        return adm is not None
    finally:
        session.close()


async def verify_group_eligibility(update: Update, context: ContextTypes.DEFAULT_TYPE) -> tuple[bool, str]:
    chat = update.effective_chat
    if chat.type == "private":
        return True, ""

    chat_id = str(chat.id)

    # 1. Admin Status Check
    try:
        bot_member = await context.bot.get_chat_member(chat_id=chat.id, user_id=context.bot.id)
        if bot_member.status != "administrator":
            return False, "⚠️ **BOT ACCESS ERROR!**\n\nဘော့ကို အသုံးပြုရန်အတွက် ဤ Group တွင် ဘော့အား **Admin** အဖြစ် ခန့်အပ်ပေးထားရန် လိုအပ်ပါသည်။"
    except Exception:
        return False, "⚠️ ဘော့အား Group Admin ပေးထားခြင်း ရှိ/မရှိ မစစ်ဆေးနိုင်ပါ။"

    # 2. Owner Approval Check (လူ ၅၀ သတ်မှတ်ချက်ကို ဖြုတ်ပေးထားပါသည်)
    session = SessionLocal()
    try:
        cs = session.query(ChatSettings).filter(ChatSettings.chat_id == chat_id).first()
        if not cs or not cs.is_allowed:
            return False, (
                "⚠️ **GROUP NOT APPROVED!**\n\n"
                "ဤ Group တွင် ဘော့အသုံးပြုခွင့် မဖွင့်ရသေးပါ။ အသုံးပြုလိုပါက **Bot Owner** ထံ ခွင့်ပြုချက် (Approval) တောင်းခံပေးပါ။"
            )
    finally:
        session.close()

    return True, ""


async def allow_group_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id):
        return

    if not context.args:
        await update.message.reply_text("❌ Usage: `/allow <group_id>`", parse_mode="Markdown")
        return

    target_chat_id = context.args[0].strip()
    session = SessionLocal()
    try:
        cs = session.query(ChatSettings).filter(ChatSettings.chat_id == target_chat_id).first()
        if not cs:
            cs = ChatSettings(chat_id=target_chat_id, is_allowed=True)
            session.add(cs)
        else:
            cs.is_allowed = True

        session.commit()
        await update.message.reply_text(f"✅ Group ID `{target_chat_id}` ကို ဘော့အသုံးပြုခွင့် ဖွင့်ပေးလိုက်ပါပြီ။", parse_mode="Markdown")

        try:
            await context.bot.send_message(
                chat_id=target_chat_id,
                text="🎉 **CONGRATULATIONS!**\n\nBot Owner မှ ဤ Group တွင် Bot အသုံးပြုခွင့်ကို အောင်မြင်စွာ ဖွင့်ပေးလိုက်ပါပြီ။ စတင်အသုံးပြုနိုင်ပါပြီ!",
                parse_mode="Markdown"
            )
        except Exception:
            pass
    finally:
        session.close()


async def track_group_addition(update: Update, context: ContextTypes.DEFAULT_TYPE):
    result = update.my_chat_member
    if not result:
        return

    old_status, new_status = result.old_chat_member.status, result.new_chat_member.status
    chat, user = result.chat, result.from_user

    if old_status in ["left", "kicked"] and new_status in ["member", "administrator"]:
        try:
            member_count = await context.bot.get_chat_member_count(chat_id=chat.id)
        except Exception:
            member_count = "N/A"

        log_text = (
            f"🤖 **BOT ADDED TO A NEW GROUP!**\n\n"
            f"👤 **Added By:** {user.first_name} (@{user.username or 'N/A'})\n"
            f"🆔 **User ID:** `{user.id}`\n\n"
            f"🏰 **Group Name:** **{chat.title}**\n"
            f"🆔 **Group ID:** `{chat.id}`\n"
            f"👥 **Total Members:** `{member_count}` ယောက်\n"
            f"🔗 **Group Username:** @{chat.username if chat.username else 'Private Group'}\n\n"
            f"💡 *Owner Command to Approve:* `/allow {chat.id}`"
        )
        try:
            await context.bot.send_message(chat_id=LOG_CHANNEL_ID, text=log_text, parse_mode="Markdown")
        except Exception as e:
            print(f"Log Error: {e}")


async def addcard_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return

    if update.message.reply_to_message and update.message.reply_to_message.photo:
        photo_id = update.message.reply_to_message.photo[-1].file_id
        raw = update.message.text.split(" ", 1)[1].split("|")
    else:
        raw = " ".join(context.args).split("|")
        photo_id = raw[4].strip() if len(raw) > 4 else None

    if len(raw) < 4 or not photo_id:
        return

    cid, name, tier, power = raw[0].strip(), raw[1].strip(), int(raw[2].strip()), int(raw[3].strip())
    session = SessionLocal()
    try:
        card = CardBase(id=cid, name=name, tier_level=tier, rarity=f"Tier {tier}", base_power=power, image_url=photo_id)
        session.add(card)
        session.commit()
        await update.message.reply_text(f"✅ Card `{name}` အား ထည့်သွင်းပြီးပါပြီ။", parse_mode="Markdown")
    finally:
        session.close()


async def givecoins_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id) or len(context.args) < 2:
        return
    uid, amt = context.args[0], int(context.args[1])
    session = SessionLocal()
    try:
        u = session.query(User).filter(User.id == uid).first()
        if u:
            u.coins += amt
            session.commit()
            await update.message.reply_text(f"✅ User `{uid}` ထံ Coins `{amt}` ထည့်ပြီးပါပြီ။", parse_mode="Markdown")
    finally:
        session.close()


async def givecards_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id) or len(context.args) < 2:
        return
    uid, card_ids = context.args[0], context.args[1].split(",")
    session = SessionLocal()
    try:
        for cid in card_ids:
            cb = session.query(CardBase).filter(CardBase.id == cid.strip()).first()
            if cb:
                cb.total_prints += 1
                session.add(UserCard(user_id=uid, card_id=cb.id, print_number=cb.total_prints))
        session.commit()
        await update.message.reply_text(f"✅ Cards များ ထည့်ပေးပြီးပါပြီ။", parse_mode="Markdown")
    finally:
        session.close()


async def changetime_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id) or len(context.args) < 2:
        return
    chat_id, limit = context.args[0], int(context.args[1])
    session = SessionLocal()
    try:
        cs = session.query(ChatSettings).filter(ChatSettings.chat_id == chat_id).first()
        if not cs:
            cs = ChatSettings(chat_id=chat_id, spawn_threshold=limit)
            session.add(cs)
        else:
            cs.spawn_threshold = limit
        session.commit()
        await update.message.reply_text(f"⚙️ Spawn Threshold ကို `{limit}` သို့ ပြောင်းလိုက်ပါပြီ။", parse_mode="Markdown")
    finally:
        session.close()


async def addadmin_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id) or not context.args:
        return
    uid = context.args[0]
    session = SessionLocal()
    try:
        session.add(AdminRole(user_id=uid))
        session.commit()
        await update.message.reply_text(f"👑 User `{uid}` အား Admin ခန့်အပ်လိုက်ပါပြီ။", parse_mode="Markdown")
    finally:
        session.close()
