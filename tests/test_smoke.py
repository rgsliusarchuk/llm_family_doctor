#!/usr/bin/env python3
"""Smoke tests for CI/CD pipeline."""

import pytest
import requests
import os
import time

@pytest.mark.ci
def test_health_endpoint():
    """Test that the health endpoint returns 200."""
    base_url = os.getenv("API_BASE", "http://localhost")
    
    max_retries = 30
    for i in range(max_retries):
        try:
            response = requests.get(f"{base_url}/health", timeout=5)
            if response.status_code == 200:
                assert response.status_code == 200
                data = response.json()
                assert "status" in data
                assert data["status"] == "healthy"
                return
            else:
                print(f"⚠️  API returned status {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"⏳ Waiting for API to start... ({i+1}/{max_retries})")
            time.sleep(2)
    
    pytest.fail("Health endpoint failed after maximum retries")

@pytest.mark.ci
def test_api_docs():
    """Test that API documentation is accessible."""
    base_url = os.getenv("API_BASE", "http://localhost")
    
    try:
        response = requests.get(f"{base_url}/docs", timeout=5)
        assert response.status_code == 200
        assert "text/html" in response.headers.get("content-type", "")
    except requests.exceptions.RequestException as e:
        pytest.fail(f"API docs not accessible: {e}")

@pytest.mark.ci
def test_openapi_schema():
    """Test that OpenAPI schema is accessible."""
    base_url = os.getenv("API_BASE", "http://localhost")
    
    try:
        response = requests.get(f"{base_url}/openapi.json", timeout=5)
        assert response.status_code == 200
        data = response.json()
        assert "openapi" in data
        assert "info" in data
    except requests.exceptions.RequestException as e:
        pytest.fail(f"OpenAPI schema not accessible: {e}")

@pytest.mark.ci
def test_reverse_proxy():
    """Test that reverse proxy is responding."""
    base_url = os.getenv("API_BASE", "http://localhost")
    
    try:
        response = requests.get(base_url, timeout=5)
        # 404 is expected for root path without specific route
        assert response.status_code in [200, 404]
    except requests.exceptions.RequestException as e:
        pytest.fail(f"Reverse proxy not accessible: {e}")

if __name__ == "__main__":
    # Allow running directly for manual testing
    import sys
    
    def run_test(test_func):
        try:
            test_func()
            print(f"✅ {test_func.__name__} passed")
            return True
        except Exception as e:
            print(f"❌ {test_func.__name__} failed: {e}")
            return False
    
    tests = [
        test_reverse_proxy,
        test_health_endpoint,
        test_api_docs,
        test_openapi_schema
    ]
    
    passed = 0
    for test in tests:
        if run_test(test):
            passed += 1
    
    print(f"\n🎯 {passed}/{len(tests)} tests passed")
    sys.exit(0 if passed == len(tests) else 1) 