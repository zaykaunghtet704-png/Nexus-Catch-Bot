import os
import sqlite3
import threading
import time
from contextlib import contextmanager

from config import DATABASE_PATH


# ============================================================
# SQLITE CONFIGURATION
# ============================================================

_db_dir = os.path.dirname(os.path.abspath(DATABASE_PATH))

if _db_dir:
    os.makedirs(_db_dir, exist_ok=True)


_DB_LOCK = threading.RLock()


def _connect():
    conn = sqlite3.connect(
        DATABASE_PATH,
        timeout=30.0,
        check_same_thread=False,
    )

    conn.row_factory = sqlite3.Row

    conn.execute("PRAGMA busy_timeout = 30000")
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA synchronous = NORMAL")
    conn.execute("PRAGMA foreign_keys = ON")

    return conn


@contextmanager
def get_db():
    """
    Safe SQLite transaction.

    IMPORTANT:
    Existing database data is never deleted or recreated.
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
# SAFE MIGRATION HELPERS
# ============================================================

def _table_exists(db, table_name):
    row = db.execute(
        """
        SELECT name
        FROM sqlite_master
        WHERE type = 'table'
          AND name = ?
        """,
        (table_name,),
    ).fetchone()

    return row is not None


def _column_exists(db, table_name, column_name):
    if not _table_exists(db, table_name):
        return False

    rows = db.execute(
        f"PRAGMA table_info({table_name})"
    ).fetchall()

    return any(row["name"] == column_name for row in rows)


def _add_column_if_missing(
    db,
    table_name,
    column_name,
    column_definition,
):
    if not _column_exists(db, table_name, column_name):

        db.execute(
            f"""
            ALTER TABLE {table_name}
            ADD COLUMN {column_name} {column_definition}
            """
        )


# ============================================================
# DATABASE INITIALIZATION
# ============================================================

def init_db():

    with get_db() as db:

        # ====================================================
        # USERS
        # ====================================================

        db.execute(
            """
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
            """
        )

        # ====================================================
        # GROUPS
        # ====================================================

        db.execute(
            """
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
            """
        )

        # ====================================================
        # CARDS
        # ====================================================

        db.execute(
            """
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
            """
        )

        # ====================================================
        # USER CARDS
        # ====================================================

        db.execute(
            """
            CREATE TABLE IF NOT EXISTS user_cards (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                char_id TEXT NOT NULL,
                level INTEGER DEFAULT 1,
                exp INTEGER DEFAULT 0,
                favorite INTEGER DEFAULT 0,
                obtained_at REAL DEFAULT 0
            )
            """
        )

        # ====================================================
        # DROPS
        # ====================================================

        db.execute(
            """
            CREATE TABLE IF NOT EXISTS drops (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                group_id INTEGER NOT NULL,
                char_id TEXT NOT NULL,
                message_id INTEGER DEFAULT 0,
                claimed_by INTEGER DEFAULT 0,
                claimed INTEGER DEFAULT 0,
                created_at REAL DEFAULT 0
            )
            """
        )

        # ====================================================
        # MARKET
        # ====================================================

        db.execute(
            """
            CREATE TABLE IF NOT EXISTS market (
                listing_id INTEGER PRIMARY KEY AUTOINCREMENT,
                seller_id INTEGER NOT NULL,
                char_id TEXT NOT NULL,
                price INTEGER NOT NULL,
                active INTEGER DEFAULT 1,
                created_at REAL DEFAULT 0
            )
            """
        )

        # ====================================================
        # FAVORITES
        # ====================================================

        db.execute(
            """
            CREATE TABLE IF NOT EXISTS favorites (
                user_id INTEGER NOT NULL,
                char_id TEXT NOT NULL,
                PRIMARY KEY (user_id, char_id)
            )
            """
        )

        # ====================================================
        # TRADES
        # ====================================================

        db.execute(
            """
            CREATE TABLE IF NOT EXISTS trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sender_id INTEGER NOT NULL,
                receiver_id INTEGER NOT NULL,
                sender_card TEXT NOT NULL,
                receiver_card TEXT DEFAULT '',
                status TEXT DEFAULT 'pending',
                created_at REAL DEFAULT 0
            )
            """
        )

        # ====================================================
        # ADMINS
        # ====================================================

        db.execute(
            """
            CREATE TABLE IF NOT EXISTS admins (
                user_id INTEGER PRIMARY KEY,
                added_by INTEGER DEFAULT 0,
                created_at REAL DEFAULT 0
            )
            """
        )

        # ====================================================
        # DUELS
        # ====================================================

        db.execute(
            """
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
            """
        )

        # ====================================================
        # SETTINGS
        # ====================================================

        db.execute(
            """
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT DEFAULT ''
            )
            """
        )

        # ====================================================
        # SAFE MIGRATIONS
        #
        # Existing tables are NOT deleted.
        # Existing rows are NOT deleted.
        # ====================================================

        _add_column_if_missing(
            db,
            "users",
            "language",
            "TEXT DEFAULT 'my'",
        )

        _add_column_if_missing(
            db,
            "users",
            "coins",
            "INTEGER DEFAULT 0",
        )

        _add_column_if_missing(
            db,
            "users",
            "exp",
            "INTEGER DEFAULT 0",
        )

        _add_column_if_missing(
            db,
            "users",
            "level",
            "INTEGER DEFAULT 1",
        )

        _add_column_if_missing(
            db,
            "cards",
            "edition",
            "TEXT DEFAULT 'Common'",
        )

        _add_column_if_missing(
            db,
            "cards",
            "rarity",
            "INTEGER DEFAULT 1",
        )

        _add_column_if_missing(
            db,
            "cards",
            "price",
            "INTEGER DEFAULT 0",
        )

        _add_column_if_missing(
            db,
            "cards",
            "image_file_id",
            "TEXT DEFAULT ''",
        )

        _add_column_if_missing(
            db,
            "cards",
            "video_file_id",
            "TEXT DEFAULT ''",
        )

        _add_column_if_missing(
            db,
            "cards",
            "media_type",
            "TEXT DEFAULT 'photo'",
        )

        _add_column_if_missing(
            db,
            "cards",
            "description",
            "TEXT DEFAULT ''",
        )

        _add_column_if_missing(
            db,
            "cards",
            "drop_weight",
            "REAL DEFAULT 1",
        )

        _add_column_if_missing(
            db,
            "cards",
            "exp_reward",
            "INTEGER DEFAULT 0",
        )

        _add_column_if_missing(
            db,
            "cards",
            "created_at",
            "REAL DEFAULT 0",
        )

        _add_column_if_missing(
            db,
            "cards",
            "active",
            "INTEGER DEFAULT 1",
        )

        # ====================================================
        # DEFAULT SETTINGS
        # ====================================================

        defaults = {

            # Auto drop
            "drop_count": "85",

            # Drop enabled
            "drop_enabled": "1",

            # Maintenance
            "maintenance": "0",

            # Default language
            "default_language": "my",

            # Drop cooldown
            "drop_cooldown": "0",

            # Last automatic drop timestamp
            "last_drop_time": "0",

            # Last message counter
            "message_count": "0",

            # Channel notification
            "channel_notifications": "1",

            # Minimum group members
            "minimum_group_members": "50",

            # Daily reward
            "daily_reward": "500",
        }

        for key, value in defaults.items():

            db.execute(
                """
                INSERT OR IGNORE INTO settings (
                    key,
                    value
                )
                VALUES (?, ?)
                """,
                (key, value),
            )

        # ====================================================
        # INDEXES
        # ====================================================

        db.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_user_cards_user
            ON user_cards(user_id)
            """
        )

        db.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_user_cards_char
            ON user_cards(char_id)
            """
        )

        db.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_drops_group
            ON drops(group_id)
            """
        )

        db.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_drops_claimed
            ON drops(claimed)
            """
        )

        db.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_cards_active
            ON cards(active)
            """
        )

        db.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_cards_edition
            ON cards(edition)
            """
        )

        db.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_market_active
            ON market(active)
            """
        )

        db.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_user_cards_quantity
            ON user_cards(char_id, user_id)
            """
        )


# ============================================================
# USER FUNCTIONS
# ============================================================

def add_or_update_user(
    user_id,
    username="",
    first_name="",
    language=None,
):
    """
    Update user information WITHOUT resetting coins,
    EXP, level or collection.
    """

    with get_db() as db:

        if language is None:

            db.execute(
                """
                INSERT INTO users (
                    user_id,
                    username,
                    first_name,
                    created_at
                )
                VALUES (?, ?, ?, ?)

                ON CONFLICT(user_id)
                DO UPDATE SET
                    username = excluded.username,
                    first_name = excluded.first_name
                """,
                (
                    user_id,
                    username or "",
                    first_name or "",
                    time.time(),
                ),
            )

        else:

            db.execute(
                """
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
                """,
                (
                    user_id,
                    username or "",
                    first_name or "",
                    language or "my",
                    time.time(),
                ),
            )


def get_user(user_id):

    with get_db() as db:

        return db.execute(
            """
            SELECT *
            FROM users
            WHERE user_id = ?
            """,
            (user_id,),
        ).fetchone()


def set_user_language(user_id, language):

    language = "en" if str(language).lower() in (
        "en",
        "english",
    ) else "my"

    with get_db() as db:

        db.execute(
            """
            UPDATE users
            SET language = ?
            WHERE user_id = ?
            """,
            (language, user_id),
        )


def get_user_language(user_id, default="my"):

    with get_db() as db:

        row = db.execute(
            """
            SELECT language
            FROM users
            WHERE user_id = ?
            """,
            (user_id,),
        ).fetchone()

        if not row:
            return default

        return row["language"] or default


# ============================================================
# COINS
# ============================================================

def add_coins(user_id, amount):

    amount = int(amount)

    with get_db() as db:

        db.execute(
            """
            INSERT OR IGNORE INTO users (
                user_id,
                created_at
            )
            VALUES (?, ?)
            """,
            (user_id, time.time()),
        )

        db.execute(
            """
            UPDATE users
            SET coins = coins + ?
            WHERE user_id = ?
            """,
            (amount, user_id),
        )


def remove_coins(user_id, amount):

    amount = max(0, int(amount))

    with get_db() as db:

        db.execute(
            """
            UPDATE users
            SET coins = MAX(0, coins - ?)
            WHERE user_id = ?
            """,
            (amount, user_id),
        )


def set_coins(user_id, amount):

    amount = max(0, int(amount))

    with get_db() as db:

        db.execute(
            """
            INSERT OR IGNORE INTO users (
                user_id,
                created_at
            )
            VALUES (?, ?)
            """,
            (user_id, time.time()),
        )

        db.execute(
            """
            UPDATE users
            SET coins = ?
            WHERE user_id = ?
            """,
            (amount, user_id),
        )


def transfer_coins(sender_id, receiver_id, amount):

    amount = int(amount)

    if amount <= 0:
        return False

    with get_db() as db:

        sender = db.execute(
            """
            SELECT coins
            FROM users
            WHERE user_id = ?
            """,
            (sender_id,),
        ).fetchone()

        if not sender:
            return False

        if sender["coins"] < amount:
            return False

        db.execute(
            """
            UPDATE users
            SET coins = coins - ?
            WHERE user_id = ?
            """,
            (amount, sender_id),
        )

        db.execute(
            """
            INSERT OR IGNORE INTO users (
                user_id,
                created_at
            )
            VALUES (?, ?)
            """,
            (receiver_id, time.time()),
        )

        db.execute(
            """
            UPDATE users
            SET coins = coins + ?
            WHERE user_id = ?
            """,
            (amount, receiver_id),
        )

        return True


def get_balance(user_id):

    user = get_user(user_id)

    if not user:
        return 0

    return int(user["coins"] or 0)


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
    exp_reward=0,
):
    """
    Add a card safely.

    IMPORTANT FIX:

    If a card with the same char_id previously existed but was
    soft-deleted (active=0), the old record is RESTORED instead
    of creating a new conflicting record.

    Therefore:

        NXS001 -> delete -> add NXS001

    works again.

    Existing card data is preserved where possible.
    """

    char_id = str(char_id).strip()
    name = str(name).strip()

    if not char_id:
        raise ValueError("char_id cannot be empty")

    if not name:
        raise ValueError("name cannot be empty")

    with get_db() as db:

        old = db.execute(
            """
            SELECT *
            FROM cards
            WHERE char_id = ?
            """,
            (char_id,),
        ).fetchone()

        if old:

            # ================================================
            # RESTORE OLD CARD
            # ================================================

            db.execute(
                """
                UPDATE cards
                SET
                    name = ?,
                    edition = ?,
                    rarity = ?,
                    price = ?,
                    image_file_id = ?,
                    video_file_id = ?,
                    media_type = ?,
                    description = ?,
                    drop_weight = ?,
                    exp_reward = ?,
                    active = 1
                WHERE char_id = ?
                """,
                (
                    name,
                    edition or "Common",
                    int(rarity or 1),
                    int(price or 0),
                    image_file_id or old["image_file_id"] or "",
                    video_file_id or old["video_file_id"] or "",
                    media_type or old["media_type"] or "photo",
                    description or old["description"] or "",
                    float(drop_weight or 1),
                    int(exp_reward or 0),
                    char_id,
                ),
            )

            return old["id"]

        # ================================================
        # COMPLETELY NEW CARD
        # ================================================

        cursor = db.execute(
            """
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
                created_at,
                active
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
            """,
            (
                char_id,
                name,
                edition or "Common",
                int(rarity or 1),
                int(price or 0),
                image_file_id or "",
                video_file_id or "",
                media_type or "photo",
                description or "",
                float(drop_weight or 1),
                int(exp_reward or 0),
                time.time(),
            ),
        )

        return cursor.lastrowid


def update_card(
    char_id,
    name=None,
    edition=None,
    rarity=None,
    price=None,
    image_file_id=None,
    video_file_id=None,
    media_type=None,
    description=None,
    drop_weight=None,
    exp_reward=None,
    active=None,
):
    """
    Edit an existing card WITHOUT deleting it.
    Only supplied values are changed.
    """

    fields = []
    values = []

    if name is not None:
        fields.append("name = ?")
        values.append(str(name))

    if edition is not None:
        fields.append("edition = ?")
        values.append(str(edition))

    if rarity is not None:
        fields.append("rarity = ?")
        values.append(int(rarity))

    if price is not None:
        fields.append("price = ?")
        values.append(int(price))

    if image_file_id is not None:
        fields.append("image_file_id = ?")
        values.append(str(image_file_id))

    if video_file_id is not None:
        fields.append("video_file_id = ?")
        values.append(str(video_file_id))

    if media_type is not None:
        fields.append("media_type = ?")
        values.append(str(media_type))

    if description is not None:
        fields.append("description = ?")
        values.append(str(description))

    if drop_weight is not None:
        fields.append("drop_weight = ?")
        values.append(float(drop_weight))

    if exp_reward is not None:
        fields.append("exp_reward = ?")
        values.append(int(exp_reward))

    if active is not None:
        fields.append("active = ?")
        values.append(1 if active else 0)

    if not fields:
        return False

    values.append(str(char_id))

    with get_db() as db:

        cursor = db.execute(
            f"""
            UPDATE cards
            SET {", ".join(fields)}
            WHERE char_id = ?
            """,
            tuple(values),
        )

        return cursor.rowcount > 0


def get_card(char_id):

    with get_db() as db:

        return db.execute(
            """
            SELECT *
            FROM cards
            WHERE char_id = ?
              AND active = 1
            """,
            (str(char_id),),
        ).fetchone()


def get_card_any(char_id):

    with get_db() as db:

        return db.execute(
            """
            SELECT *
            FROM cards
            WHERE char_id = ?
            """,
            (str(char_id),),
        ).fetchone()


def get_all_cards():

    with get_db() as db:

        return db.execute(
            """
            SELECT *
            FROM cards
            WHERE active = 1
            ORDER BY id ASC
            """
        ).fetchall()


def get_all_cards_including_inactive():

    with get_db() as db:

        return db.execute(
            """
            SELECT *
            FROM cards
            ORDER BY id ASC
            """
        ).fetchall()


def search_cards(keyword):

    keyword = f"%{str(keyword).strip()}%"

    with get_db() as db:

        return db.execute(
            """
            SELECT *
            FROM cards
            WHERE active = 1
              AND (
                    char_id LIKE ?
                    OR name LIKE ?
                    OR edition LIKE ?
                    OR description LIKE ?
                  )
            ORDER BY id ASC
            """,
            (
                keyword,
                keyword,
                keyword,
                keyword,
            ),
        ).fetchall()


def get_cards_by_edition(edition):

    with get_db() as db:

        return db.execute(
            """
            SELECT *
            FROM cards
            WHERE active = 1
              AND edition = ?
            ORDER BY id ASC
            """,
            (edition,),
        ).fetchall()


def update_card_price(char_id, price):

    with get_db() as db:

        db.execute(
            """
            UPDATE cards
            SET price = ?
            WHERE char_id = ?
            """,
            (
                int(price),
                str(char_id),
            ),
        )


def update_card_drop_weight(char_id, weight):

    with get_db() as db:

        db.execute(
            """
            UPDATE cards
            SET drop_weight = ?
            WHERE char_id = ?
            """,
            (
                float(weight),
                str(char_id),
            ),
        )


def delete_card(char_id):
    """
    SOFT DELETE ONLY.

    The database record remains.
    User collections remain.
    The char_id can later be reused by add_card().
    """

    with get_db() as db:

        db.execute(
            """
            UPDATE cards
            SET active = 0
            WHERE char_id = ?
            """,
            (str(char_id),),
        )


def restore_card(char_id):

    with get_db() as db:

        cursor = db.execute(
            """
            UPDATE cards
            SET active = 1
            WHERE char_id = ?
            """,
            (str(char_id),),
        )

        return cursor.rowcount > 0


def card_exists(char_id):

    with get_db() as db:

        row = db.execute(
            """
            SELECT 1
            FROM cards
            WHERE char_id = ?
            LIMIT 1
            """,
            (str(char_id),),
        ).fetchone()

        return row is not None


def card_count():

    with get_db() as db:

        row = db.execute(
            """
            SELECT COUNT(*) AS total
            FROM cards
            WHERE active = 1
            """
        ).fetchone()

        return int(row["total"])


# ============================================================
# USER COLLECTION
# ============================================================

def add_user_card(
    user_id,
    char_id,
    level=1,
    exp=0,
):

    with get_db() as db:

        db.execute(
            """
            INSERT OR IGNORE INTO users (
                user_id,
                created_at
            )
            VALUES (?, ?)
            """,
            (user_id, time.time()),
        )

        db.execute(
            """
            INSERT INTO user_cards (
                user_id,
                char_id,
                level,
                exp,
                obtained_at
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                user_id,
                str(char_id),
                level,
                exp,
                time.time(),
            ),
        )


