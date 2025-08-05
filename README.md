# LLM-асистент сімейного лікаря (MVP)

Single-repo for data-prep **and** Streamlit UI.

* **data-prep** → `notebooks/data_prep.ipynb` (Google Colab badge below)
* **app**      → `app.py` (run locally or on Streamlit Cloud)
* **testing**  → `tests/test_index.py` (comprehensive index testing)

[![Run data prep in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/rgsliusarchuk/llm_family_doctor/blob/master/notebooks/data_prep.ipynb)

## 🚀 Quick Start

### Option 1: Google Colab (Recommended for Data Prep)
1. Click the Colab badge above to open the enhanced notebook
2. Run cells sequentially to set up environment and process data
3. Test the index with various medical queries

### Option 2: Local Development
```bash
# From the repo root (`llm_family_doctor/`)
conda create -n familydoc python=3.11 -y         # or any ≥3.9
conda activate familydoc

# Install dependencies
pip install -r requirements.txt

# Copy environment template and add your API keys
cp env.template .env          # then open .env and paste your keys

# Set up local directories
make local-setup

# Add PDF files to data/raw_pdfs/
# Then run the data preparation pipeline:
make local-update

# Start Redis cache (optional but recommended for production)
make redis-start

# Start the app (it will build the index automatically on first run)
make start-streamlit
```

## 📊 Data Preparation Pipeline

### 1. Ingest PDF Protocols
Convert clinical protocol PDFs to markdown format:

```bash
# Single file
python scripts/ingest_protocol.py data/raw_pdfs/example.pdf

# All PDFs in directory (non-recursive)
python scripts/ingest_protocol.py --dir data/raw_pdfs

# All PDFs including subdirectories
python scripts/ingest_protocol.py --dir data/raw_pdfs --recursive
```

### 2. Start the App
The app automatically builds the index on first run:

```bash
streamlit run app.py
```

**Note**: The app will automatically:
- Check if protocols exist
- Build the FAISS index if missing
- Show progress messages during index building
- Handle all setup automatically

### 3. Test the Index (Optional)
For comprehensive testing of the vector database:

```bash
python tests/test_index.py
```

## 🧪 Testing Your Index

### Automated Testing
The `tests/test_index.py` script provides:
- ✅ Component loading verification
- 🔍 Search functionality testing
- 📊 Index statistics and diagnostics
- 🎯 Interactive search mode
- 📈 Performance metrics

### Manual Testing in Notebook
Use the enhanced notebook `notebooks/data_prep.ipynb` for:
- Interactive data exploration
- Query testing with various medical terms
- Index statistics and visualization
- Step-by-step pipeline execution

### Test Queries
The system includes pre-configured test queries for common medical conditions:
- головний біль в скроневій ділянці
- кашель температура
- біль в животі
- гіпертонія артеріальний тиск
- діабет цукровий діабет
- And many more...

## 🤖 Automatic Index Building

The Streamlit app automatically handles index building on first startup:

- ✅ **No manual setup required** - Just run `streamlit run app.py`
- ✅ **Progress feedback** - Shows building status with user-friendly messages
- ✅ **Error handling** - Clear error messages if something goes wrong
- ✅ **One-time only** - Index is built once and reused on subsequent runs
- ✅ **Protocol validation** - Checks if protocols exist before building

### How it works:
1. App checks if `data/faiss_index` and `data/doc_map.pkl` exist
2. If missing, validates that `data/protocols/*.md` files are present
3. Downloads the embedding model and builds the index
4. Shows progress messages during the process
5. Saves the index for future use

## 🚀 LangChain & LangSmith Integration

This project now supports **LangChain** and **LangSmith** for enhanced RAG capabilities and monitoring:

### Features:
- **LangChain RAG Pipeline**: Structured retrieval and generation using LangChain components
- **LangSmith Tracing**: Monitor and debug your RAG pipeline in real-time
- **Enhanced Vector Store**: Better document handling with metadata

### Components:
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

## 🔄 Caching System

The application implements a multi-layer caching system for optimal performance:

### Cache Layers:
1. **Exact Cache (Redis)**: SHA-256 hash of `gender|age|symptoms` → markdown answer
2. **Semantic Cache (FAISS)**: In-memory index of approved doctor answers
3. **Database Cache**: Approved answers stored in SQLite

### Cache Flow:
1. Check exact cache first (fastest)
2. Check semantic cache for similar symptoms
3. Check database for approved answers
4. Generate new answer via RAG if no cache hit

### Setup Redis Cache:
```bash
# Start Redis container
make redis-start

# Stop Redis container
make redis-stop

# Environment variables (optional)
REDIS_URL=redis://localhost:6379/0
REDIS_TTL_DAYS=30
```

### Benefits:
- **Performance**: Sub-second response times for cached queries
- **Cost Reduction**: Fewer LLM API calls
- **Consistency**: Approved answers are reused
- **Scalability**: Redis handles high concurrent load



## 📁 Project Structure

```
llm_family_doctor/
├── app.py                          # Streamlit application (handles index building)
├── requirements.txt                # Python dependencies
├── env.template                    # Environment variables template
├── data/
│   ├── raw_pdfs/                  # Input PDF files
│   ├── protocols/                 # Converted markdown files
│   ├── faiss_index               # FAISS vector index (auto-built)
│   └── doc_map.pkl               # Document mapping (auto-built)
├── notebooks/
│   └── data_prep.ipynb           # Enhanced notebook with testing
├── scripts/
│   └── ingest_protocol.py        # PDF to markdown converter
├── src/
│   ├── api/                      # FastAPI routers
│   ├── cache/                    # Redis and semantic caching
│   ├── config/                   # Configuration settings
│   ├── db/                       # Database models and migrations
│   ├── indexing/                 # Index building utilities
│   ├── models/                   # LLM and vector store models
│   └── utils/                    # Utility functions
├── .github/workflows/            # GitHub Actions
└── tests/
    ├── test_index.py             # Comprehensive index testing
    ├── test_cache.py             # Cache functionality testing
    ├── debug_vector_store.py     # Debug utilities
    └── test_langchain_integration.py
```

## 🔧 Environment Setup

```bash
# Create conda environment (optional but recommended)
conda create -n familydoc python=3.11 -y
conda activate familydoc

# Install dependencies
pip install -r requirements.txt

# Copy environment template and add your API keys
cp env.template .env
# Edit .env file with your OpenAI API key

# Create data directories (optional - app will create them if needed)
mkdir -p data/raw_pdfs data/protocols logs
```

## 🎯 Usage Examples

### Basic Workflow
1. **Add PDFs**: Place clinical protocol PDFs in `data/raw_pdfs/`
2. **Convert**: Run `python scripts/ingest_protocol.py --dir data/raw_pdfs --recursive`
3. **Start App**: Run `streamlit run app.py` (index builds automatically on first run)
4. **Test** (Optional): Run `python tests/test_index.py` for comprehensive testing

### Advanced Testing
```bash
# Run comprehensive tests
python tests/test_index.py

# Debug vector store issues
python tests/debug_vector_store.py

# Test LangChain integration
python tests/test_langchain_integration.py
```

## 🐛 Troubleshooting

### Common Issues
1. **Missing dependencies**: Run `pip install -r requirements.txt`
2. **Index not found**: The app builds the index automatically on first run
3. **Low search quality**: Check if your PDFs contain relevant medical content
4. **Memory issues**: Use smaller batch sizes in `src/indexing/build_index.py`

### Debug Tools
- `tests/debug_vector_store.py` - Diagnose index issues
- `tests/test_index.py` - Comprehensive testing
- Enhanced notebook with step-by-step debugging

## 📈 Performance Tips

1. **Model Selection**: `intfloat/multilingual-e5-base` provides good balance of speed and quality
2. **Batch Processing**: Adjust `BATCH_SIZE` in `build_index.py` based on your hardware
3. **Index Optimization**: Consider using `IndexIVFFlat` for large datasets
4. **Memory Management**: Use `faiss-cpu` for CPU-only environments

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.
