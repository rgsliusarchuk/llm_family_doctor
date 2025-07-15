#!/usr/bin/env python
"""src/models/prompts.py

Shared prompt templates for the family doctor assistant.
This module consolidates all prompt templates to avoid duplication.
"""
from __future__ import annotations

# ────────────────────────── Main Prompt Template ────────────────────────────────
FAMILY_DOCTOR_PROMPT_TEMPLATE = """You are an assistant for Ukrainian family doctors. 
Use *only* the supplied clinical guidelines, write in Ukrainian, 
and structure your answer clearly.

### Симптоми пацієнта
{query}

### Доступні клінічні протоколи
{context}

### Завдання
1. Вкажи *ймовірний діагноз*.
2. Сформулюй *план лікування* (нумерований список).
3. Якщо даних замало, перерахуй потрібні обстеження.
Відповідай українською, не вигадуй фактів поза контекстом.
"""

# ────────────────────────── System Message ──────────────────────────────────────
FAMILY_DOCTOR_SYSTEM_MESSAGE = """You are an assistant for Ukrainian family doctors. 
Use *only* the supplied clinical guidelines, write in Ukrainian, 
and structure your answer clearly."""

# ────────────────────────── Legacy Prompt (for llm_client.py) ───────────────────
def build_legacy_prompt(user_query: str, context: str) -> str:
    """Build the legacy prompt format used by llm_client.py."""
    return f"""
### Симптоми пацієнта
{user_query}

### Доступні клінічні протоколи
{context}

### Завдання
1. Вкажи *ймовірний діагноз*.
2. Сформулюй *план лікування* (нумерований список).
3. Якщо даних замало, перерахуй потрібні обстеження.
Відповідай українською, не вигадуй фактів поза контекстом.
""".strip() 