def get_user_cards(user_id):

    with get_db() as db:

        return db.execute(
            """
            SELECT
                uc.*,
                c.name,
                c.edition,
                c.rarity,
                c.price,
                c.image_file_id,
                c.video_file_id,
                c.media_type,
                c.description
            FROM user_cards uc
            JOIN cards c
                ON c.char_id = uc.char_id
            WHERE uc.user_id = ?
            ORDER BY uc.obtained_at ASC
            """,
            (user_id,),
        ).fetchall()


def count_user_cards(user_id):

    with get_db() as db:

        result = db.execute(
            """
            SELECT COUNT(*) AS total
            FROM user_cards
            WHERE user_id = ?
            """,
            (user_id,),
        ).fetchone()

        return int(result["total"])


def user_has_card(user_id, char_id):

    with get_db() as db:

        result = db.execute(
            """
            SELECT id
            FROM user_cards
            WHERE user_id = ?
              AND char_id = ?
            LIMIT 1
            """,
            (
                user_id,
                str(char_id),
            ),
        ).fetchone()

        return result is not None


def count_user_card_quantity(user_id, char_id):

    with get_db() as db:

        row = db.execute(
            """
            SELECT COUNT(*) AS quantity
            FROM user_cards
            WHERE user_id = ?
              AND char_id = ?
            """,
            (
                user_id,
                str(char_id),
            ),
        ).fetchone()

        return int(row["quantity"] or 0)


