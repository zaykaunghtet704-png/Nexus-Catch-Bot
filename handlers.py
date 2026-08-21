import time
import random
from telegram import Update, ChatMember
from telegram.ext import ContextTypes
from config import DEFAULT_START_PHOTO, OWNER_ID, LOG_CHANNEL_ID
from database import db
from keyboards import get_start_keyboard, get_join_keyboard, get_help_keyboard, get_hmode_keyboard, TIER_NAMES
from services import check_force_join, check_group_guard, is_sudo

# --- CHAT MEMBER HANDLER ---
async def my_chat_member_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    result = update.my_chat_member
    if result.new_chat_member.status in ["member", "administrator"]:
        chat = result.chat
        user = result.from_user
        try:
            count = await chat.get_member_count()
        except Exception:
            count = "Unknown"
        log_text = f"📥 **BOT ADDED TO GROUP** 🚀\n\n👥 Group: {chat.title}\n🆔 ID: `{chat.id}`\n👤 By: {user.first_name}\n📊 Members: `{count}`"
        try:
            await context.bot.send_message(chat_id=LOG_CHANNEL_ID, text=log_text, parse_mode="Markdown")
        except Exception:
            pass

# --- USER COMMANDS ---

async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    db.cursor.execute("INSERT OR IGNORE INTO users (user_id, username, first_name) VALUES (?, ?, ?)",
                      (user.id, user.username, user.first_name))
    db.conn.commit()
    caption = f"✨ **NEXUS CATCH BOT** ✨\n\n💎 မင်္ဂလာပါ {user.first_name}! ပရီမီယံကဒ်များ စုဆောင်းရန် `/help` ကို နှိပ်ကြည့်ပါ။ 🚀"
    await update.message.reply_photo(photo=DEFAULT_START_PHOTO, caption=caption, parse_mode="Markdown", reply_markup=get_start_keyboard())

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = (
        "🌟 **NEXUS CATCH BOT — PREMIUM HELP** 🌟\n\n"
        "• `/harem` - စုထားသော ကဒ်များကြည့်ရန် 🎴\n"
        "• `/profile` - ပရိုဖိုင်၊ ကဒ်များနှင့် Global Top ကြည့်ရန် 👤\n"
        "• `/search` - ကဒ်အားလုံး ရှာဖွေကြည့်ရှုရန် 🔍\n"
        "• `/Nexus <Card_Name>` - ကဒ်ဖမ်းရန် ⚡\n"
        "• `/market` - ဈေးကွက်ကြည့်ရန် 🛒 | `/sell` / `/buy` / `/delist`\n"
        "• `/daily` - 500 Coins အခမဲ့ယူရန် 💰 | `/claim` - ကဒ်ထုတ်ရန် 🎁\n"
        "• `/balance` - လက်ကျန်ငွေကြည့်ရန် 💳 | `/duel` - တိုက်ပွဲဝင်ရန် ⚔️\n"
        "• `/fav` / `/unfav` - အကြိုက်ဆုံးသတ်မှတ်ရန် ❤️ | `/upgrade` - မြှင့်တင်ရန် ⬆️\n"
        "• `/top` / `/ctop` / `/rankings` - အဆင့်သတ်မှတ်ချက်များ 🏆\n"
        "• `/trade` / `/gift` - အချင်းချင်းပေးပို့ရန် 🤝 | `/hmode` - ဖစ်တာစစ်ရန် 🎛️"
    )
    await update.message.reply_text(msg, parse_mode="Markdown", reply_markup=get_help_keyboard())

