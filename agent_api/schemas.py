from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class JobItem(BaseModel):
    title: str
    link: Optional[str] = None  # keep optional for compatibility with some feeds
    summary: Optional[str] = None
    # accept either datetime or ISO8601 string
    published: Optional[datetime | str] = None
    company: Optional[str] = None
    location: Optional[str] = None
    source: str = "rss"


class JobCreate(BaseModel):
    title: str
    link: Optional[str] = None
    summary: Optional[str] = None
    published: Optional[datetime] = None
    company: Optional[str] = None
    location: Optional[str] = None
    source: Optional[str] = None


class JobOut(BaseModel):
    id: int
    title: str
    link: Optional[str] = None
    summary: Optional[str] = None
    published: Optional[datetime] = None
    company: Optional[str] = None
    location: Optional[str] = None
    source: Optional[str] = None


class JobUpdate(BaseModel):
    title: Optional[str] = None
    link: Optional[str] = None
    summary: Optional[str] = None
    published: Optional[datetime] = None
    company: Optional[str] = None
    location: Optional[str] = None
    source: Optional[str] = None


__all__ = [
    "JobItem",
    "JobCreate",
    "JobOut",
    "JobUpdate",
]


# New response schemas for collectors
class CollectStoreSummary(BaseModel):
    # existing fields used by collect-and-store summary
    url: Optional[str] = None
    stored: Optional[int] = None
    count: Optional[int] = None
    # extended stats compatible with requested shape
    fetched: Optional[int] = None
    inserted: Optional[int] = None
    skipped: Optional[int] = None


class QueuedCollection(BaseModel):
    queued: bool
    url: str
    limit: int


class RSSCollectResponse(BaseModel):
    summary: CollectStoreSummary
    items: List[JobItem] = []
