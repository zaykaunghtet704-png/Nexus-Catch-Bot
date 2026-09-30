import os
from pymongo import MongoClient

# MongoDB Connection URI
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")

client = MongoClient(MONGO_URI)

# Database Name Definition (db object ကို တိုက်ရိုက်ထုတ်ပေးထားပါသည်)
db = client["nexus_catcher_db"]

# Collections
users_col = db["users"]
inventory_col = db["inventory"]
cards_col = db["cards"]
market_col = db["market"]
wishlist_col = db["wishlist"]
sudo_col = db["sudo"]
codes_col = db["codes"]
chats_col = db["chats"]
