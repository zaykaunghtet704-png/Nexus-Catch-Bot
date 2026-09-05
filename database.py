import os
import sqlite3
import threading
import time
from contextlib import contextmanager

from config import DATABASE_PATH


# ============================================================
# SQLITE CONFIGURATION
# ============================================================

# Make sure the database directory exists when DATABASE_PATH
# contains a directory.
_db_dir = os.path.dirname(os.path.abspath(DATABASE_PATH))
if _db_dir:
    os.makedirs(_db_dir, exist_ok=True)


# One Render worker normally runs one bot process.
# This lock prevents simultaneous SQLite transactions inside
# the same bot process.
_DB_LOCK = threading.RLock()


def _connect():
    """
    Create a SQLite connection configured for concurrent bot use.
    """
    conn = sqlite3.connect(
        DATABASE_PATH,
        timeout=30.0,
        check_same_thread=False,
    )

    conn.row_factory = sqlite3.Row

    # Wait up to 30 seconds when another transaction has the DB locked.
    conn.execute("PRAGMA busy_timeout = 30000")

    # WAL allows readers while a writer is working and is much safer
    # for a Telegram bot than the default rollback journal.
    conn.execute("PRAGMA journal_mode = WAL")

    # Good balance between speed and durability for this bot.
    conn.execute("PRAGMA synchronous = NORMAL")

    # Foreign-key enforcement.
    conn.execute("PRAGMA foreign_keys = ON")

    return conn


@contextmanager
def get_db():
    """
    Safe SQLite transaction context.

    Every database operation gets its own connection and transaction.
    The process-level lock prevents two bot handlers from writing
    through SQLite at the exact same time.
    """
    with _DB_LOCK:
        conn = None

        try:
            conn = _connect()
            yield conn
            conn.commit()

        except sqlite3.OperationalError as exc:
            if conn is not None:
                try:
                    conn.rollback()
                except Exception:
                    pass

            # The connection timeout + busy_timeout normally handles
            # locking. This message makes the Render log easier to read.
            if "locked" in str(exc).lower():
                raise sqlite3.OperationalError(
                    "SQLite database remained locked after waiting 30 seconds."
                ) from exc

            raise

        except Exception:
            if conn is not None:
                try:
                    conn.rollback()
                except Exception:
                    pass
            raise

        finally:
            if conn is not None:
                conn.close()


# ============================================================
# DATABASE INITIALIZATION
# ============================================================

