# LLM-асистент сімейного лікаря  (MVP)

Single-repo for data-prep **and** Streamlit UI.

* **data-prep** → `notebooks/data_prep.ipynb` (Google Colab badge below)
* **app**      → `app.py` (run locally or on Streamlit Cloud)

[![Run data prep in Colab](https://colab.research.google.com/assets/colab-badge.svg)]
(https://colab.research.google.com/github/rsliusarchuk/llm-family-doctor/blob/main/notebooks/data_prep.ipynb) 

## 🚀 LangChain & LangSmith Integration

This project now supports **LangChain** and **LangSmith** for enhanced RAG capabilities and monitoring:

### Features Added:
- **LangChain RAG Pipeline**: Structured retrieval and generation using LangChain components
- **LangSmith Tracing**: Monitor and debug your RAG pipeline in real-time
- **Enhanced Vector Store**: Better document handling with metadata
- **Backward Compatibility**: Original implementation still works if LangChain is not available

### New Components:
- `src/models/llm_client.py` - LLM client with embedding and response generation
- `src/models/langchain_vector_store.py` - Enhanced vector store with Document objects
- `src/models/rag_chain.py` - Complete RAG pipeline using LangChain

### Setup LangSmith (Optional):
1. Get your LangSmith API key from [smith.langchain.com](https://smith.langchain.com)
2. Add to your `.env` file:
   ```
   LANGSMITH_API_KEY=your_langsmith_api_key
   LANGSMITH_PROJECT=llm-family-doctor
   LANGSMITH_ENDPOINT=https://api.smith.langchain.com
   ```

### Benefits:
- **Monitoring**: Track query performance, token usage, and response quality
- **Debugging**: Inspect intermediate steps in the RAG pipeline
- **Experimentation**: A/B test different prompts and retrieval strategies
- **Production Ready**: Better error handling and observability

Ingest files:

```python scripts/ingest_protocol.py data/raw_pdfs/example.pdf```

```python scripts/ingest_protocol.py --dir data/raw_pdfs```

```python scripts/ingest_protocol.py --dir data/raw_pdfs --recursive```

# From the repo root (`llm_family_doctor/`)
conda create -n familydoc python=3.11 -y         # or any ≥3.9
conda activate familydoc

pip install -r requirements.txt

cp env.template .env          # then open .env and paste your key

# all PDFs in the default folder (non-recursive)
python scripts/ingest_protocol.py --dir data/raw_pdfs

# if they're nested in sub-folders
python scripts/ingest_protocol.py --dir data/raw_pdfs --recursive







