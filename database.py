import time

class DatabaseManager:
    def __init__(self):
        self.users = {}
        self.group_counts = {}
        self.cards_db = {}
        self.sudo_users = set()

    def get_user(self, uid: int, name: str = "User"):
        if uid not in self.users:
            self.users[uid] = {
                "name": name,
                "coins": 5000,
                "cards": [],       # [{id, card_key, print_num, mint, frame, dye, font, level}]
                "inventory": {"frames": ["Neon", "Gold"], "dyes": ["#FF0055", "#00FFFF"], "fonts": ["Gothic", "Comic"]},
                "hmode": "ALL",
                "is_banned": False,
                "last_claim": 0,
                "last_nclaim": 0,
                "rank_points": 0,
                "guild": None
            }
        return self.users[uid]

    def is_owner_or_sudo(self, uid: int, owner_ids: list):
        return (uid in owner_ids) or (uid in self.sudo_users)

db = DatabaseManager()
