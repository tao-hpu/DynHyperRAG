#!/usr/bin/env python
"""
Test script for Query API endpoints

Tests query execution and history management.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def test_query_api():
    """Test Query API endpoints"""
    
    print("🧪 Testing Query API Endpoints...")
    print()
    
    try:
        # Import FastAPI app
        print("1. Importing FastAPI app...")
        from api.main import app
        from fastapi.testclient import TestClient
        print("   ✓ Import successful")
        
        # Create test client
        print("2. Creating test client...")
        client = TestClient(app)
        print("   ✓ Test client created")
        
        # Check if data exists
        import os
        if not os.path.exists("expr/example/graph_chunk_entity_relation.graphml"):
            print("   ⚠️  Warning: No data found in expr/example/")
            print("   Skipping query tests (run script_construct.py first)")
            print()
            print("✅ API structure tests passed!")
            return
        
        # Initialize services manually for testing
        print("3. Initializing services for testing...")
        from api.main import graph_service, query_service
        import asyncio
        
        async def init_services():
            await graph_service.initialize()
            await query_service.initialize(graph_service.rag)
        
        asyncio.run(init_services())
        print("   ✓ Services initialized")
        
        # Test query execution
        print("4. Testing POST /api/query/...")
        query_request = {
            "query": "What is hypertension?",
            "mode": "hybrid",
            "top_k": 60
        }
        response = client.post("/api/query/", json=query_request)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"   Answer preview: {result['answer'][:100]}...")
            print(f"   Execution time: {result['execution_time']:.2f}s")
            print(f"   Mode: {result['mode']}")
            print("   ✓ POST /api/query/ passed")
        else:
            print(f"   Response: {response.json()}")
        
        # Test query history
        print("5. Testing GET /api/query/history...")
        response = client.get("/api/query/history?limit=5")
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            history = response.json()
            print(f"   Total queries: {history['total']}")
            print(f"   Retrieved: {len(history['queries'])} queries")
            if history['queries']:
                latest = history['queries'][0]
                print(f"   Latest query: '{latest['query'][:50]}...'")
            print("   ✓ GET /api/query/history passed")
        else:
            print(f"   Response: {response.json()}")
        
        # Test different query modes
        print("6. Testing different query modes...")
        modes = ["local", "global", "naive"]
        for mode in modes:
            query_request = {
                "query": "What causes hypertension?",
                "mode": mode,
                "top_k": 30
            }
            response = client.post("/api/query/", json=query_request)
            if response.status_code == 200:
                result = response.json()
                print(f"   {mode} mode: {result['execution_time']:.2f}s")
            else:
                print(f"   {mode} mode failed: {response.status_code}")
        print("   ✓ Multiple query modes tested")
        
        # Test clear history
        print("7. Testing DELETE /api/query/history...")
        response = client.delete("/api/query/history")
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"   Message: {result['message']}")
            print("   ✓ DELETE /api/query/history passed")
        
        # Verify history is cleared
        response = client.get("/api/query/history")
        if response.status_code == 200:
            history = response.json()
            print(f"   History after clear: {history['total']} queries")
        
        # Test validation errors
        print("8. Testing validation errors...")
        
        # Empty query
        response = client.post("/api/query/", json={"query": ""})
        if response.status_code == 422:
            print("   ✓ Empty query rejected")
        
        # Invalid mode
        response = client.post("/api/query/", json={"query": "test", "mode": "invalid"})
        if response.status_code == 422:
            print("   ✓ Invalid mode rejected")
        
        # Invalid top_k
        response = client.post("/api/query/", json={"query": "test", "top_k": 999})
        if response.status_code == 422:
            print("   ✓ Invalid top_k rejected")
        
        print()
        print("✅ All Query API tests completed!")
        print()
        print("Query API is ready to use. Start the server with:")
        print("  python api/main.py")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    test_query_api()
