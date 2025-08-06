#!/usr/bin/env python
"""Test script to demonstrate knowledge base flow with similar symptoms."""

import sys
import os
import asyncio
import aiohttp
import json
from datetime import datetime

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configuration
API_BASE_URL = "http://localhost:8000"

async def test_knowledge_base_flow():
    """Test the complete knowledge base flow."""
    
    print("🧪 Testing Knowledge Base Flow")
    print("=" * 50)
    
    async with aiohttp.ClientSession() as session:
        
        # Test 1: Generate first diagnosis (will be new)
        print("\n📋 Test 1: Generate first diagnosis (Patient A)")
        print("-" * 40)
        
        patient_a_request = {
            "text": "У мене головний біль і температура 38 градусів",
            "user_id": "patient_a",
            "chat_id": "chat_a"
        }
        
        print(f"Patient A symptoms: {patient_a_request['text']}")
        
        response = await session.post(
            f"{API_BASE_URL}/assistant/message",
            json=patient_a_request
        )
        
        if response.status == 200:
            result = await response.json()
            print(f"✅ Response received")
            print(f"Intent: {result.get('intent')}")
            print(f"Message: {result.get('message', 'No message')[:100]}...")
            
            # Extract symptoms hash if available
            symptoms_hash = result.get('data', {}).get('symptoms_hash', '')
            if symptoms_hash:
                print(f"Symptoms hash: {symptoms_hash[:16]}...")
        else:
            print(f"❌ Error: {response.status}")
            return
        
        # Test 2: Check knowledge base stats
        print("\n📊 Test 2: Check knowledge base stats")
        print("-" * 40)
        
        response = await session.get(f"{API_BASE_URL}/knowledge-base/")
        if response.status == 200:
            stats = await response.json()
            print(f"Total entries: {stats.get('total_entries', 0)}")
            print(f"Approved entries: {stats.get('approved_entries', 0)}")
            print(f"Total doctors: {stats.get('total_doctors', 0)}")
        else:
            print(f"❌ Error getting stats: {response.status}")
        
        # Test 3: Simulate doctor approval (using the review endpoint)
        print("\n👨‍⚕️ Test 3: Simulate doctor approval")
        print("-" * 40)
        
        if symptoms_hash:
            approve_request = {
                "doctor_id": 1
            }
            
            response = await session.post(
                f"{API_BASE_URL}/doctor_review/{symptoms_hash}/approve",
                json=approve_request
            )
            
            if response.status == 200:
                result = await response.json()
                print(f"✅ Diagnosis approved by doctor")
                print(f"Status: {result.get('status')}")
                print(f"Message: {result.get('message')}")
            else:
                print(f"❌ Error approving diagnosis: {response.status}")
        
        # Test 4: Generate similar diagnosis (Patient B)
        print("\n📋 Test 4: Generate similar diagnosis (Patient B)")
        print("-" * 40)
        
        patient_b_request = {
            "text": "У мене головний біль, температура 37.5 і легкий кашель",
            "user_id": "patient_b", 
            "chat_id": "chat_b"
        }
        
        print(f"Patient B symptoms: {patient_b_request['text']}")
        print("(Similar to Patient A but with cough)")
        
        response = await session.post(
            f"{API_BASE_URL}/assistant/message",
            json=patient_b_request
        )
        
        if response.status == 200:
            result = await response.json()
            print(f"✅ Response received")
            print(f"Intent: {result.get('intent')}")
            print(f"Message: {result.get('message', 'No message')[:100]}...")
            
            # Check if this was cached (similar case)
            data = result.get('data', {})
            if data.get('cached'):
                print("🎯 This was served from cache (similar case found!)")
            else:
                print("🔄 This was a new diagnosis (no similar case found)")
        else:
            print(f"❌ Error: {response.status}")
        
        # Test 5: Search knowledge base for similar cases
        print("\n🔍 Test 5: Search knowledge base for similar cases")
        print("-" * 40)
        
        search_request = {
            "query": "headache fever",
            "top_k": 3,
            "min_similarity": 0.8
        }
        
        response = await session.post(
            f"{API_BASE_URL}/knowledge-base/search",
            json=search_request
        )
        
        if response.status == 200:
            result = await response.json()
            print(f"✅ Search completed")
            print(f"Query: {result.get('query')}")
            print(f"Total found: {result.get('total_found')}")
            print(f"Search method: {result.get('search_method')}")
            
            results = result.get('results', [])
            for i, entry in enumerate(results, 1):
                print(f"\nResult {i}:")
                print(f"  Doctor: {entry.get('doctor_name', 'Unknown')}")
                print(f"  Date: {entry.get('created_at')}")
                print(f"  Similarity: {entry.get('similarity_score', 'N/A')}")
                print(f"  Diagnosis: {entry.get('answer_md', '')[:100]}...")
        else:
            print(f"❌ Error searching: {response.status}")
        
        # Test 6: List recent knowledge base entries
        print("\n📚 Test 6: List recent knowledge base entries")
        print("-" * 40)
        
        response = await session.get(f"{API_BASE_URL}/knowledge-base/entries?limit=5")
        if response.status == 200:
            entries = await response.json()
            print(f"✅ Found {len(entries)} recent entries")
            
            for i, entry in enumerate(entries, 1):
                print(f"\nEntry {i}:")
                print(f"  ID: {entry.get('id')}")
                print(f"  Doctor: {entry.get('doctor_name', 'Unknown')}")
                print(f"  Date: {entry.get('created_at')}")
                print(f"  Approved: {entry.get('approved')}")
                print(f"  Hash: {entry.get('symptoms_hash', '')[:16]}...")
        else:
            print(f"❌ Error listing entries: {response.status}")

async def test_semantic_similarity():
    """Test semantic similarity with different symptom variations."""
    
    print("\n🧠 Testing Semantic Similarity")
    print("=" * 50)
    
    # Test cases with similar symptoms
    test_cases = [
        "У мене головний біль і температура",
        "Головний біль, температура 38 градусів",
        "Температура і головний біль",
        "Болить голова, підвищена температура",
        "Лихоманка і головний біль"
    ]
    
    async with aiohttp.ClientSession() as session:
        for i, symptoms in enumerate(test_cases, 1):
            print(f"\n📋 Test Case {i}: {symptoms}")
            print("-" * 30)
            
            request = {
                "text": symptoms,
                "user_id": f"test_user_{i}",
                "chat_id": f"test_chat_{i}"
            }
            
            response = await session.post(
                f"{API_BASE_URL}/assistant/message",
                json=request
            )
            
            if response.status == 200:
                result = await response.json()
                data = result.get('data', {})
                
                if data.get('cached'):
                    print("🎯 Served from cache (similar case found)")
                else:
                    print("🔄 New diagnosis generated")
                
                print(f"Response: {result.get('message', '')[:80]}...")
            else:
                print(f"❌ Error: {response.status}")

async def main():
    """Main test function."""
    print("🚀 Starting Knowledge Base Flow Tests")
    print(f"API URL: {API_BASE_URL}")
    print("=" * 60)
    
    try:
        # Test basic flow
        await test_knowledge_base_flow()
        
        # Test semantic similarity
        await test_semantic_similarity()
        
        print("\n✅ All tests completed!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main()) 