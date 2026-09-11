import json
import sqlite3
from pathlib import Path

from app.models import Item

import hashlib
import json


def content_hash(item: Item) -> str:
    content = {
        "title": item.title,
        "body": item.body,
        "url": item.url,
        "published_at": (
            item.published_at.isoformat()
            if item.published_at
            else None
        ),
        "metadata": item.metadata,
    }

    raw = json.dumps(
        content,
        sort_keys=True,
        ensure_ascii=False
    )

    return hashlib.sha256(
        raw.encode("utf-8")
    ).hexdigest()


DB_PATH = Path("data/watchtower.db")


def init_db():
    DB_PATH.parent.mkdir(exist_ok=True)

    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
                     CREATE TABLE IF NOT EXISTS items
                     (
                         id
                         TEXT
                         PRIMARY
                         KEY,
                         source
                         TEXT
                         NOT
                         NULL,
                         category
                         TEXT
                         NOT
                         NULL,
                         title
                         TEXT
                         NOT
                         NULL,
                         body
                         TEXT,
                         url
                         TEXT,
                         published_at
                         TEXT,
                         metadata
                         TEXT,
                         content_hash
                         TEXT
                         NOT
                         NULL,
                         first_seen_at
                         DATETIME
                         DEFAULT
                         CURRENT_TIMESTAMP,
                         updated_at
                         DATETIME
                         DEFAULT
                         CURRENT_TIMESTAMP
                     )
                     """)

        conn.execute("""
                     CREATE TABLE IF NOT EXISTS settings
                     (
                         key
                         TEXT
                         PRIMARY
                         KEY,
                         value
                         TEXT
                         NOT
                         NULL
                     )
                     """)


def get_setting(key: str) -> str | None:
    with sqlite3.connect(DB_PATH) as conn:
        row = conn.execute(
            """
            SELECT value
            FROM settings
            WHERE key = ?
            """,
            (key,)
        ).fetchone()

    return row[0] if row else None


def set_setting(key: str, value: str):
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            INSERT INTO settings (key, value)
            VALUES (?, ?) ON CONFLICT(key)
                    DO
            UPDATE SET value = excluded.value
            """,
            (key, value)
        )


def get_item_hash(item_id: str) -> str | None:
    with sqlite3.connect(DB_PATH) as conn:
        row = conn.execute(
            """
            SELECT content_hash
            FROM items
            WHERE id = ?
            """,
            (item_id,)
        ).fetchone()

    return row[0] if row else None


def save_item(item: Item):
    item_hash = content_hash(item)

    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            INSERT INTO items (id,
                               source,
                               category,
                               title,
                               body,
                               url,
                               published_at,
                               metadata,
                               content_hash)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                item.id,
                item.source,
                item.category,
                item.title,
                item.body,
                item.url,
                (
                    item.published_at.isoformat()
                    if item.published_at
                    else None
                ),
                json.dumps(
                    item.metadata,
                    ensure_ascii=False
                ),
                item_hash,
            )
        )


def update_item(item: Item):
    item_hash = content_hash(item)

    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            UPDATE items
            SET title        = ?,
                body         = ?,
                url          = ?,
                published_at = ?,
                metadata     = ?,
                content_hash = ?,
                updated_at   = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (
                item.title,
                item.body,
                item.url,
                (
                    item.published_at.isoformat()
                    if item.published_at
                    else None
                ),
                json.dumps(
                    item.metadata,
                    ensure_ascii=False
                ),
                item_hash,
                item.id,
            )
        )
