import time
import random
from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes
from config import OWNER_ID, LOG_CHANNEL_ID
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
    # ပုံမပါဘဲ စာသားသီးသန့် ပေါ်စေရန် reply_text သုံးထားသည်
    caption = f"✨ **NEXUS CATCH BOT** ✨\n\n💎 မင်္ဂလာပါ {user.first_name}! ပရီမီယံကဒ်များ စုဆောင်းရန် `/help` ကို နှိပ်ကြည့်ပါ။ 🚀"
    await update.message.reply_text(caption, parse_mode="Markdown", reply_markup=get_start_keyboard())

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = (
        "🌟 **NEXUS CATCH BOT — PREMIUM HELP** 🌟\n\n"
        "• `/harem` - စုထားသော ကဒ်များကြည့်ရန် 🎴\n"
        "• `/profile` - ပရိုဖိုင်၊ ကဒ်များနှင့် Global Top ကြည့်ရန် 👤\n"
        "• `/search` - ကဒ်အားလုံး ရှာဖွေကြည့်ရှုရန် 🔍\n"
        "• `/Nexus <Card_Name>` - ကဒ်ဖမ်းရန် ⚡\n"
        "• `/market` - ဈေးကွက်ကြည့်ရန် 🛒 | `/sell` / `/buy` / `/delist`\n"
        "• `/daily` - 500 Coins တစ်ရက်တစ်ကြိမ်ယူရန် 💰 | `/claim` - ကဒ်တစ်စောင် တစ်ရက်တစ်ကြိမ်ထုတ်ရန် 🎁\n"
        "• `/balance` - လက်ကျန်ငွေကြည့်ရန် 💳 | `/duel` - တိုက်ပွဲဝင်ရန် ⚔️\n"
        "• `/fav` / `/unfav` - အကြိုက်ဆုံးသတ်မှတ်ရန် ❤️ | `/upgrade` - မြှင့်တင်ရန် ⬆️\n"
        "• `/top` / `/ctop` / `/rankings` - အဆင့်သတ်မှတ်ချက်များ 🏆\n"
        "• `/trade` / `/gift` - အချင်းချင်းပေးပို့ရန် 🤝 | `/hmode` - ဖစ်တာစစ်ရန် 🎛️"
    )
    await update.message.reply_text(msg, parse_mode="Markdown", reply_markup=get_help_keyboard())

async def harem_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    # Owner ဖြစ်ပါက Force Join စစ်ဆေးမှုကို ကျော်လွန်ခွင့်ရှိသည်
    if user.id != OWNER_ID and not await check_force_join(user.id, context):
        await update.message.reply_text("⚠️ **[Force Join]** Harem မကြည့်မီ အောက်ပါ Link များကို အရင် ဂျွိုင်း (Join) ပေးပါရန်။ 🔗", reply_markup=get_join_keyboard())
        return

    target_user_id = user.id
    # Owner သီးသန့် အခြား User များ၏ ကဒ်များကို ဝင်ကြည့်နိုင်ခြင်း (/harem <user_id>)
    if context.args and user.id == OWNER_ID:
        try:
            target_user_id = int(context.args[0])
        except ValueError:
            pass

    db.cursor.execute("SELECT tier_filter FROM hmode WHERE user_id = ?", (target_user_id,))
    filter_res = db.cursor.fetchone()

    if filter_res:
        tier = filter_res[0]
        tier_name = TIER_NAMES[tier-1] if 1 <= tier <= len(TIER_NAMES) else f"Tier {tier}"
        db.cursor.execute("""
            SELECT inventory.id, cards.name, cards.rarity_id, inventory.level, inventory.is_fav, cards.image_url 
            FROM inventory JOIN cards ON inventory.card_id = cards.card_id
            WHERE inventory.user_id = ? AND cards.rarity_id = ? ORDER BY inventory.id DESC LIMIT 15
        """, (target_user_id, tier))
        cards = db.cursor.fetchall()
        header = f"🎴 **Harem ({tier_name}) [User ID: {target_user_id}]** 💎\n\n"
    else:
        db.cursor.execute("""
            SELECT inventory.id, cards.name, cards.rarity_id, inventory.level, inventory.is_fav, cards.image_url 
            FROM inventory JOIN cards ON inventory.card_id = cards.card_id
            WHERE inventory.user_id = ? ORDER BY inventory.id DESC LIMIT 15
        """, (target_user_id,))
        cards = db.cursor.fetchall()
        header = f"🎴 **Premium Harem [User ID: {target_user_id}]** 💎\n\n"

    if not cards:
        await update.message.reply_text("❌ ဤအမျိုးအစားအလိုက် ကဒ်များ မရှိသေးပါ။ 📭")
        return

    first_image = cards[0][5] if len(cards[0]) > 5 and cards[0][5] else None
    msg = header
    for c in cards:
        fav = "❤️ " if c[4] else "🔹 "
        tier_str = TIER_NAMES[c[2]-1] if 1 <= c[2] <= len(TIER_NAMES) else f"Tier {c[2]}"
        msg += f"{fav}🆔 `{c[0]}` | **{c[1]}** | ✨ {tier_str} | 🛡️ Lvl {c[3]}\n"

    if first_image:
        try:
            await update.message.reply_photo(photo=first_image, caption=msg, parse_mode="Markdown")
            return
        except Exception:
            pass
    await update.message.reply_text(msg, parse_mode="Markdown")

