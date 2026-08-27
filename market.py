import math
import time

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import ContextTypes

from database import (
    get_db,
    get_balance,
    add_coins,
    remove_coins,
    get_card,
    get_user_cards,
    add_user_card,
)


# ============================================================
# MARKET CONFIG
# ============================================================

MARKET_PER_PAGE = 8

MIN_SELL_PRICE = 1
MAX_SELL_PRICE = 1_000_000_000


# ============================================================
# MARKET DATABASE
# ============================================================

def init_market_db():
    """
    Creates marketplace table if it doesn't already exist.
    """

    with get_db() as db:

        db.execute(
            """
            CREATE TABLE IF NOT EXISTS market_listings (
                listing_id INTEGER PRIMARY KEY AUTOINCREMENT,

                seller_id INTEGER NOT NULL,

                char_id TEXT NOT NULL,

                price INTEGER NOT NULL,

                created_at REAL NOT NULL,

                status TEXT NOT NULL DEFAULT 'active',

                buyer_id INTEGER DEFAULT 0,

                sold_at REAL DEFAULT 0
            )
            """
        )

        db.execute(
            """
            CREATE INDEX IF NOT EXISTS
            idx_market_status
            ON market_listings(status)
            """
        )


# Initialize market database
init_market_db()


# ============================================================
# HELPERS
# ============================================================

def get_active_listings():

    with get_db() as db:

        return db.execute(
            """
            SELECT *
            FROM market_listings
            WHERE status = 'active'
            ORDER BY listing_id DESC
            """
        ).fetchall()


def get_listing(listing_id):

    with get_db() as db:

        return db.execute(
            """
            SELECT *
            FROM market_listings
            WHERE listing_id = ?
            """,
            (listing_id,),
        ).fetchone()


def user_owns_card(user_id, char_id):

    cards = get_user_cards(user_id)

    for card in cards:

        if str(card["char_id"]) == str(char_id):
            return True

    return False


# ============================================================
# SELL
# ============================================================

async def sell_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    user = update.effective_user

    if not user:
        return

    if len(context.args) != 2:

        await update.effective_message.reply_text(
            "🛒 <b>Sell Usage</b>\n\n"
            "<code>/sell [char_id] [price]</code>\n\n"
            "Example:\n"
            "<code>/sell 0021 5000</code>",
            parse_mode="HTML",
        )

        return

    char_id = context.args[0]

    try:
        price = int(context.args[1])

    except ValueError:

        await update.effective_message.reply_text(
            "❌ Price က နံပါတ်ဖြစ်ရပါမယ်။"
        )

        return

    # Price validation
    if price < MIN_SELL_PRICE:

        await update.effective_message.reply_text(
            f"❌ အနည်းဆုံးစျေးက "
            f"{MIN_SELL_PRICE:,} Coins ပါ။"
        )

        return

    if price > MAX_SELL_PRICE:

        await update.effective_message.reply_text(
            f"❌ အများဆုံးစျေးက "
            f"{MAX_SELL_PRICE:,} Coins ပါ။"
        )

        return

    # Card existence
    card = get_card(char_id)

    if not card:

        await update.effective_message.reply_text(
            "❌ ဒီ Card ID မရှိပါ။"
        )

        return

    # Ownership
    if not user_owns_card(
        user.id,
        char_id,
    ):

        await update.effective_message.reply_text(
            "❌ ဒီ Card က မင်းပိုင် Card မဟုတ်ပါ။"
        )

        return

    # Already listed?
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

        await update.effective_message.reply_text(
            "⚠️ ဒီ Card ကို Market မှာ တင်ထားပြီးသားပါ။\n\n"
            f"Listing ID: <code>{existing['listing_id']}</code>",
            parse_mode="HTML",
        )

        return

    # Create listing
    with get_db() as db:

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

    await update.effective_message.reply_text(
        "🛒 <b>CARD LISTED!</b>\n\n"
        f"🎴 {card['name']}\n"
        f"🆔 Card ID: <code>{char_id}</code>\n"
        f"💰 Price: <b>{price:,}</b> Coins\n"
        f"🔖 Listing ID: <code>{listing_id}</code>\n\n"
        "Market မှာ ရောင်းရန်တင်ပြီးပါပြီ။",
        parse_mode="HTML",
    )


