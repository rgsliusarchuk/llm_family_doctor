#!/usr/bin/env python3
"""Test script to verify deployment works correctly."""

import requests
import time
import sys
from pathlib import Path

def test_api_health():
    """Test API health endpoint."""
    print("🔍 Testing API health endpoint...")
    
    max_retries = 30
    for i in range(max_retries):
        try:
            response = requests.get("http://localhost:8000/health", timeout=5)
            if response.status_code == 200:
                print("✅ API health check passed!")
                return True
            else:
                print(f"⚠️  API returned status {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"⏳ Waiting for API to start... ({i+1}/{max_retries})")
            time.sleep(2)
    
    print("❌ API health check failed after maximum retries")
    return False

def test_streamlit():
    """Test Streamlit endpoint."""
    print("🔍 Testing Streamlit endpoint...")
    
    try:
        response = requests.get("http://localhost:8501", timeout=5)
        if response.status_code == 200:
            print("✅ Streamlit endpoint accessible!")
            return True
        else:
            print(f"⚠️  Streamlit returned status {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Streamlit endpoint not accessible: {e}")
        return False

def main():
    """Run all deployment tests."""
    print("🚀 Testing LLM Family Doctor Deployment")
    print("=" * 50)
    
    # Test API
    api_ok = test_api_health()
    
    # Test Streamlit
    streamlit_ok = test_streamlit()
    
    print("\n" + "=" * 50)
    if api_ok and streamlit_ok:
        print("🎉 All tests passed! Deployment is working correctly.")
        print("\n📱 Access your applications:")
        print("   - API: http://localhost:8000")
        print("   - API Docs: http://localhost:8000/docs")
        print("   - Streamlit: http://localhost:8501")
        return 0
    else:
        print("❌ Some tests failed. Check the logs above.")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 