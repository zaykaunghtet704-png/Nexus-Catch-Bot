"""
modules/start.py - Start & Help Module
"""
from datetime import datetime, timezone
from html import escape
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler
from database import chats_col, users_col

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat = update.effective_chat

    if not user:
        return

    # User Profile သို့မဟုတ် Balance ကို Database ထဲတွင် အသစ်သွင်းခြင်း/ပြင်ဆင်ခြင်း
    users_col.update_one(
        {"user_id": user.id},
        {
            "$set": {
                "username": user.username or "",
                "first_name": user.first_name or "User"
            },
            "$setOnInsert": {
                "balance": 500,
                "gems": 10,
                "xp": 0,
                "is_vip": False,
                "is_gbanned": False,
                "joined_at": datetime.now(timezone.utc)
            }
        },
        upsert=True
    )

    # Backfill missing defaults for partial/legacy user documents without
    # overwriting existing balances or collection progress.
    users_col.update_one(
        {
            "user_id": user.id,
            "balance": {"$exists": False},
            "coins": {"$exists": False},
        },
        {"$set": {"balance": 500}},
    )
    users_col.update_one(
        {"user_id": user.id, "gems": {"$exists": False}},
        {"$set": {"gems": 10}},
    )
    users_col.update_one(
        {"user_id": user.id, "xp": {"$exists": False}},
        {"$set": {"xp": 0}},
    )
    users_col.update_one(
        {"user_id": user.id, "is_vip": {"$exists": False}},
        {"$set": {"is_vip": False}},
    )
    users_col.update_one(
        {"user_id": user.id, "is_gbanned": {"$exists": False}},
        {"$set": {"is_gbanned": False}},
    )

    if chat.type == "private":
        bot_username = context.bot.username
        keyboard = [
            [InlineKeyboardButton("➕ 𝗔𝗗𝗗 𝗧𝗢 𝗚𝗥𝗢𝗨𝗣", url=f"https://t.me/{bot_username}?startgroup=true")],
            [InlineKeyboardButton("📚 𝗛𝗘𝗟𝗣", callback_data="help_menu"), InlineKeyboardButton("🛍️ 𝗦𝗛𝗢𝗣", callback_data="shop_menu")]
        ]
        text = (
            f"🌸 မင်္ဂလာပါ <b>{escape(user.first_name or 'Collector')}</b>!\n\n"
            f"╭━━━━━━━━━━━━━━━━━━╮\n"
            f"       🃏 <b>NEXUS CATCH</b>\n"
            f"╰━━━━━━━━━━━━━━━━━━╯\n\n"
            f"✨ Anime Character ကတ်များကို ဖမ်းယူ၊ စုဆောင်းပြီး\n"
            f"🏆 အခြား Collector များနှင့် ယှဉ်ပြိုင်လိုက်ပါ!\n\n"
            f"💫 <i>Your collection journey starts here.</i>"
        )
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)
    else:
        chats_col.update_one(
            {"chat_id": chat.id},
            {"$set": {"chat_title": chat.title or "Group Chat"}},
            upsert=True
        )
        await update.message.reply_text("╭━━━━━━━━━━━━━━━━━━╮\n   🃏 <b>NEXUS CATCH ACTIVE</b>\n╰━━━━━━━━━━━━━━━━━━╯\n\n✨ ကတ်များဖမ်းယူရန် အဆင်သင့်ဖြစ်ပါပြီ!\n🎯 <b>/catch</b> ကို စမ်းသုံးကြည့်ပါ။", parse_mode=ParseMode.HTML)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "╭━━━━━━━━━━━━━━━━━━╮\n"
        "       📚 <b>NEXUS CATCH • HELP</b>\n"
        "╰━━━━━━━━━━━━━━━━━━╯\n\n"
        "🌟 <b>COLLECTION</b>\n"
        "├ 🃏 `/catch` — ကတ်ဖမ်းရန်\n"
        "├ 📚 `/harem` — ကတ်စုဆောင်းမှုကြည့်ရန်\n"
        "├ 🔎 `/check` — Card ID စစ်ရန်\n"
        "└ 👤 `/profile` — ကိုယ်ရေးအချက်အလက်\n\n"
        "🪙 <b>ECONOMY</b>\n"
        "├ 🎁 `/daily` — နေ့စဉ်ဆုယူရန်\n"
        "├ 💰 `/balance` — လက်ကျန်ကြည့်ရန်\n"
        "└ 🛍️ `/shop` — ဆိုင်ဖွင့်ရန်\n\n"
        "🏆 <b>COMMUNITY</b>\n"
        "└ 🌍 `/ranking` — ထိပ်တန်းစာရင်း\n\n"
        "✨ <b>NEW FEATURES</b>\n"
        "├ 🎨 `/haremstyle compact` — Harem ပုံစံ\n"
        "├ ♻️ `/exchange [CardID]` — Duplicate လဲရန်\n"
        "├ 🎁 `/weekly` — Weekly Reward\n"
        "├ 🔥 `/streak` — Daily Streak\n"
        "├ 📦 `/chest` — Card Chest\n"
        "├ ⚡ `/booster buy` — Lucky Booster\n"
        "├ 🔎 `/findowner [CardID]` — Card ပိုင်ရှင်\n"
        "├ 🔨 `/auction` — Auction\n"
        "├ 🛒 `/market rarity=...` — Market Filter\n"
        "├ 🏆 `/weeklyranking` — Weekly Ranking\n"
        "└ 🏘️ `/topgroups` — Top Groups\n\n"
        "💫 <i>Collect • Trade • Become a Legend</i>"
    )
    
    # Message မှ ခေါ်လျှင် သို့မဟုတ် Callback မှ ခေါ်လျှင် နှစ်မျိုးလုံး အလုပ်လုပ်စေရန်
    if update.message:
        await update.message.reply_text(text, parse_mode=ParseMode.HTML)
    elif update.callback_query:
        await update.callback_query.message.edit_text(text, parse_mode=ParseMode.HTML)

