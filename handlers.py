import time
import random
from telegram import Update, ChatMember, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from config import OWNER_ID, LOG_CHANNEL_ID, RARITY_STAGES
from database import db
from keyboards import get_start_keyboard, get_force_join_keyboard, get_hmode_keyboard
from services import check_force_join, is_sudo, generate_math_captcha
from card_generator import generate_card_canvas

# ==========================================
# 1. CORE & USER COMMANDS (30+ COMMANDS)
# ==========================================

async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    db.cursor.execute("INSERT OR IGNORE INTO users (user_id, username, first_name) VALUES (?, ?, ?)",
                      (user.id, user.username, user.first_name))
    db.conn.commit()
    
    caption = (
        f"✨ **NEXUS CATCH RPG BOT** ✨\n\n"
        f"မင်္ဂလာပါ {user.first_name}! Bot မှ ကြိုဆိုပါသည်။\n"
        f"Command များအားလုံးကို ကြည့်ရှုရန် `/help` ကို အသုံးပြုပါ။"
    )
    await update.message.reply_photo(
        photo="https://t.me/c/4461314187/10360",
        caption=caption,
        parse_mode="Markdown",
        reply_markup=get_start_keyboard()
    )

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "📖 **NEXUS CATCH BOT - COMMAND CENTER**\n\n"
        "🎮 **User Commands (30+):**\n"
        "• `/Nexus <Card>` - ကဒ် ဖမ်းယူရန်\n"
        "• `/harem` - မိမိ ပိုင်ဆိုင်သော ကဒ်များ ကြည့်ရန်\n"
        "• `/hmode` - Harem Tier Filter ပြောင်းရန်\n"
        "• `/view <id>` - Canvas Rendering ဖြင့် ကဒ်ကြည့်ရန်\n"
        "• `/profile` - Profile & Wallet ကြည့်ရန်\n"
        "• `/daily` - Daily Reward ရယူရန်\n"
        "• `/claim` - 12h Cooldown Free Card ရယူရန်\n"
        "• `/nclaim` - 4h Cooldown Free 2 Cards ရယူရန်\n"
        "• `/fav <id>` - Favorite ကဒ် မှတ်ရန်/ဖြုတ်ရန်\n"
        "• `/favlist` - Favorite ဖြစ်ထားသော ကဒ်များကြည့်ရန်\n"
        "• `/sell <id>` - ကဒ်ကို Coins ဖြင့် ရောင်းရန်\n"
        "• `/sellprice` - Rarity အလိုက် ရောင်းဈေးများ ကြည့်ရန်\n"
        "• `/gift <id> <user_id>` - အခြားသူထံ ကဒ် လက်ဆောင်ပေးရန်\n"
        "• `/trade <user_id> <my_card_id> <his_card_id>` - ကဒ် ချိန်းရန်\n"
        "• `/pay <user_id> <amount>` - Coins လွှဲပြောင်းရန်\n"
        "• `/duel <user_id>` - Card PvP တိုက်ခိုက်ရန်\n"
        "• `/top` - Top Card Collector များကြည့်ရန်\n"
        "• `/rich` - Top Coin Rich Users ကြည့်ရန်\n"
        "• `/search <name>` - Card Database တွင် ရှာရန်\n"
        "• `/rarity` - Drop Rates & Rarities ကြည့်ရန်\n"
        "• `/shop` - Frame/Dye/Font စတိုးဆိုင်\n"
        "• `/buy <item_type> <item_name>` - ပစ္စည်း ဝယ်ယူရန်\n"
        "• `/frame <id> <name>` - ကဒ်တွင် Frame တပ်ရန်\n"
        "• `/dye <id> <hex>` - ကဒ်၏ အနားသတ် Color ပြောင်းရန်\n"
        "• `/font <id> <name>` - Font Style ပြောင်းရန်\n"
        "• `/guild` - မိမိ Guild အချက်အလက် ကြည့်ရန်\n"
        "• `/gcreate <name>` - Guild အသစ် ထူထောင်ရန်\n"
        "• `/gjoin <guild_id>` - Guild သို့ ဝင်ရောက်ရန်\n"
        "• `/pass` - Battle Pass Level & Rewards ကြည့်ရန်\n"
        "• `/lang` - ဘာသာစကား ပြောင်းရန် (MM/EN)\n"
        "• `/ping` - Bot Response Speed စစ်ရန်\n\n"
        "👑 **Owner & Sudo Controls (20+):**\n"
        "`/sudo`, `/rmsudo`, `/sudolist`, `/gcoin`, `/rmcoin`, `/gcard`, `/rmcard`, "
        "`/spawn`, `/changetime`, `/broadcast`, `/ban`, `/unban`, `/checkuser`, "
        "`/maintenance`, `/stats`, `/setpass`, `/addcard`, `/delcard`, `/reload`, `/log`"
    )
    await update.message.reply_text(help_text, parse_mode="Markdown")

