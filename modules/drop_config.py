import os
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler

# ဆာဗာ Env ထဲက ADMIN_IDS ကို ဖတ်ခြင်း
env_admins = os.getenv("ADMIN_IDS", "")
ADMIN_IDS = [int(x.strip()) for x in env_admins.split(",") if x.strip().isdigit()]

# Default ကျနှုန်း ရာခိုင်နှုန်းများ
DEFAULT_DROP_RATES = {
    "Common 🧊": 40.0,
    "Uncommon 🟢": 25.0,
    "Rare 🔵": 15.0,
    "Super Rare 🟣": 8.0,
    "Epic 🌟": 5.0,
    "Legendary 🟡": 3.0,
    "Mythic 🔴": 1.5,
    "Divine ✨": 1.0,
    "Celestial 🌌": 0.6,
    "Immortal 💠": 0.4,
    "Supreme 👑": 0.2,
    "Ultimate 🌠": 0.1,
    "Premium Edition 💎": 0.05
}

CURRENT_DROP_RATES = DEFAULT_DROP_RATES.copy()

def get_current_drop_rates() -> dict:
    return CURRENT_DROP_RATES

# ==========================================
# 📊 /droprates Command
# ==========================================
async def droprates_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    rates = get_current_drop_rates()
    total_percentage = sum(rates.values())

    text = "📊 **Nexus Catch Bot - Card Drop Rates**\n\n"
    for idx, (rarity, rate) in enumerate(rates.items(), 1):
        text += f"`{idx}.` **{rarity}:** `{rate}%`\n"

    text += f"\n📈 **Total Sum:** `{total_percentage:.2f}%`"
    await update.message.reply_text(text, parse_mode="Markdown")

# ==========================================
# ⚙️ /setdrop Command
# ==========================================
async def setdrop_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("❌ ဤ Command ကို Admin များသာ အသုံးပြုနိုင်ပါသည်။")
        return

    try:
        args = " ".join(context.args)
        parts = [p.strip() for p in args.split("|")]

        if len(parts) < 2:
            raise ValueError()

        target_input = parts[0]
        new_rate = float(parts[1])

        if new_rate < 0:
            await update.message.reply_text("❌ ရာခိုင်နှုန်းသည် 0% ထက် မငယ်ရပါ။")
            return

        rarity_keys = list(CURRENT_DROP_RATES.keys())
        matched_rarity = None

        if target_input.isdigit():
            idx = int(target_input) - 1
            if 0 <= idx < len(rarity_keys):
                matched_rarity = rarity_keys[idx]
        else:
            for r in rarity_keys:
                if target_input.lower() in r.lower():
                    matched_rarity = r
                    break

        if not matched_rarity:
            await update.message.reply_text("❌ Rarity အမည် သို့မဟုတ် နံပါတ် မှားယွင်းနေပါသည်။")
            return

        CURRENT_DROP_RATES[matched_rarity] = new_rate
        total_percentage = sum(CURRENT_DROP_RATES.values())

        await update.message.reply_text(
            f"✅ **Drop Rate အောင်မြင်စွာ ပြောင်းလဲပြီးပါပြီ!**\n\n"
            f"💎 **Rarity:** `{matched_rarity}`\n"
            f"📊 **New Rate:** `{new_rate}%`\n\n"
            f"📈 **Total Sum:** `{total_percentage:.2f}%`",
            parse_mode="Markdown"
        )

    except (IndexError, ValueError):
        await update.message.reply_text(
            "⚠️ **အသုံးပြုပုံ မှားယွင်းနေပါသည်။**\n\n"
            "**Format:** `/setdrop [နံပါတ် သို့မဟုတ် အမည်] | [ရာခိုင်နှုန်း]`\n"
            "**ဥပမာ:** `/setdrop Divine ✨ | 2.5` (သို့) `/setdrop 8 | 2.5`",
            parse_mode="Markdown"
        )

def get_spawn_settings_handlers():
    return [
        CommandHandler("droprates", droprates_command),
        CommandHandler("setdrop", setdrop_command),
    ]
