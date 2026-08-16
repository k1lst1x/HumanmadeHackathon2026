import json
import os
import sqlite3
import time
import uuid
from contextlib import contextmanager

DB_PATH = os.environ.get("TEXTSHOP_DB", "textshop.db")
DATABASE_URL = os.environ.get("DATABASE_URL", "").strip()
USE_POSTGRES = bool(DATABASE_URL)

SQLITE_SCHEMA = """
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
CREATE INDEX IF NOT EXISTS idx_jobs_state ON jobs(state);
CREATE INDEX IF NOT EXISTS idx_ledger_job_kind ON ledger(job_id, kind);
CREATE INDEX IF NOT EXISTS idx_decisions_created ON decisions(created_at);
"""

POSTGRES_SCHEMA = """
CREATE TABLE IF NOT EXISTS jobs (
    id TEXT PRIMARY KEY,
    thread_id TEXT NOT NULL,
    state TEXT NOT NULL,
    data JSONB NOT NULL,
    created_at DOUBLE PRECISION NOT NULL,
    updated_at DOUBLE PRECISION NOT NULL
);
CREATE TABLE IF NOT EXISTS outcomes (
    id BIGSERIAL PRIMARY KEY,
    job_id TEXT NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
    price_cents INTEGER NOT NULL,
    accepted INTEGER NOT NULL,
    build_seconds DOUBLE PRECISION,
    verify_cost_cents INTEGER,
    created_at DOUBLE PRECISION NOT NULL
);
CREATE TABLE IF NOT EXISTS ledger (
    id BIGSERIAL PRIMARY KEY,
    job_id TEXT REFERENCES jobs(id) ON DELETE SET NULL,
    kind TEXT NOT NULL,
    amount_cents INTEGER NOT NULL,
    note TEXT,
    created_at DOUBLE PRECISION NOT NULL
);
CREATE TABLE IF NOT EXISTS decisions (
    id BIGSERIAL PRIMARY KEY,
    job_id TEXT REFERENCES jobs(id) ON DELETE SET NULL,
    kind TEXT NOT NULL,
    summary TEXT NOT NULL,
    detail TEXT,
    created_at DOUBLE PRECISION NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_jobs_thread ON jobs(thread_id);
CREATE INDEX IF NOT EXISTS idx_jobs_state ON jobs(state);
CREATE INDEX IF NOT EXISTS idx_jobs_updated ON jobs(updated_at DESC);
CREATE INDEX IF NOT EXISTS idx_ledger_job_kind ON ledger(job_id, kind);
CREATE INDEX IF NOT EXISTS idx_ledger_created ON ledger(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_decisions_created ON decisions(created_at DESC);
"""


@contextmanager
def conn():
    if USE_POSTGRES:
        import psycopg
        from psycopg.rows import dict_row

        c = psycopg.connect(DATABASE_URL, row_factory=dict_row)
    else:
        c = sqlite3.connect(DB_PATH, timeout=30)
        c.row_factory = sqlite3.Row
    try:
        yield c
        c.commit()
    finally:
        c.close()


def backend_name():
    return "postgres" if USE_POSTGRES else "sqlite"


def _sql(query):
    return query.replace("?", "%s") if USE_POSTGRES else query


def _execute(c, query, params=()):
    return c.execute(_sql(query), params)


def _dict(row):
    return dict(row) if row is not None else None


def _json_data(data):
    if USE_POSTGRES:
        from psycopg.types.json import Jsonb

        return Jsonb(data)
    return json.dumps(data, separators=(",", ":"))


def init():
    with conn() as c:
        if USE_POSTGRES:
            for statement in POSTGRES_SCHEMA.split(";"):
                statement = statement.strip()
                if statement:
                    c.execute(statement)
        else:
            c.executescript(SQLITE_SCHEMA)


def seed_float(amount_cents):
    with conn() as c:
        row = _execute(
            c, "SELECT COUNT(*) AS n FROM ledger WHERE kind = 'seed'"
        ).fetchone()
        if row["n"] == 0:
            _execute(
                c,
                "INSERT INTO ledger (job_id, kind, amount_cents, note, created_at) VALUES (?, ?, ?, ?, ?)",
                (None, "seed", amount_cents, "starting float", time.time()),
            )


def create_job(thread_id, state, data):
    job_id = uuid.uuid4().hex[:12]
    now = time.time()
    with conn() as c:
        _execute(
            c,
            "INSERT INTO jobs (id, thread_id, state, data, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
            (job_id, thread_id, state, _json_data(data), now, now),
        )
    return job_id


