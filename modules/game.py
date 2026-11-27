"""
NEXUS CATCH BOT
modules/game.py - Game Spawn, Catch & Collection Module
"""

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

# Runtime Memory Trackers
SPAWNED_CARDS = {}
weekly_catches_col = db['weekly_catches']
group_stats_col = db['group_stats']

# Default Spawn Threshold (စာစောင် ၁၀၀ ပြည့်တိုင်း ပုံမှန်ထွက်မည်)
DEFAULT_SPAWN_THRESHOLD = 100

async def set_spawn_threshold(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Group တစ်ခုချင်းစီအတွက် ကတ်ထွက်မည့် စာစောင်ရေ သတ်မှတ်ရန် (/setspawn)"""
    chat = update.effective_chat
    user = update.effective_user

    if not chat or chat.type == "private":
        await update.message.reply_text("❌ ဤ Command ကို Group ထဲတွင်သာ အသုံးပြုနိုင်ပါသည်။")
        return

    # Admin permission check: fail closed if Telegram cannot verify membership.
    if user.id != OWNER_ID:
        try:
            member = await chat.get_member(user.id)
        except Exception:
            await update.message.reply_text("❌ Admin ခွင့်ပြုချက်ကို စစ်ဆေးမရပါ။ ခဏနေ ပြန်ကြိုးစားပါ။")
            return
        if member.status not in ("creator", "administrator"):
            await update.message.reply_text("❌ ဤ Command ကို Group Admin များသာ အသုံးပြုနိုင်ပါသည်။")
            return

    if not context.args:
        await update.message.reply_text(
            "အသုံးပြုပုံ: <code>/setspawn [number]</code>\n"
            "ဥပမာ: <code>/setspawn 5</code> (စာ ၅ စောင်ပို့တိုင်း ကတ်ကျမည်)",
            parse_mode=ParseMode.HTML
        )
        return

    try:
        threshold = int(context.args[0])
        if threshold < 1:
            raise ValueError

        # Database ထဲတွင် Group ၏ spawn_rate သို့မဟုတ် threshold ကို သိမ်းဆည်းခြင်း
        chats_col.update_one(
            {"chat_id": chat.id},
            {"$set": {"spawn_threshold": threshold, "chat_title": chat.title or "Group Chat"}},
            upsert=True
        )

        await update.message.reply_text(
            f"✅ <b>Spawn Settings ပြောင်းလဲပြီးပါပြီ!</b>\n\n"
            f"ယခု Group အတွက် စာစောင် <b>{threshold}</b> စောင်ပြည့်တိုင်း Character ကတ်တလတ်တလတ် အလိုအလျောက် ပေါ်လာလိမ့်မည်။",
            parse_mode=ParseMode.HTML
        )
    except ValueError:
        await update.message.reply_text("❌ ကျေးဇူးပြု၍ မှန်ကန်သော ဂဏန်းအပေါင်းကိုသာ ထည့်သွင်းပါ။")

async def message_counter(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Count group messages and persist the spawned card in PostgreSQL."""
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
                        "chat_id": chat_id,
                        "chat_title": chat.title or "Group Chat",
                        "spawn_threshold": DEFAULT_SPAWN_THRESHOLD,
                        "message_count": 0,
                        "active_card": None,
                    }},
                    upsert=True,
                )
                chat_doc = chats_col.find_one_for_update({"chat_id": chat_id})
                if not chat_doc:
                    return

            # Do not replace an unclaimed card with a new one.
            if chat_doc.get("active_card"):
                return

            threshold = max(1, int(chat_doc.get("spawn_threshold", DEFAULT_SPAWN_THRESHOLD) or DEFAULT_SPAWN_THRESHOLD))
            current_count = int(chat_doc.get("message_count", 0) or 0) + 1
            if current_count < threshold:
                chats_col.update_one(
                    {"_id": chat_doc["_id"]},
                    {"$set": {"message_count": current_count, "chat_title": chat.title or "Group Chat"}},
                )
                return

            all_cards = list(cards_col.find())
            if not all_cards:
                chats_col.update_one(
                    {"_id": chat_doc["_id"]},
                    {"$set": {"message_count": 0}},
                )
                return

            spawned_card = random.choice(all_cards)
            chats_col.update_one(
                {"_id": chat_doc["_id"]},
                {"$set": {
                    "message_count": 0,
                    "chat_title": chat.title or "Group Chat",
                    "active_card": spawned_card,
                    "spawned_at": datetime.now(timezone.utc).isoformat(),
                }},
            )
            SPAWNED_CARDS[chat_id] = spawned_card
    except Exception:
        import logging
        logging.getLogger(__name__).exception("Group message counter failed for %s", chat_id)
        return

    if not spawned_card:
        return

    caption = (
        f"🍁 <b>A WILD CHARACTER APPEARED!</b>\n\n"
        f"📺 <b>Anime:</b> {escape(str(spawned_card.get('anime', 'Unknown')))}\n"
        f"🎴 <b>Rarity:</b> {escape(str(spawned_card.get('rarity', 'Common')))}\n\n"
        f"ဖမ်းယူရန် <code>/catch [Character Name]</code> ကို ရိုက်ပါ။"
    )
    try:
        image_url = spawned_card.get("img_url") or spawned_card.get("image")
        if image_url:
            await context.bot.send_photo(
                chat_id=chat_id,
                photo=image_url,
                caption=caption,
                parse_mode=ParseMode.HTML,
            )
        else:
            await context.bot.send_message(
                chat_id=chat_id,
                text=caption,
                parse_mode=ParseMode.HTML,
            )
    except Exception:
        import logging
        logging.getLogger(__name__).exception("Could not announce spawned card in %s", chat_id)


