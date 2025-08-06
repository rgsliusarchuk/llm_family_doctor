#!/usr/bin/env python
"""Test intent classification functionality."""
import os
import sys
from pathlib import Path

# Add src to Python path for imports
sys.path.append(str(Path(__file__).parent.parent / "src"))

# Disable tokenizers parallelism to avoid warnings
os.environ["TOKENIZERS_PARALLELISM"] = "false"

import pytest
from src.models.intent_classifier import classify_intent, IntentEnum, _chain


class TestIntentClassifier:
    """Test cases for intent classification."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test environment."""
        # Ensure we're in the right directory for imports
        os.chdir(Path(__file__).parent.parent)
    
    def test_clinic_info_queries(self):
        """Test that clinic-related queries are classified as clinic_info."""
        clinic_queries = [
            "Який графік роботи клініки?",
            "Де знаходиться ваша клініка?",
            "Який у вас номер телефону та години роботи?",
        ]
        
        for query in clinic_queries:
            result = classify_intent(query)
            assert result == IntentEnum.clinic_info, f"Expected clinic_info for: {query}"
    
    def test_doctor_schedule_queries(self):
        """Test that doctor schedule queries are classified as doctor_schedule."""
        doctor_queries = [
            "Коли приймає доктор Іваненко?",
            "Графік роботи лікаря 12?",
        ]
        
        for query in doctor_queries:
            result = classify_intent(query)
            assert result == IntentEnum.doctor_schedule, f"Expected doctor_schedule for: {query}"
    
    def test_diagnose_queries(self):
        """Test that medical diagnosis queries are classified as diagnose."""
        diagnose_queries = [
            "У мене два дні температура 38 і кашель.",
            "Моєму сину 5 років, болить живіт.",
        ]
        
        for query in diagnose_queries:
            result = classify_intent(query)
            assert result == IntentEnum.diagnose, f"Expected diagnose for: {query}"
    
    def test_raw_llm_responses(self):
        """Test that raw LLM responses are properly parsed."""
        test_cases = [
            ("Який графік роботи клініки?", IntentEnum.clinic_info),
            ("Коли приймає доктор Іваненко?", IntentEnum.doctor_schedule),
            ("У мене два дні температура 38 і кашель.", IntentEnum.diagnose),
        ]
        
        for query, expected in test_cases:
            # Get raw LLM response for debugging
            raw_response = _chain.invoke({"text": query})
            
            # Verify the response is not empty
            assert raw_response is not None, f"Raw response should not be None for: {query}"
            
            # Verify the classification works
            result = classify_intent(query)
            assert result == expected, f"Expected {expected} for: {query}"
    
    def test_intent_classification_edge_cases(self):
        """Test edge cases and potential error conditions."""
        # Test empty string
        with pytest.raises(Exception):
            classify_intent("")
        
        # Test very long input
        long_input = "У мене дуже довгий опис симптомів " * 50
        result = classify_intent(long_input)
        assert result in [IntentEnum.clinic_info, IntentEnum.doctor_schedule, IntentEnum.diagnose]
    
    def test_all_intent_types_covered(self):
        """Test that all intent types are properly handled."""
        test_cases = [
            ("клініка", IntentEnum.clinic_info),
            ("доктор", IntentEnum.doctor_schedule),
            ("лікар", IntentEnum.doctor_schedule),
            ("температура", IntentEnum.diagnose),
            ("болить", IntentEnum.diagnose),
        ]
        
        for keyword, expected in test_cases:
            result = classify_intent(f"Тест з ключовим словом: {keyword}")
            assert result == expected, f"Expected {expected} for keyword: {keyword}"


if __name__ == "__main__":
    # Allow running as standalone script for debugging
    pytest.main([__file__, "-v", "-s"]) 