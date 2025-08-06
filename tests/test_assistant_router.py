#!/usr/bin/env python
"""Unit tests for assistant router."""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient
from sqlmodel import Session

from src.api.router_assistant import (
    router, 
    AssistantRequest, 
    AssistantResponse
)
from src.db.models import Clinic, Doctor
from src.models.intent_classifier import IntentEnum, classify_intent

# ─────────────────────────────────────────────────────────────────────────────
# Test Intent Classification
# ─────────────────────────────────────────────────────────────────────────────

@patch('src.models.intent_classifier._chain')
def test_classify_intent_clinic_info(mock_chain):
    """Test intent classification for clinic info."""
    mock_chain.invoke.return_value = "clinic_info"
    
    result = classify_intent("Where is your clinic located?")
    assert result == IntentEnum.CLINIC_INFO

@patch('src.models.intent_classifier._chain')
def test_classify_intent_doctor_schedule(mock_chain):
    """Test intent classification for doctor schedule."""
    mock_chain.invoke.return_value = "doctor_schedule"
    
    result = classify_intent("When is Dr. Smith available?")
    assert result == IntentEnum.DOCTOR_SCHEDULE

@patch('src.models.intent_classifier._chain')
def test_classify_intent_diagnose(mock_chain):
    """Test intent classification for diagnose."""
    mock_chain.invoke.return_value = "diagnose"
    
    result = classify_intent("I have a headache")
    assert result == IntentEnum.DIAGNOSE

# ─────────────────────────────────────────────────────────────────────────────
# Test Assistant Router Endpoints
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture
def client():
    """Create test client."""
    from fastapi import FastAPI
    app = FastAPI()
    app.include_router(router)
    return TestClient(app)

@pytest.fixture
def mock_session():
    """Create mock database session."""
    session = MagicMock(spec=Session)
    return session

@pytest.fixture
def sample_clinic():
    """Create sample clinic data."""
    return Clinic(
        id=1,
        address="123 Medical St, Kyiv",
        opening_hours="Mon-Fri 08:00-18:00",
        services="General practice, Pediatrics, Emergency care"
    )

@pytest.fixture
def sample_doctor():
    """Create sample doctor data."""
    return Doctor(
        id=1,
        full_name="Dr. Ivan Petrenko",
        position="Family Doctor",
        schedule="Mon-Fri 09:00-17:00"
    )

# ─────────────────────────────────────────────────────────────────────────────
# Test Clinic Info Handler
# ─────────────────────────────────────────────────────────────────────────────

@patch('src.api.router_assistant.classify_intent')
async def test_handle_clinic_info_success(mock_classify, mock_session, sample_clinic):
    """Test successful clinic info request."""
    from src.api.router_assistant import handle_clinic_info
    
    # Mock the database query
    mock_session.exec.return_value.first.return_value = sample_clinic
    
    result = await handle_clinic_info(mock_session)
    
    assert result["address"] == "123 Medical St, Kyiv"
    assert result["opening_hours"] == "Mon-Fri 08:00-18:00"
    assert result["services"] == "General practice, Pediatrics, Emergency care"

@patch('src.api.router_assistant.classify_intent')
async def test_handle_clinic_info_not_found(mock_classify, mock_session):
    """Test clinic info request when clinic not found."""
    from src.api.router_assistant import handle_clinic_info
    from fastapi import HTTPException
    
    # Mock empty database query
    mock_session.exec.return_value.first.return_value = None
    
    with pytest.raises(HTTPException) as exc_info:
        await handle_clinic_info(mock_session)
    
    assert exc_info.value.status_code == 404

# ─────────────────────────────────────────────────────────────────────────────
# Test Doctor Schedule Handler
# ─────────────────────────────────────────────────────────────────────────────

@patch('src.api.router_assistant.classify_intent')
async def test_handle_doctor_schedule_by_id(mock_classify, mock_session, sample_doctor):
    """Test doctor schedule request by ID."""
    from src.api.router_assistant import handle_doctor_schedule
    
    # Mock the database query
    mock_session.exec.return_value.first.return_value = sample_doctor
    
    result = await handle_doctor_schedule("Show me doctor 1 schedule", mock_session)
    
    assert result["full_name"] == "Dr. Ivan Petrenko"
    assert result["position"] == "Family Doctor"
    assert result["schedule"] == "Mon-Fri 09:00-17:00"

@patch('src.api.router_assistant.classify_intent')
async def test_handle_doctor_schedule_by_name(mock_classify, mock_session, sample_doctor):
    """Test doctor schedule request by name."""
    from src.api.router_assistant import handle_doctor_schedule
    
    # Mock the database query - first call returns None (ID not found), second returns doctor
    mock_session.exec.return_value.first.side_effect = [None, sample_doctor]
    
    result = await handle_doctor_schedule("When is Dr. Petrenko available?", mock_session)
    
    assert result["full_name"] == "Dr. Ivan Petrenko"

@patch('src.api.router_assistant.classify_intent')
async def test_handle_doctor_schedule_not_found(mock_classify, mock_session):
    """Test doctor schedule request when doctor not found."""
    from src.api.router_assistant import handle_doctor_schedule
    from fastapi import HTTPException
    
    # Mock empty database query
    mock_session.exec.return_value.first.return_value = None
    
    with pytest.raises(HTTPException) as exc_info:
        await handle_doctor_schedule("Show me doctor 999 schedule", mock_session)
    
    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "doctor_not_found"

