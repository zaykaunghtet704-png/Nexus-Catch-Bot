import sqlite3
from datetime import date


DB_NAME = "cardbot.db"


def get_db():
    conn = sqlite3.connect(
        DB_NAME,
        timeout=15
    )

    conn.execute(
        "PRAGMA journal_mode=WAL"
    )

    conn.execute(
        "PRAGMA foreign_keys=ON"
    )

    return conn


def init_db():

    conn = get_db()
    cur = conn.cursor()

    # =========================
    # USERS
    # =========================

    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT DEFAULT '',
            first_name TEXT DEFAULT '',
            coins INTEGER NOT NULL DEFAULT 100,
            xp INTEGER NOT NULL DEFAULT 0,
            level INTEGER NOT NULL DEFAULT 1,
            last_daily TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # =========================
    # CARDS
    # =========================

    cur.execute("""
        CREATE TABLE IF NOT EXISTS cards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            edition TEXT NOT NULL,
            price INTEGER NOT NULL DEFAULT 0,
            drop_rate REAL NOT NULL DEFAULT 0,
            description TEXT DEFAULT '',
            media_type TEXT DEFAULT '',
            file_id TEXT DEFAULT '',
            limited INTEGER NOT NULL DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # =========================
    # COLLECTION
    # =========================

    cur.execute("""
        CREATE TABLE IF NOT EXISTS collection (
            user_id INTEGER NOT NULL,
            card_id INTEGER NOT NULL,
            amount INTEGER NOT NULL DEFAULT 1,

            PRIMARY KEY (
                user_id,
                card_id
            ),

            FOREIGN KEY(user_id)
                REFERENCES users(user_id)
                ON DELETE CASCADE,

            FOREIGN KEY(card_id)
                REFERENCES cards(id)
                ON DELETE CASCADE
        )
    """)

    # =========================
    # DROPS
    # =========================

    cur.execute("""
        CREATE TABLE IF NOT EXISTS drops (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            card_id INTEGER NOT NULL,
            claimed_by INTEGER DEFAULT NULL,
            active INTEGER NOT NULL DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY(card_id)
                REFERENCES cards(id)
                ON DELETE CASCADE
        )
    """)

    # =========================
    # TRANSACTIONS
    # =========================

    cur.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            from_user INTEGER,
            to_user INTEGER,
            amount INTEGER NOT NULL,
            type TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()


# ==================================================
# USER
# ==================================================

def create_user(
    user_id: int,
    username: str = "",
    first_name: str = ""
):

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO users (
            user_id,
            username,
            first_name
        )
        VALUES (?, ?, ?)

        ON CONFLICT(user_id)
        DO UPDATE SET
            username = excluded.username,
            first_name = excluded.first_name
        """,
        (
            user_id,
            username or "",
            first_name or ""
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
            first_name,
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


# ==================================================
# XP / LEVEL
# ==================================================

def add_xp(user_id: int, amount: int):

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT xp, level
        FROM users
        WHERE user_id = ?
        """,
        (user_id,)
    )

    result = cur.fetchone()

    if not result:
        conn.close()
        return None

    xp, level = result

    xp += amount

    new_level = max(
        1,
        (xp // 100) + 1
    )

    cur.execute(
        """
        UPDATE users
        SET
            xp = ?,
            level = ?
        WHERE user_id = ?
        """,
        (
            xp,
            new_level,
            user_id
        )
    )

    conn.commit()
    conn.close()

    return new_level


# ==================================================
# COINS
# ==================================================

def add_coins(
    user_id: int,
    amount: int
):

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        """
        UPDATE users
        SET coins = coins + ?
        WHERE user_id = ?
        """,
        (
            amount,
            user_id
        )
    )

    changed = cur.rowcount > 0

    conn.commit()
    conn.close()

    return changed


def transfer_coins(
    from_user: int,
    to_user: int,
    amount: int
):

    if amount <= 0:
        return False, "INVALID_AMOUNT"

    if from_user == to_user:
        return False, "SELF_TRANSFER"

    conn = get_db()
    cur = conn.cursor()

    try:

        cur.execute("BEGIN IMMEDIATE")

        cur.execute(
            """
            SELECT coins
            FROM users
            WHERE user_id = ?
            """,
            (from_user,)
        )

        sender = cur.fetchone()

        if not sender:
            conn.rollback()
            return False, "SENDER_NOT_FOUND"

        cur.execute(
            """
            SELECT user_id
            FROM users
            WHERE user_id = ?
            """,
            (to_user,)
        )

        receiver = cur.fetchone()

        if not receiver:
            conn.rollback()
            return False, "RECEIVER_NOT_FOUND"

        if sender[0] < amount:
            conn.rollback()
            return False, "INSUFFICIENT"

        cur.execute(
            """
            UPDATE users
            SET coins = coins - ?
            WHERE user_id = ?
            """,
            (
                amount,
                from_user
            )
        )

        cur.execute(
            """
            UPDATE users
            SET coins = coins + ?
            WHERE user_id = ?
            """,
            (
                amount,
                to_user
            )
        )

        cur.execute(
            """
            INSERT INTO transactions (
                from_user,
                to_user,
                amount,
                type
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                from_user,
                to_user,
                amount,
                "TRANSFER"
            )
        )

        conn.commit()

        return True, "OK"

    except Exception:

        conn.rollback()
        raise

    finally:

        conn.close()


# ==================================================
# DAILY
# ==================================================

def claim_daily(user_id: int):

    today = str(date.today())

    conn = get_db()
    cur = conn.cursor()

    try:

        cur.execute("BEGIN IMMEDIATE")

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
            conn.rollback()
            return False

        if result[0] == today:
            conn.rollback()
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

        return True

    except Exception:

        conn.rollback()
        raise

    finally:

        conn.close()


# ==================================================
# CARDS
# ==================================================

def create_card(
    name,
    edition,
    price,
    drop_rate,
    description="",
    media_type="",
    file_id="",
    limited=0
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
            file_id,
            limited
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            name,
            edition,
            price,
            drop_rate,
            description,
            media_type,
            file_id,
            limited
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
            file_id,
            limited
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
            file_id,
            limited
        FROM cards
        ORDER BY id DESC
        """
    )

    result = cur.fetchall()

    conn.close()

    return result


def get_drop_cards():

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
            file_id,
            limited
        FROM cards
        WHERE drop_rate > 0
        """
    )

    result = cur.fetchall()

    conn.close()

    return result


def update_card(
    card_id,
    name=None,
    edition=None,
    price=None,
    drop_rate=None,
    description=None,
    media_type=None,
    file_id=None,
    limited=None
):

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT
            name,
            edition,
            price,
            drop_rate,
            description,
            media_type,
            file_id,
            limited
        FROM cards
        WHERE id = ?
        """,
        (card_id,)
    )

    old = cur.fetchone()

    if not old:
        conn.close()
        return False

    (
        old_name,
        old_edition,
        old_price,
        old_rate,
        old_description,
        old_media_type,
        old_file_id,
        old_limited
    ) = old

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
            file_id = ?,
            limited = ?
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
            limited if limited is not None else old_limited,
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


# ==================================================
# COLLECTION
# ==================================================

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
        DO UPDATE SET
            amount = amount + 1
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
            cards.media_type,
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


# ==================================================
# DROPS
# ==================================================

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
            DO UPDATE SET
                amount = amount + 1
            """,
            (
                user_id,
                card_id
            )
        )

        cur.execute(
            """
            UPDATE users
            SET
                xp = xp + 10
            WHERE user_id = ?
            """,
            (user_id,)
        )

        conn.commit()

        return card_id

    except Exception:

        conn.rollback()
        raise

    finally:

        conn.close()
