import os
from pymongo import MongoClient

MONGO_URI = os.getenv("MONGO_URI")

if not MONGO_URI:
    raise ValueError("MONGO_URI environment variable ကို ရှာမတွေ့ပါ။")

client = MongoClient(MONGO_URI)
db = client["waifu_bot_db"]

users_col = db["users"]          
cards_col = db["cards"]          
inventory_col = db["inventory"]  
market_col = db["marketplace"]
