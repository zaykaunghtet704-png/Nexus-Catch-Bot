"""Owner drop-rate controls. Settings are stored additively in PostgreSQL."""
import random
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import CommandHandler, ContextTypes

try:
    from config import OWNER_ID, RARITIES
except ImportError:
    OWNER_ID = 0
    RARITIES = ["Common", "Uncommon", "Rare", "Epic", "Legendary", "Mythic",
                "Divine", "Celestial", "Eternal", "Ultimate", "Supreme",
                "Transcendent", "Premium Edition"]

from database import db

chats_col = db["chats"]
drop_settings_col = db["drop_settings"]

DEFAULT_RATES = {
    "Common": 40.0, "Uncommon": 20.0, "Rare": 15.0, "Epic": 10.0,
    "Legendary": 6.0, "Mythic": 3.0, "Divine": 2.0, "Celestial": 1.0,
    "Eternal": 1.0, "Ultimate": 0.7, "Supreme": 0.5,
    "Transcendent": 0.3, "Premium Edition": 0.5,
}

def _is_owner(user_id: int) -> bool:
    return bool(OWNER_ID) and user_id == OWNER_ID

def get_drop_rates() -> dict:
    doc = drop_settings_col.find_one({"key": "global"}) or {}
    saved = doc.get("rates") or {}
    return {rarity: max(0.0, float(saved.get(rarity, DEFAULT_RATES.get(rarity, 0.0))))
            for rarity in RARITIES}

def choose_weighted_card(cards: list):
    """Pick a rarity using configured weights, then pick a card of that rarity."""
    if not cards:
        return None
    rates = get_drop_rates()
    groups = {}
    for card in cards:
        rarity = str(card.get("rarity", "Common"))
        groups.setdefault(rarity, []).append(card)
    available = [(rarity, rates.get(rarity, 0.0)) for rarity in groups if rates.get(rarity, 0.0) > 0]
    if not available:
        return random.choice(cards)
    selected_rarity = random.choices(
        [item[0] for item in available],
        weights=[item[1] for item in available],
        k=1,
    )[0]
    return random.choice(groups[selected_rarity])

async def set_drop_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    if not user or not _is_owner(user.id):
        await update.effective_message.reply_text("❌ ဒီ Command ကို Bot Owner သာ အသုံးပြုနိုင်ပါသည်။")
        return
    if len(context.args) != 2:
        await update.effective_message.reply_text(
            "အသုံးပြုပုံ: <code>/setdrop [Rarity] [Percent]</code>\n"
            "ဥပမာ: <code>/setdrop Legendary 5</code>\n"
            "ပြီးလျှင် /droprates ဖြင့် စစ်ပါ။",
            parse_mode=ParseMode.HTML,
        )
        return
    rarity_input = " ".join(context.args[:-1]).casefold()
    rarity = next((r for r in RARITIES if r.casefold() == rarity_input), None)
    try:
        value = float(context.args[-1])
        if not 0 <= value <= 100:
            raise ValueError
    except ValueError:
        await update.effective_message.reply_text("❌ Percent ကို 0 မှ 100 အတွင်း ထည့်ပါ။")
        return
    if not rarity:
        await update.effective_message.reply_text("❌ Rarity မမှန်ပါ။ /droprates ဖြင့် Rarity အမည်များကြည့်ပါ။")
        return
    rates = get_drop_rates()
    rates[rarity] = value
    if sum(rates.values()) <= 0:
        await update.effective_message.reply_text("❌ Drop Rate အားလုံး 0 မဖြစ်ရပါ။")
        return
    drop_settings_col.update_one(
        {"key": "global"},
        {"$set": {"rates": rates}},
        upsert=True,
    )
    await update.effective_message.reply_text(
        f"✅ <b>DROP RATE UPDATED</b>\n{rarity}: <b>{value:g}%</b>\n"
        "မှတ်ချက်: Rate များကို စုစုပေါင်းအချိုးအစားအဖြစ် Normalize လုပ်ပြီး အသုံးပြုပါသည်။",
        parse_mode=ParseMode.HTML,
    )

async def drop_rates_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    rates = get_drop_rates()
    total = sum(rates.values())
    lines = []
    for rarity in RARITIES:
        actual = (rates[rarity] / total * 100) if total else 0
        lines.append(f"• {rarity}: <b>{rates[rarity]:g}%</b>  <i>(effective {actual:.2f}%)</i>")
    await update.effective_message.reply_text(
        "🎲 <b>NEXUS DROP RATES</b>\n"
        "━━━━━━━━━━━━━━━━━━\n" + "\n".join(lines) +
        "\n\nOwner: <code>/setdrop Legendary 5</code>",
        parse_mode=ParseMode.HTML,
    )

async def set_spawn_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    chat = update.effective_chat
    if not _is_owner(user_id):
        await update.effective_message.reply_text("❌ ဤ Command ကို Bot Owner သာ အသုံးပြုနိုင်ပါသည်။")
        return
    if not chat or chat.type == "private":
        await update.effective_message.reply_text("❌ Group ထဲတွင် အသုံးပြုပါ။")
        return
    if not context.args or not context.args[0].isdigit():
        await update.effective_message.reply_text("အသုံးပြုပုံ: /setspawn [စာစောင်အရေအတွက်]")
        return
    threshold = int(context.args[0])
    if not 5 <= threshold <= 100000:
        await update.effective_message.reply_text("❌ 5 မှ 100000 အတွင်း ထည့်ပါ။")
        return
    chats_col.update_one(
        {"chat_id": chat.id},
        {"$set": {"spawn_threshold": threshold, "chat_title": chat.title or "Group"}},
        upsert=True,
    )
    await update.effective_message.reply_text(
        f"✅ ယခု Group တွင် စာ <b>{threshold}</b> စောင်ပြည့်တိုင်း Card Drop ဖြစ်ပါမည်။",
        parse_mode=ParseMode.HTML,
    )

def get_spawn_settings_handlers():
    return [
        CommandHandler(["setspawn", "changetime"], set_spawn_command, block=False),
        CommandHandler("setdrop", set_drop_command, block=False),
        CommandHandler("droprates", drop_rates_command, block=False),
    ]
