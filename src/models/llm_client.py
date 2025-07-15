#!/usr/bin/env python
"""src/models/llm_client.py

Single-file client that provides:
• **embedder(text | list[str]) → np.ndarray** — returns unit-norm float32 vectors using a Sentence-Transformers model.
• **generate_response(query, context) → str** — drafts a triaged Ukrainian answer via the OpenAI Chat Completions API.

Only the OpenAI backend is supported for generation; embeddings are always local.
Configuration is read from `.env` through `src.config.settings`:
    MODEL_ID      – HF embedding model (default set in settings)
    OPENAI_API_KEY
    OPENAI_MODEL  – e.g. "gpt-4o-mini" (fallback if unset)
"""
from __future__ import annotations

import os
import textwrap
from typing import List, Sequence

import numpy as np
from dotenv import load_dotenv
from openai import OpenAI
from sentence_transformers import SentenceTransformer

from src.config import settings

# ─────────────────────────── Environment ────────────────────────────────────
load_dotenv()  # loads KEY=value pairs from .env (repo root)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise EnvironmentError(
        "OPENAI_API_KEY is missing – add it to .env or export as env var"
    )

# ────────────────────────── Embedding model ─────────────────────────────────
_EMBED_MODEL_ID = settings.model_id
_embed_model = None

def _get_embed_model():
    """Get or create the SentenceTransformer model."""
    global _embed_model
    if _embed_model is None:
        _embed_model = SentenceTransformer(_EMBED_MODEL_ID)
    return _embed_model

def _get_embed_dim():
    """Get the embedding dimension."""
    model = _get_embed_model()
    return model.get_sentence_embedding_dimension()

EMBED_DIM = _get_embed_dim()


def embedder(text: str | Sequence[str]) -> np.ndarray:
    """Return 1-D or 2-D float32 unit-normalised embedding(s)."""
    model = _get_embed_model()
    single = isinstance(text, str)
    texts: List[str] = [text] if single else list(text)
    vecs = model.encode(
        texts,
        normalize_embeddings=True,  # inner-product == cosine
        show_progress_bar=False,
    )
    arr = np.asarray(vecs, dtype="float32")
    return arr[0] if single else arr

# ─────────────────────────── OpenAI client ──────────────────────────────────
_OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
_client = OpenAI()


def _openai_chat(prompt: str) -> str:
    """Low-level wrapper around Chat Completions."""
    resp = _client.chat.completions.create(
        model=_OPENAI_MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are an assistant for Ukrainian family doctors. "
                    "Use *only* the supplied clinical guidelines, write in Ukrainian, "
                    "and structure your answer clearly."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        temperature=0.2,
    )
    return resp.choices[0].message.content.strip()

# ─────────────────────────── Public API ─────────────────────────────────────

def generate_response(user_query: str, context: str) -> str:
    """Build the RAG prompt and return the assistant's answer."""
    prompt = textwrap.dedent(
        f"""
        ### Симптоми пацієнта
        {user_query}

        ### Доступні клінічні протоколи
        {context}

        ### Завдання
        1. Вкажи *ймовірний діагноз*.
        2. Сформулюй *план лікування* (нумерований список).
        3. Якщо даних замало, перерахуй потрібні обстеження.
        Відповідай українською, не вигадуй фактів поза контекстом.
        """
    ).strip()

    return _openai_chat(prompt)

# ───────────────────────── Module self-test ─────────────────────────────────
if __name__ == "__main__":
    print("✔️  Embedding dimension:", EMBED_DIM)
    draft = generate_response(
        "кашель, температура 38 °C у дитини 8 років",
        "Протокол: Гострі респіраторні вірусні інфекції у дітей…"
    )
    print(draft[:400], "…") 