# ─────────────────────────────────────────────────────────────────────────────
# Test Diagnose Handler
# ─────────────────────────────────────────────────────────────────────────────

@patch('src.api.router_assistant.classify_intent')
@patch('httpx.AsyncClient')
async def test_handle_diagnose_success(mock_client, mock_classify, mock_session):
    """Test successful diagnosis request."""
    from src.api.router_assistant import handle_diagnose
    
    # Mock the httpx client response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "diagnosis": "Based on your symptoms, you may have a common cold.",
        "cached": False,
        "symptoms_hash": "abc123"
    }
    
    mock_client_instance = MagicMock()
    mock_client_instance.__aenter__.return_value.post.return_value = mock_response
    mock_client.return_value = mock_client_instance
    
    result = await handle_diagnose("I have a headache", "user123", "chat456")
    
    assert result["diagnosis"] == "Based on your symptoms, you may have a common cold."
    assert result["cached"] == False
    assert result["symptoms_hash"] == "abc123"

# ─────────────────────────────────────────────────────────────────────────────
# Test Main Endpoint
# ─────────────────────────────────────────────────────────────────────────────

@patch('src.api.router_assistant.classify_intent')
@patch('src.api.router_assistant.handle_clinic_info')
async def test_assistant_message_clinic_info(mock_handle_clinic, mock_classify, client, sample_clinic):
    """Test assistant message endpoint for clinic info."""
    # Mock intent classification
    mock_classify.return_value = IntentEnum.CLINIC_INFO
    
    # Mock clinic info handler
    mock_handle_clinic.return_value = {
        "address": "123 Medical St, Kyiv",
        "opening_hours": "Mon-Fri 08:00-18:00",
        "services": "General practice, Pediatrics, Emergency care"
    }
    
    # Mock database session
    with patch('src.api.router_assistant.get_session') as mock_get_session:
        mock_session = MagicMock()
        mock_get_session.return_value = mock_session
        
        response = client.post(
            "/assistant/message",
            json={
                "text": "Where is your clinic located?",
                "user_id": "user123",
                "chat_id": "chat456"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["intent"] == "clinic_info"
        assert "address" in data["data"]

@patch('src.api.router_assistant.classify_intent')
@patch('src.api.router_assistant.handle_doctor_schedule')
async def test_assistant_message_doctor_schedule(mock_handle_doctor, mock_classify, client, sample_doctor):
    """Test assistant message endpoint for doctor schedule."""
    # Mock intent classification
    mock_classify.return_value = IntentEnum.DOCTOR_SCHEDULE
    
    # Mock doctor schedule handler
    mock_handle_doctor.return_value = {
        "full_name": "Dr. Ivan Petrenko",
        "position": "Family Doctor",
        "schedule": "Mon-Fri 09:00-17:00"
    }
    
    # Mock database session
    with patch('src.api.router_assistant.get_session') as mock_get_session:
        mock_session = MagicMock()
        mock_get_session.return_value = mock_session
        
        response = client.post(
            "/assistant/message",
            json={
                "text": "When is Dr. Petrenko available?",
                "user_id": "user123",
                "chat_id": "chat456"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["intent"] == "doctor_schedule"
        assert "full_name" in data["data"]

@patch('src.api.router_assistant.classify_intent')
@patch('src.api.router_assistant.handle_diagnose')
async def test_assistant_message_diagnose(mock_handle_diagnose, mock_classify, client):
    """Test assistant message endpoint for diagnose."""
    # Mock intent classification
    mock_classify.return_value = IntentEnum.DIAGNOSE
    
    # Mock diagnose handler
    mock_handle_diagnose.return_value = {
        "diagnosis": "Based on your symptoms, you may have a common cold.",
        "cached": False,
        "symptoms_hash": "abc123"
    }
    
    # Mock database session
    with patch('src.api.router_assistant.get_session') as mock_get_session:
        mock_session = MagicMock()
        mock_get_session.return_value = mock_session
        
        response = client.post(
            "/assistant/message",
            json={
                "text": "I have a headache",
                "user_id": "user123",
                "chat_id": "chat456"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["intent"] == "diagnose"
        assert "diagnosis" in data["data"]
        assert "symptoms_hash" in data["data"]

# ─────────────────────────────────────────────────────────────────────────────
# Test Error Handling
# ─────────────────────────────────────────────────────────────────────────────

@patch('src.api.router_assistant.classify_intent')
async def test_assistant_message_internal_error(mock_classify, client):
    """Test assistant message endpoint with internal error."""
    # Mock intent classification to raise exception
    mock_classify.side_effect = Exception("Test error")
    
    # Mock database session
    with patch('src.api.router_assistant.get_session') as mock_get_session:
        mock_session = MagicMock()
        mock_get_session.return_value = mock_session
        
        response = client.post(
            "/assistant/message",
            json={
                "text": "Test message",
                "user_id": "user123",
                "chat_id": "chat456"
            }
        )
        
        assert response.status_code == 500
        data = response.json()
        assert "Internal server error" in data["detail"] 