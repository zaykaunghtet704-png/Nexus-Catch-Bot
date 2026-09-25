"""
database.py - Database Connection Setup
"""
import os
from pymongo import MongoClient

MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "nexus_catch_bot")

client = MongoClient(MONGO_URL)
db = client[DB_NAME]

users_col = db["users"]
cards_col = db["cards"]
inventory_col = db["inventory"]
chats_col = db["chats"]
