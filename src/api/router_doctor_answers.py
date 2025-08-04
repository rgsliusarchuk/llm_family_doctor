from __future__ import annotations

import hashlib
from typing import Dict, Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlmodel import Session, select

from src.db import get_session
from src.db.models import DoctorAnswer

router = APIRouter(
    prefix="/doctor_answers",
    tags=["doctor_answers"],
)

# ─────────────────────────────────────────────────────────────────────────────
# Request/Response Models
# ─────────────────────────────────────────────────────────────────────────────

class DoctorAnswerRequest(BaseModel):
    symptoms_hash: str
    answer_md: str
    approved: bool = False

# ─────────────────────────────────────────────────────────────────────────────
# Endpoints
# ─────────────────────────────────────────────────────────────────────────────

@router.post(
    "/",
    summary="Save/overwrite an approved or edited answer",
    status_code=status.HTTP_201_CREATED,
)
def upsert_doctor_answer(
    request: DoctorAnswerRequest,
    session: Session = Depends(get_session),
) -> Dict[str, Any]:
    db_obj = session.exec(
        select(DoctorAnswer).where(DoctorAnswer.symptoms_hash == request.symptoms_hash)
    ).first()
    if db_obj:
        db_obj.answer_md = request.answer_md
        db_obj.approved = request.approved
    else:
        db_obj = DoctorAnswer(
            symptoms_hash=request.symptoms_hash, 
            answer_md=request.answer_md,
            approved=request.approved
        )
        session.add(db_obj)
    session.commit()
    session.refresh(db_obj)
    return {"id": db_obj.id, "msg": "stored"}

# ─────────────────────────────────────────────────────────────────────────────
@router.patch(
    "/{answer_id}/status",
    summary="Toggle approved / rejected (used by Telegram bot)",
)
def set_answer_status(
    answer_id: int,
    approved: bool,
    session: Session = Depends(get_session),
) -> Dict[str, Any]:
    answer = session.get(DoctorAnswer, answer_id)
    if not answer:
        raise HTTPException(404, "answer not found")
    answer.approved = approved
    session.add(answer)
    session.commit()
    return {"id": answer.id, "approved": answer.approved} 