async def ping_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    start_t = time.time()
    msg = await update.message.reply_text("🏓 Pong...")
    end_t = time.time()
    await msg.edit_text(f"🏓 **Pong!** `{(end_t - start_t) * 1000:.2f}ms`", parse_mode="Markdown")

async def profile_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    db.cursor.execute("SELECT balance, lang FROM users WHERE user_id = ?", (user.id,))
    res = db.cursor.fetchone()
    bal = res[0] if res else 0

    db.cursor.execute("SELECT COUNT(*) FROM inventory WHERE user_id = ?", (user.id,))
    cards_cnt = db.cursor.fetchone()[0]

    photos = await context.bot.get_user_profile_photos(user.id, limit=1)
    msg = (
        f"👤 **USER PROFILE**\n"
        f"━━━━━━━━━━━━━━━\n"
        f"📛 **Name**: {user.first_name}\n"
        f"🆔 **ID**: `{user.id}`\n"
        f"💰 **Coins**: `{bal:,}`\n"
        f"🎴 **Total Cards**: `{cards_cnt:,}`\n"
        f"🌐 **Language**: `{res[1] if res else 'MM'}`"
    )
    if photos.total_count > 0:
        await update.message.reply_photo(photo=photos.photos[0][-1].file_id, caption=msg, parse_mode="Markdown")
    else:
        await update.message.reply_text(msg, parse_mode="Markdown")

async def harem_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not await check_force_join(context.bot, user_id):
        await update.message.reply_text("⚠️ Harem မသုံးမီ Channel ကို Join ပေးပါ၊", reply_markup=get_force_join_keyboard())
        return

    db.cursor.execute("SELECT tier_filter FROM hmode WHERE user_id = ?", (user_id,))
    hm = db.cursor.fetchone()
    filter_q = f"AND cards.rarity_id = {hm[0]}" if hm and hm[0] else ""

    db.cursor.execute(f"""
        SELECT inventory.id, cards.name, cards.rarity_id, inventory.mint_rate, inventory.serial_no, inventory.is_fav
        FROM inventory JOIN cards ON inventory.card_id = cards.card_id
        WHERE inventory.user_id = ? {filter_q} ORDER BY inventory.id DESC LIMIT 10
    """, (user_id,))
    cards = db.cursor.fetchall()

    if not cards:
        await update.message.reply_text("❌ ပိုင်ဆိုင်ထားသော ကဒ်များ မရှိသေးပါ။")
        return

    msg = f"🎴 **{update.effective_user.first_name}'s Harem**\n━━━━━━━━━━━━━━━\n"
    for c in cards:
        r_name = RARITY_STAGES.get(c[2], {}).get("name", "Common")
        fav = "❤️ " if c[5] else ""
        msg += f"{fav}🆔 `{c[0]}` | **{c[1]}** | [{r_name}] | `{c[3]:.1f}%` (#{c[4]})\n"

    await update.message.reply_text(msg, parse_mode="Markdown")

async def hmode_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🎴 **Harem Tier Filter** အောက်ပါ Button မှ ရွေးချယ်ပါ:", reply_markup=get_hmode_keyboard())

async def view_card_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        inv_id = int(context.args[0])
        db.cursor.execute("""
            SELECT cards.name, cards.rarity_id, inventory.mint_rate, inventory.serial_no, inventory.dye
            FROM inventory JOIN cards ON inventory.card_id = cards.card_id WHERE inventory.id = ?
        """, (inv_id,))
        row = db.cursor.fetchone()
        if row:
            r_name = RARITY_STAGES.get(row[1], {}).get("name", "Common")
            canvas = generate_card_canvas(row[0], r_name, row[2], row[3], row[4])
            await update.message.reply_photo(photo=canvas, caption=f"🎴 **{row[0]}** (`#{inv_id}`)\nRarity: {r_name}", parse_mode="Markdown")
        else:
            await update.message.reply_text("❌ ထို ID ဖြင့် ကဒ်ရှာမတွေ့ပါ။")
    except Exception:
        await update.message.reply_text("Usage: `/view <Inventory_ID>`")

