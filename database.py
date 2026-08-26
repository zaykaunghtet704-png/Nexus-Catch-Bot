import sqlite3
from datetime import date

DB_NAME = "cardbot.db"


def connect():
    return sqlite3.connect(DB_NAME)


def init_db():
    db = connect()
    cur = db.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            coins INTEGER DEFAULT 100,
            xp INTEGER DEFAULT 0,
            level INTEGER DEFAULT 1,
            last_daily TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS cards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            rarity TEXT NOT NULL,
            image_url TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS user_cards (
            user_id INTEGER,
            card_id INTEGER,
            amount INTEGER DEFAULT 1,
            PRIMARY KEY (user_id, card_id)
        )
    """)

    db.commit()
    db.close()


def create_user(user_id, username):
    db = connect()
    cur = db.cursor()

    cur.execute(
        "SELECT user_id FROM users WHERE user_id = ?",
        (user_id,)
    )

    if cur.fetchone() is None:
        cur.execute(
            """
            INSERT INTO users (user_id, username)
            VALUES (?, ?)
            """,
            (user_id, username or "")
        )

    db.commit()
    db.close()


def get_user(user_id):
    db = connect()
    cur = db.cursor()

    cur.execute(
        "SELECT * FROM users WHERE user_id = ?",
        (user_id,)
    )

    result = cur.fetchone()
    db.close()

    return result


def add_card_to_user(user_id, card_id):
    db = connect()
    cur = db.cursor()

    cur.execute(
        """
        SELECT amount FROM user_cards
        WHERE user_id = ? AND card_id = ?
        """,
        (user_id, card_id)
    )

    result = cur.fetchone()

    if result:
        cur.execute(
            """
            UPDATE user_cards
            SET amount = amount + 1
            WHERE user_id = ? AND card_id = ?
            """,
            (user_id, card_id)
        )
    else:
        cur.execute(
            """
            INSERT INTO user_cards (user_id, card_id, amount)
            VALUES (?, ?, 1)
            """,
            (user_id, card_id)
        )

    db.commit()
    db.close()


def get_collection(user_id):
    db = connect()
    cur = db.cursor()

    cur.execute(
        """
        SELECT cards.name, cards.rarity, user_cards.amount
        FROM user_cards
        JOIN cards ON cards.id = user_cards.card_id
        WHERE user_cards.user_id = ?
        ORDER BY cards.rarity, cards.name
        """,
        (user_id,)
    )

    result = cur.fetchall()
    db.close()

    return result


def claim_daily(user_id):
    db = connect()
    cur = db.cursor()

    today = str(date.today())

    cur.execute(
        "SELECT last_daily FROM users WHERE user_id = ?",
        (user_id,)
    )

    result = cur.fetchone()

    if result and result[0] == today:
        db.close()
        return False

    cur.execute(
        """
        UPDATE users
        SET coins = coins + 100,
            xp = xp + 20,
            last_daily = ?
        WHERE user_id = ?
        """,
        (today, user_id)
    )

    db.commit()
    db.close()

    return True
