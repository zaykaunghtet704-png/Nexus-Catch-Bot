import os
from pymongo import MongoClient

MONGO_URI = os.getenv("MONGO_URI", "mongodb+srv://username:password@cluster.mongodb.net/?retryWrites=true&w=majority")

try:
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    db = client["nexus_catch_bot"]

    users_col = db["users"]
    chats_col = db["chats"]
    inventory_col = db["inventory"]
    cards_col = db["cards"]
    system_col = db["system"]
    codes_col = db["codes"]
    sudo_col = db["sudo"]
    blacklist_col = db["blacklist"]
    market_col = db["market"]
    wishlist_col = db["wishlist"]
except Exception as e:
    print(f"⚠️ MongoDB Connection Warning: {e}")
    class MockCol:
        def __getattr__(self, name):
            return lambda *args, **kwargs: None

    users_col = chats_col = inventory_col = cards_col = system_col = codes_col = sudo_col = blacklist_col = market_col = wishlist_col = MockCol()
