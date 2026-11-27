"""Separate Coin/Gem gacha pools with transactional wallet, inventory and pity updates."""
import asyncio
import random
from datetime import datetime, timezone
from html import escape

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import CommandHandler, ContextTypes

from database import atomic, db, users_col, cards_col, inventory_col, lock_query

gacha_pity_col = db["gacha_pity"]
gacha_history_col = db["gacha_history"]

COIN_COST = 2000
GEM_COST = 20
PITY_LIMIT = 50

# Independent weighted pools. Rarity labels from old uploads may contain emoji.
COIN_RATES = {
    "common": 40, "uncommon": 20, "rare": 15, "epic": 10,
    "legendary": 6, "mythic": 3, "ancient": 2, "divine": 1.5,
    "immortal": 1, "cosmic": 0.7, "primordial": 0.4,
    "omnipotent": 0.2, "transcendent": 0.2, "premium edition": 0.5,
    "supreme": 0.5, "crossverse": 0.5, "cataphract": 0.5,
}
GEM_RATES = {
    "common": 15, "uncommon": 12, "rare": 18, "epic": 18,
    "legendary": 12, "mythic": 8, "ancient": 5, "divine": 4,
    "immortal": 2.5, "cosmic": 1.5, "primordial": 1,
    "omnipotent": 0.6, "transcendent": 0.5, "premium edition": 1,
    "supreme": 1, "crossverse": 0.7, "cataphract": 0.7,
}
HIGH_RARITY = {
    "legendary", "mythic", "ancient", "divine", "immortal", "cosmic",
    "primordial", "omnipotent", "transcendent", "premium edition",
    "supreme", "crossverse", "cataphract",
}
RARITY_EMOJI = {
    "common": "⚪", "uncommon": "🟢", "rare": "🔵", "epic": "🟣",
    "legendary": "🟡", "mythic": "🔴", "ancient": "🟠",
    "divine": "🔮", "immortal": "👑", "cosmic": "🌌",
    "primordial": "🔱", "omnipotent": "👁️", "transcendent": "♾️",
    "premium edition": "💎", "supreme": "👑", "crossverse": "💠",
    "cataphract": "⚔️",
}

def _rarity_key(value):
    return " ".join(str(value or "common").casefold().split()).strip()

def _pool_choice(pool, pity_due=False):
    cards = list(cards_col.find())
    if not cards:
        return None
    groups = {}
    for card in cards:
        groups.setdefault(_rarity_key(card.get("rarity")), []).append(card)
    if pity_due:
        eligible = [r for r in groups if r in HIGH_RARITY]
        if eligible:
            rarity = random.choice(sorted(eligible))
            return random.choice(groups[rarity]), True
        # If no high-tier card exists yet, guarantee the best available tier.
        rarity = max(groups, key=lambda r: (COIN_RATES.get(r, 0), r))
        return random.choice(groups[rarity]), True
    rates = COIN_RATES if pool == "coin" else GEM_RATES
    available = [(r, rates.get(r, 0)) for r in groups if rates.get(r, 0) > 0]
    if not available:
        return random.choice(cards), False
    rarity = random.choices([x[0] for x in available], weights=[x[1] for x in available], k=1)[0]
    return random.choice(groups[rarity]), False

def _wallet_field(doc):
    return "coins" if "coins" in doc else "balance"

async def gacha_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text(
        "╭━━━━━━━━━━━━━━━━━━━━╮\n"
        "       🎴 <b>NEXUS GACHA</b>\n"
        "╰━━━━━━━━━━━━━━━━━━━━╯\n\n"
        "🪙 <code>/coindraw</code> — 2,000 Coins\n"
        "💎 <code>/gemdraw</code> — 20 Gems\n\n"
        "🎯 Pool တစ်ခုစီအတွက် Pity 50 Draws\n"
        "✨ 50 ကြိမ်ပြည့်လျှင် High Rarity အာမခံ\n"
        "🔐 Coin / Gem Pool နှင့် Pity သီးခြားစီ",
        parse_mode=ParseMode.HTML,
    )

