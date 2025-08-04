from sqlmodel import SQLModel, create_engine, Session
from pathlib import Path
import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///data/clinic.db")
engine = create_engine(DATABASE_URL, echo=False)

def init_db() -> None:
    """Create missing tables – call from FastAPI start-up or Alembic."""
    SQLModel.metadata.create_all(engine)

def get_session() -> Session:
    """FastAPI dependency that yields a DB session."""
    with Session(engine) as session:
        yield session 