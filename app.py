#!/usr/bin/env python
"""Streamlit-інтерфейс MVP «LLM-асистент сімейного лікаря»."""
from __future__ import annotations
import csv
import datetime as dt
import os
import sys
from pathlib import Path

# Add current directory to Python path for imports
sys.path.append(str(Path(__file__).parent))

# Disable tokenizers parallelism to avoid warnings in multiprocessing
os.environ["TOKENIZERS_PARALLELISM"] = "false"

import streamlit as st
from dotenv import load_dotenv

# ── env & settings ───────────────────────────────────────────────────────────
load_dotenv()

from src.config import settings

# ── local modules ──────────────────────────────────────────────────────────
# Try to use LangChain components first, fallback to original if not available
try:
    from src.models.rag_chain import generate_rag_response
    USE_LANGCHAIN = True
except ImportError:
    from src.models.vector_store import search
    from src.models.llm_client import generate_response
    USE_LANGCHAIN = False

# ── Streamlit базова конфігурація ────────────────────────────────────────────
st.set_page_config(page_title="LLM-асистент", page_icon="🩺")
st.title("LLM-асистент сімейного лікаря — MVP")

# ── Sidebar (лише перегляд конфігу) ──────────────────────────────────────────
with st.sidebar:
    st.caption("⚙️ Конфігурація (read-only)")
    st.write(f"**Embedding-модель:** `{settings.model_id}`")
    st.write(f"**Індекс:** `{settings.index_path}`")
    st.write(f"**Doc-map:** `{settings.map_path}`")
    st.write(f"**LangChain:** {'✅ Enabled' if USE_LANGCHAIN else '❌ Disabled'}")
    if hasattr(settings, 'langsmith_project'):
        st.write(f"**LangSmith:** `{settings.langsmith_project}`")

# ── поле введення симптомів ──────────────────────────────────────────────────
symptoms = st.text_area(
    "Опис симптомів пацієнта",
    placeholder="Напр.: біль у горлі, температура 38 °C, кашель 3 дні…"
)

# ── кнопка генерації ─────────────────────────────────────────────────────────
if st.button("Згенерувати попередній діагноз", type="primary"):
    if not symptoms.strip():
        st.warning("Будь ласка, введіть симптоми.")
        st.stop()

    if USE_LANGCHAIN:
        # Use LangChain RAG pipeline
        with st.spinner("Генеруємо відповідь (LangChain)…"):
            result = generate_rag_response(symptoms, top_k=3)
            answer = result["response"]
            retrieved_docs = result["documents"]
    else:
        # Fallback to original implementation
        retrieved = search(symptoms, top_k=3)
        if not retrieved:
            st.error("Не знайдено релевантних протоколів.")
            st.stop()

        context = "\n\n".join(snippet for _, snippet in retrieved)

        with st.spinner("Генеруємо відповідь…"):
            answer = generate_response(symptoms, context)
        
        # Convert to document format for consistency
        retrieved_docs = []
        for score, snippet in retrieved:
            from langchain.schema import Document
            doc = Document(
                page_content=snippet,
                metadata={"similarity_score": score}
            )
            retrieved_docs.append(doc)

    # 3) відображення
    st.markdown("## Попередній діагноз і план лікування")
    st.markdown(answer)

    with st.expander("Показати використані протоколи"):
        for i, doc in enumerate(retrieved_docs, 1):
            score = doc.metadata.get("similarity_score", 0.0)
            st.markdown(f"**Протокол {i}** (схожість: {score:.3f})  \n{doc.page_content}\n\n---")

    # ── цикл схвалення лікарем ───────────────────────────────────────────────
    col1, col2, col3 = st.columns(3)
    feedback_log = Path("logs/doctor_feedback.csv")
    feedback_log.parent.mkdir(parents=True, exist_ok=True)

    def log_feedback(status: str, edited: str | None = None):
        with feedback_log.open("a", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow(
                [dt.datetime.now().isoformat(), symptoms, status, edited or answer]
            )

    with col1:
        if st.button("Схвалити"):
            log_feedback("approved")
            st.success("Відповідь схвалено та збережено.")
    with col2:
        if st.button("Відхилити"):
            log_feedback("rejected")
            st.warning("Відповідь відхилено та збережено.")
    with col3:
        edited = st.text_area("✏️ Відредагуйте перед збереженням:", value=answer)
        if st.button("Зберегти редаговане"):
            log_feedback("edited", edited)
            st.success("Редаговану відповідь збережено.")