# AtlasGPT release readiness

This checklist separates the current single-host pilot architecture from requirements for a public commercial launch. A passing test suite is necessary, but it is not proof of production readiness.

## Current product capabilities

- [x] Browser guest sessions and registered accounts
- [x] Session cookies are HttpOnly; production cookie security defaults to enabled
- [x] Configurable trusted frontend origins
- [x] Chat and conversation history
- [x] Per-user document retrieval and document ownership checks
- [x] PDF, TXT, and DOCX ingestion
- [x] Persistent asynchronous ingestion queue and separate worker
- [x] Guest/free/paid entitlement limits enforced by the backend
- [x] Backend and frontend automated CI workflows
- [x] No browser-controlled endpoint for granting paid entitlements

## Required before a public commercial launch

### Security and identity

- [ ] Select and configure a production hosting environment and HTTPS ingress.
- [ ] Add email verification and a secure password-reset flow.
- [ ] Review session lifetime, revocation, concurrent sessions, and guest-account conversion.
- [ ] Replace process-local IP/user rate limiting with a shared limiter (for example Redis) before running multiple API workers or hosts.
- [ ] Add security headers, request-size limits at the reverse proxy, and a documented secrets-rotation procedure.
- [ ] Perform dependency vulnerability scanning and an independent security review.
- [ ] Define privacy policy, terms, data retention, account deletion, and incident-response procedures.

### Data durability and operations

- [ ] Use durable managed database/storage services appropriate to the selected deployment topology.
- [ ] Define automated encrypted backups and prove restore procedures.
- [ ] Add structured log aggregation, metrics, error tracking, and alerting.
- [ ] Add health/readiness checks for the API, Ollama, vector store, and ingestion worker.
- [ ] Test worker restart, queue recovery, disk-full behavior, and backup restoration.
- [ ] Load-test chat and ingestion with realistic document sizes and concurrent users.

### Product and commercial operations

- [ ] Select a payment provider before enabling paid subscriptions.
- [ ] Implement server-verified, signature-checked, idempotent payment webhooks and subscription reconciliation.
- [ ] Add support/contact workflows and a process for handling abuse and account disputes.
- [ ] Validate accessibility, mobile layouts, browser compatibility, and end-to-end user journeys.
- [ ] Publish clear supported-file, usage-limit, privacy, and service-availability documentation.

## Deployment boundary

The current SQLite databases, local upload directory, and persistent ChromaDB directory are a **single-host deployment design**. The API and ingestion worker must share the same durable filesystem and environment configuration. Do not horizontally scale API or worker instances across hosts with independent local disks and expect data consistency.

The Ollama inference service must remain private to the application network. Do not expose its API directly to the public internet.

For a same-origin deployment, configure the reverse proxy to route the frontend's API requests to the FastAPI service. For a separately hosted frontend and API, set the frontend build variable `VITE_API_BASE_URL` to the public HTTPS API origin and configure `FRONTEND_ORIGINS` on the backend to the exact frontend origin. Production frontend builds no longer silently fall back to a visitor's own `localhost:8000`.

## Release gate

A release candidate should not be called production-ready until:

1. Backend tests and frontend typecheck/build/lint pass on the exact candidate commit.
2. The API, worker, frontend, and Ollama have been exercised together in a clean staging environment.
3. Registration, login, guest access, logout, chat, history, upload, ingestion failure/retry, deletion, and cross-user isolation have been tested end to end.
4. Backup restoration, monitoring/alerting, HTTPS, and security configuration have been verified in the target hosting environment.

Payment integration is intentionally not included until a provider is selected. The paid entitlement in the code is an internal capability, not a functioning subscription product.
