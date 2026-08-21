import random
from config import OWNER_ID
from database import db

async def check_force_join(user_id: int, context) -> bool:
    return True

async def check_group_guard(update, context) -> bool:
    chat = update.effective_chat
    if chat.type in ["group", "supergroup"]:
        db.cursor.execute("SELECT user_id FROM blacklist WHERE user_id = ?", (update.effective_user.id,))
        if db.cursor.fetchone():
            return False
    return True

def is_sudo(user_id: int) -> bool:
    return user_id == OWNER_ID

def get_weighted_rarity() -> int:
    """
    သင်္ချာပုစ္စာအချိုးကျ (Probability Distribution Function) ဖြင့် ကဒ်အဆင့် ၁၃ ဆင့်ကို 
    စာစောင်ပမာဏအလိုက် အနိမ့်အမြင့် ရာခိုင်နှုန်းခွဲပေးသော ညီမျှခြင်းစနစ်။
    """
    roll = random.uniform(0, 1000)  # 0 to 1000 scale for precision
    
    # 70 စောင်နှုန်းထားကဲ့သို့ အနိမ့်ပိုင်းများတွင် ရာခိုင်နှုန်းများပြီး၊ 700 စောင်နှုန်းထားကဲ့သို့ မြင့်မားရာတွင် အလွန်ခက်ခဲစေရန်
    if roll < 300:      return 1   # Common (~30%)
    elif roll < 500:    return 2   # Uncommon (~20%)
    elif roll < 650:    return 3   # Rare (~15%)
    elif roll < 770:    return 4   # Epic (~12%)
    elif roll < 860:    return 5   # Legendary (~9%)
    elif roll < 920:    return 6   # Mythic (~6%)
    elif roll < 960:    return 7   # Celestial (~4%)
    elif roll < 980:    return 8   # Divine (~2%)
    elif roll < 990:    return 9   # Radiant (~1%)
    elif roll < 995:    return 10  # Supreme (~0.5%)
    elif roll < 998:    return 11  # Immortal (~0.3%)
    elif roll < 999.5:  return 12  # Exclusive (~0.15%)
    else:               return 13  # Premium Edition (~0.05%)

def add_power_footer(text: str) -> str:
    """အမိန့်ပေးတိုင်း power by 'maybe' ကို ထည့်သွင်းပေးသော Function"""
    return f"{text}\n\n<i>⚡ power by \"maybe\"</i>"
