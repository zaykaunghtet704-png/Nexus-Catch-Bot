import time
from datetime import datetime, timezone

from telegram import Update
from telegram.ext import ContextTypes

from database import (
    get_db,
    get_balance,
    get_card,
    get_user_cards,
)


# ============================================================
# CONFIG
# ============================================================

DAILY_REWARD = 500
DAILY_COOLDOWN = 24 * 60 * 60

MAX_MARKET_PRICE = 1_000_000_000
MIN_MARKET_PRICE = 1


# ============================================================
# DATABASE INITIALIZATION
# ============================================================

def init_economy_db():

    with get_db() as db:

        db.execute(
            """
            CREATE TABLE IF NOT EXISTS daily_claims (
                user_id INTEGER PRIMARY KEY,
                last_claim REAL NOT NULL DEFAULT 0
            )
            """
        )

        db.execute(
            """
            CREATE TABLE IF NOT EXISTS market_listings (
                listing_id INTEGER PRIMARY KEY AUTOINCREMENT,
                seller_id INTEGER NOT NULL,
                char_id TEXT NOT NULL,
                price INTEGER NOT NULL,
                created_at REAL NOT NULL,
                status TEXT NOT NULL DEFAULT 'active'
            )
            """
        )


init_economy_db()


# ============================================================
# HELPERS
# ============================================================

def add_coins(
    user_id,
    amount,
):

    with get_db() as db:

        db.execute(
            """
            INSERT INTO users (
                user_id,
                coins
            )
            VALUES (?, ?)

            ON CONFLICT(user_id)
            DO UPDATE SET
                coins = coins + excluded.coins
            """,
            (
                user_id,
                amount,
            ),
        )


def remove_coins(
    user_id,
    amount,
):

    with get_db() as db:

        row = db.execute(
            """
            SELECT coins
            FROM users
            WHERE user_id = ?
            """,
            (user_id,),
        ).fetchone()

        if not row:
            return False

        current = int(
            row["coins"] or 0
        )

        if current < amount:
            return False

        db.execute(
            """
            UPDATE users
            SET coins = coins - ?
            WHERE user_id = ?
            """,
            (
                amount,
                user_id,
            ),
        )

        return True


def card_owned_by_user(
    user_id,
    char_id,
):

    cards = get_user_cards(
        user_id
    )

    for card in cards:

        if str(card["char_id"]) == str(char_id):

            return True

    return False


def get_card_sale_price(
    card,
):

    edition = str(
        card["edition"]
    ).lower()

    rarity = str(
        card["rarity"]
    ).lower()

    # Premium = highest price
    if "premium" in edition:

        return 15_000

    # Higher editions
    if "legend" in edition:

        return 12_000

    if "mythic" in edition:

        return 10_000

    if "epic" in edition:

        return 8_000

    if "rare" in edition:

        return 5_000

    # Rarity fallback
    if "legend" in rarity:

        return 12_000

    if "mythic" in rarity:

        return 10_000

    if "epic" in rarity:

        return 8_000

    if "rare" in rarity:

        return 5_000

    return 1_000


def get_listing(
    listing_id,
):

    with get_db() as db:

        return db.execute(
            """
            SELECT *
            FROM market_listings
            WHERE listing_id = ?
              AND status = 'active'
            """,
            (listing_id,),
        ).fetchone()


# ============================================================
# DAILY
# ============================================================

