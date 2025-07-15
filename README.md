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

# Setup environment and install dependencies
python scripts/setup_environment.py

# Copy environment template and add your API keys
cp env.template .env          # then open .env and paste your keys

# Add PDF files to data/raw_pdfs/
# Then run the data preparation pipeline:
python scripts/ingest_protocol.py --dir data/raw_pdfs --recursive
python src/indexing/build_index.py

# Test the index
python tests/test_index.py
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

### 2. Build Vector Index
Create FAISS index from markdown protocols:

```bash
python src/indexing/build_index.py --hf-model intfloat/multilingual-e5-base
```

### 3. Test the Index
Comprehensive testing of the vector database:

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

## 📁 Project Structure

```
llm_family_doctor/
├── app.py                          # Streamlit application
├── requirements.txt                # Python dependencies
├── env.template                    # Environment variables template
├── data/
│   ├── raw_pdfs/                  # Input PDF files
│   ├── protocols/                 # Converted markdown files
│   ├── faiss_index               # FAISS vector index
│   └── doc_map.pkl               # Document mapping
├── notebooks/
│   └── data_prep.ipynb           # Enhanced notebook with testing
├── scripts/
│   ├── ingest_protocol.py        # PDF to markdown converter
│   ├── setup_environment.py      # Environment setup script
│   └── build_index.py            # Index building script
├── src/
│   ├── config/                   # Configuration settings
│   ├── indexing/                 # Index building utilities
│   ├── models/                   # LLM and vector store models
│   └── utils/                    # Utility functions
└── tests/
    ├── test_index.py             # Comprehensive index testing
    ├── debug_vector_store.py     # Debug utilities
    └── test_langchain_integration.py
```

## 🔧 Environment Setup

### Automatic Setup
```bash
python scripts/setup_environment.py
```

### Manual Setup
```bash
# Create conda environment
conda create -n familydoc python=3.11 -y
conda activate familydoc

# Install dependencies
pip install -r requirements.txt

# Create necessary directories
mkdir -p data/raw_pdfs data/protocols logs tests

# Copy environment template
cp env.template .env
```

## 🎯 Usage Examples

### Basic Workflow
1. **Add PDFs**: Place clinical protocol PDFs in `data/raw_pdfs/`
2. **Convert**: Run `python scripts/ingest_protocol.py --dir data/raw_pdfs --recursive`
3. **Index**: Run `python src/indexing/build_index.py`
4. **Test**: Run `python tests/test_index.py`
5. **Use**: Start the Streamlit app with `streamlit run app.py`

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
1. **Missing dependencies**: Run `python scripts/setup_environment.py`
2. **Index not found**: Ensure you've run the indexing pipeline
3. **Low search quality**: Check if your PDFs contain relevant medical content
4. **Memory issues**: Use smaller batch sizes in `build_index.py`

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