# ============================================================
# MARKET
# ============================================================

async def market_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    listings = get_active_listings()

    if not listings:

        await update.effective_message.reply_text(
            "🛒 <b>MARKET</b>\n\n"
            "လောလောဆယ် ရောင်းရန်တင်ထားတဲ့ Card မရှိသေးပါ။",
            parse_mode="HTML",
        )

        return

    page = 1

    if context.args:

        try:
            page = max(
                1,
                int(context.args[0]),
            )

        except ValueError:
            page = 1

    total_pages = max(
        1,
        math.ceil(
            len(listings) / MARKET_PER_PAGE
        ),
    )

    if page > total_pages:
        page = total_pages

    start = (
        (page - 1)
        * MARKET_PER_PAGE
    )

    end = (
        start
        + MARKET_PER_PAGE
    )

    page_listings = listings[start:end]

    text = (
        "🛒 <b>NEXUS MARKET</b>\n\n"
        f"📄 Page {page}/{total_pages}\n\n"
    )

    for listing in page_listings:

        card = get_card(
            listing["char_id"]
        )

        if not card:
            continue

        text += (
            f"🔖 <b>#{listing['listing_id']}</b>\n"
            f"🎴 {card['name']}\n"
            f"🆔 <code>{card['char_id']}</code>\n"
            f"✨ {card['edition']}\n"
            f"⭐ {card['rarity']}\n"
            f"💰 <b>{listing['price']:,}</b> Coins\n"
            f"👤 Seller: <code>{listing['seller_id']}</code>\n\n"
        )

    buttons = []

    navigation = []

    if page > 1:

        navigation.append(
            InlineKeyboardButton(
                "⬅️",
                callback_data=f"market:{page - 1}",
            )
        )

    if page < total_pages:

        navigation.append(
            InlineKeyboardButton(
                "➡️",
                callback_data=f"market:{page + 1}",
            )
        )

    if navigation:
        buttons.append(navigation)

    # Buy buttons
    for listing in page_listings:

        card = get_card(
            listing["char_id"]
        )

        if not card:
            continue

        buttons.append([
            InlineKeyboardButton(
                f"🛒 Buy #{listing['listing_id']}",
                callback_data=(
                    f"marketbuy:{listing['listing_id']}"
                ),
            )
        ])

    await update.effective_message.reply_text(
        text,
        reply_markup=InlineKeyboardMarkup(
            buttons
        ) if buttons else None,
        parse_mode="HTML",
    )


# ============================================================
# BUY
# ============================================================

async def buy_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    user = update.effective_user

    if not context.args:

        await update.effective_message.reply_text(
            "🛒 Usage:\n"
            "<code>/buy [listing_id]</code>\n\n"
            "Example:\n"
            "<code>/buy 15</code>",
            parse_mode="HTML",
        )

        return

    try:
        listing_id = int(
            context.args[0]
        )

    except ValueError:

        await update.effective_message.reply_text(
            "❌ Listing ID မှားနေပါတယ်။"
        )

        return

    success, result = purchase_listing(
        user.id,
        listing_id,
    )

    if not success:

        await update.effective_message.reply_text(
            result,
            parse_mode="HTML",
        )

        return

    card = get_card(
        result["char_id"]
    )

    await update.effective_message.reply_text(
        "🎉 <b>PURCHASE SUCCESSFUL!</b>\n\n"
        f"🎴 {card['name']}\n"
        f"🆔 <code>{card['char_id']}</code>\n"
        f"💰 Paid: <b>{result['price']:,}</b> Coins\n\n"
        f"👤 Buyer: <code>{user.id}</code>\n"
        f"🛒 Listing: <code>#{listing_id}</code>",
        parse_mode="HTML",
    )


# ============================================================
# PURCHASE ENGINE
# ============================================================

