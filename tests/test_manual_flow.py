#!/usr/bin/env python
"""Manual test script to demonstrate knowledge base flow."""

import requests
import json
import time

# Configuration
API_BASE_URL = "http://localhost:8000"

def test_manual_flow():
    """Manual test of the knowledge base flow."""
    
    print("🧪 Manual Knowledge Base Flow Test")
    print("=" * 50)
    
    # Step 1: First patient (Patient A) - with gender info
    print("\n📋 Step 1: Patient A asks for diagnosis")
    print("-" * 40)
    
    patient_a_request = {
        "text": "Я чоловік, мені 25 років. У мене головний біль і температура 38 градусів",
        "user_id": "patient_a",
        "chat_id": "chat_a"
    }
    
    print(f"Patient A: {patient_a_request['text']}")
    
    response = requests.post(f"{API_BASE_URL}/assistant/message", json=patient_a_request)
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Response: {result.get('message', '')[:100]}...")
        
        # Get symptoms hash
        symptoms_hash = result.get('data', {}).get('symptoms_hash', '')
        if symptoms_hash:
            print(f"🔑 Symptoms hash: {symptoms_hash[:16]}...")
    else:
        print(f"❌ Error: {response.status_code}")
        return
    
    # Step 2: Simulate doctor approval
    print("\n👨‍⚕️ Step 2: Doctor approves the diagnosis")
    print("-" * 40)
    
    if symptoms_hash:
        approve_request = {"doctor_id": 1}
        response = requests.post(
            f"{API_BASE_URL}/doctor_review/{symptoms_hash}/approve",
            json=approve_request
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Approved: {result.get('message')}")
        else:
            print(f"❌ Approval failed: {response.status_code}")
    
    # Step 3: Second patient with similar symptoms (Patient B) - with gender info
    print("\n📋 Step 3: Patient B asks for similar diagnosis")
    print("-" * 40)
    
    patient_b_request = {
        "text": "Я чоловік, мені 30 років. У мене головний біль, температура 37.5 і легкий кашель",
        "user_id": "patient_b",
        "chat_id": "chat_b"
    }
    
    print(f"Patient B: {patient_b_request['text']}")
    print("(Similar symptoms but with cough and different age)")
    
    response = requests.post(f"{API_BASE_URL}/assistant/message", json=patient_b_request)
    
    if response.status_code == 200:
        result = response.json()
        data = result.get('data', {})
        
        print(f"✅ Response: {result.get('message', '')[:100]}...")
        
        if data.get('cached'):
            print("🎯 RESULT: This was served from cache (similar case found!)")
            print("   → Patient B got a doctor-approved diagnosis instantly!")
        else:
            print("🔄 RESULT: This was a new diagnosis (no similar case found)")
            print("   → Patient B will wait for doctor review")
    else:
        print(f"❌ Error: {response.status_code}")
    
    # Step 4: Check knowledge base
    print("\n📚 Step 4: Check knowledge base")
    print("-" * 40)
    
    response = requests.get(f"{API_BASE_URL}/knowledge-base/")
    if response.status_code == 200:
        stats = response.json()
        print(f"📊 Knowledge Base Stats:")
        print(f"   Total entries: {stats.get('total_entries', 0)}")
        print(f"   Approved entries: {stats.get('approved_entries', 0)}")
        print(f"   Total doctors: {stats.get('total_doctors', 0)}")
    else:
        print(f"❌ Error getting stats: {response.status_code}")

def test_semantic_search():
    """Test semantic search functionality."""
    
    print("\n🔍 Testing Semantic Search")
    print("=" * 50)
    
    # Test different symptom variations
    test_queries = [
        "headache fever",
        "головний біль температура",
        "лихоманка головний біль",
        "температура 38 головний біль"
    ]
    
    for query in test_queries:
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

def test_exact_match():
    """Test exact match scenario."""
    
    print("\n🎯 Testing Exact Match Scenario")
    print("=" * 50)
    
    # Step 1: First patient with exact symptoms
    print("\n📋 Step 1: Patient A with exact symptoms")
    print("-" * 40)
    
    patient_a_request = {
        "text": "Я чоловік, мені 25 років. У мене головний біль і температура 38 градусів",
        "user_id": "patient_a_exact",
        "chat_id": "chat_a_exact"
    }
    
    print(f"Patient A: {patient_a_request['text']}")
    
    response = requests.post(f"{API_BASE_URL}/assistant/message", json=patient_a_request)
    
    if response.status_code == 200:
        result = response.json()
        symptoms_hash = result.get('data', {}).get('symptoms_hash', '')
        print(f"✅ Response: {result.get('message', '')[:100]}...")
        print(f"🔑 Symptoms hash: {symptoms_hash[:16]}...")
        
        # Approve the diagnosis
        if symptoms_hash:
            approve_request = {"doctor_id": 1}
            response = requests.post(
                f"{API_BASE_URL}/doctor_review/{symptoms_hash}/approve",
                json=approve_request
            )
            if response.status_code == 200:
                print("✅ Diagnosis approved")
        
        # Step 2: Second patient with EXACT same symptoms
        print("\n📋 Step 2: Patient B with EXACT same symptoms")
        print("-" * 40)
        
        patient_b_request = {
            "text": "Я чоловік, мені 25 років. У мене головний біль і температура 38 градусів",
            "user_id": "patient_b_exact",
            "chat_id": "chat_b_exact"
        }
        
        print(f"Patient B: {patient_b_request['text']}")
        print("(EXACT same symptoms as Patient A)")
        
        response = requests.post(f"{API_BASE_URL}/assistant/message", json=patient_b_request)
        
        if response.status_code == 200:
            result = response.json()
            data = result.get('data', {})
            
            print(f"✅ Response: {result.get('message', '')[:100]}...")
            
            if data.get('cached'):
                print("🎯 RESULT: This was served from cache (EXACT match found!)")
                print("   → Patient B got the exact same doctor-approved diagnosis!")
            else:
                print("🔄 RESULT: This was a new diagnosis (no exact match found)")
        else:
            print(f"❌ Error: {response.status_code}")

if __name__ == "__main__":
    print("🚀 Starting Manual Knowledge Base Test")
    print(f"API URL: {API_BASE_URL}")
    print("Make sure the API server is running!")
    print("=" * 60)
    
    try:
        # Test the main flow
        test_manual_flow()
        
        # Test exact match scenario
        test_exact_match()
        
        # Test semantic search
        test_semantic_search()
        
        print("\n✅ Manual test completed!")
        print("\n💡 What to look for:")
        print("   • Patient A: Should get 'being reviewed' message")
        print("   • After approval: Should be saved to knowledge base")
        print("   • Patient B: Should get cached response if similar enough")
        print("   • Knowledge base: Should show the approved entry")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc() 