from datetime import datetime
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import CommandHandler, ContextTypes

from database import atomic, codes_col, inventory_col, users_col

# ── 1. Redeem Code System ─────────────────────────────────────────────────────

async def redeem_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/redeem [Code] - Atomic one-time reward claim."""
    user_id = int(update.effective_user.id)

    if not context.args:
        await update.message.reply_text("❌ <code>/redeem [Code]</code> ဟု အသုံးပြုပါ", parse_mode=ParseMode.HTML)
        return

    code_str = context.args[0].strip().upper()
    try:
        with atomic():
            # Conditional update prevents two simultaneous claims by the same user.
            claim = codes_col.update_one(
                {"code": code_str, "used_by": {"$nin": [user_id]}},
                {"$addToSet": {"used_by": user_id}},
            )
            if claim.modified_count != 1:
                code_doc = codes_col.find_one({"code": code_str})
                reason = "သင် ဤ Code ကို အသုံးပြုပြီးဖြစ်ပါသည်။" if code_doc else "Code မှားယွင်းနေပါသည် (သို့မဟုတ်) သက်တမ်းကုန်သွားပါပြီ။"
                await update.message.reply_text("❌ " + reason)
                return

            code_doc = codes_col.find_one({"code": code_str}) or {}
            coins_reward = max(0, int(code_doc.get("coins", 0) or 0))
            gems_reward = max(0, int(code_doc.get("gems", 0) or 0))
            users_col.update_one(
                {"user_id": user_id},
                {"$inc": {"coins": coins_reward, "gems": gems_reward}},
                upsert=True,
            )
    except Exception:
        await update.message.reply_text("❌ Code ထုတ်ယူရာတွင် Error ဖြစ်နေပါသည်။ ထပ်မံမကြိုးစားမီ Owner ကို အသိပေးပါ။")
        return

    await update.message.reply_text(
        f"╭━━━━━━━━━━━━━━━━━━╮\n"
        f"       🎉 <b>REDEEM SUCCESS</b>\n"
        f"╰━━━━━━━━━━━━━━━━━━╯\n\n"
        f"🎁 ဆုလက်ဆောင် ရရှိပါပြီ!\n"
        f"🪙 Coins: <b>+{coins_reward:,}</b>\n"
        f"💎 Gems: <b>+{gems_reward}</b>",
        parse_mode=ParseMode.HTML
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
            copies = list(inventory_col.find({"user_id": user_id, "card_id": card_id}))
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
        CommandHandler("redeem", redeem_command, block=False),
        CommandHandler(["recycle", "disassemble", "exchange"], recycle_command, block=False),
        CommandHandler("quest", quest_command, block=False)
    ]
