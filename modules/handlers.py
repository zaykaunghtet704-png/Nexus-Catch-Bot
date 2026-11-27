"""
modules/handlers.py - User Profile, Check & Balance Handlers
"""
import math
from html import escape
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import CommandHandler, ContextTypes
from database import users_col, inventory_col, cards_col
from modules.force_join import check_must_join


def get_coins_and_gems(user_doc: dict):
    coins = user_doc.get("coins")
    if coins is None:
        coins = user_doc.get("balance", 0)
    gems = user_doc.get("gems", 0)
    return coins, gems


def calculate_level(xp: int):
    level = int(math.sqrt(xp / 10)) if xp > 0 else 1
    current_level_xp = (level ** 2) * 10
    next_level_xp = ((level + 1) ** 2) * 10
    needed = next_level_xp - current_level_xp
    gained = xp - current_level_xp
    
    progress = min(max(int((gained / max(needed, 1)) * 10), 0), 10)
    bar = "■" * progress + "□" * (10 - progress)
    return level, bar


async def profile_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/profile Command - Rarity Tier (၁၃) ခု အစဉ်လိုက် ပြသခြင်း"""
    user = update.effective_user
    target_user_id = user.id
    target_first_name = user.first_name

    if update.message and update.message.reply_to_message:
        target_user_id = update.message.reply_to_message.from_user.id
        target_first_name = update.message.reply_to_message.from_user.first_name
    elif context.args:
        try:
            target_user_id = int(context.args[0])
            u_doc = users_col.find_one({"user_id": target_user_id}) or {}
            target_first_name = u_doc.get("first_name", f"User {target_user_id}")
        except ValueError:
            pass

    user_doc = users_col.find_one({"user_id": target_user_id}) or {}
    coins, gems = get_coins_and_gems(user_doc)
    xp = user_doc.get("xp", 0)
    level, bar = calculate_level(xp)

    total_cards = inventory_col.count_documents({"user_id": target_user_id})
    unique_card_ids = set(inventory_col.distinct("card_id", {"user_id": target_user_id}))
    unique_card_ids.update(inventory_col.distinct("id", {"user_id": target_user_id}))
    unique_cards = len({str(card_id) for card_id in unique_card_ids if card_id not in (None, "")})
    total_global_cards = cards_col.count_documents({}) or 1
    harem_pct = (unique_cards / total_global_cards) * 100

    # Rarity (၁၃) ခု အမြင့်ဆုံးမှ အနိမ့်ဆုံး အစီအစဉ်အတိုင်း Emoji များနှင့်တကွ
    rarity_list = [
        ("Premium Edition", "👑"),
        ("Supreme", "🌀"),
        ("Cataphract", "⚔️"),
        ("CrossVerse", "💎"),
        ("Divine", "⚜️️"),
        ("Mystical", "🔥"),
        ("Ancient", "📜"),
        ("Mythic", "🔴"),
        ("Legendary", "🏆"),
        ("Epic", "✨"),
        ("Rare", "🎁"),
        ("Uncommon", "🔮"),
        ("Common", "🧊")
    ]

    rarity_lines = []
    for r_name, r_emoji in rarity_list:
        count = inventory_col.count_documents({"user_id": target_user_id, "rarity": r_name})
        rarity_lines.append(f"├─► {r_emoji} <b>RARITY: {r_name}: {count}</b>")

    pipeline = [
        {"$group": {"_id": "$user_id", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}
    ]
    all_collectors = list(inventory_col.aggregate(pipeline))
    global_pos = "N/A"
    for idx, u in enumerate(all_collectors, 1):
        if u["_id"] == target_user_id:
            global_pos = idx
            break

    profile_text = (
        f"╭━━━━━━━━━━━━━━━━━━╮\n"
        f"      👑 <b>COLLECTOR PROFILE</b>\n"
        f"╰━━━━━━━━━━━━━━━━━━╯\n\n"
        f"👤 <b>Collector:</b> {escape(target_first_name)}\n"
        f"🆔 <b>ID:</b> <code>{target_user_id}</code>\n\n"
        f"💰 <b>WALLET</b>\n"
        f"├ 🪙 Coins: <b>{coins:,}</b>\n"
        f"└ 💎 Gems: <b>{gems:,}</b>\n\n"
        f"🃏 <b>COLLECTION</b>\n"
        f"├ 🎴 Total Cards: <b>{total_cards}</b>\n"
        f"├ ✨ Unique Cards: <b>{unique_cards}</b>\n"
        f"└ 🌸 Completion: <b>{harem_pct:.2f}%</b>\n\n"
        f"🌟 <b>FAVORITE SHOWCASE</b>\n"
        f"├ 🎴 {escape(str(user_doc.get('favorite_card') or 'Not selected'))}\n"
        f"└ 🆔 {escape(str(user_doc.get('favorite_card_id') or '—'))}\n\n"
        f"⚡ <b>LEVEL {level}</b>\n"
        f"<code>[{bar}]</code>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        + "\n".join(rarity_lines) +
        f"\n─────────────────────────\n"
        f"🏆 <b>GLOBAL COLLECTOR RANK:</b> #{global_pos}\n"
        f"💫 <i>Keep collecting and climb the ranks!</i>\n"
    )

    await update.message.reply_text(profile_text, parse_mode=ParseMode.HTML)


async def check_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/check [card_id] Command"""
    if not context.args:
        await update.message.reply_text("အသုံးပြုပုံ: <code>/check [card_id]</code>", parse_mode=ParseMode.HTML)
        return

    card_id = context.args[0].strip()
    card = cards_col.find_one({"$or": [{"card_id": card_id}, {"id": card_id}]})

    if not card:
        await update.message.reply_text("🔎 <b>CARD NOT FOUND</b>\n\nဒီ Card ID ကို မတွေ့ပါ။ ID ကို ပြန်စစ်ပေးပါ။", parse_mode=ParseMode.HTML)
        return

    cid = card.get("card_id") or card.get("id")
    name = escape(card.get("name", "Unknown"))
    anime = escape(card.get("anime", "Unknown"))
    rarity = escape(str(card.get("rarity", "Common")))
    img_url = card.get("img_url") or card.get("image")

    global_caught = inventory_col.count_documents({"$or": [{"card_id": cid}, {"id": cid}]})

    pipeline = [
        {"$match": {"$or": [{"card_id": cid}, {"id": cid}]}},
        {"$group": {"_id": "$user_id", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 10}
    ]
    top_catchers_raw = list(inventory_col.aggregate(pipeline))

    top_lines = []
    for item in top_catchers_raw:
        uid = item["_id"]
        cnt = item["count"]
        u_doc = users_col.find_one({"user_id": uid}) or {}
        uname = escape(u_doc.get("first_name", f"User {uid}"))
        top_lines.append(f"⇒ {uname} (<code>{uid}</code>) x{cnt}")

    top_str = "\n".join(top_lines) if top_lines else "မရှိသေးပါ။"

    caption = (
        f"╭━━━━━━━━━━━━━━━━━━╮\n"
        f"       🃏 <b>CARD INSPECTION</b>\n"
        f"╰━━━━━━━━━━━━━━━━━━╯\n\n"
        f"🎬 <b>{anime}</b>\n"
        f"🌸 <b>{cid}: {name}</b>\n"
        f"💠 <b>RARITY:</b> {rarity}\n\n"
        f"💰 <b>ESTIMATED VALUE:</b> 280 ~ 500 Coins\n"
        f"🌍 <b>GLOBAL CATCHES:</b> {global_caught}\n\n"
        f"🏆 <b>TOP 10 COLLECTORS</b>\n"
        f"{top_str}"
    )

    if img_url:
        try:
            await update.message.reply_photo(photo=img_url, caption=caption, parse_mode=ParseMode.HTML)
            return
        except Exception:
            pass

    await update.message.reply_text(caption, parse_mode=ParseMode.HTML)


async def balance_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/balance Command"""
    user_id = update.effective_user.id
    user_doc = users_col.find_one({"user_id": user_id}) or {}
    coins, gems = get_coins_and_gems(user_doc)

    await update.message.reply_text(
        f"╭━━━━━━━━━━━━━━━━━━╮\n"
        f"       💰 <b>MY WALLET</b>\n"
        f"╰━━━━━━━━━━━━━━━━━━╯\n\n"
        f"🪙 <b>Coins</b>  ·  <code>{coins:,}</code>\n"
        f"💎 <b>Gems</b>   ·  <code>{gems:,}</code>\n\n"
        f"✨ <i>Manage your collection wisely!</i>",
        parse_mode=ParseMode.HTML
    )


def get_user_handlers():
    return [
        CommandHandler("profile", profile_command),
        CommandHandler("check", check_command),
        CommandHandler("balance", balance_command)
    ]
