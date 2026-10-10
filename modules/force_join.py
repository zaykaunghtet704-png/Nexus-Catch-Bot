import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler

env_admins = os.getenv("ADMIN_IDS", "")
ADMIN_IDS = [int(x.strip()) for x in env_admins.split(",") if x.strip().isdigit()]

MUST_JOIN_CHATS = []

async def check_must_join(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    if not MUST_JOIN_CHATS:
        return True

    user_id = update.effective_user.id
    bot = context.bot
    not_joined_buttons = []

    for chat in MUST_JOIN_CHATS:
        try:
            member = await bot.get_chat_member(chat["chat_id"], user_id)
            if member.status in ["banned", "kicked"]:
                await update.message.reply_text("❌ သင်သည် လိုအပ်သော Channel မှ Ban ခံထားရသဖြင့် Bot သုံးခွင့်မရှိပါ။")
                return False
        except Exception:
            not_joined_buttons.append([
                InlineKeyboardButton(chat["title"], url=chat["link"])
            ])

    if not_joined_buttons:
        bot_username = (await bot.get_me()).username
        not_joined_buttons.append([
            InlineKeyboardButton("✅ Join ပြီးပါပြီ (ပြန်လည်စစ်ဆေးမည်)", url=f"https://t.me/{bot_username}?start=start")
        ])

        await update.message.reply_text(
            "⚠️ **Bot ကို အသုံးပြုရန်အတွက် အောက်ပါ လင့်ခ်များအားလုံးကို မဖြစ်မနေ Join ပေးရပါမည်။**",
            reply_markup=InlineKeyboardMarkup(not_joined_buttons)
        )
        return False

    return True

async def add_must_join(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("❌ Admin များသာ အသုံးပြုနိုင်ပါသည်။")
        return

    try:
        args = " ".join(context.args)
        parts = [p.strip() for p in args.split("|")]
        if len(parts) < 3:
            raise ValueError()

        chat_id_input = parts[0]
        title = parts[1]
        link = parts[2]
        chat_id = int(chat_id_input) if (chat_id_input.startswith("-") and chat_id_input[1:].isdigit()) else chat_id_input

        MUST_JOIN_CHATS.append({"chat_id": chat_id, "title": title, "link": link})
        await update.message.reply_text(f"✅ Must Join လင့်ခ် အောင်မြင်စွာ ထည့်ပြီးပါပြီ!\nTitle: {title}")
    except Exception:
        await update.message.reply_text("⚠️ Format: `/addjoin @Channel | Title | Link`", parse_mode="Markdown")

def get_force_join_handlers():
    return [
        CommandHandler("addjoin", add_must_join)
    ]