async def daily_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    message = update.effective_message
    user = update.effective_user

    if not message or not user:
        return

    now = time.time()

    with get_db() as db:

        row = db.execute(
            """
            SELECT last_claim
            FROM daily_claims
            WHERE user_id = ?
            """,
            (user.id,),
        ).fetchone()

        last_claim = (
            float(row["last_claim"])
            if row
            else 0
        )

        elapsed = now - last_claim

        if elapsed < DAILY_COOLDOWN:

            remaining = int(
                DAILY_COOLDOWN - elapsed
            )

            hours = remaining // 3600
            minutes = (
                remaining % 3600
            ) // 60

            await message.reply_text(
                "⏳ <b>DAILY COOLDOWN</b>\n\n"
                "ဒီနေ့ Reward ယူပြီးပါပြီ။\n\n"
                f"🕐 ပြန်ယူနိုင်ရန် "
                f"<b>{hours}h {minutes}m</b> ကျန်ပါသေးတယ်။",
                parse_mode="HTML",
            )

            return

        db.execute(
            """
            INSERT INTO daily_claims (
                user_id,
                last_claim
            )
            VALUES (?, ?)

            ON CONFLICT(user_id)
            DO UPDATE SET
                last_claim = excluded.last_claim
            """,
            (
                user.id,
                now,
            ),
        )

        add_coins(
            user.id,
            DAILY_REWARD,
        )

    balance = get_balance(
        user.id
    )

    await message.reply_text(
        "🎁 <b>DAILY REWARD</b>\n\n"
        f"🪙 +{DAILY_REWARD:,} Coins ရရှိပါပြီ!\n\n"
        f"💰 Balance: <b>{balance:,}</b> Coins\n\n"
        "⏳ နောက်တစ်ကြိမ် 24 နာရီအကြာမှာ ပြန်ယူနိုင်ပါတယ်။",
        parse_mode="HTML",
    )


# ============================================================
# BALANCE
# ============================================================

async def balance_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    message = update.effective_message
    user = update.effective_user

    if not message or not user:
        return

    balance = get_balance(
        user.id
    )

    await message.reply_text(
        "💰 <b>NEXUS WALLET</b>\n\n"
        f"👤 {user.first_name}\n"
        f"🆔 <code>{user.id}</code>\n\n"
        f"🪙 Coins: <b>{balance:,}</b>",
        parse_mode="HTML",
    )


# ============================================================
# SELL PRICE
# ============================================================

async def sellprice_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    message = update.effective_message

    if not message:
        return

    cards = []

    try:

        from database import get_all_cards

        cards = get_all_cards()

    except Exception:

        cards = []

    if not cards:

        await message.reply_text(
            "💰 Sell Price data မရှိသေးပါ။",
            parse_mode="HTML",
        )

        return

    text = (
        "💰 <b>NEXUS SELL PRICE</b>\n\n"
        "🎴 Edition အလိုက် သတ်မှတ်ထားသော "
        "အခြေခံရောင်းဈေးများ\n\n"
    )

    editions = {}

    for card in cards:

        edition = str(
            card["edition"]
        )

        if edition not in editions:

            editions[edition] = (
                get_card_sale_price(
                    card
                )
            )

    for edition, price in editions.items():

        text += (
            f"✨ <b>{edition}</b>"
            f" → 🪙 {price:,}\n"
        )

    text += (
        "\n💎 <b>Premium Edition</b>"
        " → 🪙 15,000 Coins"
    )

    await message.reply_text(
        text,
        parse_mode="HTML",
    )


# ============================================================
# SELL
# ============================================================

async def sell_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    message = update.effective_message
    user = update.effective_user

    if not message or not user:
        return

    if len(context.args) != 2:

        await message.reply_text(
            "💸 <b>SELL CARD</b>\n\n"
            "Usage:\n"
            "<code>/sell [char_id] [price]</code>\n\n"
            "Example:\n"
            "<code>/sell 0021 5000</code>",
            parse_mode="HTML",
        )

        return

    char_id = context.args[0]

    try:

        price = int(
            context.args[1]
        )

    except ValueError:

        await message.reply_text(
            "❌ Price က နံပါတ်ဖြစ်ရပါမယ်။",
            parse_mode="HTML",
        )

        return

    if price < MIN_MARKET_PRICE:

        await message.reply_text(
            f"❌ အနည်းဆုံး Price က "
            f"{MIN_MARKET_PRICE:,} Coins ဖြစ်ရပါမယ်။"
        )

        return

    if price > MAX_MARKET_PRICE:

        await message.reply_text(
            "❌ Price အရမ်းမြင့်နေပါတယ်။"
        )

        return

    card = get_card(
        char_id
    )

    if not card:

        await message.reply_text(
            "❌ Card ID မတွေ့ပါ။"
        )

        return

    if not card_owned_by_user(
        user.id,
        char_id,
    ):

        await message.reply_text(
            "❌ ဒီ Card ကို မင်းမပိုင်ပါ။"
        )

        return

    # Prevent duplicate active listing
    with get_db() as db:

        existing = db.execute(
            """
            SELECT listing_id
            FROM market_listings
            WHERE seller_id = ?
              AND char_id = ?
              AND status = 'active'
            """,
            (
                user.id,
                char_id,
            ),
        ).fetchone()

        if existing:

            await message.reply_text(
                "⚠️ ဒီ Card ကို Market မှာ "
                "တင်ထားပြီးသားပါ။"
            )

            return

        cursor = db.execute(
            """
            INSERT INTO market_listings (
                seller_id,
                char_id,
                price,
                created_at,
                status
            )
            VALUES (?, ?, ?, ?, 'active')
            """,
            (
                user.id,
                char_id,
                price,
                time.time(),
            ),
        )

        listing_id = cursor.lastrowid

    await message.reply_text(
        "🛒 <b>CARD LISTED</b>\n\n"
        f"🎴 {card['name']}\n"
        f"🆔 <code>{char_id}</code>\n"
        f"💰 Price: <b>{price:,}</b> Coins\n"
        f"🔖 Listing ID: <code>{listing_id}</code>\n\n"
        f"🛍 ဝယ်ချင်ရင်:\n"
        f"<code>/buy {listing_id}</code>",
        parse_mode="HTML",
    )


