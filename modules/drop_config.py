from pyrogram import Client, filters
from pyrogram.types import Message

# ---------------------------------------------------------
# Admin User ID များ ထည့်ပါ
# ---------------------------------------------------------
ADMIN_IDS = [123456789]  # မိမိ၏ Telegram User ID ပြောင်းပါ

# Default ကျနှုန်း ရာခိုင်နှုန်းများ (Database မရှိသေးမီ/မပြောင်းမီ သုံးရန်)
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

# လက်ရှိ Drop Rates များကို Memory တွင် သိမ်းဆည်းထားမည်
CURRENT_DROP_RATES = DEFAULT_DROP_RATES.copy()


def get_current_drop_rates() -> dict:
    """card_spawn.py မှ လှမ်းယူအသုံးပြုရန် Function"""
    return CURRENT_DROP_RATES


# =========================================================
# ၁။ လက်ရှိ ရာခိုင်နှုန်း စာရင်း ကြည့်ရှုသည့် Command (/droprates)
# =========================================================
@Client.on_message(filters.command("droprates"))
async def view_drop_rates(bot: Client, message: Message):
    rates = get_current_drop_rates()
    total_percentage = sum(rates.values())

    text = "📊 **Nexus Catch Bot - Card Drop Rates Configuration**\n\n"
    for idx, (rarity, rate) in enumerate(rates.items(), 1):
        text += f"`{idx}.` **{rarity}:** `{rate}%`\n"

    text += f"\n📈 **Total Rate Sum:** `{total_percentage:.2f}%`"
    if round(total_percentage, 2) != 100.0:
        text += "\n⚠️ *သတိပေးချက်: စုစုပေါင်း ရာခိုင်နှုန်းပေါင်းသည် 100% မပြည့်ပါ သို့မဟုတ် ကျော်လွန်နေပါသည်။*"

    await message.reply_text(text)


# =========================================================
# ၂။ ရာခိုင်နှုန်း ပြင်ဆင်သည့် Command (/setdrop)
# =========================================================
@Client.on_message(filters.command("setdrop") & filters.private)
async def set_drop_rate(bot: Client, message: Message):
    # Admin စစ်ဆေးခြင်း
    if message.from_user.id not in ADMIN_IDS:
        return await message.reply_text("❌ ဤ Command ကို Admin များသာ အသုံးပြုနိုင်ပါသည်။")

    # Command Format: /setdrop [Rarity အမည် သို့မဟုတ် နံပါတ်] | [ရာခိုင်နှုန်း %]
    # ဥပမာ: /setdrop Divine ✨ | 2.5  (သို့မဟုတ်)  /setdrop 8 | 2.5
    try:
        args = message.text.split(maxsplit=1)[1]
        parts = [p.strip() for p in args.split("|")]

        if len(parts) < 2:
            raise ValueError()

        target_input = parts[0]
        new_rate = float(parts[1])

        if new_rate < 0:
            return await message.reply_text("❌ ရာခိုင်နှုန်းသည် 0% ထက် မငယ်ရပါ။")

        # Rarity အမည် သို့မဟုတ် နံပါတ် ရှာဖွေခြင်း
        rarity_keys = list(CURRENT_DROP_RATES.keys())
        matched_rarity = None

        # နံပါတ်ဖြင့် ရိုက်ပါက (ဥပမာ - 1 မှ 13)
        if target_input.isdigit():
            idx = int(target_input) - 1
            if 0 <= idx < len(rarity_keys):
                matched_rarity = rarity_keys[idx]
        else:
            # စာသားဖြင့် ရိုက်ပါက တိုက်ရိုက်ရှာမည်
            for r in rarity_keys:
                if target_input.lower() in r.lower():
                    matched_rarity = r
                    break

        if not matched_rarity:
            return await message.reply_text("❌ Rarity အမည် သို့မဟုတ် နံပါတ် မှားယွင်းနေပါသည်။ `/droprates` ဖြင့် ပြန်စစ်ပါ။")

        # ရာခိုင်နှုန်း ပြောင်းလဲခြင်း
        CURRENT_DROP_RATES[matched_rarity] = new_rate
        
        # MongoDB သို့မဟုတ် Database သုံးပါက ဒီနေရာတွင် DB ထဲ Save လုပ်ပါ:
        # await db.config.update_one({"type": "drop_rates"}, {"$set": {matched_rarity: new_rate}}, upsert=True)

        total_percentage = sum(CURRENT_DROP_RATES.values())

        await message.reply_text(
            f"✅ **Drop Rate အောင်မြင်စွာ ပြောင်းလဲပြီးပါပြီ!**\n\n"
            f"💎 **Rarity:** `{matched_rarity}`\n"
            f"📊 **New Rate:** `{new_rate}%`\n\n"
            f"📈 **Current Total Sum:** `{total_percentage:.2f}%`\n"
            f"*(မသိသေးပါက `/droprates` ဖြင့် ပြန်လည် စစ်ဆေးနိုင်ပါသည်)*"
        )

    except (IndexError, ValueError):
        await message.reply_text(
            "⚠️ **အသုံးပြုပုံ မှားယွင်းနေပါသည်။**\n\n"
            "**Format:**\n"
            "`/setdrop [Rarity အမည် သို့မဟုတ် နံပါတ်] | [ရာခိုင်နှုန်း]`\n\n"
            "**ဥပမာများ:**\n"
            "• `/setdrop Common 🧊 | 35`\n"
            "• `/setdrop Divine ✨ | 2.5`\n"
            "• `/setdrop 13 | 0.1` *(Premium Edition ကို 0.1% ဟု ပြောင်းခြင်း)*"
        )