# ============================================================
# CHECK CARD - TOP 15 OWNERS
# ============================================================

def get_card_top_owners(char_id, limit=15):

    """
    Return the users who own the most copies of a card.

    Used by /check.

    Example:

        🥇 User A — 18x
        🥈 User B — 12x
        🥉 User C — 9x
    """

    with get_db() as db:

        return db.execute(
            """
            SELECT
                u.user_id,
                u.username,
                u.first_name,
                COUNT(uc.id) AS quantity
            FROM user_cards uc
            LEFT JOIN users u
                ON u.user_id = uc.user_id
            WHERE uc.char_id = ?
            GROUP BY
                uc.user_id
            ORDER BY
                quantity DESC,
                uc.user_id ASC
            LIMIT ?
            """,
            (
                str(char_id),
                int(limit),
            ),
        ).fetchall()


# ============================================================
# FAVORITES
# ============================================================

def add_favorite(user_id, char_id):

    with get_db() as db:

        db.execute(
            """
            INSERT OR IGNORE INTO favorites (
                user_id,
                char_id
            )
            VALUES (?, ?)
            """,
            (
                user_id,
                str(char_id),
            ),
        )


def remove_favorite(user_id, char_id):

    with get_db() as db:

        db.execute(
            """
            DELETE FROM favorites
            WHERE user_id = ?
              AND char_id = ?
            """,
            (
                user_id,
                str(char_id),
            ),
        )


