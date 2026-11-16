# Product Requirements Document: Autonomous Job-Matching Agent

**Status:** Draft for implementation  
**Product:** Job Match Agent  
**Primary users:** Job seekers  
**Job source:** Adzuna API

## 1. Product summary

Build a service that lets a job seeker upload a resume, save job-search preferences, and receive relevant Adzuna job listings ranked with an explainable match score from 0 to 100. A background worker periodically retrieves new listings, avoids duplicates, and creates or updates matches without requiring the user to keep the application open.

The agent assists discovery only. It does not apply for jobs, contact employers, or make hiring decisions.

## 2. Problem

Job seekers must repeatedly search multiple listings and manually compare each role with their experience, skills, and preferences. This is time-consuming, makes it easy to miss new opportunities, and offers little consistent explanation for why a listing is or is not relevant.

## 3. Goals and success measures

### Goals

- Make resume-based job discovery straightforward and repeatable.
- Keep job listings current through scheduled, fault-tolerant Adzuna polling.
- Rank jobs consistently and explain the factors contributing to each score.
- Keep API credentials and resume data private and under the user's control.

### Success measures

- A user can upload a supported resume and configure a search without assistance.
- New matching listings are visible after a successful polling cycle, with duplicates suppressed.
- Every displayed score is between 0 and 100 and includes a human-readable explanation.
- Failed polling runs are recorded, retried according to policy, and observable by operators.
- Users can replace or delete their resume and account data.

## 4. Users and primary workflow

1. A user creates an account and provides search preferences (for example, keywords, location, distance, and remote preference).
2. The user uploads a PDF resume and reviews or corrects extracted profile details.
3. The service stores the resume securely and generates a normalized candidate profile.
4. A scheduled background job fetches eligible listings from Adzuna, handles pagination, and upserts listings by their source identifier.
5. The matching pipeline compares new or changed listings with eligible user profiles and stores scores and explanations.
6. The user reviews, filters, saves, dismisses, or marks listings as applied.
7. The service continues polling in the background and surfaces newly matched listings.

## 5. Scope

### MVP features

- Account access and per-user search preferences.
- PDF resume upload, text extraction, profile review, replacement, and deletion.
- Adzuna API integration using server-side credentials.
- Configurable scheduled polling with pagination, timeouts, rate-limit handling, retry/backoff, and run status.
- Job normalization, source-ID deduplication, and listing expiry/update handling.
- Explainable 0–100 matching with a persisted score and factor-level rationale.
- Job search and filters, saved/dismissed/applied states, and a new-match view.
- Basic operational logs, health checks, and error monitoring.

### Out of scope for MVP

- Automatically applying to jobs or messaging employers.
- Scraping job sites or using sources other than Adzuna.
- Ranking candidates for employers or making employment decisions.
- Guaranteed real-time results; polling frequency is subject to Adzuna limits and configured cadence.
- Non-PDF resume formats unless added with their own extraction and validation support.

## 6. Functional requirements

### Resume and profile

- Accept PDF files only in the initial release; enforce configurable size limits and validate actual file content, not only the filename or browser-provided MIME type.
- Reject encrypted, malformed, empty, or unsupported files with a useful error.
- Extract text without silently treating an extraction failure as a valid empty profile.
- Let users review and edit extracted skills, titles, experience, location, and other matching-relevant fields.
- Store resume files outside the public web root, restrict access to their owner and authorized services, and support permanent deletion.

### Adzuna ingestion

- Keep the Adzuna application ID and API key in server-side secret configuration; never return them to clients or write them to logs.
- Fetch jobs using saved searches and the configured polling interval. Schedule polling in a dedicated worker system rather than relying on an in-process web-server timer.
- Respect API quotas and terms, set connection/read timeouts, paginate results, and retry transient failures with bounded exponential backoff.
- Persist polling-run status, timestamps, result counts, and sanitized failure details.
- Upsert listings by source and source job ID; avoid duplicate notifications and reprocess listings when relevant fields change.
- Support pausing a user's search and a global operator pause.

### Matching and job results

