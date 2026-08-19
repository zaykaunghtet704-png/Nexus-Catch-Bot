import asyncio
import datetime
import random
import time
from threading import Thread

from config import BOT_TOKEN, OWNER_IDS, PORT, SPAWN_THRESHOLD
from flask import Flask
from models import (
    ADVANCED_RARITIES,
    ELEMENTS,
    Base,
    CardBase,
    ChatSettings,
    SessionLocal,
    User,
    UserCard,
)
from sqlalchemy.orm import joinedload
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

# ==========================================
# 🌐 KEEP-ALIVE SERVER (FOR TERMUX / CLOUD)
# ==========================================
app = Flask(__name__)


@app.route("/")
def home():
    return "<h1>Nexus Extended Production Core Operational</h1>"


def run_web():
    app.run(host="0.0.0.0", port=PORT)


# ==========================================
# 🧠 MEMORY CACHES & ACTIVE TRADES
# ==========================================
active_spawns = {}  # {chat_id: {"card_id": str, "hint": str}}
active_trades = {}  # {trade_id: {"sender": str, "receiver": str, ...}}
user_last_msg_time = {}
user_spam_count = {}
user_ignored_until = {}

# ==========================================
# 🛡️ HELPER FUNCTIONS & SECURITY
# ==========================================


async def check_anti_spam(update: Update) -> bool:
    if not update.effective_user:
        return True
    uid = update.effective_user.id
    now = time.time()

    if uid in user_ignored_until:
        if now < user_ignored_until[uid]:
            return False
        del user_ignored_until[uid]

    last = user_last_msg_time.get(uid, 0)
    user_last_msg_time[uid] = now

    if now - last < 0.7:
        user_spam_count[uid] = user_spam_count.get(uid, 0) + 1
    else:
        user_spam_count[uid] = 0

    if user_spam_count[uid] >= 6:
        user_ignored_until[uid] = now + 300
        user_spam_count[uid] = 0
        if update.message:
            await update.message.reply_text(
                "⛔ **Anti-Spam Activated!** You are muted for 5 minutes."
            )
        return False
    return True


def is_owner(user_id: int) -> bool:
    return user_id in OWNER_IDS


def calculate_card_power(user_card: UserCard) -> int:
    base = user_card.card_info.base_power
    lvl_multiplier = 1 + (user_card.level * 0.15)
    quality_multiplier = user_card.quality / 100.0
    return int(base * lvl_multiplier * quality_multiplier)


# ==========================================
# 🎮 USER & START COMMANDS
# ==========================================


async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_anti_spam(update):
        return
    session = SessionLocal()
    uid = str(update.effective_user.id)
    user = session.query(User).filter(User.id == uid).first()
    if not user:
        user = User(id=uid, name=update.effective_user.first_name)
        session.add(user)
        session.commit()
    session.close()
    await update.message.reply_text(
        f"✨ **WELCOME TO NEXUS CARD REALM!** ✨\n\nHello {update.effective_user.first_name}! Type `/help` to view all features."
    )


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_anti_spam(update):
        return
    text = (
        "📖 **FULL BOT FEATURE COMMANDS:**\n\n"
        "🎮 **COLLECTION & CATCH:**\n"
        "• `/catch <name>` - Catch spawned character\n"
        "• `/hint` - Reveal name puzzle hint\n"
        "• `/harem` - View card collection (Paginated)\n"
        "• `/check <uuid>` - Inspect card specs & battle power\n"
        "• `/fav <uuid>` / `/unfav` - Set favorite card\n\n"
        "⚔️ **GAMEPLAY & CARDS:**\n"
        "• `/upgrade <uuid>` - Level up your card\n"
        "• `/duel` - Battle other players (Reply to user)\n"
        "• `/gacha` - Spin 8-tier premium gacha\n\n"
        "🏪 **MARKET & TRADE:**\n"
        "• `/trade <uuid>` - Initiate direct secure trade\n"
        "• `/sell <uuid> <price>` - List card on market\n"
        "• `/buy <uuid>` - Buy card from market\n"
        "• `/market` - View global card market\n"
        "• `/gift <uuid>` - Gift card to a user (Reply)\n\n"
        "💰 **PROFILE & ECONOMY:**\n"
        "• `/profile` - Check stats & balance\n"
        "• `/daily` - Claim daily coin rewards\n"
        "• `/top` - Wealthiest collectors\n"
        "• `/ctop` - Most printed cards\n\n"
        "⚙️ **ADMIN COMMANDS:**\n"
        "• `/addcard` | `/delcard` | `/ban` | `/unban` | `/givecoins`"
    )
    await update.message.reply_text(text, parse_mode="Markdown")


