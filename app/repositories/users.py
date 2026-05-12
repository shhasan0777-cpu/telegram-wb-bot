from app.db.connection import db


def save_user(user_id: int, username: str | None = None) -> None:
    with db() as conn:
        conn.execute("INSERT OR IGNORE INTO users(user_id, username) VALUES(?, ?)", (user_id, username))
        if username:
            conn.execute("UPDATE users SET username=? WHERE user_id=?", (username, user_id))


def get_user(user_id: int):
    with db() as conn:
        return conn.execute("SELECT * FROM users WHERE user_id=?", (user_id,)).fetchone()


def update_user(user_id: int, **kwargs) -> None:
    if not kwargs:
        return
    fields = ", ".join(f"{k}=?" for k in kwargs)
    values = list(kwargs.values()) + [user_id]
    with db() as conn:
        conn.execute(f"UPDATE users SET {fields} WHERE user_id=?", values)
