import logging
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
    ChatMemberHandler,
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
    get_balance,
    add_coins,
    remove_coins,
    get_card,
    get_all_cards,
    search_cards,
    add_user_card,
    get_user_cards,
    count_user_cards,
    add_favorite,
    remove_favorite,
    get_global_top,
    get_group_top,
    get_setting,
    set_setting,
    is_admin,
    add_admin,
    remove_admin,
    save_group,
    approve_group,
    reject_group,
    is_group_enabled,
    add_card,
    delete_card,
    update_card_price,
    get_db,
)

# ============================================================
# MODULES
# ============================================================

from drops import (
    create_drop,
    claim_drop_callback,
)

from harem_system import (
    harem_command,
    harem_callback,
    reset_command,
)

from profile_system import (
    profile_command,
    profile_callback,
)

from search import (
    search_command,
    search_callback,
)

from market import (
    sell_command as market_sell_command,
    market_command,
    buy_command as market_buy_command,
    delist_command,
    market_callback,
)

from economy import (
    daily_command,
    balance_command,
    sellprice_command,
    gift_command,
    trade_command,
)


# ============================================================
# LOGGING
# ============================================================

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.INFO,
)

logger = logging.getLogger("nexus-card-bot")


# ============================================================
# DATABASE
# ============================================================

init_db()


# ============================================================
# USER REGISTER
# ============================================================

def register_user(update):

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
# PERMISSION
# ============================================================

def is_owner(user_id):

    return int(user_id) == int(OWNER_ID)


def is_staff(user_id):

    return (
        is_owner(user_id)
        or is_admin(user_id)
    )


async def owner_guard(update):

    user = update.effective_user

    if user and is_owner(user.id):
        return True

    await update.effective_message.reply_text(
        "👑 <b>Owner Only</b>\n\n"
        "ဒီ Command ကို Bot Owner ပဲ အသုံးပြုနိုင်ပါတယ်။",
        parse_mode="HTML",
    )

    return False


async def admin_guard(update):

    user = update.effective_user

    if user and is_staff(user.id):
        return True

    await update.effective_message.reply_text(
        "🛡️ <b>Admin Only</b>\n\n"
        "ဒီ Command ကို Admin / Owner ပဲ အသုံးပြုနိုင်ပါတယ်။",
        parse_mode="HTML",
    )

    return False


# ============================================================
# GROUP ACCESS
# ============================================================

async def check_group_access(
    update,
    context,
):

    chat = update.effective_chat
    user = update.effective_user

    if not chat:
        return True

    if chat.type == "private":
        return True

    if user and is_owner(user.id):
        return True

    # --------------------------------------------------------
    # BOT ADMIN CHECK
    # --------------------------------------------------------

    bot_is_admin = False

    try:

        me = await context.bot.get_me()

        member = await context.bot.get_chat_member(
            chat.id,
            me.id,
        )

        bot_is_admin = member.status in (
            "administrator",
            "creator",
        )

    except Exception:

        bot_is_admin = False

    # --------------------------------------------------------
    # MEMBER COUNT
    # --------------------------------------------------------

    try:

        member_count = (
            await context.bot.get_chat_member_count(
                chat.id
            )
        )

    except Exception:

        member_count = 0

    # --------------------------------------------------------
    # SAVE GROUP
    # --------------------------------------------------------

    save_group(
        chat.id,
        chat.title or "",
        member_count,
        int(bot_is_admin),
        user.id if user else 0,
    )

    # --------------------------------------------------------
    # BOT ADMIN REQUIRED
    # --------------------------------------------------------

    if (
        REQUIRE_BOT_ADMIN
        and not bot_is_admin
    ):

        await update.effective_message.reply_text(
            "🤖 <b>Bot Admin လိုအပ်ပါတယ်။</b>\n\n"
            "Bot ကို Group Admin ပေးပြီး "
            "ပြန်အသုံးပြုပါ။",
            parse_mode="HTML",
        )

        return False

    # --------------------------------------------------------
    # MINIMUM MEMBERS
    # --------------------------------------------------------

    if member_count < MIN_GROUP_MEMBERS:

        await update.effective_message.reply_text(
            f"👥 Group မှာ Member အနည်းဆုံး "
            f"<b>{MIN_GROUP_MEMBERS}</b> ယောက်ရှိရပါမယ်။\n\n"
            f"လက်ရှိ Member — <b>{member_count}</b>",
            parse_mode="HTML",
        )

        return False

    # --------------------------------------------------------
    # OWNER APPROVAL
    # --------------------------------------------------------

    if (
        REQUIRE_OWNER_APPROVAL
        and not is_group_enabled(chat.id)
    ):

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

START_TEXT_MY = f"""
🎴 <b>{BOT_NAME}</b>

✨ Nexus Card Collection Bot

🎴 Card Collection
🪙 Coin Economy
🛒 Card Market
🏆 Global Rankings
⚔️ Duel System
🎁 Daily Rewards
⭐ Favorites

🧩 Version: <b>{BOT_VERSION}</b>

အောက်က Button တွေကနေ စတင်အသုံးပြုနိုင်ပါတယ်။ 💎
"""


START_TEXT_EN = f"""
🎴 <b>{BOT_NAME}</b>

✨ Nexus Card Collection Bot

🎴 Card Collection
🪙 Coin Economy
🛒 Card Market
🏆 Global Rankings
⚔️ Duel System
🎁 Daily Rewards
⭐ Favorites

🧩 Version: <b>{BOT_VERSION}</b>

Use the buttons below to get started.
"""


