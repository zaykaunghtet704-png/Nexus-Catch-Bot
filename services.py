import random
from telegram import ChatMember
from config import REQUIRED_CHANNEL_ID, OWNER_ID
from database import db

async def check_force_join(bot, user_id: int) -> bool:
    try:
        member = await bot.get_chat_member(chat_id=REQUIRED_CHANNEL_ID, user_id=user_id)
        return member.status in [ChatMember.MEMBER, ChatMember.ADMINISTRATOR, ChatMember.OWNER]
    except Exception:
        return True

def is_sudo(user_id: int) -> bool:
    if user_id == OWNER_ID:
        return True
    db.cursor.execute("SELECT user_id FROM sudo_users WHERE user_id = ?", (user_id,))
    return db.cursor.fetchone() is not None

def generate_math_captcha() -> tuple:
    a, b, c = random.randint(1, 9), random.randint(1, 9), random.randint(1, 5)
    ans = a + b + c
    question = f"{a} + {b} + {c} = ?"
    return question, str(ans)
