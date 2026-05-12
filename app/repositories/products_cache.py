import json
from app.db.connection import db


def save_cache(user_id: int, payload: dict) -> None:
    with db() as conn:
        conn.execute("""
            INSERT INTO products_cache(user_id, payload, updated_at)
            VALUES(?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(user_id) DO UPDATE SET payload=excluded.payload, updated_at=CURRENT_TIMESTAMP
        """, (user_id, json.dumps(payload, ensure_ascii=False)))


def get_cache(user_id: int) -> dict | None:
    with db() as conn:
        row = conn.execute("SELECT payload FROM products_cache WHERE user_id=?", (user_id,)).fetchone()
    return json.loads(row["payload"]) if row else None


def delete_cache(user_id: int) -> None:
    with db() as conn:
        conn.execute("DELETE FROM products_cache WHERE user_id=?", (user_id,))
