import os
import json
from config import DB_FILE, OWNER_IDS

class DatabaseManager:
    def __init__(self):
        self.data = {
            "users": {},
            "groups": {},
            "market": {},
            "auctions": {},
            "sudos": [],
            "cards_master": {
                "0021": {"name": "Astraea Celestial Guardian", "rarity": 13, "series": "Fate", "atk": 950, "def": 880, "hp": 2400},
                "0022": {"name": "Luna Cosmic Librarian", "rarity": 9, "series": "Overlord", "atk": 450, "def": 500, "hp": 1800},
                "0023": {"name": "Naruto Uzumaki", "rarity": 7, "series": "Naruto", "atk": 700, "def": 650, "hp": 2000}
            }
        }
        self.load_db()

    def load_db(self):
        if os.path.exists(DB_FILE):
            try:
                with open(DB_FILE, "r", encoding="utf-8") as f:
                    self.data = json.load(f)
            except Exception:
                pass

    def save_db(self):
        with open(DB_FILE, "w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=4, ensure_ascii=False)

    def get_user(self, uid: int, name: str = "User"):
        uid_str = str(uid)
        if uid_str not in self.data["users"]:
            self.data["users"][uid_str] = {
                "name": name,
                "lang": "MM",
                "coins": 5000,
                "cards": [
                    {"id": "0021", "print": 1, "mint": 100, "level": 1, "frame": "Gold", "dye": "#FF0055"}
                ],
                "favorites": [],
                "last_claim": 0,
                "last_daily": 0,
                "quests": {"daily_messages": 0, "completed": False}
            }
            self.save_db()
        return self.data["users"][uid_str]

    def get_group(self, chat_id: int):
        cid_str = str(chat_id)
        if cid_str not in self.data["groups"]:
            self.data["groups"][cid_str] = {
                "spawn_rate": 10,
                "msg_count": 0,
                "approved": True,
                "spawned_card": None,
                "last_spawn_time": 0
            }
            self.save_db()
        return self.data["groups"][cid_str]

    def is_admin_or_owner(self, uid: int):
        return (uid in OWNER_IDS) or (str(uid) in self.data["sudos"])

db = DatabaseManager()
