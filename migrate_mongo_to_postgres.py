"""One-time MongoDB -> PostgreSQL migration.

Set MONGO_URI and DATABASE_URL, then run:
    python migrate_mongo_to_postgres.py

The script copies every collection and preserves Mongo document IDs as strings.
It is safe to re-run: existing PostgreSQL documents are updated by ID.
"""
import os
from datetime import date, datetime
from decimal import Decimal

from bson import ObjectId
from pymongo import MongoClient
from psycopg2.extras import Json

from database import _session


MONGO_URI = os.getenv("MONGO_URI")
if not MONGO_URI:
    raise RuntimeError("MONGO_URI မတွေ့ပါ။ MongoDB connection string ထည့်ပါ။")


def convert(value):
    if isinstance(value, ObjectId):
        return str(value)
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, dict):
        return {str(k): convert(v) for k, v in value.items()}
    if isinstance(value, list):
        return [convert(v) for v in value]
    if isinstance(value, tuple):
        return [convert(v) for v in value]
    return value


def main():
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=10000)
    client.admin.command("ping")

    source = client[os.getenv("MONGO_DB_NAME", "nexus_catcher_db")]
    copied_total = 0

    try:
        for collection_name in source.list_collection_names():
            collection = source[collection_name]
            copied = 0

            with _session() as conn:
                with conn.cursor() as cur:
                    for original in collection.find({}):
                        document = dict(original)
                        raw_id = document.pop("_id", None)
                        if raw_id is None:
                            continue
                        document_id = str(raw_id)
                        safe_document = convert(document)
                        cur.execute(
                            """
                            INSERT INTO nexus_documents
                                (collection_name, document_id, document)
                            VALUES (%s, %s, %s)
                            ON CONFLICT (collection_name, document_id)
                            DO UPDATE SET document = EXCLUDED.document
                            """,
                            (collection_name, document_id, Json(safe_document)),
                        )
                        copied += 1

            copied_total += copied
            print(f"{collection_name}: {copied} documents copied")

        print(f"Migration complete: {copied_total} documents copied.")
    finally:
        client.close()


if __name__ == "__main__":
    main()
