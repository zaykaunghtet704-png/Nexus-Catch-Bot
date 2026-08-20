import math
from models import MarketItem, SessionLocal, User, UserCard
from telegram import Update
from telegram.ext import ContextTypes


async def market_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    page = int(context.args[0]) if context.args and context.args[0].isdigit() else 1
    limit = 5
    session = SessionLocal()
    try:
        total = session.query(MarketItem).count()
        total_pages = math.ceil(total / limit) or 1
        page = max(1, min(page, total_pages))

        items = session.query(MarketItem).offset((page - 1) * limit).limit(limit).all()
        text = f"🏪 **GLOBAL MARKET (Page {page}/{total_pages}):**\n\n"
        for item in items:
            text += f"• Listing ID: `{item.id}` | Card: **{item.card.card_info.name}** | Price: `{item.price}` 🪙\n"

        await update.message.reply_text(text or "စျေးကွက်တွင် တင်ထားသော Card မရှိပါ။", parse_mode="Markdown")
    finally:
        session.close()


async def sell_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2:
        return
    char_id, price = context.args[0], int(context.args[1])
    uid = str(update.effective_user.id)
    session = SessionLocal()
    try:
        uc = session.query(UserCard).filter(UserCard.card_id == char_id, UserCard.user_id == uid).first()
        if uc and not uc.is_locked:
            item = MarketItem(seller_id=uid, card_uuid=uc.uuid, price=price)
            session.add(item)
            session.commit()
            await update.message.reply_text(f"✅ Listing ID `{item.id}` ဖြင့် ရောင်းရန် တင်လိုက်ပါပြီ။", parse_mode="Markdown")
    finally:
        session.close()


async def buy_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        return
    list_id = context.args[0]
    uid = str(update.effective_user.id)
    session = SessionLocal()
    try:
        item = session.query(MarketItem).filter(MarketItem.id == list_id).first()
        buyer = session.query(User).filter(User.id == uid).first()
        if item and buyer and buyer.coins >= item.price:
            buyer.coins -= item.price
            item.card.user_id = uid
            session.delete(item)
            session.commit()
            await update.message.reply_text("🎉 Card ကို ဝယ်ယူလိုက်ပါပြီ!", parse_mode="Markdown")
    finally:
        session.close()


async def delist_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        return
    list_id = context.args[0]
    uid = str(update.effective_user.id)
    session = SessionLocal()
    try:
        item = session.query(MarketItem).filter(MarketItem.id == list_id, MarketItem.seller_id == uid).first()
        if item:
            session.delete(item)
            session.commit()
            await update.message.reply_text("✅ စျေးကွက်မှ ပြန်လည် ရုပ်သိမ်းလိုက်ပါပြီ။", parse_mode="Markdown")
    finally:
        session.close()


async def trade_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.reply_to_message or len(context.args) < 2:
        return
    u1_id, u2_id = str(update.effective_user.id), str(update.message.reply_to_message.from_user.id)
    c1_id, c2_id = context.args[0], context.args[1]
    session = SessionLocal()
    try:
        uc1 = session.query(UserCard).filter(UserCard.card_id == c1_id, UserCard.user_id == u1_id).first()
        uc2 = session.query(UserCard).filter(UserCard.card_id == c2_id, UserCard.user_id == u2_id).first()
        if uc1 and uc2:
            uc1.user_id, uc2.user_id = u2_id, u1_id
            session.commit()
            await update.message.reply_text("🤝 **Trade အောင်မြင်ပါသည်!**", parse_mode="Markdown")
    finally:
        session.close()


async def gift_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.reply_to_message or not context.args:
        return
    giver_id, receiver_id = str(update.effective_user.id), str(update.message.reply_to_message.from_user.id)
    cid = context.args[0]
    session = SessionLocal()
    try:
        uc = session.query(UserCard).filter(UserCard.card_id == cid, UserCard.user_id == giver_id).first()
        if uc:
            uc.user_id = receiver_id
            session.commit()
            await update.message.reply_text(f"🎁 Card `{cid}` ကို လက်ဆောင်ပေးလိုက်ပါပြီ!", parse_mode="Markdown")
    finally:
        session.close()