async def harem_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not await check_force_join(user.id, context):
        await update.message.reply_text("⚠️ **[Force Join]** Harem မကြည့်မီ အောက်ပါ Link များကို အရင် ဂျွိုင်း (Join) ပေးပါရန်။ 🔗", reply_markup=get_join_keyboard())
        return

    db.cursor.execute("""
        SELECT inventory.id, cards.name, cards.rarity_id, inventory.level, inventory.is_fav 
        FROM inventory JOIN cards ON inventory.card_id = cards.card_id
        WHERE inventory.user_id = ? ORDER BY inventory.id DESC LIMIT 15
    """, (user.id,))
    cards = db.cursor.fetchall()

    if not cards:
        await update.message.reply_text("❌ သင့်ထံတွင် ကဒ်များ မရှိသေးပါ။ `/claim` ဖြင့် ကဒ်ထုတ်ယူပါ။ 📭")
        return

    msg = f"🎴 **{user.first_name}'s Premium Harem** 💎\n\n"
    for c in cards:
        fav = "❤️ " if c[4] else "🔹 "
        tier_str = TIER_NAMES[c[2]-1] if 1 <= c[2] <= len(TIER_NAMES) else f"Tier {c[2]}"
        msg += f"{fav}🆔 `{c[0]}` | **{c[1]}** | ✨ {tier_str} | 🛡️ Lvl {c[3]}\n"
    await update.message.reply_text(msg, parse_mode="Markdown")

async def search_cards_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db.cursor.execute("SELECT card_id, name, rarity_id FROM cards LIMIT 20")
    cards = db.cursor.fetchall()
    if not cards:
        await update.message.reply_text("❌ ဒေတာဘေ့စ်တွင် ကဒ်များ မရှိသေးပါ။ 📭")
        return
    msg = "🔍 **AVAILABLE CARDS DATABASE** 💎\n\n"
    for c in cards:
        tier_str = TIER_NAMES[c[2]-1] if 1 <= c[2] <= len(TIER_NAMES) else f"Tier {c[2]}"
        msg += f"🆔 `{c[0]}` | **{c[1]}** | ✨ {tier_str}\n"
    await update.message.reply_text(msg, parse_mode="Markdown")

async def check_card_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: `/check <card_id>`", parse_mode="Markdown")
        return
    card_id = context.args[0]
    db.cursor.execute("SELECT card_id, name, rarity_id FROM cards WHERE card_id = ?", (card_id,))
    c = db.cursor.fetchone()
    if not c:
        await update.message.reply_text("❌ ကဒ်ကို မတွေ့ပါ။ 🚫")
        return
    tier_str = TIER_NAMES[c[2]-1] if 1 <= c[2] <= len(TIER_NAMES) else f"Tier {c[2]}"
    await update.message.reply_text(f"🎴 **Card Details** 💎\n\n🆔 ID: `{c[0]}`\n📌 Name: **{c[1]}**\n⭐ Rarity: {tier_str}", parse_mode="Markdown")

async def profile_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    db.cursor.execute("SELECT coins FROM users WHERE user_id = ?", (user.id,))
    res = db.cursor.fetchone()
    coins = res[0] if res else 0

    db.cursor.execute("SELECT COUNT(*) FROM inventory WHERE user_id = ?", (user.id,))
    cards_cnt = db.cursor.fetchone()[0]

    db.cursor.execute("""
        SELECT users.first_name, COUNT(inventory.id) as cnt 
        FROM inventory JOIN users ON inventory.user_id = users.user_id 
        GROUP BY inventory.user_id ORDER BY cnt DESC LIMIT 1
    """)
    top_user = db.cursor.fetchone()
    top_name = top_user[0] if top_user else "None"

    msg = (
        f"👤 **USER PREMIUM PROFILE** 💎\n\n"
        f"📛 **Name**: {user.first_name}\n"
        f"🆔 **ID**: `{user.id}`\n"
        f"💰 **Coins**: `{coins:,}` Coins 🪙\n"
        f"🎴 **Cards Collected**: `{cards_cnt:,}` စောင် 📦\n\n"
        f"🏆 **Global Top #1**: {top_name} 👑"
    )
    try:
        photos = await user.get_profile_photos(limit=1)
        if photos.total_count > 0:
            await update.message.reply_photo(photo=photos.photos[0][-1].file_id, caption=msg, parse_mode="Markdown")
            return
    except Exception:
        pass
    await update.message.reply_photo(photo=DEFAULT_START_PHOTO, caption=msg, parse_mode="Markdown")