def is_favorite(user_id, char_id):

    with get_db() as db:

        result = db.execute(
            """
            SELECT 1
            FROM favorites
            WHERE user_id = ?
              AND char_id = ?
            """,
            (
                user_id,
                str(char_id),
            ),
        ).fetchone()

        return result is not None


# ============================================================
# GLOBAL TOP
# ============================================================

def get_global_top(limit=15):

    with get_db() as db:

        return db.execute(
            """
            SELECT
                u.user_id,
                u.username,
                u.first_name,
                COUNT(uc.id) AS card_count
            FROM users u
            LEFT JOIN user_cards uc
                ON uc.user_id = u.user_id
            GROUP BY u.user_id
            ORDER BY
                card_count DESC,
                u.user_id ASC
            LIMIT ?
            """,
            (int(limit),),
        ).fetchall()


def get_global_rank(user_id):

    with get_db() as db:

        rows = db.execute(
            """
            SELECT
                u.user_id,
                COUNT(uc.id) AS card_count
            FROM users u
            LEFT JOIN user_cards uc
                ON uc.user_id = u.user_id
            GROUP BY u.user_id
            ORDER BY
                card_count DESC,
                u.user_id ASC
            """
        ).fetchall()

        for index, row in enumerate(rows, start=1):

            if int(row["user_id"]) == int(user_id):
                return index

        return None


