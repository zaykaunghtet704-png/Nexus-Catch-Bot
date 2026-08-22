import sqlite3

DB_NAME = "card_bot.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Users Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            coins INTEGER DEFAULT 500,
            lang TEXT DEFAULT 'my',
            is_banned INTEGER DEFAULT 0
        )
    """)
    
    # Cards Database
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cards (
            card_id TEXT PRIMARY KEY,
            name TEXT,
            rarity_level INTEGER,
            file_id TEXT
        )
    """)
    
    # User Inventory
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            card_id TEXT,
            is_fav INTEGER DEFAULT 0,
            level INTEGER DEFAULT 1
        )
    """)
    
    # Marketplace
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS market (
            listing_id INTEGER PRIMARY KEY AUTOINCREMENT,
            seller_id INTEGER,
            card_id TEXT,
            price INTEGER
        )
    """)
    
    # Group Message Counter & Drop Tracking
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS group_stats (
            chat_id INTEGER PRIMARY KEY,
            msg_count INTEGER DEFAULT 0,
            threshold INTEGER DEFAULT 70,
            active_spawn_id TEXT DEFAULT NULL
        )
    """)
    
    conn.commit()
    conn.close()

def db_query(query, params=(), fetchone=False, fetchall=False, commit=False):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(query, params)
    
    data = None
    if fetchone:
        data = cursor.fetchone()
    elif fetchall:
        data = cursor.fetchall()
        
    if commit:
        conn.commit()
    conn.close()
    return data
