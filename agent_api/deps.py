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
    """Require X-API-Key header only when API_KEY env var is set.

    If API_KEY is unset/empty, no auth is enforced (open mode).
    """
    if API_KEY and x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
