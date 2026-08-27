import logging
import os
import random
import time

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from config import (
    BOT_TOKEN,
    OWNER_ID,
    CHANNEL_ID,
    GROUP_LINK,
    CHANNEL_LINK,
    WAIFU_LINK,
    DAILY_COINS,
    CLAIM_COOLDOWN_HOURS,
    CLAIM_LIMIT_24H,
    HAREM_PER_PAGE,
    MARKET_PER_PAGE,
    TOP_LIMIT,
    HMODE_LIMIT,
    EDITIONS,
    PREMIUM_PRICE,
    DEFAULT_LANGUAGE,
    MIN_GROUP_MEMBERS,
    REQUIRE_BOT_ADMIN,
    REQUIRE_OWNER_APPROVAL,
    BOT_NAME,
    BOT_VERSION,
)

from database import (
    init_db,
    add_or_update_user,
    get_user,
    add_coins,
    remove_coins,
    get_balance,
    get_card,
    get_all_cards,
    search_cards,
    add_user_card,
    get_user_cards,
    count_user_cards,
    add_favorite,
    remove_favorite,
    is_favorite,
    get_global_top,
    get_group_top,
    get_setting,
    set_setting,
    is_admin,
    save_group,
    approve_group,
    reject_group,
    is_group_enabled,
)


# ============================================================
# LOGGING
# ============================================================

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

logger = logging.getLogger(__name__)


# ============================================================
# STARTUP
# ============================================================

init_db()


# ============================================================
# TEXT
# ============================================================

START_TEXT_MY = f"""
🎴 <b>{BOT_NAME}</b>

✨ Welcome to Nexus Card!

🎴 Card Collection
💰 Coin Economy
🛒 Card Market
⚔️ Duel System
🏆 Global Rankings
🎁 Daily Rewards
⭐ Favorites

<b>Version:</b> {BOT_VERSION}

အောက်က Button တွေကနေ စတင်အသုံးပြုနိုင်ပါတယ်။
"""

START_TEXT_EN = f"""
🎴 <b>{BOT_NAME}</b>

✨ Welcome to Nexus Card!

🎴 Card Collection
💰 Coin Economy
🛒 Card Market
⚔️ Duel System
🏆 Global Rankings
🎁 Daily Rewards
⭐ Favorites

<b>Version:</b> {BOT_VERSION}

Use the buttons below to get started.
"""


# ============================================================
# HELP
# ============================================================

HELP_MY = """
📚 <b>NEXUS CARD — COMMAND GUIDE</b>

🎴 <b>Basic</b>

/start — Bot စတင်ရန်
/help — Command Guide
/balance — Coin လက်ကျန်
/daily — နေ့စဉ် 500 Coins
/profile — Profile
/harem — ကိုယ်ပိုင် Card Collection
/search — Card ရှာရန်
/check [id] — Card ကြည့်ရန်

🏆 <b>Ranking</b>

/top — Global Top 15
/ctop — လက်ရှိ Group Top
/rankings — Global Ranking

🎴 <b>Card</b>

/claim — Card ရယူရန်
/Nexus [Card Name] — Card ရှာရန်
/fav [id] — Favorite
/unfav [id] — Favorite ဖြုတ်ရန်
/hmode — Harem display mode
/reset — Harem setting reset
/upgrade — Card Level တင်ရန်

🛒 <b>Market</b>

/market — ရောင်းရန်တင်ထားသော Card များ
/sell [char_id] [price] — Card ရောင်းရန်
/buy [listing_id] — Card ဝယ်ရန်
/delist [listing_id] — Listing ဖြုတ်ရန်
/sellprice — Card စျေးနှုန်း

🤝 <b>Social</b>

/gift [char_id] — Card လက်ဆောင်ပေးရန်
/trade YOUR_ID THEIR_ID — Trade
/duel — Duel

🎁 <b>Daily</b>

/todayNexusCatch — ဒီနေ့ Card ရထားသူ Ranking

👑 <b>Owner/Admin</b>

/drop
/addcard
/deletecard
/givecard
/givecoin
/setprice
/setdrop
/setadmin
/deladmin
/approve
/reject
/broadcast
/stats
/maintenance
/changetime
"""


