# database.py
#
# Advanced Telegram Card Bot
# Database Models - Foundation + Pack/Gacha System
#
# PostgreSQL + SQLAlchemy 2.x + AsyncPG

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
)
from sqlalchemy.ext.asyncio import (
    AsyncAttrs,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from config import settings


# ============================================================
# DATABASE BASE
# ============================================================

class Base(AsyncAttrs, DeclarativeBase):
    pass


# ============================================================
# USER
# ============================================================

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
        nullable=False,
    )

    username: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    first_name: Mapped[str] = mapped_column(
        String(255),
        default="Player",
    )

    # Progression
    level: Mapped[int] = mapped_column(
        Integer,
        default=1,
    )

    xp: Mapped[int] = mapped_column(
        Integer,
        default=0,
    )

    # Economy
    coins: Mapped[int] = mapped_column(
        BigInteger,
        default=1000,
    )

    gems: Mapped[int] = mapped_column(
        Integer,
        default=100,
    )

    # Account status
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


# ============================================================
# TELEGRAM GROUP
# ============================================================

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
        nullable=False,
    )

    title: Mapped[str] = mapped_column(
        String(255),
        default="Telegram Group",
    )

    enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
    )

    drop_enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )


# ============================================================
# CARD
# ============================================================

class Card(Base):
    __tablename__ = "cards"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    # 13-tier rarity
    rarity: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )

    # Battle stats
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

    # Card metadata
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

    # Special card flags
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

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )


# ============================================================
# USER CARD / COLLECTION
# ============================================================

class UserCard(Base):
    __tablename__ = "user_cards"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        index=True,
        nullable=False,
    )

    card_id: Mapped[int] = mapped_column(
        ForeignKey("cards.id"),
        index=True,
        nullable=False,
    )

    # Card progression
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

    # Collection state
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


# ============================================================
# PACK
# ============================================================

class Pack(Base):
    __tablename__ = "packs"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # Price
    price_coins: Mapped[int] = mapped_column(
        BigInteger,
        default=0,
    )

    price_gems: Mapped[int] = mapped_column(
        Integer,
        default=0,
    )

    # Pack behavior
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


# ============================================================
# PACK DROP RATES
# ============================================================

class PackRate(Base):
    __tablename__ = "pack_rates"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    pack_id: Mapped[int] = mapped_column(
        ForeignKey("packs.id"),
        index=True,
        nullable=False,
    )

    rarity: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    rate: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    __table_args__ = (
        UniqueConstraint(
            "pack_id",
            "rarity",
            name="uq_pack_rarity",
        ),
    )


# ============================================================
# PACK OPENING HISTORY
# ============================================================

class PackOpening(Base):
    __tablename__ = "pack_openings"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        index=True,
        nullable=False,
    )

    pack_id: Mapped[int] = mapped_column(
        ForeignKey("packs.id"),
        index=True,
        nullable=False,
    )

    card_id: Mapped[int] = mapped_column(
        ForeignKey("cards.id"),
        index=True,
        nullable=False,
    )

    rarity: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )


# ============================================================
# PITY SYSTEM
# ============================================================

class PityCounter(Base):
    __tablename__ = "pity_counters"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        index=True,
        nullable=False,
    )

    pack_id: Mapped[int] = mapped_column(
        ForeignKey("packs.id"),
        index=True,
        nullable=False,
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


# ============================================================
# ECONOMY TRANSACTIONS
# ============================================================

class EconomyTransaction(Base):
    __tablename__ = "economy_transactions"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        index=True,
        nullable=False,
    )

    transaction_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    currency: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )

    amount: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )


# ============================================================
# DAILY REWARD / STREAK FOUNDATION
# ============================================================

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
        nullable=False,
    )

    streak: Mapped[int] = mapped_column(
        Integer,
        default=0,
    )

    last_claimed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )


# ============================================================
# AUDIT LOG
# ============================================================

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
        nullable=False,
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


# ============================================================
# DATABASE ENGINE
# ============================================================

engine = create_async_engine(
    settings.database_url,
    pool_pre_ping=True,
)


SessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


# ============================================================
# DATABASE INITIALIZATION
# ============================================================

async def init_db():
    async with engine.begin() as connection:
        await connection.run_sync(
            Base.metadata.create_all
        )


# ============================================================
# SESSION HELPER
# ============================================================

async def get_session():
    async with SessionLocal() as session:
        yield session
