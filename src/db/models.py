from __future__ import annotations
from datetime import datetime

from sqlmodel import SQLModel, Field

################################################################################
# Core domain tables
################################################################################

class Doctor(SQLModel, table=True):
    """Basic registry of clinicians shown in /doctors route."""
    id: int | None = Field(default=None, primary_key=True)
    full_name: str
    position: str
    schedule: str           # e.g. "Mon-Fri 09-17" JSON or plain text

class Clinic(SQLModel, table=True):
    """Singleton table with public clinic info (/clinic route)."""
    id: int | None = Field(default=1, primary_key=True)
    address: str
    opening_hours: str      # e.g. "Mon-Sat 08-20"
    services: str           # comma-separated or Markdown

################################################################################
# Doctor-approved knowledge base
################################################################################

class DoctorAnswer(SQLModel, table=True):
    """Cache of answers a doctor marked as approved or edited."""
    id: int | None = Field(default=None, primary_key=True)
    symptoms_hash: str                  # sha256(gender|age|symptoms)
    answer_md: str                      # markdown (doctor edition)
    doctor_id: int | None = Field(default=None, foreign_key="doctor.id")
    created_at: datetime = Field(default_factory=datetime.utcnow) 