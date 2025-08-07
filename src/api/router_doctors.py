from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from src.db import get_session
from src.db.models import Doctor

router = APIRouter(prefix="/doctors", tags=["doctors"])

@router.get("/", summary="List doctors")
def list_doctors(session: Session = Depends(get_session)):
    return session.exec(select(Doctor)).all()

@router.post("/", summary="Add new doctor",
             status_code=status.HTTP_201_CREATED)
def create_doctor(doc: Doctor, session: Session = Depends(get_session)) -> Doctor:
    session.add(doc)
    session.commit()
    session.refresh(doc)
    return doc 