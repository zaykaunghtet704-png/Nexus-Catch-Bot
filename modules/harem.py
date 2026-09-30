import math
from html import escape
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler

from database import inventory_col, users_col, cards_col

PAGE_SIZE = 10  # စာမျက်နှာတစ်ခုတွင် ပြသမည့် Anime / Rarity အရေအတွက်

# ── Rarity Icons & Emoji Mapping (13 Rarities Total) ──────────────────────────
RARITY_ICONS = {
    "⚪ Common": "🧊",
    "🟢 Uncommon": "🔮",
    "🔵 Rare": "🎁",
    "🟣 Epic": "✨",
    "🟡 Legendary": "🏆",
    "🔴 Mythic": "🔥",
    "🟠 Ancient": "📜",
    "Divine": "⚜️",
    "Immortal": "👑",
    "Cosmic": "🌌",
    "Primordial": "🔱",
    "Omnipotent": "👁️",
    "Transcendent": "♾️",
    # Text Matching Fallbacks
    "Common": "🧊",
    "Uncommon": "🔮",
    "Rare": "🎁",
    "Epic": "✨",
    "Legendary": "🏆",
    "Mythic": "🔥",
    "Ancient": "📜",
    "CrossVerse": "💎",
    "Cataphract": "🛡️",
    "Supreme": "🌌"
}

# ══════════════════════════════════════════════════════════════════════════════
# 1. /chmode (HAREM PREFERENCES SETTINGS)
# ══════════════════════════════════════════════════════════════════════════════

