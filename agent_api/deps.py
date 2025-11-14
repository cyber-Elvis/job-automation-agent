# agent_api/deps.py
import os
from fastapi import Header, HTTPException
from .db import SessionLocal

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Simple API key dependency. Only enforced when API_KEY is set.
API_KEY = os.getenv("API_KEY", "").strip()


def require_api_key(x_api_key: str | None = Header(None)):
    """Require a matching X-API-Key header when API_KEY env var is set.

    - If API_KEY is empty/missing, auth is effectively disabled (no-op).
    - If API_KEY is set and header doesn't match, raise 401.
    """
    if not API_KEY:
        # auth disabled when no API key configured
        return
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized: invalid API key")
    return
