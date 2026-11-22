# Backend worker and deployment configuration

## Configuration

Copy `.env.example` to `.env` and set values for the target environment.

In production:
- Set `ATLASGPT_ENV=production`.
- Set `FRONTEND_ORIGINS` to the exact HTTPS origin(s) serving the frontend.
- Keep `COOKIE_SECURE=true` (the production default).
- Keep `.env` out of version control.
- Put Ollama behind a private network; do not expose its port publicly.

## Asynchronous document ingestion

The API supports two upload paths:

- `POST /documents/upload`: waits until indexing completes.
- `POST /documents/upload-async`: stores the file and returns HTTP 202 with a job ID.

For asynchronous uploads, run the API and at least one ingestion worker as separate processes:

```powershell
# Terminal 1: API
python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000

# Terminal 2: ingestion worker
python -m src.workers.ingestion_worker
```

Poll `GET /documents/jobs/{job_id}` until the status is `completed` or `failed`.

The API and worker must share:
- The same `.env` configuration.
- The same `data/jobs.db` file.
- The same uploaded-files directory.
- The same ChromaDB persistent data directory.

Do not run the worker in an isolated container without shared persistent storage. A worker lease is recovered after 15 minutes if a process exits while holding a job. Failed jobs are retried up to three attempts.

## Current deployment boundary

The persistent job queue is suitable for a single-host pilot where API and worker share a durable filesystem. It is not a substitute for a distributed queue and object storage in a multi-host deployment. SQLite and local ChromaDB also remain single-host storage choices. Move those services to PostgreSQL, shared object storage, and a supported remote vector database before horizontally scaling across hosts.

## Health and operational checks

Before exposing the service:
- Terminate TLS at a trusted reverse proxy or platform ingress.
- Restrict API and Ollama network access.
- Persist and back up `data/` (including the account database, job database, uploads, and ChromaDB).
- Configure log collection and alerting.
- Test restore procedures.
- Load-test uploads and chat with realistic concurrent usage.