- Produce a deterministic baseline score in the range 0–100 using documented, configurable factors such as skills, role/title alignment, experience/seniority, location/work-mode preferences, and semantic relevance.
- Normalize missing data explicitly; do not interpret missing job or resume fields as a positive match.
- Show the score with factor-level reasons and distinguish required qualifications from optional preferences.
- Recompute scores when the resume/profile, preferences, or relevant listing fields change.
- Allow users to filter by score, location, date, and work mode, and mark jobs saved, dismissed, or applied.
- Do not use an LLM as the sole scoring authority. If an LLM assists with extraction or semantic comparison, validate its structured output and retain a deterministic, auditable score calculation.

## 7. Non-functional and production requirements

- **Reliability:** Separate web/API processes from scheduled workers; jobs must be safe to retry and idempotent.
- **Security:** Use TLS in transit, least-privilege service credentials, secret management, authorization checks on every user-owned resource, and encryption at rest for databases and file storage.
- **Privacy:** Collect only required data; define retention periods; provide account/resume deletion; avoid logging resume text, API keys, or sensitive profile data.
- **File safety:** Apply upload size/type limits, content validation, and malware scanning before processing. Keep uploads private and use short-lived authorized downloads if downloads are supported.
- **Performance:** Paginate job results and perform ingestion/matching asynchronously. Set explicit request and upstream API timeouts.
- **Observability:** Track polling success/failure, API latency and rate limits, queue depth, retries, matching failures, and service health; alert on sustained ingestion failures.
- **Operations:** Support schema migrations, backups and restore testing, graceful worker shutdown, configuration validation at startup, and separate development/staging/production settings.
- **Compliance:** Follow Adzuna API terms, attribution and rate limits, and applicable privacy and data-protection requirements.

## 8. Proposed stack

| Area | Technology |
|---|---|
| API | Python 3.14+, FastAPI, Uvicorn, Pydantic Settings |
| Adzuna client | HTTPX |
| Background scheduling and tasks | Celery worker + Celery Beat |
| Broker / task result backend | Redis |
| Persistence | PostgreSQL, SQLAlchemy, Alembic, psycopg 3 |
| Resume processing | `python-multipart` for uploads, pypdf for PDF text extraction |
| Matching / agent workflows | Deterministic Python scoring first; LangChain, LangGraph, and LangChain OpenAI integration only for bounded extraction or semantic comparison where needed |
| Deployment | Containerized API, worker, and scheduler; managed PostgreSQL/Redis and private object storage in production |

The API and worker share application services and persistence rules. Celery Beat triggers periodic ingestion; workers fetch and normalize listings, then enqueue idempotent matching work. Redis is infrastructure and must be configured with appropriate persistence/availability for the chosen deployment. PostgreSQL is the source of truth for users, preferences, listings, matches, and task/run metadata.

## 9. Core data concepts

- **User:** account identifier and lifecycle state.
- **Search preference:** Adzuna query/location parameters, work preferences, cadence, and enabled state.
- **Resume/profile:** private file reference, extracted text/profile fields, version, and processing state.
- **Job listing:** source identifier, normalized listing fields, source timestamps, and last-seen/expiry state.
- **Match:** user, resume/profile version, listing, score, factor breakdown, computation version, and user status.
- **Polling run:** search, start/end time, status, counts, retry information, and sanitized error summary.

## 10. Acceptance criteria

- A user can upload a valid PDF and receives either a reviewed profile or a clear processing error.
- Invalid and oversized uploads are rejected before normal processing.
- A configured search can be polled by a background worker while no user is signed in.
- Repeating the same Adzuna response does not create duplicate jobs or duplicate new-match events.
- A transient Adzuna error is retried within configured limits and is visible in operational status.
- Each eligible listing has a reproducible 0–100 score, stored factor breakdown, and explanation.
- A changed resume, preference, or listing causes an appropriate match refresh.
- One user cannot access another user's resume, profile, or match data.
- Deleting a resume/account removes or schedules deletion of associated private data according to the retention policy.

## 11. Assumptions and decisions to confirm

- The initial resume format is PDF.
- The service uses one platform-managed Adzuna credential set; credentials are not supplied by end users.
- Polling cadence and supported Adzuna regions/search parameters will be configured to stay within the account's API limits.
- Authentication provider, hosting provider, upload limits, retention period, and exact scoring weights must be selected before production launch.
- LLM use is optional; the MVP can launch with deterministic matching and add validated semantic assistance later.
