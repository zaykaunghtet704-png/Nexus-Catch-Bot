import os
from pymongo import MongoClient

# MongoDB လိပ်စာကို ဤနေရာတွင် တိုက်ရိုက်ထည့်ပါ (အပေါ်က Username/Password ထည့်ထားပြီးသား Link အပြည့်အစုံ)
MONGO_URI = "mongodb+srv://3Maybe:Nsnenfnddn283_283@cluster0.vdys92x.mongodb.net/?appName=Cluster0"

if not MONGO_URI:
    raise ValueError("MONGO_URI ကို ထည့်သွင်းရန် လိုအပ်ပါသည်။")

# MongoDB client ချိတ်ဆက်ခြင်း
client = MongoClient(MONGO_URI)
db = client["nexus_catch_bot"] # Database နာမည်

# Collection များ
users_col = db["users"]
cards_col = db["cards"]
inventory_col = db["inventory"]
