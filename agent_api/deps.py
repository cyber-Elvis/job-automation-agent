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
    """TEMP: disable auth for development

    Previously enforced X-API-Key when API_KEY env was set. Now a no-op.
    """
    return
