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

Base = declarative_base()
engine = create_engine("sqlite:///bot_database.db", echo=False)
SessionLocal = sessionmaker(bind=engine)

# 10-Tier Rarity Matrix
ADVANCED_RARITIES = {
    "⚪ Common": 0.38,
    "🟢 Uncommon": 0.25,
    "🔵 Rare": 0.15,
    "🟣 Epic": 0.10,
    "🟡 Legendary": 0.06,
    "🟠 Mythic": 0.03,
    "🔴 Celestial": 0.015,
    "🌌 Godlike": 0.008,
    "✨ Omnipotent": 0.005,  # Tier 9
    "👑 Sovereign": 0.002,  # Tier 10
}

ELEMENTS = [
    "🔥 Fire",
    "💧 Water",
    "⚡ Thunder",
    "🌪️ Wind",
    "✨ Light",
    "🖤 Dark",
    "☯️ Chaos",
]


class User(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True)
    name = Column(String)
    coins = Column(Integer, default=2000)
    shards = Column(Integer, default=0)
    fav_card_id = Column(String, nullable=True)
    last_daily = Column(DateTime, nullable=True)
    last_grab = Column(DateTime, nullable=True)
    daily_streak = Column(Integer, default=0)

    cards = relationship(
        "UserCard", back_populates="owner", cascade="all, delete-orphan"
    )


class ChatSettings(Base):
    __tablename__ = "chat_settings"
    chat_id = Column(String, primary_key=True)
    spawn_threshold = Column(Integer, default=50)
    current_msg_count = Column(Integer, default=0)


class CardBase(Base):
    __tablename__ = "card_base"
    id = Column(String, primary_key=True)
    name = Column(String)
    anime = Column(String, default="General")
    rarity = Column(String, default="⚪ Common")
    element = Column(String, default="🔥 Fire")
    base_power = Column(Integer, default=1200)
    image_url = Column(String)
    total_prints = Column(Integer, default=0)


class UserCard(Base):
    __tablename__ = "user_cards"
    uuid = Column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())[:8]
    )
    user_id = Column(String, ForeignKey("users.id"))
    card_id = Column(String, ForeignKey("card_base.id"))
    print_number = Column(Integer)
    quality = Column(Float)
    level = Column(Integer, default=1)
    is_market = Column(Boolean, default=False)
    market_price = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    owner = relationship("User", back_populates="cards")
    card_info = relationship("CardBase")


Base.metadata.create_all(engine)
