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
    intent: str  # Intent classification
    data: dict   # Response data
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
# Conversation State Management
# ─────────────────────────────────────────────────────────────────────────────

# In-memory storage for conversation state (in production, use Redis)
_conversation_states: Dict[str, Dict[str, Any]] = {}

def _get_conversation_state(user_id: str, chat_id: str) -> Dict[str, Any]:
    """Get conversation state for user/chat."""
    key = f"{user_id}:{chat_id}"
    return _conversation_states.get(key, {})

def _save_conversation_state(user_id: str, chat_id: str, state: Dict[str, Any]):
    """Save conversation state for user/chat."""
    import logging
    logger = logging.getLogger(__name__)
    key = f"{user_id}:{chat_id}"
    _conversation_states[key] = state
    logger.info(f"Saved conversation state with key '{key}': {state}")
    logger.info(f"Total conversation states: {len(_conversation_states)}")

def _clear_conversation_state(user_id: str, chat_id: str):
    """Clear conversation state for user/chat."""
    key = f"{user_id}:{chat_id}"
    if key in _conversation_states:
        del _conversation_states[key]

def _extract_patient_info(text: str) -> tuple[Optional[str], Optional[int]]:
    """
    Extract gender and age from text.
    Returns (gender, age) where gender is 'm', 'f', or None, and age is int or None.
    """
    import logging
    logger = logging.getLogger(__name__)
    
    text_lower = text.lower()
    gender = None
    age = None
    
    logger.info(f"Extracting patient info from text: '{text}' (lower: '{text_lower}')")
    
    # Extract gender
    if any(word in text_lower for word in ["жінка", "дівчина", "донька", "доньці", "жіноча", "female", "woman", "girl"]):
        gender = "f"
        logger.info(f"Extracted gender: {gender}")
    elif any(word in text_lower for word in ["чоловік", "хлопець", "син", "хлопчик", "чоловіча", "male", "man", "boy"]):
        gender = "m"
        logger.info(f"Extracted gender: {gender}")
    
    # Extract age
    import re
    # Look for age patterns like "30 років", "30 years", "вік 30", etc.
    age_patterns = [
        r'(\d+)\s*(?:років?|роки|years?)',
        r'вік\s*(\d+)',
        r'age\s*(\d+)',
        r'(\d+)\s*рік',
        r'(\d+)\s*року',
        r'(\d+)\s*років'  # Explicit pattern for "років"
    ]
    
    for pattern in age_patterns:
        match = re.search(pattern, text_lower)
        if match:
            age = int(match.group(1))
            logger.info(f"Extracted age: {age} using pattern: {pattern}")
            break
        else:
            logger.debug(f"Pattern '{pattern}' did not match text: '{text_lower}'")
    
    logger.info(f"Final extraction result: gender={gender}, age={age}")
    return gender, age

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