def init_db():
    with get_db() as db:

        # =========================
        # Users
        # =========================
        db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT DEFAULT '',
                first_name TEXT DEFAULT '',
                language TEXT DEFAULT 'my',
                coins INTEGER DEFAULT 0,
                exp INTEGER DEFAULT 0,
                level INTEGER DEFAULT 1,
                daily_claim INTEGER DEFAULT 0,
                claim_count_24h INTEGER DEFAULT 0,
                last_claim REAL DEFAULT 0,
                created_at REAL DEFAULT 0
            )
        """)

        # =========================
        # Groups
        # =========================
        db.execute("""
            CREATE TABLE IF NOT EXISTS groups (
                group_id INTEGER PRIMARY KEY,
                title TEXT DEFAULT '',
                member_count INTEGER DEFAULT 0,
                bot_is_admin INTEGER DEFAULT 0,
                owner_approved INTEGER DEFAULT 0,
                enabled INTEGER DEFAULT 0,
                added_by INTEGER DEFAULT 0,
                created_at REAL DEFAULT 0
            )
        """)

        # =========================
        # Cards
        # =========================
        db.execute("""
            CREATE TABLE IF NOT EXISTS cards (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                char_id TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                edition TEXT DEFAULT 'Common',
                rarity INTEGER DEFAULT 1,
                price INTEGER DEFAULT 0,
                image_file_id TEXT DEFAULT '',
                video_file_id TEXT DEFAULT '',
                media_type TEXT DEFAULT 'photo',
                description TEXT DEFAULT '',
                drop_weight REAL DEFAULT 1,
                exp_reward INTEGER DEFAULT 0,
                created_at REAL DEFAULT 0,
                active INTEGER DEFAULT 1
            )
        """)

        # =========================
        # User Collection
        # =========================
        db.execute("""
            CREATE TABLE IF NOT EXISTS user_cards (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                char_id TEXT NOT NULL,
                level INTEGER DEFAULT 1,
                exp INTEGER DEFAULT 0,
                favorite INTEGER DEFAULT 0,
                obtained_at REAL DEFAULT 0
            )
        """)

        # =========================
        # Drop Events
        # =========================
        db.execute("""
            CREATE TABLE IF NOT EXISTS drops (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                group_id INTEGER NOT NULL,
                char_id TEXT NOT NULL,
                message_id INTEGER DEFAULT 0,
                claimed_by INTEGER DEFAULT 0,
                claimed INTEGER DEFAULT 0,
                created_at REAL DEFAULT 0
            )
        """)

        # =========================
        # Market
        # =========================
        db.execute("""
            CREATE TABLE IF NOT EXISTS market (
                listing_id INTEGER PRIMARY KEY AUTOINCREMENT,
                seller_id INTEGER NOT NULL,
                char_id TEXT NOT NULL,
                price INTEGER NOT NULL,
                active INTEGER DEFAULT 1,
                created_at REAL DEFAULT 0
            )
        """)

        # =========================
        # Favorites
        # =========================
        db.execute("""
            CREATE TABLE IF NOT EXISTS favorites (
                user_id INTEGER NOT NULL,
                char_id TEXT NOT NULL,
                PRIMARY KEY (user_id, char_id)
            )
        """)

        # =========================
        # Trades
        # =========================
        db.execute("""
            CREATE TABLE IF NOT EXISTS trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sender_id INTEGER NOT NULL,
                receiver_id INTEGER NOT NULL,
                sender_card TEXT NOT NULL,
                receiver_card TEXT DEFAULT '',
                status TEXT DEFAULT 'pending',
                created_at REAL DEFAULT 0
            )
        """)

        # =========================
        # Admins
        # =========================
        db.execute("""
            CREATE TABLE IF NOT EXISTS admins (
                user_id INTEGER PRIMARY KEY,
                added_by INTEGER DEFAULT 0,
                created_at REAL DEFAULT 0
            )
        """)

        # =========================
        # Duel
        # =========================
        db.execute("""
            CREATE TABLE IF NOT EXISTS duels (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                challenger_id INTEGER NOT NULL,
                opponent_id INTEGER NOT NULL,
                challenger_card TEXT DEFAULT '',
                opponent_card TEXT DEFAULT '',
                winner_id INTEGER DEFAULT 0,
                reward_coins INTEGER DEFAULT 0,
                reward_exp INTEGER DEFAULT 0,
                created_at REAL DEFAULT 0
            )
        """)

        # =========================
        # Bot Settings
        # =========================
        db.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT DEFAULT ''
            )
        """)

        # =========================
        # Default Settings
        # =========================
        defaults = {
            "drop_count": "85",
            "drop_enabled": "1",
            "maintenance": "0",
            "default_language": "my",
        }

        for key, value in defaults.items():
            db.execute("""
                INSERT OR IGNORE INTO settings (key, value)
                VALUES (?, ?)
            """, (key, value))

        # =========================
        # Indexes
        # =========================
        db.execute("""
            CREATE INDEX IF NOT EXISTS idx_user_cards_user
            ON user_cards(user_id)
        """)

        db.execute("""
            CREATE INDEX IF NOT EXISTS idx_user_cards_char
            ON user_cards(char_id)
        """)

        db.execute("""
            CREATE INDEX IF NOT EXISTS idx_drops_group
            ON drops(group_id)
        """)

        db.execute("""
            CREATE INDEX IF NOT EXISTS idx_drops_claimed
            ON drops(claimed)
        """)

        db.execute("""
            CREATE INDEX IF NOT EXISTS idx_cards_active
            ON cards(active)
        """)

        db.execute("""
            CREATE INDEX IF NOT EXISTS idx_market_active
            ON market(active)
        """)


# ============================================================
# USER FUNCTIONS
# ============================================================

def add_or_update_user(
    user_id,
    username="",
    first_name="",
    language="my"
):
    with get_db() as db:
        db.execute("""
            INSERT INTO users (
                user_id,
                username,
                first_name,
                language,
                created_at
            )
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(user_id)
            DO UPDATE SET
                username = excluded.username,
                first_name = excluded.first_name,
                language = excluded.language
        """, (
            user_id,
            username or "",
            first_name or "",
            language or "my",
            time.time()
        ))


