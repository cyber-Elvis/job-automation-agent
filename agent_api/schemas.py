from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class JobItem(BaseModel):
    title: str
    link: Optional[str] = None
    summary: Optional[str] = None
    published: Optional[datetime] = None
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
