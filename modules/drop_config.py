import os
from pyrogram import Client, filters
from pyrogram.types import Message

# ဆာဗာ Env ထဲက ADMIN_IDS ကို လှမ်းဖတ်ခြင်း (မရှိပါက list လွတ်ထားမည်)
env_admins = os.getenv("ADMIN_IDS", "")
ADMIN_IDS = [int(admin_id.strip()) for admin_id in env_admins.split(",") if admin_id.strip().isdigit()]

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

@Client.on_message(filters.command("droprates"))
async def view_drop_rates(bot: Client, message: Message):
    rates = get_current_drop_rates()
    total_percentage = sum(rates.values())

    text = "📊 **Nexus Catch Bot - Card Drop Rates Configuration**\n\n"
    for idx, (rarity, rate) in enumerate(rates.items(), 1):
        text += f"`{idx}.` **{rarity}:** `{rate}%`\n"

    text += f"\n📈 **Total Rate Sum:** `{total_percentage:.2f}%`"
    await message.reply_text(text)

@Client.on_message(filters.command("setdrop") & filters.private)
async def set_drop_rate(bot: Client, message: Message):
    # ဆာဗာ Env မှ လှမ်းဖတ်ထားသော Admin IDs ထဲတွင် ပါမပါ စစ်ဆေးခြင်း
    if message.from_user.id not in ADMIN_IDS:
        return await message.reply_text("❌ ဤ Command ကို ဆာဗာတွင် သတ်မှတ်ထားသော Admin များသာ အသုံးပြုနိုင်ပါသည်။")

    try:
        args = message.text.split(maxsplit=1)[1]
        parts = [p.strip() for p in args.split("|")]

        if len(parts) < 2:
            raise ValueError()

        target_input = parts[0]
        new_rate = float(parts[1])

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
            return await message.reply_text("❌ Rarity အမည် သို့မဟုတ် နံပါတ် မှားယွင်းနေပါသည်။")

        CURRENT_DROP_RATES[matched_rarity] = new_rate
        total_percentage = sum(CURRENT_DROP_RATES.values())

        await message.reply_text(
            f"✅ **Drop Rate အောင်မြင်စွာ ပြောင်းလဲပြီးပါပြီ!**\n\n"
            f"💎 **Rarity:** `{matched_rarity}`\n"
            f"📊 **New Rate:** `{new_rate}%`\n\n"
            f"📈 **Current Total Sum:** `{total_percentage:.2f}%`"
        )

    except (IndexError, ValueError):
        await message.reply_text(
            "⚠️ **အသုံးပြုပုံ မှားယွင်းနေပါသည်။**\n"
            "`/setdrop [နံပါတ် သို့မဟုတ် အမည်] | [ရာခိုင်နှုန်း]`\n"
            "ဥပမာ: `/setdrop Divine ✨ | 2.5`"
        )
