import sqlite3
from datetime import date

DB_NAME = "cardbot.db"


def db():
    return sqlite3.connect(DB_NAME)


def init_db():
    conn = db()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT DEFAULT '',
            coins INTEGER DEFAULT 100,
            xp INTEGER DEFAULT 0,
            level INTEGER DEFAULT 1,
            last_daily TEXT DEFAULT ''
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS cards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            edition TEXT NOT NULL,
            price INTEGER DEFAULT 0,
            image_type TEXT DEFAULT '',
            file_id TEXT DEFAULT ''
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS collection (
            user_id INTEGER,
            card_id INTEGER,
            amount INTEGER DEFAULT 1,
            PRIMARY KEY (user_id, card_id)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS drops (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            card_id INTEGER NOT NULL,
            claimed_by INTEGER DEFAULT NULL,
            active INTEGER DEFAULT 1
        )
    """)

    conn.commit()
    conn.close()


def create_user(user_id, username):
    conn = db()
    cur = conn.cursor()

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
    else:
        cur.execute(
            """
            UPDATE users
            SET username = ?
            WHERE user_id = ?
            """,
            (username or "", user_id)
        )

    conn.commit()
    conn.close()


def get_user(user_id):
    conn = db()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT user_id, username, coins, xp, level
        FROM users
        WHERE user_id = ?
        """,
        (user_id,)
    )

    result = cur.fetchone()
    conn.close()

    return result


def add_card(user_id, card_id):
    conn = db()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT amount
        FROM collection
        WHERE user_id = ? AND card_id = ?
        """,
        (user_id, card_id)
    )

    result = cur.fetchone()

    if result:
        cur.execute(
            """
            UPDATE collection
            SET amount = amount + 1
            WHERE user_id = ? AND card_id = ?
            """,
            (user_id, card_id)
        )
    else:
        cur.execute(
            """
            INSERT INTO collection (user_id, card_id, amount)
            VALUES (?, ?, 1)
            """,
            (user_id, card_id)
        )

    conn.commit()
    conn.close()


def create_drop(card_id):
    conn = db()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO drops (card_id)
        VALUES (?)
        """,
        (card_id,)
    )

    drop_id = cur.lastrowid

    conn.commit()
    conn.close()

    return drop_id


def claim_drop(drop_id, user_id):
    """
    First-click protection.

    UPDATE ကို active=1 ဖြစ်နေမှ လုပ်တာကြောင့်
    လူအများကြီး တစ်ပြိုင်နက်နှိပ်လည်း
    User တစ်ယောက်ပဲ အောင်မြင်နိုင်ပါတယ်။
    """

    conn = db()
    cur = conn.cursor()

    cur.execute(
        """
        UPDATE drops
        SET claimed_by = ?, active = 0
        WHERE id = ?
          AND active = 1
          AND claimed_by IS NULL
        """,
        (user_id, drop_id)
    )

    success = cur.rowcount == 1

    conn.commit()
    conn.close()

    if success:
        add_card(user_id, get_drop_card_id(drop_id))

    return success


def get_drop_card_id(drop_id):
    conn = db()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT card_id
        FROM drops
        WHERE id = ?
        """,
        (drop_id,)
    )

    result = cur.fetchone()
    conn.close()

    return result[0] if result else None


def get_card(card_id):
    conn = db()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT id, name, edition, price, image_type, file_id
        FROM cards
        WHERE id = ?
        """,
        (card_id,)
    )

    result = cur.fetchone()
    conn.close()

    return result


def get_random_card():
    conn = db()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT id, name, edition, price, image_type, file_id
        FROM cards
        ORDER BY RANDOM()
        LIMIT 1
        """
    )

    result = cur.fetchone()
    conn.close()

    return result


def get_collection(user_id):
    conn = db()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT
            cards.name,
            cards.edition,
            cards.price,
            collection.amount
        FROM collection
        JOIN cards
            ON cards.id = collection.card_id
        WHERE collection.user_id = ?
        ORDER BY cards.id DESC
        """,
        (user_id,)
    )

    result = cur.fetchall()
    conn.close()

    return result


def daily_reward(user_id):
    today = str(date.today())

    conn = db()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT last_daily
        FROM users
        WHERE user_id = ?
        """,
        (user_id,)
    )

    result = cur.fetchone()

    if result and result[0] == today:
        conn.close()
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

    conn.commit()
    conn.close()

    return True