HELP_EN = """
📚 <b>NEXUS CARD — COMMAND GUIDE</b>

🎴 <b>Basic</b>

/start — Start the bot
/help — Command Guide
/balance — Check coins
/daily — Daily 500 Coins
/profile — Profile
/harem — Your collection
/search — Search cards
/check [id] — View card

🏆 <b>Ranking</b>

/top — Global Top 15
/ctop — Current Group Top
/rankings — Global Ranking

🎴 <b>Cards</b>

/claim — Claim a card
/Nexus [Card Name] — Search card
/fav [id] — Favorite
/unfav [id] — Remove favorite
/hmode — Harem display mode
/reset — Reset harem mode
/upgrade — Upgrade card

🛒 <b>Market</b>

/market — View marketplace
/sell [char_id] [price] — Sell card
/buy [listing_id] — Buy listing
/delist [listing_id] — Remove listing
/sellprice — Card prices

🤝 <b>Social</b>

/gift [char_id] — Gift a card
/trade YOUR_ID THEIR_ID — Trade
/duel — Duel

🎁 <b>Daily</b>

/todayNexusCatch — Today's catch ranking

👑 <b>Owner/Admin</b>

/drop
/addcard
/deletecard
/givecard
/givecoin
/setprice
/setdrop
/setadmin
/deladmin
/approve
/reject
/broadcast
/stats
/maintenance
/changetime
"""


# ============================================================
# USER REGISTER
# ============================================================

def register_user(update: Update):
    user = update.effective_user

    if not user:
        return

    add_or_update_user(
        user.id,
        user.username or "",
        user.first_name or "",
        DEFAULT_LANGUAGE,
    )


# ============================================================
# ADMIN CHECK
# ============================================================

def is_owner(user_id: int) -> bool:
    return user_id == OWNER_ID


def is_owner_or_admin(user_id: int) -> bool:
    return is_owner(user_id) or is_admin(user_id)


# ============================================================
# GROUP ACCESS
# ============================================================

