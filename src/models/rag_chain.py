#!/usr/bin/env python
"""src/models/rag_chain.py

Complete RAG (Retrieval-Augmented Generation) chain using LangChain.
This module provides a unified interface for the entire RAG pipeline:
1. Query embedding and retrieval
2. Context preparation
3. Response generation with LangSmith tracing (automatic when configured)
"""
from __future__ import annotations

from typing import List, Dict, Any
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from langchain_openai import ChatOpenAI
from langchain.schema import Document

from src.config import settings
from src.models.langchain_vector_store import search_documents
from src.models.prompts import FAMILY_DOCTOR_PROMPT_TEMPLATE

# ────────────────────────── LLM Setup ──────────────────────────────────────
llm = ChatOpenAI(
    model=settings.openai_model,
    temperature=0.2,
    api_key=settings.openai_api_key
)

# ────────────────────────── Prompt Template ────────────────────────────────
prompt = ChatPromptTemplate.from_template(FAMILY_DOCTOR_PROMPT_TEMPLATE)

# ────────────────────────── Helper Functions ────────────────────────────────
def retrieve_documents(query: str, top_k: int = 3) -> List[Document]:
    """Retrieve relevant documents for the query."""
    return search_documents(query, top_k)

def format_context(documents: List[Document]) -> str:
    """Format retrieved documents into context string."""
    if not documents:
        return "Не знайдено релевантних протоколів."
    
    context_parts = []
    for i, doc in enumerate(documents, 1):
        score = doc.metadata.get("similarity_score", 0.0)
        context_parts.append(f"Протокол {i} (релевантність: {score:.3f}):\n{doc.page_content}")
    
    return "\n\n".join(context_parts)

# ────────────────────────── RAG Chain ──────────────────────────────────────
def create_rag_chain(top_k: int = 3):
    """Create a RAG chain with the specified number of documents to retrieve."""
    
    def retrieve_and_format(input_dict):
        query = input_dict["query"]
        documents = retrieve_documents(query, top_k)
        context = format_context(documents)
        return {"query": query, "context": context}
    
    chain = (
        {"query": RunnablePassthrough()}
        | RunnableLambda(retrieve_and_format)
        | prompt
        | llm
        | StrOutputParser()
    )
    
    return chain

# ────────────────────────── Public API ─────────────────────────────────────
def generate_rag_response(query: str, top_k: int = 3) -> Dict[str, Any]:
    """Generate a response using the complete RAG pipeline with tracing."""
    
    try:
        # LangChain will automatically trace if LangSmith is configured
        chain = create_rag_chain(top_k)
        response = chain.invoke({"query": query})
        
        # Get retrieved documents for additional context
        documents = retrieve_documents(query, top_k)
        
        return {
            "response": response,
            "documents": documents,
            "query": query
        }
            
    except Exception as e:
        print(f"RAG chain error: {e}")
        raise

# ───────────────────────── Module self-test ─────────────────────────────────
if __name__ == "__main__":
    print("✔️  RAG chain initialized")
    print("✔️  LangSmith tracing:", "enabled" if settings.langsmith_api_key else "disabled")
    
    result = generate_rag_response("кашель, температура 38 °C у дитини 8 років", top_k=2)
    print(f"✔️  Response generated: {len(result['response'])} characters")
    print(f"✔️  Documents retrieved: {len(result['documents'])}")
    print("Response preview:", result['response'][:200], "...") 