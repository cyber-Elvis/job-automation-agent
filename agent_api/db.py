from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg2://postgres:postgres@db:5432/postgres")

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()


def init_db():
	"""Create database tables defined on Base subclasses.

	This is a convenience wrapper used by development scripts. In production
	you should run migrations (Alembic) instead of create_all.
	"""
	Base.metadata.create_all(bind=engine)
