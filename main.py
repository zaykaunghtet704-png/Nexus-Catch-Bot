import asyncio
import random
import time
from datetime import datetime, timedelta
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

app = Flask(__name__)


@app.route("/")
def home():
    return "10-Tier Ultimate Production Core Online"


def run_web():
    app.run(host="0.0.0.0", port=PORT)


active_spawns = {}
active_trades = {}
user_last_msg_time = {}
user_spam_count = {}
user_ignored_until = {}


# --- ANTI-SPAM SYSTEM ---
async def check_anti_spam(update: Update) -> bool:
    if not update.effective_user:
        return True
    uid, now = update.effective_user.id, time.time()
    if uid in user_ignored_until and now < user_ignored_until[uid]:
        return False
    last = user_last_msg_time.get(uid, 0)
    user_last_msg_time[uid] = now
    user_spam_count[uid] = (
        user_spam_count.get(uid, 0) + 1 if now - last < 0.7 else 0
    )
    if user_spam_count[uid] >= 6:
        user_ignored_until[uid] = now + 300
        user_spam_count[uid] = 0
        if update.message:
            await update.message.reply_text("⛔ Spam Detected! Muted for 5 mins.")
        return False
    return True


def is_owner(user_id: int) -> bool:
    return user_id in OWNER_IDS


def calculate_card_power(c: UserCard) -> int:
    tier_bonus = 1.0
    if c.card_info.rarity == "✨ Omnipotent":
        tier_bonus = 1.5
    elif c.card_info.rarity == "👑 Sovereign":
        tier_bonus = 2.0
    return int(
        (c.card_info.base_power * tier_bonus)
        * (1 + c.level * 0.15)
        * (c.quality / 100.0)
    )


# --- GENERAL & HELP COMMANDS ---
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
        f"✨ **WELCOME TO NEXUS 10-TIER REALM!**\nCommands အားလုံးကြည့်ရန် `/help` ရိုက်ပါ!"
    )


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_anti_spam(update):
        return
    text = (
        "📖 **10-TIER MEGA BOT COMMANDS LIST:**\n\n"
        "🎮 **COLLECTION & GAMEPLAY:**\n"
        "• `/catch <name>` - Catch wild spawned card\n"
        "• `/hint` - Show hint for spawned character\n"
        "• `/grab` / `/claim` - Free card claim (15m Cooldown)\n"
        "• `/fuse <uuid1> <uuid2>` - Fuse 2 cards to upgrade\n"
        "• `/harem` - View paginated collection\n"
        "• `/fav <uuid>` - Set favorite battle card\n\n"
        "⚔️ **DUEL & UPGRADE:**\n"
        "• `/upgrade <uuid>` - Level up card\n"
        "• `/duel` - Battle target user (Reply)\n"
        "• `/gacha` - Spin 10-tier premium gacha\n\n"
        "🏪 **MARKET & TRADE & CRAFT:**\n"
        "• `/trade <uuid>` - Direct secure 1-on-1 trade\n"
        "• `/sell <uuid> <price>` - List card on market\n"
        "• `/buy <uuid>` - Buy card from market\n"
        "• `/market` - Global market listings\n"
        "• `/disassemble <uuid>` - Break card into Shards\n\n"
        "💰 **PROFILE & ECONOMY:**\n"
        "• `/profile` - Stats, coins & shards\n"
        "• `/daily` - Claim daily reward + streak\n"
        "• `/top` - Leaderboard\n\n"
        "⚙️ **ADMIN DIRECT COMMANDS:**\n"
        "• `/addcard` | `/givecoins`"
    )
    await update.message.reply_text(text, parse_mode="Markdown")


# --- CATCH & HINT ENGINE ---
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


# --- HAREM & PAGINATION ENGINE ---
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
        await update.message.reply_text("🏰 သင့် Harem ထဲတွင် ကဒ်မရှိသေးပါ!")
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

    text = f"🏰 **{user_name}'s Harem ({len(cards)} Cards) - Page {page + 1}/{total_pages}**\n\n"
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