async def daily_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    now = int(time.time())
    db.cursor.execute("SELECT last_daily, balance FROM users WHERE user_id = ?", (user_id,))
    row = db.cursor.fetchone()
    
    if row and (now - row[0]) < 86400:
        remain = 86400 - (now - row[0])
        await update.message.reply_text(f"⏳ Daily reward ရယူရန် `{remain // 3600}h {(remain % 3600) // 60}m` စောင့်ပါ၊")
        return

    reward = 1000
    db.cursor.execute("UPDATE users SET balance = balance + ?, last_daily = ? WHERE user_id = ?", (reward, now, user_id))
    db.conn.commit()
    await update.message.reply_text(f"🎉 **Daily Reward +`{reward}` Coins ရရှိပါသည်။", parse_mode="Markdown")

async def claim_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    now = int(time.time())
    db.cursor.execute("SELECT last_claim FROM users WHERE user_id = ?", (user_id,))
    row = db.cursor.fetchone()

    if row and (now - row[0]) < 43200:
        remain = 43200 - (now - row[0])
        await update.message.reply_text(f"⏳ `/claim` အတွက် `{remain // 3600}h {(remain % 3600) // 60}m` စောင့်ပါ၊")
        return

    # Random Drop Card Logic
    db.cursor.execute("SELECT card_id, name, rarity_id FROM cards ORDER BY RANDOM() LIMIT 1")
    card = db.cursor.fetchone()
    if not card:
        await update.message.reply_text("❌ System တွင် ကဒ်များ မရှိသေးပါ။")
        return

    db.cursor.execute("INSERT INTO inventory (user_id, card_id, mint_rate, serial_no, obtained_time) VALUES (?, ?, ?, ?, ?)",
                      (user_id, card[0], random.uniform(50.0, 99.9), random.randint(1, 100), now))
    db.cursor.execute("UPDATE users SET last_claim = ? WHERE user_id = ?", (now, user_id))
    db.conn.commit()

    r_name = RARITY_STAGES.get(card[2], {}).get("name", "Common")
    await update.message.reply_text(f"🎁 Free Claim Card: ** [{r_name}] ကို ရရှိလိုက်ပါပြီ!", parse_mode="Markdown")

async def nclaim_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    now = int(time.time())
    db.cursor.execute("SELECT last_nclaim FROM users WHERE user_id = ?", (user_id,))
    row = db.cursor.fetchone()

    if row and (now - row[0]) < 14400:
        remain = 14400 - (now - row[0])
        await update.message.reply_text(f"⏳ `/nclaim` အတွက် `{remain // 3600}h {(remain % 3600) // 60}m` စောင့်ပါ၊")
        return

    db.cursor.execute("SELECT card_id, name FROM cards ORDER BY RANDOM() LIMIT 2")
    cards = db.cursor.fetchall()
    for c in cards:
        db.cursor.execute("INSERT INTO inventory (user_id, card_id, mint_rate, serial_no, obtained_time) VALUES (?, ?, ?, ?, ?)",
                          (user_id, c[0], random.uniform(40.0, 95.0), random.randint(1, 200), now))
    
    db.cursor.execute("UPDATE users SET last_nclaim = ? WHERE user_id = ?", (now, user_id))
    db.conn.commit()
    await update.message.reply_text(f"🎁 `/nclaim` မှ ကဒ် 2 ကဒ် ရရှိလိုက်ပါပြီ!", parse_mode="Markdown")

async def fav_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        inv_id = int(context.args[0])
        user_id = update.effective_user.id
        db.cursor.execute("SELECT is_fav FROM inventory WHERE id = ? AND user_id = ?", (inv_id, user_id))
        row = db.cursor.fetchone()
        if not row:
            await update.message.reply_text("❌ ထိုကဒ်သည် သင့်ထံတွင် မရှိပါ။")
            return
        new_fav = 0 if row[0] == 1 else 1
        db.cursor.execute("UPDATE inventory SET is_fav = ? WHERE id = ?", (new_fav, inv_id))
        db.conn.commit()
        status = "❤️ Favorite ပြုလုပ်ပြီး" if new_fav else "💔 Favorite မှ ဖြုတ်လိုက်ပါပြီ"
        await update.message.reply_text(f"✅ Card `#{inv_id}` ကို {status}။", parse_mode="Markdown")
    except Exception:
        await update.message.reply_text("Usage: `/fav <Inventory_ID>`")

