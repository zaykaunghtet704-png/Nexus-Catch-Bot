
from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.ext.asyncio import (
    AsyncAttrs,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from config import settings


# =========================================================
# BASE
# =========================================================

class Base(AsyncAttrs, DeclarativeBase):
    pass


# =========================================================
# USER
# =========================================================

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    telegram_id: Mapped[int] = mapped_column(
        BigInteger,
        unique=True,
        index=True,
    )

    username: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    first_name: Mapped[str] = mapped_column(
        String(255),
        default="Player",
    )

    level: Mapped[int] = mapped_column(
        Integer,
        default=1,
    )

    xp: Mapped[int] = mapped_column(
        Integer,
        default=0,
    )

    coins: Mapped[int] = mapped_column(
        BigInteger,
        default=1000,
    )

    gems: Mapped[int] = mapped_column(
        Integer,
        default=100,
    )

    is_banned: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
    )

    is_muted: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )


# =========================================================
# GROUP
# =========================================================

class Group(Base):
    __tablename__ = "groups"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    telegram_id: Mapped[int] = mapped_column(
        BigInteger,
        unique=True,
        index=True,
    )

    title: Mapped[str] = mapped_column(
        String(255),
        default="Telegram Group",
    )

    username: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
    )

    drop_enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )


# =========================================================
# GROUP ACTIVATION
# =========================================================

class GroupActivation(Base):
    __tablename__ = "group_activations"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    group_id: Mapped[int] = mapped_column(
        ForeignKey("groups.id"),
        unique=True,
        index=True,
    )

    member_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
    )

    bot_is_admin: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
    )

    owner_approved: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
    )

    requested_by: Mapped[int | None] = mapped_column(
        BigInteger,
        nullable=True,
    )

    approved_by: Mapped[int | None] = mapped_column(
        BigInteger,
        nullable=True,
    )

    approved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )


# =========================================================
# USER PREFERENCES
# =========================================================

class UserPreference(Base):
    __tablename__ = "user_preferences"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        unique=True,
        index=True,
    )

    language: Mapped[str] = mapped_column(
        String(10),
        default="my",
    )

    harem_mode: Mapped[str] = mapped_column(
        String(30),
        default="all",
    )

    catch_interval: Mapped[int] = mapped_column(
        Integer,
        default=85,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )


# =========================================================
# CARD
# =========================================================

class Card(Base):
    __tablename__ = "cards"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    name: Mapped[str] = mapped_column(
        String(255),
    )

    rarity: Mapped[str] = mapped_column(
        String(50),
        index=True,
    )

    attack: Mapped[int] = mapped_column(
        Integer,
        default=10,
    )

    defense: Mapped[int] = mapped_column(
        Integer,
        default=10,
    )

    hp: Mapped[int] = mapped_column(
        Integer,
        default=100,
    )

    speed: Mapped[int] = mapped_column(
        Integer,
        default=10,
    )

    element: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    card_class: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    image_url: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    base_price: Mapped[int] = mapped_column(
        BigInteger,
        default=100,
    )

    is_limited: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
    )

    is_shiny: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
    )

    is_animated: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
    )

    is_premium: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )


# =========================================================
# USER CARD
# =========================================================

class UserCard(Base):
    __tablename__ = "user_cards"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        index=True,
    )

    card_id: Mapped[int] = mapped_column(
        ForeignKey("cards.id"),
        index=True,
    )

    level: Mapped[int] = mapped_column(
        Integer,
        default=1,
    )

    xp: Mapped[int] = mapped_column(
        Integer,
        default=0,
    )

    quantity: Mapped[int] = mapped_column(
        Integer,
        default=1,
    )

    is_favorite: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
    )

    is_locked: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
    )

    obtained_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "card_id",
            name="uq_user_card",
        ),
    )


# =========================================================
# PACK
# =========================================================

class Pack(Base):
    __tablename__ = "packs"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    name: Mapped[str] = mapped_column(
        String(255),
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    price_coins: Mapped[int] = mapped_column(
        BigInteger,
        default=0,
    )

    price_gems: Mapped[int] = mapped_column(
        Integer,
        default=0,
    )

    opens_per_day: Mapped[int] = mapped_column(
        Integer,
        default=10,
    )

    cards_per_open: Mapped[int] = mapped_column(
        Integer,
        default=1,
    )

    active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )


# =========================================================
# PACK RATE
# =========================================================

class PackRate(Base):
    __tablename__ = "pack_rates"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    pack_id: Mapped[int] = mapped_column(
        ForeignKey("packs.id"),
        index=True,
    )

    rarity: Mapped[str] = mapped_column(
        String(50),
    )

    rate: Mapped[float] = mapped_column(
        Float,
    )

    __table_args__ = (
        UniqueConstraint(
            "pack_id",
            "rarity",
            name="uq_pack_rarity",
        ),
    )


# =========================================================
# PACK OPENING
# =========================================================

