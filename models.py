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


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True)
    name = Column(String)
    coins = Column(Integer, default=1000)
    tokens = Column(Integer, default=10)
    language = Column(String, default="en")
    is_banned = Column(Boolean, default=False)
    fav_card_id = Column(String, nullable=True)
    last_daily = Column(DateTime, nullable=True)

    cards = relationship("UserCard", back_populates="owner")


class CardBase(Base):
    __tablename__ = "card_base"

    id = Column(String, primary_key=True)
    name = Column(String)
    anime = Column(String, default="General")
    rarity = Column(String, default="Common ⚪")
    base_power = Column(Integer, default=1000)
    element = Column(String, default="Neutral")
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
    is_market = Column(Boolean, default=False)
    market_price = Column(Integer, default=0)

    owner = relationship("User", back_populates="cards")
    card_info = relationship("CardBase")


Base.metadata.create_all(engine)