# ==========================================
# ⚡ SPAWN, CATCH & HINT ENGINE
# ==========================================


async def catch_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_anti_spam(update):
        return
    chat_id = str(update.effective_chat.id)

    if chat_id not in active_spawns:
        await update.message.reply_text("❌ ဖမ်းယူရန် ကဒ်မရှိပါ။")
        return

    if not context.args:
        await update.message.reply_text("❌ Usage: `/catch <character_name>`")
        return

    guess = " ".join(context.args).strip().lower()
    session = SessionLocal()
    spawn_data = active_spawns[chat_id]
    card = (
        session.query(CardBase)
        .filter(CardBase.id == spawn_data["card_id"])
        .first()
    )

    if card and guess == card.name.lower():
        uid = str(update.effective_user.id)
        user = session.query(User).filter(User.id == uid).first()
        if not user:
            user = User(id=uid, name=update.effective_user.first_name)
            session.add(user)

        card.total_prints += 1
        new_card = UserCard(
            user_id=uid,
            card_id=card.id,
            print_number=card.total_prints,
            quality=round(random.uniform(75.0, 100.0), 1),
        )
        session.add(new_card)
        session.commit()

        del active_spawns[chat_id]
        session.close()

        await update.message.reply_text(
            f"🎉 **SUCCESSFUL CATCH!**\n"
            f"👤 **{update.effective_user.first_name}** caught **{card.name}**!\n"
            f"🌟 Rarity: {card.rarity}\n"
            f"⚡ Element: {card.element}\n"
            f"🏷️ Print: `#{card.total_prints}` | ✨ Quality: `{new_card.quality}%`\n"
            f"🆔 UUID: `{new_card.uuid}`",
            parse_mode="Markdown",
        )
    else:
        session.close()
        await update.message.reply_text(
            "❌ နာမည်အမှန် မဟုတ်ပါ။ ပြန်လည်ကြိုးစားပါ!"
        )


async def hint_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_anti_spam(update):
        return
    chat_id = str(update.effective_chat.id)
    if chat_id not in active_spawns:
        await update.message.reply_text("❌ အချက်အလက်ပြစရာ ကဒ်မရှိပါ။")
        return
    await update.message.reply_text(
        f"💡 **HINT:** `{active_spawns[chat_id]['hint']}`", parse_mode="Markdown"
    )


# ==========================================
# 🏰 INTERACTIVE PAGINATION HAREM
# ==========================================


async def harem_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_anti_spam(update):
        return
    session = SessionLocal()
    uid = str(update.effective_user.id)
    cards = (
        session.query(UserCard)
        .options(joinedload(UserCard.card_info))
        .filter(UserCard.user_id == uid)
        .all()
    )

    if not cards:
        await update.message.reply_text("🏰 သင့် Harem ထဲမှာ ကဒ်မရှိသေးပါ။")
        session.close()
        return

    text, keyboard = render_harem_page(
        cards, 0, update.effective_user.first_name
    )
    session.close()
    await update.message.reply_text(
        text, reply_markup=keyboard, parse_mode="Markdown"
    )


def render_harem_page(cards, page, user_name):
    per_page = 8
    total_pages = (len(cards) + per_page - 1) // per_page
    start = page * per_page
    end = start + per_page

    text = f"🏰 **{user_name}'s Collection ({len(cards)} Cards) - Page {page + 1}/{total_pages}**\n\n"
    for idx, c in enumerate(cards[start:end], start + 1):
        pwr = calculate_card_power(c)
        text += (
            f"{idx}. **{c.card_info.name}** [{c.card_info.rarity}]\n"
            f"   ⚡ Power: `{pwr}` | Lvl: `{c.level}` | Q: `{c.quality}%` | #{c.print_number} | ID: `{c.uuid}`\n"
        )

    buttons = []
    if page > 0:
        buttons.append(
            InlineKeyboardButton("◀️ Prev", callback_data=f"harem_{page - 1}")
        )
    if page < total_pages - 1:
        buttons.append(
            InlineKeyboardButton("Next ▶️", callback_data=f"harem_{page + 1}")
        )

    keyboard = InlineKeyboardMarkup([buttons]) if buttons else None
    return text, keyboard


async def harem_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    page = int(query.data.split("_")[1])
    session = SessionLocal()
    uid = str(query.from_user.id)
    cards = (
        session.query(UserCard)
        .options(joinedload(UserCard.card_info))
        .filter(UserCard.user_id == uid)
        .all()
    )
    text, keyboard = render_harem_page(cards, page, query.from_user.first_name)
    session.close()
    await query.edit_message_text(
        text, reply_markup=keyboard, parse_mode="Markdown"
    )