class PackOpening(Base):
    __tablename__ = "pack_openings"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        index=True,
    )

    pack_id: Mapped[int] = mapped_column(
        ForeignKey("packs.id"),
        index=True,
    )

    card_id: Mapped[int] = mapped_column(
        ForeignKey("cards.id"),
        index=True,
    )

    rarity: Mapped[str] = mapped_column(
        String(50),
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )


# =========================================================
# PITY
# =========================================================

class PityCounter(Base):
    __tablename__ = "pity_counters"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        index=True,
    )

    pack_id: Mapped[int] = mapped_column(
        ForeignKey("packs.id"),
        index=True,
    )

    pulls: Mapped[int] = mapped_column(
        Integer,
        default=0,
    )

    legendary_pity: Mapped[int] = mapped_column(
        Integer,
        default=50,
    )

    mythic_pity: Mapped[int] = mapped_column(
        Integer,
        default=100,
    )

    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "pack_id",
            name="uq_user_pack_pity",
        ),
    )


# =========================================================
# ECONOMY TRANSACTION
# =========================================================

class EconomyTransaction(Base):
    __tablename__ = "economy_transactions"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        index=True,
    )

    transaction_type: Mapped[str] = mapped_column(
        String(100),
    )

    currency: Mapped[str] = mapped_column(
        String(30),
    )

    amount: Mapped[int] = mapped_column(
        BigInteger,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )


# =========================================================
# DAILY REWARD
# =========================================================

class DailyReward(Base):
    __tablename__ = "daily_rewards"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        unique=True,
        index=True,
    )

    streak: Mapped[int] = mapped_column(
        Integer,
        default=0,
    )

    last_claimed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )


# =========================================================
# MARKET
# =========================================================

class MarketListing(Base):
    __tablename__ = "market_listings"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    seller_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        index=True,
    )

    user_card_id: Mapped[int] = mapped_column(
        ForeignKey("user_cards.id"),
        index=True,
    )

    card_id: Mapped[int] = mapped_column(
        ForeignKey("cards.id"),
        index=True,
    )

    price: Mapped[int] = mapped_column(
        BigInteger,
    )

    active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    sold_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )


# =========================================================
# TRADE
# =========================================================

class Trade(Base):
    __tablename__ = "trades"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    sender_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        index=True,
    )

    receiver_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        index=True,
    )

    sender_card_id: Mapped[int | None] = mapped_column(
        ForeignKey("user_cards.id"),
        nullable=True,
    )

    receiver_card_id: Mapped[int | None] = mapped_column(
        ForeignKey("user_cards.id"),
        nullable=True,
    )

    sender_coins: Mapped[int] = mapped_column(
        BigInteger,
        default=0,
    )

    receiver_coins: Mapped[int] = mapped_column(
        BigInteger,
        default=0,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        default="pending",
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )


# =========================================================
# GIFT
# =========================================================

class GiftLog(Base):
    __tablename__ = "gift_logs"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    sender_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        index=True,
    )

    receiver_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        index=True,
    )

    user_card_id: Mapped[int] = mapped_column(
        ForeignKey("user_cards.id"),
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )


# =========================================================
# CATCH LOG
# =========================================================

class CatchLog(Base):
    __tablename__ = "catch_logs"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        index=True,
    )

    group_id: Mapped[int | None] = mapped_column(
        ForeignKey("groups.id"),
        index=True,
        nullable=True,
    )

    card_id: Mapped[int] = mapped_column(
        ForeignKey("cards.id"),
        index=True,
    )

    rarity: Mapped[str] = mapped_column(
        String(50),
    )

    is_duplicate: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )


# =========================================================
# DUEL
# =========================================================

class Duel(Base):
    __tablename__ = "duels"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    challenger_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        index=True,
    )

    opponent_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        index=True,
    )

    challenger_card_id: Mapped[int | None] = mapped_column(
        ForeignKey("user_cards.id"),
        nullable=True,
    )

    opponent_card_id: Mapped[int | None] = mapped_column(
        ForeignKey("user_cards.id"),
        nullable=True,
    )

    winner_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"),
        nullable=True,
    )

    reward_coins: Mapped[int] = mapped_column(
        BigInteger,
        default=0,
    )

    reward_xp: Mapped[int] = mapped_column(
        Integer,
        default=0,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        default="pending",
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )


# =========================================================
# MINES GAME
# =========================================================

class MinesGame(Base):
    __tablename__ = "mines_games"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        index=True,
    )

    grid_size: Mapped[int] = mapped_column(
        Integer,
        default=5,
    )

    mines_count: Mapped[int] = mapped_column(
        Integer,
        default=5,
    )

    revealed_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
    )

    multiplier: Mapped[float] = mapped_column(
        Float,
        default=1.0,
    )

    reward: Mapped[int] = mapped_column(
        BigInteger,
        default=0,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        default="active",
        index=True,
    )

    mine_positions: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    revealed_cells: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    finished_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )


