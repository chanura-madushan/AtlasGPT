# AtlasGPT bug and reliability audit

**Audit branch:** `audit/full-system-checkup`  
**Review base:** `feature/frontend-experience`  
**Pull request:** [#5 — Audit fixes](https://github.com/chanura-madushan/AtlasGPT/pull/5)  
**Audit date:** 2026-11-22

## Scope and validation boundary

Reviewed the current API, authentication/session flow, upload endpoints, ingestion queue and worker, SQLite persistence, ChromaDB access, embedding response handling, conversation prompt construction, frontend API configuration, dashboard upload flow, test setup, and release-readiness documentation.

This was a source-level review through the repository. The complete runtime stack (Windows environment, Ollama model server, ChromaDB persistence, browser, API and worker processes) was not available for an end-to-end run during this audit. The regression tests below have been added, but their execution is pending CI. Do not interpret this report as a claim that every possible bug has been eliminated.

## Bugs found and changes made

| # | Finding | Impact | Change |
|---|---|---|---|
| 1 | The ingestion job database path was resolved before the worker loaded the project `.env`. | API and worker could use different SQLite queue files when `ATLASGPT_JOBS_DB` was customised; jobs would remain queued. | Load dotenv configuration before resolving `DATABASE_PATH`. Added a configuration regression test. |
| 2 | Terminally failed ingestion jobs left their uploaded file behind. | Re-uploading the same filename returned a duplicate conflict even though the document had never been indexed. | The worker now removes the failed upload and attempts to remove partial vectors after terminal failure. The queue returns exhausted stale jobs to the worker for cleanup. |
| 3 | A document could be deleted while its ingestion job was queued or processing. | The worker could later process a missing file, retry it, and ultimately leave a confusing failed job. | Added an active-job query and return HTTP 409 when deletion is attempted during ingestion. |
| 4 | Two concurrent uploads could pass the initial existence check and overwrite the same destination file. | One user's upload could replace another in-flight upload with the same filename. | Upload persistence now uses exclusive file creation (`xb`) and returns HTTP 409 if the path already exists. Added a regression test proving the original file is not overwritten. |
| 5 | Expired rate-limit identity buckets were retained indefinitely if those identities never made another request. | Long-running API processes could accumulate stale IP/user keys in memory. | Added periodic cleanup of expired buckets under the rate-limit lock. Added a regression test for stale-key eviction. |
| 6 | Embedding responses were checked for count but not vector contents or dimensions. | Empty, non-numeric, non-finite, or dimension-mismatched vectors could reach ChromaDB and fail later or corrupt an ingestion attempt. | Validate each vector for non-empty finite numeric values and consistent dimensions across batches. Added malformed-vector and cross-batch tests. |
| 7 | Production frontend builds silently defaulted to `http://localhost:8000`. | A deployed user's browser would try to contact its own machine instead of the hosted API unless the variable was explicitly configured. | Development retains the localhost default; production uses `VITE_API_BASE_URL` when set, otherwise same-origin routing. Deployment documentation now explains both configurations. |
| 8 | API tests used the default job database and upload directory in some cases. | Test runs could touch persistent working-tree data and interfere with local development or other tests. | The API test fixture now redirects the queue database and upload directory into per-test temporary storage. |
| 9 | Document policy instructions were concatenated into the same prompt text as conversation and retrieved content. | The policy did not use Ollama's dedicated system-prompt field, weakening separation between instructions and untrusted document text. | Pass AtlasGPT's policy through Ollama's `system` field and keep document context/user question in the prompt. Added request-payload and conversation-engine regression coverage. |

## Regression tests added or extended

- `tests/test_job_db.py`: dotenv path resolution, retry status, and exhausted stale-lease handoff.
- `tests/test_worker_cleanup.py`: cleanup of terminal failed uploads and file cleanup when vector deletion errors.
- `tests/test_api.py`: exclusive upload creation, rate-limit bucket eviction, active-ingestion deletion conflict, and temporary test storage.
- `tests/test_embeddings.py`: invalid vectors and inconsistent dimensions across embedding batches.
- `tests/test_conversation_engine.py`: system prompt is supplied separately from the document/user prompt.
- `tests/test_ollama_client.py`: Ollama receives the dedicated system field.

**Automated CI result:** on audit commit `71119e14d75c4916f3dcc969c73d9791e62c8207`, GitHub Actions completed successfully:
- Backend: **189 passed, 1 warning** (Python 3.13).
- Frontend: **production build and ESLint passed** (Node.js 22).

The single backend warning is a Starlette TestClient deprecation warning about passing cookies per request. It did not fail the suite.

**Still unverified:** the user's Windows runtime and full staging integration with the real Ollama service, persistent ChromaDB, API, worker, and browser. Automated CI does not prove those components work together on the target machine.

## Remaining findings and release blockers

These are not represented as fixed:

1. **Worker lease heartbeat:** the queue uses a 15-minute lease. A long-running ingestion can outlive the lease and be reclaimed while the original worker is still processing. Add a lease heartbeat with ownership-safe renewal before relying on multiple workers or long-running ingestion.
2. **Crash-safe cleanup:** the worker can crash after a job is marked failed but before the source file/partial vectors are removed. Cleanup should become a durable, retryable queue state rather than a best-effort action.
3. **Rate limiting is process-local:** the current limiter is not shared across multiple API workers or hosts. Use a shared store such as Redis before horizontal scaling.
4. **Single-host persistence:** SQLite, local uploads, and persistent local ChromaDB require API and worker processes to share one durable host/filesystem. This is not a multi-host architecture.
5. **Retrieval quality needs evaluation:** the current retriever asks ChromaDB for a small top-k set and then applies a distance threshold. A relevant chunk outside that initial set can be missed. Tune top-k, chunking, hybrid retrieval, and reranking against a labelled evaluation set rather than changing thresholds blindly.
6. **Document extraction limitations:** scanned/image-only PDFs do not have OCR, and DOCX extraction currently focuses on paragraphs rather than all possible embedded structures such as tables. These are feature limitations, not verified regressions.
7. **Production identity and operations:** email verification, password recovery, security review, shared rate limiting, HTTPS ingress, monitoring/alerting, backup/restore testing, and load testing remain necessary.
8. **Payments:** paid plan limits exist internally, but there is no payment provider, checkout flow, or verified subscription webhook. Do not advertise paid subscriptions as operational.

## Language decision

No Rust, C++, or other language was introduced.

The inspected hot paths primarily call Ollama for embedding and generation, then perform I/O against ChromaDB and SQLite. No profiling evidence currently identifies Python CPU-bound code as the bottleneck. Rewriting those orchestration paths would add complexity without improving embedding model quality or inference speed. Reconsider Rust only if profiling identifies a CPU-heavy component such as parsing, transformation, or reranking that justifies a native extension.

## Release decision

**Not yet production-ready.** The changes in PR #5 are targeted reliability and correctness improvements. Merge only after CI passes, then run the full Windows/API/worker/Ollama/browser integration checklist and address the remaining blockers above.