# ============================================================
# MARKET
# ============================================================

async def market_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    message = update.effective_message

    if not message:
        return

    with get_db() as db:

        listings = db.execute(
            """
            SELECT *
            FROM market_listings
            WHERE status = 'active'
            ORDER BY listing_id DESC
            LIMIT 20
            """
        ).fetchall()

    if not listings:

        await message.reply_text(
            "🛒 <b>NEXUS MARKET</b>\n\n"
            "📭 Market မှာ Card တင်ထားတာ မရှိသေးပါ။",
            parse_mode="HTML",
        )

        return

    text = (
        "🛒 <b>NEXUS MARKET</b>\n\n"
    )

    for listing in listings:

        card = get_card(
            listing["char_id"]
        )

        if not card:
            continue

        text += (
            f"🎴 <b>{card['name']}</b>\n"
            f"🆔 Card ID: <code>{card['char_id']}</code>\n"
            f"💰 Price: <b>{listing['price']:,}</b> Coins\n"
            f"🔖 Listing ID: <code>{listing['listing_id']}</code>\n"
            f"👤 Seller: <code>{listing['seller_id']}</code>\n\n"
        )

    text += (
        "🛍 ဝယ်ရန်:\n"
        "<code>/buy [listing_id]</code>\n\n"
        "💡 ကိုယ့် Card ရောင်းရန်:\n"
        "<code>/sell [char_id] [price]</code>"
    )

    await message.reply_text(
        text,
        parse_mode="HTML",
    )


# ============================================================
# BUY
# ============================================================