async def check_group_access(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> bool:

    chat = update.effective_chat

    if not chat:
        return True

    # Private chat
    if chat.type == "private":
        return True

    # Owner bypass
    if update.effective_user and is_owner(
        update.effective_user.id
    ):
        return True

    # Get bot membership
    try:
        bot_member = await context.bot.get_chat_member(
            chat.id,
            context.bot.id,
        )

        bot_is_admin = bot_member.status in (
            "administrator",
            "creator",
        )

    except Exception:
        bot_is_admin = False

    # Get member count
    try:
        member_count = await context.bot.get_chat_member_count(
            chat.id
        )
    except Exception:
        member_count = 0

    # Save group
    save_group(
        chat.id,
        chat.title or "",
        member_count,
        int(bot_is_admin),
        update.effective_user.id
        if update.effective_user
        else 0,
    )

    # Bot Admin required
    if REQUIRE_BOT_ADMIN and not bot_is_admin:
        await update.effective_message.reply_text(
            "⚠️ <b>Bot Admin မဟုတ်သေးပါ။</b>\n\n"
            "Bot ကို Group Admin ပေးပြီး ပြန်အသုံးပြုပါ။",
            parse_mode="HTML",
        )
        return False

    # Minimum members
    if member_count < MIN_GROUP_MEMBERS:
        await update.effective_message.reply_text(
            f"👥 ဒီ Group မှာ အနည်းဆုံး "
            f"<b>{MIN_GROUP_MEMBERS}</b> ယောက်ရှိရပါမယ်။\n\n"
            f"လက်ရှိ Members: <b>{member_count}</b>",
            parse_mode="HTML",
        )
        return False

    # Owner approval
    if REQUIRE_OWNER_APPROVAL and not is_group_enabled(chat.id):
        await update.effective_message.reply_text(
            "🔐 <b>Owner Approval လိုအပ်ပါတယ်။</b>\n\n"
            "Bot Owner ကို အကြောင်းကြားပြီး "
            "Group ကို ဖွင့်ပေးမှ အသုံးပြုနိုင်ပါတယ်။",
            parse_mode="HTML",
        )
        return False

    return True


# ============================================================
# START
# ============================================================

async def start_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    register_user(update)

    keyboard = [
        [
            InlineKeyboardButton(
                "💗 I'm Waifu",
                url=WAIFU_LINK,
            )
        ],
        [
            InlineKeyboardButton(
                "👥 Group",
                url=GROUP_LINK,
            ),
            InlineKeyboardButton(
                "📢 Channel",
                url=CHANNEL_LINK,
            ),
        ],
        [
            InlineKeyboardButton(
                "📚 Help",
                callback_data="help",
            )
        ],
    ]

    await update.effective_message.reply_text(
        START_TEXT_MY,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML",
    )


# ============================================================
# HELP
# ============================================================

async def help_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    register_user(update)

    keyboard = [
        [
            InlineKeyboardButton(
                "🇲🇲 Myanmar",
                callback_data="help_my",
            ),
            InlineKeyboardButton(
                "🇬🇧 English",
                callback_data="help_en",
            ),
        ]
    ]

    await update.effective_message.reply_text(
        HELP_MY,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML",
    )


# ============================================================
# HELP CALLBACK
# ============================================================

async def help_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    query = update.callback_query
    await query.answer()

    if query.data == "help_en":
        text = HELP_EN
    else:
        text = HELP_MY

    keyboard = [
        [
            InlineKeyboardButton(
                "🇲🇲 Myanmar",
                callback_data="help_my",
            ),
            InlineKeyboardButton(
                "🇬🇧 English",
                callback_data="help_en",
            ),
        ],
        [
            InlineKeyboardButton(
                "🏠 Start",
                callback_data="start",
            )
        ],
    ]

    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="HTML",
    )


# ============================================================
# BALANCE
# ============================================================

async def balance_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    register_user(update)

    user_id = update.effective_user.id
    coins = get_balance(user_id)

    await update.effective_message.reply_text(
        f"💰 <b>Your Balance</b>\n\n"
        f"🪙 Coins: <b>{coins:,}</b>",
        parse_mode="HTML",
    )


# ============================================================
# DAILY
# ============================================================

async def daily_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    register_user(update)

    user_id = update.effective_user.id
    user = get_user(user_id)

    now = time.time()

    last_daily = 0

    if user:
        last_daily = user["daily_claim"] or 0

    if now - last_daily < 86400:

        remaining = int(
            86400 - (now - last_daily)
        )

        hours = remaining // 3600
        minutes = (remaining % 3600) // 60

        await update.effective_message.reply_text(
            f"⏳ Daily Reward ပြန်ရဖို့ "
            f"<b>{hours}h {minutes}m</b> ကျန်ပါသေးတယ်။",
            parse_mode="HTML",
        )

        return

    add_coins(user_id, DAILY_COINS)

    with __import__("database").get_db() as db:
        db.execute(
            """
            UPDATE users
            SET daily_claim = ?
            WHERE user_id = ?
            """,
            (now, user_id),
        )

    await update.effective_message.reply_text(
        f"🎁 <b>Daily Reward!</b>\n\n"
        f"🪙 +{DAILY_COINS:,} Coins\n\n"
        f"💰 Balance: <b>{get_balance(user_id):,}</b>",
        parse_mode="HTML",
    )


# ============================================================
# PROFILE
# ============================================================

