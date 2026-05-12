import sqlite3
from contextlib import contextmanager
from app.config import get_settings


@contextmanager
def db():
    conn = sqlite3.connect(get_settings().database_path)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
