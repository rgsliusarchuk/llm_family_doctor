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

# ── Index validation and building ───────────────────────────────────────────────────────────
def ensure_index_exists():
    """Check if index exists, build if missing."""
    index_path = Path(settings.index_path)
    map_path = Path(settings.map_path)
    protocols_dir = Path("data/protocols")
    
    if not index_path.exists() or not map_path.exists():
        st.info("🔍 Індекс не знайдено. Перевіряємо наявність протоколів...")
        
        if not protocols_dir.exists() or not list(protocols_dir.glob("*.md")):
            st.error("❌ Не знайдено протоколів для індексування. Будь ласка, запустіть `python scripts/ingest_protocol.py` спочатку.")
            st.stop()
        
        st.info("🔨 Будуємо індекс... Це може зайняти кілька хвилин.")
        
        try:
            from src.indexing.build_index import build_index
            build_index(settings.model_id)
            st.success("✅ Індекс успішно створено!")
        except Exception as e:
            st.error(f"❌ Помилка створення індексу: {e}")
            st.stop()

# ── Initialize index on startup ─────────────────────────────────────────────────────────────
if 'index_checked' not in st.session_state:
    ensure_index_exists()
    st.session_state.index_checked = True

# ── local modules ──────────────────────────────────────────────────────────
from src.models.rag_chain import generate_rag_response

# ── Streamlit базова конфігурація ────────────────────────────────────────────────────────────
st.set_page_config(page_title="LLM-асистент", page_icon="🩺")
st.title("LLM-асистент сімейного лікаря — MVP")

# ── Sidebar (лише перегляд конфігу) ──────────────────────────────────────────────────────────
with st.sidebar:
    st.caption("⚙️ Конфігурація (read-only)")
    st.write(f"**Embedding-модель:** `{settings.model_id}`")
    st.write(f"**Індекс:** `{settings.index_path}`")
    st.write(f"**Doc-map:** `{settings.map_path}`")
    st.write("**LangChain:** ✅ Enabled")
    if hasattr(settings, 'langsmith_project'):
        st.write(f"**LangSmith:** `{settings.langsmith_project}`")

# ── поле введення симптомів ──────────────────────────────────────────────────────────────────
symptoms = st.text_area(
    "Опис симптомів пацієнта",
    placeholder="Напр.: біль у горлі, температура 38 °C, кашель 3 дні…"
)

# ── кнопка генерації ─────────────────────────────────────────────────────────
if st.button("Згенерувати попередній діагноз", type="primary"):
    # Clear previous feedback when generating new diagnosis
    if 'feedback_status' in st.session_state:
        st.session_state.feedback_status = None
        st.session_state.feedback_message = ""
    
    if not symptoms.strip():
        st.warning("Будь ласка, введіть симптоми.")
        st.stop()

    # Use LangChain RAG pipeline
    with st.spinner("Генеруємо відповідь (LangChain)…"):
        result = generate_rag_response(symptoms, top_k=3)
        answer = result["response"]
        retrieved_docs = result["documents"]

    # Store results in session state
    st.session_state.current_answer = answer
    st.session_state.current_symptoms = symptoms
    st.session_state.current_docs = retrieved_docs
    st.session_state.show_results = True

# ── відображення результатів ────────────────────────────────────────────────────────────────
if st.session_state.get('show_results', False):
    st.markdown("## Попередній діагноз і план лікування")
    st.markdown(st.session_state.current_answer)

    with st.expander("Показати використані протоколи"):
        for i, doc in enumerate(st.session_state.current_docs, 1):
            score = doc.metadata.get("similarity_score", 0.0)
            st.markdown(f"**Протокол {i}** (схожість: {score:.3f})  \n{doc.page_content}\n\n---")

    # ── цикл схвалення лікарем ───────────────────────────────────────────────────────────────
    col1, col2, col3 = st.columns(3)
    feedback_log = Path("logs/doctor_feedback.csv")
    feedback_log.parent.mkdir(parents=True, exist_ok=True)

    def log_feedback(status: str, edited: str | None = None):
        try:
            with feedback_log.open("a", newline="", encoding="utf-8") as f:
                csv.writer(f).writerow(
                    [dt.datetime.now().isoformat(), st.session_state.current_symptoms, status, edited or st.session_state.current_answer]
                )
            return True
        except Exception as e:
            st.error(f"Помилка збереження відгуку: {e}")
            return False

    # Initialize feedback state if not exists
    if 'feedback_status' not in st.session_state:
        st.session_state.feedback_status = None
        st.session_state.feedback_message = ""

    with col1:
        if st.button("Схвалити", key="approve_btn"):
            if log_feedback("approved"):
                st.rerun()
    with col2:
        if st.button("Відхилити", key="reject_btn"):
            if log_feedback("rejected"):
                st.rerun()
    with col3:
        edited = st.text_area("✏️ Відредагуйте перед збереженням:", value=st.session_state.current_answer, key="edit_area")
        if st.button("Зберегти редаговане", key="save_edited_btn"):
            if log_feedback("edited", edited):
                st.rerun()

if __name__ == "__main__":
    # This will be called when running with: streamlit run streamlit_app.py
    pass 