async def profile_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    register_user(update)

    user = update.effective_user
    db_user = get_user(user.id)

    cards = count_user_cards(user.id)
    balance = get_balance(user.id)

    caption = (
        f"👤 <b>{user.first_name}</b>\n\n"
        f"🆔 ID: <code>{user.id}</code>\n"
        f"🎴 Cards: <b>{cards}</b>\n"
        f"🪙 Coins: <b>{balance:,}</b>\n"
        f"⭐ Level: <b>{db_user['level'] if db_user else 1}</b>\n"
        f"✨ EXP: <b>{db_user['exp'] if db_user else 0}</b>\n"
    )

    photos = await context.bot.get_user_profile_photos(
        user.id,
        limit=1,
    )

    if photos.total_count > 0:

        file_id = photos.photos[0][-1].file_id

        await update.effective_message.reply_photo(
            photo=file_id,
            caption=caption,
            parse_mode="HTML",
        )

    else:

        await update.effective_message.reply_text(
            caption,
            parse_mode="HTML",
        )


# ============================================================
# HAREM
# ============================================================

async def harem_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    register_user(update)

    if not await check_group_access(
        update,
        context,
    ):
        return

    user_id = update.effective_user.id
    cards = get_user_cards(user_id)

    if not cards:

        await update.effective_message.reply_text(
            "🎴 <b>Your Harem is Empty!</b>\n\n"
            "Card ရဖို့ /claim ကိုအသုံးပြုပါ။",
            parse_mode="HTML",
        )

        return

    page = 0

    await send_harem_page(
        update.effective_message,
        cards,
        page,
    )


async def send_harem_page(
    message,
    cards,
    page,
):

    start = page * HAREM_PER_PAGE
    end = start + HAREM_PER_PAGE

    page_cards = cards[start:end]

    text = (
        f"🎴 <b>HAREM</b>\n"
        f"📄 Page {page + 1}/"
        f"{max(1, (len(cards) + HAREM_PER_PAGE - 1) // HAREM_PER_PAGE)}\n\n"
    )

    for index, card in enumerate(
        page_cards,
        start=start + 1,
    ):

        fav = "⭐" if card["favorite"] else ""

        text += (
            f"<b>{index}.</b> "
            f"{fav}{card['name']}\n"
            f"🆔 {card['char_id']} • "
            f"{card['edition']} • "
            f"Lv.{card['level']}\n\n"
        )

    buttons = []

    if page > 0:
        buttons.append(
            InlineKeyboardButton(
                "⬅️",
                callback_data=f"harem:{page - 1}",
            )
        )

    if end < len(cards):
        buttons.append(
            InlineKeyboardButton(
                "➡️",
                callback_data=f"harem:{page + 1}",
            )
        )

    keyboard = [buttons] if buttons else []

    await message.reply_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard)
        if keyboard
        else None,
        parse_mode="HTML",
    )


# ============================================================
# HAREM CALLBACK
# ============================================================

async def harem_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    query = update.callback_query
    await query.answer()

    if not query.data.startswith("harem:"):
        return

    page = int(
        query.data.split(":")[1]
    )

    cards = get_user_cards(
        query.from_user.id
    )

    if not cards:
        await query.edit_message_text(
            "🎴 Harem is empty."
        )
        return

    start = page * HAREM_PER_PAGE
    end = start + HAREM_PER_PAGE

    page_cards = cards[start:end]

    text = (
        f"🎴 <b>HAREM</b>\n"
        f"📄 Page {page + 1}/"
        f"{max(1, (len(cards) + HAREM_PER_PAGE - 1) // HAREM_PER_PAGE)}\n\n"
    )

    for index, card in enumerate(
        page_cards,
        start=start + 1,
    ):

        fav = "⭐" if card["favorite"] else ""

        text += (
            f"<b>{index}.</b> "
            f"{fav}{card['name']}\n"
            f"🆔 {card['char_id']} • "
            f"{card['edition']} • "
            f"Lv.{card['level']}\n\n"
        )

    buttons = []

    if page > 0:
        buttons.append(
            InlineKeyboardButton(
                "⬅️",
                callback_data=f"harem:{page - 1}",
            )
        )

    if end < len(cards):
        buttons.append(
            InlineKeyboardButton(
                "➡️",
                callback_data=f"harem:{page + 1}",
            )
        )

    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(
            [buttons]
        ) if buttons else None,
        parse_mode="HTML",
    )


