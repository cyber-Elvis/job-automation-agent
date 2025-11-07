from typing import Optional, List
from pydantic import BaseModel, HttpUrl


class DiscoverRequest(BaseModel):
	query: str
	locations: Optional[List[str]] = None
	sources: Optional[List[str]] = None  # e.g., ["site", "rss"]


class JobPosting(BaseModel):
	title: str
	company: str
	url: HttpUrl
	location: Optional[str] = None
	summary: Optional[str] = None


class DiscoverResponse(BaseModel):
	items: List[JobPosting]
	count: int


class PrefillRequest(BaseModel):
	job_url: HttpUrl
	resume_text: Optional[str] = None
	notes: Optional[str] = None


class PrefillResponse(BaseModel):
	status: str
	fields: dict