async def chmode_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Harem Display Mode များကို ပြောင်းလဲသတ်မှတ်ရန် Command"""
    user_id = update.effective_user.id
    user = await users_col.find_one({"user_id": user_id}) or {}

    mode = user.get("harem_mode", "DETAILED")
    rarity_pref = user.get("harem_rarity_filter", "ALL")
    event_pref = user.get("harem_event_filter", "ALL")

    text = (
        f"<b>Character Catcher Bot</b>\n\n"
        f"👤 <b>Account:</b> @{update.effective_user.username or 'No Username'}\n"
        f"🆔 <b>User ID:</b> <code>{user_id}</code>\n\n"
        f"✅ <b>PREFERENCES SET:</b>\n"
        f"<b>INTERFACE:</b> {mode} 🦖\n"
        f"<b>RARITY:</b> ⚜️ {rarity_pref}\n"
        f"<b>EVENT:</b> {event_pref}\n\n"
        f"YOU CAN CHANGE YOUR HAREM INTERFACE USING THESE BUTTONS:"
    )

    keyboard = [
        [
            InlineKeyboardButton("🦎 DEFAULT", callback_data="chmode_set_mode_DEFAULT"),
            InlineKeyboardButton("DETAILED 🦖", callback_data="chmode_set_mode_DETAILED")
        ],
        [
            InlineKeyboardButton("🏵️ RARITY / EVENT", callback_data="chmode_menu_rarity"),
            InlineKeyboardButton("📖 SORT BY ANIME", callback_data="chmode_sort_anime")
        ],
        [
            InlineKeyboardButton("🦕 RESET PREFERENCE", callback_data="chmode_reset"),
            InlineKeyboardButton("❌ CLOSE", callback_data="chmode_close")
        ]
    ]

    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)

async def chmode_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """chmode ၏ Inline Keyboard များကို နှိပ်သည့်အခါ အလုပ်လုပ်မည့် Callback"""
    query = update.callback_query
    user_id = query.from_user.id
    data = query.data

    await query.answer()

    if data == "chmode_close":
        await query.message.delete()
        return

    elif data.startswith("chmode_set_mode_"):
        new_mode = data.split("_")[-1]
        await users_col.update_one({"user_id": user_id}, {"$set": {"harem_mode": new_mode}}, upsert=True)
        await query.edit_message_text(
            f"✅ <b>Harem Interface Set To: {new_mode}</b>",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data="chmode_main")]]),
            parse_mode=ParseMode.HTML
        )

    elif data == "chmode_menu_rarity":
        # 13 Rarities Menu Layout
        keyboard = [
            [InlineKeyboardButton("♾️ Transcendent", callback_data="chmode_rarity_Transcendent"), InlineKeyboardButton("👁️ Omnipotent", callback_data="chmode_rarity_Omnipotent")],
            [InlineKeyboardButton("🔱 Primordial", callback_data="chmode_rarity_Primordial"), InlineKeyboardButton("🌌 Cosmic", callback_data="chmode_rarity_Cosmic")],
            [InlineKeyboardButton("👑 Immortal", callback_data="chmode_rarity_Immortal"), InlineKeyboardButton("⚜️ Divine", callback_data="chmode_rarity_Divine")],
            [InlineKeyboardButton("📜 Ancient", callback_data="chmode_rarity_Ancient"), InlineKeyboardButton("🔥 Mythic", callback_data="chmode_rarity_Mythic")],
            [InlineKeyboardButton("🏆 Legendary", callback_data="chmode_rarity_Legendary"), InlineKeyboardButton("✨ Epic", callback_data="chmode_rarity_Epic")],
            [InlineKeyboardButton("🎁 Rare", callback_data="chmode_rarity_Rare"), InlineKeyboardButton("🔮 Uncommon", callback_data="chmode_rarity_Uncommon")],
            [InlineKeyboardButton("🧊 Common", callback_data="chmode_rarity_Common")],
            [InlineKeyboardButton("⏩ Skip Rarity", callback_data="chmode_rarity_ALL")],
            [InlineKeyboardButton("❌ CLOSE", callback_data="chmode_close")]
        ]
        await query.edit_message_text("❄️ <b>CHOOSE YOUR PREFERRED RARITY:</b>", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)

    elif data.startswith("chmode_rarity_"):
        selected_rarity = data.replace("chmode_rarity_", "")
        await users_col.update_one({"user_id": user_id}, {"$set": {"harem_rarity_filter": selected_rarity}}, upsert=True)

        keyboard = [
            [InlineKeyboardButton("🐰 Bunny", callback_data="chmode_event_Bunny"), InlineKeyboardButton("🧹 Maid", callback_data="chmode_event_Maid")],
            [InlineKeyboardButton("🎓 Tuxedo", callback_data="chmode_event_Tuxedo"), InlineKeyboardButton("🏖️ Summer", callback_data="chmode_event_Summer")],
            [InlineKeyboardButton("🎃 Halloween", callback_data="chmode_event_Halloween"), InlineKeyboardButton("👘 Kimono", callback_data="chmode_event_Kimono")],
            [InlineKeyboardButton("⏩ Skip Event", callback_data="chmode_event_ALL")],
            [InlineKeyboardButton("❌ CLOSE", callback_data="chmode_close")]
        ]
        await query.edit_message_text(f"✅ <b>RARITY SET TO: {selected_rarity}</b>\n\n🎉 NOW CHOOSE AN EVENT (OR SKIP):", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode=ParseMode.HTML)

    elif data.startswith("chmode_event_"):
        selected_event = data.replace("chmode_event_", "")
        await users_col.update_one({"user_id": user_id}, {"$set": {"harem_event_filter": selected_event}}, upsert=True)
        await query.edit_message_text("✅ <b>Preferences Updated Successfully!</b>\nType /harem to view your updated character list.", parse_mode=ParseMode.HTML)

    elif data == "chmode_reset":
        await users_col.update_one({"user_id": user_id}, {"$set": {"harem_mode": "DETAILED", "harem_rarity_filter": "ALL", "harem_event_filter": "ALL"}}, upsert=True)
        await query.edit_message_text("🔄 <b>Preferences Reset To Default!</b>", parse_mode=ParseMode.HTML)

# ══════════════════════════════════════════════════════════════════════════════
# 2. /harem (CHARACTER INVENTORY DISPLAY)
# ══════════════════════════════════════════════════════════════════════════════

async def harem_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """User ၏ Harem Character များ စာရင်းကို ပြသပေးမည့် Command"""
    user_id = update.effective_user.id
    user_name = escape(update.effective_user.first_name)

    page = 1
    if context.args and context.args[0].isdigit():
        page = int(context.args[0])

    await send_harem_page(update.effective_chat.id, user_id, user_name, page, context)

async def harem_pagination_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Harem Pagination Buttons (Next / Prev) ဖိသည့်အခါ စာမျက်နှာ ပြောင်းပေးခြင်း"""
    query = update.callback_query
    data = query.data

    if not data.startswith("harem_page_"):
        return

    await query.answer()
    parts = data.split("_")
    target_user_id = int(parts[2])
    page = int(parts[3])

    if query.from_user.id != target_user_id:
        await query.answer("❌ ဤ Harem သည် အခြားသူ၏ Inventory ဖြစ်ပါသည်။", show_alert=True)
        return

    user_name = escape(query.from_user.first_name)
    await send_harem_page(query.message.chat_id, target_user_id, user_name, page, context, message_id=query.message.message_id)

