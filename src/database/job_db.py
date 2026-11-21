import os
import sqlite3
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path


DATABASE_PATH = Path(
    os.getenv("ATLASGPT_JOBS_DB", "data/jobs.db")
)


def _connect():
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DATABASE_PATH, timeout=30)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA journal_mode=WAL")
    connection.execute("PRAGMA busy_timeout=30000")
    return connection


def init_job_db():
    with _connect() as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS ingestion_jobs (
                id TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL,
                filename TEXT NOT NULL,
                file_path TEXT NOT NULL,
                status TEXT NOT NULL CHECK (
                    status IN ('queued', 'processing', 'completed', 'failed')
                ),
                chunks INTEGER,
                error TEXT,
                attempts INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                claimed_at TEXT
            )
        """)
        connection.execute("""
            CREATE INDEX IF NOT EXISTS idx_ingestion_jobs_status_created
            ON ingestion_jobs(status, created_at)
        """)
        connection.execute("""
            CREATE INDEX IF NOT EXISTS idx_ingestion_jobs_user_created
            ON ingestion_jobs(user_id, created_at)
        """)


def create_ingestion_job(user_id: int, filename: str, file_path: str) -> dict:
    if user_id <= 0:
        raise ValueError("user_id must be greater than zero.")
    now = datetime.now(timezone.utc).isoformat()
    job_id = uuid.uuid4().hex
    with _connect() as connection:
        connection.execute("""
            INSERT INTO ingestion_jobs
                (id, user_id, filename, file_path, status, created_at, updated_at)
            VALUES (?, ?, ?, ?, 'queued', ?, ?)
        """, (job_id, user_id, filename, file_path, now, now))
    return get_ingestion_job(job_id, user_id)


def get_ingestion_job(job_id: str, user_id: int) -> dict | None:
    with _connect() as connection:
        row = connection.execute("""
            SELECT id, filename, status, chunks, error, attempts,
                   created_at, updated_at
            FROM ingestion_jobs
            WHERE id = ? AND user_id = ?
        """, (job_id, user_id)).fetchone()
    return dict(row) if row else None


def claim_ingestion_job(lease_seconds: int = 900) -> dict | None:
    now = datetime.now(timezone.utc)
    stale_before = (now - timedelta(seconds=lease_seconds)).isoformat()
    with _connect() as connection:
        connection.execute("BEGIN IMMEDIATE")
        connection.execute("""
            UPDATE ingestion_jobs
            SET status = 'queued', claimed_at = NULL, updated_at = ?
            WHERE status = 'processing' AND claimed_at < ?
        """, (now.isoformat(), stale_before))
        row = connection.execute("""
            SELECT id, user_id, filename, file_path, attempts
            FROM ingestion_jobs
            WHERE status = 'queued'
            ORDER BY created_at ASC
            LIMIT 1
        """).fetchone()
        if row is None:
            return None
        connection.execute("""
            UPDATE ingestion_jobs
            SET status = 'processing', attempts = attempts + 1,
                claimed_at = ?, updated_at = ?
            WHERE id = ? AND status = 'queued'
        """, (now.isoformat(), now.isoformat(), row["id"]))
        return dict(row)


def finish_ingestion_job(job_id: str, chunks: int) -> None:
    now = datetime.now(timezone.utc).isoformat()
    with _connect() as connection:
        connection.execute("""
            UPDATE ingestion_jobs
            SET status = 'completed', chunks = ?, error = NULL,
                claimed_at = NULL, updated_at = ?
            WHERE id = ? AND status = 'processing'
        """, (chunks, now, job_id))


def fail_ingestion_job(
    job_id: str,
    error: str,
    retry: bool = False,
    max_attempts: int = 3,
) -> None:
    now = datetime.now(timezone.utc).isoformat()
    status = "queued" if retry else "failed"
    with _connect() as connection:
        connection.execute("""
            UPDATE ingestion_jobs
            SET status = CASE
                    WHEN ? = 'queued' AND attempts < ? THEN 'queued'
                    ELSE 'failed'
                END,
                error = ?, claimed_at = NULL, updated_at = ?
            WHERE id = ? AND status = 'processing'
        """, (status, max_attempts, error[:500], now, job_id))
