import datetime
import uuid
from config import DATABASE_URL
from sqlalchemy import (
    JSON,
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


class User(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True)  # Telegram User ID
    name = Column(String)
    coins = Column(Integer, default=10000)
    tokens = Column(Integer, default=100)
    language = Column(
        String, default="en"
    )  # Language Preference ("en" or "my")
    pity_counter = Column(Integer, default=0)
    is_banned = Column(Boolean, default=False)
    cards = relationship("UserCard", back_populates="owner")


class CardBase(Base):
    __tablename__ = "card_bases"
    id = Column(String, primary_key=True)
    name = Column(String)
    anime = Column(String)
    rarity = Column(String)
    base_power = Column(Integer)
    element = Column(String)
    image_url = Column(String)
    total_prints = Column(Integer, default=0)


class UserCard(Base):
    __tablename__ = "user_cards"
    uuid = Column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())[:8]
    )
    user_id = Column(String, ForeignKey("users.id"))
    card_id = Column(String, ForeignKey("card_bases.id"))
    print_number = Column(Integer)  # Print System (#1, #2, #3...)
    quality = Column(Float)  # Quality System (10.00% to 100.00%)
    level = Column(Integer, default=1)
    is_locked = Column(Boolean, default=False)

    owner = relationship("User", back_populates="cards")
    base = relationship("CardBase")


engine = create_engine(DATABASE_URL)
Base.metadata.create_all(engine)
SessionLocal = sessionmaker(bind=engine)