async def buy_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    message = update.effective_message
    buyer = update.effective_user

    if not message or not buyer:
        return

    if len(context.args) != 1:

        await message.reply_text(
            "🛍 <b>BUY CARD</b>\n\n"
            "Usage:\n"
            "<code>/buy [listing_id]</code>",
            parse_mode="HTML",
        )

        return

    try:

        listing_id = int(
            context.args[0]
        )

    except ValueError:

        await message.reply_text(
            "❌ Listing ID မှားနေပါတယ်။"
        )

        return

    with get_db() as db:

        listing = db.execute(
            """
            SELECT *
            FROM market_listings
            WHERE listing_id = ?
              AND status = 'active'
            """,
            (listing_id,),
        ).fetchone()

        if not listing:

            await message.reply_text(
                "❌ ဒီ Listing မရှိတော့ပါ။"
            )

            return

        seller_id = listing["seller_id"]
        char_id = listing["char_id"]
        price = int(
            listing["price"]
        )

        if seller_id == buyer.id:

            await message.reply_text(
                "❌ ကိုယ့် Listing ကို "
                "ကိုယ်ပြန်ဝယ်လို့မရပါ။"
            )

            return

        card = get_card(
            char_id
        )

        if not card:

            await message.reply_text(
                "❌ Card မတွေ့ပါ။"
            )

            return

        balance = get_balance(
            buyer.id
        )

        if balance < price:

            await message.reply_text(
                "❌ Coin မလုံလောက်ပါ။\n\n"
                f"💰 Your Balance: {balance:,}\n"
                f"💸 Required: {price:,}"
            )

            return

        if not card_owned_by_user(
            seller_id,
            char_id,
        ):

            db.execute(
                """
                UPDATE market_listings
                SET status = 'cancelled'
                WHERE listing_id = ?
                """,
                (listing_id,),
            )

            await message.reply_text(
                "❌ Seller မှာ ဒီ Card မရှိတော့ပါ။"
            )

            return

        # Money transfer
        db.execute(
            """
            UPDATE users
            SET coins = coins - ?
            WHERE user_id = ?
            """,
            (
                price,
                buyer.id,
            ),
        )

        db.execute(
            """
            UPDATE users
            SET coins = coins + ?
            WHERE user_id = ?
            """,
            (
                price,
                seller_id,
            ),
        )

        # Transfer card ownership
        db.execute(
            """
            UPDATE user_cards
            SET user_id = ?
            WHERE user_id = ?
              AND char_id = ?
            """,
            (
                buyer.id,
                seller_id,
                char_id,
            ),
        )

        db.execute(
            """
            UPDATE market_listings
            SET status = 'sold'
            WHERE listing_id = ?
            """,
            (listing_id,),
        )

    new_balance = get_balance(
        buyer.id
    )

    await message.reply_text(
        "✅ <b>CARD PURCHASED!</b>\n\n"
        f"🎴 {card['name']}\n"
        f"🆔 <code>{char_id}</code>\n"
        f"💰 Paid: <b>{price:,}</b> Coins\n"
        f"💳 Balance: <b>{new_balance:,}</b> Coins\n\n"
        "🎴 Card ကို မင်းရဲ့ Harem ထဲ ထည့်ပြီးပါပြီ။",
        parse_mode="HTML",
    )


# ============================================================
# DELIST
# ============================================================

async def delist_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    message = update.effective_message
    user = update.effective_user

    if not message or not user:
        return

    if len(context.args) != 1:

        await message.reply_text(
            "❌ Usage:\n"
            "<code>/delist [listing_id]</code>",
            parse_mode="HTML",
        )

        return

    try:

        listing_id = int(
            context.args[0]
        )

    except ValueError:

        await message.reply_text(
            "❌ Listing ID မှားနေပါတယ်။"
        )

        return

    with get_db() as db:

        listing = db.execute(
            """
            SELECT *
            FROM market_listings
            WHERE listing_id = ?
              AND status = 'active'
            """,
            (listing_id,),
        ).fetchone()

        if not listing:

            await message.reply_text(
                "❌ Listing မတွေ့ပါ။"
            )

            return

        if listing["seller_id"] != user.id:

            await message.reply_text(
                "🚫 ဒီ Listing ကို မင်းမပိုင်ပါ။"
            )

            return

        db.execute(
            """
            UPDATE market_listings
            SET status = 'cancelled'
            WHERE listing_id = ?
            """,
            (listing_id,),
        )

    await message.reply_text(
        "✅ <b>DELISTED</b>\n\n"
        f"🔖 Listing ID: <code>{listing_id}</code>\n"
        "🛒 Market ကနေ ဖယ်ရှားပြီးပါပြီ။",
        parse_mode="HTML",
    )


# ============================================================
# GIFT
# ============================================================