# ============================================================
# SEARCH
# ============================================================

async def search_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    register_user(update)

    if not context.args:

        await update.effective_message.reply_text(
            "🔎 Usage:\n"
            "<code>/search Naruto</code>",
            parse_mode="HTML",
        )

        return

    keyword = " ".join(context.args)

    cards = search_cards(keyword)

    if not cards:

        await update.effective_message.reply_text(
            "❌ Card မတွေ့ပါ။"
        )

        return

    text = (
        f"🔎 <b>Search:</b> {keyword}\n\n"
    )

    for card in cards[:SEARCH_LIMIT]:

        text += (
            f"🎴 <b>{card['name']}</b>\n"
            f"🆔 <code>{card['char_id']}</code>\n"
            f"✨ {card['edition']}\n"
            f"💰 {card['price']:,} Coins\n\n"
        )

    await update.effective_message.reply_text(
        text,
        parse_mode="HTML",
    )


SEARCH_LIMIT = 10


# ============================================================
# CHECK CARD
# ============================================================

async def check_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    register_user(update)

    if not context.args:

        await update.effective_message.reply_text(
            "Usage: /check [card_id]"
        )

        return

    char_id = context.args[0]

    card = get_card(char_id)

    if not card:

        await update.effective_message.reply_text(
            "❌ Card မတွေ့ပါ။"
        )

        return

    text = (
        f"🎴 <b>{card['name']}</b>\n\n"
        f"🆔 ID: <code>{card['char_id']}</code>\n"
        f"✨ Edition: <b>{card['edition']}</b>\n"
        f"⭐ Rarity: <b>{card['rarity']}</b>\n"
        f"💰 Price: <b>{card['price']:,}</b>\n"
        f"📝 {card['description'] or 'No description'}"
    )

    if card["media_type"] == "video" and card["video_file_id"]:

        await update.effective_message.reply_video(
            video=card["video_file_id"],
            caption=text,
            parse_mode="HTML",
        )

    elif card["image_file_id"]:

        await update.effective_message.reply_photo(
            photo=card["image_file_id"],
            caption=text,
            parse_mode="HTML",
        )

    else:

        await update.effective_message.reply_text(
            text,
            parse_mode="HTML",
        )


# ============================================================
# TOP
# ============================================================

async def top_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    register_user(update)

    top = get_global_top(TOP_LIMIT)

    if not top:

        await update.effective_message.reply_text(
            "🏆 Ranking မရှိသေးပါ။"
        )

        return

    text = "🏆 <b>GLOBAL TOP 15</b>\n\n"

    medals = {
        1: "🥇",
        2: "🥈",
        3: "🥉",
    }

    for index, row in enumerate(top, start=1):

        medal = medals.get(
            index,
            f"{index}.",
        )

        name = (
            f"@{row['username']}"
            if row["username"]
            else row["first_name"]
        )

        text += (
            f"{medal} <b>{name}</b> — "
            f"🎴 {row['card_count']}\n"
        )

    await update.effective_message.reply_text(
        text,
        parse_mode="HTML",
    )


# ============================================================
# RANKINGS
# ============================================================

async def rankings_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    await top_command(
        update,
        context,
    )


# ============================================================
# GROUP TOP
# ============================================================

