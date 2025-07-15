import faiss, pickle, numpy as np
from sentence_transformers import SentenceTransformer
from src.config import settings

model = SentenceTransformer(settings.model_id)

index   = faiss.read_index(settings.index_path)
doc_map = pickle.load(open(settings.map_path, "rb"))

def search(query: str, top_k: int = 3):
    vec = model.encode(query, normalize_embeddings=True).astype("float32")[None]
    D, I = index.search(vec, top_k)
    return [(float(D[0][i]), doc_map[I[0][i]]) for i in range(top_k)]