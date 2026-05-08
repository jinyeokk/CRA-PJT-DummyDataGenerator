import sqlite3
from pathlib import Path
from contextlib import contextmanager


DB_PATH = Path(__file__).parent / "dummy_data.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS products (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT    NOT NULL,
    category    TEXT    NOT NULL,
    price       REAL    NOT NULL,
    stock       INTEGER NOT NULL,
    description TEXT,
    created_at  TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS orders (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    order_number  TEXT    NOT NULL UNIQUE,
    product_id    INTEGER NOT NULL,
    quantity      INTEGER NOT NULL,
    total_price   REAL    NOT NULL,
    status        TEXT    NOT NULL,
    customer_name TEXT    NOT NULL,
    created_at    TEXT    NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (product_id) REFERENCES products(id)
);
"""


def get_connection(db_path: str | None = None) -> sqlite3.Connection:
    path = db_path or str(DB_PATH)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


@contextmanager
def transaction(db_path: str | None = None):
    conn = get_connection(db_path)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db(db_path: str | None = None) -> None:
    with transaction(db_path) as conn:
        conn.executescript(SCHEMA)


def reset_db(db_path: str | None = None) -> None:
    with transaction(db_path) as conn:
        conn.executescript("""
            DROP TABLE IF EXISTS orders;
            DROP TABLE IF EXISTS products;
        """)
    init_db(db_path)
