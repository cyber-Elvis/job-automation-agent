from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session
from ..deps import get_db
from ..models import JobORM

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.get("/stats")
def stats(db: Session = Depends(get_db)):
    rows = (
        db.query(
            JobORM.source.label("source"),
            func.count().label("total"),
            func.max(JobORM.published).label("last_published"),
            func.max(JobORM.id).label("last_id"),
        )
        .group_by(JobORM.source)
        .all()
    )
    return [
        {
            "source": r.source,
            "count": int(r.total),
            "last_published": r.last_published,
            "last_id": int(r.last_id) if r.last_id is not None else None,
        }
        for r in rows
    ]


@router.get("")
def list_jobs(
    q: str | None = Query(None, description="search in title"),
    source: str | None = Query(None),
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
