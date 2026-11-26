"""Nexus Catch collection upgrades: weekly rewards, chests, owner lookup and auctions."""
import random
from datetime import datetime, timedelta, timezone
from html import escape

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import CommandHandler, ContextTypes

from database import (
    atomic, db, users_col, inventory_col, cards_col, market_col,
)

auctions_col = db["auctions"]
weekly_catches_col = db["weekly_catches"]
group_stats_col = db["group_stats"]


def _week_key():
    now = datetime.now(timezone.utc).isocalendar()
    return f"{now.year}-W{now.week:02d}"


def _balance_field(user_doc):
    return "coins" if "coins" in user_doc else "balance"


async def weekly_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    week = _week_key()
    coins, gems = 5000, 25
    try:
        with atomic():
            result = users_col.update_one(
                {"user_id": uid, "weekly_claim_week": {"$ne": week}},
                {"$inc": {"coins": coins, "gems": gems},
                 "$set": {"weekly_claim_week": week}},
                upsert=True,
            )
            if result.modified_count != 1 and result.upserted_id is None:
                await update.effective_message.reply_text("⏳ ဒီအပတ် Weekly Reward ကို ရယူပြီးပါပြီ။ နောက်အပတ်မှ ပြန်လာခဲ့ပါ။")
                return
    except Exception:
        await update.effective_message.reply_text("❌ Weekly Reward ရယူရာတွင် Error ဖြစ်နေပါသည်။")
        return
    await update.effective_message.reply_text(
        "╭━━━━━━━━━━━━━━━━━━╮\n🎁 <b>WEEKLY REWARD</b>\n╰━━━━━━━━━━━━━━━━━━╯\n\n"
        f"🪙 Coins: <b>+{coins:,}</b>\n💎 Gems: <b>+{gems}</b>\n"
        "✨ နောက်အပတ်လည်း ပြန်လာခဲ့ပါ!",
        parse_mode=ParseMode.HTML,
    )


async def streak_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    doc = users_col.find_one({"user_id": update.effective_user.id}) or {}
    streak = int(doc.get("daily_streak", 0) or 0)
    last = doc.get("last_daily") or "မရယူရသေးပါ"
    await update.effective_message.reply_text(
        "🔥 <b>DAILY STREAK</b>\n\n"
        f"🔥 လက်ရှိ Streak: <b>{streak} ရက်</b>\n"
        f"🗓️ နောက်ဆုံး Daily: <code>{escape(str(last))}</code>\n"
        "🎁 Streak ဆက်လက်ထိန်းထားရန် နေ့တိုင်း /daily ယူပါ။",
        parse_mode=ParseMode.HTML,
    )


async def find_owner_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.effective_message.reply_text("အသုံးပြုပုံ: <code>/owner [Card ID]</code>", parse_mode=ParseMode.HTML)
        return
    card_id = context.args[0].strip()
    holders = list(inventory_col.find({"card_id": card_id}))
    if not holders:
        await update.effective_message.reply_text("🔎 ဒီ Card ကို လက်ရှိ ဘယ်သူမှ မပိုင်ဆိုင်သေးပါ။")
        return
    lines = []
    seen = set()
    for item in holders:
        uid = item.get("user_id")
        if uid in seen:
            continue
        seen.add(uid)
        user = users_col.find_one({"user_id": uid}) or {}
        label = escape(user.get("first_name") or user.get("username") or f"User {uid}")
        lines.append(f"👤 {label} — <code>{uid}</code>")
    await update.effective_message.reply_text(
        f"🔍 <b>CARD OWNER SEARCH</b>\n🎴 {escape(str(holders[0].get('name') or card_id))}\n\n"
        + "\n".join(lines[:20]), parse_mode=ParseMode.HTML,
    )


CHESTS = {
    "common": (500, "Common Chest"),
    "rare": (2000, "Rare Chest"),
    "legendary": (50, "Legendary Crate"),
}


async def chest_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args or context.args[0].lower() not in CHESTS:
        await update.effective_message.reply_text(
            "📦 <b>CARD CHESTS</b>\n"
            "• <code>/chest common</code> — 500 Coins\n"
            "• <code>/chest rare</code> — 2,000 Coins\n"
            "• <code>/chest legendary</code> — 50 Gems",
            parse_mode=ParseMode.HTML,
        )
        return
    kind = context.args[0].lower()
    cost, label = CHESTS[kind]
    cards = list(cards_col.find())
    if not cards:
        await update.effective_message.reply_text("❌ Card Database ထဲတွင် ဖွင့်ရန်ကတ် မရှိသေးပါ။")
        return
    card = random.choice(cards)
    uid = update.effective_user.id
    try:
        with atomic():
            user = users_col.find_one({"user_id": uid}) or {"user_id": uid}
            currency = "gems" if kind == "legendary" else _balance_field(user)
            debit = users_col.update_one(
                {"user_id": uid, currency: {"$gte": cost}},
                {"$inc": {currency: -cost}},
            )
            if debit.modified_count != 1:
                await update.effective_message.reply_text("❌ လက်ကျန်ငွေ မလုံလောက်ပါ။")
                return
            inventory_col.insert_one({
                "user_id": uid,
                "card_id": card.get("card_id") or card.get("id"),
                "name": card.get("name", "Unknown"),
                "anime": card.get("anime", "Unknown"),
                "rarity": card.get("rarity", "Common"),
                "edition": card.get("edition", "Normal"),
                "img_url": card.get("img_url") or card.get("image"),
                "obtained_at": datetime.now(timezone.utc).isoformat(),
            })
    except Exception:
        await update.effective_message.reply_text("❌ Chest ဖွင့်ရာတွင် Error ဖြစ်နေပါသည်။")
        return
    await update.effective_message.reply_text(
        f"🎉 <b>{escape(label)} OPENED!</b>\n\n"
        f"🎴 <b>{escape(str(card.get('name', 'Unknown')))}</b>\n"
        f"✨ {escape(str(card.get('rarity', 'Common')))}\n"
        f"🪙 Cost: {cost} {'Gems' if kind == 'legendary' else 'Coins'}",
        parse_mode=ParseMode.HTML,
    )


