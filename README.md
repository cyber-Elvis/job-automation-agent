# Job Automation Agent (FastAPI)


Runs both **locally** and in **GitHub Codespaces**.


## Quickstart (Local)


```bash
# inside the repo root
python -m venv .venv
# Windows PowerShell:
. .venv/Scripts/Activate.ps1
# macOS/Linux:
# source .venv/bin/activate


pip install --upgrade pip
pip install -r requirements.txt


uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Alternatively, the job ingestion API runs under `agent_api`:

```bash
uvicorn agent_api.main:app --reload --host 0.0.0.0 --port 8000
```

## Database (dev)

This project includes a tiny helper to create the database tables locally for development.

1. Set your DATABASE_URL environment variable (optional). Example for the compose Postgres service:

	 - Windows (cmd):
		 set DATABASE_URL=postgresql://jobagent:jobagent@localhost:5432/jobagent

	 - PowerShell:
		 $env:DATABASE_URL = 'postgresql://jobagent:jobagent@localhost:5432/jobagent'

2. Create tables:

	 python scripts\create_tables.py

Notes: `scripts/create_tables.py` calls `Base.metadata.create_all(...)` and is intended for development. For production schema management use Alembic migrations.

## Endpoints

Key routes exposed by `agent_api`:

| Method | Path                         | Description |
|--------|------------------------------|-------------|
| GET    | `/health`                    | API health check |
| GET    | `/collectors/rss/health`     | RSS collector health |
| POST   | `/collectors/rss/collect`    | Parse an RSS/Atom feed (no DB write) |
| POST   | `/collectors/rss/collect-and-store` | Parse and bulk-insert items (skips duplicates) |
| POST   | `/collectors/rss/collect-from`      | Queue/synchronously collect+store by URL |
| GET    | `/jobs`                      | List jobs (q, source, limit, offset) |
| GET    | `/jobs/stats`                | Per-source counts and last published |

Notes:
- Bulk insert uses PostgreSQL `ON CONFLICT DO NOTHING` on `(source, link)` to avoid duplicate errors.
- Background scheduling is available if you set env vars: `RSS_COLLECT_URL` and optional `RSS_COLLECT_INTERVAL_SECONDS` (default 900).

## Optional Features

Some capabilities are intentionally optional so the core API can run in minimal environments.

### Structured Extraction (extruct + w3lib)
The helper `agent_api.extract.structured.extract_jobposting(url, ua)` attempts to parse JSON-LD `JobPosting` objects from a single page. It requires:

```
extruct
w3lib
```

If either library is missing, the function safely returns an empty list (no ImportError). Install them (already pinned in `requirements.txt`) if you want automatic enrichment:

```bash
pip install extruct w3lib
```

### Scheduling (APScheduler)
Periodic RSS collection uses APScheduler. Set these environment variables to enable it:

```
RSS_COLLECT_URL=https://example.com/feed.xml
RSS_COLLECT_INTERVAL_SECONDS=900   # optional; default 900 seconds
```

If `APScheduler` is not installed, the app logs a warning and skips scheduler setup (no crash). To add scheduling support:

```bash
pip install APScheduler
```

### Verifying Optional Components
After installing optional packages, restart the application. You should see log lines similar to:

```
[collectors] included: rss_generic
INFO Scheduled RSS collector for url=... interval=900s
```

And structured extraction calls will populate `company` / `location` automatically when JSON-LD data contains them.

