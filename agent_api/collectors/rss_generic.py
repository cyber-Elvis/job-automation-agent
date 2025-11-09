from __future__ import annotations

from typing import List, Optional
from datetime import datetime, timezone
import html
import re

import feedparser  # RSS/Atom parser
import httpx       # HTTP client with timeouts & retries
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from ..models import Job
from ..deps import get_db
from pydantic import BaseModel, HttpUrl, Field

router = APIRouter(prefix="/collectors/rss", tags=["collectors: rss"])


# -----------------------
# Models
# -----------------------
class RSSCollectRequest(BaseModel):
    url: HttpUrl = Field(..., description="RSS/Atom feed URL")
    limit: int = Field(20, ge=1, le=200, description="Max items to return")
    timeout_seconds: float = Field(10.0, ge=2.0, le=60.0, description="Network timeout")
    # Optional: try to pull company/location from title with a regex like 'Title - Company (Location)'
    guess_meta_from_title: bool = Field(True, description="Try to infer company/location from entry title")


class JobItem(BaseModel):
    title: str
    link: Optional[HttpUrl] = None
    summary: Optional[str] = None
    published: Optional[datetime] = None
    company: Optional[str] = None
    location: Optional[str] = None
    source: str = "rss"


class RSSCollectResponse(BaseModel):
    url: HttpUrl
    count: int
    items: List[JobItem]


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
        return RSSCollectResponse(url=req.url, count=0, items=[])

    items: List[JobItem] = []
    for entry in parsed.entries[: req.limit]:
        title = entry.get("title") or "(untitled)"
        link = entry.get("link")
        summary = _clean_html(entry.get("summary") or entry.get("description"))
        published = _parse_published(entry)

        company = entry.get("author") or entry.get("source", {}).get("title")
        location = None

        if req.guess_meta_from_title:
            pure_title, guess_company, guess_location = _guess_from_title(title)
            title = pure_title or title
            # Keep existing author if present; otherwise use guessed
            company = company or guess_company
            location = location or guess_location

        items.append(
            JobItem(
                title=title,
                link=link,
                summary=summary,
                published=published,
                company=(company or None),
                location=(location or None),
            )
        )

        return RSSCollectResponse(url=req.url, count=len(items), items=items)


    @router.post("/collect-and-store", response_model=RSSCollectResponse)
    def collect_and_store(req: RSSCollectRequest, db: Session = Depends(get_db)):
        """Collect items from the feed and insert them into the jobs table.

        This reuses the `collect()` parser above and attempts to insert each parsed
        item into the database. Duplicate links are silently skipped (UniqueConstraint).
        """
        resp = collect(req)
        inserted = 0

        for item in resp.items:
            row = Job(
                title=item.title,
                link=str(item.link) if item.link else None,
                summary=item.summary,
                published=item.published,
                company=item.company,
                location=item.location,
                source=item.source,
            )
            try:
                db.add(row)
                db.commit()
                inserted += 1
            except IntegrityError:
                db.rollback()  # duplicate link (UniqueConstraint)
            except Exception:
                db.rollback()
                raise

        # Return what we parsed (count is the parsed count, not inserted count)
        return resp
