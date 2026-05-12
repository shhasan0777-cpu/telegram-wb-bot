from app.db.connection import db
from app.services.security import encrypt_wb_api_key, decrypt_wb_api_key


def create_session(user_id: int, stage: str = "api_key") -> None:
    with db() as conn:
        conn.execute("DELETE FROM wb_unit_sessions WHERE user_id=?", (user_id,))
        conn.execute("INSERT INTO wb_unit_sessions(user_id, stage) VALUES(?, ?)", (user_id, stage))


def get_last_session(user_id: int):
    with db() as conn:
        return conn.execute("SELECT * FROM wb_unit_sessions WHERE user_id=? ORDER BY id DESC LIMIT 1", (user_id,)).fetchone()


def update_session(session_id: int, **kwargs) -> None:
    if "api_key" in kwargs and kwargs["api_key"] and not str(kwargs["api_key"]).startswith("enc:"):
        kwargs["api_key"] = encrypt_wb_api_key(kwargs["api_key"])
    fields = ", ".join(f"{k}=?" for k in kwargs)
    values = list(kwargs.values()) + [session_id]
    with db() as conn:
        conn.execute(f"UPDATE wb_unit_sessions SET {fields}, updated_at=CURRENT_TIMESTAMP WHERE id=?", values)


def get_session_api_key(session) -> str | None:
    return decrypt_wb_api_key(session["api_key"] if session else None)