# =========================================================
# ACHIEVEMENTS
# =========================================================

class Achievement(Base):
    __tablename__ = "achievements"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    code: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        index=True,
    )

    name: Mapped[str] = mapped_column(
        String(255),
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    reward_coins: Mapped[int] = mapped_column(
        BigInteger,
        default=0,
    )

    reward_gems: Mapped[int] = mapped_column(
        Integer,
        default=0,
    )

    active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
    )


# =========================================================
# USER ACHIEVEMENT
# =========================================================

class UserAchievement(Base):
    __tablename__ = "user_achievements"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        index=True,
    )

    achievement_id: Mapped[int] = mapped_column(
        ForeignKey("achievements.id"),
        index=True,
    )

    unlocked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "achievement_id",
            name="uq_user_achievement",
        ),
    )


# =========================================================
# ADMIN
# =========================================================

class BotAdmin(Base):
    __tablename__ = "bot_admins"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    telegram_id: Mapped[int] = mapped_column(
        BigInteger,
        unique=True,
        index=True,
    )

    role: Mapped[str] = mapped_column(
        String(30),
        default="admin",
    )

    added_by: Mapped[int | None] = mapped_column(
        BigInteger,
        nullable=True,
    )

    active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )


# =========================================================
# AUDIT LOG
# =========================================================

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    actor_id: Mapped[int | None] = mapped_column(
        BigInteger,
        nullable=True,
    )

    action: Mapped[str] = mapped_column(
        String(100),
    )

    target_id: Mapped[int | None] = mapped_column(
        BigInteger,
        nullable=True,
    )

    details: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )


# =========================================================
# ENGINE
# =========================================================

engine = create_async_engine(
    settings.database_url,
    pool_pre_ping=True,
)


# =========================================================
# SESSION
# =========================================================

SessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


# =========================================================
# DATABASE INIT + AUTO MIGRATION
# =========================================================

async def init_db():
    async with engine.begin() as conn:

        # Create tables that don't exist yet.
        await conn.run_sync(
            Base.metadata.create_all
        )

        # -------------------------------------------------
        # CARD TABLE MIGRATION
        # -------------------------------------------------
        # These commands safely add columns if they are
        # missing from an existing PostgreSQL database.

        await conn.execute(
            text(
                """
                ALTER TABLE cards
                ADD COLUMN IF NOT EXISTS base_price
                BIGINT DEFAULT 100
                """
            )
        )

        await conn.execute(
            text(
                """
                ALTER TABLE cards
                ADD COLUMN IF NOT EXISTS is_limited
                BOOLEAN DEFAULT FALSE
                """
            )
        )

        await conn.execute(
            text(
                """
                ALTER TABLE cards
                ADD COLUMN IF NOT EXISTS is_shiny
                BOOLEAN DEFAULT FALSE
                """
            )
        )

        await conn.execute(
            text(
                """
                ALTER TABLE cards
                ADD COLUMN IF NOT EXISTS is_animated
                BOOLEAN DEFAULT FALSE
                """
            )
        )

        await conn.execute(
            text(
                """
                ALTER TABLE cards
                ADD COLUMN IF NOT EXISTS is_premium
                BOOLEAN DEFAULT FALSE
                """
            )
        )

        # -------------------------------------------------
        # USER CARD TABLE MIGRATION
        # -------------------------------------------------

        await conn.execute(
            text(
                """
                ALTER TABLE user_cards
                ADD COLUMN IF NOT EXISTS level
                INTEGER DEFAULT 1
                """
            )
        )

        await conn.execute(
            text(
                """
                ALTER TABLE user_cards
                ADD COLUMN IF NOT EXISTS xp
                INTEGER DEFAULT 0
                """
            )
        )

        await conn.execute(
            text(
                """
                ALTER TABLE user_cards
                ADD COLUMN IF NOT EXISTS quantity
                INTEGER DEFAULT 1
                """
            )
        )

        await conn.execute(
            text(
                """
                ALTER TABLE user_cards
                ADD COLUMN IF NOT EXISTS is_favorite
                BOOLEAN DEFAULT FALSE
                """
            )
        )

        await conn.execute(
            text(
                """
                ALTER TABLE user_cards
                ADD COLUMN IF NOT EXISTS is_locked
                BOOLEAN DEFAULT FALSE
                """
            )
        )

        await conn.execute(
            text(
                """
                ALTER TABLE user_cards
                ADD COLUMN IF NOT EXISTS obtained_at
                TIMESTAMPTZ DEFAULT NOW()
                """
            )
        )

        # -------------------------------------------------
        # CATCH LOG TABLE MIGRATION
        # -------------------------------------------------

        await conn.execute(
            text(
                """
                ALTER TABLE catch_logs
                ADD COLUMN IF NOT EXISTS is_duplicate
                BOOLEAN DEFAULT FALSE
                """
            )
        )
