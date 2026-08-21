import time

class DatabaseManager:
    def __init__(self):
        self.users = {}
        self.group_settings = {}  # {chat_id: {"spawn_rate": 85, "msg_count": 0, "approved": False}}
        self.market_listings = {} # {listing_id: {seller_id, card_data, price}}
        self.sudo_users = set()
        self.cards_master = {
            "0021": {"name": "Astraea Guardian", "rarity": "10", "price": 15000},
            "0022": {"name": "Shadow Assassin", "rarity": "7", "price": 9000},
            "0023": {"name": "Cyber Valkyrie", "rarity": "5", "price": 5000}
        }

    def get_user(self, uid: int, name: str = "User"):
        if uid not in self.users:
            self.users[uid] = {
                "name": name,
                "lang": "MM",
                "coins": 5000,
                "cards": [],       # [{id, card_key, print_num, mint, level, exp}]
                "favorites": [],
                "hmode": "ALL",
                "last_claim": 0,
                "today_catches": 0
            }
        return self.users[uid]

    def get_group(self, chat_id: int):
        if chat_id not in self.group_settings:
            self.group_settings[chat_id] = {
                "spawn_rate": 85,
                "msg_count": 0,
                "approved": False,
                "group_catches": {}
            }
        return self.group_settings[chat_id]

    def is_owner_or_sudo(self, uid: int, owner_ids: list):
        return (uid in owner_ids) or (uid in self.sudo_users)

db = DatabaseManager()