async def _draw(update: Update, context: ContextTypes.DEFAULT_TYPE, pool: str):
    user = update.effective_user
    msg = update.effective_message
    if not user or not msg:
        return
    cost = COIN_COST if pool == "coin" else GEM_COST
    currency = "coins" if pool == "coin" else "gems"
    label = "Coins" if pool == "coin" else "Gems"
    selected = None
    pity_count = 0
    guaranteed = False
    failure = None
    try:
        with atomic():
            # Serialize each user's draw and pity progression in this pool.
            lock_query("users", {"user_id": user.id})
            lock_query("gacha_pity", {"user_id": user.id, "pool": pool})
            account = users_col.find_one({"user_id": user.id}) or {}
            wallet = _wallet_field(account) if pool == "coin" else "gems"
            current = int(account.get(wallet, 0) or 0)
            if current < cost:
                failure = f"❌ {label} မလုံလောက်ပါ။ လက်ကျန်: {current:,}"
            else:
                pity_doc = gacha_pity_col.find_one({"user_id": user.id, "pool": pool}) or {}
                previous = int(pity_doc.get("misses", 0) or 0)
                guaranteed = previous >= PITY_LIMIT - 1
                result = _pool_choice(pool, pity_due=guaranteed)
                if not result:
                    failure = "❌ Gacha Card မရှိသေးပါ။ Owner ထံ အကြောင်းကြားပါ။"
                else:
                    selected, pity_hit = result
                    guaranteed = pity_hit
                    debit = users_col.update_one(
                        {"user_id": user.id, wallet: {"$gte": cost}},
                        {"$inc": {wallet: -cost}},
                    )
                    if debit.modified_count != 1:
                        failure = f"❌ {label} လက်ကျန် မလုံလောက်ပါ။"
                    else:
                        pity_count = 0 if guaranteed else previous + 1
                        gacha_pity_col.update_one(
                            {"user_id": user.id, "pool": pool},
                            {"$set": {"misses": pity_count, "last_draw_at": datetime.now(timezone.utc).isoformat()}},
                            upsert=True,
                        )
                        card_id = selected.get("card_id") or selected.get("id")
                        inventory_col.insert_one({
                            "user_id": user.id,
                            "card_id": card_id,
                            "name": selected.get("name", "Unknown"),
                            "anime": selected.get("anime", "Unknown"),
                            "rarity": selected.get("rarity", "Common"),
                            "edition": selected.get("edition", "Normal"),
                            "img_url": selected.get("img_url") or selected.get("image"),
                            "obtained_at": datetime.now(timezone.utc).isoformat(),
                            "source": f"{pool}_gacha",
                        })
                        gacha_history_col.insert_one({
                            "user_id": user.id, "pool": pool, "cost": cost,
                            "currency": currency, "card_id": card_id,
                            "card_name": selected.get("name", "Unknown"),
                            "rarity": selected.get("rarity", "Common"),
                            "pity": guaranteed,
                            "created_at": datetime.now(timezone.utc).isoformat(),
                        })
    except Exception:
        import logging
        logging.getLogger(__name__).exception("Gacha transaction failed")
        failure = "❌ Gacha လုပ်ဆောင်ရာတွင် Database Error ဖြစ်နေပါသည်။"
    if failure:
        await msg.reply_text(failure)
        return

    # Full reveal animation. If Telegram edit fails, the draw remains safely saved.
    try:
        animation = await msg.reply_text(
            "╭━━━━━━━━━━━━━━━━━━━━╮\n"
            "       ✨ <b>NEXUS SUMMON</b> ✨\n"
            "╰━━━━━━━━━━━━━━━━━━━━╯\n\n"
            "🎴 Summoning...\n<code>[□□□□□□□□□□]</code>",
            parse_mode=ParseMode.HTML,
        )
        frames = [
            "🎴 Summoning...\n<code>[■■□□□□□□□□]</code>",
            "🔮 Energy gathering...\n<code>[■■■■□□□□□□]</code>",
            "✨ Rarity scanning...\n<code>[■■■■■■■□□□]</code>",
            "🌟 Card reveal...\n<code>[■■■■■■■■■■]</code>",
        ]
        for frame in frames:
            await asyncio.sleep(0.65)
            await animation.edit_text(
                "╭━━━━━━━━━━━━━━━━━━━━╮\n"
                "       ✨ <b>NEXUS SUMMON</b> ✨\n"
                "╰━━━━━━━━━━━━━━━━━━━━╯\n\n" + frame,
                parse_mode=ParseMode.HTML,
            )
    except Exception:
        animation = None

    rarity = str(selected.get("rarity", "Common"))
    emoji = RARITY_EMOJI.get(_rarity_key(rarity), "🎴")
    name = escape(str(selected.get("name", "Unknown")))
    anime = escape(str(selected.get("anime", "Unknown")))
    card_code = escape(str(selected.get("card_id") or selected.get("id") or "N/A"))
    pity_text = "🎯 <b>PITY GUARANTEED!</b>" if guaranteed else f"🎯 Pity: <b>{pity_count}/{PITY_LIMIT}</b>"
    result_text = (
        "╭━━━━━━━━━━━━━━━━━━━━╮\n"
        "       🎉 <b>SUMMON SUCCESS!</b>\n"
        "╰━━━━━━━━━━━━━━━━━━━━╯\n\n"
        f"{emoji} <b>{name}</b>\n"
        f"📺 {anime}\n"
        f"💎 Rarity: <b>{escape(rarity)}</b>\n"
        f"🆔 Card ID: <code>{card_code}</code>\n\n"
        f"💰 Cost: <b>{cost:,} {label}</b>\n"
        f"{pity_text}\n"
        "🎴 Card ကို သင့် Harem ထဲသို့ ထည့်ပြီးပါပြီ။"
    )
    image_url = selected.get("img_url") or selected.get("image")
    try:
        if image_url:
            await msg.reply_photo(photo=image_url, caption=result_text, parse_mode=ParseMode.HTML)
            if animation:
                await animation.delete()
        elif animation:
            await animation.edit_text(result_text, parse_mode=ParseMode.HTML)
        else:
            await msg.reply_text(result_text, parse_mode=ParseMode.HTML)
    except Exception:
        if animation:
            try:
                await animation.edit_text(result_text, parse_mode=ParseMode.HTML)
            except Exception:
                await msg.reply_text(result_text, parse_mode=ParseMode.HTML)
        else:
            await msg.reply_text(result_text, parse_mode=ParseMode.HTML)

async def coin_draw_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _draw(update, context, "coin")

async def gem_draw_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _draw(update, context, "gem")

def get_gacha_handlers():
    return [
        CommandHandler("gacha", gacha_command, block=False),
        CommandHandler("coindraw", coin_draw_command, block=False),
        CommandHandler("gemdraw", gem_draw_command, block=False),
    ]