async def nexus_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_group_guard(update, context): return
    if not context.args:
        await update.message.reply_text("Usage: `/Nexus <Card_Name>`", parse_mode="Markdown")
        return

    name = " ".join(context.args)
    db.cursor.execute("SELECT card_id, name FROM cards WHERE LOWER(name) = LOWER(?)", (name,))
    card = db.cursor.fetchone()
    if not card:
        await update.message.reply_text("❌ ထိုအမည်ရှိ ကဒ် ဒေတာဘေ့စ်တွင် မရှိပါ။ 🚫")
        return

    db.cursor.execute("INSERT INTO inventory (user_id, card_id, chat_id) VALUES (?, ?, ?)",
                      (update.effective_user.id, card[0], update.effective_chat.id))
    db.conn.commit()
    await update.message.reply_text(f"🎉 **{update.effective_user.first_name} က `[{card[0]}]` ** ကဒ်ကို အောင်မြင်စွာ ကောက်ယူလိုက်ပါပြီ! ⚡✨", parse_mode="Markdown")

async def claim_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    db.cursor.execute("SELECT card_id, name FROM cards ORDER BY RANDOM() LIMIT 2")
    cards = db.cursor.fetchall()
    if len(cards) < 2:
        await update.message.reply_text("❌ ဒေတာဘေ့စ်တွင် ကဒ်များ မလုံလောက်သေးပါ။ 📭")
        return
    for c in cards:
        db.cursor.execute("INSERT INTO inventory (user_id, card_id) VALUES (?, ?)", (user_id, c[0]))
    db.conn.commit()
    await update.message.reply_text(f"🎁 **Claim Cards (၂ စောင်ရရှိသည်):** 💎\n1. `{cards[0][0]}` - **{cards[0][1]}**\n2. `{cards[1][0]}` - **{cards[1][1]}**", parse_mode="Markdown")

async def daily_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db.cursor.execute("UPDATE users SET coins = coins + 500 WHERE user_id = ?", (update.effective_user.id,))
    db.conn.commit()
    await update.message.reply_text("💰 **Daily Reward:** +`500` Coins အခမဲ့ ရရှိပါသည်။ 🪙✨", parse_mode="Markdown")

async def balance_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db.cursor.execute("SELECT coins FROM users WHERE user_id = ?", (update.effective_user.id,))
    res = db.cursor.fetchone()
    coins = res[0] if res else 0
    await update.message.reply_text(f"💳 သင့်လက်ကျန်ငွေ: `{coins:,}` Coins 🪙", parse_mode="Markdown")

async def market_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db.cursor.execute("""
        SELECT market.listing_id, cards.name, market.price, users.first_name 
        FROM market JOIN inventory ON market.inv_id = inventory.id 
        JOIN cards ON inventory.card_id = cards.card_id 
        JOIN users ON market.seller_id = users.user_id LIMIT 10
    """)
    listings = db.cursor.fetchall()
    if not listings:
        await update.message.reply_text("🛒 ဈေးကွက်ထဲတွင် ကဒ်များ မရှိသေးပါ။ 📭")
        return
    msg = "🛒 **NEXUS PREMIUM MARKETPLACE** 💎\n\n"
    for l in listings:
        msg += f"🆔 Listing `{l[0]}` | **{l[1]}** — 💰 `{l[2]:,}` Coins (Seller: {l[3]})\n"
    await update.message.reply_text(msg, parse_mode="Markdown")

async def sell_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        inv_id, price = int(context.args[0]), int(context.args[1])
        db.cursor.execute("INSERT INTO market (seller_id, inv_id, price) VALUES (?, ?, ?)", (update.effective_user.id, inv_id, price))
        db.conn.commit()
        await update.message.reply_text("✅ ဈေးကွက်သို့ ကဒ် တင်ပြီးပါပြီ။ 🛒✨")
    except Exception:
        await update.message.reply_text("Usage: `/sell [inv_id] [price]`", parse_mode="Markdown")

async def buy_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        listing_id = int(context.args[0])
        db.cursor.execute("SELECT seller_id, inv_id, price FROM market WHERE listing_id = ?", (listing_id,))
        item = db.cursor.fetchone()
        if not item:
            await update.message.reply_text("❌ မတွေ့ပါ။ 🚫")
            return
        seller_id, inv_id, price = item
        db.cursor.execute("UPDATE inventory SET user_id = ? WHERE id = ?", (update.effective_user.id, inv_id))
        db.cursor.execute("DELETE FROM market WHERE listing_id = ?", (listing_id,))
        db.conn.commit()
        await update.message.reply_text("🎉 ကဒ်ဝယ်ယူမှု အောင်မြင်ပါသည်။ 🛒💎")
    except Exception:
        await update.message.reply_text("Usage: `/buy [listing_id]`", parse_mode="Markdown")