async def translate_and_format_clinic_data(clinic) -> Dict[str, Any]:
    """Translate and format clinic data from English to Ukrainian using LLM."""
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a helpful medical clinic assistant. Translate and format clinic information from English to Ukrainian.
        Return the data in a structured format that can be used by a Telegram bot.
        
        Rules:
        1. Translate all text to Ukrainian
        2. Format addresses in Ukrainian style
        3. Convert time formats to Ukrainian style (e.g., "Mon-Sat 08-20" → "Пн-Сб 08:00-20:00")
        4. Translate service names to Ukrainian medical terms
        5. Return only the translated values, no explanations
        6. IMPORTANT: Return ONLY valid JSON, no other text"""),
        ("user", f"""Translate and format this clinic data to Ukrainian:
        Address: {clinic.address}
        Opening hours: {clinic.opening_hours}
        Services: {clinic.services}
        Phone: {getattr(clinic, 'phone', 'Not available')}
        
        Return ONLY this JSON format (no other text):
        {{{{ 
            "address": "translated_address",
            "opening_hours": "translated_opening_hours", 
            "services": "translated_services",
            "phone": "translated_phone_or_null"
        }}}}"""),
    ])
    
    chain = prompt | _llm
    response = chain.invoke({})
    
    # Parse the JSON response
    import json
    import logging
    
    logger = logging.getLogger(__name__)
    
    try:
        # First try to parse the entire response as JSON
        translated_data = json.loads(response.content.strip())
        logger.info(f"Successfully parsed JSON from LLM response: {translated_data}")
        return translated_data
    except json.JSONDecodeError as e:
        logger.warning(f"Failed to parse JSON from LLM response: {response.content}")
        logger.warning(f"JSON decode error: {e}")
        
        # Try to extract JSON from the response (in case LLM adds extra text)
        import re
        json_match = re.search(r'\{.*\}', response.content, re.DOTALL)
        if json_match:
            try:
                translated_data = json.loads(json_match.group())
                logger.info(f"Successfully extracted and parsed JSON: {translated_data}")
                return translated_data
            except json.JSONDecodeError as e2:
                logger.warning(f"Failed to parse extracted JSON: {e2}")
        
        # Fallback to original data if translation fails
        logger.info("Using fallback to original clinic data")
        return {
            "address": clinic.address,
            "opening_hours": clinic.opening_hours,
            "services": clinic.services,
            "phone": getattr(clinic, 'phone', None)
        }

async def generate_contextual_clinic_response(user_question: str, clinic_data: Dict[str, Any]) -> str:
    """Generate contextual, natural language response for clinic questions."""
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a helpful medical clinic assistant. Respond in Ukrainian with a friendly, professional tone.
        Answer the specific question asked by the user in a natural, conversational way.
        Be direct and helpful, as if you're talking to a patient on the phone."""),
        ("user", f"""The user asked: "{user_question}"
        
        Here is the clinic information:
        Address: {clinic_data.get('address', 'Not available')}
        Opening hours: {clinic_data.get('opening_hours', 'Not available')}
        Services: {clinic_data.get('services', 'Not available')}
        Phone: {clinic_data.get('phone', 'Not available')}
        
        Provide a natural, conversational answer to their specific question. Don't just list all the information - answer what they actually asked."""),
    ])
    
    chain = prompt | _llm
    response = chain.invoke({})
    return response.content

async def generate_contextual_doctor_response(user_question: str, doctor_data: Dict[str, Any]) -> str:
    """Generate contextual, natural language response for doctor questions."""
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a helpful medical clinic assistant. Respond in Ukrainian with a friendly, professional tone.
        Answer the specific question asked by the user about the doctor in a natural, conversational way."""),
        ("user", f"""The user asked: "{user_question}"
        
        Here is the doctor information:
        Name: {doctor_data.get('full_name', 'Not available')}
        Position: {doctor_data.get('position', 'Not available')}
        Schedule: {doctor_data.get('schedule', 'Not available')}
        
        Provide a natural, conversational answer to their specific question about this doctor."""),
    ])
    
    chain = prompt | _llm
    response = chain.invoke({})
    return response.content

async def generate_general_doctor_response(user_question: str, session: Session) -> str:
    """Generate response for general doctor availability questions."""
    # Get all doctors
    doctors = session.exec(select(Doctor)).all()
    
    if not doctors:
        return "Вибачте, зараз немає інформації про лікарів. Спробуйте пізніше або зверніться до адміністрації."
    
    doctors_info = []
    for doctor in doctors:
        doctors_info.append(f"- {doctor.full_name} ({doctor.position}): {doctor.schedule}")
    
    doctors_text = "\n".join(doctors_info)
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a helpful medical clinic assistant. Respond in Ukrainian with a friendly, professional tone.
        Answer general questions about doctor availability in a natural, conversational way."""),
        ("user", f"""The user asked: "{user_question}"
        
        Here are all the doctors at the clinic:
        {doctors_text}
        
        Provide a natural, conversational answer to their question about doctor availability."""),
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

