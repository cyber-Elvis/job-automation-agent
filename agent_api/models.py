from sqlalchemy import Column, Integer, String, Text, DateTime, UniqueConstraint
from .db import Base


# -----------------------
# SQLAlchemy ORM
# -----------------------
class JobORM(Base):
    __tablename__ = "jobs"
    __table_args__ = (UniqueConstraint("source", "link", name="uq_job_source_link"),)

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(512), nullable=False)
    link = Column(String, nullable=True, index=True)
    summary = Column(Text, nullable=True)
    published = Column(DateTime, nullable=True)
    company = Column(String(256), nullable=True)
    location = Column(String(256), nullable=True)
    source = Column(String(64), nullable=True)


__all__ = [
    "Base",
    "JobORM",
]