# ============================================================
# GROUP TOP
# ============================================================

def get_group_top(group_user_ids, limit=15):

    if not group_user_ids:
        return []

    placeholders = ",".join(
        ["?"] * len(group_user_ids)
    )

    with get_db() as db:

        return db.execute(
            f"""
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
            ORDER BY
                card_count DESC,
                u.user_id ASC
            LIMIT ?
            """,
            (
                *group_user_ids,
                int(limit),
            ),
        ).fetchall()


# ============================================================
# SETTINGS
# ============================================================

def get_setting(key, default=None):

    with get_db() as db:

        result = db.execute(
            """
            SELECT value
            FROM settings
            WHERE key = ?
            """,
            (str(key),),
        ).fetchone()

        if not result:
            return default

        return result["value"]


def set_setting(key, value):

    with get_db() as db:

        db.execute(
            """
            INSERT INTO settings (
                key,
                value
            )
            VALUES (?, ?)

            ON CONFLICT(key)
            DO UPDATE SET
                value = excluded.value
            """,
            (
                str(key),
                str(value),
            ),
        )


def get_setting_int(key, default=0):

    value = get_setting(key, default)

    try:
        return int(value)
    except (TypeError, ValueError):
        return int(default)


def get_setting_float(key, default=0.0):

    value = get_setting(key, default)

    try:
        return float(value)
    except (TypeError, ValueError):
        return float(default)


