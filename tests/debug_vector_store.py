#!/usr/bin/env python
"""Debug script to test vector store functionality."""

import os
# Disable tokenizers parallelism to avoid warnings in multiprocessing
os.environ["TOKENIZERS_PARALLELISM"] = "false"

import faiss
import pickle
import numpy as np
from sentence_transformers import SentenceTransformer
from src.config import settings

def debug_vector_store():
    """Debug the vector store to identify the issue."""
    print("🔍 Debugging vector store...")
    
    try:
        # Load the index
        print("Loading FAISS index...")
        index = faiss.read_index(settings.index_path)
        print(f"✅ Index loaded: {index.ntotal} documents, {index.d} dimensions")
        
        # Load the document map
        print("Loading document map...")
        with open(settings.map_path, "rb") as f:
            doc_map = pickle.load(f)
        print(f"✅ Document map loaded: {len(doc_map)} entries")
        
        # Check if indices match
        print(f"Index total: {index.ntotal}")
        print(f"Doc map length: {len(doc_map)}")
        print(f"Doc map type: {type(doc_map)}")
        
        # Check if there's a mismatch
        if index.ntotal != len(doc_map):
            print(f"⚠️  Mismatch: index has {index.ntotal} docs, map has {len(doc_map)} entries")
        
        # Test encoding
        print("Testing sentence transformer...")
        model = SentenceTransformer(settings.model_id)
        query = "кашель температура"
        vec = model.encode(query, normalize_embeddings=True).astype("float32")[None]
        print(f"✅ Query encoded: {vec.shape}")
        
        # Test search
        print("Testing FAISS search...")
        D, I = index.search(vec, 3)
        print(f"✅ Search completed")
        print(f"Distances: {D[0]}")
        print(f"Indices: {I[0]}")
        
        # Test document access
        print("Testing document access...")
        for i, idx in enumerate(I[0]):
            print(f"Index {i}: FAISS idx {idx}, type {type(idx)}")
            if 0 <= idx < len(doc_map):
                content = doc_map[idx]
                print(f"  Content length: {len(content)}")
                print(f"  Preview: {content[:100]}...")
            else:
                print(f"  ❌ Index {idx} out of range! (doc_map has {len(doc_map)} entries)")
                print(f"  Valid range: 0 to {len(doc_map) - 1}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    debug_vector_store() 