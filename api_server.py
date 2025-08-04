#!/usr/bin/env python
"""FastAPI server for LLM Family Doctor API."""
from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging
from datetime import datetime

# Add current directory to Python path for imports
sys.path.append(str(Path(__file__).parent))

# Disable tokenizers parallelism to avoid warnings in multiprocessing
os.environ["TOKENIZERS_PARALLELISM"] = "false"

# --------------- routers ----------------
from src.api import clinic_router, doctors_router

# Lifespan helper
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn

from src.config import settings

# ── Logging setup ────────────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ── Lifespan (startup / shutdown) ────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Runs once on startup (before yield) and once on shutdown (after)."""
    logger.info("Starting API server…")
    initialize_models()          # <── your original startup logic
    yield                        # ── app runs between these two lines
    logger.info("API shutting down — bye!")

# ── FastAPI app ──────────────────────────────────────────────────────────────
app = FastAPI(
    title="LLM Family Doctor API",
    description="API for generating medical diagnoses using RAG with Ukrainian medical protocols",
    version="1.0.0",
    lifespan=lifespan,           # <── new lifespan
)

# Routers
app.include_router(clinic_router)
app.include_router(doctors_router)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Pydantic models ──────────────────────────────────────────────────────────
class DiagnosisRequest(BaseModel):
    symptoms: str = Field(..., description="Опис симптомів пацієнта")
    user_id: Optional[str] = Field(None, description="ID користувача (для Telegram)")
    chat_id: Optional[str] = Field(None, description="ID чату (для Telegram)")
    top_k: int = Field(3, description="Кількість протоколів для пошуку")

class DiagnosisResponse(BaseModel):
    diagnosis: str = Field(..., description="Попередній діагноз і план лікування")
    protocols_used: List[Dict[str, Any]] = Field(..., description="Використані протоколи")
    request_id: str = Field(..., description="Унікальний ID запиту")

class HealthResponse(BaseModel):
    status: str = Field(..., description="Статус сервісу")
    model_loaded: bool = Field(..., description="Чи завантажена модель")
    index_exists: bool = Field(..., description="Чи існує індекс")

class FeedbackRequest(BaseModel):
    request_id: str = Field(..., description="ID запиту для відгуку")
    status: str = Field(..., description="Статус: approved/rejected/edited")
    edited_diagnosis: Optional[str] = Field(None, description="Відредагований діагноз")

# ── Global state ─────────────────────────────────────────────────────────────
model_loaded = False

# ── Model initialization ─────────────────────────────────────────────────────
def initialize_models():
    """Initialize the RAG model."""
    global model_loaded
    
    try:
        # Check if index exists
        index_path = Path(settings.index_path)
        map_path = Path(settings.map_path)
        
        if not index_path.exists() or not map_path.exists():
            logger.error("Index files not found. Please run the indexing script first.")
            model_loaded = False
            return
        
        # Test LangChain RAG model
        from src.models.rag_chain import generate_rag_response
        # Test the model with a simple query
        test_result = generate_rag_response("тест", top_k=1)
        model_loaded = True
        logger.info("LangChain RAG model loaded successfully")
            
    except Exception as e:
        logger.error(f"Failed to initialize models: {e}")
        model_loaded = False

# ── API endpoints ────────────────────────────────────────────────────────────
# (startup decorator removed — logic now lives in lifespan)

@app.get("/", response_model=Dict[str, str])
async def root():
    """Root endpoint."""
    return {
        "message": "LLM Family Doctor API",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    index_path = Path(settings.index_path)
    map_path = Path(settings.map_path)
    
    return HealthResponse(
        status="healthy" if model_loaded else "unhealthy",
        model_loaded=model_loaded,
        index_exists=index_path.exists() and map_path.exists()
    )

@app.post("/diagnose", response_model=DiagnosisResponse)
async def generate_diagnosis(request: DiagnosisRequest, background_tasks: BackgroundTasks):
    """Generate diagnosis based on symptoms."""
    if not model_loaded:
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    if not request.symptoms.strip():
        raise HTTPException(status_code=400, detail="Symptoms cannot be empty")
    
    try:
        # Generate diagnosis using RAG pipeline
        from src.models.rag_chain import generate_rag_response
        result = generate_rag_response(request.symptoms, top_k=request.top_k)
        answer = result["response"]
        retrieved_docs = result["documents"]
        
        # Prepare response
        protocols_used = []
        for i, doc in enumerate(retrieved_docs, 1):
            protocols_used.append({
                "protocol_id": i,
                "content": doc.page_content,
                "similarity_score": doc.metadata.get("similarity_score", 0.0)
            })
        
        # Generate unique request ID
        import uuid
        request_id = str(uuid.uuid4())
        
        # Log the request for feedback tracking
        background_tasks.add_task(log_diagnosis_request, request_id, request, answer)
        
        return DiagnosisResponse(
            diagnosis=answer,
            protocols_used=protocols_used,
            request_id=request_id
        )
        
    except Exception as e:
        logger.error(f"Error generating diagnosis: {e}")
        raise HTTPException(status_code=500, detail=f"Error generating diagnosis: {str(e)}")

@app.post("/feedback")
async def submit_feedback(feedback: FeedbackRequest):
    """Submit feedback for a diagnosis."""
    try:
        # Log feedback to CSV file
        feedback_log = Path("logs/doctor_feedback.csv")
        feedback_log.parent.mkdir(parents=True, exist_ok=True)
        
        import csv
        with feedback_log.open("a", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow([
                datetime.now().isoformat(),
                feedback.request_id,
                feedback.status,
                feedback.edited_diagnosis or ""
            ])
        
        return {"message": "Feedback submitted successfully"}
        
    except Exception as e:
        logger.error(f"Error submitting feedback: {e}")
        raise HTTPException(status_code=500, detail=f"Error submitting feedback: {str(e)}")

@app.get("/protocols")
async def list_protocols():
    """List available medical protocols."""
    try:
        protocols_dir = Path("data/protocols")
        if not protocols_dir.exists():
            return {"protocols": []}
        
        protocols = []
        for protocol_file in protocols_dir.glob("*.md"):
            protocols.append({
                "filename": protocol_file.name,
                "name": protocol_file.stem.replace("_", " ").title(),
                "size": protocol_file.stat().st_size
            })
        
        return {"protocols": protocols}
        
    except Exception as e:
        logger.error(f"Error listing protocols: {e}")
        raise HTTPException(status_code=500, detail=f"Error listing protocols: {str(e)}")

# ── Background tasks ─────────────────────────────────────────────────────────
def log_diagnosis_request(request_id: str, request: DiagnosisRequest, diagnosis: str):
    """Log diagnosis request for analytics."""
    try:
        log_file = Path("logs/diagnosis_requests.csv")
        log_file.parent.mkdir(parents=True, exist_ok=True)
        
        import csv
        with log_file.open("a", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow([
                datetime.now().isoformat(),
                request_id,
                request.user_id or "",
                request.chat_id or "",
                request.symptoms[:200],  # Truncate for CSV
                diagnosis[:200]  # Truncate for CSV
            ])
            
    except Exception as e:
        logger.error(f"Error logging diagnosis request: {e}")

# ── Main entry point ─────────────────────────────────────────────────────────
if __name__ == "__main__":
    uvicorn.run(
        "api_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    ) 