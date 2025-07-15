#!/usr/bin/env python
"""src/models/langchain_vector_store.py

LangChain-based vector store that provides:
• **search(query: str, top_k: int = 3) → List[Tuple[float, str]]** — returns similarity scores and document snippets
• **search_documents(query: str, top_k: int = 3) → List[Document]** — returns LangChain Document objects
• **add_documents(documents: List[Document])** — add new documents to the index

Features:
- LangChain Document integration
- Better metadata handling
- LangSmith tracing for search operations (automatic when configured)
"""
from __future__ import annotations

import os
# Disable tokenizers parallelism to avoid warnings in multiprocessing
os.environ["TOKENIZERS_PARALLELISM"] = "false"

import faiss
import pickle
import numpy as np
from typing import List, Tuple, Optional
from pathlib import Path

from sentence_transformers import SentenceTransformer
from langchain.schema import Document

from src.config import settings

# ────────────────────────── Vector Store ────────────────────────────────────
model = SentenceTransformer(settings.model_id)

# Load existing index and document map
index = faiss.read_index(settings.index_path)
doc_map = pickle.load(open(settings.map_path, "rb"))

# Validate index and document map compatibility
if index.ntotal != len(doc_map):
    print(f"Warning: FAISS index has {index.ntotal} documents but document map has {len(doc_map)} entries")
    print("This may cause issues with document retrieval")

# Note: doc_map is a list where index corresponds to FAISS index
# No need to check for sequential keys since it's a list

def search(query: str, top_k: int = 3) -> List[Tuple[float, str]]:
    """Search for similar documents and return (score, snippet) pairs."""
    try:
        # Convert query to list to avoid numpy int64 indexing issues
        vec = model.encode([query], normalize_embeddings=True).astype("float32")
        D, I = index.search(vec, top_k)
        
        results = []
        for i in range(top_k):
            idx = int(I[0][i])  # Convert numpy int64 to Python int
            score = float(D[0][i])
            
            # Check if the index is valid
            if idx < 0 or idx >= len(doc_map):
                print(f"Warning: Invalid index {idx} returned by FAISS (doc_map has {len(doc_map)} entries)")
                continue
                
            content = doc_map[idx]
            results.append((score, content))
        
        return results
            
    except Exception as e:
        print(f"Vector search error: {e}")
        raise

def search_documents(query: str, top_k: int = 3) -> List[Document]:
    """Search for similar documents and return LangChain Document objects."""
    results = search(query, top_k)
    
    documents = []
    for score, content in results:
        doc = Document(
            page_content=content,
            metadata={
                "similarity_score": score,
                "source": "clinical_protocols",
                "query": query
            }
        )
        documents.append(doc)
    
    return documents

def add_documents(documents: List[Document]) -> None:
    """Add new documents to the vector store."""
    # This is a placeholder - would need to implement document addition logic
    # For now, just raise NotImplementedError
    raise NotImplementedError("Document addition not yet implemented")

def get_index_stats() -> dict:
    """Get statistics about the current index."""
    return {
        "total_documents": index.ntotal,
        "embedding_dimension": index.d,
        "index_type": type(index).__name__
    }

# ───────────────────────── Module self-test ─────────────────────────────────
if __name__ == "__main__":
    print("✔️  Vector store loaded")
    print(f"✔️  Index shape: {index.ntotal} documents")
    
    results = search("кашель температура", top_k=2)
    print(f"✔️  Search test: {len(results)} results")
    for score, snippet in results:
        print(f"  Score: {score:.3f}, Snippet: {snippet[:100]}...") 