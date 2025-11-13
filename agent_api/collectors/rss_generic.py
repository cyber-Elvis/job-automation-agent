from __future__ import annotations

from typing import List, Optional
from datetime import datetime, timezone
import html
import re

import feedparser  # RSS/Atom parser
import httpx       # HTTP client with timeouts & retries
from fastapi import APIRouter, HTTPException, Depends, Query, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert
from ..models import JobORM
from ..deps import get_db, require_api_key
from ..db import SessionLocal
from pydantic import BaseModel, HttpUrl, Field, AnyUrl
from ..schemas import JobItem, CollectStoreSummary, RSSCollectResponse
from ..logging_config import get_logger

router = APIRouter(prefix="/collectors/rss", tags=["collectors: rss"])
logger = get_logger(__name__)


# -----------------------
# Models
# -----------------------
class RSSCollectRequest(BaseModel):
    url: HttpUrl = Field(..., description="RSS/Atom feed URL")
    limit: int = Field(20, ge=1, le=200, description="Max items to return")
    timeout_seconds: float = Field(10.0, ge=2.0, le=60.0, description="Network timeout")
    # Optional: try to pull company/location from title with a regex like 'Title - Company (Location)'
    guess_meta_from_title: bool = Field(True, description="Try to infer company/location from entry title")


# -----------------------
# Helpers
# -----------------------
_TITLE_META_RE = re.compile(r"^(?P<title>[^–\-|]+?)(?:\s*[-–|]\s*(?P<company>[^(\[]+?))?(?:\s*[\[(]\s*(?P<location>[^)\]]+)\s*[\])])?$")

def _parse_published(entry) -> Optional[datetime]:
    # feedparser normalizes as 'published_parsed' or 'updated_parsed' (time.struct_time)
    for key in ("published_parsed", "updated_parsed"):
        t = entry.get(key)
        if t:
            try:
                return datetime(*t[:6], tzinfo=timezone.utc)
            except Exception:
                pass
    # Fallback: None (client can set to now if needed)
    return None

def _clean_html(text: Optional[str]) -> Optional[str]:
    if not text:
        return None
    return html.unescape(re.sub(r"<[^>]+>", "", text)).strip() or None

def _guess_from_title(title: str) -> tuple[str, Optional[str], Optional[str]]:
    """
    Try to split like: 'Senior SOC Analyst - ACME Corp (Melbourne)'
    Returns (pure_title, company?, location?)
    """
    m = _TITLE_META_RE.match(title.strip())
    if not m:
        return title.strip(), None, None
    g = m.groupdict()
    return g.get("title", "").strip(), (g.get("company") or None) and g["company"].strip(), (g.get("location") or None) and g["location"].strip()


# -----------------------
# Routes
# -----------------------
@router.get("/health")
def health():
    return {"ok": True, "source": "rss"}


@router.post("/collect", response_model=RSSCollectResponse)
def collect(req: RSSCollectRequest):
    # Fetch the feed
    headers = {
        "User-Agent": "JobAutomationAgent/0.1 (+https://localhost) httpx",
        "Accept": "application/rss+xml, application/atom+xml, application/xml;q=0.9, text/xml;q=0.8, */*;q=0.5",
    }

    try:
        # A single request is enough for most feeds; retries keep it robust.
        transport = httpx.HTTPTransport(retries=2)
        with httpx.Client(transport=transport, timeout=req.timeout_seconds, headers=headers, follow_redirects=True) as client:
            resp = client.get(str(req.url))
            resp.raise_for_status()
            content = resp.content
    except httpx.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"Failed to fetch feed: {e!s}")

    # Parse with feedparser (handles RSS/Atom variations)
    parsed = feedparser.parse(content)
    if parsed.bozo and parsed.bozo_exception:
        # Non-fatal, but we surface it so you know the feed might be malformed
        # You can choose to ignore this in production if feeds are often messy.
        pass

    if not parsed.entries:
        return RSSCollectResponse(
            summary=CollectStoreSummary(url=str(req.url), fetched=0),
            items=[],
        )

    items: List[JobItem] = []
    def _first(val):
        # feedparser sometimes returns lists; normalise to first element string
        if isinstance(val, list):
            if not val:
                return None
            val = val[0]
        return val

    for entry in parsed.entries[: req.limit]:
        raw_title = _first(entry.get("title"))
        title = str(raw_title).strip() if raw_title else "(untitled)"
        raw_link = _first(entry.get("link"))
        link = str(raw_link).strip() if raw_link else None
        summary_raw = _first(entry.get("summary") or entry.get("description"))
        summary = _clean_html(str(summary_raw)) if summary_raw else None
        published = _parse_published(entry)

        author_val = _first(entry.get("author"))
        source_raw = entry.get("source")
        if isinstance(source_raw, dict):
            company_source = source_raw.get("title")
        else:
            company_source = None
        company_val = author_val or company_source
        company = str(company_val).strip() if company_val else None
        location = None

        if req.guess_meta_from_title:
            pure_title, guess_company, guess_location = _guess_from_title(title)
            title = pure_title or title
            # Keep existing author if present; otherwise use guessed
            company = company or guess_company
            location = location or guess_location

        items.append(JobItem(
            title=title,
            link=link,
            summary=summary,
            published=published,
            company=company,
            location=location,
        ))
    # after loop: return collected items with summary
    return RSSCollectResponse(
        summary=CollectStoreSummary(url=str(req.url), fetched=len(items)),
        items=items,
    )