async def search_cards_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db.cursor.execute("SELECT card_id, name, rarity_id, image_url FROM cards LIMIT 20")
    cards = db.cursor.fetchall()
    if not cards:
        await update.message.reply_text("❌ ဒေတာဘေ့စ်တွင် ကဒ်များ မရှိသေးပါ။ 📭")
        return
    msg = "🔍 **AVAILABLE CARDS DATABASE** 💎\n\n"
    for c in cards:
        tier_str = TIER_NAMES[c[2]-1] if 1 <= c[2] <= len(TIER_NAMES) else f"Tier {c[2]}"
        msg += f"🆔 `{c[0]}` | **{c[1]}** | ✨ {tier_str}\n"
    await update.message.reply_text(msg, parse_mode="Markdown")

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
    await update.message.reply_text(msg, parse_mode="Markdown")

async def nexus_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    # Owner ဖြစ်ပါက Group Guard ကို ကျော်လွန်ခွင့်ရှိသည်
    if user_id != OWNER_ID and not await check_group_guard(update, context): 
        return
    if not context.args:
        await update.message.reply_text("Usage: `/Nexus <Card_Name>`", parse_mode="Markdown")
        return

    name = " ".join(context.args)
    db.cursor.execute("SELECT card_id, name, image_url FROM cards WHERE LOWER(name) = LOWER(?)", (name,))
    card = db.cursor.fetchone()
    if not card:
        await update.message.reply_text("❌ ထိုအမည်ရှိ ကဒ် ဒေတာဘေ့စ်တွင် မရှိပါ။ 🚫")
        return

    db.cursor.execute("INSERT INTO inventory (user_id, card_id, chat_id) VALUES (?, ?, ?)",
                      (user_id, card[0], update.effective_chat.id))
    db.conn.commit()
    
    success_msg = f"🎉 **{update.effective_user.first_name} က `[{card[0]}]` ** ကဒ်ကို အောင်မြင်စွာ ကောက်ယူလိုက်ပါပြီ! ⚡✨"
    if card[2]:
        try:
            await update.message.reply_photo(photo=card[2], caption=success_msg, parse_mode="Markdown")
            return
        except Exception:
            pass
    await update.message.reply_text(success_msg, parse_mode="Markdown")