async def delist_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        listing_id = int(context.args[0])
        db.cursor.execute("DELETE FROM market WHERE listing_id = ? AND seller_id = ?", (listing_id, update.effective_user.id))
        db.conn.commit()
        await update.message.reply_text("🗑️ Listing ကို ဈေးကွက်မှ ပြန်ရုပ်သိမ်းလိုက်ပါပြီ။ 🔄")
    except Exception:
        await update.message.reply_text("Usage: `/delist [listing_id]`", parse_mode="Markdown")

async def trade_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        target_uid = int(context.args[0])
        my_inv_id = int(context.args[1])
        their_inv_id = int(context.args[2])
        my_id = update.effective_user.id

        db.cursor.execute("SELECT id FROM inventory WHERE id = ? AND user_id = ?", (my_inv_id, my_id))
        if not db.cursor.fetchone():
            await update.message.reply_text("❌ ပထမပါသော ကဒ်သည် သင့်ပိုင်ဆိုင်မှု မဟုတ်ပါ။ 🚫")
            return

        db.cursor.execute("SELECT id FROM inventory WHERE id = ? AND user_id = ?", (their_inv_id, target_uid))
        if not db.cursor.fetchone():
            await update.message.reply_text("❌ ဒုတိယပါသော ကဒ်သည် သက်ဆိုင်ရာ ယူဆာ၏ ပိုင်ဆိုင်မှု မဟုတ်ပါ။ 🚫")
            return

        db.cursor.execute("UPDATE inventory SET user_id = ? WHERE id = ?", (target_uid, my_inv_id))
        db.cursor.execute("UPDATE inventory SET user_id = ? WHERE id = ?", (my_id, their_inv_id))
        db.conn.commit()
        await update.message.reply_text("🤝 ကဒ်လဲလှယ်မှု (Trade) အောင်မြင်ပါသည်။ ✨")
    except Exception:
        await update.message.reply_text("Usage: `/trade <user_id> <my_inv_id> <their_inv_id>`", parse_mode="Markdown")

async def gift_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        target_uid = int(context.args[0])
        inv_id = int(context.args[1])
        my_id = update.effective_user.id

        db.cursor.execute("SELECT id FROM inventory WHERE id = ? AND user_id = ?", (inv_id, my_id))
        if not db.cursor.fetchone():
            await update.message.reply_text("❌ ဤကဒ်သည် သင့်ထံတွင် မရှိပါ။ 🚫")
            return

        db.cursor.execute("UPDATE inventory SET user_id = ? WHERE id = ?", (target_uid, inv_id))
        db.conn.commit()
        await update.message.reply_text(f"🎁 User `{target_uid}` ထံသို့ ကဒ် လက်ဆောင်ပေးပို့ပြီးပါပြီ။ ✨", parse_mode="Markdown")
    except Exception:
        await update.message.reply_text("Usage: `/gift <user_id> <inv_id>`", parse_mode="Markdown")

async def duel_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    won = random.choice([True, False])
    if won:
        db.cursor.execute("UPDATE users SET coins = coins + 300 WHERE user_id = ?", (update.effective_user.id,))
        db.conn.commit()
        await update.message.reply_text("⚔️ **Duel Victory!** +300 Coins ရရှိပါသည်။ 🏆")
    else:
        await update.message.reply_text("⚔️ **Duel Defeat!** ရှုံးနိမ့်သွားပါသည်။ 💀")

async def upgrade_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        inv_id = int(context.args[0])
        db.cursor.execute("UPDATE inventory SET level = level + 1 WHERE id = ? AND user_id = ?", (inv_id, update.effective_user.id))
        db.conn.commit()
        await update.message.reply_text("⬆️ Card Level အောင်မြင်စွာ မြင့်တက်သွားပါပြီ! 🛡️✨")
    except Exception:
        await update.message.reply_text("Usage: `/upgrade [inv_id]`", parse_mode="Markdown")

