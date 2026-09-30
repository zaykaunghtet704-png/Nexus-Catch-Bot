from datetime import datetime
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import CommandHandler, ContextTypes

from database import codes_col, inventory_col, users_col

# ── 1. Redeem Code System ─────────────────────────────────────────────────────

async def redeem_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/redeem [Code]"""
    user_id = int(update.effective_user.id)

    if not context.args:
        await update.message.reply_text("❌ <code>/redeem [Code]</code> ဟု အသုံးပြုပါ", parse_mode=ParseMode.HTML)
        return

    code_str = context.args[0].strip().upper()
    code_doc = codes_col.find_one({"code": code_str})

    if not code_doc:
        await update.message.reply_text("❌ Code မှားယွင်းနေပါသည် (သို့မဟုတ်) သက်တမ်းကုန်သွားပါပြီ။")
        return

    used_by = code_doc.get("used_by", [])
    if user_id in used_by:
        await update.message.reply_text("❌ သင် ဤ Code အား အသုံးပြုပြီးဖြစ်ပါသည်။")
        return

    coins_reward = code_doc.get("coins", 0)
    gems_reward = code_doc.get("gems", 0)

    users_col.update_one({"user_id": user_id}, {"$inc": {"coins": coins_reward, "gems": gems_reward}}, upsert=True)
    codes_col.update_one({"code": code_str}, {"$push": {"used_by": user_id}})

    await update.message.reply_text(
        f"🎉 <b>REDEEM SUCCESSFUL!</b>\n\n"
        f"🎁 +<b>{coins_reward:,}</b> Coins | 💎 +<b>{gems_reward}</b> Gems ရရှိသွားပါပြီ!",
        parse_mode=ParseMode.HTML
    )

# ── 2. Card Recycle / Disassemble System ──────────────────────────────────────

async def recycle_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/recycle [Card ID] - ထပ်နေသော ကတ်များကို ဖျက်ဆီး၍ Dust/Gems ပြောင်းခြင်း"""
    user_id = int(update.effective_user.id)

    if not context.args:
        await update.message.reply_text("❌ <b>အသုံးပြုပုံ:</b> <code>/recycle [Card ID]</code>", parse_mode=ParseMode.HTML)
        return

    card_id = context.args[0]
    item = inventory_col.find_one({"user_id": user_id, "card_id": card_id})

    if not item:
        await update.message.reply_text("❌ သင့်ထံတွင် ထို ID ဖြင့် ကတ်မရှိပါ။")
        return

    # Delete Card and Reward Gems
    inventory_col.delete_one({"_id": item["_id"]})
    gem_reward = 2 if "Common" in item.get("rarity", "") else 5
    users_col.update_one({"user_id": user_id}, {"$inc": {"gems": gem_reward}}, upsert=True)

    await update.message.reply_text(
        f"♻️ <b>{item['name']}</b> အား Recycle ပြုလုပ်ပြီး ဖျက်ဆီးလိုက်ပါပြီ!\n"
        f"💎 +<b>{gem_reward} Gems</b> ပြန်လည်ရရှိသည်။",
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
        CommandHandler(["recycle", "disassemble"], recycle_command, block=False),
        CommandHandler("quest", quest_command, block=False)
    ]
