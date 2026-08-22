import random
from database import get_db
from config import RARITY_LEVELS

async def check_force_join(bot, user_id):
    # Force join verification placeholder for group and channel
    return True

def calculate_card_drop(chat_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT message_count, drop_threshold FROM group_stats WHERE chat_id = ?", (chat_id,))
    row = cursor.fetchone()
    
    if not row:
        cursor.execute("INSERT INTO group_stats (chat_id, message_count, drop_threshold) VALUES (?, 1, 70)", (chat_id,))
        conn.commit()
        conn.close()
        return False, None
    
    count, threshold = row
    count += 1
    
    if count >= threshold:
        # Math formula to randomize higher cards when threshold reaches 70 to 700
        new_threshold = random.randint(70, 700)
        cursor.execute("UPDATE group_stats SET message_count = 0, drop_threshold = ? WHERE chat_id = ?", (new_threshold, chat_id))
        conn.commit()
        conn.close()
        
        rand_val = random.uniform(0, 100)
        cumulative = 0
        selected_rarity = RARITY_LEVELS[0]["name"]
        for r in RARITY_LEVELS:
            cumulative += r["rate"]
            if rand_val <= cumulative:
                selected_rarity = r["name"]
                break
        return True, selected_rarity
    else:
        cursor.execute("UPDATE group_stats SET message_count = ? WHERE chat_id = ?", (count, chat_id))
        conn.commit()
        conn.close()
        return False, None