def get_job(job_id):
    with conn() as c:
        row = _execute(c, "SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
    return _row_to_job(row) if row else None


def active_job_for_thread(thread_id):
    with conn() as c:
        row = _execute(
            c,
            "SELECT * FROM jobs WHERE thread_id = ? AND state NOT IN ('DONE', 'ABANDONED') ORDER BY created_at DESC LIMIT 1",
            (thread_id,),
        ).fetchone()
    return _row_to_job(row) if row else None


def save_job(job):
    with conn() as c:
        _execute(
            c,
            "UPDATE jobs SET state = ?, data = ?, updated_at = ? WHERE id = ?",
            (job["state"], _json_data(job["data"]), time.time(), job["id"]),
        )


def _row_to_job(row):
    data = row["data"]
    if isinstance(data, str):
        data = json.loads(data)
    return {
        "id": row["id"],
        "thread_id": row["thread_id"],
        "state": row["state"],
        "data": data,
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


def record_outcome(job_id, price_cents, accepted, build_seconds=None, verify_cost_cents=None):
    with conn() as c:
        _execute(
            c,
            "INSERT INTO outcomes (job_id, price_cents, accepted, build_seconds, verify_cost_cents, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (
                job_id,
                price_cents,
                1 if accepted else 0,
                build_seconds,
                verify_cost_cents,
                time.time(),
            ),
        )


def recent_outcomes(limit=20):
    with conn() as c:
        rows = _execute(
            c, "SELECT * FROM outcomes ORDER BY created_at DESC LIMIT ?", (limit,)
        ).fetchall()
    return [_dict(r) for r in rows]


def post_ledger(kind, amount_cents, job_id=None, note=None):
    with conn() as c:
        _execute(
            c,
            "INSERT INTO ledger (job_id, kind, amount_cents, note, created_at) VALUES (?, ?, ?, ?, ?)",
            (job_id, kind, amount_cents, note, time.time()),
        )


def has_ledger(job_id, kind):
    with conn() as c:
        row = _execute(
            c,
            "SELECT COUNT(*) AS n FROM ledger WHERE job_id = ? AND kind = ?",
            (job_id, kind),
        ).fetchone()
    return row["n"] > 0


def balance_cents():
    with conn() as c:
        row = _execute(c, "SELECT COALESCE(SUM(amount_cents), 0) AS b FROM ledger").fetchone()
    return row["b"]


def log_decision(kind, summary, job_id=None, detail=None):
    with conn() as c:
        _execute(
            c,
            "INSERT INTO decisions (job_id, kind, summary, detail, created_at) VALUES (?, ?, ?, ?, ?)",
            (job_id, kind, summary, detail, time.time()),
        )


def recent_decisions(limit=50):
    with conn() as c:
        rows = _execute(
            c, "SELECT * FROM decisions ORDER BY created_at DESC LIMIT ?", (limit,)
        ).fetchall()
    return [_dict(r) for r in rows]


def recent_ledger(limit=50):
    with conn() as c:
        rows = _execute(
            c, "SELECT * FROM ledger ORDER BY created_at DESC LIMIT ?", (limit,)
        ).fetchall()
    return [_dict(r) for r in rows]


def recent_jobs(limit=25):
    with conn() as c:
        rows = _execute(
            c,
            "SELECT id, thread_id, state, data, created_at, updated_at FROM jobs ORDER BY updated_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
    jobs = []
    for row in rows:
        job = _row_to_job(row)
        data = job["data"]
        jobs.append(
            {
                "id": job["id"],
                "thread_id": job["thread_id"],
                "state": job["state"],
                "price_cents": data.get("price_cents"),
                "scope": (data.get("scope") or {}).get("summary"),
                "artifact_url": data.get("artifact_url"),
                "checkout_id": data.get("checkout_id"),
                "verify_cost_cents": data.get("verify_cost_cents"),
                "created_at": job["created_at"],
                "updated_at": job["updated_at"],
            }
        )
    return jobs


def pnl():
    with conn() as c:
        rows = _execute(
            c,
            "SELECT kind, COALESCE(SUM(amount_cents), 0) AS total, COUNT(*) AS n FROM ledger GROUP BY kind",
        ).fetchall()
        jobs_done = _execute(
            c, "SELECT COUNT(*) AS n FROM jobs WHERE state = 'DONE'"
        ).fetchone()["n"]
        jobs_open = _execute(
            c, "SELECT COUNT(*) AS n FROM jobs WHERE state NOT IN ('DONE', 'ABANDONED')"
        ).fetchone()["n"]
    by_kind = {r["kind"]: {"total_cents": r["total"], "count": r["n"]} for r in rows}
    return {
        "db_backend": backend_name(),
        "balance_cents": balance_cents(),
        "revenue_cents": by_kind.get("revenue", {}).get("total_cents", 0),
        "verify_spend_cents": abs(by_kind.get("verify", {}).get("total_cents", 0)),
        "compute_spend_cents": abs(by_kind.get("compute", {}).get("total_cents", 0)),
        "jobs_done": jobs_done,
        "jobs_open": jobs_open,
        "by_kind": by_kind,
    }
