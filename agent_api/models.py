from sqlalchemy import Column, Integer, String, Text, DateTime, UniqueConstraint
from .db import Base

class Job(Base):
    __tablename__ = "jobs"
    id = Column(Integer, primary_key=True)
    title = Column(String(512), nullable=False)
    link = Column(Text, nullable=True)            # often long
    summary = Column(Text, nullable=True)
    published = Column(DateTime, nullable=True)
    company = Column(String(256), nullable=True)
    location = Column(String(256), nullable=True)
    source = Column(String(64), nullable=False, default="rss")

    __table_args__ = (
        UniqueConstraint("link", name="uq_jobs_link"),
    )
from pydantic import BaseModel, AnyHttpUrl
from typing import Optional, Literal
from datetime import datetime

class Job(BaseModel):
    title: str
    company: Optional[str]
    location: Optional[str]
    url: AnyHttpUrl
    source: Literal["greenhouse","lever","rss","generic"]
    posted_at: Optional[datetime] = None
    raw: Optional[dict] = None

class PrefillPayload(BaseModel):
    apply_url: AnyHttpUrl
    name: str
    email: str
    phone: Optional[str] = None
    resume_path: Optional[str] = None
    cover_letter: Optional[str] = None
