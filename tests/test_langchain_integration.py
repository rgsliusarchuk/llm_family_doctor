#!/usr/bin/env python
"""Test script to verify LangChain and LangSmith integration."""

import os
import sys
from pathlib import Path

# Add parent directory to path to import src modules
sys.path.insert(0, str(Path(__file__).parent.parent))

def test_imports():
    """Test that all LangChain components can be imported."""
    print("🔍 Testing imports...")
    
    try:
        from src.config import settings
        print("✅ Settings imported")
        
        from src.models.langchain_vector_store import search, search_documents
        print("✅ LangChain vector store imported")
        
        from src.models.rag_chain import generate_rag_response
        print("✅ RAG chain imported")
        
        return True
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False

def test_vector_search():
    """Test vector search functionality."""
    print("\n🔍 Testing vector search...")
    
    try:
        from src.models.langchain_vector_store import search, search_documents
        
        # Test basic search
        results = search("кашель", top_k=2)
        print(f"✅ Basic search returned {len(results)} results")
        
        # Test document search
        docs = search_documents("температура", top_k=2)
        print(f"✅ Document search returned {len(docs)} documents")
        
        return True
    except Exception as e:
        print(f"❌ Vector search test failed: {e}")
        return False

def test_rag_chain():
    """Test the complete RAG chain."""
    print("\n🔍 Testing RAG chain...")
    
    try:
        from src.models.rag_chain import generate_rag_response
        from src.models.langchain_vector_store import search_documents
        
        # Test document retrieval first
        print("  Testing document retrieval...")
        docs = search_documents("кашель, температура 38 °C у дитини 8 років", top_k=2)
        print(f"  ✅ Retrieved {len(docs)} documents")
        
        # Test RAG response
        print("  Testing RAG response generation...")
        query = "кашель, температура 38 °C у дитини 8 років"
        result = generate_rag_response(query, top_k=2)
        
        print(f"✅ RAG response generated: {len(result['response'])} characters")
        print(f"✅ Retrieved {len(result['documents'])} documents")
        
        return True
    except Exception as e:
        print(f"❌ RAG chain test failed: {e}")
        import traceback
        print(f"❌ Full traceback:")
        traceback.print_exc()
        return False

def test_langsmith_config():
    """Test LangSmith configuration."""
    print("\n🔍 Testing LangSmith configuration...")
    
    try:
        from src.config import settings
        
        if hasattr(settings, 'langsmith_api_key') and settings.langsmith_api_key:
            print("✅ LangSmith API key configured")
            print(f"✅ Project: {settings.langsmith_project}")
            print(f"✅ Endpoint: {settings.langsmith_endpoint}")
        else:
            print("⚠️  LangSmith not configured (optional)")
        
        return True
    except Exception as e:
        print(f"❌ LangSmith config test failed: {e}")
        return False

def main():
    """Run all tests."""
    print("🚀 Testing LangChain & LangSmith Integration\n")
    
    tests = [
        test_imports,
        test_vector_search,
        test_rag_chain,
        test_langsmith_config
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print(f"\n📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! LangChain integration is working correctly.")
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 