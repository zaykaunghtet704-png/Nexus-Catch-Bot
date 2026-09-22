import json
import os

DATA_DIR = "data"
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

class LocalCollection:
    def __init__(self, filename):
        self.filepath = os.path.join(DATA_DIR, filename)
        if not os.path.exists(self.filepath):
            self._save([])

    def _load(self):
        try:
            with open(self.filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []

    def _save(self, data):
        with open(self.filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

    def find_one(self, query):
        data = self._load()
        for item in data:
            if all(item.get(k) == v for k, v in query.items()):
                return item
        return None

    def insert_one(self, document):
        data = self._load()
        data.append(document)
        self._save(data)

    def insert_many(self, documents):
        data = self._load()
        for doc in documents:
            data.append(doc)
        self._save(data)

    def update_one(self, query, update):
        data = self._load()
        updated = False
        for item in data:
            if all(item.get(k) == v for k, v in query.items()):
                if "$set" in update:
                    for k, v in update["$set"].items():
                        item[k] = v
                    updated = True
                if "$inc" in update:
                    for k, v in update["$inc"].items():
                        item[k] = item.get(k, 0) + v
                        updated = True
        if updated:
            self._save(data)

    def find(self, query=None):
        data = self._load()
        if not query:
            return data
        result = []
        for item in data:
            if all(item.get(k) == v for k, v in query.items()):
                result.append(item)
        return result

    def count_documents(self, query=None):
        data = self._load()
        if not query:
            return len(data)
        count = 0
        for item in data:
            if all(item.get(k) == v for k, v in query.items()):
                count += 1
        return count

users_col = LocalCollection("users.json")
cards_col = LocalCollection("cards.json")
inventory_col = LocalCollection("inventory.json")