# ==========================================
# 🌟 LEVEL UP & UPGRADE ENGINE
# ==========================================


async def upgrade_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_anti_spam(update):
        return
    if not context.args:
        await update.message.reply_text("❌ Usage: `/upgrade <card_uuid>`")
        return

    card_uuid = context.args[0]
    session = SessionLocal()
    uid = str(update.effective_user.id)

    card = (
        session.query(UserCard)
        .options(joinedload(UserCard.card_info))
        .filter(UserCard.uuid == card_uuid, UserCard.user_id == uid)
        .first()
    )

    if not card:
        await update.message.reply_text("❌ ဒီကဒ်ကို ရှာမတွေ့ပါ။")
        session.close()
        return

    upgrade_cost = card.level * 500
    user = session.query(User).filter(User.id == uid).first()

    if user.coins < upgrade_cost:
        await update.message.reply_text(
            f"❌ Level တက်ရန် Coins မလောက်ပါ။ လိုအပ်သော ငွေ: `{upgrade_cost}` Coins"
        )
        session.close()
        return

    user.coins -= upgrade_cost
    card.level += 1
    new_power = calculate_card_power(card)

    session.commit()
    session.close()

    await update.message.reply_text(
        f"📈 **LEVEL UP SUCCESSFUL!**\n\n"
        f"👤 Card: **{card.card_info.name}**\n"
        f"🔝 New Level: `{card.level}`\n"
        f"⚡ New Battle Power: `{new_power}`",
        parse_mode="Markdown",
    )


# ==========================================
# ⚔️ CARD DUEL & BATTLE ENGINE
# ==========================================


async def duel_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_anti_spam(update):
        return
    if not update.message.reply_to_message:
        await update.message.reply_text(
            "⚔️ Challenge ပြုလုပ်ရန် ယှဉ်ပြိုင်လိုသူ၏ စာကို Reply ပြန်၍ `/duel` ရိုက်ပါ။"
        )
        return

    p1_id = str(update.effective_user.id)
    p2_id = str(update.message.reply_to_message.from_user.id)

    if p1_id == p2_id:
        await update.message.reply_text("❌ မိမိကိုယ်တိုင် Duel တိုက်၍ မရပါ။")
        return

    session = SessionLocal()
    p1_user = session.query(User).filter(User.id == p1_id).first()
    p2_user = session.query(User).filter(User.id == p2_id).first()

    p1_card = (
        session.query(UserCard)
        .options(joinedload(UserCard.card_info))
        .filter(UserCard.uuid == (p1_user.fav_card_id if p1_user else None))
        .first()
    )
    p2_card = (
        session.query(UserCard)
        .options(joinedload(UserCard.card_info))
        .filter(UserCard.uuid == (p2_user.fav_card_id if p2_user else None))
        .first()
    )

    if not p1_card or not p2_card:
        await update.message.reply_text(
            "❌ ပြိုင်ဘက် နှစ်ဦးလုံး `/fav <uuid>` သုံးပြီး Favorite Card သတ်မှတ်ထားရပါမည်။"
        )
        session.close()
        return

    p1_pwr = calculate_card_power(p1_card)
    p2_pwr = calculate_card_power(p2_card)

    # Random RNG Variance (+/- 15%)
    p1_final = int(p1_pwr * random.uniform(0.85, 1.15))
    p2_final = int(p2_pwr * random.uniform(0.85, 1.15))

    winner_name = (
        update.effective_user.first_name
        if p1_final > p2_final
        else update.message.reply_to_message.from_user.first_name
    )

    text = (
        f"⚔️ **EPIC CARD DUEL BATTLE** ⚔️\n\n"
        f"🔴 **{update.effective_user.first_name}** ({p1_card.card_info.name})\n"
        f"⚡ Power Score: `{p1_final}`\n\n"
        f"🔵 **{update.message.reply_to_message.from_user.first_name}** ({p2_card.card_info.name})\n"
        f"⚡ Power Score: `{p2_final}`\n\n"
        f"🏆 Winner: **{winner_name}**!"
    )
    session.close()
    await update.message.reply_text(text, parse_mode="Markdown")


# ==========================================
# 🎰 ADVANCED 8-TIER GACHA SYSTEM
# ==========================================


