import sqlite3

class DatabaseManager:
    def __init__(self, db_path="nexus_bot.db"):
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.init_db()

    def init_db(self):
        self.cursor.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            coins INTEGER DEFAULT 1000,
            lang TEXT DEFAULT 'MM',
            is_banned INTEGER DEFAULT 0,
            last_daily INTEGER DEFAULT 0,
            last_claim INTEGER DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS cards (
            card_id TEXT PRIMARY KEY,
            name TEXT,
            rarity_id INTEGER
        );
        CREATE TABLE IF NOT EXISTS inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            card_id TEXT,
            level INTEGER DEFAULT 1,
            exp INTEGER DEFAULT 0,
            is_fav INTEGER DEFAULT 0,
            chat_id INTEGER DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS market (
            listing_id INTEGER PRIMARY KEY AUTOINCREMENT,
            seller_id INTEGER,
            inv_id INTEGER,
            price INTEGER
        );
        CREATE TABLE IF NOT EXISTS approved_groups (
            chat_id INTEGER PRIMARY KEY,
            approved_by INTEGER,
            msg_freq INTEGER DEFAULT 85
        );
        CREATE TABLE IF NOT EXISTS sudo_users (
            user_id INTEGER PRIMARY KEY
        );
        CREATE TABLE IF NOT EXISTS hmode (
            user_id INTEGER PRIMARY KEY,
            tier_filter INTEGER
        );
        CREATE TABLE IF NOT EXISTS blacklist (
            user_id INTEGER PRIMARY KEY
        );
        CREATE TABLE IF NOT EXISTS promo_codes (
            code TEXT PRIMARY KEY,
            reward_coins INTEGER,
            uses_left INTEGER
        );
        CREATE TABLE IF NOT EXISTS bot_settings (
            key TEXT PRIMARY KEY,
            value TEXT
        );
        """)
        self.conn.commit()

db = DatabaseManager()
