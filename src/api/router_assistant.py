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
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from src.config import settings

router = APIRouter(prefix="/assistant", tags=["assistant"])

# ─────────────────────────────────────────────────────────────────────────────
# Request/Response Models
# ─────────────────────────────────────────────────────────────────────────────

class AssistantRequest(BaseModel):
    user_id: Optional[str] = None
    chat_id: Optional[str] = None
    text: str

class AssistantResponse(BaseModel):
    message: str  # Natural language response for the user

# ─────────────────────────────────────────────────────────────────────────────
# LLM Setup for Response Generation
# ─────────────────────────────────────────────────────────────────────────────

_llm = ChatOpenAI(
    model=settings.openai_model,
    temperature=0.7,
    api_key=settings.openai_api_key,
)

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

async def generate_clinic_info_response(clinic_data: Dict[str, Any]) -> str:
    """Generate natural language response for clinic information."""
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a helpful medical clinic assistant. Respond in Ukrainian with a friendly, professional tone.
        Provide clinic information in a natural, conversational way that would be suitable for a Telegram bot."""),
        ("user", f"""Generate a natural response about clinic information based on this data:
        Address: {clinic_data.get('address', 'Not available')}
        Opening hours: {clinic_data.get('opening_hours', 'Not available')}
        Services: {clinic_data.get('services', 'Not available')}
        Phone: {clinic_data.get('phone', 'Not available')}
        
        Make it sound natural and helpful, as if you're talking to a patient."""),
    ])
    
    chain = prompt | _llm
    response = chain.invoke({})
    return response.content

async def generate_doctor_schedule_response(doctor_data: Dict[str, Any]) -> str:
    """Generate natural language response for doctor schedule."""
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a helpful medical clinic assistant. Respond in Ukrainian with a friendly, professional tone.
        Provide doctor schedule information in a natural, conversational way that would be suitable for a Telegram bot."""),
        ("user", f"""Generate a natural response about doctor schedule based on this data:
        Doctor name: {doctor_data.get('full_name', 'Not available')}
        Position: {doctor_data.get('position', 'Not available')}
        Schedule: {doctor_data.get('schedule', 'Not available')}
        
        Make it sound natural and helpful, as if you're talking to a patient."""),
    ])
    
    chain = prompt | _llm
    response = chain.invoke({})
    return response.content

async def handle_clinic_info(session: Session) -> str:
    """Handle clinic information requests and return natural language response."""
    clinic = session.exec(select(Clinic).limit(1)).first()
    
    if not clinic:
        return "Вибачте, інформація про клініку зараз недоступна. Спробуйте пізніше або зверніться до адміністрації."
    
    clinic_data = {
        "address": clinic.address,
        "opening_hours": clinic.opening_hours,
        "services": clinic.services,
        "phone": getattr(clinic, 'phone', None)
    }
    
    return await generate_clinic_info_response(clinic_data)

async def handle_doctor_schedule(text: str, session: Session) -> str:
    """Handle doctor schedule requests and return natural language response."""
    doctor_info = extract_doctor_info(text)
    
    if not doctor_info:
        return "Вибачте, не вдалося знайти інформацію про лікаря. Будь ласка, уточніть ім'я лікаря або його ID."
    
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
        return f"Вибачте, не знайдено лікаря з іменем або ID '{doctor_info}'. Перевірте правильність введених даних."
    
    doctor_data = {
        "full_name": doctor.full_name,
        "position": doctor.position,
        "schedule": doctor.schedule
    }
    
    return await generate_doctor_schedule_response(doctor_data)

async def handle_diagnose(text: str, user_id: Optional[str], chat_id: Optional[str], session: Session) -> str:
    """Handle diagnosis requests and return natural language response."""
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
    
    # Return the diagnosis message directly (assuming it's already in natural language)
    return result.diagnosis

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
    Returns natural language response suitable for Telegram bot.
    """
    # Classify user intent
    intent = classify_intent(request.text)
    
    try:
        # Dispatch based on intent
        if intent == IntentEnum.CLINIC_INFO:
            message = await handle_clinic_info(session)
        elif intent == IntentEnum.DOCTOR_SCHEDULE:
            message = await handle_doctor_schedule(request.text, session)
        elif intent == IntentEnum.DIAGNOSE:
            message = await handle_diagnose(request.text, request.user_id, request.chat_id, session)
        else:
            # Fallback to diagnose
            message = await handle_diagnose(request.text, request.user_id, request.chat_id, session)
        
        return AssistantResponse(message=message)
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Handle other errors gracefully
        error_message = "Вибачте, сталася помилка при обробці вашого запиту. Спробуйте ще раз або зверніться до адміністрації."
        return AssistantResponse(message=error_message) 