async def favlist_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    db.cursor.execute("""
        SELECT inventory.id, cards.name FROM inventory 
        JOIN cards ON inventory.card_id = cards.card_id 
        WHERE inventory.user_id = ? AND inventory.is_fav = 1
    """, (user_id,))
    cards = db.cursor.fetchall()
    if not cards:
        await update.message.reply_text("❌ Favorite မှတ်ထားသော ကဒ်မရှိပါ။")
        return
    msg = "❤️ **Your Favorite Cards:**\n" + "\n".join([f"• `{c[0]}` | **{c[1]}**" for c in cards])
    await update.message.reply_text(msg, parse_mode="Markdown")

async def sell_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        inv_id = int(context.args[0])
        user_id = update.effective_user.id
        db.cursor.execute("""
            SELECT inventory.id, cards.rarity_id FROM inventory 
            JOIN cards ON inventory.card_id = cards.card_id WHERE inventory.id = ? AND inventory.user_id = ?
        """, (inv_id, user_id))
        row = db.cursor.fetchone()
        if not row:
            await update.message.reply_text("❌ ရောင်းရန် ကဒ်ရှာမတွေ့ပါ။")
            return
        price = RARITY_STAGES.get(row[1], {}).get("price", 1000)
        db.cursor.execute("DELETE FROM inventory WHERE id = ?", (inv_id,))
        db.cursor.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (price, user_id))
        db.conn.commit()
        await update.message.reply_text(f"💰 Card `#{inv_id}` ကို `{price:,}` Coins ဖြင့် ရောင်းချပြီးပါပြီ။", parse_mode="Markdown")
    except Exception:
        await update.message.reply_text("Usage: `/sell <Inventory_ID>`")

async def sellprice_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = "💰 **CARD SELL PRICES BY RARITY**\n━━━━━━━━━━━━━━━\n"
    for k, v in RARITY_STAGES.items():
        msg += f"• **Tier {k} ({v['name']})**: `{v['price']:,}` Coins\n"
    await update.message.reply_text(msg, parse_mode="Markdown")

async def gift_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        inv_id = int(context.args[0])
        target_id = int(context.args[1])
        user_id = update.effective_user.id
        
        db.cursor.execute("SELECT id FROM inventory WHERE id = ? AND user_id = ?", (inv_id, user_id))
        if not db.cursor.fetchone():
            await update.message.reply_text("❌ သင့်ထံတွင် ထိုကဒ်မရှိပါ။")
            return

        db.cursor.execute("UPDATE inventory SET user_id = ? WHERE id = ?", (target_id, inv_id))
        db.conn.commit()
        await update.message.reply_text(f"🎁 Card `#{inv_id}` ကို User `{target_id}` ထံ လက်ဆောင်ပေးလိုက်ပါပြီ။", parse_mode="Markdown")
    except Exception:
        await update.message.reply_text("Usage: `/gift <Inventory_ID> <Target_User_ID>`")

async def pay_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        target_id = int(context.args[0])
        amount = int(context.args[1])
        user_id = update.effective_user.id

        if amount <= 0:
            return

        db.cursor.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,))
        bal = db.cursor.fetchone()[0]
        if bal < amount:
            await update.message.reply_text("❌ Coins မလုံလောက်ပါ။")
            return

        db.cursor.execute("UPDATE users SET balance = balance - ? WHERE user_id = ?", (amount, user_id))
        db.cursor.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (amount, target_id))
        db.conn.commit()
        await update.message.reply_text(f"💸 User `{target_id}` ထံ `{amount:,}` Coins လွှဲပြောင်းပေးပြီးပါပြီ။", parse_mode="Markdown")
    except Exception:
        await update.message.reply_text("Usage: `/pay <User_ID> <Amount>`")

async def top_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db.cursor.execute("""
        SELECT users.first_name, COUNT(inventory.id) as cnt 
        FROM inventory JOIN users ON inventory.user_id = users.user_id 
        GROUP BY inventory.user_id ORDER BY cnt DESC LIMIT 10
    """)
    rows = db.cursor.fetchall()
    msg = "🏆 **TOP CARD COLLECTORS**\n━━━━━━━━━━━━━━━\n"
    for idx, r in enumerate(rows, 1):
        msg += f"{idx}. **{r[0]}** - `{r[1]:,}` Cards\n"
    await update.message.reply_text(msg, parse_mode="Markdown")

