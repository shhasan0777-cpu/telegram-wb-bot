from app.db.connection import db


def schedule_task(user_id: int, task_type: str, run_at: str, payload: str | None = None) -> None:
    with db() as conn:
        conn.execute("INSERT INTO scheduled_tasks(user_id, task_type, run_at, payload) VALUES(?, ?, ?, ?)", (user_id, task_type, run_at, payload))


def due_tasks(now_iso: str, limit: int = 50):
    with db() as conn:
        return conn.execute("SELECT * FROM scheduled_tasks WHERE status='pending' AND run_at <= ? ORDER BY run_at LIMIT ?", (now_iso, limit)).fetchall()


def mark_done(task_id: int) -> None:
    with db() as conn:
        conn.execute("UPDATE scheduled_tasks SET status='done', updated_at=CURRENT_TIMESTAMP WHERE id=?", (task_id,))


def mark_failed(task_id: int, error: str) -> None:
    with db() as conn:
        conn.execute("UPDATE scheduled_tasks SET status='failed', last_error=?, updated_at=CURRENT_TIMESTAMP WHERE id=?", (error[:1000], task_id))
