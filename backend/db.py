import sqlite3
from pathlib import Path
from datetime import datetime

DB_PATH = Path(__file__).parent / "stocksense.db"


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db():
    conn = get_conn()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS products (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT    NOT NULL UNIQUE,
            unit        TEXT    NOT NULL DEFAULT '件',
            stock       INTEGER NOT NULL DEFAULT 0,
            price       REAL    NOT NULL DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS purchase_history (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id  INTEGER NOT NULL REFERENCES products(id),
            quantity    INTEGER NOT NULL DEFAULT 1,
            purchased_at TEXT  NOT NULL
        );
    """)
    conn.commit()
    conn.close()


# ── Products ──────────────────────────────────────────────

def add_product(name: str, unit: str, stock: int, price: float) -> int:
    conn = get_conn()
    cur = conn.execute(
        "INSERT INTO products (name, unit, stock, price) VALUES (?, ?, ?, ?)",
        (name, unit, stock, price),
    )
    conn.commit()
    pid = cur.lastrowid
    conn.close()
    return pid


def list_products() -> list[dict]:
    conn = get_conn()
    rows = conn.execute("SELECT * FROM products ORDER BY id").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def update_stock(product_id: int, stock: int):
    conn = get_conn()
    conn.execute("UPDATE products SET stock = ? WHERE id = ?", (stock, product_id))
    conn.commit()
    conn.close()


def update_price(product_id: int, price: float):
    conn = get_conn()
    conn.execute("UPDATE products SET price = ? WHERE id = ?", (price, product_id))
    conn.commit()
    conn.close()


# ── Purchase History ──────────────────────────────────────

def add_purchase(product_id: int, quantity: int, purchased_at: str | None = None):
    if purchased_at is None:
        purchased_at = datetime.now().strftime("%Y-%m-%d")
    conn = get_conn()
    conn.execute(
        "INSERT INTO purchase_history (product_id, quantity, purchased_at) VALUES (?, ?, ?)",
        (product_id, quantity, purchased_at),
    )
    # 同时增加库存
    conn.execute(
        "UPDATE products SET stock = stock + ? WHERE id = ?",
        (quantity, product_id),
    )
    conn.commit()
    conn.close()


def get_purchases(product_id: int) -> list[dict]:
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM purchase_history WHERE product_id = ? ORDER BY purchased_at",
        (product_id,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]