async def claim_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    today_date = datetime.now().strftime("%Y-%m-%d")
    
    try:
        db.cursor.execute("ALTER TABLE users ADD COLUMN last_claim TEXT;")
        db.conn.commit()
    except Exception:
        pass

    # Owner ဖြစ်ပါက တစ်ရက်တစ်ကြိမ် ကန့်သတ်ချက်ကို ကျော်လွန်၍ အချိန်မရွေး ထုတ်ယူနိုင်သည်
    if user_id != OWNER_ID:
        db.cursor.execute("SELECT last_claim FROM users WHERE user_id = ?", (user_id,))
        res = db.cursor.fetchone()
        last_claim = res[0] if res else None
        
        if last_claim == today_date:
            await update.message.reply_text("⏳ **Claim:** ယနေ့အတွက် ကဒ်ထုတ်ယူပြီးဖြစ်ပါသည်။ မနက်ဖြန်မှ ထပ်မံထုတ်ယူပါ။ 🎁", parse_mode="Markdown")
            return

    db.cursor.execute("SELECT card_id, name, image_url FROM cards ORDER BY RANDOM() LIMIT 1")
    card = db.cursor.fetchone()
    if not card:
        await update.message.reply_text("❌ ဒေတာဘေ့စ်တွင် ကဒ်များ မလုံလောက်သေးပါ။ 📭")
        return
        
    db.cursor.execute("INSERT INTO inventory (user_id, card_id) VALUES (?, ?)", (user_id, card[0]))
    db.cursor.execute("UPDATE users SET last_claim = ? WHERE user_id = ?", (today_date, user_id))
    db.conn.commit()
    
    msg = f"🎁 **Claim Card (တစ်ရက်တစ်ကြိမ်): 💎\n🆔 `[{card[0]}]` - ** အောင်မြင်စွာ ရရှိပါသည်။ ✨"
    if card[2]:
        try:
            await update.message.reply_photo(photo=card[2], caption=msg, parse_mode="Markdown")
            return
        except Exception:
            pass
    await update.message.reply_text(msg, parse_mode="Markdown")

async def daily_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    today_date = datetime.now().strftime("%Y-%m-%d")
    
    db.cursor.execute("SELECT last_daily FROM users WHERE user_id = ?", (user_id,))
    res = db.cursor.fetchone()
    last_daily = res[0] if res else None
    
    # Owner ဖြစ်ပါက Cooldown မလိုဘဲ အချိန်မရွေး ယူနိုင်သည်
    if user_id != OWNER_ID and last_daily == today_date:
        await update.message.reply_text("⏳ **Daily Reward:** ယနေ့အတွက် ဆုလာဘ်ကို ယူပြီးဖြစ်ပါသည်။ မနက်ဖြန်မှ ထပ်မံထုတ်ယူပါ။ 🪙", parse_mode="Markdown")
        return

    db.cursor.execute("UPDATE users SET coins = coins + 500, last_daily = ? WHERE user_id = ?", (today_date, user_id))
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
        db.cursor.execute("UPDATE inventory SET level = level + 1 WHERE id = ?", (inv_id,))
        db.conn.commit()
        await update.message.reply_text("⬆️ Card Level အောင်မြင်စွာ မြင့်တက်သွားပါပြီ! 🛡️✨")
    except Exception:
        await update.message.reply_text("Usage: `/upgrade [inv_id]`", parse_mode="Markdown")

async def fav_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        inv_id = int(context.args[0])
        db.cursor.execute("UPDATE inventory SET is_fav = 1 WHERE id = ?", (inv_id,))
        db.conn.commit()
        await update.message.reply_text("❤️ ကဒ်ကို Favorite အဖြစ် သတ်မှတ်လိုက်ပါပြီ။ ✨")
    except Exception:
        await update.message.reply_text("Usage: `/fav [inv_id]`", parse_mode="Markdown")

