import os
from pymongo import MongoClient

# MongoDB လိပ်စာကို ဤနေရာတွင် တိုက်ရိုက်ထည့်ပါ
MONGO_URI = "mongodb+srv://3Maybe:Nsnenfnddn283_283@cluster0.vdys92x.mongodb.net/?appName=Cluster0"

# MongoDB client ချိတ်ဆက်ခြင်း
client = MongoClient(MONGO_URI)
db = client["nexus_catch_bot"]

# Collection များ
users_col = db["users"]
cards_col = db["cards"]
inventory_col = db["inventory"]