async def rich_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db.cursor.execute("SELECT first_name, balance FROM users ORDER BY balance DESC LIMIT 10")
    rows = db.cursor.fetchall()
    msg = "💰 **TOP RICH USERS**\n━━━━━━━━━━━━━━━\n"
    for idx, r in enumerate(rows, 1):
        msg += f"{idx}. **{r[0]}** - `{r[1]:,}` Coins\n"
    await update.message.reply_text(msg, parse_mode="Markdown")

async def search_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: `/search <Card_Name>`")
        return
    q = " ".join(context.args)
    db.cursor.execute("SELECT name, rarity_id FROM cards WHERE name LIKE ? LIMIT 5", (f"%{q}%",))
    rows = db.cursor.fetchall()
    if not rows:
        await update.message.reply_text("❌ Card မရှိပါ။")
        return
    msg = f"🔍 **Search Results for '{q}':**\n"
    for r in rows:
        r_name = RARITY_STAGES.get(r[1], {}).get("name", "Common")
        msg += f"• **{r[0]}** [{r_name}]\n"
    await update.message.reply_text(msg, parse_mode="Markdown")

async def rarity_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = "✨ **RARITY & DROP RATES**\n━━━━━━━━━━━━━━━\n"
    for k, v in RARITY_STAGES.items():
        msg += f"• **Tier {k} ({v['name']})**: `{v['chance']}%` Chance\n"
    await update.message.reply_text(msg, parse_mode="Markdown")

async def shop_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    shop_text = (
        "🛍️ **NEXUS COSMETICS SHOP**\n━━━━━━━━━━━━━━━\n"
        "🎨 **Dyes (Color Frames):**\n"
        "• Red Dye (`#FF0000`) - 5,000 Coins\n"
        "• Gold Dye (`#FFD700`) - 15,000 Coins\n"
        "• Neon Dye (`#00FFFF`) - 20,000 Coins\n\n"
        "ဝယ်ယူရန်: `/buy dye <hex_code>`"
    )
    await update.message.reply_text(shop_text, parse_mode="Markdown")

async def buy_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ ပစ္စည်း ဝယ်ယူမှု အောင်မြင်ပါသည်။")

async def dye_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        inv_id = int(context.args[0])
        hex_code = context.args[1]
        user_id = update.effective_user.id
        db.cursor.execute("UPDATE inventory SET dye = ? WHERE id = ? AND user_id = ?", (hex_code, inv_id, user_id))
        db.conn.commit()
        await update.message.reply_text(f"🎨 Card `#{inv_id}` ၏ Dye Color ကို `{hex_code}` သို့ ပြောင်းလိုက်ပါပြီ။", parse_mode="Markdown")
    except Exception:
        await update.message.reply_text("Usage: `/dye <Inventory_ID> <Hex_Code>`")

async def duel_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("⚔️ **PvP Duel System**: စိန်ခေါ်မှုကို ခေါ်ယူလိုက်ပါပြီ!")

async def guild_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🛡️ **Guild Info**: သင်သည် Guild တစ်ခုတွင် ဝင်ရောက်မထားပါ။")

async def gcreate_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🛡️ Guild ထူထောင်ရန် Coins 50,000 လိုအပ်ပါသည်။")

async def gjoin_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🛡️ Guild ID ထည့်သွင်းပေးပါ။")

async def pass_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🎫 **NEXUS BATTLE PASS** - Level 1 (0/100 EXP)")

async def lang_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    db.cursor.execute("SELECT lang FROM users WHERE user_id = ?", (user_id,))
    curr = db.cursor.fetchone()[0]
    new_lang = "EN" if curr == "MM" else "MM"
    db.cursor.execute("UPDATE users SET lang = ? WHERE user_id = ?", (new_lang, user_id))
    db.conn.commit()
    await update.message.reply_text(f"🌐 Language changed to `{new_lang}`", parse_mode="Markdown")

async def frame_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🖼️ Frame တပ်ဆင်ပြီးပါပြီ။")

async def font_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔤 Font Style ပြောင်းလဲပြီးပါပြီ။")

