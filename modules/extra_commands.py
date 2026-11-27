"""Extra commands with clearly separated Coin, Gem and Card gifts."""
from html import escape
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import CommandHandler, ContextTypes
from database import atomic, users_col, inventory_col, cards_col


async def profile_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    doc = users_col.find_one({"user_id": user.id}) or {}
    coins = doc.get("coins", doc.get("balance", 0))
    gems = doc.get("gems", 0)
    count = inventory_col.count_documents({"user_id": user.id})
    await update.effective_message.reply_text(
        f"👤 <b>{escape(user.first_name or 'Collector')}'s Profile</b>\n"
        f"🪙 Coins: <b>{coins:,}</b>\n💎 Gems: <b>{gems:,}</b>\n🎴 Cards: <b>{count}</b>",
        parse_mode=ParseMode.HTML,
    )


async def balance_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    doc = users_col.find_one({"user_id": user.id}) or {}
    coins = doc.get("coins", doc.get("balance", 0))
    await update.effective_message.reply_text(
        f"💰 <b>{escape(user.first_name or 'Collector')}'s Wallet</b>\n"
        f"🪙 Coins: <code>{coins:,}</code>\n💎 Gems: <code>{int(doc.get('gems', 0) or 0):,}</code>",
        parse_mode=ParseMode.HTML,
    )