# --- 10-TIER GACHA SUMMON ---
async def gacha_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_anti_spam(update):
        return
    session = SessionLocal()
    uid = str(update.effective_user.id)
    user = session.query(User).filter(User.id == uid).first()

    if not user or user.coins < 1000:
        await update.message.reply_text(
            "❌ Gacha လှည့်ရန် Coins 1,000 လိုအပ်ပါသည်။"
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
        quality=round(random.uniform(80.0, 100.0), 1),
    )
    session.add(new_card)
    session.commit()

    pwr = calculate_card_power(new_card)
    caption = (
        f"🌌 **10-TIER GACHA SUMMON!**\n\n"
        f"👤 Character: **{card.name}**\n"
        f"🌟 Rarity: **{card.rarity}**\n"
        f"⚡ Element: {card.element}\n"
        f"💥 Power: `{pwr}`\n"
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


# --- TIME-BASED FREE GRAB ---
async def grab_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_anti_spam(update):
        return
    session = SessionLocal()
    uid = str(update.effective_user.id)
    user = session.query(User).filter(User.id == uid).first()
    if not user:
        user = User(id=uid, name=update.effective_user.first_name)
        session.add(user)

    now = datetime.utcnow()
    if user.last_grab and (now - user.last_grab) < timedelta(minutes=15):
        rem = timedelta(minutes=15) - (now - user.last_grab)
        mins, secs = divmod(rem.seconds, 60)
        await update.message.reply_text(
            f"⏳ Cooldown Active! Wait `{mins}m {secs}s` to grab again."
        )
        session.close()
        return

    cards = session.query(CardBase).all()
    if not cards:
        await update.message.reply_text("❌ Database ထဲတွင် ကဒ်မရှိသေးပါ။")
        session.close()
        return

    card = random.choice(cards)
    card.total_prints += 1
    user.last_grab = now

    new_card = UserCard(
        user_id=uid,
        card_id=card.id,
        print_number=card.total_prints,
        quality=round(random.uniform(70.0, 99.0), 1),
    )
    session.add(new_card)
    session.commit()

    caption = (
        f"🎁 **FREE CLAIM SUCCESSFUL!**\n\n"
        f"👤 Character: **{card.name}**\n"
        f"🌟 Rarity: **{card.rarity}**\n"
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


# --- CARD FUSION SYSTEM ---
async def fuse_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_anti_spam(update):
        return
    if len(context.args) < 2:
        await update.message.reply_text(
            "❌ Usage: `/fuse <card_uuid_1> <card_uuid_2>`"
        )
        return

    u1, u2 = context.args[0], context.args[1]
    session = SessionLocal()
    uid = str(update.effective_user.id)

    c1 = (
        session.query(UserCard)
        .filter(UserCard.uuid == u1, UserCard.user_id == uid)
        .first()
    )
    c2 = (
        session.query(UserCard)
        .filter(UserCard.uuid == u2, UserCard.user_id == uid)
        .first()
    )

    if not c1 or not c2:
        await update.message.reply_text("❌ သင့် Harem ထဲတွင် ကဒ်များ မရှိပါ!")
        session.close()
        return

    session.delete(c1)
    session.delete(c2)

    rarities = list(ADVANCED_RARITIES.keys())
    weights = list(ADVANCED_RARITIES.values())
    chosen_rarity = random.choices(rarities, weights=weights, k=1)[0]

    cards = (
        session.query(CardBase).filter(CardBase.rarity == chosen_rarity).all()
    )
    if not cards:
        cards = session.query(CardBase).all()

    new_base = random.choice(cards)
    new_base.total_prints += 1

    fused_card = UserCard(
        user_id=uid,
        card_id=new_base.id,
        print_number=new_base.total_prints,
        quality=round(random.uniform(85.0, 100.0), 1),
    )
    session.add(fused_card)
    session.commit()

    await update.message.reply_text(
        f"🔮 **FUSION SUCCESSFUL!**\nFused 2 cards into **{new_base.name}** [{new_base.rarity}]!\n🆔 UUID: `{fused_card.uuid}`",
        parse_mode="Markdown",
    )
    session.close()


# --- MARKET & TRADE SYSTEM ---
async def sell_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_anti_spam(update) or len(context.args) < 2:
        await update.message.reply_text(
            "❌ Usage: `/sell <card_uuid> <price>`"
        )
        return

    uuid, price = context.args[0], int(context.args[1])
    session = SessionLocal()
    uid = str(update.effective_user.id)
    card = (
        session.query(UserCard)
        .filter(UserCard.uuid == uuid, UserCard.user_id == uid)
        .first()
    )
    if not card:
        await update.message.reply_text("❌ ဒီကဒ်ကို ရှာမတွေ့ပါ။")
        session.close()
        return

    card.is_market = True
    card.market_price = price
    session.commit()
    session.close()
    await update.message.reply_text(
        f"🏪 Card `{uuid}` Listed on Market for `{price}` Coins!"
    )


async def market_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_anti_spam(update):
        return
    session = SessionLocal()
    cards = (
        session.query(UserCard)
        .options(joinedload(UserCard.card_info))
        .filter(UserCard.is_market == True)
        .limit(10)
        .all()
    )
    if not cards:
        await update.message.reply_text(
            "🏪 ဈေးကွက်ထဲတွင် ရောင်းရန် ကဒ်မရှိသေးပါ။"
        )
        session.close()
        return

    text = "🏪 **GLOBAL CARD MARKET:**\n\n"
    for c in cards:
        text += f"• **{c.card_info.name}** [{c.card_info.rarity}] | 💰 `{c.market_price}` Coins | ID: `{c.uuid}`\n"
    text += "\nဝယ်ယူရန်: `/buy <uuid>`"
    session.close()
    await update.message.reply_text(text, parse_mode="Markdown")


async def buy_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_anti_spam(update) or not context.args:
        await update.message.reply_text("❌ Usage: `/buy <card_uuid>`")
        return

    uuid = context.args[0]
    session = SessionLocal()
    uid = str(update.effective_user.id)
    buyer = session.query(User).filter(User.id == uid).first()
    card = (
        session.query(UserCard)
        .filter(UserCard.uuid == uuid, UserCard.is_market == True)
        .first()
    )

    if not card or buyer.coins < card.market_price:
        await update.message.reply_text(
            "❌ ဝယ်ယူ၍ မရပါ (ကဒ်မရှိပါ သို့ ငွေမလောက်ပါ)!"
        )
        session.close()
        return

    seller = session.query(User).filter(User.id == card.user_id).first()
    buyer.coins -= card.market_price
    if seller:
        seller.coins += card.market_price

    card.user_id = uid
    card.is_market = False
    card.market_price = 0
    session.commit()
    session.close()
    await update.message.reply_text("🎉 ကဒ်ကို အောင်မြင်စွာ ဝယ်ယူလိုက်ပါပြီ!")


# --- PROFILE, DAILY & LEADERBOARD ---
async def profile_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_anti_spam(update):
        return
    session = SessionLocal()
    uid = str(update.effective_user.id)
    user = session.query(User).filter(User.id == uid).first()
    if not user:
        user = User(id=uid, name=update.effective_user.first_name)
        session.add(user)
        session.commit()

    card_count = (
        session.query(UserCard).filter(UserCard.user_id == uid).count()
    )
    text = (
        f"👤 **USER PROFILE:** {user.name}\n"
        f"💰 Coins: `{user.coins}`\n"
        f"🧩 Shards: `{user.shards}`\n"
        f"🎴 Total Cards: `{card_count}`\n"
        f"🔥 Daily Streak: `{user.daily_streak} Days`"
    )
    session.close()
    await update.message.reply_text(text, parse_mode="Markdown")


async def daily_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_anti_spam(update):
        return
    session = SessionLocal()
    uid = str(update.effective_user.id)
    user = session.query(User).filter(User.id == uid).first()
    if not user:
        user = User(id=uid, name=update.effective_user.first_name)
        session.add(user)

    now = datetime.utcnow()
    if user.last_daily and (now - user.last_daily) < timedelta(hours=24):
        rem = timedelta(hours=24) - (now - user.last_daily)
        hours, remainder = divmod(rem.seconds, 3600)
        mins, _ = divmod(remainder, 60)
        await update.message.reply_text(
            f"⏳ Daily reward claimed already! Wait `{hours}h {mins}m`."
        )
        session.close()
        return

    if user.last_daily and (now - user.last_daily) < timedelta(hours=48):
        user.daily_streak += 1
    else:
        user.daily_streak = 1

    bonus = user.daily_streak * 100
    reward = 1000 + bonus
    user.coins += reward
    user.last_daily = now

    session.commit()
    session.close()
    await update.message.reply_text(
        f"🎉 **DAILY REWARD CLAIMED!**\n💰 Reward: `{reward}` Coins\n🔥 Daily Streak: `{user.daily_streak} Days`",
        parse_mode="Markdown",
    )


async def disassemble_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_anti_spam(update) or not context.args:
        await update.message.reply_text(
            "❌ Usage: `/disassemble <card_uuid>`"
        )
        return

    uuid = context.args[0]
    session = SessionLocal()
    uid = str(update.effective_user.id)
    card = (
        session.query(UserCard)
        .filter(UserCard.uuid == uuid, UserCard.user_id == uid)
        .first()
    )
    if not card:
        await update.message.reply_text("❌ ဒီကဒ်ကို ရှာမတွေ့ပါ။")
        session.close()
        return

    user = session.query(User).filter(User.id == uid).first()
    user.shards += 15
    session.delete(card)
    session.commit()
    session.close()
    await update.message.reply_text("🧩 Card disassembled! Gained `15` Shards.")


# --- ADMIN DIRECT CONTROLS ---
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
        f"✅ Card **{parts[1]}** successfully added!"
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
            f"✅ Gave `{amount}` Coins to `{uid}`."
        )
    session.close()


# --- SPAWN ENGINE ---
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
            selected = random.choice(cards)
            hint = (
                selected.name[0]
                + " "
                + " ".join(["_" if c != " " else " " for c in selected.name[1:-1]])
                + " "
                + selected.name[-1]
            )

            active_spawns[chat_id] = {"card_id": selected.id, "hint": hint}
            caption = (
                f"⚡ **A WILD CHARACTER APPEARED!**\n\n"
                f"🌟 Rarity: **{selected.rarity}**\n"
                f"💡 Hint: `{hint}`\n\n"
                f"`/catch <name>` ဖြင့် ဖမ်းယူပါ!"
            )
            try:
                await context.bot.send_photo(
                    chat_id=int(chat_id),
                    photo=selected.image_url,
                    caption=caption,
                    parse_mode="Markdown",
                )
            except Exception as e:
                print(f"Spawn Error: {e}")

    session.commit()
    session.close()


# --- LAUNCH APPLICATION ---
if __name__ == "__main__":
    Thread(target=run_web).start()
    bot = ApplicationBuilder().token(BOT_TOKEN).build()

    bot.add_handler(CommandHandler("start", start_cmd))
    bot.add_handler(CommandHandler("help", help_cmd))
    bot.add_handler(CommandHandler("catch", catch_cmd))
    bot.add_handler(CommandHandler("hint", hint_cmd))
    bot.add_handler(CommandHandler("harem", harem_cmd))
    bot.add_handler(CommandHandler("gacha", gacha_cmd))
    bot.add_handler(CommandHandler("grab", grab_cmd))
    bot.add_handler(CommandHandler("claim", grab_cmd))
    bot.add_handler(CommandHandler("fuse", fuse_cmd))
    bot.add_handler(CommandHandler("sell", sell_cmd))
    bot.add_handler(CommandHandler("market", market_cmd))
    bot.add_handler(CommandHandler("buy", buy_cmd))
    bot.add_handler(CommandHandler("profile", profile_cmd))
    bot.add_handler(CommandHandler("daily", daily_cmd))
    bot.add_handler(CommandHandler("disassemble", disassemble_cmd))

    # Admin Command Handlers
    bot.add_handler(CommandHandler("addcard", addcard_cmd))
    bot.add_handler(CommandHandler("givecoins", givecoins_cmd))

    # Callback Query Handlers
    bot.add_handler(CallbackQueryHandler(harem_callback, pattern="^harem_"))

    # Spawn Handler
    bot.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_spawns)
    )

    print("10-Tier Ultimate Production Core Engine Running!")
    bot.run_polling()
