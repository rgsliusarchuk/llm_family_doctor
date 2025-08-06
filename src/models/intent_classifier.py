#!/usr/bin/env python
"""Intent classification for assistant messages."""
from __future__ import annotations

from enum import Enum
from typing import Literal
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

from src.config import settings

class IntentEnum(str, Enum):
    """Intent classification for user messages."""
    CLINIC_INFO = "clinic_info"
    DOCTOR_SCHEDULE = "doctor_schedule"
    DIAGNOSE = "diagnose"

# LLM for intent classification
classifier_llm = ChatOpenAI(
    model="gpt-4.1-mini",
    temperature=0.1,
    api_key=settings.openai_api_key
)

# Few-shot prompt for intent classification
INTENT_CLASSIFICATION_PROMPT = """You are an intent classifier for a medical assistant. Classify the user's message into one of three categories:

1. **clinic_info** - Questions about clinic address, hours, phone, services, location
2. **doctor_schedule** - Asking for doctor's full name, position, schedule, availability
3. **diagnose** - Medical symptoms, health concerns, "I feel...", "I have...", "My child has..."

Examples:
- "Where is your clinic located?" → clinic_info
- "What are your opening hours?" → clinic_info
- "Can I see Dr. Smith's schedule?" → doctor_schedule
- "When is Dr. Johnson available?" → doctor_schedule
- "I have a headache" → diagnose
- "My child has a fever" → diagnose
- "I feel dizzy" → diagnose

User message: {text}

Respond with ONLY the intent category (clinic_info, doctor_schedule, or diagnose):"""

intent_prompt = ChatPromptTemplate.from_template(INTENT_CLASSIFICATION_PROMPT)

def classify_intent(text: str) -> IntentEnum:
    """
    Classify user message intent using OpenAI.
    
    Args:
        text: User message text
        
    Returns:
        IntentEnum: Classified intent
    """
    try:
        # Create classification chain
        chain = intent_prompt | classifier_llm
        
        # Get classification
        result = chain.invoke({"text": text})
        
        # Clean and validate result
        intent_str = result.strip().lower()
        
        # Map to enum
        if intent_str == "clinic_info":
            return IntentEnum.CLINIC_INFO
        elif intent_str == "doctor_schedule":
            return IntentEnum.DOCTOR_SCHEDULE
        elif intent_str == "diagnose":
            return IntentEnum.DIAGNOSE
        else:
            # Default to diagnose for unclear cases
            return IntentEnum.DIAGNOSE
            
    except Exception as e:
        # Default to diagnose on error
        return IntentEnum.DIAGNOSE 