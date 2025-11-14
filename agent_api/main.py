import os
import logging
from fastapi import FastAPI, Depends, HTTPException
import importlib
from sqlalchemy.orm import Session
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from typing import Optional, List, Dict, Any
from datetime import datetime
from .db import Base, engine, SessionLocal
from .models import JobORM as JobModel
# pydantic helpers and prefill util
from pydantic import BaseModel, HttpUrl
from .prefill.playwright_prefill import prefill_and_pause
# Job API routes are provided by `agent_api.routers.jobs`

# --- Logging (replace get_logger with stdlib logging) ---
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger(__name__)

# Minimal API shell that includes available collectors as routers.
from .collectors import rss_generic
from .routers import jobs as jobs_router

app = FastAPI(title="Job Automation Agent API", version="0.3.0")

# ✅ Mount routers explicitly
app.include_router(rss_generic.router)
app.include_router(jobs_router.router)


# ---- Request models ----
class PrefillPayload(BaseModel):
    apply_url: HttpUrl
    name: str
    email: str
    phone: str
    resume_path: str = ""
    cover_letter: str = ""


@app.on_event("startup")
def _on_startup():
    # create tables on startup (development convenience). Use migrations for prod.
    Base.metadata.create_all(bind=engine)
    # start APScheduler (if configured)
    try:
        _schedule_jobs()
    except Exception as e:
        # do not crash app if scheduling fails
        print(f"[scheduler] failed to start: {e}")


def _include_optional(name: str):
    try:
        mod = importlib.import_module(f".collectors.{name}", package=__package__)
        app.include_router(mod.router)
        print(f"[collectors] included: {name}")
    except Exception as e:
        # Don't fail the app if a collector module is missing or misconfigured
        print(f"[collectors] skipping {name}: {e}")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


for _name in ("greenhouse", "lever"):
    _include_optional(_name)


# Explicitly include the RSS collector router and its jobs sub-router so they're
# mounted even if dynamic imports change; this makes the jobs API available at
# /collectors/rss/jobs and also ensures the collector router is mounted.
# Routers are already explicitly mounted above.

# --- APScheduler setup (optional) ---
try:
    from apscheduler.schedulers.background import BackgroundScheduler  # type: ignore
    from apscheduler.triggers.interval import IntervalTrigger  # type: ignore
except ImportError:  # pragma: no cover
    BackgroundScheduler = None  # type: ignore
    IntervalTrigger = None  # type: ignore

_scheduler: BackgroundScheduler | None = None  # type: ignore[name-defined]

def _schedule_jobs():
    global _scheduler
    if _scheduler is not None or BackgroundScheduler is None:
        if BackgroundScheduler is None:
            logger.warning("APScheduler not installed; skipping scheduler setup.")
        return _scheduler
    _scheduler = BackgroundScheduler()

    # Example: schedule a periodic RSS collection if env var is set
    feed_url = os.getenv("RSS_COLLECT_URL")
    if feed_url:
        interval_seconds = int(os.getenv("RSS_COLLECT_INTERVAL_SECONDS", "900"))  # 15 min default
        def _job():
            # Use SessionLocal inside job; avoid reusing request-scoped sessions
            try:
                from .collectors.rss_generic import RSSCollectRequest, _do_collect_and_store
            except Exception as e:
                logger.error("Scheduled job cannot import rss_generic: %s", e)
                return
            from .db import SessionLocal as _SessionLocal
            db = _SessionLocal()
            try:
                # feed_url may be plain string; let pydantic validate/raise if invalid
                req = RSSCollectRequest(url=feed_url, limit=50, timeout_seconds=10.0, guess_meta_from_title=True)  # type: ignore[arg-type]
                _do_collect_and_store(req, db)
            except Exception as e:
                logger.exception("scheduled rss collection failed: %s", e)
            finally:
                db.close()
        if IntervalTrigger is not None and _scheduler is not None:
            _scheduler.add_job(_job, IntervalTrigger(seconds=interval_seconds), id="rss_collect")
            logger.info("Scheduled RSS collector for url=%s interval=%ss", feed_url, interval_seconds)
        else:
            logger.warning("IntervalTrigger unavailable; RSS collection scheduling skipped.")

    if _scheduler is not None:
        try:
            _scheduler.start()
        except Exception as e:  # pragma: no cover
            logger.error("Failed to start scheduler: %s", e)
    return _scheduler


@app.get("/health")
def health():
    return {"ok": True}


@app.post("/prefill")
def prefill(payload: PrefillPayload):
    """
    Open a headed Chromium browser, prefill what we can, then pause for manual submission.
    """
    # Map incoming data into a generic 'fields' dict
    fields: Dict[str, Any] = {
        "name": payload.name,
        "email": payload.email,
        "phone": payload.phone,
        "resume_path": payload.resume_path,
        "cover_letter": payload.cover_letter,
    }

    ua = (
        "Mozilla/5.0 (X11; Linux x86_64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36 JobAgentPrefill"
    )

    try:
        # This will open Chromium inside the agent-api container
        prefill_and_pause(str(payload.apply_url), ua, fields)
        status = "ok"
    except Exception as e:
        # Don't crash the API; return the error so you can see it in OpenWebUI
        status = f"error: {e!s}"

    return {"status": status, "fields": fields}


# Note: job CRUD/listing endpoints are provided by the `agent_api.routers.jobs`
# module. The older inline handlers were removed to avoid route collisions.

