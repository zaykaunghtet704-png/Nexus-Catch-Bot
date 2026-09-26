import os
from pymongo import MongoClient

# MongoDB Connection URL (Render Environment Variable သို့မဟုတ် Default URI)
MONGO_URI = os.getenv("MONGO_URI", "mongodb+srv://username:password@cluster.mongodb.net/?retryWrites=true&w=majority")

# MongoDB Client initialization
client = MongoClient(MONGO_URI)

# Database Name
db = client["nexus_catch_bot"]

# All Database Collections
users_col = db["users"]
chats_col = db["chats"]
inventory_col = db["inventory"]
cards_col = db["cards"]
system_col = db["system"]       # 🛠️ Maintenance & Lockdown အတွက် လိုအပ်သော Collection
codes_col = db["codes"]         # 🎁 Redeem Codes အတွက် လိုအပ်သော Collection
sudo_col = db["sudo"]           # 👑 Admin/Sudo Users များအတွက်
blacklist_col = db["blacklist"] # 🚫 Global Blacklist အတွက်
