import os
from pymongo import MongoClient

# Environment Variable မှ MONGO_URI ခေါ်ယူခြင်း
MONGO_URI = os.getenv("MONGO_URI")

if not MONGO_URI:
    print("⚠️ MONGO_URI မတွေ့ရှိပါ။ Local MongoDB ကို ချိတ်ဆက်ပါမည်။")
    MONGO_URI = "mongodb://localhost:27017"

# 🛑 WriteConcernError မတက်စေရန် w=1 ထည့်သွင်းပေးခြင်း
client = MongoClient(MONGO_URI, w=1)

# Database Name
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