async def gacha_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_anti_spam(update):
        return
    session = SessionLocal()
    uid = str(update.effective_user.id)
    user = session.query(User).filter(User.id == uid).first()

    if not user or user.coins < 1000:
        await update.message.reply_text(
            "❌ Premium Gacha လှည့်ရန် Coins 1,000 လိုအပ်ပါသည်။"
        )
        session.close()
        return

    rarities = list(ADVANCED_RARITIES.keys())
    weights = list(ADVANCED_RARITIES.values())
    chosen_rarity = random.choices(rarities, weights=weights, k=1)[0]

    cards = (
        session.query(CardBase).filter(CardBase.rarity == chosen_rarity).all()
    )
    if not cards:
        cards = session.query(CardBase).all()

    card = random.choice(cards)
    user.coins -= 1000
    card.total_prints += 1

    new_card = UserCard(
        user_id=uid,
        card_id=card.id,
        print_number=card.total_prints,
        quality=round(random.uniform(85.0, 100.0), 1),
    )
    session.add(new_card)
    session.commit()

    pwr = calculate_card_power(new_card)
    caption = (
        f"🌌 **SUMMONING RESULTS!**\n\n"
        f"👤 Character: **{card.name}**\n"
        f"🌟 Rarity: **{card.rarity}**\n"
        f"⚡ Element: {card.element}\n"
        f"💥 Battle Power: `{pwr}`\n"
        f"✨ Quality: `{new_card.quality}%`\n"
        f"🆔 UUID: `{new_card.uuid}`"
    )
    session.close()
    try:
        await update.message.reply_photo(
            photo=card.image_url, caption=caption, parse_mode="Markdown"
        )
    except Exception:
        await update.message.reply_text(caption, parse_mode="Markdown")


# ==========================================
# 🤝 ESCROW DIRECT TRADE SYSTEM
# ==========================================


async def trade_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_anti_spam(update):
        return
    if not update.message.reply_to_message or not context.args:
        await update.message.reply_text(
            "❌ Usage: Reply to target user with `/trade <your_card_uuid>`"
        )
        return

    sender_id = str(update.effective_user.id)
    receiver_id = str(update.message.reply_to_message.from_user.id)
    card_uuid = context.args[0]

    session = SessionLocal()
    card = (
        session.query(UserCard)
        .options(joinedload(UserCard.card_info))
        .filter(UserCard.uuid == card_uuid, UserCard.user_id == sender_id)
        .first()
    )

    if not card:
        await update.message.reply_text("❌ ဒီကဒ်ကို သင့် Harem ထဲမှာ ရှာမတွေ့ပါ!")
        session.close()
        return

    trade_id = f"{sender_id}_{receiver_id}_{card_uuid}"
    active_trades[trade_id] = {
        "sender": sender_id,
        "receiver": receiver_id,
        "uuid": card_uuid,
    }

    buttons = [
        [
            InlineKeyboardButton(
                "✅ Accept Trade", callback_data=f"tr_acc_{trade_id}"
            ),
            InlineKeyboardButton(
                "❌ Decline", callback_data=f"tr_dec_{trade_id}"
            ),
        ]
    ]
    keyboard = InlineKeyboardMarkup(buttons)

    session.close()
    await update.message.reply_text(
        f"🤝 **TRADE OFFER**\n\n"
        f"**{update.effective_user.first_name}** wants to gift/trade card **{card.card_info.name}** (`{card.uuid}`) "
        f"to **{update.message.reply_to_message.from_user.first_name}**.",
        reply_markup=keyboard,
        parse_mode="Markdown",
    )


async def trade_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data
    action, trade_id = data.split("_")[1], data.split("_")[2]
    trade = active_trades.get(trade_id)

    if not trade:
        await query.edit_message_text("❌ ဒီ Trade က သက်တမ်းကုန်သွားပါပြီ။")
        return

    if str(query.from_user.id) != trade["receiver"]:
        await query.answer("❌ သင်သည် လက်ခံသူ မဟုတ်ပါ!", show_alert=True)
        return

    if action == "acc":
        session = SessionLocal()
        card = (
            session.query(UserCard)
            .filter(
                UserCard.uuid == trade["uuid"],
                UserCard.user_id == trade["sender"],
            )
            .first()
        )
        if card:
            card.user_id = trade["receiver"]
            session.commit()
            await query.edit_message_text("🎉 **TRADE COMPLETED SUCCESSFULLY!**")
        else:
            await query.edit_message_text(
                "❌ Trade မအောင်မြင်ပါ (ကဒ် မရှိတော့ပါ)။"
            )
        session.close()
    else:
        await query.edit_message_text("❌ Trade ❌ ငြင်းပယ်လိုက်ပါပြီ။")

    if trade_id in active_trades:
        del active_trades[trade_id]


