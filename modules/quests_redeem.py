from datetime import datetime, timezone
from html import escape
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import CommandHandler, ContextTypes

from database import atomic, cards_col, codes_col, inventory_col, market_col, users_col

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

def _date_value(value):
    if value in (None, "", 0):
        return None
    try:
        if isinstance(value, (int, float)):
            return datetime.fromtimestamp(value, timezone.utc).date()
        if isinstance(value, str):
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        elif isinstance(value, datetime):
            parsed = value
        else:
            return None
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc).date()
    except (TypeError, ValueError, OverflowError, OSError):
        return None


async def quest_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = int(update.effective_user.id)
    today = datetime.now(timezone.utc).date().isoformat()

    def progress():
        user_doc = users_col.find_one({"user_id": user_id}) or {}
        daily_done = _date_value(user_doc.get("last_daily")) == datetime.fromisoformat(today).date()
        caught_today = sum(
            1 for item in inventory_col.find({"user_id": user_id})
            if _date_value(item.get("obtained_at")) == datetime.fromisoformat(today).date()
        )
        listed_today = int(
            _date_value(user_doc.get("market_listed_date")) == datetime.fromisoformat(today).date()
        )
        return user_doc, daily_done, caught_today, listed_today

    if context.args and context.args[0].lower() == "claim":
        failure = None
        try:
            with atomic():
                user_doc = users_col.find_one_for_update({"user_id": user_id}) or {}
                user_doc, daily_done, caught_today, listed_today = progress()
                if user_doc.get("daily_quest_claim_date") == today:
                    failure = "⏳ ဒီနေ့ Quest Reward ကို ရယူပြီးပါပြီ။"
                elif not daily_done or caught_today < 3 or listed_today < 1:
                    failure = "❌ Quest မပြီးသေးပါ။ /quest ဖြင့် လက်ရှိ Progress ကို ကြည့်ပါ။"
                else:
                    result = users_col.update_one(
                        {"user_id": user_id, "daily_quest_claim_date": {"$ne": today}},
                        {"$inc": {"gems": 50}, "$set": {"daily_quest_claim_date": today}},
                    )
                    if result.modified_count != 1:
                        failure = "⏳ Quest Reward ကို တစ်ကြိမ်သာ ရယူနိုင်ပါသည်။"
        except Exception:
            failure = "❌ Quest Reward ရယူရာတွင် Error ဖြစ်နေပါသည်။"
        if failure:
            await update.effective_message.reply_text(failure)
            return
        await update.effective_message.reply_text(
            "🎉 <b>DAILY QUEST COMPLETED!</b>\n💎 <b>+50 Gems</b> ရရှိပါပြီ။",
            parse_mode=ParseMode.HTML,
        )
        return

    user_doc, daily_done, caught_today, listed_today = progress()
    claimed = user_doc.get("daily_quest_claim_date") == today
    daily_mark = "✅" if daily_done else "⬜"
    catch_mark = "✅" if caught_today >= 3 else "⬜"
    market_mark = "✅" if listed_today >= 1 else "⬜"
    all_done = daily_done and caught_today >= 3 and listed_today >= 1
    reward_status = "ရယူပြီးပါပြီ" if claimed else ("<code>/quest claim</code> ဖြင့် ရယူပါ" if all_done else "Quest အားလုံး ပြီးအောင်လုပ်ပါ")
    await update.effective_message.reply_text(
        "📜 <b>DAILY QUESTS</b>\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
        f"{daily_mark} Daily Reward ယူပါ — <b>{'1/1' if daily_done else '0/1'}</b>\n"
        f"{catch_mark} Card 3 ကတ် ဖမ်းပါ — <b>{min(caught_today, 3)}/3</b>\n"
        f"{market_mark} Market တွင် Card 1 ကတ် တင်ပါ — <b>{min(listed_today, 1)}/1</b>\n\n"
        f"🎁 Reward: <b>+50 Gems</b>\n{reward_status}",
        parse_mode=ParseMode.HTML,
    )


def get_quests_redeem_handlers():
    return [
        CommandHandler(["redeem", "promo"], redeem_command, block=False),
        CommandHandler(["recycle", "disassemble", "exchange"], recycle_command, block=False),
        CommandHandler("quest", quest_command, block=False)
    ]
