import random
from telegram import Update
from telegram.ext import ContextTypes
from config import OWNER_ID

def is_sudo(user_id: int) -> bool:
    return user_id == OWNER_ID

async def check_group_guard(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    if update.effective_chat.type == "private":
        await update.message.reply_text("❌ ဤ Command ကို Group ချတ်များတွင်သာ အသုံးပြုနိုင်ပါသည်။ 🛡️", parse_mode="HTML")
        return False
    return True

def get_weighted_rarity(total_pool_size: int = 100) -> int:
    """
    သင်္ချာစနစ်ဖြင့် ရာခိုင်နှုန်း/စောင်ရေအလိုက် 13 ဆင့် Rarity ခွဲထုတ်ပေးခြင်း
    Tier 1 (Common) မှ Tier 13 (Premium Edition) ထိ အဆင့်သတ်မှတ်ချက်
    """
    # Weights for 13 Tiers (Index 0 to 12)
    weights = [35.0, 22.0, 14.0, 10.0, 7.0, 5.0, 3.0, 2.0, 1.2, 0.5, 0.15, 0.1, 0.05]
    tier = random.choices(range(1, 14), weights=weights)[0]
    return tier

def add_power_footer(text: str) -> str:
    return f"{text}\n\npower by \"maybe\""
