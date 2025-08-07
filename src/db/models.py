from __future__ import annotations
from datetime import datetime

from sqlmodel import SQLModel, Field

################################################################################
# Core domain tables
################################################################################

class Doctor(SQLModel, table=True):
    """Basic registry of clinicians shown in /doctors route."""
    __tablename__ = "doctors"             # renamed table
    id: int | None = Field(default=None, primary_key=True)
    clinic_id: int | None = Field(
        default=1,                          # ← default to main clinic
        foreign_key="clinics.id",         # FK points to new table name
        index=True
    )
    full_name: str
    position: str
    schedule: str           # e.g. "Mon-Fri 09-17" JSON or plain text

class Clinic(SQLModel, table=True):
    """Singleton table with public clinic info (/clinic route)."""
    __tablename__ = "clinics"             # renamed table
    id: int | None = Field(default=1, primary_key=True)
    address: str
    opening_hours: str      # e.g. "Mon-Sat 08-20"
    services: str           # comma-separated or Markdown

################################################################################
# Doctor-approved knowledge base
################################################################################

class DoctorAnswer(SQLModel, table=True):
    """Cache of answers a doctor marked as approved or edited."""
    __tablename__ = "doctor_answers"      # renamed table
    id: int | None = Field(default=None, primary_key=True)
    symptoms_hash: str  # SHA-256 of gender|age|symptoms
    answer_md: str
    approved: bool = False
    doctor_id: int | None = Field(default=None, foreign_key="doctors.id")
    created_at: datetime = Field(default_factory=datetime.utcnow) 