# ============================================================
# AUTO DROP MESSAGE COUNTER
# ============================================================

def get_message_count():

    return get_setting_int(
        "message_count",
        0,
    )


def set_message_count(count):

    set_setting(
        "message_count",
        max(0, int(count)),
    )


def increment_message_count(amount=1):

    with get_db() as db:

        current = db.execute(
            """
            SELECT value
            FROM settings
            WHERE key = 'message_count'
            """
        ).fetchone()

        try:
            count = int(
                current["value"]
                if current
                else 0
            )
        except (TypeError, ValueError):
            count = 0

        count += int(amount)

        db.execute(
            """
            INSERT INTO settings (
                key,
                value
            )
            VALUES (
                'message_count',
                ?
            )
            ON CONFLICT(key)
            DO UPDATE SET
                value = excluded.value
            """,
            (str(count),),
        )

        return count


def reset_message_count():

    set_setting(
        "message_count",
        "0",
    )


# ============================================================
# DROP SETTINGS
# ============================================================

def get_drop_count():

    return get_setting_int(
        "drop_count",
        85,
    )


def set_drop_count(count):

    set_setting(
        "drop_count",
        max(1, int(count)),
    )


def is_drop_enabled():

    return bool(
        get_setting_int(
            "drop_enabled",
            1,
        )
    )


def set_drop_enabled(enabled):

    set_setting(
        "drop_enabled",
        "1" if enabled else "0",
    )


def get_last_drop_time():

    return get_setting_float(
        "last_drop_time",
        0,
    )