async def ctop_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    register_user(update)

    chat = update.effective_chat

    if not chat or chat.type == "private":

        await update.effective_message.reply_text(
            "👥 ဒီ command ကို Group ထဲမှာ အသုံးပြုပါ။"
        )

        return

    if not await check_group_access(
        update,
        context,
    ):
        return

    try:

        members = []

        administrators = await context.bot.get_chat_administrators(
            chat.id
        )

        for member in administrators:
            members.append(
                member.user.id
            )

        top = get_group_top(
            members,
            TOP_LIMIT,
        )

    except Exception:

        top = []

    text = (
        f"🏆 <b>{chat.title}</b>\n"
        f"👥 Group Top\n\n"
    )

    if not top:

        text += "Ranking data မရှိသေးပါ။"

    else:

        for index, row in enumerate(
            top,
            start=1,
        ):

            name = (
                f"@{row['username']}"
                if row["username"]
                else row["first_name"]
            )

            text += (
                f"<b>{index}.</b> "
                f"{name} — "
                f"🎴 {row['card_count']}\n"
            )

    await update.effective_message.reply_text(
        text,
        parse_mode="HTML",
    )


# ============================================================
# FAVORITE
# ============================================================

async def fav_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    register_user(update)

    if not context.args:

        await update.effective_message.reply_text(
            "Usage: /fav [character_id]"
        )

        return

    char_id = context.args[0]

    if not get_card(char_id):

        await update.effective_message.reply_text(
            "❌ Card မတွေ့ပါ။"
        )

        return

    add_favorite(
        update.effective_user.id,
        char_id,
    )

    await update.effective_message.reply_text(
        f"⭐ <code>{char_id}</code> ကို Favorite လုပ်ပြီးပါပြီ။",
        parse_mode="HTML",
    )


async def unfav_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    register_user(update)

    if not context.args:

        await update.effective_message.reply_text(
            "Usage: /unfav [character_id]"
        )

        return

    char_id = context.args[0]

    remove_favorite(
        update.effective_user.id,
        char_id,
    )

    await update.effective_message.reply_text(
        "💔 Favorite ဖြုတ်ပြီးပါပြီ။"
    )


# ============================================================
# CLAIM
# ============================================================

async def claim_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    register_user(update)

    if not await check_group_access(
        update,
        context,
    ):
        return

    user_id = update.effective_user.id

    user = get_user(user_id)

    if not user:

        await update.effective_message.reply_text(
            "❌ User registration error."
        )

        return

    now = time.time()

    last_claim = user["last_claim"] or 0

    # 12-hour cooldown
    if now - last_claim < CLAIM_COOLDOWN_HOURS * 3600:

        remaining = int(
            CLAIM_COOLDOWN_HOURS * 3600
            - (now - last_claim)
        )

        hours = remaining // 3600
        minutes = (remaining % 3600) // 60

        await update.effective_message.reply_text(
            f"⏳ Claim cooldown\n\n"
            f"နောက်ထပ် <b>{hours}h {minutes}m</b> ကြာမှ "
            f"ပြန် Claim လုပ်နိုင်ပါမယ်။",
            parse_mode="HTML",
        )

        return

    # 24h max 2 cards
    count = user["claim_count_24h"] or 0

    if count >= CLAIM_LIMIT_24H:

        await update.effective_message.reply_text(
            "🎴 24 နာရီအတွင်း Card 2 ကဒ် ရပြီးပါပြီ။\n\n"
            "နောက်နေ့မှ ပြန် Claim လုပ်ပါ။"
        )

        return

    cards = get_all_cards()

    if not cards:

        await update.effective_message.reply_text(
            "❌ Card database ထဲမှာ Card မရှိသေးပါ။"
        )

        return

    card = random.choices(
        cards,
        weights=[
            max(0.01, float(c["drop_weight"]))
            for c in cards
        ],
        k=1,
    )[0]

    add_user_card(
        user_id,
        card["char_id"],
    )

    with __import__("database").get_db() as db:

        new_count = count + 1

        db.execute(
            """
            UPDATE users
            SET last_claim = ?,
                claim_count_24h = ?
            WHERE user_id = ?
            """,
            (
                now,
                new_count,
                user_id,
            ),
        )

    await send_card_message(
        update.effective_message,
        card,
        prefix="🎉 <b>Card Claimed!</b>\n\n",
    )