async def fav_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        inv_id = int(context.args[0])
        db.cursor.execute("UPDATE inventory SET is_fav = 1 WHERE id = ? AND user_id = ?", (inv_id, update.effective_user.id))
        db.conn.commit()
        await update.message.reply_text("❤️ ကဒ်ကို Favorite အဖြစ် သတ်မှတ်လိုက်ပါပြီ။ ✨")
    except Exception:
        await update.message.reply_text("Usage: `/fav [inv_id]`", parse_mode="Markdown")

async def unfav_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        inv_id = int(context.args[0])
        db.cursor.execute("UPDATE inventory SET is_fav = 0 WHERE id = ? AND user_id = ?", (inv_id, update.effective_user.id))
        db.conn.commit()
        await update.message.reply_text("🤍 Favorite မှ ဖယ်ရှားလိုက်ပါပြီ။ 🔄")
    except Exception:
        await update.message.reply_text("Usage: `/unfav [inv_id]`", parse_mode="Markdown")

async def top_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db.cursor.execute("""
        SELECT users.first_name, COUNT(inventory.id) as cnt 
        FROM inventory JOIN users ON inventory.user_id = users.user_id 
        GROUP BY inventory.user_id ORDER BY cnt DESC LIMIT 15
    """)
    rows = db.cursor.fetchall()
    msg = "🏆 **GLOBAL TOP 15 COLLECTORS** 💎\n\n"
    for idx, r in enumerate(rows, 1):
        msg += f"{idx}. **{r[0]}** — `{r[1]:,}` Cards 🎴\n"
    await update.message.reply_text(msg, parse_mode="Markdown")

async def ranking_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await top_cmd(update, context)

async def sellprice_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db.cursor.execute("""
        SELECT cards.name, market.price, users.first_name 
        FROM market JOIN inventory ON market.inv_id = inventory.id 
        JOIN cards ON inventory.card_id = cards.card_id 
        JOIN users ON market.seller_id = users.user_id LIMIT 10
    """)
    items = db.cursor.fetchall()
    if not items:
        await update.message.reply_text("🛒 ဈေးကွက်အတွင်း သတ်မှတ်ထားသော ဈေးနှုန်းစာရင်း မရှိသေးပါ။ 📭")
        return
    msg = "📊 **MARKET SELL PRICES** 💎\n\n"
    for item in items:
        msg += f"• **{item[0]}** — 💰 `{item[1]:,}` Coins (Seller: {item[2]})\n"
    await update.message.reply_text(msg, parse_mode="Markdown")

async def todaytop_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db.cursor.execute("""
        SELECT users.first_name, COUNT(inventory.id) as cnt 
        FROM inventory JOIN users ON inventory.user_id = users.user_id 
        GROUP BY inventory.user_id ORDER BY cnt DESC LIMIT 10
    """)
    rows = db.cursor.fetchall()
    msg = "⭐ **TODAY'S TOP COLLECTORS** 💎\n\n"
    for idx, r in enumerate(rows, 1):
        msg += f"{idx}. **{r[0]}** — `{r[1]:,}` Cards 🎴\n"
    await update.message.reply_text(msg, parse_mode="Markdown")

async def changetime_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_sudo(update.effective_user.id):
        await update.message.reply_text("⚠️ ဤအမိန့်သည် Admin များအတွက်သာ ဖြစ်ပါသည်။ 🔒")
        return
    try:
        new_time = int(context.args[0])
        db.cursor.execute("INSERT OR REPLACE INTO bot_settings (key, value) VALUES ('catch_cooldown', ?)", (str(new_time),))
        db.conn.commit()
        await update.message.reply_text(f"⏱️ ကဒ်ဖမ်း cooldown အချိန်ကို `{new_time}` စက္ကန့်သို့ ပြောင်းလဲလိုက်ပါပြီ။ ⚡", parse_mode="Markdown")
    except Exception:
        await update.message.reply_text("Usage: `/changetime <seconds>` (Admin Only)", parse_mode="Markdown")

