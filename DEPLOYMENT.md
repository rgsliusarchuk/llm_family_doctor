# Simple Deployment Guide

This project is designed to be simple to deploy. The app handles index building automatically, so you don't need complex setup scripts.

## Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Set Up Environment
```bash
cp env.template .env
# Edit .env with your OpenAI API key
```

### 3. Start the App
```bash
streamlit run app.py
```

That's it! The app will automatically build the index on first run if needed.

## Deployment Options

### Option 1: Pre-built Index (Production)
**Best for:** Production deployments, Docker containers

1. **Build index locally first:**
   ```bash
   # Add PDFs and convert to markdown
   python scripts/ingest_protocol.py --dir data/raw_pdfs --recursive
   
   # Build the index
   python src/indexing/build_index.py
   ```

2. **Include these files in deployment:**
   - `data/faiss_index`
   - `data/doc_map.pkl`
   - `data/protocols/`

3. **Deploy and run:**
   ```bash
   pip install -r requirements.txt
   cp env.template .env  # add your API key
   streamlit run app.py
   ```

### Option 2: Auto-build Index (Development)
**Best for:** Development, testing, simple deployments

1. **Deploy with protocols only:**
   - Include `data/protocols/*.md` files
   - Don't include pre-built index files

2. **Start the app:**
   ```bash
   pip install -r requirements.txt
   cp env.template .env  # add your API key
   streamlit run app.py
   ```

3. **Wait for index building** (first startup only)

## Environment Variables

Required:
```bash
OPENAI_API_KEY=your_openai_key_here
```

Optional (have sensible defaults):
```bash
MODEL_ID=intfloat/multilingual-e5-base
INDEX_PATH=data/faiss_index
MAP_PATH=data/doc_map.pkl
```

## Docker Example

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
RUN cp env.template .env
# Edit .env with your API key

EXPOSE 8501
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

## Streamlit Cloud

1. **Connect your repository**
2. **Set environment variables** in the Streamlit Cloud dashboard
3. **Deploy** - the app handles everything else automatically

## Troubleshooting

### Index Building Issues
- Check if protocols exist: `ls data/protocols/*.md`
- Verify internet connection (for model download)
- Check disk space

### Slow Startup
- Use pre-built index files for production
- Consider smaller embedding model

### Memory Issues
- Reduce batch size in `src/indexing/build_index.py`
- Use `faiss-cpu` instead of `faiss-gpu`

## Why This Approach?

✅ **Simple**: Standard Python workflow  
✅ **Reliable**: No custom scripts to maintain  
✅ **Flexible**: Works in any environment  
✅ **Self-contained**: App handles its own setup  

The app is designed to "just work" without complex setup procedures. 