# ============================================================
# SEND CARD
# ============================================================

async def send_card_message(
    message,
    card,
    prefix="",
):

    text = (
        f"{prefix}"
        f"🎴 <b>{card['name']}</b>\n"
        f"🆔 <code>{card['char_id']}</code>\n"
        f"✨ {card['edition']}\n"
        f"⭐ Rarity: {card['rarity']}\n"
        f"💰 Price: {card['price']:,} Coins\n"
    )

    if card["description"]:
        text += (
            f"\n📝 {card['description']}"
        )

    if (
        card["media_type"] == "video"
        and card["video_file_id"]
    ):

        await message.reply_video(
            video=card["video_file_id"],
            caption=text,
            parse_mode="HTML",
        )

    elif card["image_file_id"]:

        await message.reply_photo(
            photo=card["image_file_id"],
            caption=text,
            parse_mode="HTML",
        )

    else:

        await message.reply_text(
            text,
            parse_mode="HTML",
        )


# ============================================================
# HMODE
# ============================================================

async def hmode_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    register_user(update)

    cards = get_user_cards(
        update.effective_user.id
    )

    if not cards:

        await update.effective_message.reply_text(
            "🎴 Harem မရှိသေးပါ။"
        )

        return

    text = "🎴 <b>HMODE</b>\n\n"

    for index, card in enumerate(
        cards[:HMODE_LIMIT],
        start=1,
    ):

        text += (
            f"{index}. {card['name']} "
            f"— {card['edition']}\n"
        )

    text += (
        "\nအောက်က Card ကို ရွေးပါ။"
    )

    buttons = []

    for card in cards[:HMODE_LIMIT]:

        buttons.append([
            InlineKeyboardButton(
                card["name"][:30],
                callback_data=(
                    f"hmode:{card['char_id']}"
                ),
            )
        ])

    await update.effective_message.reply_text(
        text,
        reply_markup=InlineKeyboardMarkup(buttons),
        parse_mode="HTML",
    )


# ============================================================
# HMODE CALLBACK
# ============================================================

async def hmode_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    query = update.callback_query
    await query.answer()

    if not query.data.startswith("hmode:"):
        return

    char_id = query.data.split(
        ":",
        1
    )[1]

    with __import__("database").get_db() as db:

        db.execute(
            """
            INSERT INTO settings(key, value)
            VALUES (?, ?)
            ON CONFLICT(key)
            DO UPDATE SET value = excluded.value
            """,
            (
                f"hmode_{query.from_user.id}",
                char_id,
            ),
        )

    await query.edit_message_text(
        f"✅ HMODE Card သတ်မှတ်ပြီးပါပြီ။\n\n"
        f"🎴 <code>{char_id}</code>",
        parse_mode="HTML",
    )


# ============================================================
# RESET
# ============================================================

async def reset_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    register_user(update)

    user_id = update.effective_user.id

    set_setting(
        f"hmode_{user_id}",
        "",
    )

    await update.effective_message.reply_text(
        "🔄 Harem display setting ကို Reset လုပ်ပြီးပါပြီ။"
    )


# ============================================================
# SELL PRICE
# ============================================================

async def sellprice_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    register_user(update)

    text = "💰 <b>CARD SELL PRICE</b>\n\n"

    price_map = {
        "Common": 500,
        "Uncommon": 1000,
        "Rare": 2000,
        "Super Rare": 3500,
        "Epic": 5000,
        "Legendary": 7000,
        "Mythic": 8500,
        "Divine": 10000,
        "Celestial": 11500,
        "Eternal": 12500,
        "Ultimate": 13500,
        "Exclusive": 14500,
        "Premium": PREMIUM_PRICE,
    }

    for edition in EDITIONS:

        price = price_map.get(
            edition,
            500,
        )

        text += (
            f"✨ {edition} — "
            f"<b>{price:,}</b> Coins\n"
        )

    await update.effective_message.reply_text(
        text,
        parse_mode="HTML",
    )


