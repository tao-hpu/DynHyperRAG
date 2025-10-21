#!/usr/bin/env python
"""
Test script for Graph API endpoints

Tests all Graph API routes with the TestClient.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def test_graph_api():
    """Test Graph API endpoints"""
    
    print("🧪 Testing Graph API Endpoints...")
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
        
        # Test health endpoint
        print("3. Testing /api/health...")
        response = client.get("/api/health")
        assert response.status_code == 200
        print(f"   ✓ Health check passed: {response.json()}")
        
        # Check if data exists
        import os
        if not os.path.exists("expr/example/graph_chunk_entity_relation.graphml"):
            print("   ⚠️  Warning: No data found in expr/example/")
            print("   Skipping endpoint tests (run script_construct.py first)")
            print()
            print("✅ API structure tests passed!")
            print("   To test with real data, run: python script_construct.py")
            return
        
        # Initialize graph service manually for testing
        print("4. Initializing GraphService for testing...")
        from api.main import graph_service
        import asyncio
        asyncio.run(graph_service.initialize())
        print("   ✓ GraphService initialized")
        
        # Test get stats
        print("5. Testing GET /api/graph/stats...")
        response = client.get("/api/graph/stats")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            stats = response.json()
            print(f"   Nodes: {stats['num_nodes']}")
            print(f"   Edges: {stats['num_edges']}")
            print(f"   Hyperedges: {stats['num_hyperedges']}")
            print("   ✓ GET /api/graph/stats passed")
        else:
            print(f"   Response: {response.json()}")
        
        # Test get nodes
        print("6. Testing GET /api/graph/nodes...")
        response = client.get("/api/graph/nodes?limit=5")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            nodes = response.json()
            print(f"   Retrieved {len(nodes)} nodes")
            if nodes:
                print(f"   Sample: {nodes[0]['label']} ({nodes[0]['type']})")
            print("   ✓ GET /api/graph/nodes passed")
        else:
            print(f"   Response: {response.json()}")
        
        # Test get edges
        print("7. Testing GET /api/graph/edges...")
        response = client.get("/api/graph/edges?limit=5")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            edges = response.json()
            print(f"   Retrieved {len(edges)} edges")
            if edges:
                print(f"   Sample: {edges[0]['source']} -> {edges[0]['target']}")
                print(f"   Is hyperedge: {edges[0]['is_hyperedge']}")
            print("   ✓ GET /api/graph/edges passed")
        else:
            print(f"   Response: {response.json()}")
        
        # Test search
        print("8. Testing GET /api/graph/search...")
        response = client.get("/api/graph/search?keyword=test&limit=3")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            results = response.json()
            print(f"   Search returned {len(results)} results")
            print("   ✓ GET /api/graph/search passed")
        else:
            print(f"   Response: {response.json()}")
        
        # Test get single node (if we have nodes)
        nodes = response.json() if response.status_code == 200 else []
        if nodes:
            print("9. Testing GET /api/graph/nodes/{node_id}...")
            node_id = nodes[0]['id']
            response = client.get(f"/api/graph/nodes/{node_id}")
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                node = response.json()
                print(f"   Node: {node['label']}")
                print("   ✓ GET /api/graph/nodes/{node_id} passed")
            else:
                print(f"   Response: {response.json()}")
        
        # Test subgraph (if we have nodes)
        if nodes:
            print("10. Testing GET /api/graph/subgraph...")
            node_id = nodes[0]['id']
            response = client.get(f"/api/graph/subgraph?center_node_id={node_id}&depth=1")
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                subgraph = response.json()
                print(f"   Subgraph: {len(subgraph['nodes'])} nodes, {len(subgraph['edges'])} edges")
                print("   ✓ GET /api/graph/subgraph passed")
            else:
                print(f"   Response: {response.json()}")
        
        # Test error handling - 404
        print("11. Testing error handling (404)...")
        response = client.get("/api/graph/nodes/nonexistent-node-id")
        print(f"   Status: {response.status_code}")
        if response.status_code == 404:
            print(f"   Error: {response.json()}")
            print("   ✓ 404 error handling works")
        
        # Test validation error - invalid limit
        print("12. Testing validation error...")
        response = client.get("/api/graph/nodes?limit=99999")
        print(f"   Status: {response.status_code}")
        if response.status_code == 422:
            print(f"   Validation error: {response.json()['error']}")
            print("   ✓ Validation error handling works")
        
        print()
        print("✅ All Graph API endpoint tests completed!")
        print()
        print("API is ready to use. Start the server with:")
        print("  python api/main.py")
        print("  or")
        print("  ./scripts/start_api.sh")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    test_graph_api()