async def gift_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    message = update.effective_message
    sender = update.effective_user

    if not message or not sender:
        return

    if len(context.args) != 1:

        await message.reply_text(
            "🎁 <b>GIFT CARD</b>\n\n"
            "Usage:\n"
            "<code>/gift [char_id]</code>\n\n"
            "📌 User ကို Reply လုပ်ပြီး command သုံးပါ။",
            parse_mode="HTML",
        )

        return

    if not message.reply_to_message:

        await message.reply_text(
            "🎁 Card ပေးမယ့် User ကို "
            "Reply လုပ်ပြီး <code>/gift CHAR_ID</code> "
            "သုံးပါ။",
            parse_mode="HTML",
        )

        return

    receiver = (
        message.reply_to_message.from_user
    )

    if not receiver:

        await message.reply_text(
            "❌ Receiver ကို မသိနိုင်ပါ။"
        )

        return

    if receiver.id == sender.id:

        await message.reply_text(
            "❌ ကိုယ့်ကိုယ်ကို Gift ပေးလို့မရပါ။"
        )

        return

    char_id = context.args[0]

    card = get_card(
        char_id
    )

    if not card:

        await message.reply_text(
            "❌ Card ID မတွေ့ပါ။"
        )

        return

    if not card_owned_by_user(
        sender.id,
        char_id,
    ):

        await message.reply_text(
            "❌ ဒီ Card ကို မင်းမပိုင်ပါ။"
        )

        return

    with get_db() as db:

        db.execute(
            """
            UPDATE user_cards
            SET user_id = ?
            WHERE user_id = ?
              AND char_id = ?
            """,
            (
                receiver.id,
                sender.id,
                char_id,
            ),
        )

    await message.reply_text(
        "🎁 <b>CARD GIFTED!</b>\n\n"
        f"🎴 {card['name']}\n"
        f"🆔 <code>{char_id}</code>\n\n"
        f"👤 From: <b>{sender.first_name}</b>\n"
        f"🎁 To: <b>{receiver.first_name}</b>",
        parse_mode="HTML",
    )


# ============================================================
# TRADE
# ============================================================

async def trade_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    message = update.effective_message
    user = update.effective_user

    if not message or not user:
        return

    if len(context.args) != 2:

        await message.reply_text(
            "🔄 <b>TRADE</b>\n\n"
            "User နှစ်ယောက် Card ID တွေကို "
            "သတ်မှတ်ပေးပြီး Trade လုပ်ပါ။\n\n"
            "Usage:\n"
            "<code>/trade YOUR_ID THEIR_ID</code>\n\n"
            "📌 Trade လုပ်မယ့် User ကို Reply လုပ်ပြီး "
            "command သုံးနိုင်ပါတယ်။",
            parse_mode="HTML",
        )

        return

    if not message.reply_to_message:

        await message.reply_text(
            "🔄 Trade လုပ်မယ့် User ကို "
            "Reply လုပ်ပါ။",
            parse_mode="HTML",
        )

        return

    other_user = (
        message.reply_to_message.from_user
    )

    if not other_user:

        await message.reply_text(
            "❌ Other user မတွေ့ပါ။"
        )

        return

    if other_user.id == user.id:

        await message.reply_text(
            "❌ ကိုယ့်ကိုယ်ကို Trade မလုပ်နိုင်ပါ။"
        )

        return

    your_card = context.args[0]
    their_card = context.args[1]

    if not get_card(your_card):

        await message.reply_text(
            "❌ YOUR_ID Card မတွေ့ပါ။"
        )

        return

    if not get_card(their_card):

        await message.reply_text(
            "❌ THEIR_ID Card မတွေ့ပါ။"
        )

        return

    if not card_owned_by_user(
        user.id,
        your_card,
    ):

        await message.reply_text(
            "❌ ပထမ Card ကို မင်းမပိုင်ပါ။"
        )

        return

    if not card_owned_by_user(
        other_user.id,
        their_card,
    ):

        await message.reply_text(
            "❌ ဒုတိယ Card ကို သူမပိုင်ပါ။"
        )

        return

    with get_db() as db:

        db.execute(
            """
            UPDATE user_cards
            SET user_id = ?
            WHERE user_id = ?
              AND char_id = ?
            """,
            (
                other_user.id,
                user.id,
                your_card,
            ),
        )

        db.execute(
            """
            UPDATE user_cards
            SET user_id = ?
            WHERE user_id = ?
              AND char_id = ?
            """,
            (
                user.id,
                other_user.id,
                their_card,
            ),
        )

    your_card_data = get_card(
        your_card
    )

    their_card_data = get_card(
        their_card
    )

    await message.reply_text(
        "🔄 <b>TRADE COMPLETE!</b>\n\n"
        f"👤 {user.first_name}\n"
        f"🎴 {your_card_data['name']} → "
        f"{other_user.first_name}\n\n"
        f"👤 {other_user.first_name}\n"
        f"🎴 {their_card_data['name']} → "
        f"{user.first_name}",
        parse_mode="HTML",
    )
