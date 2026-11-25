"""PostgreSQL-backed document store with a small PyMongo-compatible API.

The bot modules use a document-style API. This adapter stores each document as
JSONB in PostgreSQL, allowing the database engine to change without rewriting
all game and economy features.
"""
import copy
from contextlib import contextmanager
import json
import os
import re
import uuid
from enum import Enum

import psycopg2
from psycopg2.extras import Json, RealDictCursor


DATABASE_URL = os.getenv("DATABASE_URL") or os.getenv("POSTGRES_URL")
if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL မတွေ့ပါ။ Render PostgreSQL ရဲ့ Internal Database URL "
        "ကို Environment Variables ထဲတွင် DATABASE_URL အဖြစ်ထည့်ပါ။"
    )


class ReturnDocument(Enum):
    BEFORE = 0
    AFTER = 1


def _connect():
    url = DATABASE_URL
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://"):]
    kwargs = {"connect_timeout": 10}
    if "localhost" not in url and "127.0.0.1" not in url and "sslmode=" not in url:
        kwargs["sslmode"] = "require"
    return psycopg2.connect(url, **kwargs)


@contextmanager
def _session():
    connection = _connect()
    try:
        with connection:
            yield connection
    finally:
        connection.close()


def _json_default(value):
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return str(value)


def _path(document, path):
    value = document
    for part in path.split("."):
        if not isinstance(value, dict) or part not in value:
            return _MISSING
        value = value[part]
    return value


def _compare(value, condition):
    if not isinstance(condition, dict) or not any(str(k).startswith("$") for k in condition):
        return value == condition
    for op, expected in condition.items():
        if op == "$options":
            continue
        if op == "$exists":
            exists = value is not _MISSING
            if exists != bool(expected):
                return False
        elif op == "$ne":
            if value == expected:
                return False
        elif op == "$in":
            if value not in expected:
                return False
        elif op == "$nin":
            if value in expected:
                return False
        elif op == "$gte":
            if value is _MISSING or value is None or value < expected:
                return False
        elif op == "$gt":
            if value is _MISSING or value is None or value <= expected:
                return False
        elif op == "$lte":
            if value is _MISSING or value is None or value > expected:
                return False
        elif op == "$lt":
            if value is _MISSING or value is None or value >= expected:
                return False
        elif op == "$regex":
            if value is _MISSING or value is None:
                return False
            flags = re.IGNORECASE if "i" in str(condition.get("$options", "")) else 0
            if not re.search(str(expected), str(value), flags):
                return False
        else:
            return False
    return True


_MISSING = object()


def _matches(document, query):
    for key, expected in (query or {}).items():
        if key == "$or":
            if not any(_matches(document, item) for item in expected):
                return False
        elif key == "$and":
            if not all(_matches(document, item) for item in expected):
                return False
        elif key == "$nor":
            if any(_matches(document, item) for item in expected):
                return False
        else:
            value = _path(document, key)
            if value is _MISSING:
                value = _MISSING
            if not _compare(value, expected):
                return False
    return True


def _project(document, projection):
    if not projection:
        return copy.deepcopy(document)
    include = [k for k, v in projection.items() if v and k != "_id"]
    exclude = [k for k, v in projection.items() if not v]
    if include:
        result = {}
        for key in include:
            value = _path(document, key)
            if value is not _MISSING:
                result[key] = value
        if projection.get("_id", 1) and "_id" in document:
            result["_id"] = document["_id"]
        return result
    result = copy.deepcopy(document)
    for key in exclude:
        result.pop(key, None)
    return result


class InsertOneResult:
    def __init__(self, inserted_id):
        self.inserted_id = inserted_id


class UpdateResult:
    def __init__(self, matched_count=0, modified_count=0, upserted_id=None):
        self.matched_count = matched_count
        self.modified_count = modified_count
        self.upserted_id = upserted_id


class DeleteResult:
    def __init__(self, deleted_count=0):
        self.deleted_count = deleted_count


class Cursor:
    def __init__(self, documents):
        self.documents = list(documents)
    def sort(self, key, direction=1):
        if isinstance(key, list):
            for field, order in reversed(key):
                self.sort(field, order)
        else:
            self.documents.sort(
                key=lambda d: (_path(d, key) is None, _path(d, key)),
                reverse=(direction < 0),
            )
        return self
    def limit(self, count):
        if count:
            self.documents = self.documents[:count]
        return self
    def __iter__(self):
        return iter(self.documents)
    def __len__(self):
        return len(self.documents)


