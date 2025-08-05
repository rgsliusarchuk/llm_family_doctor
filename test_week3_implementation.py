#!/usr/bin/env python
"""Test script for Week 3 implementation."""
import sys
from pathlib import Path

# Add current directory to Python path for imports
sys.path.append(str(Path(__file__).parent))

def test_guardrails():
    """Test guardrails functionality."""
    print("🧪 Testing Guardrails...")
    
    from src.guardrails.llm_guards import guard_input, guard_output, is_input_valid, get_validation_errors
    
    # Test input validation
    test_inputs = [
        "Normal symptoms description",
        "Symptoms with fuck word in it",  # Should be filtered
        "A" * 1500,  # Too long
        "Valid symptoms with shit word"  # Should be filtered
    ]
    
    for i, test_input in enumerate(test_inputs, 1):
        print(f"  Test {i}: {test_input[:50]}...")
        cleaned = guard_input(test_input)
        valid = is_input_valid(test_input)
        errors = get_validation_errors(test_input)
        
        print(f"    Cleaned: {cleaned[:50]}...")
        print(f"    Valid: {valid}")
        print(f"    Errors: {errors}")
        print()
    
    # Test output validation
    test_output = "This is a test diagnosis response."
    guarded_output = guard_output(test_output)
    print(f"  Output test: {guarded_output[:100]}...")
    print()

def test_semantic_index():
    """Test semantic index functionality."""
    print("🧪 Testing Semantic Index...")
    
    from src.cache.doctor_semantic_index import semantic_lookup, add_doc_to_index
    
    # Test adding document
    test_doc = "Test diagnosis document for semantic search"
    try:
        add_doc_to_index(test_doc)
        print("  ✅ add_doc_to_index() works")
    except Exception as e:
        print(f"  ❌ add_doc_to_index() failed: {e}")
    
    # Test semantic lookup
    try:
        result = semantic_lookup("test query")
        print(f"  ✅ semantic_lookup() works, result: {result is not None}")
    except Exception as e:
        print(f"  ❌ semantic_lookup() failed: {e}")
    
    print()

def test_api_routers():
    """Test API router imports."""
    print("🧪 Testing API Routers...")
    
    try:
        from src.api import (
            clinic_router,
            doctors_router,
            diagnose_router,
            doctor_answers_router,
            intake_router,
            doctor_review_router
        )
        print("  ✅ All routers imported successfully")
    except Exception as e:
        print(f"  ❌ Router import failed: {e}")
    
    print()

def test_models():
    """Test database models."""
    print("🧪 Testing Database Models...")
    
    from src.db.models import DoctorAnswer, Doctor, Clinic
    
    # Test model creation
    try:
        doctor = Doctor(
            full_name="Test Doctor",
            position="Test Position",
            schedule="Mon-Fri 09-17"
        )
        print("  ✅ Doctor model works")
        
        answer = DoctorAnswer(
            symptoms_hash="test_hash",
            answer_md="Test answer",
            approved=True,
            doctor_id=1
        )
        print("  ✅ DoctorAnswer model works")
        
    except Exception as e:
        print(f"  ❌ Model creation failed: {e}")
    
    print()

def main():
    """Run all tests."""
    print("🚀 Testing Week 3 Implementation")
    print("=" * 50)
    
    test_guardrails()
    test_semantic_index()
    test_api_routers()
    test_models()
    
    print("✅ All tests completed!")

if __name__ == "__main__":
    main() 