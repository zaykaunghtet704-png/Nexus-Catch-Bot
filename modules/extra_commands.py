"""
modules/extra_commands.py - Cleaned Extra Handlers
"""
from html import escape
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import CommandHandler, ContextTypes
from database import atomic, users_col, inventory_col, cards_col

async def profile_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_data = users_col.find_one({"user_id": user.id}) or {}
    
    balance = user_data.get("balance", 0)
    gems = user_data.get("gems", 0)
    cards_count = inventory_col.count_documents({"user_id": user.id})

    text = (
        f"👤 <b>{user.first_name}'s Profile</b>\n"
        f"─────────────────────────\n"
        f"🆔 <b>User ID:</b> <code>{user.id}</code>\n"
        f"💰 <b>Coins:</b> {balance:,}\n"
        f"💎 <b>Gems:</b> {gems:,}\n"
        f"🃏 <b>Total Cards:</b> {cards_count}\n"
    )
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)

async def balance_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_data = users_col.find_one({"user_id": user.id}) or {}
    balance = user_data.get("balance", 0)
    gems = user_data.get("gems", 0)

    text = (
        f"💰 <b>{user.first_name}'s Balance</b>\n"
        f"─────────────────────────\n"
        f"🪙 <b>Coins:</b> {balance:,}\n"
        f"💎 <b>Gems:</b> {gems:,}\n"
    )
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)

async def top_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pipeline = [
        {"$group": {"_id": "$user_id", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 10}
    ]
    top_users = list(inventory_col.aggregate(pipeline))
    
    if not top_users:
        await update.message.reply_text("🏆 မည်သည့် Collector မျှ ကတ်မရှိသေးပါ။")
        return

    text = "🏆 <b>TOP 10 COLLECTORS</b>\n─────────────────────────\n"
    for idx, u in enumerate(top_users, 1):
        text += f"{idx}. User ID <code>{u['_id']}</code> — <b>{u['count']} Cards</b>\n"
        
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)

async def ctop_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pipeline = [
        {"$group": {"_id": "$name", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 10}
    ]
    top_cards = list(inventory_col.aggregate(pipeline))
    
    if not top_cards:
        await update.message.reply_text("📊 မည်သည့် ကတ်မျှ မဖမ်းရသေးပါ။")
        return

    text = "📊 <b>TOP MOST CAUGHT CHARACTERS</b>\n─────────────────────────\n"
    for idx, c in enumerate(top_cards, 1):
        text += f"{idx}. <b>{c['_id']}</b> — {c['count']} times caught\n"
        
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)

async def ranking_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    top_users = sorted(list(users_col.find()), key=lambda u: int(u.get("coins", u.get("balance", 0)) or 0), reverse=True)[:10]
    
    text = "🌐 <b>GLOBAL COIN RANKING</b>\n─────────────────────────\n"
    for idx, u in enumerate(top_users, 1):
        name = escape(str(u.get("first_name", "User")))
        bal = u.get("coins", u.get("balance", 0))
        text += f"{idx}. <b>{name}</b> — 💰 {bal:,} Coins\n"
        
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)

