from fastapi import FastAPI, Depends, HTTPException
import importlib
from sqlalchemy.orm import Session
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from typing import Optional, List
from datetime import datetime
from .db import Base, engine, SessionLocal
from .models import JobORM as JobModel
# Job API routes are provided by `agent_api.routers.jobs`

# Minimal API shell that includes available collectors as routers.
app = FastAPI(title="Job Automation Agent API", version="0.3.0")


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


for _name in ("rss_generic", "greenhouse", "lever"):
    _include_optional(_name)


# Explicitly include the RSS collector router and its jobs sub-router so they're
# mounted even if dynamic imports change; this makes the jobs API available at
# /collectors/rss/jobs and also ensures the collector router is mounted.
import logging
logger = get_logger(__name__)

# Try to load collectors but don't crash the app if they fail
try:
    from .collectors import rss_generic
    from .collectors.rss_generic import jobs_router as collectors_jobs_router
    app.include_router(rss_generic.router)
    app.include_router(collectors_jobs_router)
except Exception as e:
    logger.error("Failed to load rss_generic collector: %s", e)
    rss_generic = None

# Include the consolidated jobs router (provides /jobs and /jobs/stats)
from .routers import jobs as jobs_router
app.include_router(jobs_router.router)

# --- APScheduler setup ---
import os
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from .logging_config import get_logger

logger = get_logger(__name__)

_scheduler: BackgroundScheduler | None = None

def _schedule_jobs():
    global _scheduler
    if _scheduler is not None:
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
                req = RSSCollectRequest(url=feed_url, limit=50)
                _do_collect_and_store(req, db)
            except Exception as e:
                logger.exception("scheduled rss collection failed: %s", e)
            finally:
                db.close()
        _scheduler.add_job(_job, IntervalTrigger(seconds=interval_seconds), id="rss_collect")
        logger.info("Scheduled RSS collector for url=%s interval=%ss", feed_url, interval_seconds)

    _scheduler.start()
    return _scheduler


@app.get("/health")
def health():
    return {"ok": True}


# Note: job CRUD/listing endpoints are provided by the `agent_api.routers.jobs`
# module. The older inline handlers were removed to avoid route collisions.