async def start_command(
    update,
    context,
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
                callback_data="help:0",
            )
        ],

    ]

    await update.effective_message.reply_text(
        START_TEXT_MY,
        reply_markup=InlineKeyboardMarkup(
            keyboard
        ),
        parse_mode="HTML",
    )


# ============================================================
# HELP
# ============================================================

HELP_PAGES = [

"""
📚 <b>NEXUS COMMAND GUIDE — 1/4</b>

🎴 <b>Basic</b>

/start — Bot စတင်ရန်
/help — Command Guide
/profile — User Profile
/harem — Card Collection
/search [name/id] — Card ရှာရန်
/check [id] — Card ကြည့်ရန်
/balance — Coin လက်ကျန်
/daily — နေ့စဉ် 500 Coins

🏆 <b>Ranking</b>

/top — Global Top 15
/ctop — Group Top
/rankings — Global Ranking
/todayNexusCatch — ဒီနေ့ Card ရထားသူများ
""",

"""
📚 <b>NEXUS COMMAND GUIDE — 2/4</b>

🎴 <b>Card</b>

/claim — 12 Hours Cooldown
/Nexus [Card Name] — Card Search
/fav [id] — Favorite
/unfav [id] — Favorite ဖြုတ်
/hmode — Harem Mode
/reset — Harem Reset
/upgrade [id] — Card Upgrade

🛒 <b>Market</b>

/market
/sell [char_id] [price]
/buy [listing_id]
/delist [listing_id]
/sellprice
""",

"""
📚 <b>NEXUS COMMAND GUIDE — 3/4</b>

🤝 <b>Social</b>

/gift [char_id]
/trade YOUR_ID THEIR_ID
/duel

📌 Trade / Gift မှာ
Target User ရဲ့ message ကို Reply လုပ်ပြီး
Command သုံးပါ။

🌐 <b>Group Rules</b>

• Bot ကို Group Admin ပေးထားရမယ်
• Member 50 ယောက် အနည်းဆုံးရှိရမယ်
• Owner Approval လိုအပ်တယ်
• Group / Channel Join Requirement ရှိတယ်
""",

"""
📚 <b>NEXUS COMMAND GUIDE — 4/4</b>

👑 <b>Owner / Admin</b>

/drop
/addcard
/deletecard
/givecard
/takecard
/givecoin
/takecoin
/setprice
/setdrop
/setadmin
/deladmin
/approve
/reject
/stats
/maintenance
/changetime
/broadcast

🎴 Card Edition — 13 Levels
💎 Premium Edition = Highest
🪙 Premium Sell Price = 15,000 Coins
"""
]


def help_keyboard(page):

    buttons = []

    navigation = []

    if page > 0:

        navigation.append(
            InlineKeyboardButton(
                "⬅️",
                callback_data=f"help:{page - 1}",
            )
        )

    navigation.append(
        InlineKeyboardButton(
            f"📄 {page + 1}/{len(HELP_PAGES)}",
            callback_data="help:no",
        )
    )

    if page < len(HELP_PAGES) - 1:

        navigation.append(
            InlineKeyboardButton(
                "➡️",
                callback_data=f"help:{page + 1}",
            )
        )

    buttons.append(navigation)

    buttons.append([
        InlineKeyboardButton(
            "🇲🇲 Myanmar",
            callback_data="lang:my",
        ),

        InlineKeyboardButton(
            "🇬🇧 English",
            callback_data="lang:en",
        ),
    ])

    return InlineKeyboardMarkup(buttons)


async def help_command(
    update,
    context,
):

    register_user(update)

    await update.effective_message.reply_text(
        HELP_PAGES[0],
        reply_markup=help_keyboard(0),
        parse_mode="HTML",
    )


# ============================================================
# CHECK CARD
# ============================================================

async def check_command(
    update,
    context,
):

    register_user(update)

    if not context.args:

        await update.effective_message.reply_text(
            "🎴 Usage:\n"
            "<code>/check [card_id]</code>",
            parse_mode="HTML",
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
        f"💰 Price: <b>{int(card['price'] or 0):,}</b>\n"
        f"📝 {card['description'] or 'No description'}"
    )

    if (
        card["media_type"] == "video"
        and card["video_file_id"]
    ):

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
# NEXUS SEARCH ALIAS
# ============================================================

async def nexus_command(
    update,
    context,
):

    await search_command(
        update,
        context,
    )


# ============================================================
# GLOBAL TOP
# ============================================================

