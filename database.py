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
            balance INTEGER DEFAULT 500,
            lang TEXT DEFAULT 'MM',
            is_banned INTEGER DEFAULT 0,
            last_claim INTEGER DEFAULT 0,
            last_nclaim INTEGER DEFAULT 0,
            last_daily INTEGER DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS sudo_users (
            user_id INTEGER PRIMARY KEY
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
            mint_rate REAL,
            serial_no INTEGER,
            is_fav INTEGER DEFAULT 0,
            dye TEXT DEFAULT '#FFFFFF',
            obtained_time INTEGER
        );
        CREATE TABLE IF NOT EXISTS hmode (
            user_id INTEGER PRIMARY KEY,
            tier_filter INTEGER
        );
        """)
        self.conn.commit()

db = DatabaseManager()
