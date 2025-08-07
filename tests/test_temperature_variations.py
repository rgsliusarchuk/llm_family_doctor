#!/usr/bin/env python
"""Test temperature variations in symptoms."""

import requests
import json

# Configuration
API_BASE_URL = "http://localhost:8000"

def test_temperature_variations():
    """Test what happens with small temperature differences."""
    
    print("🌡️ Testing Temperature Variations")
    print("=" * 50)
    
    # Test cases with small temperature differences
    test_cases = [
        {
            "name": "Patient A",
            "text": "Я чоловік, мені 25 років. У мене головний біль і температура 37.2 градусів",
            "user_id": "temp_test_a",
            "chat_id": "temp_test_a"
        },
        {
            "name": "Patient B", 
            "text": "Я чоловік, мені 25 років. У мене головний біль і температура 37.5 градусів",
            "user_id": "temp_test_b",
            "chat_id": "temp_test_b"
        },
        {
            "name": "Patient C",
            "text": "Я чоловік, мені 25 років. У мене головний біль і температура 37.0 градусів",
            "user_id": "temp_test_c",
            "chat_id": "temp_test_c"
        }
    ]
    
    results = []
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📋 Test {i}: {test_case['name']}")
        print("-" * 30)
        print(f"Symptoms: {test_case['text']}")
        
        response = requests.post(
            f"{API_BASE_URL}/assistant/message",
            json=test_case
        )
        
        if response.status_code == 200:
            result = response.json()
            symptoms_hash = result.get('data', {}).get('symptoms_hash', '')
            message = result.get('message', '')[:100] + "..."
            
            print(f"✅ Response: {message}")
            print(f"🔑 Symptoms hash: {symptoms_hash[:16]}...")
            
            results.append({
                "name": test_case['name'],
                "symptoms": test_case['text'],
                "hash": symptoms_hash,
                "hash_short": symptoms_hash[:16]
            })
            
            # Approve the first one to test caching
            if i == 1:
                print("👨‍⚕️ Approving first diagnosis...")
                approve_request = {"doctor_id": 1}
                approve_response = requests.post(
                    f"{API_BASE_URL}/doctor_review/{symptoms_hash}/approve",
                    json=approve_request
                )
                if approve_response.status_code == 200:
                    print("✅ First diagnosis approved and saved to knowledge base")
                else:
                    print(f"❌ Approval failed: {approve_response.status_code}")
        else:
            print(f"❌ Error: {response.status_code}")
    
    # Analyze results
    print("\n📊 Analysis of Temperature Variations")
    print("=" * 50)
    
    print("🔍 Hash Comparison:")
    for i, result in enumerate(results):
        print(f"  {result['name']}: {result['hash_short']}...")
    
    # Check if any hashes are the same
    hashes = [r['hash'] for r in results]
    unique_hashes = set(hashes)
    
    print(f"\n📈 Results:")
    print(f"  Total test cases: {len(results)}")
    print(f"  Unique hashes: {len(unique_hashes)}")
    print(f"  Hash collisions: {len(results) - len(unique_hashes)}")
    
    if len(unique_hashes) == len(results):
        print("  → Each temperature variation generates a different hash")
        print("  → Each will be treated as a separate case")
    else:
        print("  → Some temperature variations generate the same hash")
        print("  → They will be treated as the same case")
    
    # Test if second case hits cache
    print(f"\n🎯 Testing Cache Hit for Patient B:")
    print("-" * 40)
    
    # Test Patient B again to see if it hits cache
    response = requests.post(
        f"{API_BASE_URL}/assistant/message",
        json=test_cases[1]  # Patient B
    )
    
    if response.status_code == 200:
        result = response.json()
        data = result.get('data', {})
        
        if data.get('cached'):
            print("🎯 RESULT: Cache hit! Patient B got cached diagnosis")
        else:
            print("🔄 RESULT: No cache hit - new diagnosis generated")
        
        print(f"Response: {result.get('message', '')[:100]}...")

def test_semantic_similarity():
    """Test semantic similarity for temperature variations."""
    
    print("\n🧠 Testing Semantic Similarity")
    print("=" * 50)
    
    # Test semantic search for similar symptoms
    search_queries = [
        "головний біль температура 37.2",
        "головний біль температура 37.5", 
        "головний біль температура 37.0",
        "головний біль температура"
    ]
    
    for query in search_queries:
        print(f"\n🔍 Searching for: '{query}'")
        
        search_request = {
            "query": query,
            "top_k": 3,
            "min_similarity": 0.8
        }
        
        response = requests.post(
            f"{API_BASE_URL}/knowledge-base/search",
            json=search_request
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"   Found: {result.get('total_found')} results")
            print(f"   Method: {result.get('search_method')}")
        else:
            print(f"   ❌ Error: {response.status_code}")

if __name__ == "__main__":
    print("🚀 Testing Temperature Variations in Symptoms")
    print(f"API URL: {API_BASE_URL}")
    print("=" * 60)
    
    try:
        test_temperature_variations()
        test_semantic_similarity()
        
        print("\n✅ Temperature variation test completed!")
        print("\n💡 What this tells us:")
        print("   • Small temperature differences (37.2 vs 37.5) may generate different hashes")
        print("   • Each variation might be treated as a separate medical case")
        print("   • This ensures medical accuracy but may reduce cache efficiency")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc() 