def get_user(user_id):
    with get_db() as db:
        return db.execute("""
            SELECT *
            FROM users
            WHERE user_id = ?
        """, (user_id,)).fetchone()


def add_coins(user_id, amount):
    with get_db() as db:
        db.execute("""
            UPDATE users
            SET coins = coins + ?
            WHERE user_id = ?
        """, (amount, user_id))


def remove_coins(user_id, amount):
    with get_db() as db:
        db.execute("""
            UPDATE users
            SET coins = MAX(0, coins - ?)
            WHERE user_id = ?
        """, (amount, user_id))


def get_balance(user_id):
    user = get_user(user_id)

    if not user:
        return 0

    return user["coins"]


# ============================================================
# CARD FUNCTIONS
# ============================================================

def add_card(
    char_id,
    name,
    edition="Common",
    rarity=1,
    price=0,
    image_file_id="",
    video_file_id="",
    media_type="photo",
    description="",
    drop_weight=1,
    exp_reward=0
):
    with get_db() as db:
        db.execute("""
            INSERT INTO cards (
                char_id,
                name,
                edition,
                rarity,
                price,
                image_file_id,
                video_file_id,
                media_type,
                description,
                drop_weight,
                exp_reward,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            str(char_id),
            name,
            edition,
            rarity,
            price,
            image_file_id or "",
            video_file_id or "",
            media_type or "photo",
            description or "",
            drop_weight,
            exp_reward,
            time.time()
        ))


def get_card(char_id):
    with get_db() as db:
        return db.execute("""
            SELECT *
            FROM cards
            WHERE char_id = ?
              AND active = 1
        """, (str(char_id),)).fetchone()


def get_all_cards():
    with get_db() as db:
        return db.execute("""
            SELECT *
            FROM cards
            WHERE active = 1
            ORDER BY id ASC
        """).fetchall()


def search_cards(keyword):
    keyword = f"%{keyword}%"

    with get_db() as db:
        return db.execute("""
            SELECT *
            FROM cards
            WHERE active = 1
              AND (
                    char_id LIKE ?
                    OR name LIKE ?
                    OR edition LIKE ?
                  )
            ORDER BY id ASC
        """, (
            keyword,
            keyword,
            keyword
        )).fetchall()


def update_card_price(char_id, price):
    with get_db() as db:
        db.execute("""
            UPDATE cards
            SET price = ?
            WHERE char_id = ?
        """, (price, str(char_id)))


def delete_card(char_id):
    with get_db() as db:
        db.execute("""
            UPDATE cards
            SET active = 0
            WHERE char_id = ?
        """, (str(char_id),))


# ============================================================
# COLLECTION FUNCTIONS
# ============================================================

def add_user_card(
    user_id,
    char_id,
    level=1,
    exp=0
):
    with get_db() as db:
        db.execute("""
            INSERT INTO user_cards (
                user_id,
                char_id,
                level,
                exp,
                obtained_at
            )
            VALUES (?, ?, ?, ?, ?)
        """, (
            user_id,
            str(char_id),
            level,
            exp,
            time.time()
        ))


def get_user_cards(user_id):
    with get_db() as db:
        return db.execute("""
            SELECT
                uc.*,
                c.name,
                c.edition,
                c.rarity,
                c.price,
                c.image_file_id,
                c.video_file_id,
                c.media_type
            FROM user_cards uc
            JOIN cards c
                ON c.char_id = uc.char_id
            WHERE uc.user_id = ?
            ORDER BY uc.obtained_at ASC
        """, (user_id,)).fetchall()


def count_user_cards(user_id):
    with get_db() as db:
        result = db.execute("""
            SELECT COUNT(*) AS total
            FROM user_cards
            WHERE user_id = ?
        """, (user_id,)).fetchone()

        return result["total"]


def user_has_card(user_id, char_id):
    with get_db() as db:
        result = db.execute("""
            SELECT id
            FROM user_cards
            WHERE user_id = ?
              AND char_id = ?
            LIMIT 1
        """, (
            user_id,
            str(char_id)
        )).fetchone()

        return result is not None


# ============================================================
# FAVORITE
# ============================================================

def add_favorite(user_id, char_id):
    with get_db() as db:
        db.execute("""
            INSERT OR IGNORE INTO favorites (
                user_id,
                char_id
            )
            VALUES (?, ?)
        """, (
            user_id,
            str(char_id)
        ))


def remove_favorite(user_id, char_id):
    with get_db() as db:
        db.execute("""
            DELETE FROM favorites
            WHERE user_id = ?
              AND char_id = ?
        """, (
            user_id,
            str(char_id)
        ))


def is_favorite(user_id, char_id):
    with get_db() as db:
        result = db.execute("""
            SELECT 1
            FROM favorites
            WHERE user_id = ?
              AND char_id = ?
        """, (
            user_id,
            str(char_id)
        )).fetchone()

        return result is not None


# ============================================================
# GLOBAL TOP
# ============================================================

def get_global_top(limit=15):
    with get_db() as db:
        return db.execute("""
            SELECT
                u.user_id,
                u.username,
                u.first_name,
                COUNT(uc.id) AS card_count
            FROM users u
            LEFT JOIN user_cards uc
                ON uc.user_id = u.user_id
            GROUP BY u.user_id
            ORDER BY card_count DESC, u.user_id ASC
            LIMIT ?
        """, (limit,)).fetchall()


# ============================================================
# GROUP TOP
# ============================================================

def get_group_top(group_user_ids, limit=15):
    if not group_user_ids:
        return []

    placeholders = ",".join(["?"] * len(group_user_ids))

    with get_db() as db:
        return db.execute(f"""
            SELECT
                u.user_id,
                u.username,
                u.first_name,
                COUNT(uc.id) AS card_count
            FROM users u
            LEFT JOIN user_cards uc
                ON uc.user_id = u.user_id
            WHERE u.user_id IN ({placeholders})
            GROUP BY u.user_id
            ORDER BY card_count DESC, u.user_id ASC
            LIMIT ?
        """, (*group_user_ids, limit)).fetchall()


# ============================================================
# SETTINGS
# ============================================================

def get_setting(key, default=None):
    with get_db() as db:
        result = db.execute("""
            SELECT value
            FROM settings
            WHERE key = ?
        """, (key,)).fetchone()

        if not result:
            return default

        return result["value"]


def set_setting(key, value):
    with get_db() as db:
        db.execute("""
            INSERT INTO settings (key, value)
            VALUES (?, ?)
            ON CONFLICT(key)
            DO UPDATE SET value = excluded.value
        """, (
            key,
            str(value)
        ))


# ============================================================
# ADMIN
# ============================================================

def add_admin(user_id, added_by):
    with get_db() as db:
        db.execute("""
            INSERT OR REPLACE INTO admins (
                user_id,
                added_by,
                created_at
            )
            VALUES (?, ?, ?)
        """, (
            user_id,
            added_by,
            time.time()
        ))


def remove_admin(user_id):
    with get_db() as db:
        db.execute("""
            DELETE FROM admins
            WHERE user_id = ?
        """, (user_id,))


def is_admin(user_id):
    with get_db() as db:
        result = db.execute("""
            SELECT 1
            FROM admins
            WHERE user_id = ?
        """, (user_id,)).fetchone()

        return result is not None


# ============================================================
# GROUP APPROVAL
# ============================================================

def save_group(
    group_id,
    title,
    member_count=0,
    bot_is_admin=0,
    added_by=0
):
    with get_db() as db:
        db.execute("""
            INSERT INTO groups (
                group_id,
                title,
                member_count,
                bot_is_admin,
                added_by,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(group_id)
            DO UPDATE SET
                title = excluded.title,
                member_count = excluded.member_count,
                bot_is_admin = excluded.bot_is_admin
        """, (
            group_id,
            title or "",
            member_count,
            bot_is_admin,
            added_by,
            time.time()
        ))


def approve_group(group_id):
    with get_db() as db:
        db.execute("""
            UPDATE groups
            SET owner_approved = 1,
                enabled = 1
            WHERE group_id = ?
        """, (group_id,))


def reject_group(group_id):
    with get_db() as db:
        db.execute("""
            UPDATE groups
            SET owner_approved = 0,
                enabled = 0
            WHERE group_id = ?
        """, (group_id,))


def is_group_enabled(group_id):
    with get_db() as db:
        result = db.execute("""
            SELECT enabled
            FROM groups
            WHERE group_id = ?
        """, (group_id,))

        row = result.fetchone()

        return bool(row and row["enabled"])