async def top_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    rows = list(inventory_col.aggregate([
        {"$group": {"_id": "$user_id", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}, {"$limit": 10}
    ]))
    if not rows:
        await update.effective_message.reply_text("🏆 Collector မရှိသေးပါ။")
        return
    body = "\n".join(f"{i}. <code>{r['_id']}</code> — <b>{r['count']} Cards</b>" for i, r in enumerate(rows, 1))
    await update.effective_message.reply_text("🏆 <b>TOP 10 COLLECTORS</b>\n" + body, parse_mode=ParseMode.HTML)


async def ctop_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    rows = list(inventory_col.aggregate([
        {"$group": {"_id": "$name", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}, {"$limit": 10}
    ]))
    if not rows:
        await update.effective_message.reply_text("📊 ကတ်မရှိသေးပါ။")
        return
    body = "\n".join(f"{i}. <b>{escape(str(r['_id']))}</b> — {r['count']} catches" for i, r in enumerate(rows, 1))
    await update.effective_message.reply_text("📊 <b>MOST CAUGHT CARDS</b>\n" + body, parse_mode=ParseMode.HTML)


async def ranking_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    rows = sorted(list(users_col.find()), key=lambda d: int(d.get("coins", d.get("balance", 0)) or 0), reverse=True)[:10]
    lines = []
    for i, doc in enumerate(rows, 1):
        lines.append(f"{i}. <b>{escape(str(doc.get('first_name', 'Collector')))}</b> — 🪙 {int(doc.get('coins', doc.get('balance', 0)) or 0):,}")
    await update.effective_message.reply_text("🌐 <b>GLOBAL COIN RANKING</b>\n" + ("\n".join(lines) or "စာရင်းမရှိသေးပါ။"), parse_mode=ParseMode.HTML)


def _gift_target(update: Update):
    msg = update.effective_message
    reply = msg.reply_to_message if msg else None
    return reply.from_user if reply else None


async def _transfer_wallet(update: Update, currency: str):
    msg, sender = update.effective_message, update.effective_user
    recipient = _gift_target(update)
    if not recipient:
        await msg.reply_text("လက်ခံမည့်သူ၏ Message ကို Reply လုပ်ပြီး Command သုံးပါ။")
        return
    if recipient.is_bot or recipient.id == sender.id:
        await msg.reply_text("❌ Bot သို့မဟုတ် မိမိကိုယ်ကို Gift မပေးနိုင်ပါ။")
        return
    args = update.effective_message.text.split() if update.effective_message.text else []
    if len(args) < 2:
        await msg.reply_text(f"အသုံးပြုပုံ: /gift{currency} [ပမာဏ]")
        return
    try:
        amount = int(args[1])
        if amount <= 0 or amount > 1_000_000_000:
            raise ValueError
    except ValueError:
        await msg.reply_text("❌ 1 မှ 1,000,000,000 အတွင်းရှိ ဂဏန်းအပေါင်း ထည့်ပါ။")
        return

    field = ("coins" if "coins" in (users_col.find_one({"user_id": sender.id}) or {}) else "balance") if currency == "coin" else "gems"
    error = None
    try:
        with atomic():
            sender_doc = users_col.find_one({"user_id": sender.id}) or {}
            field = ("coins" if "coins" in sender_doc else "balance") if currency == "coin" else "gems"
            debit = users_col.update_one(
                {"user_id": sender.id, field: {"$gte": amount}},
                {"$inc": {field: -amount}},
            )
            if debit.modified_count != 1:
                error = f"သင့်တွင် {('Coins' if currency == 'coin' else 'Gems')} မလုံလောက်ပါ။"
            else:
                recipient_doc = users_col.find_one({"user_id": recipient.id}) or {}
                recipient_field = (("coins" if "coins" in recipient_doc else "balance")
                                   if currency == "coin" else "gems")
                users_col.update_one(
                    {"user_id": recipient.id},
                    {"$inc": {recipient_field: amount},
                     "$setOnInsert": {"first_name": recipient.first_name or "Collector",
                                      "username": recipient.username or "", "xp": 0}},
                    upsert=True,
                )
    except Exception:
        error = "Database error ဖြစ်သဖြင့် Gift ကို မပို့နိုင်ပါ။"
    if error:
        await msg.reply_text("❌ " + error)
        return
    unit = "🪙 Coins" if currency == "coin" else "💎 Gems"
    await msg.reply_text(
        f"🎁 <b>{unit} GIFT SENT!</b>\n"
        f"👤 To: {escape(recipient.first_name or 'Collector')}\n"
        f"Amount: <b>{amount:,}</b>",
        parse_mode=ParseMode.HTML,
    )


async def giftcoin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _transfer_wallet(update, "coin")


async def giftgem_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _transfer_wallet(update, "gem")


async def giftcard_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg, sender = update.effective_message, update.effective_user
    recipient = _gift_target(update)
    if not recipient:
        await msg.reply_text("လက်ခံမည့်သူ၏ Message ကို Reply လုပ်ပြီး /giftcard [Card ID] ဟု ရိုက်ပါ။")
        return
    if recipient.is_bot or recipient.id == sender.id:
        await msg.reply_text("❌ Bot သို့မဟုတ် မိမိကိုယ်ကို Card Gift မပေးနိုင်ပါ။")
        return
    args = context.args or []
    if not args:
        await msg.reply_text("အသုံးပြုပုံ: /giftcard [Card ID]")
        return
    card_id = str(args[0]).strip()
    error = None
    card = None
    try:
        with atomic():
            card = inventory_col.find_one({
                "user_id": sender.id,
                "$or": [{"card_id": card_id}, {"id": card_id}],
            })
            if not card:
                error = "သင့် Inventory ထဲတွင် ဒီ Card ID မရှိပါ။"
            else:
                removed = inventory_col.delete_one({"_id": card["_id"], "user_id": sender.id})
                if removed.deleted_count != 1:
                    error = "Card ပိုင်ဆိုင်မှုကို အတည်မပြုနိုင်ပါ။"
                else:
                    transferred = {k: v for k, v in card.items() if k != "_id"}
                    transferred.update({"user_id": recipient.id, "source": "gift"})
                    inventory_col.insert_one(transferred)
                    users_col.update_one(
                        {"user_id": recipient.id},
                        {"$setOnInsert": {"first_name": recipient.first_name or "Collector",
                                          "username": recipient.username or "", "coins": 0,
                                          "gems": 0, "xp": 0}},
                        upsert=True,
                    )
    except Exception:
        error = "Database error ဖြစ်သဖြင့် Card Gift မအောင်မြင်ပါ။"
    if error:
        await msg.reply_text("❌ " + error)
        return
    await msg.reply_text(
        f"🎴 <b>CARD GIFT SENT!</b>\n"
        f"🌸 {escape(str(card.get('name', 'Unknown')))}\n"
        f"🆔 <code>{escape(card_id)}</code>\n"
        f"👤 To: {escape(recipient.first_name or 'Collector')}",
        parse_mode=ParseMode.HTML,
    )


async def gift_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text(
        "🎁 <b>Gift Commands ကို ခွဲထားပါပြီ</b>\n"
        "Reply လုပ်ပြီး အသုံးပြုပါ:\n"
        "🪙 /giftcoin [amount]\n💎 /giftgem [amount]\n🎴 /giftcard [Card ID]",
        parse_mode=ParseMode.HTML,
    )


async def check_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.effective_message.reply_text("အသုံးပြုပုံ: /check [Card ID သို့မဟုတ် Character Name]")
        return
    query = " ".join(context.args).strip()
    card = cards_col.find_one({"$or": [{"card_id": query}, {"id": query}]})
    if not card:
        card = cards_col.find_one({"name": {"$regex": query, "$options": "i"}})
    if not card:
        await update.effective_message.reply_text("❌ Character မတွေ့ပါ။")
        return
    await update.effective_message.reply_text(
        f"🔍 <b>CARD INFO</b>\n🌸 {escape(str(card.get('name', 'Unknown')))}\n"
        f"📺 {escape(str(card.get('anime', 'N/A')))}\n⭐ {escape(str(card.get('rarity', 'Common')))}",
        parse_mode=ParseMode.HTML,
    )


def get_extra_handlers():
    return [
        CommandHandler("profile", profile_command),
        CommandHandler("balance", balance_command),
        CommandHandler("top", top_command),
        CommandHandler("ctop", ctop_command),
        CommandHandler("ranking", ranking_command),
        CommandHandler("gift", gift_command),
        CommandHandler("giftcoin", giftcoin_command),
        CommandHandler("giftgem", giftgem_command),
        CommandHandler("giftcard", giftcard_command),
        CommandHandler("check", check_command),
    ]
