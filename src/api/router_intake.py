from __future__ import annotations

from typing import Dict, Any, Optional
from enum import Enum
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, validator
from sqlmodel import Session, select

from src.db import get_session
from src.db.models import Doctor
from src.guardrails.llm_guards import guard_input, is_input_valid, get_validation_errors

router = APIRouter(
    prefix="/intake",
    tags=["intake"],
)

# ─────────────────────────────────────────────────────────────────────────────
# Enums and Constants
# ─────────────────────────────────────────────────────────────────────────────

class IntakeStep(str, Enum):
    GENDER = "gender"
    AGE = "age"
    DOCTOR = "doctor"
    SYMPTOMS = "symptoms"
    COMPLETE = "complete"

class Gender(str, Enum):
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"

# ─────────────────────────────────────────────────────────────────────────────
# Request/Response Models
# ─────────────────────────────────────────────────────────────────────────────

class IntakeSession(BaseModel):
    """Represents an intake session in progress."""
    session_id: str
    step: IntakeStep
    gender: Optional[Gender] = None
    age: Optional[int] = None
    doctor_id: Optional[int] = None
    symptoms: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class IntakeRequest(BaseModel):
    """Request to start or continue intake process."""
    session_id: Optional[str] = None
    step: IntakeStep
    value: str

class IntakeResponse(BaseModel):
    """Response for intake requests."""
    session_id: str
    step: IntakeStep
    message: str
    next_step: Optional[IntakeStep] = None
    options: Optional[Dict[str, Any]] = None
    is_complete: bool = False

class IntakeCompleteResponse(BaseModel):
    """Response when intake is complete."""
    session_id: str
    gender: Gender
    age: int
    doctor_id: int
    symptoms: str
    symptoms_hash: str

# ─────────────────────────────────────────────────────────────────────────────
# In-Memory Session Storage (In production, use Redis or DB)
# ─────────────────────────────────────────────────────────────────────────────

_intake_sessions: Dict[str, IntakeSession] = {}

def _get_session(session_id: str) -> Optional[IntakeSession]:
    """Get intake session by ID."""
    return _intake_sessions.get(session_id)

def _save_session(session: IntakeSession):
    """Save intake session."""
    session.updated_at = datetime.utcnow()
    _intake_sessions[session.session_id] = session

def _create_session_id() -> str:
    """Create a unique session ID."""
    import uuid
    return str(uuid.uuid4())

# ─────────────────────────────────────────────────────────────────────────────
# Helper Functions
# ─────────────────────────────────────────────────────────────────────────────

def _validate_gender(value: str) -> Gender:
    """Validate and convert gender input."""
    value_lower = value.lower().strip()
    
    if value_lower in ["чоловік", "male", "м", "m"]:
        return Gender.MALE
    elif value_lower in ["жінка", "female", "ж", "f"]:
        return Gender.FEMALE
    elif value_lower in ["інше", "other", "о"]:
        return Gender.OTHER
    else:
        raise ValueError("Невідома стать. Виберіть: чоловік, жінка, або інше")

def _validate_age(value: str) -> int:
    """Validate and convert age input."""
    try:
        age = int(value.strip())
        if age < 0 or age > 120:
            raise ValueError("Вік повинен бути від 0 до 120 років")
        return age
    except ValueError:
        raise ValueError("Введіть коректний вік (число від 0 до 120)")

def _validate_doctor_id(value: str, session: Session) -> int:
    """Validate and convert doctor ID input."""
    try:
        doctor_id = int(value.strip())
        # Check if doctor exists
        doctor = session.exec(select(Doctor).where(Doctor.id == doctor_id)).first()
        if not doctor:
            raise ValueError("Лікаря з таким ID не знайдено")
        return doctor_id
    except ValueError:
        raise ValueError("Введіть коректний ID лікаря")

def _validate_symptoms(value: str) -> str:
    """Validate symptoms input."""
    if not is_input_valid(value):
        errors = get_validation_errors(value)
        raise ValueError(f"Помилка в описі симптомів: {'; '.join(errors)}")
    
    return guard_input(value)

def _get_available_doctors(session: Session) -> list:
    """Get list of available doctors."""
    doctors = session.exec(select(Doctor)).all()
    return [
        {"id": doc.id, "name": doc.full_name, "position": doc.position}
        for doc in doctors
    ]

