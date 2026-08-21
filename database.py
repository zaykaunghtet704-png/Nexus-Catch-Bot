class DatabaseManager:
    def __init__(self):
        self.users = {}
        self.group_settings = {}
        self.market_listings = {}
        self.sudo_users = set()

    def get_user(self, uid: int, name: str = "User"):
        if uid not in self.users:
            self.users[uid] = {
                "name": name,
                "lang": "MM",
                "coins": 5000,
                "cards": [
                    {"id": "0021", "name": "Astraea Guardian", "rarity": "10", "level": 1, "price": 15000}
                ],
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
                "approved": True, # Test လုပ်ရလွယ်အောင် True ပေးထားသည်
                "spawned_card": None,
                "group_catches": {}
            }
        return self.group_settings[chat_id]

    def is_owner_or_sudo(self, uid: int, owner_ids: list):
        return (uid in owner_ids) or (uid in self.sudo_users)

db = DatabaseManager()
