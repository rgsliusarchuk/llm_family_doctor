# LLM Family Doctor - Startup Guide

This project now has two separate ways to run:

## 🚀 Quick Start

### 1. Streamlit App (Web Interface)

To run the web interface:

```bash
# Option 1: Using startup script
python start_streamlit.py

# Option 2: Direct launch
streamlit run streamlit_app.py

# Option 3: With parameters
streamlit run streamlit_app.py --server.port 8501 --server.address 0.0.0.0
```

🌐 **Available at:** http://localhost:8501

### 2. API Server (For Telegram Bot)

To run the API server:

```bash
# Option 1: Using startup script
python start_api_server.py

# Option 2: Direct launch
python api_server.py

# Option 3: With uvicorn
uvicorn api_server:app --host 0.0.0.0 --port 8000 --reload
```

🌐 **API available at:** http://localhost:8000
📚 **API Documentation:** http://localhost:8000/docs

### 3. Telegram Bot (Additional)

To run the Telegram bot:

```bash
python telegram_bot_example.py
```

## 📋 Available API Endpoints

### Main endpoints:

- `GET /` - API information
- `GET /health` - Service health check
- `POST /diagnose` - Generate diagnosis
- `POST /feedback` - Send feedback
- `GET /protocols` - List of available protocols

### API Usage Example:

```bash
# Generate diagnosis
curl -X POST "http://localhost:8000/diagnose" \
  -H "Content-Type: application/json" \
  -d '{
    "symptoms": "sore throat, temperature 38°C, cough for 3 days",
    "user_id": "12345",
    "chat_id": "67890",
    "top_k": 3
  }'

# Health check
curl "http://localhost:8000/health"
```

## 🔧 Configuration

### Environment variables (.env):

```bash
# For API server
API_BASE_URL=http://localhost:8000

# For Telegram bot
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
API_BASE_URL=http://localhost:8000

# Other settings (already existing)
OPENAI_API_KEY=your_openai_api_key
MODEL_ID=your_model_id
INDEX_PATH=path/to/index
MAP_PATH=path/to/map
```

## 📁 File Structure

```
llm_family_doctor/
├── app.py                    # Original file (can be deleted)
├── streamlit_app.py          # 🆕 Streamlit app
├── api_server.py             # 🆕 API server
├── telegram_bot_example.py   # 🆕 Telegram bot example
├── start_streamlit.py        # 🆕 Streamlit startup script
├── start_api_server.py       # 🆕 API server startup script
├── requirements.txt          # Updated dependencies
└── STARTUP_GUIDE.md          # 🆕 This file
```

## 🚀 Recommended Launch Order

1. **First, start the API server:**
   ```bash
   python start_api_server.py
   ```

2. **Then start Streamlit (in a separate terminal):**
   ```bash
   python start_streamlit.py
   ```

3. **Optionally start the Telegram bot (in a third terminal):**
   ```bash
   python telegram_bot_example.py
   ```

## 🔍 Logging

- **API server:** `logs/api_server.log`
- **Telegram bot:** Console + log files
- **Streamlit:** Console

## ⚠️ Important Notes

1. **API server must be running** before using the Telegram bot
2. **Make sure the index is built** before starting any service
3. **Telegram bot requires a token** from @BotFather
4. **All services use the same models** and indexes

## 🛠️ Development

For development, I recommend using:

```bash
# Terminal 1: API server with auto-reload
uvicorn api_server:app --reload --port 8000

# Terminal 2: Streamlit with auto-reload
streamlit run streamlit_app.py --server.runOnSave true
```

## 📞 Support

If you encounter problems:

1. Check if all dependencies are installed: `pip install -r requirements.txt`
2. Check if the `.env` file is properly configured
3. Check logs in the `logs/` folder
4. Make sure the index is built: `python scripts/ingest_protocol.py` 