async def unfav_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        inv_id = int(context.args[0])
        db.cursor.execute("UPDATE inventory SET is_fav = 0 WHERE id = ?", (inv_id,))
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
    user = update.effective_user
    db.cursor.execute("SELECT tier_filter FROM hmode WHERE user_id = ?", (user.id,))
    res = db.cursor.fetchone()
    current_tier = res[0] if res else None
    tier_info = f" (လက်ရှိ Filter: Tier {current_tier})" if current_tier else " (Filter မရှိသေးပါ)"

    await update.message.reply_text(
        f"🎴 **Select Harem Mode Tier:** 💎{tier_info}\nအောက်ပါတို့မှ လိုချင်သော Tier ကို ရွေးချယ်ပါ။", 
        parse_mode="Markdown", 
        reply_markup=get_hmode_keyboard()
    )

# --- ADMIN & OWNER COMMANDS ---

async def addcard_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_sudo(update.effective_user.id): return
    try:
        cid = context.args[0]
        name = context.args[1]
        rid = int(context.args[2])
        image_url = context.args[3] if len(context.args) > 3 else None
        
        db.cursor.execute("INSERT OR REPLACE INTO cards (card_id, name, rarity_id, image_url) VALUES (?, ?, ?, ?)", (cid, name, rid, image_url))
        db.conn.commit()
        await update.message.reply_text(f"✅ Card **{name}** (`{cid}`) အား ပုံနှင့်တကွ အောင်မြင်စွာ ထည့်ပြီးပါပြီ။ 🛡️✨", parse_mode="Markdown")
    except Exception:
        await update.message.reply_text("Usage: `/addcard <card_id> <name> <rarity> [image_url]`", parse_mode="Markdown")

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

# --- INLINE BUTTON CALLBACK HANDLER ---

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    try:
        await query.answer()
    except Exception:
        pass
    
    data = query.data
    user_id = query.from_user.id

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

    elif data.startswith("hmode_"):
        val = data.split("_")[1]
        if val == "reset":
            db.cursor.execute("DELETE FROM hmode WHERE user_id = ?", (user_id,))
            db.conn.commit()
            try:
                await query.answer("🔄 Harem Filter ကို ရှင်းလင်းလိုက်ပါပြီ။ ✨", show_alert=True)
                await query.edit_message_text("🔄 Harem Filter ကို ရှင်းလင်းလိုက်ပါပြီ။ `/harem` ဖြင့် ပြန်လည်ကြည့်ရှုပါ။", parse_mode="Markdown")
            except Exception:
                pass
        else:
            try:
                tier = int(val)
                tier_name = TIER_NAMES[tier - 1] if 1 <= tier <= len(TIER_NAMES) else f"Tier {tier}"
                
                db.cursor.execute("INSERT OR REPLACE INTO hmode (user_id, tier_filter) VALUES (?, ?)", (user_id, tier))
                db.conn.commit()
                
                db.cursor.execute("""
                    SELECT inventory.id, cards.name, inventory.level, inventory.is_fav 
                    FROM inventory JOIN cards ON inventory.card_id = cards.card_id
                    WHERE inventory.user_id = ? AND cards.rarity_id = ? 
                    ORDER BY inventory.id DESC LIMIT 15
                """, (user_id, tier))
                cards = db.cursor.fetchall()
                
                msg = f"🎴 **Harem Mode: {tier_name}** 💎\n\n"
                if not cards:
                    msg += "❌ ဤ Tier ထဲတွင် သင့်ပိုင်ဆိုင်သော ကဒ်များ မရှိသေးပါ။ 📭"
                else:
                    for c in cards:
                        fav = "❤️ " if c[3] else "🔹 "
                        msg += f"{fav}🆔 `{c[0]}` | **{c[1]}** | 🛡️ Lvl {c[2]}\n"
                
                await query.answer(f"✅ Tier {tier} ({tier_name}) သို့ ပြောင်းလိုက်ပါပြီ။ 💎", show_alert=True)
                await query.edit_message_text(msg, parse_mode="Markdown", reply_markup=get_hmode_keyboard())
            except Exception as e:
                print(f"Error in hmode callback: {e}")
