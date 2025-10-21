#!/usr/bin/env python
"""
Test script to verify API can start and respond

This script:
1. Imports the FastAPI app
2. Creates a test client
3. Tests the health endpoint
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    print("🧪 Testing HyperGraphRAG Visualization API...")
    print()
    
    # Test 1: Import FastAPI app
    print("1. Importing FastAPI app...")
    from api.main import app
    print("   ✓ Import successful")
    
    # Test 2: Create test client
    print("2. Creating test client...")
    from fastapi.testclient import TestClient
    client = TestClient(app)
    print("   ✓ Test client created")
    
    # Test 3: Test health endpoint
    print("3. Testing health endpoint...")
    response = client.get("/api/health")
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.json()}")
    
    if response.status_code == 200:
        print("   ✓ Health check passed")
    else:
        print("   ✗ Health check failed")
        sys.exit(1)
    
    # Test 4: Test root endpoint
    print("4. Testing root endpoint...")
    response = client.get("/")
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.json()}")
    
    if response.status_code == 200:
        print("   ✓ Root endpoint passed")
    else:
        print("   ✗ Root endpoint failed")
        sys.exit(1)
    
    print()
    print("✅ All tests passed!")
    print()
    print("To start the API server, run:")
    print("  python api/main.py")
    print("  or")
    print("  ./scripts/start_api.sh")
    
except Exception as e:
    print(f"❌ Test failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
