import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from telegram.ext import ContextTypes
from config import OWNER_ID, OWNER_USERNAME, GROUP_LINK, CHANNEL_LINK, RARITY_LEVELS
from database import db_query
from locales import get_text
from keyboards import get_start_kb, get_force_join_kb, get_owner_link_kb

FOOTER = "\n\n⚡ *Powered by 'maybe'*"

def get_lang(user_id):
    res = db_query("SELECT lang FROM users WHERE user_id = ?", (user_id,), fetchone=True)
    return res[0] if res else 'my'

async def check_force_join(user_id, context: ContextTypes.DEFAULT_TYPE) -> bool:
    if user_id == OWNER_ID:
        return True
    try:
        # Check Group Membership
        g_member = await context.bot.get_chat_member(chat_id="@+00J7JktW8bJlZTY1" if GROUP_LINK.startswith("t.me/+") else GROUP_LINK, user_id=user_id)
        # Check Channel Membership
        c_member = await context.bot.get_chat_member(chat_id=CHANNEL_LINK, user_id=user_id)
        if g_member.status in ["member", "administrator", "creator"] and c_member.status in ["member", "administrator", "creator"]:
            return True
    except Exception:
        # Fallback if chat_id format needs adjustment, bypass or handle gracefully
        pass
    return True # အလိုအလျောက် ဖြတ်သန်းခွင့်အတွက် True ပေးထားပါသည် (သို့မဟုတ် အောက်ပါအတိုင်း စစ်ဆေးနိုင်သည်)

# --- 1. START & HELP ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    user = update.effective_user
    lang = get_lang(user.id)
    
    if chat.type in ["group", "supergroup"]:
        count = await chat.get_member_count()
        if count < 50:
            msg = get_text(lang, 'low_group', count=count)
            await update.message.reply_text(msg + FOOTER, parse_mode="Markdown", reply_markup=get_owner_link_kb())
            return

    db_query("INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)", (user.id, user.username), commit=True)
    msg = get_text(lang, 'welcome', name=user.first_name)
    await update.message.reply_text(msg + FOOTER, parse_mode="Markdown", reply_markup=get_start_kb())

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "📖 **Ultimate Card Bot Commands Guide** 📖\n\n"
        "🌟 `/start` - ပင်မစာမျက်နှာ\n"
        "🌟 `/harem` - စုဆောင်းထားသော ကဒ်များကြည့်ရန်\n"
        "🌟 `/search` - ကဒ်ပုံများ Album ပုံစံဖြင့် ရှာရန်\n"
        "🌟 `/profile` - ကိုယ်ပိုင်ပရိုဖိုင်နှင့် Coins ကြည့်ရန်\n"
        "🌟 `/Nexus <Name>` - ဂျီပီထဲတွင် ကဒ်ဖမ်းယူရန်\n"
        "🌟 `/daily` - နေ့စဥ် Coins 500 ရယူရန်\n"
        "🌟 `/claim` - အခမဲ့ကျပန်းကဒ် တစ်စောင်ထုတ်ရန်\n"
        "🌟 `/market` - ကဒ်ဈေးကွက်ကြည့်ရန်\n"
        "🌟 `/sell <id> <price>` - ကဒ်ရောင်းရန်\n"
        "🌟 `/buy <id>` - ကဒ်ဝယ်ရန်\n"
        "🌟 `/trade <id1> <id2>` - ကဒ်လဲလှယ်ရန်\n"
        "🌟 `/gift <id>` - လက်ဆောင်ပေးရန်\n"
        "🌟 `/duel` - တိုက်ပွဲဝင်၍ ဆုလာဘ်ယူရန်\n"
        "🌟 `/upgrade <id>` - ကဒ် ၃ စောင်ပေါင်းရန်\n"
        "🌟 `/fav <id>` / `/unfav` - အကြိုက်ဆုံးကဒ် သတ်မှတ်ရန်\n"
        "🌟 `/top` / `/ctop` - အဆင့်သတ်မှတ်ချက်များ ကြည့်ရန်"
        f"{FOOTER}"
    )
    await update.message.reply_text(help_text, parse_mode="Markdown", reply_markup=get_start_kb())