async def top_command(
    update,
    context,
):

    register_user(update)

    rows = get_global_top(
        TOP_LIMIT
    )

    if not rows:

        await update.effective_message.reply_text(
            "🏆 Ranking data မရှိသေးပါ။"
        )

        return

    text = (
        "🏆 <b>NEXUS GLOBAL TOP 15</b>\n\n"
    )

    for index, row in enumerate(
        rows[:TOP_LIMIT],
        start=1,
    ):

        medal = {
            1: "🥇",
            2: "🥈",
            3: "🥉",
        }.get(
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
# GROUP TOP
# ============================================================

async def ctop_command(
    update,
    context,
):

    register_user(update)

    if not await check_group_access(
        update,
        context,
    ):

        return

    chat = update.effective_chat

    try:

        administrators = (
            await context.bot.get_chat_administrators(
                chat.id
            )
        )

        member_ids = [
            x.user.id
            for x in administrators
        ]

        rows = get_group_top(
            member_ids,
            TOP_LIMIT,
        )

    except Exception:

        rows = []

    text = (
        f"👥 <b>{chat.title or 'GROUP'} TOP</b>\n\n"
    )

    if not rows:

        text += "📭 Ranking data မရှိသေးပါ။"

    else:

        for index, row in enumerate(
            rows,
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
# TODAY NEXUS CATCH
# ============================================================

async def today_nexus_catch_command(
    update,
    context,
):

    register_user(update)

    cutoff = (
        time.time()
        - 86400
    )

    with get_db() as db:

        rows = db.execute(
            """
            SELECT
                user_id,
                COUNT(*) AS total
            FROM user_cards
            WHERE obtained_at >= ?
            GROUP BY user_id
            ORDER BY total DESC
            LIMIT ?
            """,
            (
                cutoff,
                TOP_LIMIT,
            ),
        ).fetchall()

    text = (
        "⚡ <b>TODAY NEXUS CATCH</b>\n\n"
    )

    if not rows:

        text += (
            "📭 ဒီနေ့ Card ရထားသူ "
            "မရှိသေးပါ။"
        )

    else:

        for index, row in enumerate(
            rows,
            start=1,
        ):

            user = get_user(
                row["user_id"]
            )

            if user:

                name = (
                    f"@{user['username']}"
                    if user["username"]
                    else user["first_name"]
                )

            else:

                name = str(
                    row["user_id"]
                )

            text += (
                f"<b>{index}.</b> "
                f"{name} — "
                f"🎴 {row['total']}\n"
            )

    await update.effective_message.reply_text(
        text,
        parse_mode="HTML",
    )


# ============================================================
# RANKINGS ALIAS
# ============================================================

async def rankings_command(
    update,
    context,
):

    await top_command(
        update,
        context,
    )


# ============================================================
# FAVORITE
# ============================================================

async def fav_command(
    update,
    context,
):

    register_user(update)

    if not context.args:

        await update.effective_message.reply_text(
            "Usage: <code>/fav [character_id]</code>",
            parse_mode="HTML",
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
        f"⭐ <code>{char_id}</code> ကို "
        "Favorite လုပ်ပြီးပါပြီ။",
        parse_mode="HTML",
    )


async def unfav_command(
    update,
    context,
):

    register_user(update)

    if not context.args:

        await update.effective_message.reply_text(
            "Usage: <code>/unfav [character_id]</code>",
            parse_mode="HTML",
        )

        return

    remove_favorite(
        update.effective_user.id,
        context.args[0],
    )

    await update.effective_message.reply_text(
        "💔 Favorite ဖြုတ်ပြီးပါပြီ။"
    )


# ============================================================
# CLAIM
# ============================================================

async def claim_command(
    update,
    context,
):

    register_user(update)

    if not await check_group_access(
        update,
        context,
    ):

        return

    user_id = (
        update.effective_user.id
    )

    user = get_user(
        user_id
    )

    if not user:
        return

    now = time.time()

    last_claim = float(
        user["last_claim"] or 0
    )

    claim_count = int(
        user["claim_count_24h"] or 0
    )

    # Reset 24h counter
    if now - last_claim >= 86400:

        claim_count = 0

    if claim_count >= CLAIM_LIMIT_24H:

        await update.effective_message.reply_text(
            "🎴 24 နာရီအတွင်း Card "
            "2 ကဒ် ရပြီးပါပြီ။\n\n"
            "နောက်နေ့မှ ပြန် Claim လုပ်ပါ။"
        )

        return

    if (
        now - last_claim
        < CLAIM_COOLDOWN_HOURS * 3600
    ):

        remaining = int(
            CLAIM_COOLDOWN_HOURS * 3600
            - (now - last_claim)
        )

        hours = remaining // 3600

        minutes = (
            remaining % 3600
        ) // 60

        await update.effective_message.reply_text(
            f"⏳ Claim Cooldown\n\n"
            f"နောက်ထပ် <b>{hours}h "
            f"{minutes}m</b> ကြာမှ "
            f"ပြန် Claim လုပ်နိုင်ပါတယ်။",
            parse_mode="HTML",
        )

        return

    cards = get_all_cards()

    if not cards:

        await update.effective_message.reply_text(
            "❌ Card database ထဲမှာ "
            "Card မရှိသေးပါ။"
        )

        return

    card = random.choices(
        cards,
        weights=[
            max(
                0.01,
                float(
                    c["drop_weight"] or 1
                ),
            )
            for c in cards
        ],
        k=1,
    )[0]

    add_user_card(
        user_id,
        card["char_id"],
    )

    with get_db() as db:

        db.execute(
            """
            UPDATE users
            SET last_claim = ?,
                claim_count_24h = ?
            WHERE user_id = ?
            """,
            (
                now,
                claim_count + 1,
                user_id,
            ),
        )

    await send_card_message(
        update.effective_message,
        card,
        "🎉 <b>CARD CLAIMED!</b>\n\n",
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
        prefix
        + f"🎴 <b>{card['name']}</b>\n"
        + f"🆔 <code>{card['char_id']}</code>\n"
        + f"✨ {card['edition']}\n"
        + f"⭐ Rarity: {card['rarity']}\n"
        + f"💰 {int(card['price'] or 0):,} Coins\n"
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
            card["video_file_id"],
            caption=text,
            parse_mode="HTML",
        )

    elif card["image_file_id"]:

        await message.reply_photo(
            card["image_file_id"],
            caption=text,
            parse_mode="HTML",
        )

    else:

        await message.reply_text(
            text,
            parse_mode="HTML",
        )


# ============================================================
# DROP
# ============================================================

async def drop_command(
    update,
    context,
):

    register_user(update)

    if not is_staff(
        update.effective_user.id
    ):

        await update.effective_message.reply_text(
            "👑 Owner/Admin ပဲ "
            "/drop အသုံးပြုနိုင်ပါတယ်။"
        )

        return

    if not await check_group_access(
        update,
        context,
    ):

        return

    await create_drop(
        update.effective_message,
        context,
    )


# ============================================================
# HMODE
# ============================================================

async def hmode_command(
    update,
    context,
):

    from harem_system import (
        hmode_command as real_hmode_command
    )

    await real_hmode_command(
        update,
        context,
    )


# ============================================================
# UPGRADE
# ============================================================

async def upgrade_command(
    update,
    context,
):

    register_user(update)

    if not context.args:

        await update.effective_message.reply_text(
            "⬆️ Usage:\n"
            "<code>/upgrade [card_id]</code>",
            parse_mode="HTML",
        )

        return

    char_id = context.args[0]

    user_id = (
        update.effective_user.id
    )

    with get_db() as db:

        row = db.execute(
            """
            SELECT *
            FROM user_cards
            WHERE user_id = ?
              AND char_id = ?
            LIMIT 1
            """,
            (
                user_id,
                char_id,
            ),
        ).fetchone()

    if not row:

        await update.effective_message.reply_text(
            "❌ ဒီ Card ကို မင်းမပိုင်ပါ။"
        )

        return

    level = int(
        row["level"] or 1
    )

    cost = (
        level * 250
    )

    if (
        get_balance(user_id)
        < cost
    ):

        await update.effective_message.reply_text(
            f"🪙 Coin မလုံလောက်ပါ။\n\n"
            f"Upgrade Cost: "
            f"<b>{cost:,}</b>",
            parse_mode="HTML",
        )

        return

    remove_coins(
        user_id,
        cost,
    )

    with get_db() as db:

        db.execute(
            """
            UPDATE user_cards
            SET level = ?,
                exp = 0
            WHERE id = ?
            """,
            (
                level + 1,
                row["id"],
            ),
        )

    await update.effective_message.reply_text(
        f"⬆️ <b>UPGRADE SUCCESS</b>\n\n"
        f"🎴 Card: <code>{char_id}</code>\n"
        f"⭐ Lv.{level} → Lv.{level + 1}\n"
        f"🪙 Cost: {cost:,}",
        parse_mode="HTML",
    )


# ============================================================
# TARGET USER
# ============================================================

def get_target_user_id(
    update,
    context,
):

    if context.args:

        try:

            return int(
                context.args[0]
            )

        except ValueError:

            pass

    message = (
        update.effective_message
    )

    if message.reply_to_message:

        user = (
            message.reply_to_message
            .from_user
        )

        if user:

            return user.id

    return None


# ============================================================
# GIVE COIN
# ============================================================

async def givecoin_command(
    update,
    context,
):

    if not await admin_guard(update):
        return

    target = get_target_user_id(
        update,
        context,
    )

    if (
        not target
        or len(context.args) < 2
    ):

        await update.effective_message.reply_text(
            "Usage:\n"
            "<code>/givecoin USER_ID AMOUNT</code>",
            parse_mode="HTML",
        )

        return

    try:

        amount = int(
            context.args[1]
        )

    except ValueError:

        await update.effective_message.reply_text(
            "❌ Amount မှားနေပါတယ်။"
        )

        return

    if amount <= 0:

        await update.effective_message.reply_text(
            "❌ Amount က 0 ထက်ကြီးရပါမယ်။"
        )

        return

    add_or_update_user(
        target
    )

    add_coins(
        target,
        amount,
    )

    await update.effective_message.reply_text(
        f"🪙 <b>+{amount:,} Coins</b>\n\n"
        f"👤 User ID: <code>{target}</code>",
        parse_mode="HTML",
    )


# ============================================================
# TAKE COIN
# ============================================================

async def takecoin_command(
    update,
    context,
):

    if not await admin_guard(update):
        return

    target = get_target_user_id(
        update,
        context,
    )

    if (
        not target
        or len(context.args) < 2
    ):

        await update.effective_message.reply_text(
            "Usage:\n"
            "<code>/takecoin USER_ID AMOUNT</code>",
            parse_mode="HTML",
        )

        return

    try:

        amount = int(
            context.args[1]
        )

    except ValueError:

        await update.effective_message.reply_text(
            "❌ Amount မှားနေပါတယ်။"
        )

        return

    remove_coins(
        target,
        max(0, amount),
    )

    await update.effective_message.reply_text(
        "✅ Coins ဖြုတ်ပြီးပါပြီ။"
    )


# ============================================================
# GIVE CARD
# ============================================================

async def givecard_command(
    update,
    context,
):

    if not await admin_guard(update):
        return

    target = get_target_user_id(
        update,
        context,
    )

    if (
        not target
        or len(context.args) < 2
    ):

        await update.effective_message.reply_text(
            "Usage:\n"
            "<code>/givecard USER_ID CARD_ID</code>",
            parse_mode="HTML",
        )

        return

    char_id = context.args[1]

    card = get_card(
        char_id
    )

    if not card:

        await update.effective_message.reply_text(
            "❌ Card မတွေ့ပါ။"
        )

        return

    add_or_update_user(
        target
    )

    add_user_card(
        target,
        char_id,
    )

    await update.effective_message.reply_text(
        f"🎁 Card ပေးပြီးပါပြီ။\n\n"
        f"🎴 {card['name']}\n"
        f"🆔 <code>{char_id}</code>\n"
        f"👤 <code>{target}</code>",
        parse_mode="HTML",
    )


# ============================================================
# TAKE CARD
# ============================================================

async def takecard_command(
    update,
    context,
):

    if not await admin_guard(update):
        return

    target = get_target_user_id(
        update,
        context,
    )

    if (
        not target
        or len(context.args) < 2
    ):

        await update.effective_message.reply_text(
            "Usage:\n"
            "<code>/takecard USER_ID CARD_ID</code>",
            parse_mode="HTML",
        )

        return

    char_id = context.args[1]

    with get_db() as db:

        row = db.execute(
            """
            SELECT id
            FROM user_cards
            WHERE user_id = ?
              AND char_id = ?
            LIMIT 1
            """,
            (
                target,
                char_id,
            ),
        ).fetchone()

        if row:

            db.execute(
                """
                DELETE FROM user_cards
                WHERE id = ?
                """,
                (
                    row["id"],
                ),
            )

    await update.effective_message.reply_text(
        "✅ User Card ဖြုတ်ပြီးပါပြီ။"
    )


# ============================================================
# ADD CARD
# ============================================================

async def addcard_command(
    update,
    context,
):

    if not await admin_guard(update):
        return

    if len(context.args) < 2:

        await update.effective_message.reply_text(
            "🎴 <b>ADD CARD</b>\n\n"
            "Usage:\n"
            "<code>/addcard "
            "CARD_ID | NAME | EDITION | "
            "RARITY | PRICE | DROP_WEIGHT</code>\n\n"
            "Photo/Video ကို Reply လုပ်ပြီး "
            "ဒီ Command သုံးနိုင်ပါတယ်။",
            parse_mode="HTML",
        )

        return

    raw = " ".join(
        context.args
    )

    parts = [
        x.strip()
        for x in raw.split("|")
    ]

    char_id = parts[0]

    name = parts[1]

    edition = (
        parts[2]
        if len(parts) > 2
        and parts[2]
        else "Common"
    )

    try:

        rarity = int(
            parts[3]
        ) if len(parts) > 3 else 1

    except ValueError:

        rarity = 1

    try:

        price = int(
            parts[4]
        ) if len(parts) > 4 else 0

    except ValueError:

        price = 0

    try:

        drop_weight = float(
            parts[5]
        ) if len(parts) > 5 else 1

    except ValueError:

        drop_weight = 1

    image_file_id = ""

    video_file_id = ""

    media_type = "photo"

    reply = (
        update.effective_message
        .reply_to_message
    )

    if reply:

        if reply.photo:

            image_file_id = (
                reply.photo[-1].file_id
            )

        elif reply.video:

            video_file_id = (
                reply.video.file_id
            )

            media_type = "video"

    try:

        add_card(
            char_id,
            name,
            edition,
            rarity,
            price,
            image_file_id,
            video_file_id,
            media_type,
            "",
            drop_weight,
            0,
        )

    except Exception as exc:

        await update.effective_message.reply_text(
            "❌ Card ထည့်မရပါ။\n\n"
            f"<code>{str(exc)[:300]}</code>",
            parse_mode="HTML",
        )

        return

    await update.effective_message.reply_text(
        f"✅ <b>CARD ADDED</b>\n\n"
        f"🎴 {name}\n"
        f"🆔 <code>{char_id}</code>\n"
        f"✨ {edition}\n"
        f"⭐ Rarity: {rarity}\n"
        f"💰 Price: {price:,}",
        parse_mode="HTML",
    )


# ============================================================
# DELETE CARD
# ============================================================

async def deletecard_command(
    update,
    context,
):

    if not await admin_guard(update):
        return

    if not context.args:

        await update.effective_message.reply_text(
            "Usage: /deletecard CARD_ID"
        )

        return

    delete_card(
        context.args[0]
    )

    await update.effective_message.reply_text(
        "🗑️ Card ဖျက်ပြီးပါပြီ။"
    )


# ============================================================
# SET PRICE
# ============================================================

async def setprice_command(
    update,
    context,
):

    if not await admin_guard(update):
        return

    if len(context.args) != 2:

        await update.effective_message.reply_text(
            "Usage: /setprice CARD_ID PRICE"
        )

        return

    try:

        price = int(
            context.args[1]
        )

    except ValueError:

        await update.effective_message.reply_text(
            "❌ Price မှားနေပါတယ်။"
        )

        return

    update_card_price(
        context.args[0],
        price,
    )

    await update.effective_message.reply_text(
        f"✅ Price = <b>{price:,}</b> Coins",
        parse_mode="HTML",
    )


# ============================================================
# SET DROP
# ============================================================

async def setdrop_command(
    update,
    context,
):

    if not await admin_guard(update):
        return

    if not context.args:

        await update.effective_message.reply_text(
            "Usage: /setdrop COUNT"
        )

        return

    try:

        count = int(
            context.args[0]
        )

    except ValueError:

        await update.effective_message.reply_text(
            "❌ Count မှားနေပါတယ်။"
        )

        return

    set_setting(
        "drop_count",
        max(1, count),
    )

    await update.effective_message.reply_text(
        f"🎴 Drop Count = <b>{count}</b>",
        parse_mode="HTML",
    )


# ============================================================
# SET ADMIN
# ============================================================

async def setadmin_command(
    update,
    context,
):

    if not await owner_guard(update):
        return

    target = get_target_user_id(
        update,
        context,
    )

    if not target:

        await update.effective_message.reply_text(
            "Usage: /setadmin USER_ID"
        )

        return

    add_admin(
        target,
        update.effective_user.id,
    )

    await update.effective_message.reply_text(
        f"🛡️ <code>{target}</code> ကို "
        "Admin ခန့်ပြီးပါပြီ။",
        parse_mode="HTML",
    )


# ============================================================
# DELETE ADMIN
# ============================================================

async def deladmin_command(
    update,
    context,
):

    if not await owner_guard(update):
        return

    target = get_target_user_id(
        update,
        context,
    )

    if not target:

        await update.effective_message.reply_text(
            "Usage: /deladmin USER_ID"
        )

        return

    remove_admin(
        target
    )

    await update.effective_message.reply_text(
        "✅ Admin ဖြုတ်ပြီးပါပြီ။"
    )


# ============================================================
# APPROVE GROUP
# ============================================================

async def approve_command(
    update,
    context,
):

    if not await owner_guard(update):
        return

    if not context.args:

        await update.effective_message.reply_text(
            "Usage: /approve GROUP_ID"
        )

        return

    try:

        group_id = int(
            context.args[0]
        )

    except ValueError:

        await update.effective_message.reply_text(
            "❌ Group ID မှားနေပါတယ်။"
        )

        return

    approve_group(
        group_id
    )

    await update.effective_message.reply_text(
        f"✅ Group <code>{group_id}</code> "
        "Approved.",
        parse_mode="HTML",
    )


# ============================================================
# REJECT GROUP
# ============================================================

async def reject_command(
    update,
    context,
):

    if not await owner_guard(update):
        return

    if not context.args:

        await update.effective_message.reply_text(
            "Usage: /reject GROUP_ID"
        )

        return

    try:

        group_id = int(
            context.args[0]
        )

    except ValueError:

        await update.effective_message.reply_text(
            "❌ Group ID မှားနေပါတယ်။"
        )

        return

    reject_group(
        group_id
    )

    await update.effective_message.reply_text(
        f"⛔ Group <code>{group_id}</code> "
        "Disabled.",
        parse_mode="HTML",
    )


# ============================================================
# STATS
# ============================================================

async def stats_command(
    update,
    context,
):

    if not await owner_guard(update):
        return

    with get_db() as db:

        users = db.execute(
            "SELECT COUNT(*) c FROM users"
        ).fetchone()["c"]

        cards = db.execute(
            """
            SELECT COUNT(*) c
            FROM cards
            WHERE active = 1
            """
        ).fetchone()["c"]

        owned = db.execute(
            """
            SELECT COUNT(*) c
            FROM user_cards
            """
        ).fetchone()["c"]

        groups = db.execute(
            """
            SELECT COUNT(*) c
            FROM groups
            """
        ).fetchone()["c"]

    await update.effective_message.reply_text(
        f"📊 <b>NEXUS BOT STATS</b>\n\n"
        f"👤 Users: <b>{users:,}</b>\n"
        f"🎴 Cards: <b>{cards:,}</b>\n"
        f"📦 Owned Cards: <b>{owned:,}</b>\n"
        f"👥 Groups: <b>{groups:,}</b>",
        parse_mode="HTML",
    )


# ============================================================
# MAINTENANCE
# ============================================================

async def maintenance_command(
    update,
    context,
):

    if not await owner_guard(update):
        return

    current = (
        get_setting(
            "maintenance",
            "0",
        )
        == "1"
    )

    new_value = (
        "0"
        if current
        else "1"
    )

    set_setting(
        "maintenance",
        new_value,
    )

    await update.effective_message.reply_text(
        "🔧 Maintenance: "
        f"<b>{'ON' if new_value == '1' else 'OFF'}</b>",
        parse_mode="HTML",
    )


# ============================================================
# CHANGE TIME / DROP COUNT
# ============================================================

async def changetime_command(
    update,
    context,
):

    if not await owner_guard(update):
        return

    if not context.args:

        current = get_setting(
            "drop_count",
            "85",
        )

        await update.effective_message.reply_text(
            f"⚙️ Current Drop Count: "
            f"<b>{current}</b>\n\n"
            "Usage: /changetime COUNT",
            parse_mode="HTML",
        )

        return

    try:

        count = int(
            context.args[0]
        )

    except ValueError:

        await update.effective_message.reply_text(
            "❌ Count မှားနေပါတယ်။"
        )

        return

    set_setting(
        "drop_count",
        max(1, count),
    )

    await update.effective_message.reply_text(
        "✅ Drop setting updated."
    )


# ============================================================
# BROADCAST
# ============================================================

async def broadcast_command(
    update,
    context,
):

    if not await owner_guard(update):
        return

    if not context.args:

        await update.effective_message.reply_text(
            "Usage: /broadcast MESSAGE"
        )

        return

    text = " ".join(
        context.args
    )

    with get_db() as db:

        users = db.execute(
            """
            SELECT user_id
            FROM users
            """
        ).fetchall()

    success = 0

    for row in users:

        try:

            await context.bot.send_message(
                row["user_id"],
                text,
                parse_mode="HTML",
            )

            success += 1

        except Exception:

            pass

    await update.effective_message.reply_text(
        f"📢 Broadcast Complete\n\n"
        f"✅ Sent: <b>{success}</b>",
        parse_mode="HTML",
    )


# ============================================================
# DUEL
# ============================================================

async def duel_command(
    update,
    context,
):

    register_user(update)

    message = (
        update.effective_message
    )

    user = (
        update.effective_user
    )

    if not message.reply_to_message:

        await message.reply_text(
            "⚔️ Duel လုပ်မယ့် User ရဲ့ "
            "message ကို Reply လုပ်ပြီး "
            "/duel သုံးပါ။"
        )

        return

    target = (
        message
        .reply_to_message
        .from_user
    )

    if (
        not target
        or target.id == user.id
        or target.is_bot
    ):

        await message.reply_text(
            "❌ Target User မမှန်ပါ။"
        )

        return

    my_cards = get_user_cards(
        user.id
    )

    their_cards = get_user_cards(
        target.id
    )

    if (
        not my_cards
        or not their_cards
    ):

        await message.reply_text(
            "🎴 နှစ်ဖက်လုံးမှာ Card "
            "ရှိရပါမယ်။"
        )

        return

    my_card = random.choice(
        my_cards
    )

    their_card = random.choice(
        their_cards
    )

    my_score = (
        int(my_card["level"] or 1)
        + int(my_card["exp"] or 0)
    )

    their_score = (
        int(their_card["level"] or 1)
        + int(their_card["exp"] or 0)
    )

    if my_score >= their_score:

        winner = user

    else:

        winner = target

    reward = random.randint(
        50,
        500,
    )

    add_coins(
        winner.id,
        reward,
    )

    await message.reply_text(
        f"⚔️ <b>DUEL RESULT</b>\n\n"
        f"🎴 {user.first_name}: "
        f"{my_card['name']} "
        f"(Lv.{my_card['level']})\n\n"
        f"🎴 {target.first_name}: "
        f"{their_card['name']} "
        f"(Lv.{their_card['level']})\n\n"
        f"🏆 Winner: "
        f"<b>{winner.first_name}</b>\n"
        f"🪙 Reward: "
        f"<b>+{reward}</b> Coins",
        parse_mode="HTML",
    )


# ============================================================
# BOT ADDED TO GROUP
# ============================================================

async def bot_install_handler(
    update,
    context,
):

    change = (
        update.my_chat_member
    )

    if not change:
        return

    chat = change.chat

    new_status = (
        change
        .new_chat_member
        .status
    )

    old_status = (
        change
        .old_chat_member
        .status
    )

    if (
        new_status
        not in (
            "member",
            "administrator",
        )
    ):

        return

    if (
        old_status
        not in (
            "left",
            "kicked",
        )
    ):

        return

    added_by = change.from_user

    try:

        member_count = (
            await context.bot
            .get_chat_member_count(
                chat.id
            )
        )

    except Exception:

        member_count = 0

    try:

        me = (
            await context.bot.get_me()
        )

        bot_member = (
            await context.bot
            .get_chat_member(
                chat.id,
                me.id,
            )
        )

        bot_admin = (
            bot_member.status
            in (
                "administrator",
                "creator",
            )
        )

    except Exception:

        bot_admin = False

    save_group(
        chat.id,
        chat.title or "",
        member_count,
        int(bot_admin),
        added_by.id if added_by else 0,
    )

    # --------------------------------------------------------
    # SEND LOG TO CHANNEL
    # --------------------------------------------------------

    if CHANNEL_ID:

        text = (
            "🚀 <b>NEXUS BOT ADDED</b>\n\n"
            f"👥 Group: <b>{chat.title or 'Unknown'}</b>\n"
            f"🆔 Group ID: <code>{chat.id}</code>\n\n"
            f"👤 Added By: "
            f"<b>{added_by.first_name if added_by else 'Unknown'}</b>\n"
            f"🆔 User ID: "
            f"<code>{added_by.id if added_by else 0}</code>\n\n"
            f"👥 Members: "
            f"<b>{member_count}</b>\n"
            f"🤖 Bot Admin: "
            f"<b>{'YES' if bot_admin else 'NO'}</b>\n\n"
            "🔐 Status: "
            "<b>WAITING FOR OWNER APPROVAL</b>"
        )

        try:

            await context.bot.send_message(
                CHANNEL_ID,
                text,
                parse_mode="HTML",
            )

        except Exception as exc:

            logger.warning(
                "Channel log failed: %s",
                exc,
            )


# ============================================================
# CALLBACK ROUTER
# ============================================================

async def callback_router(
    update,
    context,
):

    query = (
        update.callback_query
    )

    data = (
        query.data or ""
    )

    # --------------------------------------------------------
    # DROP
    # --------------------------------------------------------

    if data.startswith("drop:"):

        await claim_drop_callback(
            update,
            context,
        )

        return

    # --------------------------------------------------------
    # HAREM
    # --------------------------------------------------------

    if (
        data.startswith("harem_")
        or data.startswith("hmode_set:")
        or data == "harem_noop"
    ):

        await harem_callback(
            update,
            context,
        )

        return

    # --------------------------------------------------------
    # PROFILE
    # --------------------------------------------------------

    if data.startswith("profile_"):

        await profile_callback(
            update,
            context,
        )

        return

    # --------------------------------------------------------
    # SEARCH
    # --------------------------------------------------------

    if data.startswith("search_"):

        await search_callback(
            update,
            context,
        )

        return

    # --------------------------------------------------------
    # MARKET
    # --------------------------------------------------------

    if data.startswith("market"):

        await market_callback(
            update,
            context,
        )

        return

    # --------------------------------------------------------
    # HELP
    # --------------------------------------------------------

    if data.startswith("help:"):

        await query.answer()

        value = data.split(
            ":",
            1,
        )[1]

        if value == "no":
            return

        page = int(value)

        await query.edit_message_text(
            HELP_PAGES[page],
            reply_markup=help_keyboard(
                page
            ),
            parse_mode="HTML",
        )

        return

    # --------------------------------------------------------
    # LANGUAGE
    # --------------------------------------------------------

    if data == "lang:my":

        await query.answer()

        await query.edit_message_text(
            HELP_PAGES[0],
            reply_markup=help_keyboard(0),
            parse_mode="HTML",
        )

        return

    if data == "lang:en":

        await query.answer()

        await query.edit_message_text(
            """
📚 <b>NEXUS CARD COMMAND GUIDE</b>

🎴 <b>Basic</b>

/start
/help
/profile
/harem
/search
/check
/balance
/daily

🏆 <b>Ranking</b>

/top
/ctop
/rankings
/todayNexusCatch

🛒 <b>Market</b>

/market
/sell
/buy
/delist
/sellprice

🎁 <b>Card</b>

/claim
/fav
/unfav
/hmode
/reset
/upgrade
""",
            reply_markup=help_keyboard(0),
            parse_mode="HTML",
        )

        return

    await query.answer()


# ============================================================
# UNKNOWN COMMAND
# ============================================================

async def unknown_command(
    update,
    context,
):

    if update.effective_message:

        await update.effective_message.reply_text(
            "❓ Unknown Command\n\n"
            "📚 အသုံးပြုနိုင်တဲ့ Command တွေကို "
            "/help မှာကြည့်ပါ။"
        )


# ============================================================
# ERROR HANDLER
# ============================================================

async def error_handler(
    update,
    context,
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
            "Render Environment Variables ကို စစ်ပါ။"
        )

    application = (
        Application
        .builder()
        .token(BOT_TOKEN)
        .build()
    )

    # ========================================================
    # USER COMMANDS
    # ========================================================

    commands = {

        "start": start_command,

        "help": help_command,

        "profile": profile_command,

        "harem": harem_command,

        "search": search_command,

        "Nexus": nexus_command,

        "check": check_command,

        "top": top_command,

        "ctop": ctop_command,

        "rankings": rankings_command,

        "todayNexusCatch":
            today_nexus_catch_command,

        "balance": balance_command,

        "daily": daily_command,

        "sellprice": sellprice_command,

        "claim": claim_command,

        "fav": fav_command,

        "unfav": unfav_command,

        "hmode": hmode_command,

        "reset": reset_command,

        "upgrade": upgrade_command,

        "drop": drop_command,

        "market": market_command,

        "sell": market_sell_command,

        "buy": market_buy_command,

        "delist": delist_command,

        "gift": gift_command,

        "trade": trade_command,

        "duel": duel_command,

        # ----------------------------------------------------
        # OWNER / ADMIN
        # ----------------------------------------------------

        "addcard":
            addcard_command,

        "deletecard":
            deletecard_command,

        "delcard":
            deletecard_command,

        "givecard":
            givecard_command,

        "takecard":
            takecard_command,

        "givecoin":
            givecoin_command,

        "givecoins":
            givecoin_command,

        "takecoin":
            takecoin_command,

        "setprice":
            setprice_command,

        "setdrop":
            setdrop_command,

        "setadmin":
            setadmin_command,

        "deladmin":
            deladmin_command,

        "approve":
            approve_command,

        "reject":
            reject_command,

        "stats":
            stats_command,

        "maintenance":
            maintenance_command,

        "changetime":
            changetime_command,

        "broadcast":
            broadcast_command,
    }

    for command, handler in commands.items():

        application.add_handler(
            CommandHandler(
                command,
                handler,
            )
        )

    # ========================================================
    # CALLBACKS
    # ========================================================

    application.add_handler(
        CallbackQueryHandler(
            callback_router
        )
    )

    # ========================================================
    # BOT ADDED / REMOVED FROM GROUP
    # ========================================================

    application.add_handler(
        ChatMemberHandler(
            bot_install_handler,
            ChatMemberHandler.MY_CHAT_MEMBER,
        )
    )

    # ========================================================
    # UNKNOWN COMMAND
    # ========================================================

    application.add_handler(
        MessageHandler(
            filters.COMMAND,
            unknown_command,
        )
    )

    # ========================================================
    # ERROR
    # ========================================================

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


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":

    main()