@router.post("/collect-and-store-json", response_model=RSSCollectResponse, dependencies=[Depends(require_api_key)])
def collect_and_store(req: RSSCollectRequest, db: Session = Depends(get_db)):
    """Collect items from the feed and insert them into the jobs table.

    This reuses the `collect()` parser above and performs a fast bulk insert
    using `bulk_insert_ignore_duplicates`. Returns a small summary dict so the
    endpoint won't 500 on duplicate inserts and doesn't commit per-row.
    """
    # parse items (reuses same parsing logic)
    resp = collect(req)
    fetched = len(resp.items)

    # perform fast bulk insert (single roundtrip)
    inserted = bulk_insert_ignore_duplicates(db, resp.items)
    skipped = max(fetched - inserted, 0)

    return RSSCollectResponse(
        summary=CollectStoreSummary(url=str(req.url), fetched=fetched, inserted=inserted, skipped=skipped),
        items=resp.items,
    )


def _do_collect_and_store(req: RSSCollectRequest, db: Session) -> RSSCollectResponse:
    """Internal helper to collect and store using an explicit DB session."""
    resp = collect(req)
    fetched = len(resp.items)
    # Fast bulk insert using Postgres ON CONFLICT DO NOTHING
    inserted = bulk_insert_ignore_duplicates(db, resp.items)
    skipped = max(fetched - inserted, 0)
    logger.info("rss bulk-insert stored=%d total=%d", inserted, fetched)
    return RSSCollectResponse(
        summary=CollectStoreSummary(url=str(req.url), fetched=fetched, inserted=inserted, skipped=skipped),
        items=resp.items,
    )


def _rows_from_items(items):
    rows = []
    for it in items:
        rows.append({
            "title": (it.title or "(untitled)")[:512],
            "link": str(it.link) if it.link else None,
            "summary": it.summary,
            "published": it.published,
            "company": it.company[:256] if it.company else None,
            "location": it.location[:256] if it.location else None,
            "source": it.source or "rss",
        })
    return rows


def bulk_insert_ignore_duplicates(db: Session, items) -> int:
    payload = _rows_from_items(items)
    if not payload:
        return 0

    stmt = insert(JobORM).values(payload)
    # relies on UNIQUE (source, link)
    stmt = stmt.on_conflict_do_nothing(index_elements=["source", "link"])

    result = db.execute(stmt)   # fast, single roundtrip
    db.commit()
    # NOTE: Postgres returns number of rows attempted; rowcount can be -1 on some drivers.
    try:
        return int(result.rowcount) if result.rowcount is not None else 0
    except Exception:
        return 0


def _collect_from_core(url: HttpUrl, limit: int = 20):
    """Helper to run collection+store without FastAPI injection.

    Useful for background tasks or direct programmatic invocation.
    """
    req = RSSCollectRequest(url=url, limit=limit, timeout_seconds=10.0, guess_meta_from_title=True)
    db = SessionLocal()
    try:
        _do_collect_and_store(req, db)
    finally:
        db.close()


@router.post("/collect-and-store", response_model=RSSCollectResponse, dependencies=[Depends(require_api_key)])
@router.post("/collect-from", response_model=RSSCollectResponse, dependencies=[Depends(require_api_key)])
def collect_from(url: HttpUrl, background_tasks: BackgroundTasks, *, limit: int = 20):
    """Enqueue collection+store to run in the background.

    FastAPI injects `background_tasks`, so no Optional/union is needed.
    Returns immediately with a queued summary.
    """
    background_tasks.add_task(_collect_from_core, url, limit)
    return RSSCollectResponse(
        summary=CollectStoreSummary(url=str(url), fetched=0, inserted=0, skipped=0),
        items=[],
    )


# -----------------------
# Simple jobs query API (mounted under the same router)
# -----------------------
jobs_router = APIRouter(prefix="/jobs", tags=["jobs"])


@jobs_router.get("", response_model=list[dict])
def list_jobs(
    q: Optional[str] = Query(None, description="search in title"),
    source: Optional[str] = None,
    limit: int = Query(20, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    query = db.query(JobORM).order_by(JobORM.id.desc())
    if source:
        query = query.filter(JobORM.source == source)
    if q:
        query = query.filter(JobORM.title.ilike(f"%{q}%"))
    rows = query.limit(limit).offset(offset).all()
    # quick dict view; or make a Pydantic JobOut schema
    return [
        {
            "id": r.id,
            "title": r.title,
            "link": r.link,
            "published": r.published,
            "company": r.company,
            "location": r.location,
            "source": r.source,
        }
        for r in rows
    ]


# include under the main collector router so main.py's include_router(mod.router) picks it up
router.include_router(jobs_router)
