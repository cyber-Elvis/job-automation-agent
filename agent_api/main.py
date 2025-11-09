from fastapi import FastAPI, Depends, HTTPException
import importlib
from sqlalchemy.orm import Session
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from typing import Optional, List
from datetime import datetime
from .db import Base, engine, SessionLocal
from .models import JobORM as JobModel
from .schemas import JobCreate, JobOut, JobUpdate

# Minimal API shell that includes available collectors as routers.
app = FastAPI(title="Job Automation Agent API", version="0.3.0")


@app.on_event("startup")
def _on_startup():
    # create tables on startup (development convenience). Use migrations for prod.
    Base.metadata.create_all(bind=engine)


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


@app.get("/health")
def health():
    return {"ok": True}


def _job_to_dict(j: JobModel) -> dict:
    return {
        "id": j.id,
        "title": j.title,
        "link": j.link,
        "summary": j.summary,
        "published": j.published.isoformat() if j.published else None,
        "company": j.company,
        "location": j.location,
        "source": j.source,
    }


@app.get("/jobs", response_model=List[JobOut])
def list_jobs(limit: int = 100, db: Session = Depends(get_db)):
    stmt = select(JobModel).limit(limit)
    rows = db.execute(stmt).scalars().all()
    return [_job_to_dict(r) for r in rows]


@app.get("/jobs/{job_id}", response_model=JobOut)
def get_job(job_id: int, db: Session = Depends(get_db)):
    j = db.get(JobModel, job_id)
    if not j:
        raise HTTPException(status_code=404, detail="Job not found")
    return _job_to_dict(j)


@app.post("/jobs", status_code=201, response_model=JobOut)
def create_job(payload: JobCreate, db: Session = Depends(get_db)):
    job = JobModel(**payload.dict())
    db.add(job)
    try:
        db.commit()
        db.refresh(job)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Job with this link already exists")
    return _job_to_dict(job)


@app.put("/jobs/{job_id}", response_model=JobOut)
def update_job(job_id: int, payload: JobUpdate, db: Session = Depends(get_db)):
    j = db.get(JobModel, job_id)
    if not j:
        raise HTTPException(status_code=404, detail="Job not found")
    data = payload.dict(exclude_unset=True)
    if not data:
        return _job_to_dict(j)
    for field, val in data.items():
        setattr(j, field, val)
    try:
        db.add(j)
        db.commit()
        db.refresh(j)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Job with this link already exists")
    return _job_to_dict(j)


@app.delete("/jobs/{job_id}")
def delete_job(job_id: int, db: Session = Depends(get_db)):
    j = db.get(JobModel, job_id)
    if not j:
        raise HTTPException(status_code=404, detail="Job not found")
    db.delete(j)
    db.commit()
    return {"deleted": True}