async def auction_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    user = update.effective_user
    if not context.args:
        await msg.reply_text(
            "🔨 <b>AUCTION</b>\n"
            "<code>/auction start [CardID] [MinBid] [Hours]</code>\n"
            "<code>/auction bid [AuctionID] [Amount]</code>\n"
            "<code>/auction close [AuctionID]</code>\n"
            "<code>/auction list</code>",
            parse_mode=ParseMode.HTML,
        )
        return
    action = context.args[0].lower()
    try:
        if action == "list":
            rows = list(auctions_col.find())
            if not rows:
                await msg.reply_text("🔨 လက်ရှိ Auction မရှိသေးပါ။")
                return
            lines = [f"🆔 <code>{escape(str(a['_id']))}</code> | {escape(str(a.get('name')))} | Bid: {int(a.get('highest_bid', a.get('min_bid', 0))):,}" for a in rows[:15]]
            await msg.reply_text("🔨 <b>LIVE AUCTIONS</b>\n\n" + "\n".join(lines), parse_mode=ParseMode.HTML)
            return

        if action == "start":
            if len(context.args) < 4:
                await msg.reply_text("အသုံးပြုပုံ: <code>/auction start [CardID] [MinBid] [Hours]</code>", parse_mode=ParseMode.HTML)
                return
            card_id, minimum, hours = context.args[1], int(context.args[2]), int(context.args[3])
            if minimum < 1 or not 1 <= hours <= 168:
                await msg.reply_text("❌ MinBid သည် 1 အထက်၊ ကြာချိန်သည် 1–168 နာရီ ဖြစ်ရပါမည်။")
                return
            with atomic():
                card = inventory_col.find_one({"user_id": user.id, "card_id": card_id})
                if not card:
                    await msg.reply_text("❌ သင့်ထံတွင် ထို Card မရှိပါ။")
                    return
                removed = inventory_col.delete_one({"_id": card["_id"], "user_id": user.id})
                if removed.deleted_count != 1:
                    await msg.reply_text("❌ Card ပိုင်ဆိုင်မှု အတည်မပြုနိုင်ပါ။")
                    return
                result = auctions_col.insert_one({
                    "seller_id": user.id, "seller_name": user.first_name,
                    "card": {k: card.get(k) for k in ("card_id", "name", "anime", "rarity", "edition", "img_url")},
                    "min_bid": minimum, "highest_bid": 0, "highest_bidder": None,
                    "expires_at": (datetime.now(timezone.utc) + timedelta(hours=hours)).isoformat(),
                })
            await msg.reply_text(f"🔨 Auction ဖွင့်ပြီးပါပြီ!\n🆔 <code>{result.inserted_id}</code>\n🎴 {escape(str(card.get('name')))}\n💰 Minimum: {minimum:,} Coins", parse_mode=ParseMode.HTML)
            return

        if action == "bid":
            if len(context.args) < 3:
                await msg.reply_text("အသုံးပြုပုံ: <code>/auction bid [AuctionID] [Amount]</code>", parse_mode=ParseMode.HTML)
                return
            auction_id, amount = context.args[1], int(context.args[2])
            with atomic():
                auction = auctions_col.find_one({"_id": auction_id})
                if not auction or datetime.fromisoformat(auction["expires_at"]) <= datetime.now(timezone.utc):
                    await msg.reply_text("❌ Auction မရှိတော့ပါ သို့မဟုတ် သက်တမ်းကုန်ပါပြီ။")
                    return
                if auction["seller_id"] == user.id or amount < max(int(auction["min_bid"]), int(auction.get("highest_bid", 0)) + 1):
                    await msg.reply_text("❌ Bid ပမာဏ မမှန်ပါ သို့မဟုတ် ကိုယ့် Auction ကို Bid မလုပ်နိုင်ပါ။")
                    return
                bidder = users_col.find_one({"user_id": user.id}) or {}
                field = _balance_field(bidder)
                debit = users_col.update_one({"user_id": user.id, field: {"$gte": amount}}, {"$inc": {field: -amount}})
                if debit.modified_count != 1:
                    await msg.reply_text("❌ Coins မလုံလောက်ပါ။")
                    return
                previous = auction.get("highest_bidder")
                if previous:
                    prev_doc = users_col.find_one({"user_id": previous}) or {}
                    prev_field = auction.get("bid_currency_field") or _balance_field(prev_doc)
                    users_col.update_one({"user_id": previous}, {"$inc": {prev_field: int(auction.get("highest_bid", 0))}})
                auctions_col.update_one({"_id": auction_id}, {"$set": {
                    "highest_bid": amount, "highest_bidder": user.id, "bid_currency_field": field,
                }})
            await msg.reply_text(f"✅ Bid အောင်မြင်ပါပြီ! <b>{amount:,} Coins</b>", parse_mode=ParseMode.HTML)
            return

        if action == "close":
            if len(context.args) < 2:
                await msg.reply_text("အသုံးပြုပုံ: <code>/auction close [AuctionID]</code>", parse_mode=ParseMode.HTML)
                return
            auction_id = context.args[1]
            with atomic():
                auction = auctions_col.find_one({"_id": auction_id})
                if not auction:
                    await msg.reply_text("❌ Auction မတွေ့ပါ။")
                    return
                expired = datetime.fromisoformat(auction["expires_at"]) <= datetime.now(timezone.utc)
                if auction["seller_id"] != user.id and not expired:
                    await msg.reply_text("⏳ Auction ကို ပိုင်ရှင်သာပိတ်နိုင်ပြီး သက်တမ်းကုန်မှ အခြားသူများ ပိတ်နိုင်ပါသည်။")
                    return
                winner = auction.get("highest_bidder")
                card = dict(auction.get("card") or {})
                if winner:
                    inventory_col.insert_one({"user_id": winner, **card, "obtained_at": datetime.now(timezone.utc).isoformat()})
                    seller_doc = users_col.find_one({"user_id": auction["seller_id"]}) or {}
                    seller_field = _balance_field(seller_doc)
                    users_col.update_one({"user_id": auction["seller_id"]}, {"$inc": {seller_field: int(auction.get("highest_bid", 0))}})
                else:
                    inventory_col.insert_one({"user_id": auction["seller_id"], **card})
                auctions_col.delete_one({"_id": auction_id})
            await msg.reply_text("🏁 Auction ပိတ်ပြီးပါပြီ။ " + ("အနိုင်ရသူထံ Card ပို့ပြီး Seller ကို ငွေလွှဲပြီးပါပြီ။" if winner else "Bid မရှိသောကြောင့် Card ကို ပိုင်ရှင်ထံ ပြန်ပို့ပြီးပါပြီ။"))
            return

        await msg.reply_text("❌ Auction action မမှန်ပါ။ <code>/auction</code> ကိုကြည့်ပါ။", parse_mode=ParseMode.HTML)
    except (ValueError, KeyError):
        await msg.reply_text("❌ ID၊ Amount သို့မဟုတ် Hours တန်ဖိုး မမှန်ပါ။")
    except Exception:
        await msg.reply_text("❌ Auction လုပ်ဆောင်ရာတွင် Error ဖြစ်နေပါသည်။")