def set_last_drop_time(timestamp=None):

    if timestamp is None:
        timestamp = time.time()

    set_setting(
        "last_drop_time",
        str(timestamp),
    )


# ============================================================
# DROP EVENTS
# ============================================================

def create_drop(
    group_id,
    char_id,
    message_id=0,
):

    with get_db() as db:

        cursor = db.execute(
            """
            INSERT INTO drops (
                group_id,
                char_id,
                message_id,
                claimed_by,
                claimed,
                created_at
            )
            VALUES (?, ?, ?, 0, 0, ?)
            """,
            (
                group_id,
                str(char_id),
                message_id,
                time.time(),
            ),
        )

        return cursor.lastrowid


def get_drop(drop_id):

    with get_db() as db:

        return db.execute(
            """
            SELECT *
            FROM drops
            WHERE id = ?
            """,
            (drop_id,),
        ).fetchone()


def claim_drop(drop_id, user_id):

    """
    Atomic first-click claim.

    Only the first successful claimant can receive the drop.
    """

    with get_db() as db:

        cursor = db.execute(
            """
            UPDATE drops
            SET
                claimed_by = ?,
                claimed = 1
            WHERE id = ?
              AND claimed = 0
            """,
            (
                user_id,
                drop_id,
            ),
        )

        return cursor.rowcount > 0


def get_active_drop(group_id):

    with get_db() as db:

        return db.execute(
            """
            SELECT *
            FROM drops
            WHERE group_id = ?
              AND claimed = 0
            ORDER BY id DESC
            LIMIT 1
            """,
            (group_id,),
        ).fetchone()


# ============================================================
# ADMINS
# ============================================================

def add_admin(user_id, added_by):

    with get_db() as db:

        db.execute(
            """
            INSERT OR REPLACE INTO admins (
                user_id,
                added_by,
                created_at
            )
            VALUES (?, ?, ?)
            """,
            (
                user_id,
                added_by,
                time.time(),
            ),
        )


def remove_admin(user_id):

    with get_db() as db:

        db.execute(
            """
            DELETE FROM admins
            WHERE user_id = ?
            """,
            (user_id,),
        )


def is_admin(user_id):

    with get_db() as db:

        result = db.execute(
            """
            SELECT 1
            FROM admins
            WHERE user_id = ?
            """,
            (user_id,),
        ).fetchone()

        return result is not None


def get_admins():

    with get_db() as db:

        return db.execute(
            """
            SELECT *
            FROM admins
            ORDER BY created_at ASC
            """
        ).fetchall()


# ============================================================
# GROUP APPROVAL
# ============================================================

def save_group(
    group_id,
    title,
    member_count=0,
    bot_is_admin=0,
    added_by=0,
):

    with get_db() as db:

        db.execute(
            """
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
            """,
            (
                group_id,
                title or "",
                member_count,
                bot_is_admin,
                added_by,
                time.time(),
            ),
        )


def get_group(group_id):

    with get_db() as db:

        return db.execute(
            """
            SELECT *
            FROM groups
            WHERE group_id = ?
            """,
            (group_id,),
        ).fetchone()


def approve_group(group_id):

    with get_db() as db:

        db.execute(
            """
            UPDATE groups
            SET
                owner_approved = 1,
                enabled = 1
            WHERE group_id = ?
            """,
            (group_id,),
        )


def reject_group(group_id):

    with get_db() as db:

        db.execute(
            """
            UPDATE groups
            SET
                owner_approved = 0,
                enabled = 0
            WHERE group_id = ?
            """,
            (group_id,),
        )


def is_group_enabled(group_id):

    with get_db() as db:

        result = db.execute(
            """
            SELECT enabled
            FROM groups
            WHERE group_id = ?
            """,
            (group_id,),
        )

        row = result.fetchone()

        return bool(
            row
            and row["enabled"]
        )


def is_group_approved(group_id):

    with get_db() as db:

        row = db.execute(
            """
            SELECT owner_approved
            FROM groups
            WHERE group_id = ?
            """,
            (group_id,),
        ).fetchone()

        return bool(
            row
            and row["owner_approved"]
        )


# ============================================================
# DATABASE STARTUP
# ============================================================

# Safe to call when bot starts.
# It creates missing tables/columns only.
# It NEVER clears existing cards or user data.

try:
    init_db()
except Exception:
    # Do not hide runtime errors when imported by the bot.
    # The bot can call init_db() explicitly as well.
    raise
