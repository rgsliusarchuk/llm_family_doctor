#!/usr/bin/env python3
"""Test script to verify deployment works correctly."""

import requests
import time
import sys
import os
from pathlib import Path

def test_api_health(base_url="http://localhost"):
    """Test API health endpoint."""
    print(f"🔍 Testing API health endpoint at {base_url}...")
    
    max_retries = 30
    for i in range(max_retries):
        try:
            response = requests.get(f"{base_url}/health", timeout=5)
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

def test_streamlit(base_url="http://localhost:8501"):
    """Test Streamlit endpoint."""
    print(f"🔍 Testing Streamlit endpoint at {base_url}...")
    
    try:
        response = requests.get(base_url, timeout=5)
        if response.status_code == 200:
            print("✅ Streamlit endpoint accessible!")
            return True
        else:
            print(f"⚠️  Streamlit returned status {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Streamlit endpoint not accessible: {e}")
        return False

def test_reverse_proxy(base_url="http://localhost"):
    """Test reverse proxy configuration."""
    print(f"🔍 Testing reverse proxy at {base_url}...")
    
    try:
        # Test if Traefik is responding
        response = requests.get(base_url, timeout=5)
        if response.status_code in [200, 404]:  # 404 is expected for root path
            print("✅ Reverse proxy is responding!")
            return True
        else:
            print(f"⚠️  Reverse proxy returned status {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Reverse proxy not accessible: {e}")
        return False

def main():
    """Run all deployment tests."""
    print("🚀 Testing LLM Family Doctor Deployment")
    print("=" * 50)
    
    # Get base URL from environment or use default
    api_base = os.getenv("API_BASE", "http://localhost")
    
    # Test reverse proxy
    proxy_ok = test_reverse_proxy(api_base)
    
    # Test API through reverse proxy
    api_ok = test_api_health(api_base)
    
    # Test Streamlit (direct access for now)
    streamlit_ok = test_streamlit()
    
    print("\n" + "=" * 50)
    if proxy_ok and api_ok and streamlit_ok:
        print("🎉 All tests passed! Deployment is working correctly.")
        print(f"\n📱 Access your applications:")
        print(f"   - API: {api_base}")
        print(f"   - API Docs: {api_base}/docs")
        print("   - Streamlit: http://localhost:8501")
        return 0
    else:
        print("❌ Some tests failed. Check the logs above.")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 