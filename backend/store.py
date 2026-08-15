import json
import os
import sqlite3
import time
import uuid
from contextlib import contextmanager

DB_PATH = os.environ.get("TEXTSHOP_DB", "textshop.db")

SCHEMA = """
CREATE TABLE IF NOT EXISTS jobs (
    id TEXT PRIMARY KEY,
    thread_id TEXT NOT NULL,
    state TEXT NOT NULL,
    data TEXT NOT NULL,
    created_at REAL NOT NULL,
    updated_at REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS outcomes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id TEXT NOT NULL,
    price_cents INTEGER NOT NULL,
    accepted INTEGER NOT NULL,
    build_seconds REAL,
    verify_cost_cents INTEGER,
    created_at REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS ledger (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id TEXT,
    kind TEXT NOT NULL,
    amount_cents INTEGER NOT NULL,
    note TEXT,
    created_at REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS decisions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id TEXT,
    kind TEXT NOT NULL,
    summary TEXT NOT NULL,
    detail TEXT,
    created_at REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_jobs_thread ON jobs(thread_id);
"""


@contextmanager
def conn():
    c = sqlite3.connect(DB_PATH, timeout=30)
    c.row_factory = sqlite3.Row
    try:
        yield c
        c.commit()
    finally:
        c.close()


def init():
    with conn() as c:
        c.executescript(SCHEMA)


def seed_float(amount_cents):
    with conn() as c:
        row = c.execute(
            "SELECT COUNT(*) AS n FROM ledger WHERE kind = 'seed'"
        ).fetchone()
        if row["n"] == 0:
            c.execute(
                "INSERT INTO ledger (job_id, kind, amount_cents, note, created_at) VALUES (?, ?, ?, ?, ?)",
                (None, "seed", amount_cents, "starting float", time.time()),
            )


def create_job(thread_id, state, data):
    job_id = uuid.uuid4().hex[:12]
    now = time.time()
    with conn() as c:
        c.execute(
            "INSERT INTO jobs (id, thread_id, state, data, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
            (job_id, thread_id, state, json.dumps(data), now, now),
        )
    return job_id


def get_job(job_id):
    with conn() as c:
        row = c.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
    return _row_to_job(row) if row else None


def active_job_for_thread(thread_id):
    with conn() as c:
        row = c.execute(
            "SELECT * FROM jobs WHERE thread_id = ? AND state NOT IN ('DONE', 'ABANDONED') ORDER BY created_at DESC LIMIT 1",
            (thread_id,),
        ).fetchone()
    return _row_to_job(row) if row else None


def save_job(job):
    with conn() as c:
        c.execute(
            "UPDATE jobs SET state = ?, data = ?, updated_at = ? WHERE id = ?",
            (job["state"], json.dumps(job["data"]), time.time(), job["id"]),
        )


def _row_to_job(row):
    return {
        "id": row["id"],
        "thread_id": row["thread_id"],
        "state": row["state"],
        "data": json.loads(row["data"]),
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


def record_outcome(job_id, price_cents, accepted, build_seconds=None, verify_cost_cents=None):
    with conn() as c:
        c.execute(
            "INSERT INTO outcomes (job_id, price_cents, accepted, build_seconds, verify_cost_cents, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (job_id, price_cents, 1 if accepted else 0, build_seconds, verify_cost_cents, time.time()),
        )


def recent_outcomes(limit=20):
    with conn() as c:
        rows = c.execute(
            "SELECT * FROM outcomes ORDER BY created_at DESC LIMIT ?", (limit,)
        ).fetchall()
    return [dict(r) for r in rows]


def post_ledger(kind, amount_cents, job_id=None, note=None):
    with conn() as c:
        c.execute(
            "INSERT INTO ledger (job_id, kind, amount_cents, note, created_at) VALUES (?, ?, ?, ?, ?)",
            (job_id, kind, amount_cents, note, time.time()),
        )


def balance_cents():
    with conn() as c:
        row = c.execute("SELECT COALESCE(SUM(amount_cents), 0) AS b FROM ledger").fetchone()
    return row["b"]


def log_decision(kind, summary, job_id=None, detail=None):
    with conn() as c:
        c.execute(
            "INSERT INTO decisions (job_id, kind, summary, detail, created_at) VALUES (?, ?, ?, ?, ?)",
            (job_id, kind, summary, detail, time.time()),
        )


def recent_decisions(limit=50):
    with conn() as c:
        rows = c.execute(
            "SELECT * FROM decisions ORDER BY created_at DESC LIMIT ?", (limit,)
        ).fetchall()
    return [dict(r) for r in rows]


def pnl():
    with conn() as c:
        rows = c.execute(
            "SELECT kind, COALESCE(SUM(amount_cents), 0) AS total, COUNT(*) AS n FROM ledger GROUP BY kind"
        ).fetchall()
        jobs_done = c.execute(
            "SELECT COUNT(*) AS n FROM jobs WHERE state = 'DONE'"
        ).fetchone()["n"]
        jobs_open = c.execute(
            "SELECT COUNT(*) AS n FROM jobs WHERE state NOT IN ('DONE', 'ABANDONED')"
        ).fetchone()["n"]
    by_kind = {r["kind"]: {"total_cents": r["total"], "count": r["n"]} for r in rows}
    return {
        "balance_cents": balance_cents(),
        "revenue_cents": by_kind.get("revenue", {}).get("total_cents", 0),
        "verify_spend_cents": abs(by_kind.get("verify", {}).get("total_cents", 0)),
        "compute_spend_cents": abs(by_kind.get("compute", {}).get("total_cents", 0)),
        "jobs_done": jobs_done,
        "jobs_open": jobs_open,
        "by_kind": by_kind,
    }