async def ctop_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db.cursor.execute("""
        SELECT users.first_name, COUNT(inventory.id) as cnt 
        FROM inventory JOIN users ON inventory.user_id = users.user_id 
        WHERE inventory.chat_id = ? GROUP BY inventory.user_id ORDER BY cnt DESC LIMIT 10
    """, (update.effective_chat.id,))
    rows = db.cursor.fetchall()
    msg = "🏰 **GROUP TOP COLLECTORS** 💎\n\n"
    for idx, r in enumerate(rows, 1):
        msg += f"{idx}. **{r[0]}** — `{r[1]:,}` Cards 🎴\n"
    await update.message.reply_text(msg, parse_mode="Markdown")

async def hmode_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🎴 **Select Harem Mode Tier:** 💎", parse_mode="Markdown", reply_markup=get_hmode_keyboard())

async def reset_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db.cursor.execute("DELETE FROM hmode WHERE user_id = ?", (update.effective_user.id,))
    db.conn.commit()
    await update.message.reply_text("🔄 Filter များကို ရှင်းလင်းလိုက်ပါပြီ။ ✨")

# --- ADMIN & OWNER COMMANDS ---

async def addcard_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_sudo(update.effective_user.id): return
    try:
        cid, name, rid = context.args[0], context.args[1], int(context.args[2])
        db.cursor.execute("INSERT INTO cards (card_id, name, rarity_id) VALUES (?, ?, ?)", (cid, name, rid))
        db.conn.commit()
        await update.message.reply_text(f"✅ Card **{name}** (`{cid}`) ထည့်ပြီးပါပြီ။ 🛡️✨", parse_mode="Markdown")
    except Exception:
        await update.message.reply_text("Usage: `/addcard <card_id> <name> <rarity_1_to_13>`", parse_mode="Markdown")

async def remove_card_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_sudo(update.effective_user.id): return
    try:
        card_id = context.args[0]
        db.cursor.execute("DELETE FROM cards WHERE card_id = ?", (card_id,))
        db.cursor.execute("DELETE FROM inventory WHERE card_id = ?", (card_id,))
        db.conn.commit()
        await update.message.reply_text(f"🗑️ Card `{card_id}` အား ဖျက်ဆီးလိုက်ပါပြီ။ 🛡️", parse_mode="Markdown")
    except Exception:
        await update.message.reply_text("Usage: `/removecard <card_id>`", parse_mode="Markdown")

async def approve_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID: return
    try:
        cid = int(context.args[0])
        db.cursor.execute("INSERT OR REPLACE INTO approved_groups (chat_id, approved_by) VALUES (?, ?)", (cid, OWNER_ID))
        db.conn.commit()
        await update.message.reply_text(f"✅ Group `{cid}` အား အသုံးပြုခွင့်ပေးလိုက်ပါပြီ။ 👑", parse_mode="Markdown")
    except Exception:
        await update.message.reply_text("Usage: `/approve <chat_id>`", parse_mode="Markdown")

async def givecoins_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_sudo(update.effective_user.id): return
    try:
        uid, amt = int(context.args[0]), int(context.args[1])
        db.cursor.execute("UPDATE users SET coins = coins + ? WHERE user_id = ?", (amt, uid))
        db.conn.commit()
        await update.message.reply_text(f"✅ User `{uid}` ထံ Coins `{amt:,}` ထည့်ပေးလိုက်ပါပြီ။ 🪙✨", parse_mode="Markdown")
    except Exception:
        await update.message.reply_text("Usage: `/gcoin <user_id> <amount>`", parse_mode="Markdown")

async def ban_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_sudo(update.effective_user.id): return
    try:
        uid = int(context.args[0])
        db.cursor.execute("INSERT OR IGNORE INTO blacklist (user_id) VALUES (?)", (uid,))
        db.conn.commit()
        await update.message.reply_text(f"🚫 User `{uid}` အား ဘော့တ်သုံးမရအောင် ပိတ်ပင်လိုက်ပါပြီ။ 🛡️", parse_mode="Markdown")
    except Exception:
        await update.message.reply_text("Usage: `/ban <user_id>`", parse_mode="Markdown")