# ============================================================
# CALLBACK ROUTER
# ============================================================

async def callback_router(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    query = update.callback_query

    data = query.data or ""

    if data in (
        "help",
        "help_my",
        "help_en",
    ):

        await help_callback(
            update,
            context,
        )

        return

    if data == "start":

        await query.answer()

        await query.edit_message_text(
            START_TEXT_MY,
            parse_mode="HTML",
        )

        return

    if data.startswith("harem:"):

        await harem_callback(
            update,
            context,
        )

        return

    if data.startswith("hmode:"):

        await hmode_callback(
            update,
            context,
        )

        return

    await query.answer()


# ============================================================
# UNKNOWN COMMAND
# ============================================================

async def unknown_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    await update.effective_message.reply_text(
        "❓ Unknown command.\n\n"
        "/help ကို အသုံးပြုပြီး Commands ကြည့်ပါ။"
    )


# ============================================================
# ERROR HANDLER
# ============================================================

async def error_handler(
    update: object,
    context: ContextTypes.DEFAULT_TYPE,
):

    logger.exception(
        "Unhandled exception:",
        exc_info=context.error,
    )


# ============================================================
# MAIN
# ============================================================

def main():

    if not BOT_TOKEN:

        raise RuntimeError(
            "BOT_TOKEN မထည့်ရသေးပါ။ "
            "Render Environment Variables ထဲမှာ "
            "BOT_TOKEN ထည့်ပါ။"
        )

    application = (
        Application.builder()
        .token(BOT_TOKEN)
        .build()
    )

    # Basic commands
    application.add_handler(
        CommandHandler(
            "start",
            start_command,
        )
    )

    application.add_handler(
        CommandHandler(
            "help",
            help_command,
        )
    )

    application.add_handler(
        CommandHandler(
            "balance",
            balance_command,
        )
    )

    application.add_handler(
        CommandHandler(
            "daily",
            daily_command,
        )
    )

    application.add_handler(
        CommandHandler(
            "profile",
            profile_command,
        )
    )

    application.add_handler(
        CommandHandler(
            "harem",
            harem_command,
        )
    )

    application.add_handler(
        CommandHandler(
            "search",
            search_command,
        )
    )

    application.add_handler(
        CommandHandler(
            "check",
            check_command,
        )
    )

    application.add_handler(
        CommandHandler(
            "top",
            top_command,
        )
    )

    application.add_handler(
        CommandHandler(
            "rankings",
            rankings_command,
        )
    )

    application.add_handler(
        CommandHandler(
            "ctop",
            ctop_command,
        )
    )

    application.add_handler(
        CommandHandler(
            "fav",
            fav_command,
        )
    )

    application.add_handler(
        CommandHandler(
            "unfav",
            unfav_command,
        )
    )

    application.add_handler(
        CommandHandler(
            "claim",
            claim_command,
        )
    )

    application.add_handler(
        CommandHandler(
            "hmode",
            hmode_command,
        )
    )

    application.add_handler(
        CommandHandler(
            "reset",
            reset_command,
        )
    )

    application.add_handler(
        CommandHandler(
            "sellprice",
            sellprice_command,
        )
    )

    # Callback buttons
    application.add_handler(
        CallbackQueryHandler(
            callback_router
        )
    )

    # Unknown commands
    application.add_handler(
        MessageHandler(
            filters.COMMAND,
            unknown_command,
        )
    )

    # Error handler
    application.add_error_handler(
        error_handler
    )

    logger.info(
        "%s %s started.",
        BOT_NAME,
        BOT_VERSION,
    )

    application.run_polling(
        allowed_updates=Update.ALL_TYPES
    )


if __name__ == "__main__":
    main()
