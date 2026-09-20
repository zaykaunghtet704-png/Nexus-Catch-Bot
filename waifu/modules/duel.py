"""
modules/duel.py — PvP duel system.
"""
import asyncio
import random
import time
from html import escape

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.constants import ParseMode
from telegram.ext import CallbackContext, CallbackQueryHandler, CommandHandler

from waifu import application, user_collection
from waifu.config import Config

_pending: dict[str, dict] = {}
_EXPIRY = 120   # 2 minutes

# Rarity 13 ဆင့်အတွက် Power Multiplier Scaled Values
_RARITY_POWER = {
    "⚪ Common": 10,
    "🟢 Uncommon": 15,
    "🔵 Rare": 25,
    "🟣 Epic": 40,
    "🟡 Legendary": 60,
    "🟠 Mythic": 85,
    "🔴 Ancient": 120,
    "🔮 Celestial": 160,
    "🌟 Exotic": 210,
    "🌌 Cosmic": 270,
    "✨ Immortal": 350,
    "👑 Exclusive Edition": 450,
    "🏆 Premium Edition": 600,
}


def _duel_id(a: int, b: int) -> str:
    return f"d_{a}_{b}_{int(time.time())}"


async def _expire(did: str) -> None:
    await asyncio.sleep(_EXPIRY)
    _pending.pop(did, None)


def _power(char: dict) -> int:
    rarity = char.get("rarity", "")
    base = _RARITY_POWER.get(rarity, 10)
    # Variance (random multiplier between 0.85 and 1.15)
    return int(base * random.uniform(0.85, 1.15))


async def duel(update: Update, context: CallbackContext) -> None:
    if not update.message or not update.message.reply_to_message:
        await update.message.reply_text(
            "⚔️ Duel စိန်ခေါ်ချင်သော User ၏ စာကို Reply ပြန်ပြီး /duel ဟု ရိုက်ပါ။"
        )
        return

    a = update.effective_user
    b = update.message.reply_to_message.from_user

    if a.id == b.id:
        await update.message.reply_text("❌ မိမိကိုယ်ကို Duel စိန်ခေါ်၍ မရပါ။")
        return
    if b.is_bot:
        await update.message.reply_text("❌ Bot များကို Duel စိန်ခေါ်၍ မရပါ။")
        return

    a_doc = await user_collection.find_one({"$or": [{"id": a.id}, {"user_id": a.id}]})
    b_doc = await user_collection.find_one({"$or": [{"id": b.id}, {"user_id": b.id}]})

    if not a_doc or not a_doc.get("characters"):
        await update.message.reply_text("❌ သင့်ထံတွင် Duel ယှဉ်ပြိုင်ရန် Character တစ်ခုမျှ မရှိသေးပါ။")
        return
    if not b_doc or not b_doc.get("characters"):
        await update.message.reply_text(
            f"❌ <b>{escape(b.first_name)}</b> ထံတွင် Character မရှိသေးပါ။",
            parse_mode=ParseMode.HTML,
        )
        return

    did = _duel_id(a.id, b.id)

    # Pick top-5 unique characters for challenger
    unique_a = list({c["id"]: c for c in a_doc["characters"]}.values())[:5]
    unique_b = list({c["id"]: c for c in b_doc["characters"]}.values())[:5]

    _pending[did] = {
        "challenger_id": a.id,
        "challenger_name": a.first_name,
        "opponent_id": b.id,
        "opponent_name": b.first_name,
        "a_chars": unique_a,
        "b_chars": unique_b,
        "a_pick": None,
        "b_pick": None,
    }
    asyncio.create_task(_expire(did))

    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton(
            f"{c.get('rarity','🎴')} {c['name'][:18]}",
            callback_data=f"duel_a:{did}:{i}",
        )]
        for i, c in enumerate(unique_a)
    ])
    await update.message.reply_text(
        f"⚔️ <b>{escape(a.first_name)}</b> က <b>{escape(b.first_name)}</b> ကို Duel စိန်ခေါ်လိုက်ပါပြီ!\n\n"
        f"<b>{escape(a.first_name)}</b>, ယှဉ်ပြိုင်လိုသော Character ကို ရွေးချယ်ပါ:",
        parse_mode=ParseMode.HTML,
        reply_markup=kb,
    )