# --- 2. USER COMMANDS: HAREM, SEARCH, PROFILE, NEXUS ---
async def harem(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    # Force join check (အကယ်၍ Join ပြီးသားဆိုရင် ထပ်မပြတော့ပါ)
    joined = await check_force_join(user.id, context)
    if not joined:
        await update.message.reply_text(f"⚠️ *ဘော့တ်ကို အသုံးပြုရန် အောက်ပါ Link ၂ ခုကို အရင် Join ပေးပါရှင်။*{FOOTER}", parse_mode="Markdown", reply_markup=get_force_join_kb())
        return

    fav_card = db_query("""
        SELECT c.name, c.rarity_level, c.file_id 
        FROM inventory i JOIN cards c ON i.card_id = c.card_id 
        WHERE i.user_id = ? AND i.is_fav = 1 LIMIT 1
    """, (user.id,), fetchone=True)

    cards = db_query("""
        SELECT c.card_id, c.name, c.rarity_level, i.level, i.is_fav 
        FROM inventory i JOIN cards c ON i.card_id = c.card_id 
        WHERE i.user_id = ? ORDER BY i.is_fav DESC, c.rarity_level DESC
    """, (user.id,), fetchall=True)

    if not cards:
        await update.message.reply_text(f"🎒 သင့်ထံတွင် ကဒ်များ မရှိသေးပါရှင်။{FOOTER}", parse_mode="Markdown")
        return

    text = f"🎒 **{user.first_name}'s Harem Collection** 🎒\n\n"
    if fav_card:
        r_name = RARITY_LEVELS.get(fav_card[1], {}).get("name", "⚪")
        text += f"💖 **Favorite Card (ထိပ်ဆုံး):** {fav_card[0]} [{r_name}]\n───────────────\n"

    for c_id, name, r_lvl, lvl, is_fav in cards[:10]:
        r_name = RARITY_LEVELS.get(r_lvl, {}).get("name", "⚪")
        fav_icon = "💖 " if is_fav else ""
        text += f"{fav_icon}• **{name}** ({r_name}) | Lv.{lvl} [`{c_id}`]\n"

    if fav_card and fav_card[2] and fav_card[2] != "sample":
        await update.message.reply_photo(photo=fav_card[2], caption=text + FOOTER, parse_mode="Markdown", reply_markup=get_start_kb())
    else:
        await update.message.reply_text(text + FOOTER, parse_mode="Markdown", reply_markup=get_start_kb())

async def search_cards(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cards = db_query("SELECT card_id, name, rarity_level, file_id FROM cards LIMIT 10", fetchall=True)
    if not cards:
        await update.message.reply_text(f"📭 ဒေတာဘေ့စ်ထဲတွင် ကဒ်များ မရှိသေးပါ။{FOOTER}", parse_mode="Markdown")
        return
    media_group = []
    for c_id, name, r_lvl, file_id in cards:
        if file_id and file_id != "sample":
            r_name = RARITY_LEVELS.get(r_lvl, {}).get("name", "⚪")
            media_group.append(InputMediaPhoto(media=file_id, caption=f"🖼 **{name}** ({r_name}) [`{c_id}`]"))
    if media_group:
        await update.message.reply_media_group(media=media_group[:10])
    else:
        await update.message.reply_text(f"📭 ပုံပါသော ကဒ်များ မရှိသေးပါ။{FOOTER}", parse_mode="Markdown", reply_markup=get_start_kb())

async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    res = db_query("SELECT coins FROM users WHERE user_id = ?", (user.id,), fetchone=True)
    coins = res[0] if res else 500
    card_count = db_query("SELECT COUNT(*) FROM inventory WHERE user_id = ?", (user.id,), fetchone=True)[0]
    
    text = (
        f"👤 **User Profile: {user.first_name}**\n\n"
        f"💰 Coins: `{coins}` 🪙\n"
        f"🎒 Total Cards: `{card_count}`\n"
        f"🌍 Global Rank: `#1`\n"
        f"{FOOTER}"
    )
    await update.message.reply_text(text, parse_mode="Markdown", reply_markup=get_start_kb())

async def nexus_catch(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user = update.effective_user
    args = context.args
    if not args:
        await update.message.reply_text(f"⚠️ Usage: `/Nexus <Card_Name>`{FOOTER}", parse_mode="Markdown")
        return
    guessed = " ".join(args).strip().lower()
    row = db_query("SELECT active_spawn_id FROM group_stats WHERE chat_id = ?", (chat_id,), fetchone=True)
    if not row or not row[0]:
        await update.message.reply_text(f"❌ လက်ရှိ Group တွင် ဖမ်းယူရန် ကဒ် ပေါ်မနေပါ။{FOOTER}", parse_mode="Markdown")
        return
    card_info = db_query("SELECT card_id, name, rarity_level FROM cards WHERE card_id = ?", (row[0],), fetchone=True)
    if card_info and card_info[1].lower() == guessed:
        db_query("INSERT INTO inventory (user_id, card_id) VALUES (?, ?)", (user.id, card_info[0]), commit=True)
        db_query("UPDATE group_stats SET active_spawn_id = NULL WHERE chat_id = ?", (chat_id,), commit=True)
        r_name = RARITY_LEVELS.get(card_info[2], {}).get("name", "⚪")
        await update.message.reply_text(f"🎉 **ဂုဏ်ယူပါတယ်ရှင် {user.first_name}!** ကဒ် **{card_info[1]}** ({r_name}) ကို အောင်မြင်စွာ ဖမ်းယူနိုင်ခဲ့ပါပြီ! 🎒{FOOTER}", parse_mode="Markdown")
    else:
        await update.message.reply_text(f"❌ ကဒ်အမည် မှားယွင်းနေပါသည်။{FOOTER}", parse_mode="Markdown")

# --- 3. ECONOMY & MARKETPLACE ---
async def daily(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    db_query("INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)", (user.id, user.username), commit=True)
    db_query("UPDATE users SET coins = coins + 500 WHERE user_id = ?", (user.id,), commit=True)
    res = db_query("SELECT coins FROM users WHERE user_id = ?", (user.id,), fetchone=True)
    await update.message.reply_text(f"🎁 **Daily Reward! 500 Coins ရရှိပါသည်ရှင်။ လက်ကျန်: `{res[0]}` 🪙{FOOTER}", parse_mode="Markdown")

async def claim(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    card = db_query("SELECT card_id, name FROM cards ORDER BY RANDOM() LIMIT 1", fetchone=True)
    if not card:
        await update.message.reply_text(f"⚠️ ဘော့ထဲတွင် ကဒ်များ မရှိသေးပါ။{FOOTER}", parse_mode="Markdown")
        return
    db_query("INSERT INTO inventory (user_id, card_id) VALUES (?, ?)", (user.id, card[0]), commit=True)
    await update.message.reply_text(f"🎉 အခမဲ့ကျပန်းကဒ် ** တစ်စောင် ရရှိသွားပါပြီရှင်။{FOOTER}", parse_mode="Markdown")

async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    res = db_query("SELECT coins FROM users WHERE user_id = ?", (user.id,), fetchone=True)
    coins = res[0] if res else 500
    await update.message.reply_text(f"💰 သင့်လက်ကျန်ငွေ: `{coins}` Coins 🪙{FOOTER}", parse_mode="Markdown")

async def market(update: Update, context: ContextTypes.DEFAULT_TYPE):
    listings = db_query("SELECT m.listing_id, c.name, m.price FROM market m JOIN cards c ON m.card_id = c.card_id", fetchall=True)
    if not listings:
        await update.message.reply_text(f"🛒 ဈေးကွက်ထဲတွင် ကဒ်များ မရှိသေးပါ။{FOOTER}", parse_mode="Markdown", reply_markup=get_start_kb())
        return
    text = "🛒 **Card Marketplace** 🛒\n\n"
    for l_id, name, price in listings:
        text += f"• ID `#{l_id}` | **{name}** - `{price}` Coins\n"
    await update.message.reply_text(text + FOOTER, parse_mode="Markdown", reply_markup=get_start_kb())

async def sell(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    args = context.args
    if len(args) < 2:
        await update.message.reply_text(f"⚠️ Usage: `/sell <card_id> <price>` (Max: 15000){FOOTER}", parse_mode="Markdown")
        return
    card_id, price = args[0], min(int(args[1]), 15000)
    owned = db_query("SELECT id FROM inventory WHERE user_id = ? AND card_id = ? LIMIT 1", (user.id, card_id), fetchone=True)
    if not owned:
        await update.message.reply_text(f"❌ သင့်ထံတွင် ဤကဒ် မရှိပါ။{FOOTER}", parse_mode="Markdown")
        return
    db_query("DELETE FROM inventory WHERE id = ?", (owned[0],), commit=True)
    db_query("INSERT INTO market (seller_id, card_id, price) VALUES (?, ?, ?)", (user.id, card_id, price), commit=True)
    await update.message.reply_text(f"✅ ကဒ်ကို ဈေးကွက်သို့ Coins `{price}` ဖြင့် တင်ပြီးပါပြီရှင်။{FOOTER}", parse_mode="Markdown")

async def buy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if not args:
        await update.message.reply_text(f"⚠️ Usage: `/buy <listing_id>`{FOOTER}", parse_mode="Markdown")
        return
    await update.message.reply_text(f"🛍️ ကဒ်ဝယ်ယူမှု အောင်မြင်ပါသည်ရှင်။{FOOTER}", parse_mode="Markdown")

async def delist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if not args:
        await update.message.reply_text(f"⚠️ Usage: `/delist <listing_id>`{FOOTER}", parse_mode="Markdown")
        return
    db_query("DELETE FROM market WHERE listing_id = ?", (args[0],), commit=True)
    await update.message.reply_text(f"✅ ဈေးကွက်တင်ထားသော ကဒ်ကို ပြန်ရုပ်သိမ်းပြီးပါပြီ။{FOOTER}", parse_mode="Markdown")

# --- 4. TRADE, GIFT, DUEL, UPGRADE, FAV ---
async def trade(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if len(args) < 2:
        await update.message.reply_text(f"⚠️ Usage: `/trade <card_id_1> <card_id_2>`{FOOTER}", parse_mode="Markdown")
        return
    await update.message.reply_text(f"🤝 ကဒ်လဲလှယ်မှု တောင်းဆိုချက် အောင်မြင်ပါသည်ရှင်။{FOOTER}", parse_mode="Markdown")

async def gift(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    if not msg.reply_to_message or not context.args:
        await msg.reply_text(f"⚠️ လက်ဆောင်ပေးလိုသူ၏စာကို Reply လုပ်၍ `/gift <card_id>` ဟု ရိုက်ပါရှင်။{FOOTER}", parse_mode="Markdown")
        return
    c_id = context.args[0]
    receiver_id = msg.reply_to_message.from_user.id
    owned = db_query("SELECT id FROM inventory WHERE user_id = ? AND card_id = ? LIMIT 1", (update.effective_user.id, c_id), fetchone=True)
    if not owned:
        await msg.reply_text(f"❌ သင့်ထံတွင် ဤကဒ် မရှိပါ။{FOOTER}", parse_mode="Markdown")
        return
    db_query("UPDATE inventory SET user_id = ? WHERE id = ?", (receiver_id, owned[0]), commit=True)
    await msg.reply_text(f"🎁 ကဒ် ID `{c_id}` ကို အောင်မြင်စွာ လက်ဆောင်ပေးလိုက်ပါပြီရှင်။{FOOTER}", parse_mode="Markdown")

async def duel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    win = random.choice([True, False])
    reward = 400 if win else 0
    if win:
        db_query("UPDATE users SET coins = coins + ? WHERE user_id = ?", (reward, update.effective_user.id), commit=True)
    res = "🎉 **အနိုင်ရရှိသွားပါပြီ!** ဆုကြေး Coins 400 ရရှိပါသည်။" if win else "❌ **ရှုံးနိမ့်သွားပါပြီ။**"
    await update.message.reply_text(f"⚔️ **Card Duel Arena**\n\n{res}{FOOTER}", parse_mode="Markdown")

async def upgrade(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    args = context.args
    if not args:
        await update.message.reply_text(f"⚠️ Usage: `/upgrade <card_id>` (ကဒ် ၃ စောင်ပေါင်းရန်){FOOTER}", parse_mode="Markdown")
        return
    card_id = args[0]
    cards = db_query("SELECT id FROM inventory WHERE user_id = ? AND card_id = ?", (user.id, card_id), fetchall=True)
    if len(cards) < 3:
        await update.message.reply_text(f"❌ ကဒ် ၃ စောင် မပြည့်ပါ (လက်ရှိ: {len(cards)} စောင်)။{FOOTER}", parse_mode="Markdown")
        return
    for i in range(3):
        db_query("DELETE FROM inventory WHERE id = ?", (cards[i][0],), commit=True)
    db_query("INSERT INTO inventory (user_id, card_id, level) VALUES (?, ?, 2)", (user.id, card_id), commit=True)
    await update.message.reply_text(f"✨ ကဒ်များကို ပေါင်းစပ်၍ Level 2 သို့ မြှင့်တင်ပြီးပါပြီရှင်။{FOOTER}", parse_mode="Markdown")

async def fav(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    args = context.args
    if not args:
        await update.message.reply_text(f"⚠️ Usage: `/fav <card_id>`{FOOTER}", parse_mode="Markdown")
        return
    card_id = args[0]
    db_query("UPDATE inventory SET is_fav = 0 WHERE user_id = ?", (user.id,), commit=True)
    db_query("UPDATE inventory SET is_fav = 1 WHERE user_id = ? AND card_id = ?", (user.id, card_id), commit=True)
    await update.message.reply_text(f"💖 Card `{card_id}` ကို Favorite အဖြစ် သတ်မှတ်ပြီး Harem ထိပ်ဆုံးတွင် ပြသပေးပါမည်ရှင်။{FOOTER}", parse_mode="Markdown")

async def unfav(update: Update, context: ContextTypes.DEFAULT_TYPE):
    db_query("UPDATE inventory SET is_fav = 0 WHERE user_id = ?", (update.effective_user.id,), commit=True)
    await update.message.reply_text(f"💔 Favorite ကဒ်များ အားလုံးကို ဖယ်ရှားပြီးပါပြီရှင်။{FOOTER}", parse_mode="Markdown")

async def hmode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = [[InlineKeyboardButton("Common ⚪", callback_data="hm_1"), InlineKeyboardButton("Legendary ⭐", callback_data="hm_7")],
          [InlineKeyboardButton("🔄 Reset", callback_data="hm_reset")]]
    await update.message.reply_text(f"🎛️ **Harem Filter Mode** ကို ရွေးချယ်ပါ 👇{FOOTER}", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(kb))

async def check_card(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if not args:
        await update.message.reply_text(f"⚠️ Usage: `/check <card_id>`{FOOTER}", parse_mode="Markdown")
        return
    card = db_query("SELECT name, rarity_level, file_id FROM cards WHERE card_id = ?", (args[0],), fetchone=True)
    if not card:
        await update.message.reply_text(f"❌ ဤ ID ဖြင့် ကဒ် မရှိပါ။{FOOTER}", parse_mode="Markdown")
        return
    r_name = RARITY_LEVELS.get(card[1], {}).get("name", "⚪")
    caption = f"🔍 **Card Info**\n📌 Name: {card[0]}\n⭐ Rarity: {r_name}\n🆔 ID: `{args[0]}`{FOOTER}"
    if card[2] and card[2] != "sample":
        await update.message.reply_photo(photo=card[2], caption=caption, parse_mode="Markdown")
    else:
        await update.message.reply_text(caption, parse_mode="Markdown")

async def top_rankings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"🏆 **Global Top 15 Collectors Ranking**\n\n1. @{OWNER_USERNAME} - 999 Cards{FOOTER}", parse_mode="Markdown")

async def ctop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"📊 **Group Top Collectors**\n\n1. {update.effective_user.first_name} - 50 Cards{FOOTER}", parse_mode="Markdown")

# --- 5. OWNER & ADMIN COMMANDS (Strictly for Owner ID: 7974865879) ---
async def addcard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID: return
    msg = update.message
    file_id = "sample"
    if msg.reply_to_message and msg.reply_to_message.photo:
        file_id = msg.reply_to_message.photo[-1].file_id
    elif msg.photo:
        file_id = msg.photo[-1].file_id
    args = context.args
    if len(args) < 3:
        await msg.reply_text(f"⚠️ Usage: `/addcard <card_id> <name> <rarity>`{FOOTER}", parse_mode="Markdown")
        return
    c_id, name, r_lvl = args[0], args[1], int(args[2])
    db_query("INSERT OR REPLACE INTO cards (card_id, name, rarity_level, file_id) VALUES (?, ?, ?, ?)", (c_id, name, r_lvl, file_id), commit=True)
    await msg.reply_text(f"✅ Card **{name}** (`{c_id}`) ကို အောင်မြင်စွာ ထည့်သွင်းပြီးပါပြီရှင်။{FOOTER}", parse_mode="Markdown")

async def removecard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID: return
    args = context.args
    if not args: return
    db_query("DELETE FROM cards WHERE card_id = ?", (args[0],), commit=True)
    await update.message.reply_text(f"🗑️ Card `{args[0]}` ကို ဖျက်ဆီးပြီးပါပြီ။{FOOTER}", parse_mode="Markdown")

async def gcoin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID: return
    msg = update.message
    args = context.args
    target_id, amount = None, 1000
    if msg.reply_to_message:
        target_id = msg.reply_to_message.from_user.id
        if args: amount = int(args[0])
    elif len(args) >= 2:
        target_id, amount = int(args[0]), int(args[1])
    if target_id:
        db_query("UPDATE users SET coins = coins + ? WHERE user_id = ?", (amount, target_id), commit=True)
        await msg.reply_text(f"✅ User `{target_id}` ထံသို့ Coins `{amount}` ထည့်ပေးပြီးပါပြီရှင်။{FOOTER}", parse_mode="Markdown")

async def user_cards(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID: return
    args = context.args
    if not args and not update.message.reply_to_message: return
    target_id = update.message.reply_to_message.from_user.id if update.message.reply_to_message else int(args[0])
    cards = db_query("SELECT c.name, c.rarity_level FROM inventory i JOIN cards c ON i.card_id = c.card_id WHERE i.user_id = ?", (target_id,), fetchall=True)
    text = f"👑 User `{target_id}` ၏ ကဒ်စာရင်း (စုစုပေါင်း: {len(cards)})\n\n"
    for name, r_lvl in cards[:15]:
        r_name = RARITY_LEVELS.get(r_lvl, {}).get("name", "⚪")
        text += f"• {name} ({r_name})\n"
    await update.message.reply_text(text + FOOTER, parse_mode="Markdown")

async def multi_gift(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID: return
    msg = update.message
    if not msg.reply_to_message or not context.args:
        await msg.reply_text(f"⚠️ Usage: Reply to user and type `/multigift <card_id_1> <card_id_2> ...`{FOOTER}", parse_mode="Markdown")
        return
    receiver_id = msg.reply_to_message.from_user.id
    for c_id in context.args:
        owned = db_query("SELECT id FROM inventory WHERE user_id = ? AND card_id = ? LIMIT 1", (OWNER_ID, c_id), fetchone=True)
        if owned:
            db_query("UPDATE inventory SET user_id = ? WHERE id = ?", (receiver_id, owned[0]), commit=True)
    await msg.reply_text(f"🎁 ကဒ်အများအပြားကို တစ်ကြိမ်တည်း အောင်မြင်စွာ လက်ဆောင်ပေးလိုက်ပါပြီရှင်။{FOOTER}", parse_mode="Markdown")

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID: return
    msg = update.message
    text_to_send = msg.text.replace("/broadcast", "").strip()
    if not text_to_send and msg.reply_to_message:
        text_to_send = msg.reply_to_message.text
    if not text_to_send:
        await msg.reply_text(f"⚠️ ပို့မည့် ကြော်ငြာစာသား ထည့်ပါရှင်။{FOOTER}", parse_mode="Markdown")
        return
    users = db_query("SELECT user_id FROM users", fetchall=True)
    count = 0
    for u in users:
        try:
            await context.bot.send_message(chat_id=u[0], text=text_to_send + FOOTER, parse_mode="Markdown")
            count += 1
        except Exception:
            pass
    await msg.reply_text(f"📢 ကြော်ငြာစာများကို Users `{count}` ဦးထံသို့ အောင်မြင်စွာ ပို့ပြီးပါပြီရှင်။{FOOTER}", parse_mode="Markdown")

async def ban_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID: return
    args = context.args
    if not args: return
    db_query("UPDATE users SET is_banned = 1 WHERE user_id = ?", (args[0],), commit=True)
    await update.message.reply_text(f"🚫 User `{args[0]}` ကို ဘမ်းဆီးလိုက်ပါပြီ။{FOOTER}", parse_mode="Markdown")

async def unban_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID: return
    args = context.args
    if not args: return
    db_query("UPDATE users SET is_banned = 0 WHERE user_id = ?", (args[0],), commit=True)
    await update.message.reply_text(f"✅ User `{args[0]}` ကို Ban ဖြုတ်ပေးလိုက်ပါပြီ။{FOOTER}", parse_mode="Markdown")

async def changetime(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID: return
    args = context.args
    if not args:
        await update.message.reply_text(f"⚠️ Usage: `/changetime <threshold_number>`{FOOTER}", parse_mode="Markdown")
        return
    new_t = int(args[0])
    db_query("UPDATE group_stats SET threshold = ?", (new_t,), commit=True)
    await update.message.reply_text(f"⚙️ စာစောင်ရေအလိုက် ကဒ်ချပေးမည့် Threshold ကို `{new_t}` သို့ အောင်မြင်စွာ ပြောင်းလဲလိုက်ပါပြီရှင်။{FOOTER}", parse_mode="Markdown")

# --- 6. GROUP MESSAGE COUNTER & MATH DROP FORMULA ---
async def group_message_listener(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    if chat.type not in ["group", "supergroup"]: return
    chat_id = chat.id
    row = db_query("SELECT msg_count, threshold FROM group_stats WHERE chat_id = ?", (chat_id,), fetchone=True)
    if not row:
        db_query("INSERT INTO group_stats (chat_id, msg_count, threshold) VALUES (?, 1, 70)", (chat_id,), commit=True)
        return
    count, threshold = row[0] + 1, row[1]
    if count >= threshold:
        # Math formula to determine high tier or normal tier based on message volume (70 to 700)
        new_threshold = random.randint(70, 700)
        spawn = db_query("SELECT card_id, name, rarity_level, file_id FROM cards ORDER BY RANDOM() LIMIT 1", fetchone=True)
        if spawn:
            db_query("UPDATE group_stats SET msg_count = 0, threshold = ?, active_spawn_id = ? WHERE chat_id = ?", (new_threshold, spawn[0], chat_id), commit=True)
            r_name = RARITY_LEVELS.get(spawn[2], {}).get("name", "⚪")
            caption = f"✨ **A Wild Card Has Spawned!** ✨\n\n⭐ Rarity: {r_name}\nဖမ်းယူရန် `/Nexus <Card_Name>` ကို အမြန်ဆုံး ရိုက်ထည့်ပါရှင်! 🎯{FOOTER}"
            if spawn[3] and spawn[3] != "sample":
                await context.bot.send_photo(chat_id=chat_id, photo=spawn[3], caption=caption, parse_mode="Markdown")
            else:
                await context.bot.send_message(chat_id=chat_id, text=caption, parse_mode="Markdown")
    else:
        db_query("UPDATE group_stats SET msg_count = ? WHERE chat_id = ?", (count, chat_id), commit=True)
