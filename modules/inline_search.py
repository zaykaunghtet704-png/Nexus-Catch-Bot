"""
modules/inline_search.py - Inline Query & Search Functionality
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InlineQueryResultPhoto
from telegram.constants import ParseMode
from telegram.ext import CommandHandler, InlineQueryHandler, CallbackQueryHandler, ContextTypes
from database import cards_col, inventory_col


async def search_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/search Command"""
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔎 SEARCH CHARACTERS", switch_inline_query_current_chat="")]
    ])
    await update.message.reply_text(
        "⚪️ <b>TO SEARCH CHARACTER CLICK ON BUTTON BELOW</b>",
        reply_markup=keyboard,
        parse_mode=ParseMode.HTML
    )


async def inline_query_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Inline Mode Search Logic"""
    query = update.inline_query.query.strip()
    
    if query:
        cards = list(cards_col.find({"name": {"$regex": query, "$options": "i"}}).limit(50))
    else:
        cards = list(cards_col.find().limit(50))

    results = []
    for card in cards:
        cid = str(card.get("card_id") or card.get("id") or card.get("_id"))
        name = card.get("name", "Unknown")
        anime = card.get("anime", "Unknown")
        rarity = card.get("rarity", "Common")
        img_url = card.get("img_url") or card.get("image") or "https://via.placeholder.com/300"

        caption = (
            f"<b>OwO! Check out this character!</b>\n\n"
            f"<b>{anime}</b>\n"
            f"<b>{cid}: {name}</b>\n"
            f"(✨ <b>RARITY: {rarity}</b>)"
        )

        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("🏠 GROUP CATCH", callback_data=f"search_gc_{cid}"),
                InlineKeyboardButton("🌍 GLOBAL CATCH", callback_data=f"search_glob_{cid}")
            ]
        ])

        results.append(
            InlineQueryResultPhoto(
                id=cid,
                photo_url=img_url,
                thumbnail_url=img_url,
                caption=caption,
                parse_mode=ParseMode.HTML,
                reply_markup=keyboard
            )
        )

    await update.inline_query.answer(results, cache_time=1)


async def search_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Button Callbacks for Search"""
    query = update.callback_query
    await query.answer()

    data = query.data
    chat_id = update.effective_chat.id if update.effective_chat else None

    if data.startswith("search_gc_"):
        cid = data.replace("search_gc_", "")
        card = cards_col.find_one({"$or": [{"card_id": cid}, {"id": cid}]}) or {}
        
        chat_count = inventory_col.count_documents({"$or": [{"card_id": cid}, {"id": cid}], "chat_id": chat_id}) if chat_id else 0
        
        new_text = (
            f"<b>OwO! Check out this character!</b>\n\n"
            f"<b>{card.get('anime', 'N/A')}</b>\n"
            f"<b>{cid}: {card.get('name', 'N/A')}</b>\n"
            f"(✨ <b>RARITY: {card.get('rarity', 'Common')}</b>)\n\n"
            f"🏠 <b>CAUGHT IN THIS CHAT:</b> {chat_count} TIMES"
        )
        await query.edit_message_caption(caption=new_text, parse_mode=ParseMode.HTML, reply_markup=query.message.reply_markup)

    elif data.startswith("search_glob_"):
        cid = data.replace("search_glob_", "")
        card = cards_col.find_one({"$or": [{"card_id": cid}, {"id": cid}]}) or {}
        
        global_count = inventory_col.count_documents({"$or": [{"card_id": cid}, {"id": cid}]})
        
        new_text = (
            f"<b>OwO! Check out this character!</b>\n\n"
            f"<b>{card.get('anime', 'N/A')}</b>\n"
            f"<b>{cid}: {card.get('name', 'N/A')}</b>\n"
            f"(✨ <b>RARITY: {card.get('rarity', 'Common')}</b>)\n\n"
            f"💰 <b>VALUE:</b> 280 ~ 500 Coins\n"
            f"🌍 <b>CAUGHT GLOBALLY:</b> {global_count} TIMES"
        )
        await query.edit_message_caption(caption=new_text, parse_mode=ParseMode.HTML, reply_markup=query.message.reply_markup)


def get_inline_search_handlers():
    return [
        CommandHandler("search", search_command),
        InlineQueryHandler(inline_query_handler),
        CallbackQueryHandler(search_callback_handler, pattern="^search_")
    ]