async def duel_pick_a(update: Update, context: CallbackContext) -> None:
    q = update.callback_query
    parts = q.data.split(":")
    did, idx = parts[1], int(parts[2])

    state = _pending.get(did)
    if not state:
        await q.answer("⌛ Duel သက်တမ်း ကုန်ဆုံးသွားပါပြီ!", show_alert=True)
        return
    if q.from_user.id != state["challenger_id"]:
        await q.answer("❌ သင် ရွေးချယ်ရမည့် အလှည့် မဟုတ်ပါ။", show_alert=True)
        return

    await q.answer()
    state["a_pick"] = state["a_chars"][idx]

    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton(
            f"{c.get('rarity','🎴')} {c['name'][:18]}",
            callback_data=f"duel_b:{did}:{i}",
        )]
        for i, c in enumerate(state["b_chars"])
    ])
    await q.edit_message_text(
        f"⚔️ <b>{escape(state['challenger_name'])}</b> က <b>{escape(state['a_pick']['name'])}</b> ကို ရွေးချယ်လိုက်ပါပြီ!\n\n"
        f"<b>{escape(state['opponent_name'])}</b>, ယှဉ်ပြိုင်လိုသော Character ကို ရွေးချယ်ပါ:",
        parse_mode=ParseMode.HTML,
        reply_markup=kb,
    )


async def duel_pick_b(update: Update, context: CallbackContext) -> None:
    q = update.callback_query
    parts = q.data.split(":")
    did, idx = parts[1], int(parts[2])

    state = _pending.get(did)
    if not state:
        await q.answer("⌛ Duel သက်တမ်း ကုန်ဆုံးသွားပါပြီ!", show_alert=True)
        return
    if q.from_user.id != state["opponent_id"]:
        await q.answer("❌ သင် ရွေးချယ်ရမည့် အလှည့် မဟုတ်ပါ။", show_alert=True)
        return
    if state["a_pick"] is None:
        await q.answer("⌛ Challenger ရွေးချယ်သည်ကို စောင့်ဆိုင်းပါ။", show_alert=True)
        return

    await q.answer()
    _pending.pop(did, None)

    state["b_pick"] = state["b_chars"][idx]
    a_char = state["a_pick"]
    b_char = state["b_pick"]

    a_power = _power(a_char)
    b_power = _power(b_char)

    if a_power >= b_power:
        winner_id = state["challenger_id"]
        loser_id = state["opponent_id"]
        winner_name = state["challenger_name"]
        loser_name = state["opponent_name"]
        win_char = a_char["name"]
        lose_char = b_char["name"]
        w_pow, l_pow = a_power, b_power
    else:
        winner_id = state["opponent_id"]
        loser_id = state["challenger_id"]
        winner_name = state["opponent_name"]
        loser_name = state["challenger_name"]
        win_char = b_char["name"]
        lose_char = a_char["name"]
        w_pow, l_pow = b_power, a_power

    win_coins = getattr(Config, "DUEL_WIN_COINS", 150)
    lose_coins = getattr(Config, "DUEL_LOSE_COINS", 30)

    # Database updates
    await user_collection.update_one(
        {"$or": [{"id": winner_id}, {"user_id": winner_id}]},
        {"$inc": {"coins": win_coins, "xp": 100, "wins": 1}},
    )
    await user_collection.update_one(
        {"$or": [{"id": loser_id}, {"user_id": loser_id}]},
        {"$inc": {"coins": lose_coins, "xp": 25}},
    )

    await q.edit_message_text(
        f"⚔️ <b>Duel ရလဒ် ထွက်ပေါ်လာပါပြီ!</b>\n\n"
        f"🏆 <b>{escape(winner_name)}</b> က <b>{escape(win_char)}</b> ဖြင့် အနိုင်ရရှိသွားပါသည်။!\n"
        f"   ⚡ Power: <b>{w_pow}</b>\n\n"
        f"💀 <b>{escape(loser_name)}</b> က <b>{escape(lose_char)}</b> ဖြင့် ရှုံးနိမ့်သွားပါသည်။\n"
        f"   ⚡ Power: <b>{l_pow}</b>\n\n"
        f"🏅 Winner: <b>+{win_coins} 🪙</b> | <b>+100 XP</b>\n"
        f"🎖️ Loser: <b>+{lose_coins} 🪙</b> | <b>+25 XP</b>",
        parse_mode=ParseMode.HTML,
    )


application.add_handler(CommandHandler("duel", duel, block=False))
application.add_handler(CallbackQueryHandler(duel_pick_a, pattern=r"^duel_a:", block=False))
application.add_handler(CallbackQueryHandler(duel_pick_b, pattern=r"^duel_b:", block=False))
