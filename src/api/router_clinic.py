from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from src.db import get_session
from src.db.models import Clinic

router = APIRouter(prefix="/clinics", tags=["clinic"])

@router.get("/", summary="Public clinic info")
def read_clinic(session: Session = Depends(get_session)) -> Clinic | None:
    return session.exec(select(Clinic).limit(1)).first()

@router.post("/", summary="Create / replace clinic card",
             status_code=status.HTTP_201_CREATED)
def upsert_clinic(data: Clinic, session: Session = Depends(get_session)) -> Clinic:
    db_obj = session.exec(select(Clinic).where(Clinic.id == data.id)).first()
    if db_obj:
        for field, value in data.dict(exclude_unset=True).items():
            setattr(db_obj, field, value)
    else:
        db_obj = data
        session.add(db_obj)
    session.commit()
    session.refresh(db_obj)
    return db_obj 