async def start_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start Menu ရှိ Help Menu နှင့် Shop Menu ခလုတ်များအတွက် Handler"""
    query = update.callback_query
    await query.answer()

    data = query.data
    if data == "help_menu":
        text = (
            "╭━━━━━━━━━━━━━━━━━━╮\n"
            "       📚 <b>NEXUS CATCH • HELP</b>\n"
            "╰━━━━━━━━━━━━━━━━━━╯\n\n"
            "🌟 <b>COLLECTION</b>\n"
            "├ 🃏 `/catch` — ကတ်ဖမ်းရန်\n"
            "├ 📚 `/harem` — ကတ်စုဆောင်းမှုကြည့်ရန်\n"
            "├ 🔎 `/check` — Card ID စစ်ရန်\n"
            "└ 👤 `/profile` — ကိုယ်ရေးအချက်အလက်\n\n"
            "🪙 <b>ECONOMY</b>\n"
            "├ 🎁 `/daily` — နေ့စဉ်ဆုယူရန်\n"
            "├ 💰 `/balance` — လက်ကျန်ကြည့်ရန်\n"
            "└ 🛍️ `/shop` — ဆိုင်ဖွင့်ရန်\n\n"
            "🏆 <b>COMMUNITY</b>\n"
            "└ 🌍 `/ranking` — ထိပ်တန်းစာရင်း\n\n"
            "✨ <b>NEW FEATURES</b>\n"
            "├ 🎨 `/haremstyle compact` — Harem ပုံစံ\n"
            "├ ♻️ `/exchange [CardID]` — Duplicate လဲရန်\n"
            "├ 🎁 `/weekly` — Weekly Reward\n"
            "├ 🔥 `/streak` — Daily Streak\n"
            "├ 📦 `/chest` — Card Chest\n"
            "├ ⚡ `/booster buy` — Lucky Booster\n"
            "├ 🔎 `/findowner [CardID]` — Card ပိုင်ရှင်\n"
            "├ 🔨 `/auction` — Auction\n"
            "├ 🛒 `/market rarity=...` — Market Filter\n"
            "├ 🏆 `/weeklyranking` — Weekly Ranking\n"
            "└ 🏘️ `/topgroups` — Top Groups\n\n"
            "💫 <i>Collect • Trade • Become a Legend</i>"
        )
        back_keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ 𝗕𝗔𝗖𝗞", callback_data="back_start")]])
        try:
            await query.edit_message_text(text, reply_markup=back_keyboard, parse_mode=ParseMode.HTML)
        except Exception:
            pass

    elif data == "shop_menu":
        text = (
            "💎 <b>NEXUS SHOP & PACKS</b>\n"
            "─────────────────────────\n"
            "ဆိုင်အတွင်းမှ Item များနှင့် Card Packs များကို ဝယ်ယူရန် <code>/shop</code> ကို အသုံးပြုပါ။"
        )
        back_keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ 𝗕𝗔𝗖𝗞", callback_data="back_start")]])
        try:
            await query.edit_message_text(text, reply_markup=back_keyboard, parse_mode=ParseMode.HTML)
        except Exception:
            pass

    elif data == "back_start":
        user = update.effective_user
        bot_username = context.bot.username
        keyboard = [
            [InlineKeyboardButton("➕ 𝗔𝗗𝗗 𝗧𝗢 𝗚𝗥𝗢𝗨𝗣", url=f"https://t.me/{bot_username}?startgroup=true")],
            [InlineKeyboardButton("📚 𝗛𝗘𝗟𝗣", callback_data="help_menu"), InlineKeyboardButton("🛍️ 𝗦𝗛𝗢𝗣", callback_data="shop_menu")]
        ]
        text = (
            f"🌸 မင်္ဂလာပါ <b>{escape(user.first_name or 'Collector')}</b>!\n\n"
            f"╭━━━━━━━━━━━━━━━━━━╮\n"
            f"       🃏 <b>NEXUS CATCH</b>\n"
            f"╰━━━━━━━━━━━━━━━━━━╯\n\n"
            f"✨ Anime Character ကတ်များကို ဖမ်းယူ၊ စုဆောင်းပြီး\n"
            f"🏆 အခြား Collector များနှင့် ယှဉ်ပြိုင်လိုက်ပါ!\n\n"
            f"💫 <i>Your collection journey starts here.</i>"
        )
        try:
            await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)
        except Exception:
            pass

def get_start_handlers():
    return [
        CommandHandler("start", start_command),
        CommandHandler("help", help_command),
        CallbackQueryHandler(start_callback_handler, pattern="^(help_menu|shop_menu|back_start)$")
    ]
