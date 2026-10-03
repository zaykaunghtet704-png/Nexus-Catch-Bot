"""
modules/inline_search.py - Inline Query & Search Functionality
"""
from html import escape
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InlineQueryResultPhoto
from telegram.constants import ParseMode
from telegram.ext import CommandHandler, InlineQueryHandler, CallbackQueryHandler, ContextTypes
from database import cards_col, inventory_col, users_col, chats_col


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
        name = escape(card.get("name", "Unknown"))
        anime = escape(card.get("anime", "Unknown"))
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
    """Inline Messages Callback Handler"""
    query = update.callback_query
    await query.answer()

    data = query.data
    chat_instance = query.chat_instance

    # Chat ID နှင့် Chat Instance တို့ကို Database တွင် ချိတ်ဆက်သိမ်းဆည်းခြင်း
    chat_id = update.effective_chat.id if update.effective_chat else None

    if chat_id and chat_instance:
        chats_col.update_one(
            {"chat_id": chat_id},
            {"$set": {"chat_instance": chat_instance}},
            upsert=True
        )
        chats_col.update_one(
            {"chat_instance": chat_instance},
            {"$set": {"chat_id": chat_id}},
            upsert=True
        )
    elif not chat_id and chat_instance:
        chat_doc = chats_col.find_one({"chat_instance": chat_instance})
        if chat_doc:
            chat_id = chat_doc.get("chat_id")

    if data.startswith("search_gc_"):
        cid = data.replace("search_gc_", "")
        card = cards_col.find_one({"$or": [{"card_id": cid}, {"id": cid}]}) or {}
        
        # Group အတွင်း ဖမ်းဆီးထားသော အရေအတွက်ကို စစ်ဆေးခြင်း
        if chat_id:
            chat_count = inventory_col.count_documents({
                "$or": [{"card_id": cid}, {"id": cid}],
                "$or": [{"chat_id": chat_id}, {"chat_instance": chat_instance}]
            })
        elif chat_instance:
            chat_count = inventory_col.count_documents({
                "$or": [{"card_id": cid}, {"id": cid}],
                "chat_instance": chat_instance
            })
        else:
            chat_count = 0

        new_text = (
            f"<b>OwO! Check out this character!</b>\n\n"
            f"<b>{escape(card.get('anime', 'N/A'))}</b>\n"
            f"<b>{cid}: {escape(card.get('name', 'N/A'))}</b>\n"
            f"(✨ <b>RARITY: {card.get('rarity', 'Common')}</b>)\n\n"
            f"🏠 <b>CAUGHT IN THIS CHAT:</b> {chat_count} TIMES"
        )

        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("🏠 GROUP CATCH", callback_data=f"search_gc_{cid}"),
                InlineKeyboardButton("🌍 GLOBAL CATCH", callback_data=f"search_glob_{cid}")
            ]
        ])

        await query.edit_message_caption(
            caption=new_text,
            parse_mode=ParseMode.HTML,
            reply_markup=keyboard
        )

    elif data.startswith("search_glob_"):
        cid = data.replace("search_glob_", "")
        card = cards_col.find_one({"$or": [{"card_id": cid}, {"id": cid}]}) or {}
        
        global_count = inventory_col.count_documents({"$or": [{"card_id": cid}, {"id": cid}]})

        # Top 10 Global Catchers စာရင်း
        pipeline = [
            {"$match": {"$or": [{"card_id": cid}, {"id": cid}]}},
            {"$group": {"_id": "$user_id", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 10}
        ]
        top_catchers_raw = list(inventory_col.aggregate(pipeline))

        top_lines = []
        for item in top_catchers_raw:
            uid = item["_id"]
            cnt = item["count"]
            u_doc = users_col.find_one({"user_id": uid}) or {}
            uname = escape(u_doc.get("first_name", f"User {uid}"))
            top_lines.append(f"⇒ {uname} (<code>{uid}</code>) x{cnt}")

        top_str = "\n".join(top_lines) if top_lines else "မရှိသေးပါ။"

        new_text = (
            f"<b>OwO! Check out this character!</b>\n\n"
            f"<b>{escape(card.get('anime', 'N/A'))}</b>\n"
            f"<b>{cid}: {escape(card.get('name', 'N/A'))}</b>\n"
            f"(✨ <b>RARITY: {card.get('rarity', 'Common')}</b>)\n\n"
            f"💰 <b>VALUE:</b> 280 ~ 500 Coins\n"
            f"🌍 <b>CAUGHT GLOBALLY:</b> {global_count} TIMES\n\n"
            f"🎖️ <b>TOP 10 GLOBAL CATCHERS OF THIS CHARACTER:</b>\n"
            f"{top_str}"
        )

        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("🏠 GROUP CATCH", callback_data=f"search_gc_{cid}"),
                InlineKeyboardButton("🌍 GLOBAL CATCH", callback_data=f"search_glob_{cid}")
            ]
        ])

        await query.edit_message_caption(
            caption=new_text,
            parse_mode=ParseMode.HTML,
            reply_markup=keyboard
        )


def get_inline_search_handlers():
    return [
        CommandHandler("search", search_command),
        InlineQueryHandler(inline_query_handler),
        CallbackQueryHandler(search_callback_handler, pattern="^search_")
    ]
