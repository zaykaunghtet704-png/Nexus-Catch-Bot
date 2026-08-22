from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes
from config import OWNER_ID, OWNER_USERNAME, MAX_SELL_PRICE
from services import check_group_member_count, check_force_join

async def power_footer(update: Update, text: str):
    """Command တစ်ခုပြီးတိုင်း Power by 'maybe' စာသားကို ခဏပြရန်"""
    footer_text = f"\n\n✨ <i>Power by \"maybe\"</i> ✨"
    await update.message.reply_text(text + footer_text, parse_mode="HTML")

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await check_group_member_count(update, context):
        return
    if not await check_force_join(update, context):
        return

    welcome_text = (
        "🌟 **Welcome to Nexus-Catch-Bot!** 🌟\n\n"
        "🃏 ကဒ်များကို စုဆောင်းပါ၊ ဈေးကွက်တင်ပါ၊ တိုက်ပွဲဝင်ပါ!\n"
        "ဘာသာစကားနှင့် အချက်အလက်များအတွက် /help ကိုနှိပ်ပါ။"
    )
    await power_footer(update, welcome_text)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("📚 View All Commands & Guide", url=f"https://t.me/{OWNER_USERNAME}")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    help_text = "📖 **Nexus-Catch-Bot Commands Help Menu**\nအောက်ပါခလုတ်ကိုနှိပ်၍ အချက်အလက်အပြည့်အစုံ ကြည့်ရှုနိုင်ပါသည်။"
    await update.message.reply_text(help_text, reply_markup=reply_markup, parse_mode="Markdown")

async def harem_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = "🎴 **Your Harem Cards Collection:**\n(Favorite ကဒ်များကို အပေါ်ဆုံးတွင် ပြသထားသည်)"
    keyboard = [[InlineKeyboardButton("🖼 View All Card Photos", url=f"https://t.me/{OWNER_USERNAME}")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(text, reply_markup=reply_markup, parse_mode="Markdown")

async def search_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = "🔍 ဒေတာဘေ့စ်ထဲတွင်ရှိသော ကဒ်များအား Album ပုံစံဖြင့် ရှာဖွေနေပါသည်..."
    await power_footer(update, text)

async def profile_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = "👤 **User Profile**\n💰 Coins: 500\n🎴 Cards Owned: 0\n🌐 Global Rank: #1"
    await power_footer(update, text)

async def nexus_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    card_name = " ".join(context.args) if context.args else "Unknown"
    text = f"🎯 Nexus System: '{card_name}' ကဒ်ကို ရှာဖွေဖမ်းဆီးနေပါပြီ..."
    await power_footer(update, text)

async def daily_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = "🎁 Daily Reward: 500 Coins အခမဲ့ ရရှိသွားပါပြီ!"
    await power_footer(update, text)

async def claim_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = "🃏 ကျပန်းကဒ် ၅ ကဒ်ကို အခမဲ့ ထုတ်ယူပြီးပါပြီ!"
    await power_footer(update, text)

async def balance_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = "💳 လက်ကျန်ငွေ: 500 Coins"
    await power_footer(update, text)

async def market_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("🛒 Open Market", url=f"https://t.me/{OWNER_USERNAME}")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("🛍 **Card Market** (ဈေးကွက်)", reply_markup=reply_markup)

async def sell_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = f"🏷 ကဒ်ကို ဈေးကွက်တင်ပြီးပါပြီ။ (အမြင့်ဆုံးဈေးနှုန်းမှာ {MAX_SELL_PRICE} ဖြစ်သည်)"
    await power_footer(update, text)

async def duel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = "⚔️ **Duel Arena:** တိုက်ပွဲစတင်နေပါပြီ... အနိုင်အရှုံးရလဒ်မှာ..."
    await power_footer(update, text)

async def upgrade_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = "⬆️ ကဒ်များကို ပေါင်းစပ်၍ Level မြှင့်တင်ပြီးပါပြီ!"
    await power_footer(update, text)

async def fav_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = "⭐ Favorite သို့ အောင်မြင်စွာ ထည့်သွင်းပြီး Harem တွင် အပေါ်ဆုံးသို့ တင်လိုက်ပါပြီ။"
    await power_footer(update, text)

# Owner Only Protection
async def owner_check(update: Update) -> bool:
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("⛔ ဤ Command သည် Owner တစ်ဦးတည်းသာ အသုံးပြုနိုင်ပါသည်။")
        return False
    return True

async def addcard_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await owner_check(update): return
    text = "👑 Owner Command: ကဒ်အသစ် ထည့်သွင်းပြီးပါပြီ။"
    await power_footer(update, text)

async def removecard_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await owner_check(update): return
    text = "🗑 Owner Command: ကဒ်ကို ဖျက်ဆီးပြီးပါပြီ။"
    await power_footer(update, text)

async def gcoin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await owner_check(update): return
    text = "💰 Owner Command: User ထံသို့ Coins ထည့်သွင်းပေးပြီးပါပြီ။"
    await power_footer(update, text)