async def handle_diagnose_with_conversation(
    text: str, 
    user_id: Optional[str], 
    chat_id: Optional[str], 
    session: Session
) -> tuple[str, Dict[str, Any]]:
    """
    Handle diagnosis requests with conversation flow to collect missing patient info.
    Returns (message, data) where data contains conversation state info.
    """
    import logging
    logger = logging.getLogger(__name__)
    
    if not user_id or not chat_id:
        # Fallback to old behavior if no user/chat ID
        logger.warning(f"No user_id or chat_id provided, using legacy handler")
        return await handle_diagnose_legacy(text, session), {}
    
    # Get current conversation state
    state = _get_conversation_state(user_id, chat_id)
    logger.info(f"Current conversation state for {user_id}:{chat_id}: {state}")
    
    # Check if we're in the middle of collecting patient info
    if state.get("collecting_info"):
        logger.info(f"Continuing info collection for {user_id}:{chat_id}")
        return await _handle_info_collection(text, user_id, chat_id, state, session)
    
    # Try to extract patient info from the current message
    gender, age = _extract_patient_info(text)
    
    # If we have both gender and age, proceed with diagnosis
    if gender and age:
        # Clear any existing conversation state
        _clear_conversation_state(user_id, chat_id)
        
        # Create diagnosis request
        from src.api.router_diagnose import DiagnoseRequest, diagnose
        diagnose_request = DiagnoseRequest(
            gender=gender,
            age=age,
            symptoms=text
        )
        
        # Generate diagnosis
        result = await diagnose(diagnose_request, session)
        
        return result.diagnosis, {
            "diagnosis": result.diagnosis,
            "symptoms_hash": result.symptoms_hash
        }
    
    # If we're missing info, start collecting it
    missing_info = []
    if not gender:
        missing_info.append("стать")
    if not age:
        missing_info.append("вік")
    
    # Start conversation to collect missing info
    new_state = {
        "collecting_info": True,
        "missing_gender": not gender,
        "missing_age": not age,
        "symptoms": text,
        "extracted_gender": gender,
        "extracted_age": age
    }
    _save_conversation_state(user_id, chat_id, new_state)
    
    # Generate appropriate message asking for missing info
    if len(missing_info) == 2:
        message = "Для точного діагнозу мені потрібна додаткова інформація. Будь ласка, вкажіть:\n\n1. Стать (чоловіча/жіноча)\n2. Вік (скільки років)"
    else:
        missing = missing_info[0]
        if missing == "стать":
            message = "Для точного діагнозу вкажіть, будь ласка, стать (чоловіча/жіноча)."
        else:
            message = "Для точного діагнозу вкажіть, будь ласка, вік (скільки років)."
    
    return message, {"conversation_state": "collecting_info"}

async def _handle_info_collection(
    text: str, 
    user_id: str, 
    chat_id: str, 
    state: Dict[str, Any], 
    session: Session
) -> tuple[str, Dict[str, Any]]:
    """Handle the collection of missing patient information."""
    import logging
    logger = logging.getLogger(__name__)
    
    logger.info(f"Handling info collection for {user_id}:{chat_id} with text: '{text}'")
    logger.info(f"Current state: {state}")
    
    # Try to extract gender and age from the response
    gender, age = _extract_patient_info(text)
    logger.info(f"Extracted from response: gender={gender}, age={age}")
    
    # Update state with any new information
    if gender and state.get("missing_gender"):
        state["extracted_gender"] = gender
        state["missing_gender"] = False
        logger.info(f"Updated state with gender: {gender}")
    if age and state.get("missing_age"):
        state["extracted_age"] = age
        state["missing_age"] = False
        logger.info(f"Updated state with age: {age}")
    
    logger.info(f"Updated state: {state}")
    
    # Check if we now have all required information
    if not state.get("missing_gender") and not state.get("missing_age"):
        # We have all info, proceed with diagnosis
        final_gender = state["extracted_gender"]
        final_age = state["extracted_age"]
        symptoms = state["symptoms"]
        
        # Clear conversation state
        _clear_conversation_state(user_id, chat_id)
        
        # Create diagnosis request
        from src.api.router_diagnose import DiagnoseRequest, diagnose
        diagnose_request = DiagnoseRequest(
            gender=final_gender,
            age=final_age,
            symptoms=symptoms
        )
        
        # Generate diagnosis
        result = await diagnose(diagnose_request, session)
        
        return result.diagnosis, {
            "diagnosis": result.diagnosis,
            "symptoms_hash": result.symptoms_hash
        }
    
    # Still missing some info, ask for it
    missing_info = []
    if state.get("missing_gender"):
        missing_info.append("стать")
    if state.get("missing_age"):
        missing_info.append("вік")
    
    # Save updated state
    _save_conversation_state(user_id, chat_id, state)
    logger.info(f"Saved conversation state for {user_id}:{chat_id}: {state}")
    
    # Generate message asking for remaining info
    if len(missing_info) == 2:
        message = "Будь ласка, вкажіть:\n\n1. Стать (чоловіча/жіноча)\n2. Вік (скільки років)"
    else:
        missing = missing_info[0]
        if missing == "стать":
            message = "Будь ласка, вкажіть стать (чоловіча/жіноча)."
        else:
            message = "Будь ласка, вкажіть вік (скільки років)."
    
    return message, {"conversation_state": "collecting_info"}