async def broadcast_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID: return
    msg = " ".join(context.args)
    db.cursor.execute("SELECT user_id FROM users")
    for u in db.cursor.fetchall():
        try:
            await context.bot.send_message(chat_id=u[0], text=f"📢 **ANNOUNCEMENT** 💎\n\n{msg}", parse_mode="Markdown")
        except Exception:
            pass
    await update.message.reply_text("📤 Broadcast ပို့ပြီးပါပြီ။ 🚀")

# --- INLINE BUTTON CALLBACK HANDLER ---

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    try:
        await query.answer()
    except Exception:
        pass
    
    data = query.data

    if data == "help_p1":
        msg = (
            "📖 **NEXUS CATCH BOT - HELP (Page 1)** 💎\n\n"
            "• `/harem` - စုထားသော ကဒ်များကြည့်ရန် 🎴\n"
            "• `/profile` - ပရိုဖိုင်နှင့် Global Top ကြည့်ရန် 👤\n"
            "• `/search` - ကဒ်အားလုံး ရှာဖွေကြည့်ရှုရန် 🔍\n"
            "• `/Nexus <Card_Name>` - ကဒ်ဖမ်းရန် ⚡"
        )
        try:
            await query.edit_message_text(msg, parse_mode="Markdown", reply_markup=get_help_keyboard())
        except Exception:
            pass

    elif data == "help_p2":
        msg = (
            "📖 **NEXUS CATCH BOT - HELP (Page 2)** 💎\n\n"
            "• `/market` - ဈေးကွက်ကြည့်ရန် 🛒\n"
            "• `/daily` - 500 Coins အခမဲ့ယူရန် 💰\n"
            "• `/claim` - ကဒ်ထုတ်ရန် 🎁\n"
            "• `/trade` / `/gift` - ကဒ်ပေးပို့ လဲလှယ်ရန် 🤝\n"
            "• `/hmode` - ဖစ်တာစစ်ရန် 🎛️"
        )
        try:
            await query.edit_message_text(msg, parse_mode="Markdown", reply_markup=get_help_keyboard())
        except Exception:
            pass

    elif data == "help_admin":
        if not is_sudo(query.from_user.id):
            try:
                await query.answer("⚠️ ဤမီနူးသည် Admin များအတွက်သာ ဖြစ်ပါသည်။ 🔒", show_alert=True)
            except Exception:
                pass
            return
        msg = (
            "👑 **ADMIN & OWNER COMMANDS** 💎\n\n"
            "• `/addcard <id> <name> <tier>` - ကဒ်အသစ်ထည့်ရန် 🛡️\n"
            "• `/removecard <id>` - ကဒ်ဖျက်ရန် 🗑️\n"
            "• `/gcoin <user_id> <amount>` - ပိုက်ဆံထည့်ပေးရန် 🪙\n"
            "• `/ban <user_id>` - ပိတ်ပင်ရန် 🚫\n"
            "• `/approve <chat_id>` - ဂရုဖွင့်ပေးရန် ✅\n"
            "• `/broadcast <msg>` - ကြေညာချက်ပို့ရန် 📢"
        )
        try:
            await query.edit_message_text(msg, parse_mode="Markdown", reply_markup=get_help_keyboard())
        except Exception:
            pass

    elif data.startswith("hmode_"):
        val = data.split("_")[1]
        if val == "reset":
            db.cursor.execute("DELETE FROM hmode WHERE user_id = ?", (query.from_user.id,))
            db.conn.commit()
            try:
                await query.answer("🔄 Harem Filter ကို ရှင်းလင်းလိုက်ပါပြီ။ ✨", show_alert=True)
            except Exception:
                pass
        else:
            tier = int(val)
            tier_name = TIER_NAMES[tier - 1] if 1 <= tier <= len(TIER_NAMES) else f"Tier {tier}"
            db.cursor.execute("INSERT OR REPLACE INTO hmode (user_id, tier_filter) VALUES (?, ?)", (query.from_user.id, tier))
            db.conn.commit()
            try:
                await query.answer(f"✅ Tier {tier} ({tier_name}) သို့ ဖစ်တာချိတ်လိုက်ပါပြီ။ 💎", show_alert=True)
            except Exception:
                pass
