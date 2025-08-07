#!/usr/bin/env python3
"""
Debug script for testing cache functionality.
This script tests the cache modules without requiring Redis to be running.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_redis_cache_imports():
    """Test that Redis cache module can be imported."""
    try:
        from src.cache.redis_cache import get_md, set_md
        print("✅ Redis cache imports successfully")
        return True
    except Exception as e:
        print(f"❌ Redis cache import failed: {e}")
        return False

def test_semantic_cache_imports():
    """Test that semantic cache module can be imported."""
    try:
        from src.cache.doctor_semantic_index import semantic_lookup
        print("✅ Semantic cache imports successfully")
        return True
    except Exception as e:
        print(f"❌ Semantic cache import failed: {e}")
        return False

def test_router_imports():
    """Test that the diagnose router can be imported with cache dependencies."""
    try:
        from src.api.router_diagnose import router
        print("✅ Diagnose router imports successfully with cache dependencies")
        return True
    except Exception as e:
        print(f"❌ Diagnose router import failed: {e}")
        return False

def test_cache_functionality():
    """Test cache functionality with mocked Redis."""
    try:
        from unittest.mock import patch, MagicMock
        from src.cache.redis_cache import get_md, set_md
        
        # Mock Redis
        with patch('src.cache.redis_cache._r') as mock_redis:
            # Test get_md
            mock_redis.get.return_value = "Test diagnosis"
            result = get_md("test_hash")
            assert result == "Test diagnosis"
            
            # Test set_md
            set_md("test_hash", "Test diagnosis")
            mock_redis.set.assert_called_once()
            
        print("✅ Cache functionality works with mocked Redis")
        return True
    except Exception as e:
        print(f"❌ Cache functionality test failed: {e}")
        return False

def main():
    """Run all cache tests."""
    print("🔍 Testing Cache Functionality")
    print("=" * 40)
    
    tests = [
        ("Redis Cache Imports", test_redis_cache_imports),
        ("Semantic Cache Imports", test_semantic_cache_imports),
        ("Router Imports", test_router_imports),
        ("Cache Functionality", test_cache_functionality),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🧪 {test_name}...")
        if test_func():
            passed += 1
    
    print(f"\n📊 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All cache tests passed!")
        return 0
    else:
        print("❌ Some tests failed. Check the output above.")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 