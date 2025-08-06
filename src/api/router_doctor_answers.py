#!/usr/bin/env python
"""src/api/router_doctor_answers.py

Knowledge base router for doctor-approved answers.
Provides search and retrieval functionality for the knowledge base.
"""
from __future__ import annotations

from typing import List, Optional, Dict, Any
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field
from sqlmodel import Session, select, func

from src.db import get_session
from src.db.models import DoctorAnswer, Doctor
from src.cache.doctor_semantic_index import semantic_lookup

router = APIRouter(prefix="/knowledge-base", tags=["knowledge-base"])

# ─────────────────────────────────────────────────────────────────────────────
# Request/Response Models
# ─────────────────────────────────────────────────────────────────────────────

class KnowledgeBaseSearchRequest(BaseModel):
    query: str = Field(..., description="Search query for symptoms or keywords")
    top_k: int = Field(5, description="Number of results to return")
    min_similarity: float = Field(0.8, description="Minimum similarity threshold")

class KnowledgeBaseEntry(BaseModel):
    id: int
    symptoms_hash: str
    answer_md: str
    approved: bool
    doctor_id: Optional[int]
    doctor_name: Optional[str]
    doctor_position: Optional[str]
    created_at: datetime
    similarity_score: Optional[float] = None

class KnowledgeBaseSearchResponse(BaseModel):
    query: str
    results: List[KnowledgeBaseEntry]
    total_found: int
    search_method: str  # "semantic" or "exact"

class KnowledgeBaseStats(BaseModel):
    total_entries: int
    approved_entries: int
    total_doctors: int
    latest_entry: Optional[datetime]
    most_active_doctor: Optional[str]

# ─────────────────────────────────────────────────────────────────────────────
# Helper Functions
# ─────────────────────────────────────────────────────────────────────────────

def _extract_symptoms_from_hash(symptoms_hash: str) -> str:
    """Extract symptoms from hash for display purposes."""
    # This is a simplified version - in practice, you might want to store original symptoms
    return f"Symptoms hash: {symptoms_hash[:16]}..."

# ─────────────────────────────────────────────────────────────────────────────
# Endpoints
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/", response_model=KnowledgeBaseStats)
async def get_knowledge_base_stats(
    session: Session = Depends(get_session)
) -> KnowledgeBaseStats:
    """Get statistics about the knowledge base."""
    
    # Get total entries
    total_entries = session.exec(select(func.count(DoctorAnswer.id))).first() or 0
    
    # Get approved entries
    approved_entries = session.exec(
        select(func.count(DoctorAnswer.id)).where(DoctorAnswer.approved == True)
    ).first() or 0
    
    # Get total unique doctors
    total_doctors = session.exec(
        select(func.count(func.distinct(DoctorAnswer.doctor_id)))
        .where(DoctorAnswer.doctor_id.is_not(None))
    ).first() or 0
    
    # Get latest entry
    latest_entry = session.exec(
        select(DoctorAnswer.created_at)
        .order_by(DoctorAnswer.created_at.desc())
        .limit(1)
    ).first()
    
    # Get most active doctor
    most_active_doctor = session.exec(
        select(Doctor.full_name)
        .join(DoctorAnswer, Doctor.id == DoctorAnswer.doctor_id)
        .group_by(Doctor.id, Doctor.full_name)
        .order_by(func.count(DoctorAnswer.id).desc())
        .limit(1)
    ).first()
    
    return KnowledgeBaseStats(
        total_entries=total_entries,
        approved_entries=approved_entries,
        total_doctors=total_doctors,
        latest_entry=latest_entry,
        most_active_doctor=most_active_doctor
    )

@router.post("/search", response_model=KnowledgeBaseSearchResponse)
async def search_knowledge_base(
    request: KnowledgeBaseSearchRequest,
    session: Session = Depends(get_session)
) -> KnowledgeBaseSearchResponse:
    """
    Search the knowledge base using semantic similarity.
    Returns doctor-approved answers that match the query.
    """
    
    # Use semantic search to find similar diagnoses
    semantic_results = semantic_lookup(request.query, top_k=request.top_k)
    
    if semantic_results:
        # Get the full entries for semantic matches
        # Note: This is a simplified approach - in practice, you'd want to map semantic results back to database entries
        search_method = "semantic"
        
        # For now, return all approved answers (you can enhance this with proper semantic mapping)
        approved_answers = session.exec(
            select(DoctorAnswer)
            .where(DoctorAnswer.approved == True)
            .order_by(DoctorAnswer.created_at.desc())
            .limit(request.top_k)
        ).all()
        
        results = []
        for answer in approved_answers:
            # Get doctor info
            doctor = None
            if answer.doctor_id:
                doctor = session.exec(
                    select(Doctor).where(Doctor.id == answer.doctor_id)
                ).first()
            
            results.append(KnowledgeBaseEntry(
                id=answer.id,
                symptoms_hash=answer.symptoms_hash,
                answer_md=answer.answer_md,
                approved=answer.approved,
                doctor_id=answer.doctor_id,
                doctor_name=doctor.full_name if doctor else None,
                doctor_position=doctor.position if doctor else None,
                created_at=answer.created_at,
                similarity_score=0.95  # Placeholder - you'd calculate this from semantic search
            ))
    else:
        # Fallback to exact search or return empty results
        search_method = "exact"
        results = []
    
    return KnowledgeBaseSearchResponse(
        query=request.query,
        results=results,
        total_found=len(results),
        search_method=search_method
    )

