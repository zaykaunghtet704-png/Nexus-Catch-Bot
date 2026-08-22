import sqlite3

class Database:
    def __init__(self, db_name="nexus_bot.db"):
        self.conn = sqlite3.connect(db_name, check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.setup_tables()

    def setup_tables(self):
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                coins INTEGER DEFAULT 0,
                last_daily TEXT,
                last_claim TEXT
            )
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS cards (
                card_id TEXT PRIMARY KEY,
                name TEXT,
                rarity_id INTEGER,
                image_url TEXT
            )
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS inventory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                card_id TEXT,
                chat_id INTEGER,
                level INTEGER DEFAULT 1,
                is_fav INTEGER DEFAULT 0,
                FOREIGN KEY(card_id) REFERENCES cards(card_id)
            )
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS market (
                listing_id INTEGER PRIMARY KEY AUTOINCREMENT,
                seller_id INTEGER,
                inv_id INTEGER,
                price INTEGER
            )
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS hmode (
                user_id INTEGER PRIMARY KEY,
                tier_filter INTEGER
            )
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS blacklist (
                user_id INTEGER PRIMARY KEY
            )
        """)
        self.conn.commit()

db = Database()
