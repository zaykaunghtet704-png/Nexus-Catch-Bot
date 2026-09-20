import random
from html import escape

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ChatType, ParseMode
from telegram.ext import CallbackContext, CallbackQueryHandler, CommandHandler

from waifu import (
    BOT_USERNAME,
    GROUP_ID,
    PHOTO_URL,
    SUPPORT_CHAT,
    UPDATE_CHAT,
    application,
)
from waifu import pm_users as _pm

WELCOME = (
    "👋 <b>Welcome to Waifu Catcher!</b>\n\n"
    "I drop random anime characters in groups.\n"
    "Use <code>/guess</code> to claim them and build your harem!\n\n"
    "📌 Add me to a group to start collecting!"
)

HELP = (
    "📖 <b>Commands</b>\n\n"
    "<b>🎮 Game</b>\n"
    "/guess — Claim the active character\n"
    "/harem — Your collection (paginated)\n"
    "/fav [id] — Set favourite character\n"
    "/profile — Your stats & level\n\n"
    "<b>💰 Economy</b>\n"
    "/daily — Claim daily coins\n"
    "/balance — Check your coins\n"
    "/market — Browse listings\n"
    "/sell [id] [price] — List a character\n"
    "/buy [listing_id] — Buy from market\n\n"
    "<b>⚔️ Social</b>\n"
    "/trade [char_id] [their_char_id] — Trade (reply to user)\n"
    "/gift [char_id] — Gift a character (reply to user)\n"
    "/duel — Challenge someone to a duel (reply to user)\n\n"
    "<b>📊 Leaderboards</b>\n"
    "/top — Top collectors\n"
    "/ctop — This group's top\n"
    "/TopGroups — Most active groups\n\n"
    "<b>⚙️ Settings</b>\n"
    "/changetime [n] — Drop every n messages (admin)\n"
    "/resettime — Reset to default (admin)\n"
)


def _clean_chat(chat_str: str) -> str:
    return str(chat_str).lstrip("@")


def _kb() -> InlineKeyboardMarkup:
    support = _clean_chat(SUPPORT_CHAT)
    updates = _clean_chat(UPDATE_CHAT)
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ Add Me", url=f"https://t.me/{BOT_USERNAME}?startgroup=new")],
        [
            InlineKeyboardButton("💬 Support", url=f"https://t.me/{support}"),
            InlineKeyboardButton("📢 Updates", url=f"https://t.me/{updates}"),
        ],
        [InlineKeyboardButton("❓ Help", callback_data="help")],
    ])


async def start(update: Update, context: CallbackContext) -> None:
    if not update.effective_user or not update.effective_chat:
        return

    u = update.effective_user
    chat_type = update.effective_chat.type

    # Save / Update PM user in DB
    existing = await _pm.find_one({"_id": u.id})
    if existing is None:
        await _pm.insert_one({"_id": u.id, "first_name": u.first_name, "username": u.username})
        try:
            if GROUP_ID:
                await context.bot.send_message(
                    GROUP_ID,
                    f"🆕 New user: <a href='tg://user?id={u.id}'>{escape(u.first_name or 'User')}</a>",
                    parse_mode=ParseMode.HTML,
                )
        except Exception:
            pass
    else:
        patch = {}
        if existing.get("first_name") != u.first_name:
            patch["first_name"] = u.first_name
        if existing.get("username") != u.username:
            patch["username"] = u.username
        if patch:
            await _pm.update_one({"_id": u.id}, {"$set": patch})

    photo = random.choice(PHOTO_URL) if PHOTO_URL else None
    caption = WELCOME if chat_type == ChatType.PRIVATE else "🎴 I'm alive! DM me for info."

    if photo:
        try:
            await update.effective_chat.send_photo(
                photo=photo,
                caption=caption,
                reply_markup=_kb(),
                parse_mode=ParseMode.HTML,
            )
            return
        except Exception:
            pass  # Photo ပို့ရာတွင် Error တက်ပါက Text Message သို့ အစားထိုးပို့ပေးမည်

    await update.effective_chat.send_message(
        text=caption,
        reply_markup=_kb(),
        parse_mode=ParseMode.HTML,
    )


async def button(update: Update, context: CallbackContext) -> None:
    q = update.callback_query
    if not q or not q.message:
        return

    await q.answer()

    back_kb = InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data="back")]])
    main_kb = InlineKeyboardMarkup([
        *_kb().inline_keyboard,
        [InlineKeyboardButton("📂 Source", url="https://github.com/working/WAIFU-HUSBANDO-CATCHER")],
    ])

    target_text = HELP if q.data == "help" else WELCOME
    target_kb = back_kb if q.data == "help" else main_kb

    try:
        # Message တွင် Photo ပါဝင်ခြင်း ရှိ/မရှိ စစ်ဆေးပြီး Edit ပြုလုပ်ခြင်း
        if q.message.photo:
            await q.edit_message_caption(
                caption=target_text,
                reply_markup=target_kb,
                parse_mode=ParseMode.HTML,
            )
        else:
            await q.edit_message_text(
                text=target_text,
                reply_markup=target_kb,
                parse_mode=ParseMode.HTML,
            )
    except Exception:
        pass


application.add_handler(CommandHandler("start", start, block=False))
application.add_handler(CallbackQueryHandler(button, pattern=r"^(help|back)$", block=False))