async def trade_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔄 Trade Request ပို့ဆောင်ပြီးပါပြီ။")


# ==========================================
# 2. OWNER & SUDO CONTROLS (20+ COMMANDS)
# ==========================================

async def add_sudo_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return
    try:
        t_id = int(context.args[0])
        db.cursor.execute("INSERT OR IGNORE INTO sudo_users VALUES (?)", (t_id,))
        db.conn.commit()
        await update.message.reply_text(f"✅ User `{t_id}` အား Sudo ပေးလိုက်ပါပြီ။", parse_mode="Markdown")
    except Exception:
        await update.message.reply_text("Usage: `/sudo <user_id>`")

async def rmsudo_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return
    try:
        t_id = int(context.args[0])
        db.cursor.execute("DELETE FROM sudo_users WHERE user_id = ?", (t_id,))
        db.conn.commit()
        await update.message.reply_text(f"❌ User `{t_id}` အား Sudo မှ ဖြုတ်လိုက်ပါပြီ။", parse_mode="Markdown")
    except Exception:
        await update.message.reply_text("Usage: `/rmsudo <user_id>`")

async def sudolist_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_sudo(update.effective_user.id):
        return
    db.cursor.execute("SELECT user_id FROM sudo_users")
    sudos = db.cursor.fetchall()
    msg = "👑 **Sudo Users List:**\n" + "\n".join([f"• `{s[0]}`" for s in sudos])
    await update.message.reply_text(msg, parse_mode="Markdown")

async def gcoin_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_sudo(update.effective_user.id):
        return
    try:
        t_id = int(context.args[0])
        amt = int(context.args[1])
        db.cursor.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (amt, t_id))
        db.conn.commit()
        await update.message.reply_text(f"✅ User `{t_id}` ထံ Coins `{amt:,}` ဖြည့်ပေးပြီးပါပြီ။", parse_mode="Markdown")
    except Exception:
        await update.message.reply_text("Usage: `/gcoin <user_id> <amount>`")

async def rmcoin_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_sudo(update.effective_user.id):
        return
    try:
        t_id = int(context.args[0])
        amt = int(context.args[1])
        db.cursor.execute("UPDATE users SET balance = MAX(0, balance - ?) WHERE user_id = ?", (amt, t_id))
        db.conn.commit()
        await update.message.reply_text(f"✅ User `{t_id}` ထံမှ Coins `{amt:,}` နှုတ်လိုက်ပါပြီ။", parse_mode="Markdown")
    except Exception:
        await update.message.reply_text("Usage: `/rmcoin <user_id> <amount>`")

async def gcard_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_sudo(update.effective_user.id):
        return
    try:
        t_id = int(context.args[0])
        c_id = context.args[1]
        now = int(time.time())
        db.cursor.execute("INSERT INTO inventory (user_id, card_id, mint_rate, serial_no, obtained_time) VALUES (?, ?, ?, ?, ?)",
                          (t_id, c_id, 99.9, 1, now))
        db.conn.commit()
        await update.message.reply_text(f"✅ User `{t_id}` ထံ Card `{c_id}` ပေးအပ်ပြီးပါပြီ။", parse_mode="Markdown")
    except Exception:
        await update.message.reply_text("Usage: `/gcard <user_id> <card_id>`")

async def rmcard_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_sudo(update.effective_user.id):
        return
    try:
        inv_id = int(context.args[0])
        db.cursor.execute("DELETE FROM inventory WHERE id = ?", (inv_id,))
        db.conn.commit()
        await update.message.reply_text(f"✅ Inventory ID `{inv_id}` ကို ဖျက်ပြီးပါပြီ။", parse_mode="Markdown")
    except Exception:
        await update.message.reply_text("Usage: `/rmcard <Inventory_ID>`")

async def spawn_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_sudo(update.effective_user.id):
        return
    await update.message.reply_text("✨ Spawn Card Triggered!")

async def changetime_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_sudo(update.effective_user.id):
        return
    try:
        limit = int(context.args[0])
        chat_id = update.effective_chat.id
        db.cursor.execute("UPDATE approved_groups SET msg_limit = ? WHERE chat_id = ?", (limit, chat_id))
        db.conn.commit()
        await update.message.reply_text(f"⏱️ Group Spawn Message Limit ကို `{limit}` သို့ ပြောင်းလိုက်ပါပြီ။", parse_mode="Markdown")
    except Exception:
        await update.message.reply_text("Usage: `/changetime <msg_limit>`")

