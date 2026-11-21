import logging
import os
import time

from src.database.job_db import (
    claim_ingestion_job,
    fail_ingestion_job,
    finish_ingestion_job,
    init_job_db,
)
from src.rag.ingest import ingest_document

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger(__name__)


def run_worker(poll_seconds: float = 2.0) -> None:
    init_job_db()
    logger.info("AtlasGPT ingestion worker started")

    while True:
        job = claim_ingestion_job()
        if job is None:
            time.sleep(poll_seconds)
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
            fail_ingestion_job(
                job["id"],
                str(error),
                retry=job["attempts"] < 3,
            )


if __name__ == "__main__":
    run_worker()