async def send_harem_page(chat_id: int, user_id: int, user_name: str, page: int, context: ContextTypes.DEFAULT_TYPE, message_id: int = None):
    user_doc = await users_col.find_one({"user_id": user_id}) or {}
    rarity_filter = user_doc.get("harem_rarity_filter", "ALL")

    query_filter = {"user_id": user_id}
    if rarity_filter != "ALL":
        query_filter["rarity"] = {"$regex": rarity_filter, "$options": "i"}

    user_inventory = await inventory_col.find(query_filter).to_list(length=None)

    if not user_inventory:
        text = "❌ <b>သင့်ထံတွင် Character/Card များ မရှိသေးပါ။</b>\n/claim သို့မဟုတ် /catch ဖြင့် စတင်ဖမ်းယူပါ!"
        if message_id:
            await context.bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=text, parse_mode=ParseMode.HTML)
        else:
            await context.bot.send_message(chat_id=chat_id, text=text, parse_mode=ParseMode.HTML)
        return

    # Group by Anime
    anime_groups = {}
    for item in user_inventory:
        anime = item.get("anime", "Unknown Anime")
        if anime not in anime_groups:
            anime_groups[anime] = []
        anime_groups[anime].append(item)

    total_anime_count = len(anime_groups)
    total_cards_count = len(user_inventory)
    total_pages = max(1, math.ceil(total_anime_count / PAGE_SIZE))
    page = max(1, min(page, total_pages))

    # Paginate Anime List
    sorted_animes = sorted(anime_groups.keys())
    start_idx = (page - 1) * PAGE_SIZE
    end_idx = start_idx + PAGE_SIZE
    page_animes = sorted_animes[start_idx:end_idx]

    # Format Text Display
    text_lines = [f"<b>{user_name}'s RECENT CHARACTERS - PAGE: {page}/{total_pages}</b>\n"]

    for anime in page_animes:
        items = anime_groups[anime]
        total_in_db = await cards_col.count_documents({"anime": anime}) or len(items)

        text_lines.append(f"☘️ <b>{escape(anime)} ({len(items)}/{total_in_db})</b>")
        text_lines.append("--------------------")

        # Group duplicate cards
        card_counts = {}
        for c in items:
            c_id = c.get("card_id") or c.get("id", "000")
            c_name = c.get("name", "Unknown")
            c_rarity = c.get("rarity", "Common")
            key = (c_id, c_name, c_rarity)
            card_counts[key] = card_counts.get(key, 0) + 1

        for (c_id, c_name, c_rarity), count in card_counts.items():
            icon = RARITY_ICONS.get(c_rarity, "⚜️")
            text_lines.append(f"<code>{c_id}</code> | {icon} | <b>{escape(c_name)}</b> (x{count})")

        text_lines.append("")

    text_body = "\n".join(text_lines)

    # Navigation Buttons
    buttons = []
    nav_row = []
    if page > 1:
        nav_row.append(InlineKeyboardButton("⬅️ Prev", callback_data=f"harem_page_{user_id}_{page-1}"))
    if page < total_pages:
        nav_row.append(InlineKeyboardButton("Next ➡️", callback_data=f"harem_page_{user_id}_{page+1}"))

    if nav_row:
        buttons.append(nav_row)

    buttons.append([InlineKeyboardButton(f"⛩️ CHARACTERS ({total_cards_count})", callback_data="harem_count_info")])

    keyboard = InlineKeyboardMarkup(buttons)

    if message_id:
        await context.bot.edit_message_text(chat_id=chat_id, message_id=message_id, text=text_body, reply_markup=keyboard, parse_mode=ParseMode.HTML)
    else:
        await context.bot.send_message(chat_id=chat_id, text=text_body, reply_markup=keyboard, parse_mode=ParseMode.HTML)

# ══════════════════════════════════════════════════════════════════════════════
# HANDLER REGISTRATION
# ══════════════════════════════════════════════════════════════════════════════

def get_harem_handlers():
    return [
        CommandHandler("harem", harem_command, block=False),
        CommandHandler("chmode", chmode_command, block=False),
        CallbackQueryHandler(chmode_callback, pattern="^chmode_"),
        CallbackQueryHandler(harem_pagination_callback, pattern="^harem_page_")
    ]
