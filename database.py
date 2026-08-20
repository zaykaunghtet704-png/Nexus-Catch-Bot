class DatabaseManager:
    def __init__(self):
        self.users = {}
        self.group_counts = {}

    def get_user(self, uid: int, name: str = "User"):
        if uid not in self.users:
            self.users[uid] = {
                "name": name,
                "coins": 5000,
                "cards": [],
                "hmode": "ALL",
                "level": 1,
                "is_banned": False,
                "last_claim": 0,
                "last_nclaim": 0
            }
        return self.users[uid]

db = DatabaseManager()
