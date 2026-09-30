import os
from pymongo import MongoClient

MONGO_URI = os.getenv("MONGO_URI", "")

# MongoDB connection ကြောင့် crash မဖြစ်အောင် ခဏ ထိန်းထားခြင်း
try:
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=2000)
    db = client["nexus_catch_bot"]
    
    users_col = db["users"]
    chats_col = db["chats"]
    inventory_col = db["inventory"]
    cards_col = db["cards"]
    system_col = db["system"]
    codes_col = db["codes"]
    sudo_col = db["sudo"]
    blacklist_col = db["blacklist"]
except Exception as e:
    print(f"⚠️ MongoDB Connection Warning: {e}")
    # Mock collection objects to prevent module import crash
    class MockCol:
        def __getattr__(self, name):
            return lambda *args, **kwargs: None

    users_col = chats_col = inventory_col = cards_col = system_col = codes_col = sudo_col = blacklist_col = MockCol()
