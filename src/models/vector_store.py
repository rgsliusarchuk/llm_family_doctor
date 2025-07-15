import faiss, pickle, numpy as np
from sentence_transformers import SentenceTransformer
from src.config import settings

# Lazy loading to avoid tokenizer parallelism issues
_model = None
index   = faiss.read_index(settings.index_path)
doc_map = pickle.load(open(settings.map_path, "rb"))

def _get_model():
    """Get or create the SentenceTransformer model."""
    global _model
    if _model is None:
        _model = SentenceTransformer(settings.model_id)
    return _model

def search(query: str, top_k: int = 3):
    model = _get_model()
    vec = model.encode(query, normalize_embeddings=True).astype("float32")[None]
    D, I = index.search(vec, top_k)
    return [(float(D[0][i]), doc_map[I[0][i]]) for i in range(top_k)]