"""Nexus Catch group card spawning and verified catching."""
import random
from datetime import datetime, timezone
from html import escape
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes, CommandHandler, MessageHandler, filters

from database import atomic, cards_col, inventory_col, users_col, chats_col, db

try:
    from config import OWNER_ID
except ImportError:
    OWNER_ID = 0

SPAWNED_CARDS = {}
weekly_catches_col = db["weekly_catches"]
group_stats_col = db["group_stats"]
DEFAULT_SPAWN_THRESHOLD = 100

HIGH_RARITIES = {
    "Legendary", "Mythic", "Divine", "Celestial", "Eternal",
    "Ultimate", "Supreme", "Transcendent", "Premium Edition",
}

def _utcnow():
    return datetime.now(timezone.utc)

def _parse_time(value):
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
    except (TypeError, ValueError):
        return None

async def set_spawn_threshold(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat, user = update.effective_chat, update.effective_user
    if not chat or chat.type == "private":
        await update.effective_message.reply_text("❌ ဤ Command ကို Group ထဲတွင်သာ အသုံးပြုနိုင်ပါသည်။")
        return
    if user.id != OWNER_ID:
        try:
            member = await chat.get_member(user.id)
        except Exception:
            await update.effective_message.reply_text("❌ Admin ခွင့်ပြုချက် စစ်ဆေးမရပါ။")
            return
        if member.status not in ("creator", "administrator"):
            await update.effective_message.reply_text("❌ Group Admin များသာ အသုံးပြုနိုင်ပါသည်။")
            return
    if not context.args:
        await update.effective_message.reply_text("အသုံးပြုပုံ: /setspawn [number]")
        return
    try:
        threshold = int(context.args[0])
        if not 1 <= threshold <= 100000:
            raise ValueError
    except ValueError:
        await update.effective_message.reply_text("❌ 1 မှ 100000 အတွင်း ဂဏန်းထည့်ပါ။")
        return
    chats_col.update_one(
        {"chat_id": chat.id},
        {"$set": {"spawn_threshold": threshold, "chat_title": chat.title or "Group"}},
        upsert=True,
    )
    await update.effective_message.reply_text(f"✅ စာ {threshold} စောင်ပြည့်တိုင်း Card Drop ဖြစ်ပါမည်။")


async def message_counter(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat = update.effective_chat
    if not chat or chat.type == "private":
        return
    chat_id = chat.id
    spawned_card = None
    try:
        with atomic():
            chat_doc = chats_col.find_one_for_update({"chat_id": chat_id})
            if not chat_doc:
                chats_col.update_one(
                    {"chat_id": chat_id},
                    {"$setOnInsert": {
                        "chat_id": chat_id, "chat_title": chat.title or "Group Chat",
                        "spawn_threshold": DEFAULT_SPAWN_THRESHOLD, "message_count": 0,
                        "active_card": None,
                    }},
                    upsert=True,
                )
                chat_doc = chats_col.find_one_for_update({"chat_id": chat_id})
                if not chat_doc:
                    return
            if chat_doc.get("active_card"):
                return
            threshold = max(1, int(chat_doc.get("spawn_threshold", DEFAULT_SPAWN_THRESHOLD) or DEFAULT_SPAWN_THRESHOLD))
            count = int(chat_doc.get("message_count", 0) or 0) + 1
            if count < threshold:
                chats_col.update_one(
                    {"_id": chat_doc["_id"]},
                    {"$set": {"message_count": count, "chat_title": chat.title or "Group"}},
                )
                return
            all_cards = list(cards_col.find())
            if not all_cards:
                chats_col.update_one({"_id": chat_doc["_id"]}, {"$set": {"message_count": 0}})
                return
            try:
                from modules.spawn_settings import choose_weighted_card
                spawned_card = choose_weighted_card(all_cards)
            except Exception:
                spawned_card = random.choice(all_cards)
            if not spawned_card:
                spawned_card = random.choice(all_cards)
            spawn_time = _utcnow().isoformat()
            chats_col.update_one(
                {"_id": chat_doc["_id"]},
                {"$set": {
                    "message_count": 0, "chat_title": chat.title or "Group",
                    "active_card": spawned_card, "spawned_at": spawn_time,
                }},
            )
            SPAWNED_CARDS[chat_id] = spawned_card
    except Exception:
        import logging
        logging.getLogger(__name__).exception("Group message counter failed for %s", chat_id)
        return

    if not spawned_card:
        return
    rarity = str(spawned_card.get("rarity", "Common"))
    styles = {
        "Common": "🍃", "Uncommon": "🌿", "Rare": "💠", "Epic": "✨",
        "Legendary": "🏆", "Mythic": "🔥", "Divine": "⚜️",
        "Celestial": "🌌", "Eternal": "♾️", "Ultimate": "⚡",
        "Supreme": "👑", "Transcendent": "🌠", "Premium Edition": "💎",
    }
    emoji = styles.get(rarity, "🎴")
    caption = (
        "╭━━━━━━━━━━━━━━━━━━╮\n"
        f"      {emoji} <b>NEXUS CARD DROP</b> {emoji}\n"
        "╰━━━━━━━━━━━━━━━━━━╯\n\n"
        f"🎬 <b>Anime:</b> {escape(str(spawned_card.get('anime', 'Unknown')))}\n"
        f"💎 <b>Rarity:</b> <b>{escape(rarity)}</b>\n\n"
        "🔎 <b>Who will claim this character?</b>\n"
        "ဖမ်းယူရန် <code>/catch [Character Name]</code> ရိုက်ပါ။"
    )
    try:
        image_url = spawned_card.get("img_url") or spawned_card.get("image")
        if image_url:
            await context.bot.send_photo(chat_id=chat_id, photo=image_url, caption=caption, parse_mode=ParseMode.HTML)
        else:
            await context.bot.send_message(chat_id=chat_id, text=caption, parse_mode=ParseMode.HTML)
    except Exception:
        import logging
        logging.getLogger(__name__).exception("Could not announce spawned card in %s", chat_id)


async def catch_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat, user, message = update.effective_chat, update.effective_user, update.effective_message
    if not chat or not user or not message:
        return
    if not context.args:
        await message.reply_text("❌ အသုံးပြုပုံ: /catch [Character Name] [Verification Answer]")
        return

    # Last numeric argument is a human verification answer for high-rarity cards.
    answer = None
    name_parts = list(context.args)
    if len(name_parts) >= 2 and name_parts[-1].isdigit():
        answer = int(name_parts.pop())
    guess_name = " ".join(name_parts).strip().casefold()
    actual_card = None
    error_message = None
    catch_bonus = 0
    challenge_question = None
    now = _utcnow()

    try:
        week_info = now.isocalendar()
        week_key = f"{week_info.year}-W{week_info.week:02d}"
        with atomic():
            chat_doc = chats_col.find_one_for_update({"chat_id": chat.id})
            actual_card = (chat_doc or {}).get("active_card") or SPAWNED_CARDS.get(chat.id)
            if not actual_card:
                error_message = "❌ ဖမ်းယူရန် Card မရှိသေးပါ။"
            elif guess_name != str(actual_card.get("name", "")).strip().casefold():
                error_message = "❌ Character အမည် မှားနေပါသည်။"
            else:
                rarity = str(actual_card.get("rarity", "Common"))
                spawned_at = _parse_time((chat_doc or {}).get("spawned_at"))
                min_wait = 2 if rarity not in HIGH_RARITIES else 5
                if spawned_at and (now - spawned_at).total_seconds() < min_wait:
                    remaining = max(1, int(min_wait - (now - spawned_at).total_seconds()))
                    error_message = f"⏳ Card ကို သေချာကြည့်ပြီး {remaining} စက္ကန့်နောက်မှ ပြန်ဖမ်းပါ။"

                if not error_message and rarity in HIGH_RARITIES:
                    account = users_col.find_one({"user_id": user.id}) or {}
                    pending = account.get("catch_verification") or {}
                    valid_pending = (
                        pending.get("chat_id") == chat.id
                        and str(pending.get("card_name", "")).casefold() == guess_name
                        and pending.get("expires_at", 0) >= int(now.timestamp())
                    )
                    if not valid_pending:
                        a, b = random.randint(2, 9), random.randint(2, 9)
                        challenge_question = (a, b)
                        users_col.update_one(
                            {"user_id": user.id},
                            {"$set": {"catch_verification": {
                                "chat_id": chat.id, "card_name": guess_name,
                                "answer": a + b, "expires_at": int(now.timestamp()) + 90,
                            }}},
                            upsert=True,
                        )
                        error_message = f"🛡️ <b>HUMAN CHECK</b>\nAuto-catch ကာကွယ်ရန် <b>{a} + {b} = ?</b> ကို ဖြေပါ။\nပြီးလျှင် <code>/catch {escape(str(actual_card.get('name', '')))} [အဖြေ]</code> ရိုက်ပါ။"
                    elif answer is None:
                        error_message = "🛡️ အတည်ပြုရန် သင်္ချာမေးခွန်းအဖြေကို Command နောက်ဆုံးတွင် ထည့်ပါ။"
                    elif answer != int(pending.get("answer", -1)):
                        error_message = "❌ အဖြေမှားနေပါသည်။ /catch ဖြင့် ပြန်စမ်းပါ။"
                    else:
                        users_col.update_one({"user_id": user.id}, {"$unset": {"catch_verification": ""}})

                if not error_message:
                    if chat_doc:
                        chats_col.update_one(
                            {"_id": chat_doc["_id"]},
                            {"$set": {"active_card": None, "last_caught_by": user.id, "last_caught_at": now.isoformat()}},
                        )
                    card_id = actual_card.get("card_id") or actual_card.get("id")
                    inventory_col.insert_one({
                        "user_id": user.id, "card_id": card_id, "name": actual_card.get("name"),
                        "anime": actual_card.get("anime"), "rarity": actual_card.get("rarity"),
                        "edition": actual_card.get("edition", "Normal"),
                        "img_url": actual_card.get("img_url") or actual_card.get("image"),
                        "chat_id": chat.id if chat.type != "private" else None,
                        "obtained_at": now.isoformat(), "source": "catch",
                    })
                    account = users_col.find_one({"user_id": user.id}) or {}
                    wallet_field = "coins" if "coins" in account else "balance"
                    booster_until = _parse_time(account.get("booster_until"))
                    booster_uses = int(account.get("booster_uses", 0) or 0)
                    if booster_until and booster_until > now and booster_uses > 0:
                        catch_bonus = 50
                    increments = {wallet_field: 100 + catch_bonus, "xp": 10}
                    if catch_bonus:
                        increments["booster_uses"] = -1
                    users_col.update_one(
                        {"user_id": user.id},
                        {"$inc": increments, "$set": {
                            "first_name": user.first_name or "Collector",
                            "username": user.username or "",
                        }},
                        upsert=True,
                    )
                    weekly_catches_col.insert_one({
                        "user_id": user.id, "chat_id": chat.id if chat.type != "private" else None,
                        "week": week_key, "caught_at": now.isoformat(),
                    })
                    if chat.type != "private":
                        group_stats_col.update_one(
                            {"chat_id": chat.id, "week": week_key},
                            {"$set": {"title": chat.title or "Group"}, "$inc": {"weekly_catches": 1}},
                            upsert=True,
                        )
    except Exception:
        import logging
        logging.getLogger(__name__).exception("Card catch transaction failed")
        await message.reply_text("❌ Catch သိမ်းဆည်းရာတွင် Error ဖြစ်နေပါသည်။ Database အပြောင်းအလဲ မပြီးမြောက်ပါ။")
        return

    if error_message:
        await message.reply_text(error_message, parse_mode=ParseMode.HTML)
        return
    SPAWNED_CARDS.pop(chat.id, None)
    await message.reply_text(
        f"╭━━━━━━━━━━━━━━━━━━╮\n"
        f"       🎉 <b>CARD CAPTURED!</b>\n"
        f"╰━━━━━━━━━━━━━━━━━━╯\n\n"
        f"🌸 <b>{escape(str(actual_card.get('name', 'Unknown')))}</b>\n"
        f"💎 Rarity: <b>{escape(str(actual_card.get('rarity', 'Common')))}</b>\n"
        f"🪙 +{100 + catch_bonus} Coins  |  ⚡ +10 XP",
        parse_mode=ParseMode.HTML,
    )


async def collection_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    count = inventory_col.count_documents({"user_id": update.effective_user.id})
    await update.effective_message.reply_text(f"🎴 သင့်တွင် Card {count} ကတ် ရှိပါသည်။")

async def leaderboard_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        rows = list(inventory_col.aggregate([
            {"$group": {"_id": "$user_id", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}, {"$limit": 10},
        ]))
    except Exception:
        rows = []
    body = "\n".join(f"{i}. <code>{r['_id']}</code> — {r['count']} Cards" for i, r in enumerate(rows, 1))
    await update.effective_message.reply_text("🏆 <b>TOP 10 CARD COLLECTORS</b>\n" + (body or "မရှိသေးပါ။"), parse_mode=ParseMode.HTML)

def get_game_handlers():
    return [
        CommandHandler("setspawn", set_spawn_threshold, block=False),
        CommandHandler(["catch", "roll"], catch_command, block=False),
        CommandHandler("collection", collection_command, block=False),
        CommandHandler("leaderboard", leaderboard_command, block=False),
        MessageHandler(filters.TEXT & (~filters.COMMAND) & (~filters.ChatType.PRIVATE), message_counter, block=False),
    ]