def purchase_listing(
    buyer_id,
    listing_id,
):

    with get_db() as db:

        # Get listing
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

            return (
                False,
                "❌ ဒီ Listing မရှိတော့ပါ။"
            )

        seller_id = listing["seller_id"]
        char_id = listing["char_id"]
        price = int(listing["price"])

        # Can't buy own listing
        if seller_id == buyer_id:

            return (
                False,
                "❌ ကိုယ့် Card ကို ကိုယ်ပြန်ဝယ်လို့ မရပါ။"
            )

        # Check buyer balance
        balance = get_balance(buyer_id)

        if balance < price:

            return (
                False,
                "💸 <b>Coin မလုံလောက်ပါ။</b>\n\n"
                f"လိုအပ်သည်: <b>{price:,}</b>\n"
                f"ရှိသည်: <b>{balance:,}</b>",
            )

        # Check seller still owns card
        if not user_owns_card(
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

            return (
                False,
                "❌ Seller ဆီမှာ ဒီ Card မရှိတော့ပါ။"
            )

        # Remove coins from buyer
        remove_coins(
            buyer_id,
            price,
        )

        # Give coins to seller
        add_coins(
            seller_id,
            price,
        )

        # Transfer ownership
        transfer_card(
            seller_id,
            buyer_id,
            char_id,
        )

        # Mark sold
        db.execute(
            """
            UPDATE market_listings
            SET status = 'sold',
                buyer_id = ?,
                sold_at = ?
            WHERE listing_id = ?
              AND status = 'active'
            """,
            (
                buyer_id,
                time.time(),
                listing_id,
            ),
        )

        return (
            True,
            {
                "char_id": char_id,
                "price": price,
                "seller_id": seller_id,
            },
        )


# ============================================================
# TRANSFER CARD
# ============================================================

def transfer_card(
    seller_id,
    buyer_id,
    char_id,
):

    with get_db() as db:

        # Find ownership row
        owner = db.execute(
            """
            SELECT *
            FROM user_cards
            WHERE user_id = ?
              AND char_id = ?
            LIMIT 1
            """,
            (
                seller_id,
                char_id,
            ),
        ).fetchone()

        if not owner:

            return False

        # Delete seller copy
        db.execute(
            """
            DELETE FROM user_cards
            WHERE id = ?
            """,
            (
                owner["id"],
            ),
        )

    # Add to buyer
    add_user_card(
        buyer_id,
        char_id,
    )

    return True


# ============================================================
# DELIST
# ============================================================

async def delist_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    user = update.effective_user

    if not context.args:

        await update.effective_message.reply_text(
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

        await update.effective_message.reply_text(
            "❌ Listing ID မှားနေပါတယ်။"
        )

        return

    listing = get_listing(
        listing_id
    )

    if not listing:

        await update.effective_message.reply_text(
            "❌ Listing မတွေ့ပါ။"
        )

        return

    if listing["status"] != "active":

        await update.effective_message.reply_text(
            "⚠️ ဒီ Listing က Active မဟုတ်တော့ပါ။"
        )

        return

    if listing["seller_id"] != user.id:

        await update.effective_message.reply_text(
            "🚫 ဒီ Listing က မင်းတင်ထားတာ မဟုတ်ပါ။"
        )

        return

    with get_db() as db:

        db.execute(
            """
            UPDATE market_listings
            SET status = 'cancelled'
            WHERE listing_id = ?
              AND seller_id = ?
              AND status = 'active'
            """,
            (
                listing_id,
                user.id,
            ),
        )

    await update.effective_message.reply_text(
        f"✅ Listing <code>#{listing_id}</code> ကို "
        "Market ကနေ ဖြုတ်ပြီးပါပြီ။",
        parse_mode="HTML",
    )


# ============================================================
# MARKET CALLBACK
# ============================================================

async def market_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):

    query = update.callback_query

    data = query.data or ""

    # --------------------------------------------------------
    # PAGE
    # --------------------------------------------------------

    if data.startswith("market:"):

        await query.answer()

        try:
            page = int(
                data.split(":", 1)[1]
            )

        except ValueError:
            return

        listings = get_active_listings()

        if not listings:
            await query.edit_message_text(
                "🛒 Market is empty."
            )
            return

        total_pages = max(
            1,
            math.ceil(
                len(listings)
                / MARKET_PER_PAGE
            ),
        )

        page = max(
            1,
            min(page, total_pages),
        )

        start = (
            (page - 1)
            * MARKET_PER_PAGE
        )

        end = (
            start
            + MARKET_PER_PAGE
        )

        page_listings = listings[
            start:end
        ]

        text = (
            "🛒 <b>NEXUS MARKET</b>\n\n"
            f"📄 Page {page}/{total_pages}\n\n"
        )

        for listing in page_listings:

            card = get_card(
                listing["char_id"]
            )

            if not card:
                continue

            text += (
                f"🔖 <b>#{listing['listing_id']}</b>\n"
                f"🎴 {card['name']}\n"
                f"🆔 <code>{card['char_id']}</code>\n"
                f"✨ {card['edition']}\n"
                f"💰 <b>{listing['price']:,}</b> Coins\n\n"
            )

        buttons = []

        navigation = []

        if page > 1:

            navigation.append(
                InlineKeyboardButton(
                    "⬅️",
                    callback_data=f"market:{page - 1}",
                )
            )

        if page < total_pages:

            navigation.append(
                InlineKeyboardButton(
                    "➡️",
                    callback_data=f"market:{page + 1}",
                )
            )

        if navigation:
            buttons.append(navigation)

        for listing in page_listings:

            buttons.append([
                InlineKeyboardButton(
                    f"🛒 Buy #{listing['listing_id']}",
                    callback_data=(
                        f"marketbuy:{listing['listing_id']}"
                    ),
                )
            ])

        await query.edit_message_text(
            text,
            reply_markup=InlineKeyboardMarkup(
                buttons
            ),
            parse_mode="HTML",
        )

        return

    # --------------------------------------------------------
    # BUY BUTTON
    # --------------------------------------------------------

    if data.startswith("marketbuy:"):

        await query.answer()

        try:
            listing_id = int(
                data.split(":", 1)[1]
            )

        except ValueError:

            await query.answer(
                "❌ Invalid listing.",
                show_alert=True,
            )

            return

        success, result = purchase_listing(
            query.from_user.id,
            listing_id,
        )

        if not success:

            await query.answer(
                result.replace(
                    "<b>",
                    "",
                ).replace(
                    "</b>",
                    "",
                ),
                show_alert=True,
            )

            return

        card = get_card(
            result["char_id"]
        )

        await query.answer(
            "🎉 Card ဝယ်ပြီးပါပြီ!",
            show_alert=True,
        )

        try:

            await query.message.reply_text(
                "🎉 <b>PURCHASE SUCCESSFUL!</b>\n\n"
                f"🎴 {card['name']}\n"
                f"🆔 <code>{card['char_id']}</code>\n"
                f"💰 Paid: <b>{result['price']:,}</b> Coins\n"
                f"🛒 Listing: <code>#{listing_id}</code>",
                parse_mode="HTML",
            )

        except Exception:
            pass

        return

    await query.answer()


# ============================================================
# ADMIN MARKET TOOLS
# ============================================================

def admin_cancel_listing(
    listing_id,
):

    with get_db() as db:

        db.execute(
            """
            UPDATE market_listings
            SET status = 'cancelled'
            WHERE listing_id = ?
              AND status = 'active'
            """,
            (listing_id,),
        )


def get_user_market_listings(
    user_id,
):

    with get_db() as db:

        return db.execute(
            """
            SELECT *
            FROM market_listings
            WHERE seller_id = ?
            ORDER BY listing_id DESC
            """,
            (user_id,),
        ).fetchall()


# ============================================================
# MARKET STATS
# ============================================================

def get_market_stats():

    with get_db() as db:

        total = db.execute(
            """
            SELECT COUNT(*)
            AS count
            FROM market_listings
            """
        ).fetchone()["count"]

        active = db.execute(
            """
            SELECT COUNT(*)
            AS count
            FROM market_listings
            WHERE status = 'active'
            """
        ).fetchone()["count"]

        sold = db.execute(
            """
            SELECT COUNT(*)
            AS count
            FROM market_listings
            WHERE status = 'sold'
            """
        ).fetchone()["count"]

        return {
            "total": total,
            "active": active,
            "sold": sold,
        }