async def weekly_ranking_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    week = _week_key()
    rows = list(weekly_catches_col.find({"week": week}))
    counts = {}
    for row in rows:
        uid = row.get("user_id")
        counts[uid] = counts.get(uid, 0) + 1
    ranked = sorted(counts.items(), key=lambda x: x[1], reverse=True)[:10]
    if not ranked:
        await update.effective_message.reply_text("🏆 ဒီအပတ် Catch Ranking မရှိသေးပါ။")
        return
    lines = []
    for i, (uid, count) in enumerate(ranked, 1):
        user_doc = users_col.find_one({"user_id": uid}) or {}
        name = escape(user_doc.get("first_name") or f"User {uid}")
        lines.append(f"{i}. {name} — <b>{count}</b> catches")
    await update.effective_message.reply_text("🏆 <b>WEEKLY RANKING</b>\n\n" + "\n".join(lines), parse_mode=ParseMode.HTML)


async def top_groups_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    rows = list(group_stats_col.find())
    rows.sort(key=lambda x: int(x.get("weekly_catches", 0)), reverse=True)
    if not rows:
        await update.effective_message.reply_text("🏘️ Group Catch စာရင်း မရှိသေးပါ။")
        return
    lines = [f"{i}. {escape(str(r.get('title') or r.get('chat_id')))} — <b>{int(r.get('weekly_catches', 0))}</b> catches" for i, r in enumerate(rows[:10], 1)]
    await update.effective_message.reply_text("🏘️ <b>TOP GROUPS THIS WEEK</b>\n\n" + "\n".join(lines), parse_mode=ParseMode.HTML)


def get_collection_upgrade_handlers():
    return [
        CommandHandler("weekly", weekly_command),
        CommandHandler("streak", streak_command),
        CommandHandler(["owner", "findowner"], find_owner_command),
        CommandHandler("chest", chest_command),
        CommandHandler("auction", auction_command),
        CommandHandler(["weeklytop", "weeklyranking"], weekly_ranking_command),
        CommandHandler("topgroups", top_groups_command),
    ]
