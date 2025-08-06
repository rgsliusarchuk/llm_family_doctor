#!/usr/bin/env python
"""Assistant router - façade endpoint for all user interactions."""
from __future__ import annotations

from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlmodel import Session, select

from src.db import get_session
from src.db.models import Clinic, Doctor
from src.models.intent_classifier import classify_intent, IntentEnum
from src.api.router_diagnose import diagnose

router = APIRouter(prefix="/assistant", tags=["assistant"])

# ─────────────────────────────────────────────────────────────────────────────
# Request/Response Models
# ─────────────────────────────────────────────────────────────────────────────

class AssistantRequest(BaseModel):
    user_id: Optional[str] = None
    chat_id: Optional[str] = None
    text: str

class AssistantResponse(BaseModel):
    intent: str  # "clinic_info", "doctor_schedule", "diagnose"
    data: Dict[str, Any]

# ─────────────────────────────────────────────────────────────────────────────
# Helper Functions
# ─────────────────────────────────────────────────────────────────────────────

def extract_doctor_info(text: str) -> Optional[str]:
    """
    Extract doctor name or ID from text.
    Simple extraction - in production, use NER or more sophisticated parsing.
    """
    # Look for common patterns
    text_lower = text.lower()
    
    # Check for "Dr." or "doctor" followed by name
    if "dr." in text_lower or "doctor" in text_lower:
        # Simple extraction - find words after "dr." or "doctor"
        words = text.split()
        for i, word in enumerate(words):
            if word.lower() in ["dr.", "doctor"] and i + 1 < len(words):
                return words[i + 1]
    
    # Check for doctor ID patterns (numbers)
    import re
    numbers = re.findall(r'\d+', text)
    if numbers:
        return numbers[0]
    
    return None

async def handle_clinic_info(session: Session) -> Dict[str, Any]:
    """Handle clinic information requests."""
    clinic = session.exec(select(Clinic).limit(1)).first()
    
    if not clinic:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Clinic information not available"
        )
    
    return {
        "address": clinic.address,
        "opening_hours": clinic.opening_hours,
        "services": clinic.services,
        "phone": getattr(clinic, 'phone', None)  # Optional field
    }

async def handle_doctor_schedule(text: str, session: Session) -> Dict[str, Any]:
    """Handle doctor schedule requests."""
    doctor_info = extract_doctor_info(text)
    
    if not doctor_info:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="doctor_not_found"
        )
    
    # Try to find doctor by name or ID
    doctor = None
    
    # First try by ID if it's a number
    if doctor_info.isdigit():
        doctor = session.exec(
            select(Doctor).where(Doctor.id == int(doctor_info))
        ).first()
    
    # If not found by ID, try by name
    if not doctor:
        doctor = session.exec(
            select(Doctor).where(Doctor.full_name.ilike(f"%{doctor_info}%"))
        ).first()
    
    if not doctor:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="doctor_not_found"
        )
    
    return {
        "full_name": doctor.full_name,
        "position": doctor.position,
        "schedule": doctor.schedule
    }

async def handle_diagnose(text: str, user_id: Optional[str], chat_id: Optional[str], session: Session) -> Dict[str, Any]:
    """Handle diagnosis requests by calling the existing diagnose endpoint."""
    # For diagnosis, we need to extract basic info from text
    # This is a simplified approach - in production, you might want more sophisticated parsing
    
    # Default values - in production, you might want to ask for these
    gender = "m"  # Default
    age = 30      # Default
    
    # Simple extraction attempts
    text_lower = text.lower()
    if "female" in text_lower or "woman" in text_lower or "girl" in text_lower:
        gender = "f"
    elif "male" in text_lower or "man" in text_lower or "boy" in text_lower:
        gender = "m"
    
    # Try to extract age
    import re
    age_match = re.search(r'(\d+)\s*(?:years?|рік|років)', text_lower)
    if age_match:
        age = int(age_match.group(1))
    
    # Create diagnosis request
    from src.api.router_diagnose import DiagnoseRequest
    diagnose_request = DiagnoseRequest(
        gender=gender,
        age=age,
        symptoms=text
    )
    
    # Call the existing diagnose function directly instead of making HTTP request
    from src.api.router_diagnose import diagnose
    result = await diagnose(diagnose_request, session)
    
    return {
        "diagnosis": result.diagnosis,
        "cached": result.cached,
        "symptoms_hash": result.symptoms_hash
    }

# ─────────────────────────────────────────────────────────────────────────────
# Endpoints
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/message", response_model=AssistantResponse)
async def handle_message(
    request: AssistantRequest,
    session: Session = Depends(get_session)
) -> AssistantResponse:
    """
    Main façade endpoint that handles all user messages.
    Classifies intent and dispatches to appropriate handler.
    """
    # Classify user intent
    intent = classify_intent(request.text)
    
    try:
        # Dispatch based on intent
        if intent == IntentEnum.CLINIC_INFO:
            data = await handle_clinic_info(session)
        elif intent == IntentEnum.DOCTOR_SCHEDULE:
            data = await handle_doctor_schedule(request.text, session)
        elif intent == IntentEnum.DIAGNOSE:
            data = await handle_diagnose(request.text, request.user_id, request.chat_id, session)
        else:
            # Fallback to diagnose
            data = await handle_diagnose(request.text, request.user_id, request.chat_id, session)
            intent = IntentEnum.DIAGNOSE
        
        return AssistantResponse(
            intent=intent.value,
            data=data
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Handle other errors gracefully
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        ) 