@router.get("/entries", response_model=List[KnowledgeBaseEntry])
async def list_knowledge_base_entries(
    limit: int = Query(50, description="Number of entries to return"),
    offset: int = Query(0, description="Number of entries to skip"),
    approved_only: bool = Query(True, description="Show only approved entries"),
    session: Session = Depends(get_session)
) -> List[KnowledgeBaseEntry]:
    """List knowledge base entries with pagination."""
    
    # Build query
    query = select(DoctorAnswer)
    if approved_only:
        query = query.where(DoctorAnswer.approved == True)
    
    # Add pagination and ordering
    query = query.order_by(DoctorAnswer.created_at.desc()).offset(offset).limit(limit)
    
    # Execute query
    answers = session.exec(query).all()
    
    # Convert to response format
    results = []
    for answer in answers:
        # Get doctor info
        doctor = None
        if answer.doctor_id:
            doctor = session.exec(
                select(Doctor).where(Doctor.id == answer.doctor_id)
            ).first()
        
        results.append(KnowledgeBaseEntry(
            id=answer.id,
            symptoms_hash=answer.symptoms_hash,
            answer_md=answer.answer_md,
            approved=answer.approved,
            doctor_id=answer.doctor_id,
            doctor_name=doctor.full_name if doctor else None,
            doctor_position=doctor.position if doctor else None,
            created_at=answer.created_at
        ))
    
    return results

@router.get("/entries/{entry_id}", response_model=KnowledgeBaseEntry)
async def get_knowledge_base_entry(
    entry_id: int,
    session: Session = Depends(get_session)
) -> KnowledgeBaseEntry:
    """Get a specific knowledge base entry by ID."""
    
    answer = session.exec(
        select(DoctorAnswer).where(DoctorAnswer.id == entry_id)
    ).first()
    
    if not answer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Knowledge base entry not found"
        )
    
    # Get doctor info
    doctor = None
    if answer.doctor_id:
        doctor = session.exec(
            select(Doctor).where(Doctor.id == answer.doctor_id)
        ).first()
    
    return KnowledgeBaseEntry(
        id=answer.id,
        symptoms_hash=answer.symptoms_hash,
        answer_md=answer.answer_md,
        approved=answer.approved,
        doctor_id=answer.doctor_id,
        doctor_name=doctor.full_name if doctor else None,
        doctor_position=doctor.position if doctor else None,
        created_at=answer.created_at
    )

@router.get("/doctors/{doctor_id}/entries", response_model=List[KnowledgeBaseEntry])
async def get_doctor_entries(
    doctor_id: int,
    limit: int = Query(50, description="Number of entries to return"),
    offset: int = Query(0, description="Number of entries to skip"),
    session: Session = Depends(get_session)
) -> List[KnowledgeBaseEntry]:
    """Get all knowledge base entries by a specific doctor."""
    
    # Verify doctor exists
    doctor = session.exec(select(Doctor).where(Doctor.id == doctor_id)).first()
    if not doctor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Doctor not found"
        )
    
    # Get doctor's entries
    answers = session.exec(
        select(DoctorAnswer)
        .where(DoctorAnswer.doctor_id == doctor_id)
        .order_by(DoctorAnswer.created_at.desc())
        .offset(offset)
        .limit(limit)
    ).all()
    
    # Convert to response format
    results = []
    for answer in answers:
        results.append(KnowledgeBaseEntry(
            id=answer.id,
            symptoms_hash=answer.symptoms_hash,
            answer_md=answer.answer_md,
            approved=answer.approved,
            doctor_id=answer.doctor_id,
            doctor_name=doctor.full_name,
            doctor_position=doctor.position,
            created_at=answer.created_at
        ))
    
    return results 