import logging
import os
import time
from pathlib import Path

from src.database.job_db import (
    claim_ingestion_job,
    fail_ingestion_job,
    finish_ingestion_job,
    init_job_db,
)
from src.rag.ingest import ingest_document
from src.rag.vector_store import delete_document

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger(__name__)


def cleanup_failed_upload(job: dict) -> None:
    """Remove an upload and any partial vectors after terminal failure."""
    try:
        delete_document(job["filename"], job["user_id"])
    except Exception:
        logger.exception(
            "Could not remove partial vectors for failed job: id=%s",
            job["id"],
        )

    try:
        Path(job["file_path"]).unlink(missing_ok=True)
    except OSError:
        logger.exception(
            "Could not remove failed upload: id=%s",
            job["id"],
        )


def run_worker(poll_seconds: float = 2.0) -> None:
    init_job_db()
    logger.info("AtlasGPT ingestion worker started")

    while True:
        job = claim_ingestion_job()
        if job is None:
            time.sleep(poll_seconds)
            continue

        if job.get("status") == "failed":
            cleanup_failed_upload(job)
            continue

        try:
            chunks = ingest_document(job["file_path"], job["user_id"])
            finish_ingestion_job(job["id"], chunks)
            logger.info(
                "Ingestion job completed: id=%s user_id=%s chunks=%d",
                job["id"], job["user_id"], chunks,
            )
        except Exception as error:
            logger.exception("Ingestion job failed: id=%s", job["id"])
            final_status = fail_ingestion_job(
                job["id"],
                str(error),
                retry=job["attempts"] < 3,
            )

            # Keep the source file available while a retry is possible.
            # Once the job is terminal, remove both partial vectors and the
            # unindexed upload so the user can upload the same filename again.
            if final_status == "failed":
                cleanup_failed_upload(job)


if __name__ == "__main__":
    run_worker()
