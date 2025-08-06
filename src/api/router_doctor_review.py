from __future__ import annotations

from typing import Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlmodel import Session, select

from src.db import get_session
from src.db.models import DoctorAnswer, Doctor
from src.cache.redis_cache import set_md
from src.cache.doctor_semantic_index import add_doc_to_index
from src.guardrails.llm_guards import guard_output

router = APIRouter(
    prefix="/doctor_review",
    tags=["doctor_review"],
)

# ─────────────────────────────────────────────────────────────────────────────
# Request/Response Models
# ─────────────────────────────────────────────────────────────────────────────

class ApproveRequest(BaseModel):
    """Request to approve a diagnosis."""
    doctor_id: int = Field(..., description="ID of the approving doctor")

class EditRequest(BaseModel):
    """Request to edit a diagnosis."""
    doctor_id: int = Field(..., description="ID of the editing doctor")
    answer_md: str = Field(..., description="Edited answer in markdown format")

class ReviewResponse(BaseModel):
    """Response for review actions."""
    request_id: str
    status: str
    message: str
    updated_at: datetime

# ─────────────────────────────────────────────────────────────────────────────
# Helper Functions
# ─────────────────────────────────────────────────────────────────────────────

def _get_doctor_answer(request_id: str, session: Session) -> Optional[DoctorAnswer]:
    """Get doctor answer by request ID (symptoms_hash)."""
    return session.exec(
        select(DoctorAnswer).where(DoctorAnswer.symptoms_hash == request_id)
    ).first()

def _validate_doctor(doctor_id: int, session: Session) -> Doctor:
    """Validate that doctor exists."""
    doctor = session.exec(
        select(Doctor).where(Doctor.id == doctor_id)
    ).first()
    
    if not doctor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Лікаря не знайдено"
        )
    
    return doctor

async def _update_caches(symptoms_hash: str, answer_md: str):
    """Update all caches with new answer."""
    # Update Redis cache
    await set_md(symptoms_hash, answer_md)
    
    # Extract and store patient response
    from src.utils import extract_patient_response
    from src.cache.redis_cache import set_diagnosis_with_patient_response
    patient_response = extract_patient_response(answer_md)
    await set_diagnosis_with_patient_response(symptoms_hash, answer_md, patient_response)
    
    # Update semantic index
    add_doc_to_index(answer_md)

# ─────────────────────────────────────────────────────────────────────────────
# Endpoints
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/{request_id}/approve", response_model=ReviewResponse)
async def approve_diagnosis(
    request_id: str,
    request: ApproveRequest,
    session: Session = Depends(get_session)
) -> ReviewResponse:
    """
    Approve a diagnosis by a doctor.
    
    This endpoint marks a diagnosis as approved and updates all caches.
    """
    # Validate doctor exists
    doctor = _validate_doctor(request.doctor_id, session)
    
    # Get existing answer or create new one
    doctor_answer = _get_doctor_answer(request_id, session)
    
    if doctor_answer:
        # Update existing answer
        doctor_answer.approved = True
        doctor_answer.doctor_id = request.doctor_id
        doctor_answer.created_at = datetime.utcnow()
        
        # Get the answer content from Redis cache
        from src.cache.redis_cache import get_md
        cached_answer = await get_md(request_id)
        if cached_answer:
            doctor_answer.answer_md = cached_answer
    else:
        # Create new approved answer
        from src.cache.redis_cache import get_md
        cached_answer = await get_md(request_id)
        
        if not cached_answer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Діагноз не знайдено в кеші"
            )
        
        doctor_answer = DoctorAnswer(
            symptoms_hash=request_id,
            answer_md=cached_answer,
            approved=True,
            doctor_id=request.doctor_id,
            created_at=datetime.utcnow()
        )
        session.add(doctor_answer)
    
    # Save to database
    session.commit()
    session.refresh(doctor_answer)
    
    # Update caches
    await _update_caches(request_id, doctor_answer.answer_md)
    
    return ReviewResponse(
        request_id=request_id,
        status="approved",
        message=f"Діагноз схвалено лікарем {doctor.full_name}",
        updated_at=doctor_answer.created_at
    )

@router.patch("/{request_id}/edit", response_model=ReviewResponse)
async def edit_diagnosis(
    request_id: str,
    request: EditRequest,
    session: Session = Depends(get_session)
) -> ReviewResponse:
    """
    Edit a diagnosis by a doctor.
    
    This endpoint allows doctors to modify the diagnosis and marks it as approved.
    """
    # Validate doctor exists
    doctor = _validate_doctor(request.doctor_id, session)
    
    # Apply output guardrails to edited answer
    guarded_answer = guard_output(request.answer_md)
    
    # Get existing answer or create new one
    doctor_answer = _get_doctor_answer(request_id, session)
    
    if doctor_answer:
        # Update existing answer
        doctor_answer.answer_md = guarded_answer
        doctor_answer.approved = True
        doctor_answer.doctor_id = request.doctor_id
        doctor_answer.created_at = datetime.utcnow()
    else:
        # Create new approved answer
        doctor_answer = DoctorAnswer(
            symptoms_hash=request_id,
            answer_md=guarded_answer,
            approved=True,
            doctor_id=request.doctor_id,
            created_at=datetime.utcnow()
        )
        session.add(doctor_answer)
    
    # Save to database
    session.commit()
    session.refresh(doctor_answer)
    
    # Update caches
    await _update_caches(request_id, doctor_answer.answer_md)
    
    return ReviewResponse(
        request_id=request_id,
        status="edited",
        message=f"Діагноз відредаговано та схвалено лікарем {doctor.full_name}",
        updated_at=doctor_answer.created_at
    )

@router.get("/{request_id}")
async def get_review_status(
    request_id: str,
    session: Session = Depends(get_session)
):
    """Get the review status of a diagnosis."""
    doctor_answer = _get_doctor_answer(request_id, session)
    
    if not doctor_answer:
        return {
            "request_id": request_id,
            "status": "not_found",
            "approved": False,
            "doctor_id": None,
            "created_at": None
        }
    
    return {
        "request_id": request_id,
        "status": "approved" if doctor_answer.approved else "pending",
        "approved": doctor_answer.approved,
        "doctor_id": doctor_answer.doctor_id,
        "created_at": doctor_answer.created_at
    }

@router.get("/")
async def list_pending_reviews(
    session: Session = Depends(get_session),
    limit: int = 50,
    offset: int = 0
):
    """List pending reviews that need doctor attention."""
    # Get unapproved answers from cache (this would need to be implemented)
    # For now, return empty list
    return {
        "pending_reviews": [],
        "total": 0,
        "limit": limit,
        "offset": offset
    } 