# ==========================================
# 🛠️ ADMIN DIRECT CONTROL COMMANDS
# ==========================================


async def addcard_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id):
        return
    raw_text = " ".join(context.args)
    parts = [p.strip() for p in raw_text.split("|")]

    if len(parts) < 5:
        await update.message.reply_text(
            "❌ Usage: `/addcard <id> | <name> | <anime> | <rarity> | <img_url>`"
        )
        return

    session = SessionLocal()
    new_c = CardBase(
        id=parts[0],
        name=parts[1],
        anime=parts[2],
        rarity=parts[3],
        image_url=parts[4],
    )
    session.add(new_c)
    session.commit()
    session.close()
    await update.message.reply_text(
        f"✅ Card **{parts[1]}** successfully inserted to DB!"
    )


async def givecoins_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_user.id):
        return
    if len(context.args) < 2:
        await update.message.reply_text("❌ Usage: `/givecoins <user_id> <amount>`")
        return

    uid, amount = context.args[0], int(context.args[1])
    session = SessionLocal()
    user = session.query(User).filter(User.id == uid).first()
    if user:
        user.coins += amount
        session.commit()
        await update.message.reply_text(
            f"✅ Gave `{amount}` Coins to user `{uid}`."
        )
    session.close()


# ==========================================
# ⚙️ SPAWN ENGINE & MESSAGE HANDLER
# ==========================================


async def handle_spawns(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if (
        not update.message
        or not update.message.text
        or update.message.text.startswith("/")
    ):
        return

    chat_id = str(update.effective_chat.id)
    session = SessionLocal()
    setting = (
        session.query(ChatSettings)
        .filter(ChatSettings.chat_id == chat_id)
        .first()
    )

    if not setting:
        setting = ChatSettings(
            chat_id=chat_id,
            spawn_threshold=SPAWN_THRESHOLD,
            current_msg_count=1,
        )
        session.add(setting)
    else:
        setting.current_msg_count += 1

    if setting.current_msg_count >= setting.spawn_threshold:
        cards = session.query(CardBase).all()
        if cards:
            setting.current_msg_count = 0
            selected_card = random.choice(cards)
            name = selected_card.name
            hint = (
                name[0]
                + " "
                + " ".join(["_" if c != " " else " " for c in name[1:-1]])
                + " "
                + name[-1]
            )

            active_spawns[chat_id] = {"card_id": selected_card.id, "hint": hint}
            caption = (
                f"⚡ **A WILD CHARACTER APPEARED!**\n\n"
                f"🌟 Rarity: **{selected_card.rarity}**\n"
                f"⚡ Element: {selected_card.element}\n"
                f"💡 Hint: `{hint}`\n\n"
                f"Use `/catch <name>` to claim!"
            )
            try:
                await context.bot.send_photo(
                    chat_id=int(chat_id),
                    photo=selected_card.image_url,
                    caption=caption,
                    parse_mode="Markdown",
                )
            except Exception as e:
                print(f"Spawn Error: {e}")

    session.commit()
    session.close()


# ==========================================
# 🚀 MAIN APP LAUNCHER
# ==========================================

if __name__ == "__main__":
    Thread(target=run_web).start()
    bot = ApplicationBuilder().token(BOT_TOKEN).build()

    # Base Handlers
    bot.add_handler(CommandHandler("start", start_cmd))
    bot.add_handler(CommandHandler("help", help_cmd))

    # Card & Collection Handlers
    bot.add_handler(CommandHandler("catch", catch_cmd))
    bot.add_handler(CommandHandler("hint", hint_cmd))
    bot.add_handler(CommandHandler("harem", harem_cmd))
    bot.add_handler(CommandHandler("upgrade", upgrade_cmd))
    bot.add_handler(CommandHandler("duel", duel_cmd))
    bot.add_handler(CommandHandler("gacha", gacha_cmd))
    bot.add_handler(CommandHandler("trade", trade_cmd))

    # Admin Handlers
    bot.add_handler(CommandHandler("addcard", addcard_cmd))
    bot.add_handler(CommandHandler("givecoins", givecoins_cmd))

    # Callbacks
    bot.add_handler(CallbackQueryHandler(harem_callback, pattern="^harem_"))
    bot.add_handler(CallbackQueryHandler(trade_callback, pattern="^tr_"))

    # Spawn Handler
    bot.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_spawns)
    )

    print("Full Feature Extended Engine Running Smoothly!")
    bot.run_polling()
