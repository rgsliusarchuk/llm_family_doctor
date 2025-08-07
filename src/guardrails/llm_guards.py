from typing import List, Optional
import re
from guardrails import Guard
from pydantic import BaseModel, Field, validator

# ─────────────────────────────────────────────────────────────────────────────
# Banned Words List
# ─────────────────────────────────────────────────────────────────────────────

BANNED_WORDS = [
    "fuck", "shit", "bitch", "ass", "damn", "hell",
    "пизда", "хуй", "блять", "сука", "ебать", "говно",
    # Add more as needed
]

# ─────────────────────────────────────────────────────────────────────────────
# Pydantic Models for Validation
# ─────────────────────────────────────────────────────────────────────────────

class GuardedInput(BaseModel):
    """Input model with character limit validation."""
    text: str = Field(..., max_length=1000)
    
    @validator('text')
    def strip_banned_words(cls, v):
        """Strip banned words from input."""
        words = v.lower().split()
        filtered_words = [word for word in words if word not in BANNED_WORDS]
        return ' '.join(filtered_words)

class GuardedOutput(BaseModel):
    """Output model with character limit and disclaimer."""
    response: str = Field(..., max_length=2000)
    
    def __init__(self, **data):
        super().__init__(**data)
        # Append disclaimer if not already present
        disclaimer = "\n\n⚠️ **Важливо:** Це лише попередній діагноз. Завжди консультуйтесь з лікарем для остаточного діагнозу та лікування."
        if disclaimer not in self.response:
            self.response += disclaimer

# ─────────────────────────────────────────────────────────────────────────────
# Guard Instances
# ─────────────────────────────────────────────────────────────────────────────

input_guard = Guard.from_pydantic(GuardedInput, description="Validate and clean user input")
output_guard = Guard.from_pydantic(GuardedOutput, description="Validate and format LLM output")

# ─────────────────────────────────────────────────────────────────────────────
# Helper Functions
# ─────────────────────────────────────────────────────────────────────────────

def guard_input(text: str) -> str:
    """
    Apply input guardrails to user text.
    
    Args:
        text: Raw user input
        
    Returns:
        Cleaned and validated text
    """
    try:
        result = input_guard.validate(text)
        return result.validated_output.text
    except Exception as e:
        # If validation fails, truncate and clean
        cleaned = text[:1000]  # Truncate to max length
        # Strip banned words
        words = cleaned.lower().split()
        filtered_words = [word for word in words if word not in BANNED_WORDS]
        return ' '.join(filtered_words)

def guard_output(response: str) -> str:
    """
    Apply output guardrails to LLM response.
    
    Args:
        response: Raw LLM response
        
    Returns:
        Validated and formatted response with disclaimer
    """
    try:
        result = output_guard.validate(response)
        return result.validated_output.response
    except Exception as e:
        # If validation fails, truncate and add disclaimer
        truncated = response[:2000]
        disclaimer = "\n\n⚠️ **Важливо:** Це лише попередній діагноз. Завжди консультуйтесь з лікарем для остаточного діагнозу та лікування."
        return truncated + disclaimer

def is_input_valid(text: str) -> bool:
    """
    Check if input passes all guardrails.
    
    Args:
        text: User input to validate
        
    Returns:
        True if input is valid, False otherwise
    """
    try:
        input_guard.validate(text)
        return True
    except:
        return False

def get_validation_errors(text: str) -> List[str]:
    """
    Get list of validation errors for input.
    
    Args:
        text: User input to validate
        
    Returns:
        List of validation error messages
    """
    errors = []
    
    if len(text) > 1000:
        errors.append("Текст занадто довгий (максимум 1000 символів)")
    
    banned_found = [word for word in BANNED_WORDS if word in text.lower()]
    if banned_found:
        errors.append(f"Знайдено заборонені слова: {', '.join(banned_found)}")
    
    return errors 