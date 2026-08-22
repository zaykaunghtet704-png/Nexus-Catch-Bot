import sqlite3
import random
from config import RARITY_TIERS

def init_db():
    conn = sqlite3.connect("bot_database.db")
    cursor = conn.cursor()
    # Users Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            coins INTEGER DEFAULT 500,
            lang TEXT DEFAULT 'my'
        )
    """)
    # Cards Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cards (
            card_id TEXT PRIMARY KEY,
            name TEXT,
            rarity TEXT,
            file_id TEXT
        )
    """)
    # User Inventory Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            card_id TEXT,
            level INTEGER DEFAULT 1,
            is_fav INTEGER DEFAULT 0
        )
    """)
    # Market Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS market (
            listing_id INTEGER PRIMARY KEY AUTOINCREMENT,
            seller_id INTEGER,
            card_db_id INTEGER,
            price INTEGER
        )
    """)
    # Group Message Counter for Changetime
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS group_messages (
            chat_id INTEGER PRIMARY KEY,
            msg_count INTEGER DEFAULT 0,
            target_limit INTEGER DEFAULT 70
        )
    """)
    conn.commit()
    conn.close()

def get_rarity_by_messages(msg_count, target_limit):
    """
    သင်္ချာပုဒ်စာနှင့် အဆင့်မြင့် ကဒ်ချပေးသော ရာခိုင်နှုန်းစနစ်
    စာစောင် 70 လျှင် တစ်ကဒ် (Common များများ)၊ 700 ပြည့်ပါက အဆင့်မြင့်ကဒ်များ ထွက်ရန် တွက်ချက်သည်။
    """
    ratio = min(msg_count / target_limit, 1.0)
    # Weighted random based on ratio
    tier_index = int(ratio * (len(RARITY_TIERS) - 1))
    # Add some randomness to make it exciting
    variance = random.choice([-1, 0, 1])
    final_index = max(0, min(len(RARITY_TIERS) - 1, tier_index + variance))
    return RARITY_TIERS[final_index]
