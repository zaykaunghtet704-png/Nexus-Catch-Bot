import uuid
from datetime import datetime
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    create_engine,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from config import DATABASE_URL

Base = declarative_base()
engine = create_engine(
    DATABASE_URL, echo=False, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(bind=engine, serialize_replace=True)


class User(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True)
    username = Column(String, nullable=True)
    first_name = Column(String, nullable=True)
    language = Column(String, default="my")  # 'my' (Myanmar) or 'en' (English)
    coins = Column(Integer, default=1000)
    shards = Column(Integer, default=0)
    exp = Column(Integer, default=0)
    level = Column(Integer, default=1)
    fav_card_uuid = Column(String, nullable=True)
    is_banned = Column(Boolean, default=False)
    ban_reason = Column(String, nullable=True)
    last_daily = Column(DateTime, nullable=True)
    last_claim = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    cards = relationship(
        "UserCard", back_populates="owner", cascade="all, delete-orphan"
    )


class AdminRole(Base):
    __tablename__ = "admin_roles"
    user_id = Column(String, primary_key=True)
    role = Column(String, default="Admin")


class ChatSettings(Base):
    __tablename__ = "chat_settings"
    chat_id = Column(String, primary_key=True)
    spawn_threshold = Column(Integer, default=85)
    current_msg_count = Column(Integer, default=0)
    is_allowed = Column(Boolean, default=False)


class CardBase(Base):
    __tablename__ = "card_base"
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    anime = Column(String, default="General")
    rarity = Column(String, default="⚪ Tier 1")
    tier_level = Column(Integer, default=1)
    base_power = Column(Integer, default=1000)
    base_price = Column(Integer, default=1000)
    image_url = Column(String, nullable=False)
    total_prints = Column(Integer, default=0)


class UserCard(Base):
    __tablename__ = "user_cards"
    uuid = Column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())[:8]
    )
    user_id = Column(String, ForeignKey("users.id"))
    card_id = Column(String, ForeignKey("card_base.id"))
    chat_id = Column(String, nullable=True)
    print_number = Column(Integer)
    quality = Column(Float, default=100.0)
    level = Column(Integer, default=1)
    exp = Column(Integer, default=0)
    is_locked = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    owner = relationship("User", back_populates="cards")
    card_info = relationship("CardBase")


class MarketItem(Base):
    __tablename__ = "market_items"
    id = Column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())[:8]
    )
    seller_id = Column(String, ForeignKey("users.id"))
    card_uuid = Column(String, ForeignKey("user_cards.uuid"))
    price = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    card = relationship("UserCard")


Base.metadata.create_all(engine)
