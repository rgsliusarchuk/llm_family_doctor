#!/usr/bin/env python
"""
Embed Ukrainian Markdown protocols with a Hugging-Face model
and save a FAISS index + ID→text map.

USAGE
  # in repo root, after ingest_protocol.py produced data/protocols/*.md
  python src/indexing/build_index.py \
         --hf-model intfloat/multilingual-e5-base
"""
from __future__ import annotations

import argparse, pickle
from pathlib import Path
from typing import Sequence

import faiss, numpy as np
from sentence_transformers import SentenceTransformer
import sys
from pathlib import Path

# Add the src directory to the Python path
sys.path.append(str(Path(__file__).parent.parent))

from config import settings

# paths ─────────────────────────────────────────────────────────────
PROTOCOLS_DIR = Path("data/protocols")
INDEX_PATH    = Path(settings.index_path)
MAP_PATH      = Path(settings.map_path)
SNIPPET_LEN   = 2_000               # first chars stored next to vector
BATCH_SIZE    = 16                  # tweak for GPU / RAM

# ──────────────── helper ───────────────────────────────────────────
def embed_docs(model: SentenceTransformer,
               docs: Sequence[str]) -> np.ndarray:
    """Return NxD float32 matrix."""
    vecs = model.encode(
        list(docs),
        batch_size=BATCH_SIZE,
        show_progress_bar=False,
        normalize_embeddings=True,         # cosine → L2
    )
    return np.asarray(vecs, dtype="float32")

# ─────────────── main ──────────────────────────────────────────────
def build_index(hf_model_id: str):
    md_files = sorted(PROTOCOLS_DIR.glob("*.md"))
    if not md_files:
        raise SystemExit("No .md files in data/protocols – run ingest_protocol.py first.")

    print(f"🔹 Loading {hf_model_id} …")
    model = SentenceTransformer(hf_model_id)

    texts, snippets = [], []
    for fp in md_files:
        txt = fp.read_text(encoding="utf-8")
        texts.append(txt)
        snippets.append(txt[:SNIPPET_LEN])

    print(f"🔹 Encoding {len(texts)} documents")
    vectors = embed_docs(model, texts)           # -> ndarray [N, D]

    # FAISS expects float32 & contiguous
    index = faiss.IndexFlatIP(vectors.shape[1])  # cosine sim (normed)
    index.add(vectors)

    INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
    faiss.write_index(index, str(INDEX_PATH))
    with open(MAP_PATH, "wb") as f:
        pickle.dump(snippets, f)

    print(f"✅  Saved index → {INDEX_PATH}  (vectors: {index.ntotal})")

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--hf-model",
                   default=settings.model_id,
                   help="Sentence-Transformers model id")
    args = p.parse_args()
    build_index(args.hf_model)