# services.py
import random
from config import FORCE_JOIN_CHANNELS, RARITIES

async def check_force_join(client, user_id):
    """
    Force join validation logic for channels and groups
    """
    for ch in FORCE_JOIN_CHANNELS:
        try:
            # Pyrogram member check logic placeholder
            pass
        except Exception:
            return False
    return True

def generate_math_challenge_drop(message_count: int):
    """
    စာရေအတွက် 1000 သို့မဟုတ် 1500 ပြည့်မှသာ သင်္ချာပုဒ်စာမေးခွန်းထုတ်ပေးပြီး 
    ကဒ်အမြင့်များကို ကျနှုန်းအလိုက် သတ်မှတ်ပေးသော စနစ်
    """
    if message_count >= 1500:
        num1 = random.randint(50, 99)
        num2 = random.randint(10, 49)
        answer = num1 + num2
        question = f"🧮 **Math Challenge (1500 Messages Milestone):** Solve `{num1} + {num2} = ?` to claim a high-tier card!"
        tier_weights = [10, 15, 20, 15, 10, 10, 8, 6, 3, 2, 1] # High tier chance enabled
    elif message_count >= 1000:
        num1 = random.randint(10, 50)
        num2 = random.randint(1, 20)
        answer = num1 * num2
        question = f"🧮 **Math Challenge (1000 Messages Milestone):** Solve `{num1} × {num2} = ?` to claim your reward!"
        tier_weights = [30, 25, 20, 10, 8, 4, 2, 0.8, 0.1, 0.05, 0.05]
    else:
        return None, None, None

    rarity_keys = list(RARITIES.keys())
    chosen_rarity = random.choices(rarity_keys, weights=tier_weights, k=1)[0]
    return question, answer, chosen_rarity