# ─────────────────────────────────────────────────────────────────────────────
# Endpoints
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/start", response_model=IntakeResponse)
async def start_intake(
    session: Session = Depends(get_session)
) -> IntakeResponse:
    """Start a new intake session."""
    session_id = _create_session_id()
    
    intake_session = IntakeSession(
        session_id=session_id,
        step=IntakeStep.GENDER
    )
    
    _save_session(intake_session)
    
    return IntakeResponse(
        session_id=session_id,
        step=IntakeStep.GENDER,
        message="Вітаю! Давайте почнемо збор інформації. Яка ваша стать? (чоловік/жінка/інше)",
        next_step=IntakeStep.AGE
    )

@router.post("/continue", response_model=IntakeResponse)
async def continue_intake(
    request: IntakeRequest,
    session: Session = Depends(get_session)
) -> IntakeResponse:
    """Continue intake process with next step."""
    
    # Get or create session
    if request.session_id:
        intake_session = _get_session(request.session_id)
        if not intake_session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Сесію не знайдено"
            )
    else:
        # Create new session if none provided
        session_id = _create_session_id()
        intake_session = IntakeSession(
            session_id=session_id,
            step=IntakeStep.GENDER
        )
    
    # Process current step
    try:
        if request.step == IntakeStep.GENDER:
            gender = _validate_gender(request.value)
            intake_session.gender = gender
            intake_session.step = IntakeStep.AGE
            
            _save_session(intake_session)
            
            return IntakeResponse(
                session_id=intake_session.session_id,
                step=IntakeStep.AGE,
                message=f"Дякую! Ваша стать: {gender.value}. Тепер введіть ваш вік:",
                next_step=IntakeStep.DOCTOR
            )
            
        elif request.step == IntakeStep.AGE:
            age = _validate_age(request.value)
            intake_session.age = age
            intake_session.step = IntakeStep.DOCTOR
            
            _save_session(intake_session)
            
            # Get available doctors
            doctors = _get_available_doctors(session)
            
            return IntakeResponse(
                session_id=intake_session.session_id,
                step=IntakeStep.DOCTOR,
                message=f"Дякую! Ваш вік: {age} років. Виберіть лікаря:",
                next_step=IntakeStep.SYMPTOMS,
                options={"doctors": doctors}
            )
            
        elif request.step == IntakeStep.DOCTOR:
            doctor_id = _validate_doctor_id(request.value, session)
            intake_session.doctor_id = doctor_id
            intake_session.step = IntakeStep.SYMPTOMS
            
            _save_session(intake_session)
            
            return IntakeResponse(
                session_id=intake_session.session_id,
                step=IntakeStep.SYMPTOMS,
                message="Дякую! Тепер опишіть ваші симптоми детально:",
                next_step=IntakeStep.COMPLETE
            )
            
        elif request.step == IntakeStep.SYMPTOMS:
            symptoms = _validate_symptoms(request.value)
            intake_session.symptoms = symptoms
            intake_session.step = IntakeStep.COMPLETE
            
            _save_session(intake_session)
            
            return IntakeResponse(
                session_id=intake_session.session_id,
                step=IntakeStep.COMPLETE,
                message="Дякую! Збір інформації завершено. Тепер можна генерувати діагноз.",
                is_complete=True
            )
            
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Невідомий крок"
            )
            
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/{session_id}", response_model=IntakeCompleteResponse)
async def get_intake_session(session_id: str):
    """Get complete intake session data."""
    intake_session = _get_session(session_id)
    
    if not intake_session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Сесію не знайдено"
        )
    
    if intake_session.step != IntakeStep.COMPLETE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Збір інформації ще не завершено"
        )
    
    # Generate symptoms hash
    from hashlib import sha256
    raw = f"{intake_session.gender.value}|{intake_session.age}|{intake_session.symptoms.strip().lower()}"
    symptoms_hash = sha256(raw.encode()).hexdigest()
    
    return IntakeCompleteResponse(
        session_id=intake_session.session_id,
        gender=intake_session.gender,
        age=intake_session.age,
        doctor_id=intake_session.doctor_id,
        symptoms=intake_session.symptoms,
        symptoms_hash=symptoms_hash
    )

@router.delete("/{session_id}")
async def delete_intake_session(session_id: str):
    """Delete an intake session."""
    if session_id in _intake_sessions:
        del _intake_sessions[session_id]
        return {"message": "Сесію видалено"}
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Сесію не знайдено"
        ) 