async def handle_diagnose_legacy(text: str, session: Session) -> str:
    """Legacy diagnosis handler for backward compatibility."""
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
    from src.api.router_diagnose import DiagnoseRequest, diagnose
    diagnose_request = DiagnoseRequest(
        gender=gender,
        age=age,
        symptoms=text
    )
    
    # Call the existing diagnose function directly instead of making HTTP request
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
    import logging
    logger = logging.getLogger(__name__)
    
    # Classify user intent
    intent = classify_intent(request.text)
    logger.info(f"Classified intent: {intent} for text: '{request.text}'")
    
    try:
        # Dispatch based on intent
        if intent == IntentEnum.CLINIC_INFO:
            # Get clinic data and generate natural language response
            clinic = session.exec(select(Clinic).limit(1)).first()
            if clinic:
                try:
                    # Translate and format clinic data using LLM
                    translated_clinic_data = await translate_and_format_clinic_data(clinic)
                    # Generate contextual response based on the specific question
                    message = await generate_contextual_clinic_response(request.text, translated_clinic_data)
                    data = {"message": message}  # Return natural language response
                except Exception as e:
                    logger.warning(f"Translation failed, using original data: {e}")
                    # Fallback to original data if translation fails
                    clinic_data = {
                        "address": clinic.address,
                        "opening_hours": clinic.opening_hours,
                        "services": clinic.services,
                        "phone": getattr(clinic, 'phone', None)
                    }
                    message = await generate_contextual_clinic_response(request.text, clinic_data)
                    data = {"message": message}
            else:
                message = "Вибачте, інформація про клініку зараз недоступна. Спробуйте пізніше або зверніться до адміністрації."
                data = {"message": message}
        elif intent == IntentEnum.DOCTOR_SCHEDULE:
            # Get doctor data and generate natural language response
            doctor_info = extract_doctor_info(request.text)
            if doctor_info:
                doctor = None
                if doctor_info.isdigit():
                    doctor = session.exec(select(Doctor).where(Doctor.id == int(doctor_info))).first()
                if not doctor:
                    doctor = session.exec(select(Doctor).where(Doctor.full_name.ilike(f"%{doctor_info}%"))).first()
                
                if doctor:
                    doctor_data = {
                        "full_name": doctor.full_name,
                        "position": doctor.position,
                        "schedule": doctor.schedule
                    }
                    message = await generate_contextual_doctor_response(request.text, doctor_data)
                    data = {"message": message}  # Return natural language response
                else:
                    message = f"Вибачте, не знайдено лікаря з іменем або ID '{doctor_info}'. Перевірте правильність введених даних."
                    data = {"message": message}
            else:
                # Handle general doctor availability questions
                message = await generate_general_doctor_response(request.text, session)
                data = {"message": message}
        elif intent == IntentEnum.DIAGNOSE:
            # Use conversation-aware diagnosis handler
            message, data = await handle_diagnose_with_conversation(
                request.text, 
                request.user_id, 
                request.chat_id, 
                session
            )
        else:
            # Fallback to diagnose with conversation
            message, data = await handle_diagnose_with_conversation(
                request.text, 
                request.user_id, 
                request.chat_id, 
                session
            )
        
        return AssistantResponse(
            intent=intent.value,
            data=data,
            message=message
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Handle other errors gracefully
        logger.error(f"Error processing request '{request.text}': {str(e)}", exc_info=True)
        error_message = "Вибачте, сталася помилка при обробці вашого запиту. Спробуйте ще раз або зверніться до адміністрації."
        return AssistantResponse(
            intent="unknown",
            data={"error": str(e)},
            message=error_message
        ) 