class PostgresCollection:
    def __init__(self, name):
        self.name = name

    def _load(self, cursor=None, for_update=False):
        cursor.execute(
            "SELECT document_id, document FROM nexus_documents "
            "WHERE collection_name = %s" + (" FOR UPDATE" if for_update else ""),
            (self.name,),
        )
        rows = cursor.fetchall()
        result = []
        for row in rows:
            doc = dict(row["document"] or {})
            doc["_id"] = row["document_id"]
            result.append(doc)
        return result

    def insert_one(self, document):
        doc = copy.deepcopy(document)
        doc_id = str(doc.pop("_id", None) or uuid.uuid4().hex)
        with _session() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO nexus_documents(collection_name, document_id, document) "
                    "VALUES (%s, %s, %s)",
                    (self.name, doc_id, Json(doc, dumps=lambda x: json.dumps(x, default=_json_default))),
                )
        return InsertOneResult(doc_id)

    def find(self, query=None, projection=None):
        with _session() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                docs = self._load(cur)
        return Cursor(_project(d, projection) for d in docs if _matches(d, query or {}))

    def find_one(self, query=None, projection=None):
        docs = self.find(query, projection).limit(1)
        return docs.documents[0] if docs.documents else None

    def count_documents(self, query=None):
        return sum(1 for d in self.find(query))

    def distinct(self, key, query=None):
        values = []
        for doc in self.find(query):
            value = _path(doc, key)
            if value is not _MISSING and value not in values:
                values.append(value)
        return values

    def _apply_update(self, doc, update, inserting=False):
        result = copy.deepcopy(doc)
        if not any(str(k).startswith("$") for k in update):
            result = copy.deepcopy(update)
            if "_id" in doc:
                result["_id"] = doc["_id"]
            return result
        for op, fields in update.items():
            if op == "$set" or (op == "$setOnInsert" and inserting):
                for key, value in fields.items():
                    result[key] = copy.deepcopy(value)
            elif op == "$inc":
                for key, value in fields.items():
                    result[key] = (result.get(key) or 0) + value
            elif op == "$push":
                for key, value in fields.items():
                    arr = list(result.get(key) or [])
                    if isinstance(value, dict) and "$each" in value:
                        arr.extend(value["$each"])
                    else:
                        arr.append(value)
                    result[key] = arr
            elif op == "$addToSet":
                for key, value in fields.items():
                    arr = list(result.get(key) or [])
                    values = value.get("$each", []) if isinstance(value, dict) and "$each" in value else [value]
                    for item in values:
                        if item not in arr:
                            arr.append(item)
                    result[key] = arr
            elif op == "$pull":
                for key, value in fields.items():
                    result[key] = [x for x in (result.get(key) or []) if x != value]
            elif op == "$unset":
                for key in fields:
                    result.pop(key, None)
        return result

    def update_one(self, query, update, upsert=False):
        with _session() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                docs = self._load(cur, for_update=True)
                target = next((d for d in docs if _matches(d, query or {})), None)
                if target:
                    new_doc = self._apply_update(target, update)
                    body = dict(new_doc)
                    body.pop("_id", None)
                    cur.execute(
                        "UPDATE nexus_documents SET document=%s "
                        "WHERE collection_name=%s AND document_id=%s",
                        (Json(body, dumps=lambda x: json.dumps(x, default=_json_default)), self.name, str(target["_id"])),
                    )
                    return UpdateResult(1, int(new_doc != target))
                if upsert:
                    base = {k: v for k, v in (query or {}).items() if not k.startswith("$") and not isinstance(v, dict)}
                    new_doc = self._apply_update(base, update, inserting=True)
                    new_id = str(new_doc.pop("_id", None) or uuid.uuid4().hex)
                    cur.execute(
                        "INSERT INTO nexus_documents(collection_name,document_id,document) VALUES(%s,%s,%s)",
                        (self.name, new_id, Json(new_doc, dumps=lambda x: json.dumps(x, default=_json_default))),
                    )
                    return UpdateResult(0, 0, new_id)
        return UpdateResult()

    def update_many(self, query, update):
        matched = modified = 0
        with _session() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                docs = self._load(cur, for_update=True)
                for target in docs:
                    if _matches(target, query or {}):
                        matched += 1
                        new_doc = self._apply_update(target, update)
                        body = dict(new_doc)
                        body.pop("_id", None)
                        cur.execute(
                            "UPDATE nexus_documents SET document=%s WHERE collection_name=%s AND document_id=%s",
                            (Json(body, dumps=lambda x: json.dumps(x, default=_json_default)), self.name, str(target["_id"])),
                        )
                        modified += int(new_doc != target)
        return UpdateResult(matched, modified)

    def delete_one(self, query):
        with _session() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                docs = self._load(cur, for_update=True)
                target = next((d for d in docs if _matches(d, query or {})), None)
                if not target:
                    return DeleteResult()
                cur.execute(
                    "DELETE FROM nexus_documents WHERE collection_name=%s AND document_id=%s",
                    (self.name, str(target["_id"])),
                )
                return DeleteResult(cur.rowcount)

    def delete_many(self, query):
        deleted = 0
        with _session() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                docs = self._load(cur, for_update=True)
                ids = [str(d["_id"]) for d in docs if _matches(d, query or {})]
                for doc_id in ids:
                    cur.execute(
                        "DELETE FROM nexus_documents WHERE collection_name=%s AND document_id=%s",
                        (self.name, doc_id),
                    )
                    deleted += cur.rowcount
        return DeleteResult(deleted)

    def find_one_and_delete(self, query):
        with _session() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                docs = self._load(cur, for_update=True)
                target = next((d for d in docs if _matches(d, query or {})), None)
                if not target:
                    return None
                cur.execute(
                    "DELETE FROM nexus_documents WHERE collection_name=%s AND document_id=%s",
                    (self.name, str(target["_id"])),
                )
                return target

    def find_one_and_update(self, query, update, upsert=False, return_document=ReturnDocument.BEFORE):
        with _session() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                docs = self._load(cur, for_update=True)
                target = next((d for d in docs if _matches(d, query or {})), None)
                if target:
                    new_doc = self._apply_update(target, update)
                    body = dict(new_doc)
                    body.pop("_id", None)
                    cur.execute(
                        "UPDATE nexus_documents SET document=%s WHERE collection_name=%s AND document_id=%s",
                        (Json(body, dumps=lambda x: json.dumps(x, default=_json_default)), self.name, str(target["_id"])),
                    )
                    return new_doc if return_document == ReturnDocument.AFTER else target
                if upsert:
                    base = {k: v for k, v in (query or {}).items() if not k.startswith("$") and not isinstance(v, dict)}
                    new_doc = self._apply_update(base, update, inserting=True)
                    new_id = str(new_doc.pop("_id", None) or uuid.uuid4().hex)
                    cur.execute(
                        "INSERT INTO nexus_documents(collection_name,document_id,document) VALUES(%s,%s,%s)",
                        (self.name, new_id, Json(new_doc, dumps=lambda x: json.dumps(x, default=_json_default))),
                    )
                    new_doc["_id"] = new_id
                    return new_doc
        return None

    def aggregate(self, pipeline):
        docs = list(self.find())
        for stage in pipeline:
            if "$match" in stage:
                docs = [d for d in docs if _matches(d, stage["$match"])]
            elif "$sample" in stage:
                import random
                random.shuffle(docs)
                docs = docs[:int(stage["$sample"].get("size", 1))]
            elif "$group" in stage:
                spec = stage["$group"]
                grouped = {}
                for doc in docs:
                    key_expr = spec.get("_id")
                    key = _path(doc, key_expr[1:]) if isinstance(key_expr, str) and key_expr.startswith("$") else key_expr
                    bucket = grouped.setdefault(key, {"_id": key})
                    for field, expression in spec.items():
                        if field == "_id":
                            continue
                        if isinstance(expression, dict) and "$sum" in expression:
                            amount = expression["$sum"]
                            value = _path(doc, amount[1:]) if isinstance(amount, str) and amount.startswith("$") else amount
                            bucket[field] = bucket.get(field, 0) + (value or 0)
                docs = list(grouped.values())
            elif "$sort" in stage:
                for field, direction in reversed(list(stage["$sort"].items())):
                    docs.sort(key=lambda d: (d.get(field) is None, d.get(field)), reverse=direction < 0)
            elif "$limit" in stage:
                docs = docs[:int(stage["$limit"])]
        return Cursor(docs)


class PostgresDatabase:
    def __getitem__(self, name):
        return PostgresCollection(str(name))


# Initialize schema and lightweight indexes once at process start.
with _session() as _conn:
    with _conn.cursor() as _cur:
        _cur.execute("""
            CREATE TABLE IF NOT EXISTS nexus_documents (
                collection_name TEXT NOT NULL,
                document_id TEXT NOT NULL,
                document JSONB NOT NULL DEFAULT '{}'::jsonb,
                PRIMARY KEY (collection_name, document_id)
            )
        """)
        _cur.execute(
            "CREATE INDEX IF NOT EXISTS nexus_documents_collection_idx "
            "ON nexus_documents(collection_name)"
        )

db = PostgresDatabase()
users_col = db["users"]
inventory_col = db["inventory"]
cards_col = db["cards"]
market_col = db["market"]
wishlist_col = db["wishlist"]
sudo_col = db["sudo"]
codes_col = db["codes"]
chats_col = db["chats"]
group_user_totals_col = db["group_user_totals"]
top_global_groups_col = db["top_global_groups"]
system_col = db["system"]
blacklist_col = db["blacklist"]
