"""
Intent classification for assistant messages (Ukrainian-first).

We keep an ultra-light few-shot prompt and force the model to return
exactly one of:
    clinic_info | doctor_schedule | diagnose
"""

from __future__ import annotations
from enum import Enum
from typing import Literal

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

from src.config import settings

# ─────────────────────────────────────────────────────────────────────────────
class IntentEnum(str, Enum):
    CLINIC_INFO     = "clinic_info"
    DOCTOR_SCHEDULE = "doctor_schedule"
    DIAGNOSE        = "diagnose"

# ─────────── LLM setup ───────────────────────────────────────────────────────
_llm = ChatOpenAI(
    model=settings.openai_model,  # read from OPENAI_MODEL env var
    temperature=0.0,
    api_key=settings.openai_api_key,
)

# ─────────── Prompt ─────────────────────────────────────────────────────────
_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            (
                "You classify Ukrainian patient queries. "
                "Return ONLY one token: clinic_info, doctor_schedule, or diagnose."
            ),
        ),
        # ——— clinic_info ———
        ("user", "Де знаходиться ваша клініка?"),
        ("assistant", "clinic_info"),
        ("user", "Який у вас номер телефону та години роботи?"),
        ("assistant", "clinic_info"),

        # ——— doctor_schedule ———
        ("user", "Коли приймає доктор Іваненко?"),
        ("assistant", "doctor_schedule"),
        ("user", "Графік роботи лікаря 12?"),
        ("assistant", "doctor_schedule"),

        # ——— diagnose ———
        ("user", "У мене два дні температура 38 і кашель."),
        ("assistant", "diagnose"),
        ("user", "Моєму сину 5 років, болить живіт."),
        ("assistant", "diagnose"),

        # ——— runtime slot ———
        ("user", "{text}"),
    ]
)

_chain = _PROMPT | _llm

# ─────────── Public helper ───────────────────────────────────────────────────
def classify_intent(text: str) -> IntentEnum:               # noqa: D401
    """Return `IntentEnum` for the user message."""
    try:
        # BREAKPOINT: Set a breakpoint here to debug the classification
        response = _chain.invoke({"text": text})
        # Extract content from AIMessage object
        raw: str = response.content.strip().lower()
        print(f"DEBUG: Raw LLM response for '{text}': '{raw}'")
        return IntentEnum(raw)             # type: ignore[arg-type]
    except Exception as e:
        # Log the error for debugging
        print(f"Intent classification error: {e}")
        # Fallback – be safe and treat as medical question
        return IntentEnum.DIAGNOSE