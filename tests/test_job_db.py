from src.database import job_db


def test_create_and_get_ingestion_job(tmp_path, monkeypatch):
    monkeypatch.setattr(job_db, "DATABASE_PATH", tmp_path / "jobs.db")
    job_db.init_job_db()

    created = job_db.create_ingestion_job(42, "notes.txt", "/uploads/42/notes.txt")
    fetched = job_db.get_ingestion_job(created["id"], 42)

    assert fetched["status"] == "queued"
    assert fetched["filename"] == "notes.txt"
    assert fetched["chunks"] is None


def test_ingestion_job_is_isolated_by_user(tmp_path, monkeypatch):
    monkeypatch.setattr(job_db, "DATABASE_PATH", tmp_path / "jobs.db")
    job_db.init_job_db()

    created = job_db.create_ingestion_job(42, "private.pdf", "/uploads/private.pdf")

    assert job_db.get_ingestion_job(created["id"], 43) is None


def test_worker_claims_and_completes_job(tmp_path, monkeypatch):
    monkeypatch.setattr(job_db, "DATABASE_PATH", tmp_path / "jobs.db")
    job_db.init_job_db()
    created = job_db.create_ingestion_job(42, "notes.txt", "/uploads/notes.txt")

    claimed = job_db.claim_ingestion_job()

    assert claimed["id"] == created["id"]
    assert claimed["attempts"] == 0

    job_db.finish_ingestion_job(created["id"], 7)
    completed = job_db.get_ingestion_job(created["id"], 42)

    assert completed["status"] == "completed"
    assert completed["chunks"] == 7
    assert job_db.claim_ingestion_job() is None


def test_failed_job_can_be_retried(tmp_path, monkeypatch):
    monkeypatch.setattr(job_db, "DATABASE_PATH", tmp_path / "jobs.db")
    job_db.init_job_db()
    created = job_db.create_ingestion_job(42, "notes.txt", "/uploads/notes.txt")

    first = job_db.claim_ingestion_job()
    assert first["id"] == created["id"]

    job_db.fail_ingestion_job(created["id"], "temporary model outage", retry=True)
    queued = job_db.get_ingestion_job(created["id"], 42)

    assert queued["status"] == "queued"
    assert queued["error"] == "temporary model outage"

    second = job_db.claim_ingestion_job()
    assert second["id"] == created["id"]
    assert second["attempts"] == 1

    job_db.fail_ingestion_job(created["id"], "permanent failure", retry=False)
    failed = job_db.get_ingestion_job(created["id"], 42)

    assert failed["status"] == "failed"


def test_expired_worker_lease_requeues_job(tmp_path, monkeypatch):
    from datetime import datetime, timedelta, timezone
    import sqlite3

    monkeypatch.setattr(job_db, "DATABASE_PATH", tmp_path / "jobs.db")
    job_db.init_job_db()
    created = job_db.create_ingestion_job(42, "retry.txt", "/uploads/retry.txt")
    first = job_db.claim_ingestion_job()

    stale_time = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
    with sqlite3.connect(job_db.DATABASE_PATH) as connection:
        connection.execute(
            "UPDATE ingestion_jobs SET claimed_at = ? WHERE id = ?",
            (stale_time, created["id"]),
        )

    recovered = job_db.claim_ingestion_job(lease_seconds=60)
    assert recovered["id"] == first["id"]


def test_job_database_path_uses_dotenv_configuration(
    tmp_path, monkeypatch
):
    import importlib
    from dotenv import load_dotenv as original_load_dotenv

    previous_path = job_db.DATABASE_PATH
    configured_path = tmp_path / "custom-jobs.db"

    def fake_load_dotenv():
        monkeypatch.setenv("ATLASGPT_JOBS_DB", str(configured_path))
        return True

    monkeypatch.setattr("dotenv.load_dotenv", fake_load_dotenv)

    try:
        importlib.reload(job_db)
        assert job_db.DATABASE_PATH == configured_path
    finally:
        job_db.DATABASE_PATH = previous_path
        job_db.load_dotenv = original_load_dotenv
