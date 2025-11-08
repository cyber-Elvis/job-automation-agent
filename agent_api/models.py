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
