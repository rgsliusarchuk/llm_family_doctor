from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
from sqlmodel import Session, select
from src.db import get_session
from src.db.models import DoctorAnswer
from src.config import settings

_model = SentenceTransformer(settings.model_id)

def _load_vectors():
    from src.db import engine
    with Session(engine) as s:
        docs = s.exec(select(DoctorAnswer)
                      .where(DoctorAnswer.approved==True)).all()
    if not docs:
        return faiss.IndexFlatIP(_model.get_sentence_embedding_dimension()), []
    texts = [d.answer_md for d in docs]
    vecs  = _model.encode(texts, normalize_embeddings=True).astype("float32")
    index = faiss.IndexFlatIP(vecs.shape[1])
    index.add(vecs)
    return index, texts

_index, _texts = _load_vectors()

def semantic_lookup(query: str, top_k:int=1) -> str|None:
    if _index.ntotal == 0:
        return None
    v = _model.encode([query], normalize_embeddings=True).astype("float32")
    D,I = _index.search(v, top_k)
    if D[0][0] > 0.92:          # tweakable threshold
        return _texts[I[0][0]]
    return None

def add_doc_to_index(text: str):
    """Add a new document to the semantic index."""
    global _index, _texts
    
    # Encode the new text
    vec = _model.encode([text], normalize_embeddings=True).astype("float32")
    
    # Add to index
    _index.add(vec)
    
    # Add to texts list
    _texts.append(text) 