async def gift_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Gift coins or one owned card to the user being replied to."""
    message = update.effective_message
    sender = update.effective_user
    target_message = message.reply_to_message if message else None
    if not message or not sender:
        return
    if not target_message or not target_message.from_user:
        await message.reply_text(
            "🎁 လက်ဆောင်ပေးမည့်သူ၏ Message ကို Reply လုပ်ပြီး\n"
            "<code>/gift [Coins ပမာဏ သို့မဟုတ် Card ID]</code> ဟု ရိုက်ပါ။",
            parse_mode=ParseMode.HTML,
        )
        return
    recipient = target_message.from_user
    if recipient.is_bot or recipient.id == sender.id:
        await message.reply_text("❌ Bot သို့မဟုတ် မိမိကိုယ်တိုင်ထံ လက်ဆောင်မပေးနိုင်ပါ။")
        return
    if not context.args:
        await message.reply_text("❌ <code>/gift [Coins ပမာဏ သို့မဟုတ် Card ID]</code>", parse_mode=ParseMode.HTML)
        return

    value = " ".join(context.args).strip()
    try:
        amount = int(value)
    except ValueError:
        amount = None

    try:
        with atomic():
            sender_doc = users_col.find_one({"user_id": sender.id}) or {}
            recipient_doc = users_col.find_one({"user_id": recipient.id}) or {}
            sender_wallet = "coins" if "coins" in sender_doc else "balance"
            recipient_wallet = "coins" if "coins" in recipient_doc else "balance"

            if amount is not None:
                if amount <= 0:
                    await message.reply_text("❌ Coins ပမာဏသည် 0 ထက် ကြီးရပါမည်။")
                    return
                debit = users_col.update_one(
                    {"user_id": sender.id, sender_wallet: {"$gte": amount}},
                    {"$inc": {sender_wallet: -amount}},
                )
                if debit.modified_count != 1:
                    await message.reply_text("❌ သင့်တွင် Coins မလုံလောက်ပါ။")
                    return
                if recipient_doc:
                    users_col.update_one(
                        {"user_id": recipient.id},
                        {"$inc": {recipient_wallet: amount}},
                    )
                else:
                    users_col.insert_one({
                        "user_id": recipient.id,
                        "first_name": recipient.first_name,
                        "username": recipient.username,
                        "coins": amount,
                        "gems": 0,
                        "xp": 0,
                    })
                gift_label = f"🪙 {amount:,} Coins"
            else:
                card = inventory_col.find_one({
                    "user_id": sender.id,
                    "$or": [{"card_id": value}, {"id": value}],
                })
                if not card:
                    await message.reply_text("❌ သင့် Inventory ထဲတွင် ဒီ Card မရှိပါ။")
                    return
                removed = inventory_col.delete_one({
                    "_id": card["_id"],
                    "user_id": sender.id,
                })
                if removed.deleted_count != 1:
                    await message.reply_text("❌ Card ပိုင်ဆိုင်မှုကို အတည်မပြုနိုင်ပါ။")
                    return
                new_card = {k: v for k, v in card.items() if k != "_id"}
                new_card["user_id"] = recipient.id
                inventory_col.insert_one(new_card)
                if not recipient_doc:
                    users_col.insert_one({
                        "user_id": recipient.id,
                        "first_name": recipient.first_name,
                        "username": recipient.username,
                        "coins": 0,
                        "gems": 0,
                        "xp": 0,
                    })
                gift_label = f"🎴 {escape(str(card.get('name') or value))} (ID: {escape(value)})"
    except Exception:
        await message.reply_text("❌ Gift ပေးပို့ရာတွင် Error ဖြစ်နေပါသည်။")
        return

    await message.reply_text(
        "🎁 <b>GIFT SENT SUCCESSFULLY!</b>\n\n"
        f"👤 ပေးပို့သူ: {escape(sender.first_name or 'Collector')}\n"
        f"🎀 လက်ခံသူ: {escape(recipient.first_name or 'Collector')}\n"
        f"🎁 လက်ဆောင်: <b>{gift_label}</b>",
        parse_mode=ParseMode.HTML,
    )

async def check_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❓ စစ်ဆေးလိုသော Character / Card ID ကို ထည့်ပါ။\nဥပမာ - <code>/check Naruto</code>", parse_mode=ParseMode.HTML)
        return
        
    card_name = " ".join(context.args)
    card = cards_col.find_one({"name": {"$regex": card_name, "$options": "i"}})
    
    if not card:
        await update.message.reply_text("❌ Character မတွေ့ရှိပါ။")
        return
        
    text = (
        f"🔍 <b>CHARACTER INFO</b>\n"
        f"─────────────────────────\n"
        f"👤 <b>Name:</b> {card.get('name')}\n"
        f"📺 <b>Anime:</b> {card.get('anime', 'N/A')}\n"
        f"⭐ <b>Rarity:</b> {card.get('rarity', 'Common')}\n"
    )
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)

def get_extra_handlers():
    return [
        CommandHandler("profile", profile_command),
        CommandHandler("balance", balance_command),
        CommandHandler("top", top_command),
        CommandHandler("ctop", ctop_command),
        CommandHandler("ranking", ranking_command),
        CommandHandler("gift", gift_command),
        CommandHandler("check", check_command),
    ]
