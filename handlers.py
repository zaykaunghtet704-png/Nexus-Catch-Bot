import random
from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes
from config import OWNER_ID, LOG_CHANNEL_ID
from database import db
from keyboards import (
    get_start_keyboard, get_help_keyboard, get_hmode_keyboard, 
    get_market_keyboard, get_harem_pagination_keyboard, TIER_NAMES
)
from services import check_group_guard, is_sudo, get_weighted_rarity, add_power_footer

# --- CHAT MEMBER ---
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
    caption = add_power_footer(f"🔮 <b>NEXUS CATCH BOT</b> ✨\n\n💎 မင်္ဂလာပါ {user.first_name}! ပရီမီယံကဒ်များ စုဆောင်းရန် /help ကို နှိပ်ပါ။ 🚀")
    await update.message.reply_text(caption, parse_mode="HTML", reply_markup=get_start_keyboard())

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = add_power_footer(
        "🌟 <b>NEXUS CATCH BOT — HELP MENU</b> 🔮\n\n"
        "• /harem - ကိုယ်ပိုင်ကဒ်များကြည့်ရန် 🎴\n"
        "• /profile - ပရိုဖိုင်နှင့် Global အဆင့်ကြည့်ရန် 👤\n"
        "• /search - ဒေတာဘေ့စ်ရှိ ကဒ်များရှာရန် 🔍\n"
        "• /Nexus &lt;Card_Name&gt; - ကဒ်ဖမ်းရန် ⚡\n"
        "• /market - ဈေးကွက်ကြည့်ရန် 🛒 | /sell / /buy / /delist\n"
        "• /daily & /claim - ဆုလာဘ်နှင့် ကဒ်ထုတ်ရန် 🎁\n"
        "• /trade & /gift - ကဒ်လဲလှယ်/လက်ဆောင်ပေးရန် 🤝\n"
        "• /duel - တိုက်ပွဲဝင်ရန် ⚔️ | /upgrade - အဆင့်မြှင့်ရန် ⬆️\n"
        "• /fav / /unfav - အကြိုက်ဆုံးသတ်မှတ်ရန် ❤️ | /hmode - ဖစ်တာစစ်ရန် 🎛️"
    )
    await update.message.reply_text(msg, parse_mode="HTML", reply_markup=get_help_keyboard())