async def catch_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Claim the currently active group card exactly once."""
    chat = update.effective_chat
    user = update.effective_user
    message = update.effective_message
    if not chat or not user or not message:
        return
    chat_id = chat.id

    if not context.args:
        await message.reply_text(
            "❌ ဖမ်းယူလိုသော Character အမည်ကို ထည့်ပါ။\nဥပမာ: <code>/catch Naruto</code>",
            parse_mode=ParseMode.HTML,
        )
        return

    guess_name = " ".join(context.args).strip().casefold()
    actual_card = None
    error_message = None
    catch_bonus = 0

    try:
        now_utc = datetime.now(timezone.utc)
        week_info = now_utc.isocalendar()
        week_key = f"{week_info.year}-W{week_info.week:02d}"

        with atomic():
            chat_doc = chats_col.find_one_for_update({"chat_id": chat_id})
            actual_card = (chat_doc or {}).get("active_card") or SPAWNED_CARDS.get(chat_id)

            if not actual_card:
                error_message = "❌ ဖမ်းယူရန် ကတ်မရှိသေးပါ။ Group ထဲတွင် စာများပို့ပြီး Card ပေါ်လာအောင် စောင့်ပါ။"
            elif guess_name != str(actual_card.get("name", "")).strip().casefold():
                error_message = "❌ Character အမည် မှားယွင်းနေပါသည်။ ပြန်လည် ကြိုးစားပါ။"
            else:
                # Lock the group record and clear the active card in the same
                # transaction as the inventory and reward writes.
                if chat_doc:
                    chats_col.update_one(
                        {"_id": chat_doc["_id"]},
                        {"$set": {"active_card": None, "last_caught_by": user.id, "last_caught_at": now_utc.isoformat()}},
                    )

                card_id = actual_card.get("card_id") or actual_card.get("id")
                inventory_col.insert_one({
                    "user_id": user.id,
                    "card_id": card_id,
                    "name": actual_card.get("name"),
                    "anime": actual_card.get("anime"),
                    "rarity": actual_card.get("rarity"),
                    "edition": actual_card.get("edition", "Normal"),
                    "img_url": actual_card.get("img_url") or actual_card.get("image"),
                    "chat_id": chat_id if chat.type != "private" else None,
                    "obtained_at": now_utc.isoformat(),
                })

                account = users_col.find_one({"user_id": user.id}) or {}
                wallet_field = "coins" if "coins" in account else "balance"
                booster_until = account.get("booster_until")
                booster_uses = int(account.get("booster_uses", 0) or 0)
                if booster_until and booster_uses > 0:
                    try:
                        if datetime.fromisoformat(str(booster_until).replace("Z", "+00:00")) > now_utc:
                            catch_bonus = 50
                    except (TypeError, ValueError):
                        catch_bonus = 0

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
                    "user_id": user.id,
                    "chat_id": chat_id if chat.type != "private" else None,
                    "week": week_key,
                    "caught_at": now_utc.isoformat(),
                })
                if chat.type != "private":
                    group_stats_col.update_one(
                        {"chat_id": chat_id, "week": week_key},
                        {"$set": {"title": chat.title or "Group"},
                         "$inc": {"weekly_catches": 1}},
                        upsert=True,
                    )
    except Exception:
        import logging
        logging.getLogger(__name__).exception("Card catch transaction failed")
        await message.reply_text("❌ Catch သိမ်းဆည်းရာတွင် Error ဖြစ်နေပါသည်။ Card နှင့် Reward ကို Database မှာ မပြောင်းလဲဘဲ ထားထားပါသည်။")
        return

    if error_message:
        await message.reply_text(error_message)
        return

    SPAWNED_CARDS.pop(chat_id, None)
    await message.reply_text(
        f"🎉 <b>ဂုဏ်ယူပါတယ် {escape(user.first_name or 'Collector')}!</b>\n\n"
        f"<b>{escape(str(actual_card.get('name', 'Unknown')))}</b> "
        f"({escape(str(actual_card.get('rarity', 'Common')))}) ကို အောင်မြင်စွာ ဖမ်းယူနိုင်ခဲ့ပါပြီ!\n"
        f"🪙 +{100 + catch_bonus} Coins | ⚡ +10 XP ရရှိသည်။",
        parse_mode=ParseMode.HTML,
    )


async def collection_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/collection Command"""
    user_id = int(update.effective_user.id)
    try:
        count = inventory_col.count_documents({"user_id": user_id})
    except Exception:
        count = 0
    await update.message.reply_text(f"🎴 <b>သင့်ထံတွင် စုစုပေါင်း ကတ်ပေါင်း ({count}) ကတ် ရှိပါသည်။</b>", parse_mode=ParseMode.HTML)

async def leaderboard_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/leaderboard Command"""
    try:
        pipeline = [
            {"$group": {"_id": "$user_id", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 10}
        ]
        top_users = list(inventory_col.aggregate(pipeline))
    except Exception:
        top_users = []

    text = "🏆 <b>TOP 10 CARD COLLECTORS</b>\n⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n"
    for idx, u in enumerate(top_users, 1):
        text += f"{idx}. User ID: <code>{u['_id']}</code> — <b>{u['count']} Cards</b>\n"

    await update.message.reply_text(text, parse_mode=ParseMode.HTML)

def get_game_handlers():
    return [
        CommandHandler("setspawn", set_spawn_threshold, block=False),
        CommandHandler(["catch", "roll"], catch_command, block=False),
        CommandHandler("collection", collection_command, block=False),
        CommandHandler("leaderboard", leaderboard_command, block=False),
        MessageHandler(filters.TEXT & (~filters.COMMAND) & (~filters.ChatType.PRIVATE), message_counter, block=False)
    ]
