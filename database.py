import sqlite3
from datetime import date


DB_NAME = "cardbot.db"


def get_db():
    conn = sqlite3.connect(
        DB_NAME,
        timeout=10
    )

    conn.execute(
        "PRAGMA journal_mode=WAL"
    )

    return conn


def init_db():
    conn = get_db()
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
            drop_rate REAL DEFAULT 0,
            description TEXT DEFAULT '',
            media_type TEXT DEFAULT '',
            file_id TEXT DEFAULT ''
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS collection (
            user_id INTEGER NOT NULL,
            card_id INTEGER NOT NULL,
            amount INTEGER DEFAULT 1,
            PRIMARY KEY (user_id, card_id)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS drops (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            card_id INTEGER NOT NULL,
            claimed_by INTEGER DEFAULT NULL,
            active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()


# =========================
# USERS
# =========================

def create_user(
    user_id: int,
    username: str
):
    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO users (
            user_id,
            username
        )
        VALUES (?, ?)
        ON CONFLICT(user_id)
        DO UPDATE SET username = excluded.username
        """,
        (
            user_id,
            username or ""
        )
    )

    conn.commit()
    conn.close()


def get_user(user_id: int):
    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT
            user_id,
            username,
            coins,
            xp,
            level,
            last_daily
        FROM users
        WHERE user_id = ?
        """,
        (user_id,)
    )

    result = cur.fetchone()

    conn.close()

    return result


# =========================
# CARDS
# =========================

def create_card(
    name: str,
    edition: str,
    price: int,
    drop_rate: float,
    description: str = "",
    media_type: str = "",
    file_id: str = ""
):
    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO cards (
            name,
            edition,
            price,
            drop_rate,
            description,
            media_type,
            file_id
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            name,
            edition,
            price,
            drop_rate,
            description,
            media_type,
            file_id
        )
    )

    card_id = cur.lastrowid

    conn.commit()
    conn.close()

    return card_id


def get_card(card_id: int):
    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT
            id,
            name,
            edition,
            price,
            drop_rate,
            description,
            media_type,
            file_id
        FROM cards
        WHERE id = ?
        """,
        (card_id,)
    )

    result = cur.fetchone()

    conn.close()

    return result


def get_all_cards():
    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT
            id,
            name,
            edition,
            price,
            drop_rate,
            description,
            media_type,
            file_id
        FROM cards
        ORDER BY id DESC
        """
    )

    result = cur.fetchall()

    conn.close()

    return result


def update_card(
    card_id: int,
    name=None,
    edition=None,
    price=None,
    drop_rate=None,
    description=None,
    media_type=None,
    file_id=None
):
    conn = get_db()
    cur = conn.cursor()

    current = get_card(card_id)

    if not current:
        conn.close()
        return False

    (
        _id,
        old_name,
        old_edition,
        old_price,
        old_rate,
        old_description,
        old_media_type,
        old_file_id
    ) = current

    cur.execute(
        """
        UPDATE cards
        SET
            name = ?,
            edition = ?,
            price = ?,
            drop_rate = ?,
            description = ?,
            media_type = ?,
            file_id = ?
        WHERE id = ?
        """,
        (
            name if name is not None else old_name,
            edition if edition is not None else old_edition,
            price if price is not None else old_price,
            drop_rate if drop_rate is not None else old_rate,
            description if description is not None else old_description,
            media_type if media_type is not None else old_media_type,
            file_id if file_id is not None else old_file_id,
            card_id
        )
    )

    conn.commit()
    conn.close()

    return True


def delete_card(card_id: int):
    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        """
        DELETE FROM cards
        WHERE id = ?
        """,
        (card_id,)
    )

    deleted = cur.rowcount > 0

    conn.commit()
    conn.close()

    return deleted


def get_random_card():
    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT
            id,
            name,
            edition,
            price,
            drop_rate,
            description,
            media_type,
            file_id
        FROM cards
        ORDER BY RANDOM()
        LIMIT 1
        """
    )

    result = cur.fetchone()

    conn.close()

    return result


# =========================
# COLLECTION
# =========================

def add_card_to_collection(
    user_id: int,
    card_id: int
):
    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO collection (
            user_id,
            card_id,
            amount
        )
        VALUES (?, ?, 1)
        ON CONFLICT(user_id, card_id)
        DO UPDATE SET amount = amount + 1
        """,
        (
            user_id,
            card_id
        )
    )

    conn.commit()
    conn.close()


def get_collection(user_id: int):
    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT
            cards.id,
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


# =========================
# DROP
# =========================

def create_drop(card_id: int):
    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO drops (
            card_id,
            active
        )
        VALUES (?, 1)
        """,
        (card_id,)
    )

    drop_id = cur.lastrowid

    conn.commit()
    conn.close()

    return drop_id


def claim_drop(
    drop_id: int,
    user_id: int
):
    conn = get_db()
    cur = conn.cursor()

    try:
        cur.execute("BEGIN IMMEDIATE")

        cur.execute(
            """
            SELECT
                card_id,
                claimed_by,
                active
            FROM drops
            WHERE id = ?
            """,
            (drop_id,)
        )

        drop = cur.fetchone()

        if not drop:
            conn.rollback()
            return None

        card_id, claimed_by, active = drop

        if not active or claimed_by is not None:
            conn.rollback()
            return None

        cur.execute(
            """
            UPDATE drops
            SET
                claimed_by = ?,
                active = 0
            WHERE id = ?
              AND active = 1
              AND claimed_by IS NULL
            """,
            (
                user_id,
                drop_id
            )
        )

        if cur.rowcount != 1:
            conn.rollback()
            return None

        cur.execute(
            """
            INSERT INTO collection (
                user_id,
                card_id,
                amount
            )
            VALUES (?, ?, 1)
            ON CONFLICT(user_id, card_id)
            DO UPDATE SET amount = amount + 1
            """,
            (
                user_id,
                card_id
            )
        )

        conn.commit()

        return card_id

    except Exception:
        conn.rollback()
        raise

    finally:
        conn.close()


# =========================
# DAILY
# =========================

def claim_daily(user_id: int):
    today = str(date.today())

    conn = get_db()
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

    if not result:
        conn.close()
        return False

    if result[0] == today:
        conn.close()
        return False

    cur.execute(
        """
        UPDATE users
        SET
            coins = coins + 100,
            xp = xp + 20,
            last_daily = ?
        WHERE user_id = ?
        """,
        (
            today,
            user_id
        )
    )

    conn.commit()
    conn.close()

    return True
