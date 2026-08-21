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
            rarity_id INTEGER,
            img_url TEXT,
            hp INTEGER DEFAULT 100,
            atk INTEGER DEFAULT 20,
            def_stat INTEGER DEFAULT 10
        );
        CREATE TABLE IF NOT EXISTS inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            card_id TEXT,
            mint_rate REAL,
            serial_no INTEGER,
            level INTEGER DEFAULT 1,
            exp INTEGER DEFAULT 0,
            is_fav INTEGER DEFAULT 0,
            frame TEXT DEFAULT 'Default',
            dye TEXT DEFAULT '#FFFFFF',
            font TEXT DEFAULT 'Default',
            obtained_time INTEGER
        );
        CREATE TABLE IF NOT EXISTS approved_groups (
            chat_id INTEGER PRIMARY KEY,
            msg_limit INTEGER DEFAULT 85,
            msg_counter INTEGER DEFAULT 0,
            current_spawn TEXT DEFAULT NULL,
            captcha_ans TEXT DEFAULT NULL
        );
        CREATE TABLE IF NOT EXISTS hmode (
            user_id INTEGER PRIMARY KEY,
            tier_filter INTEGER
        );
        """)
        self.conn.commit()

db = DatabaseManager()
