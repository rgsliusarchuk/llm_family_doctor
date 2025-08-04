from __future__ import annotations

from hashlib import sha256
from typing import Dict, Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlmodel import Session, select

from src.db import get_session
from src.db.models import DoctorAnswer
from src.models.rag_chain import generate_rag_response

router = APIRouter(
    prefix="/diagnoses",
    tags=["diagnoses"],
)

# ─────────────────────────────────────────────────────────────────────────────
# Request/Response Models
# ─────────────────────────────────────────────────────────────────────────────

class DiagnoseRequest(BaseModel):
    gender: str
    age: int
    symptoms: str

class DiagnoseResponse(BaseModel):
    diagnosis: str
    cached: bool
    symptoms_hash: str

# ─────────────────────────────────────────────────────────────────────────────
# Helper Functions
# ─────────────────────────────────────────────────────────────────────────────

def _symptoms_hash(gender: str, age: int, symptoms: str) -> str:
    raw = f"{gender}|{age}|{symptoms.strip().lower()}"
    return sha256(raw.encode()).hexdigest()

# ─────────────────────────────────────────────────────────────────────────────
# Endpoints
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/")
async def diagnose_root():
    """Root endpoint for diagnose router."""
    return {"message": "Diagnose router is working"}

@router.post("/", response_model=DiagnoseResponse)
async def diagnose(
    request: DiagnoseRequest,
    session: Session = Depends(get_session),
) -> DiagnoseResponse:
    """
    Generate a diagnosis based on patient symptoms.
    First checks for cached approved answers, then falls back to RAG.
    """
    # Generate symptoms hash
    symptoms_hash = _symptoms_hash(request.gender, request.age, request.symptoms)
    
    # Check for cached approved answer
    cached_answer = session.exec(
        select(DoctorAnswer).where(
            DoctorAnswer.symptoms_hash == symptoms_hash,
            DoctorAnswer.approved == True
        )
    ).first()
    
    if cached_answer:
        return DiagnoseResponse(
            diagnosis=cached_answer.answer_md,
            cached=True,
            symptoms_hash=symptoms_hash
        )
    
    # Generate new diagnosis using RAG
    query = f"Стать: {request.gender}, Вік: {request.age}, Симптоми: {request.symptoms}"
    rag_result = generate_rag_response(query)
    
    return DiagnoseResponse(
        diagnosis=rag_result["response"],
        cached=False,
        symptoms_hash=symptoms_hash
    ) 