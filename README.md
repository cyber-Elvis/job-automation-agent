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