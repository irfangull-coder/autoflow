"""SQLite storage for AutoFlow starter.

Tables:
  orders    - synthetic business orders (seeded from data/orders.json)
  approvals - drafts waiting for human approval (the safety feature)
  logs      - every agent action, so the demo has an audit trail

Only the Python standard library is used here, so this file works
even before FastAPI is installed.
"""
import json
import os
import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
# Render par persistent disk ho to env var se path badlo, masalan:
#   AUTOFLOW_DB_PATH=/data/autoflow.db
# Warna local file hi use hogi. Note: Render free instance par
# redeploy/restart par SQLite file ghaib ho sakti hai — asli
# persistence ke liye baad me Postgres (Neon/Supabase) par jana hoga.
DB_PATH = Path(os.environ.get("AUTOFLOW_DB_PATH", BASE_DIR / "autoflow.db"))
DB_PATH.parent.mkdir(parents=True, exist_ok=True)


def get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    conn = get_db()
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS orders (
            id TEXT PRIMARY KEY,
            customer TEXT NOT NULL,
            product TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            amount INTEGER NOT NULL,
            status TEXT NOT NULL,
            date TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS approvals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task TEXT NOT NULL,
            draft TEXT NOT NULL,
            source TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            agent TEXT NOT NULL,
            action TEXT NOT NULL,
            detail TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );
        """
    )
    count = conn.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
    if count == 0:
        orders_path = BASE_DIR / "data" / "orders.json"
        if orders_path.exists():
            orders = json.loads(orders_path.read_text(encoding="utf-8"))
            conn.executemany(
                "INSERT INTO orders VALUES (?,?,?,?,?,?,?)",
                [
                    (
                        o["id"],
                        o["customer"],
                        o["product"],
                        o["quantity"],
                        o["amount"],
                        o["status"],
                        o["date"],
                    )
                    for o in orders
                ],
            )
    conn.commit()
    conn.close()


def log(agent: str, action: str, detail: str) -> None:
    conn = get_db()
    conn.execute(
        "INSERT INTO logs (agent, action, detail) VALUES (?,?,?)",
        (agent, action, detail),
    )
    conn.commit()
    conn.close()


def get_order(order_id: str) -> dict | None:
    conn = get_db()
    row = conn.execute(
        "SELECT * FROM orders WHERE id = ?", (order_id.upper(),)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def list_orders() -> list[dict]:
    conn = get_db()
    rows = conn.execute("SELECT * FROM orders ORDER BY date DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def create_approval(task: str, draft: str, source: str) -> int:
    conn = get_db()
    cur = conn.execute(
        "INSERT INTO approvals (task, draft, source) VALUES (?,?,?)",
        (task, draft, source),
    )
    approval_id = cur.lastrowid
    conn.commit()
    conn.close()
    return approval_id


def list_approvals() -> list[dict]:
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM approvals ORDER BY id DESC"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def set_approval(approval_id: int, status: str) -> bool:
    conn = get_db()
    cur = conn.execute(
        "UPDATE approvals SET status = ? WHERE id = ?",
        (status, approval_id),
    )
    conn.commit()
    conn.close()
    return cur.rowcount > 0


def list_logs(limit: int = 50) -> list[dict]:
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM logs ORDER BY id DESC LIMIT ?", (limit,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]