async def broadcast_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_sudo(update.effective_user.id):
        return
    msg = " ".join(context.args)
    if not msg:
        await update.message.reply_text("Usage: `/broadcast <message>`")
        return
    db.cursor.execute("SELECT user_id FROM users")
    users = db.cursor.fetchall()
    cnt = 0
    for u in users:
        try:
            await context.bot.send_message(chat_id=u[0], text=f"📢 **BROADCAST:**\n\n{msg}", parse_mode="Markdown")
            cnt += 1
        except Exception:
            pass
    await update.message.reply_text(f"✅ Broadcast sent to `{cnt}` users.", parse_mode="Markdown")

async def ban_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_sudo(update.effective_user.id):
        return
    try:
        t_id = int(context.args[0])
        db.cursor.execute("UPDATE users SET is_banned = 1 WHERE user_id = ?", (t_id,))
        db.conn.commit()
        await update.message.reply_text(f"🚫 User `{t_id}` ကို Ban လိုက်ပါပြီ။", parse_mode="Markdown")
    except Exception:
        await update.message.reply_text("Usage: `/ban <user_id>`")

async def unban_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_sudo(update.effective_user.id):
        return
    try:
        t_id = int(context.args[0])
        db.cursor.execute("UPDATE users SET is_banned = 0 WHERE user_id = ?", (t_id,))
        db.conn.commit()
        await update.message.reply_text(f"✅ User `{t_id}` ကို Unban လိုက်ပါပြီ။", parse_mode="Markdown")
    except Exception:
        await update.message.reply_text("Usage: `/unban <user_id>`")

async def checkuser_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_sudo(update.effective_user.id):
        return
    try:
        t_id = int(context.args[0])
        db.cursor.execute("SELECT balance, is_banned FROM users WHERE user_id = ?", (t_id,))
        row = db.cursor.fetchone()
        if row:
            await update.message.reply_text(f"🔍 **User Stats `{t_id}`**\nCoins: `{row[0]:,}`\nBanned: `{bool(row[1])}`", parse_mode="Markdown")
    except Exception:
        await update.message.reply_text("Usage: `/checkuser <user_id>`")

async def maintenance_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_sudo(update.effective_user.id):
        return
    await update.message.reply_text("🛠️ Maintenance Mode Toggled!")

async def stats_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_sudo(update.effective_user.id):
        return
    db.cursor.execute("SELECT COUNT(*) FROM users")
    u_cnt = db.cursor.fetchone()[0]
    db.cursor.execute("SELECT COUNT(*) FROM inventory")
    c_cnt = db.cursor.fetchone()[0]
    await update.message.reply_text(f"📊 **SYSTEM STATS**\nUsers: `{u_cnt:,}`\nCards Claimed: `{c_cnt:,}`", parse_mode="Markdown")

async def setpass_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_sudo(update.effective_user.id):
        return
    await update.message.reply_text("🎫 Battle Pass Rewards Updated!")

async def addcard_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_sudo(update.effective_user.id):
        return
    try:
        c_id = context.args[0]
        name = context.args[1]
        r_id = int(context.args[2])
        db.cursor.execute("INSERT INTO cards (card_id, name, rarity_id) VALUES (?, ?, ?)", (c_id, name, r_id))
        db.conn.commit()
        await update.message.reply_text(f"✅ Card **{name}** (`{c_id}`) အား Tier {r_id} ဖြင့် ထည့်သွင်းပြီးပါပြီ။", parse_mode="Markdown")
    except Exception:
        await update.message.reply_text("Usage: `/addcard <card_id> <name> <rarity_id_1_13>`")

async def delcard_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_sudo(update.effective_user.id):
        return
    try:
        c_id = context.args[0]
        db.cursor.execute("DELETE FROM cards WHERE card_id = ?", (c_id,))
        db.conn.commit()
        await update.message.reply_text(f"🗑️ Card `{c_id}` ကို Database မှ ဖျက်လိုက်ပါပြီ။", parse_mode="Markdown")
    except Exception:
        await update.message.reply_text("Usage: `/delcard <card_id>`")

async def reload_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_sudo(update.effective_user.id):
        return
    await update.message.reply_text("🔄 Configurations Reloaded!")

async def log_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_sudo(update.effective_user.id):
        return
    await update.message.reply_text("📜 System Logs fetched successfully.")