async def harem_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    target_user_id = user.id
    if context.args and user.id == OWNER_ID:
        try:
            target_user_id = int(context.args[0])
        except ValueError:
            pass

    page = 1
    limit = 10
    offset = (page - 1) * limit

    db.cursor.execute("SELECT COUNT(*) FROM inventory WHERE user_id = ?", (target_user_id,))
    total_cards = db.cursor.fetchone()[0]
    total_pages = max(1, (total_cards + limit - 1) // limit)

    db.cursor.execute("""
        SELECT inventory.id, cards.name, cards.rarity_id, inventory.level, inventory.is_fav, cards.image_url 
        FROM inventory JOIN cards ON inventory.card_id = cards.card_id
        WHERE inventory.user_id = ? ORDER BY inventory.is_fav DESC, inventory.id DESC LIMIT ? OFFSET ?
    """, (target_user_id, limit, offset))
    cards = db.cursor.fetchall()

    if not cards:
        await update.message.reply_text(add_power_footer("❌ စုဆောင်းထားသော ကဒ်များ မရှိသေးပါ။ 📭"), parse_mode="HTML")
        return

    msg = f"🎴 <b>Harem Collection (Page {page}/{total_pages}) [User ID: {target_user_id}]</b> 💎\n\n"
    for c in cards:
        fav = "❤️ " if c[4] else "🔹 "
        tier_str = TIER_NAMES[c[2]-1] if 1 <= c[2] <= len(TIER_NAMES) else f"Tier {c[2]}"
        msg += f"{fav}🆔 <code>InvID:{c[0]}</code> | <b>{c[1]}</b> | ✨ {tier_str} | 🛡️ Lvl {c[3]}\n"

    msg = add_power_footer(msg)
    first_image = cards[0][5] if cards[0][5] else None
    if first_image:
        try:
            await update.message.reply_photo(photo=first_image, caption=msg, parse_mode="HTML", reply_markup=get_harem_pagination_keyboard(page, total_pages))
            return
        except Exception:
            pass
    await update.message.reply_text(msg, parse_mode="HTML", reply_markup=get_harem_pagination_keyboard(page, total_pages))

async def search_cards_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db.cursor.execute("SELECT card_id, name, rarity_id, image_url FROM cards LIMIT 15")
    cards = db.cursor.fetchall()
    if not cards:
        await update.message.reply_text(add_power_footer("❌ ဒေတာဘေ့စ်တွင် ကဒ်များ မရှိသေးပါ။ 📭"), parse_mode="HTML")
        return
    msg = "🔍 <b>DATABASE CARDS LIST</b> 💎\n\n"
    for c in cards:
        tier_str = TIER_NAMES[c[2]-1] if 1 <= c[2] <= len(TIER_NAMES) else f"Tier {c[2]}"
        msg += f"🆔 <code>{c[0]}</code> | <b>{c[1]}</b> | ✨ {tier_str}\n"
    await update.message.reply_text(add_power_footer(msg), parse_mode="HTML", reply_markup=get_start_keyboard())

async def profile_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    db.cursor.execute("SELECT coins FROM users WHERE user_id = ?", (user.id,))
    res = db.cursor.fetchone()
    coins = res[0] if res else 0

    db.cursor.execute("SELECT COUNT(*) FROM inventory WHERE user_id = ?", (user.id,))
    cards_cnt = db.cursor.fetchone()[0]

    db.cursor.execute("SELECT user_id, COUNT(id) as cnt FROM inventory GROUP BY user_id ORDER BY cnt DESC")
    rankings = db.cursor.fetchall()
    my_rank = "Unranked"
    for idx, r in enumerate(rankings, 1):
        if r[0] == user.id:
            my_rank = f"#{idx}"
            break

    msg = add_power_footer(
        f"👤 <b>USER PROFILE & GLOBAL RANK</b> 🔮\n\n"
        f"📛 <b>Name</b>: {user.first_name}\n"
        f"🆔 <b>ID</b>: <code>{user.id}</code>\n"
        f"💰 <b>Coins</b>: <code>{coins:,}</code> Coins 🪙\n"
        f"🎴 <b>Cards Collected</b>: <code>{cards_cnt:,}</code> စောင် 📦\n"
        f"🏆 <b>Global Rank</b>: {my_rank} 👑"
    )
    await update.message.reply_text(msg, parse_mode="HTML")

async def nexus_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != OWNER_ID and not await check_group_guard(update, context): 
        return

    target_rarity = get_weighted_rarity()
    db.cursor.execute("SELECT card_id, name, image_url FROM cards WHERE rarity_id = ? ORDER BY RANDOM() LIMIT 1", (target_rarity,))
    card = db.cursor.fetchone()
    
    if not card:
        db.cursor.execute("SELECT card_id, name, image_url FROM cards ORDER BY RANDOM() LIMIT 1")
        card = db.cursor.fetchone()
        if not card:
            await update.message.reply_text(add_power_footer("❌ ဒေတာဘေ့စ်ထဲတွင် ကဒ်များ မရှိသေးပါ။ 📭"), parse_mode="HTML")
            return

    db.cursor.execute("INSERT INTO inventory (user_id, card_id, chat_id) VALUES (?, ?, ?)",
                      (user_id, card[0], update.effective_chat.id))
    db.conn.commit()
    
    tier_title = TIER_NAMES[target_rarity - 1]
    success_msg = add_power_footer(f"🎉 <b>{update.effective_user.first_name}</b> က [{tier_title}] <b>{card[1]}</b> ကဒ်ကို အောင်မြင်စွာ ဖမ်းယူလိုက်ပါပြီ! ⚡✨")
    if card[2]:
        try:
            await update.message.reply_photo(photo=card[2], caption=success_msg, parse_mode="HTML")
            return
        except Exception:
            pass
    await update.message.reply_text(success_msg, parse_mode="HTML")

async def daily_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    today_date = datetime.now().strftime("%Y-%m-%d")
    db.cursor.execute("SELECT last_daily FROM users WHERE user_id = ?", (user_id,))
    res = db.cursor.fetchone()
    if res and res[0] == today_date:
        await update.message.reply_text(add_power_footer("⏳ ယနေ့အတွက် Daily Coins ယူပြီးပါပြီ။ မနက်ဖြန်မှ ပြန်လာပါ။ 🪙"), parse_mode="HTML")
        return
    db.cursor.execute("UPDATE users SET coins = coins + 500, last_daily = ? WHERE user_id = ?", (today_date, user_id))
    db.conn.commit()
    await update.message.reply_text(add_power_footer("💰 Daily Reward: +<code>500</code> Coins အခမဲ့ ရရှိပါသည်။ 🪙✨"), parse_mode="HTML")

async def claim_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    today_date = datetime.now().strftime("%Y-%m-%d")
    db.cursor.execute("SELECT last_claim FROM users WHERE user_id = ?", (user_id,))
    res = db.cursor.fetchone()
    if res and res[0] == today_date:
        await update.message.reply_text(add_power_footer("⏳ ယနေ့အတွက် ကဒ်ထုတ်ယူပြီးပါပြီ။ 🎁"), parse_mode="HTML")
        return

    target_rarity = get_weighted_rarity()
    db.cursor.execute("SELECT card_id, name, image_url FROM cards WHERE rarity_id = ? ORDER BY RANDOM() LIMIT 1", (target_rarity,))
    card = db.cursor.fetchone()
    if not card:
        db.cursor.execute("SELECT card_id, name, image_url FROM cards ORDER BY RANDOM() LIMIT 1")
        card = db.cursor.fetchone()

    db.cursor.execute("INSERT INTO inventory (user_id, card_id) VALUES (?, ?)", (user_id, card[0]))
    db.cursor.execute("UPDATE users SET last_claim = ? WHERE user_id = ?", (today_date, user_id))
    db.conn.commit()
    
    msg = add_power_footer(f"🎁 <b>Claim Card:</b> <b>{card[1]}</b> ကို အောင်မြင်စွာ ရရှိပါသည်။ ✨")
    if card[2]:
        try:
            await update.message.reply_photo(photo=card[2], caption=msg, parse_mode="HTML")
            return
        except Exception:
            pass
    await update.message.reply_text(msg, parse_mode="HTML")

async def balance_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db.cursor.execute("SELECT coins FROM users WHERE user_id = ?", (update.effective_user.id,))
    res = db.cursor.fetchone()
    coins = res[0] if res else 0
    await update.message.reply_text(add_power_footer(f"💳 သင့်လက်ကျန်ငွေ: <code>{coins:,}</code> Coins 🪙"), parse_mode="HTML")

async def market_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db.cursor.execute("""
        SELECT market.listing_id, cards.name, market.price, users.first_name 
        FROM market JOIN inventory ON market.inv_id = inventory.id 
        JOIN cards ON inventory.card_id = cards.card_id 
        JOIN users ON market.seller_id = users.user_id LIMIT 10
    """)
    listings = db.cursor.fetchall()
    msg = "🛒 <b>NEXUS MARKETPLACE</b> 💎\n\n"
    if not listings:
        msg += "ဈေးကွက်ထဲတွင် ကဒ်များ မရှိသေးပါ။ 📭"
    else:
        for l in listings:
            msg += f"🆔 Listing <code>{l[0]}</code> | <b>{l[1]}</b> — 💰 <code>{l[2]:,}</code> Coins (Seller: {l[3]})\n"
    await update.message.reply_text(add_power_footer(msg), parse_mode="HTML", reply_markup=get_market_keyboard())

async def sell_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        inv_id, price = int(context.args[0]), int(context.args[1])
        db.cursor.execute("INSERT INTO market (seller_id, inv_id, price) VALUES (?, ?, ?)", (update.effective_user.id, inv_id, price))
        db.conn.commit()
        await update.message.reply_text(add_power_footer("✅ ဈေးကွက်သို့ ကဒ် တင်ပြီးပါပြီ။ 🛒✨"), parse_mode="HTML")
    except Exception:
        await update.message.reply_text(add_power_footer("Usage: /sell [card_id/inv_id] [price]"), parse_mode="HTML")

async def buy_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        listing_id = int(context.args[0])
        db.cursor.execute("SELECT seller_id, inv_id, price FROM market WHERE listing_id = ?", (listing_id,))
        item = db.cursor.fetchone()
        if not item:
            await update.message.reply_text(add_power_footer("❌ မတွေ့ပါ။ 🚫"), parse_mode="HTML")
            return
        seller_id, inv_id, price = item
        
        db.cursor.execute("SELECT coins FROM users WHERE user_id = ?", (update.effective_user.id,))
        coins = db.cursor.fetchone()[0]
        if coins < price:
            await update.message.reply_text(add_power_footer("❌ ငွေမလုံလောက်ပါ။ 🪙"), parse_mode="HTML")
            return

        db.cursor.execute("UPDATE users SET coins = coins - ? WHERE user_id = ?", (price, update.effective_user.id))
        db.cursor.execute("UPDATE users SET coins = coins + ? WHERE user_id = ?", (price, seller_id))
        db.cursor.execute("UPDATE inventory SET user_id = ? WHERE id = ?", (update.effective_user.id, inv_id))
        db.cursor.execute("DELETE FROM market WHERE listing_id = ?", (listing_id,))
        db.conn.commit()
        await update.message.reply_text(add_power_footer("🎉 ကဒ်ဝယ်ယူမှု အောင်မြင်ပါသည်။ 🛒💎"), parse_mode="HTML")
    except Exception:
        await update.message.reply_text(add_power_footer("Usage: /buy [listing_id]"), parse_mode="HTML")

async def delist_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        listing_id = int(context.args[0])
        db.cursor.execute("DELETE FROM market WHERE listing_id = ? AND seller_id = ?", (listing_id, update.effective_user.id))
        db.conn.commit()
        await update.message.reply_text(add_power_footer("🗑️ Listing ကို ဈေးကွက်မှ ပြန်ရုပ်သိမ်းလိုက်ပါပြီ။ 🔄"), parse_mode="HTML")
    except Exception:
        await update.message.reply_text(add_power_footer("Usage: /delist [listing_id]"), parse_mode="HTML")

async def trade_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        target_uid = int(context.args[0])
        my_inv_id = int(context.args[1])
        their_inv_id = int(context.args[2])
        my_id = update.effective_user.id

        db.cursor.execute("UPDATE inventory SET user_id = ? WHERE id = ?", (target_uid, my_inv_id))
        db.cursor.execute("UPDATE inventory SET user_id = ? WHERE id = ?", (my_id, their_inv_id))
        db.conn.commit()
        await update.message.reply_text(add_power_footer("🤝 ကဒ်လဲလှယ်မှု (Trade) အောင်မြင်ပါသည်။ ✨"), parse_mode="HTML")
    except Exception:
        await update.message.reply_text(add_power_footer("Usage: /trade &lt;user_id&gt; &lt;my_card_id&gt; &lt;their_card_id&gt;"), parse_mode="HTML")

async def gift_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        target_uid = int(context.args[0])
        inv_ids = [int(i) for i in context.args[1:]]
        my_id = update.effective_user.id

        for inv_id in inv_ids:
            db.cursor.execute("UPDATE inventory SET user_id = ? WHERE id = ? AND user_id = ?", (target_uid, inv_id, my_id))
        db.conn.commit()
        await update.message.reply_text(add_power_footer(f"🎁 User <code>{target_uid}</code> ထံသို့ ကဒ်များ လက်ဆောင် ပို့ပြီးပါပြီ။ ✨"), parse_mode="HTML")
    except Exception:
        await update.message.reply_text(add_power_footer("Usage: /gift &lt;user_id&gt; &lt;card_id_1&gt; &lt;card_id_2&gt; ..."), parse_mode="HTML")

async def duel_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_name = update.effective_user.first_name
    won = random.choice([True, False])
    if won:
        db.cursor.execute("UPDATE users SET coins = coins + 300 WHERE user_id = ?", (update.effective_user.id,))
        db.conn.commit()
        msg = f"⚔️ <b>DUEL BATTLE ARENA</b> ⚔️\n\n👤 {user_name} 🆚 🤖 Nexus Bot\n\n🏆 <b>ရလဒ် - အနိုင်ရရှိပါသည်!</b> (+300 Coins ရရှိသည်) 🎉"
    else:
        msg = f"⚔️ <b>DUEL BATTLE ARENA</b> ⚔️\n\n👤 {user_name} 🆚 🤖 Nexus Bot\n\n💀 <b>ရလဒ် - ရှုံးနိမ့်သွားပါပြီ!</b> ထပ်မံကြိုးစားပါ။ 🛡️"
    await update.message.reply_text(add_power_footer(msg), parse_mode="HTML")

async def upgrade_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        target_id = int(context.args[0])
        burn_ids = [int(i) for i in context.args[1:]]
        
        for bid in burn_ids:
            db.cursor.execute("DELETE FROM inventory WHERE id = ? AND user_id = ?", (bid, update.effective_user.id))
        
        db.cursor.execute("UPDATE inventory SET level = level + 1 WHERE id = ?", (target_id,))
        db.conn.commit()
        await update.message.reply_text(add_power_footer("⬆️ ကဒ်များ ပေါင်းစပ်၍ အဆင့်မြှင့်တင်ခြင်း (Upgrade) အောင်မြင်ပါသည်။ 🛡️✨"), parse_mode="HTML")
    except Exception:
        await update.message.reply_text(add_power_footer("Usage: /upgrade &lt;target_card_id&gt; &lt;burn_card_1&gt; ..."), parse_mode="HTML")

async def fav_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        inv_id = int(context.args[0])
        db.cursor.execute("UPDATE inventory SET is_fav = 1 WHERE id = ?", (inv_id,))
        db.conn.commit()
        await update.message.reply_text(add_power_footer("❤️ ကဒ်ကို Favorite အဖြစ် သတ်မှတ်လိုက်ပါပြီ (Harem တွင် ထိပ်ဆုံးသို့ ရောက်မည်)။ ✨"), parse_mode="HTML")
    except Exception:
        await update.message.reply_text(add_power_footer("Usage: /fav [card_id]"), parse_mode="HTML")

async def unfav_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if context.args and context.args[0].lower() == "all":
            db.cursor.execute("UPDATE inventory SET is_fav = 0 WHERE user_id = ?", (update.effective_user.id,))
            msg = "🤍 Favorite အားလုံးကို ဖယ်ရှားလိုက်ပါပြီ။ 🔄"
        else:
            inv_id = int(context.args[0])
            db.cursor.execute("UPDATE inventory SET is_fav = 0 WHERE id = ?", (inv_id,))
            msg = "🤍 Favorite မှ ဖယ်ရှားလိုက်ပါပြီ။ 🔄"
        db.conn.commit()
        await update.message.reply_text(add_power_footer(msg), parse_mode="HTML")
    except Exception:
        await update.message.reply_text(add_power_footer("Usage: /unfav [card_id] သို့မဟုတ် /unfav all"), parse_mode="HTML")

async def hmode_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = add_power_footer("🎴 <b>Harem Mode Tier Filter:</b> 💎\nအောက်ပါတို့မှ လိုချင်သော Tier ကို ရွေးချယ်ပါ။")
    await update.message.reply_text(msg, parse_mode="HTML", reply_markup=get_hmode_keyboard())

async def check_card_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text(add_power_footer("Usage: /check &lt;card_id&gt;"), parse_mode="HTML")
        return
    card_id = context.args[0]
    db.cursor.execute("SELECT card_id, name, rarity_id, image_url FROM cards WHERE card_id = ?", (card_id,))
    card = db.cursor.fetchone()
    if not card:
        await update.message.reply_text(add_power_footer(f"❌ <code>{card_id}</code> ကဒ်ကို မတွေ့ပါ။"), parse_mode="HTML")
        return
    tier_str = TIER_NAMES[card[2]-1] if 1 <= card[2] <= len(TIER_NAMES) else f"Tier {card[2]}"
    msg = f"🔍 <b>CARD DETAILS</b> 💎\n\n🆔 ID: <code>{card[0]}</code>\n📛 Name: <b>{card[1]}</b>\n✨ Rarity: {tier_str}"
    msg = add_power_footer(msg)
    if card[3]:
        try:
            await update.message.reply_photo(photo=card[3], caption=msg, parse_mode="HTML")
            return
        except Exception:
            pass
    await update.message.reply_text(msg, parse_mode="HTML")

async def top_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db.cursor.execute("""
        SELECT users.first_name, COUNT(inventory.id) as cnt 
        FROM inventory JOIN users ON inventory.user_id = users.user_id 
        GROUP BY inventory.user_id ORDER BY cnt DESC LIMIT 15
    """)
    rows = db.cursor.fetchall()
    msg = "🏆 <b>GLOBAL TOP 15 COLLECTORS</b> 💎\n\n"
    for idx, r in enumerate(rows, 1):
        msg += f"{idx}. <b>{r[0]}</b> — <code>{r[1]:,}</code> Cards 🎴\n"
    await update.message.reply_text(add_power_footer(msg), parse_mode="HTML")

async def ctop_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db.cursor.execute("""
        SELECT users.first_name, COUNT(inventory.id) as cnt 
        FROM inventory JOIN users ON inventory.user_id = users.user_id 
        WHERE inventory.chat_id = ? GROUP BY inventory.user_id ORDER BY cnt DESC LIMIT 10
    """, (update.effective_chat.id,))
    rows = db.cursor.fetchall()
    msg = "🏰 <b>GROUP TOP COLLECTORS</b> 💎\n\n"
    for idx, r in enumerate(rows, 1):
        msg += f"{idx}. <b>{r[0]}</b> — <code>{r[1]:,}</code> Cards 🎴\n"
    await update.message.reply_text(add_power_footer(msg), parse_mode="HTML")

# --- ADMIN & OWNER COMMANDS ---

async def addcard_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_sudo(update.effective_user.id): return
    try:
        cid = context.args[0]
        name = context.args[1]
        rid = int(context.args[2])

        if rid < 1 or rid > 13:
            await update.message.reply_text(add_power_footer("❌ Rarity ID သည် 1 မှ 13 အတွင်းသာ ဖြစ်ရပါမည်။"), parse_mode="HTML")
            return

        image_url = None
        if update.message.reply_to_message and update.message.reply_to_message.photo:
            image_url = update.message.reply_to_message.photo[-1].file_id
        elif len(context.args) > 3:
            image_url = context.args[3]

        db.cursor.execute("INSERT OR REPLACE INTO cards (card_id, name, rarity_id, image_url) VALUES (?, ?, ?, ?)", (cid, name, rid, image_url))
        db.conn.commit()
        tier_title = TIER_NAMES[rid - 1]
        await update.message.reply_text(add_power_footer(f"✅ Card <b>{name}</b> (<code>{cid}</code>) - [{tier_title}] အား ထည့်သွင်းပြီးပါပြီ။ 🛡️✨"), parse_mode="HTML")
    except Exception:
        await update.message.reply_text(add_power_footer("Usage: /addcard &lt;card_id&gt; &lt;name&gt; &lt;rarity_1-13&gt; [image_url]"), parse_mode="HTML")

async def remove_card_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_sudo(update.effective_user.id): return
    try:
        card_id = context.args[0]
        db.cursor.execute("DELETE FROM cards WHERE card_id = ?", (card_id,))
        db.cursor.execute("DELETE FROM inventory WHERE card_id = ?", (card_id,))
        db.conn.commit()
        await update.message.reply_text(add_power_footer(f"🗑️ Card <code>{card_id}</code> အား ဖျက်ဆီးလိုက်ပါပြီ။ 🛡️"), parse_mode="HTML")
    except Exception:
        await update.message.reply_text(add_power_footer("Usage: /removecard &lt;card_id&gt;"), parse_mode="HTML")

async def givecoins_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_sudo(update.effective_user.id): return
    try:
        uid = int(context.args[0])
        amt = int(context.args[1])
        db.cursor.execute("UPDATE users SET coins = coins + ? WHERE user_id = ?", (amt, uid))
        db.conn.commit()
        await update.message.reply_text(add_power_footer(f"✅ User <code>{uid}</code> ထံ Coins <code>{amt:,}</code> ထည့်ပေးလိုက်ပါပြီ။ 🪙✨"), parse_mode="HTML")
    except Exception:
        await update.message.reply_text(add_power_footer("Usage: /gcoin &lt;user_id&gt; &lt;amount&gt;"), parse_mode="HTML")

async def user_cards_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_sudo(update.effective_user.id): return
    try:
        uid = int(context.args[0])
        db.cursor.execute("""
            SELECT inventory.id, cards.name, inventory.level FROM inventory 
            JOIN cards ON inventory.card_id = cards.card_id WHERE inventory.user_id = ? LIMIT 20
        """, (uid,))
        cards = db.cursor.fetchall()
        msg = f"📦 <b>User <code>{uid}</code> ၏ ကဒ်များစာရင်း:</b> 💎\n\n"
        for c in cards:
            msg += f"🆔 <code>InvID:{c[0]}</code> | <b>{c[1]}</b> | Lvl {c[2]}\n"
        await update.message.reply_text(add_power_footer(msg), parse_mode="HTML")
    except Exception:
        await update.message.reply_text(add_power_footer("Usage: /usercards &lt;user_id&gt;"), parse_mode="HTML")

async def broadcast_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_sudo(update.effective_user.id): return
    text_to_send = " ".join(context.args)
    if not text_to_send:
        await update.message.reply_text(add_power_footer("Usage: /broadcast &lt;message&gt;"), parse_mode="HTML")
        return

    db.cursor.execute("SELECT user_id FROM users")
    users = db.cursor.fetchall()
    success = 0
    for u in users:
        try:
            await context.bot.send_message(chat_id=u[0], text=f"📢 <b>ANNOUNCEMENT</b> 📢\n\n{text_to_send}", parse_mode="HTML")
            success += 1
        except Exception:
            pass
    await update.message.reply_text(add_power_footer(f"✅ Broadcast ပေးပို့ပြီးပါပြီ။ (ရောက်ရှိသူ: {success} ဦး)"))

async def changetime_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_sudo(update.effective_user.id): return
    try:
        new_time = context.args[0]
        db.cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('spawn_time', ?)", (new_time,))
        db.conn.commit()
        await update.message.reply_text(add_power_footer(f"⏱️ Bot Spawn/Cooldown အချိန်ကို <code>{new_time}</code> သို့ ပြောင်းလဲလိုက်ပါပြီ။ ⚙️"), parse_mode="HTML")
    except Exception:
        await update.message.reply_text(add_power_footer("Usage: /changetime &lt;time_value&gt;"), parse_mode="HTML")

async def ban_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_sudo(update.effective_user.id): return
    try:
        uid = int(context.args[0])
        db.cursor.execute("INSERT OR IGNORE INTO blacklist (user_id) VALUES (?)", (uid,))
        db.conn.commit()
        await update.message.reply_text(add_power_footer(f"🚫 User <code>{uid}</code> အား ဘော့တ်သုံးမရအောင် ပိတ်ပင်လိုက်ပါပြီ။ 🛡️"), parse_mode="HTML")
    except Exception:
        await update.message.reply_text(add_power_footer("Usage: /ban &lt;user_id&gt;"), parse_mode="HTML")

async def unban_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_sudo(update.effective_user.id): return
    try:
        uid = int(context.args[0])
        db.cursor.execute("DELETE FROM blacklist WHERE user_id = ?", (uid,))
        db.conn.commit()
        await update.message.reply_text(add_power_footer(f"✅ User <code>{uid}</code> အား Ban ပိတ်ပင်မှုမှ ပြန်လည်လွတ်မြောက်စေလိုက်ပါပြီ။ 🛡️✨"), parse_mode="HTML")
    except Exception:
        await update.message.reply_text(add_power_footer("Usage: /unban &lt;user_id&gt;"), parse_mode="HTML")

# --- CALLBACKS ---

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    try:
        await query.answer()
    except Exception:
        pass
    
    data = query.data
    user_id = query.from_user.id

    if data == "help_p1":
        msg = "📖 <b>HELP (Page 1)</b>\n• /harem - ကဒ်ကြည့်ရန်\n• /profile - ပရိုဖိုင်\n• /search - ရှာဖွေရန်"
        try: await query.edit_message_text(msg, parse_mode="HTML", reply_markup=get_help_keyboard())
        except Exception: pass
    elif data == "help_p2":
        msg = "📖 <b>HELP (Page 2)</b>\n• /market - ဈေးကွက်\n• /daily / /claim - ဆုလာဘ်\n• /trade / /gift - လဲလှယ်ရန်"
        try: await query.edit_message_text(msg, parse_mode="HTML", reply_markup=get_help_keyboard())
        except Exception: pass
    elif data == "help_home":
        try: await query.edit_message_text("🔮 <b>NEXUS CATCH BOT</b> ✨", parse_mode="HTML", reply_markup=get_start_keyboard())
        except Exception: pass
    elif data.startswith("hmode_"):
        val = data.split("_")[1]
        if val == "reset":
            db.cursor.execute("DELETE FROM hmode WHERE user_id = ?", (user_id,))
            db.conn.commit()
            await query.answer("🔄 Filter ရှင်းလင်းပြီးပါပြီ။", show_alert=True)
        else:
            tier = int(val)
            db.cursor.execute("INSERT OR REPLACE INTO hmode (user_id, tier_filter) VALUES (?, ?)", (user_id, tier))
            db.conn.commit()
            await query.answer(f"✅ Tier {tier} သို့ ပြောင်းလိုက်ပါပြီ။", show_alert=True)
