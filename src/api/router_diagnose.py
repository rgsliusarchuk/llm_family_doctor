from __future__ import annotations

from hashlib import sha256
from typing import Dict, Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlmodel import Session, select

from src.db import get_session
from src.db.models import DoctorAnswer
from src.models.rag_chain import generate_rag_response
from src.cache.redis_cache import get_md, set_md
from src.cache.doctor_semantic_index import semantic_lookup
from src.guardrails.llm_guards import guard_input, guard_output

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
    First checks exact cache, then semantic cache, then DB approved answers, then RAG.
    """
    # Apply input guardrails
    guarded_symptoms = guard_input(request.symptoms)
    
    # Generate symptoms hash
    symptoms_hash = _symptoms_hash(request.gender, request.age, guarded_symptoms)
    
    # ---------- exact cache ----------
    if md := get_md(symptoms_hash):
        return DiagnoseResponse(
            diagnosis=md, 
            cached=True,
            symptoms_hash=symptoms_hash
        )
    
    # ---------- semantic cache ----------
    query = f"Стать: {request.gender}, Вік: {request.age}, Симптоми: {guarded_symptoms}"
    if (sem := semantic_lookup(query)) is not None:
        return DiagnoseResponse(
            diagnosis=sem, 
            cached=True,
            symptoms_hash=symptoms_hash
        )
    
    # Check for cached approved answer in DB
    cached_answer = session.exec(
        select(DoctorAnswer).where(
            DoctorAnswer.symptoms_hash == symptoms_hash,
            DoctorAnswer.approved == True
        )
    ).first()
    
    if cached_answer:
        # also prime exact Redis cache for next time
        set_md(symptoms_hash, cached_answer.answer_md)
        return DiagnoseResponse(
            diagnosis=cached_answer.answer_md,
            cached=True,
            symptoms_hash=symptoms_hash
        )
    
    # Generate new diagnosis using RAG
    rag_result = generate_rag_response(query)
    
    # Apply output guardrails
    guarded_response = guard_output(rag_result["response"])
    
    # store fresh answer to Redis with TTL (not yet approved)
    set_md(symptoms_hash, guarded_response)
    
    return DiagnoseResponse(
        diagnosis=guarded_response,
        cached=False,
        symptoms_hash=symptoms_hash
    ) 