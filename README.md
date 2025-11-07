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