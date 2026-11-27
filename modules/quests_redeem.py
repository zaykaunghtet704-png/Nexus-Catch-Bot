from datetime import datetime
from html import escape
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import CommandHandler, ContextTypes

from database import atomic, cards_col, codes_col, inventory_col, users_col

# ── 1. Redeem Code System ─────────────────────────────────────────────────────

async def redeem_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/redeem or /promo [Code] - one-time, max-use-aware atomic reward claim."""
    user = update.effective_user
    if not user:
        return
    user_id = int(user.id)
    if not context.args:
        await update.effective_message.reply_text(
            "🎟️ <b>PROMO / GIFT CODE</b>\nအသုံးပြုပုံ: <code>/promo [Code]</code>",
            parse_mode=ParseMode.HTML,
        )
        return

    code_str = context.args[0].strip().upper()
    card_to_award = None
    coins_reward = 0
    gems_reward = 0

    class RedeemAbort(Exception):
        pass

    try:
        with atomic():
            code_doc = codes_col.find_one_for_update({"code": code_str})
            if not code_doc:
                raise RedeemAbort("❌ Code မှားယွင်းနေပါသည် (သို့မဟုတ်) သက်တမ်းကုန်သွားပါပြီ။")

            used_by = code_doc.get("used_by", []) or []
            if user_id in used_by:
                raise RedeemAbort("❌ သင် ဤ Code ကို အသုံးပြုပြီးဖြစ်ပါသည်။")

            max_uses = int(code_doc.get("max_uses", 0) or 0)
            used_count = max(int(code_doc.get("used_count", 0) or 0), len(used_by))
            if max_uses > 0 and used_count >= max_uses:
                raise RedeemAbort("❌ ဤ Code ၏ အသုံးပြုနိုင်သည့် အကြိမ်ရေ ကုန်ဆုံးသွားပါပြီ။")

            card_id = code_doc.get("card_id")
            if card_id:
                card_to_award = cards_col.find_one({
                    "$or": [{"card_id": card_id}, {"id": card_id}]
                })
                if not card_to_award:
                    raise RedeemAbort("❌ ဒီ Promo Code နဲ့ပေးမည့် Card ID ကို Database ထဲတွင် မတွေ့ပါ။ Owner ကို အသိပေးပါ။")

            claim = codes_col.update_one(
                {"_id": code_doc["_id"], "used_by": {"$nin": [user_id]}},
                {"$addToSet": {"used_by": user_id}, "$inc": {"used_count": 1}},
            )
            if claim.modified_count != 1:
                raise RedeemAbort("❌ Code ကို အသုံးပြု၍မရတော့ပါ။")

            coins_reward = max(0, int(code_doc.get("coins", 0) or 0))
            gems_reward = max(0, int(code_doc.get("gems", 0) or 0))
            account = users_col.find_one({"user_id": user_id}) or {}
            wallet_field = "coins" if "coins" in account else "balance"
            users_col.update_one(
                {"user_id": user_id},
                {"$inc": {wallet_field: coins_reward, "gems": gems_reward},
                 "$set": {"first_name": user.first_name or "Collector", "username": user.username or ""}},
                upsert=True,
            )

            if card_to_award:
                inventory_col.insert_one({
                    "user_id": user_id,
                    "card_id": card_to_award.get("card_id") or card_to_award.get("id"),
                    "name": card_to_award.get("name"),
                    "anime": card_to_award.get("anime"),
                    "rarity": card_to_award.get("rarity"),
                    "edition": card_to_award.get("edition", "Normal"),
                    "img_url": card_to_award.get("img_url") or card_to_award.get("image"),
                    "obtained_at": datetime.utcnow().isoformat(),
                })
    except RedeemAbort as exc:
        await update.effective_message.reply_text(str(exc))
        return
    except Exception:
        await update.effective_message.reply_text("❌ Code ထုတ်ယူရာတွင် Error ဖြစ်နေပါသည်။ Database ကို မပြောင်းလဲဘဲ ပြန်လည်စစ်ဆေးထားပါသည်။")
        return

    card_line = ""
    if card_to_award:
        card_line = f"\n🎴 Card: <b>{escape(str(card_to_award.get('name', 'Unknown')))}</b>"
    await update.effective_message.reply_text(
        "╭━━━━━━━━━━━━━━━━━━╮\n"
        "       🎉 <b>REDEEM SUCCESS</b>\n"
        "╰━━━━━━━━━━━━━━━━━━╯\n\n"
        "🎁 သင့်ဆုလက်ဆောင်ကို လက်ခံရရှိပါပြီ!\n"
        f"🪙 Coins: <b>+{coins_reward:,}</b>\n"
        f"💎 Gems: <b>+{gems_reward}</b>{card_line}",
        parse_mode=ParseMode.HTML,
    )


# ── 2. Card Recycle / Disassemble System ──────────────────────────────────────

async def recycle_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/recycle [Card ID] - Duplicate cards only; keep at least one copy."""
    user_id = int(update.effective_user.id)
    if not context.args:
        await update.message.reply_text("❌ <b>အသုံးပြုပုံ:</b> <code>/recycle [Card ID]</code>", parse_mode=ParseMode.HTML)
        return

    card_id = context.args[0]
    try:
        with atomic():
            copies = list(inventory_col.find({
                "user_id": user_id,
                "$or": [{"card_id": card_id}, {"id": card_id}],
            }))
            if len(copies) < 2:
                await update.message.reply_text("❌ Duplicate ကတ်မဟုတ်ပါ။ မူရင်းကတ်တစ်ကတ်ကို အမြဲချန်ထားရပါမည်။")
                return

            item = copies[-1]
            deleted = inventory_col.delete_one({"_id": item["_id"], "user_id": user_id})
            if deleted.deleted_count != 1:
                await update.message.reply_text("❌ ကတ်ကို အတည်ပြုမဖျက်နိုင်ပါ။ ပြန်ကြိုးစားပါ။")
                return

            rarity = str(item.get("rarity", "Common"))
            gem_reward = 2 if "Common" in rarity or "Uncommon" in rarity else 5
            users_col.update_one({"user_id": user_id}, {"$inc": {"gems": gem_reward}}, upsert=True)
    except Exception:
        await update.message.reply_text("❌ Duplicate Exchange လုပ်ဆောင်ရာတွင် Error ဖြစ်နေပါသည်။")
        return

    await update.message.reply_text(
        f"♻️ <b>DUPLICATE EXCHANGE SUCCESS</b>\n"
        f"🎴 {item.get('name', 'Card')} ကို Exchange လုပ်ပြီး\n"
        f"💎 <b>+{gem_reward} Gems</b> ရရှိပါပြီ။",
        parse_mode=ParseMode.HTML
    )

# ── 3. Quests ─────────────────────────────────────────────────────────────────

async def quest_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = (
        "📜 <b>DAILY QUESTS</b>\n⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n"
        "1. နေ့စဉ် 1 ကြိမ် /daily ယူပါ - <b>[ပြီးမြောက်]</b>\n"
        "2. Character 3 ကတ် ဖမ်းယူပါ - <b>(0/3)</b>\n"
        "3. Market တွင် ကတ် 1 ကတ် တင်ရောင်းပါ - <b>(0/1)</b>\n\n"
        "🎁 <i>Quests အားလုံး ပြီးပါက Extra +50 Gems ရရှိမည်!</i>"
    )
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)

def get_quests_redeem_handlers():
    return [
        CommandHandler(["redeem", "promo"], redeem_command, block=False),
        CommandHandler(["recycle", "disassemble", "exchange"], recycle_command, block=False),
        CommandHandler("quest", quest_command, block=False)
    ]
