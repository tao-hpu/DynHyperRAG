"""
Integration tests for API endpoints

Tests the complete API flow with all endpoints.
"""

import pytest
from fastapi.testclient import TestClient
import asyncio

# Mark all tests in this module as integration tests
pytestmark = pytest.mark.integration


@pytest.fixture(scope="module")
def client():
    """Create test client with initialized services"""
    from api.main import app, graph_service, query_service
    
    # Initialize services
    async def init():
        await graph_service.initialize()
        await query_service.initialize(graph_service.rag)
    
    asyncio.run(init())
    
    return TestClient(app)


class TestHealthEndpoints:
    """Test health and root endpoints"""
    
    def test_health_check(self, client):
        """Test health check endpoint"""
        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "service" in data
        assert "version" in data
    
    def test_root_endpoint(self, client):
        """Test root endpoint"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "docs" in data
        assert "health" in data


class TestGraphAPI:
    """Test Graph API endpoints"""
    
    def test_get_stats(self, client):
        """Test GET /api/graph/stats"""
        response = client.get("/api/graph/stats")
        assert response.status_code == 200
        
        stats = response.json()
        assert "num_nodes" in stats
        assert "num_edges" in stats
        assert "num_hyperedges" in stats
        assert "avg_degree" in stats
        assert "density" in stats
        
        # Verify types
        assert isinstance(stats["num_nodes"], int)
        assert isinstance(stats["num_edges"], int)
        assert isinstance(stats["avg_degree"], float)
    
    def test_get_nodes_default(self, client):
        """Test GET /api/graph/nodes with default parameters"""
        response = client.get("/api/graph/nodes")
        assert response.status_code == 200
        
        nodes = response.json()
        assert isinstance(nodes, list)
        assert len(nodes) <= 100  # Default limit
        
        if nodes:
            node = nodes[0]
            assert "id" in node
            assert "label" in node
            assert "type" in node
            assert "weight" in node
    
    def test_get_nodes_with_pagination(self, client):
        """Test GET /api/graph/nodes with pagination"""
        # Get first page
        response1 = client.get("/api/graph/nodes?limit=5&offset=0")
        assert response1.status_code == 200
        nodes1 = response1.json()
        assert len(nodes1) <= 5
        
        # Get second page
        response2 = client.get("/api/graph/nodes?limit=5&offset=5")
        assert response2.status_code == 200
        nodes2 = response2.json()
        
        # Verify different results
        if nodes1 and nodes2:
            assert nodes1[0]["id"] != nodes2[0]["id"]
    
    def test_get_nodes_with_type_filter(self, client):
        """Test GET /api/graph/nodes with entity type filter"""
        # First get a node to know a valid type
        response = client.get("/api/graph/nodes?limit=1")
        if response.status_code == 200 and response.json():
            entity_type = response.json()[0]["type"]
            
            # Filter by that type
            response = client.get(f"/api/graph/nodes?entity_type={entity_type}")
            assert response.status_code == 200
            
            nodes = response.json()
            if nodes:
                assert all(node["type"] == entity_type for node in nodes)
    
    def test_get_node_by_id(self, client):
        """Test GET /api/graph/nodes/{node_id}"""
        # First get a node ID
        response = client.get("/api/graph/nodes?limit=1")
        assert response.status_code == 200
        
        nodes = response.json()
        if nodes:
            node_id = nodes[0]["id"]
            
            # Get that specific node
            response = client.get(f"/api/graph/nodes/{node_id}")
            assert response.status_code == 200
            
            node = response.json()
            assert node["id"] == node_id
    
    def test_get_node_not_found(self, client):
        """Test GET /api/graph/nodes/{node_id} with invalid ID"""
        response = client.get("/api/graph/nodes/nonexistent-id-12345")
        assert response.status_code == 404
        
        error = response.json()
        assert "error" in error
    
    def test_get_edges(self, client):
        """Test GET /api/graph/edges"""
        response = client.get("/api/graph/edges?limit=10")
        assert response.status_code == 200
        
        edges = response.json()
        assert isinstance(edges, list)
        
        if edges:
            edge = edges[0]
            assert "id" in edge
            assert "source" in edge
            assert "target" in edge
            assert "weight" in edge
            assert "entities" in edge
            assert "is_hyperedge" in edge
            assert isinstance(edge["is_hyperedge"], bool)
    
    def test_get_edges_with_weight_filter(self, client):
        """Test GET /api/graph/edges with min_weight filter"""
        response = client.get("/api/graph/edges?min_weight=0.5&limit=10")
        assert response.status_code == 200
        
        edges = response.json()
        if edges:
            assert all(edge["weight"] >= 0.5 for edge in edges)
    
    def test_search_nodes(self, client):
        """Test GET /api/graph/search"""
        # Get a node first to use its label as search term
        response = client.get("/api/graph/nodes?limit=1")
        if response.status_code == 200 and response.json():
            label = response.json()[0]["label"]
            search_term = label.split()[0] if label else "test"
            
            # Search
            response = client.get(f"/api/graph/search?keyword={search_term}&limit=5")
            assert response.status_code == 200
            
            results = response.json()
            assert isinstance(results, list)
            assert len(results) <= 5
            
            if results:
                assert "relevance_score" in results[0]
    
    def test_get_subgraph(self, client):
        """Test GET /api/graph/subgraph"""
        # Get a node ID first
        response = client.get("/api/graph/nodes?limit=1")
        if response.status_code == 200 and response.json():
            node_id = response.json()[0]["id"]
            
            # Get subgraph
            response = client.get(f"/api/graph/subgraph?center_node_id={node_id}&depth=1")
            assert response.status_code == 200
            
            subgraph = response.json()
            assert "nodes" in subgraph
            assert "edges" in subgraph
            assert isinstance(subgraph["nodes"], list)
            assert isinstance(subgraph["edges"], list)
    
    def test_validation_errors(self, client):
        """Test parameter validation"""
        # Invalid limit (too large)
        response = client.get("/api/graph/nodes?limit=99999")
        assert response.status_code == 422
        
        # Invalid offset (negative)
        response = client.get("/api/graph/nodes?offset=-1")
        assert response.status_code == 422
        
        # Invalid depth
        response = client.get("/api/graph/subgraph?center_node_id=test&depth=10")
        assert response.status_code == 422


class TestQueryAPI:
    """Test Query API endpoints"""
    
    def test_execute_query_hybrid(self, client):
        """Test POST /api/query/ with hybrid mode"""
        query_request = {
            "query": "What is hypertension?",
            "mode": "hybrid",
            "top_k": 60
        }
        
        response = client.post("/api/query/", json=query_request)
        assert response.status_code == 200
        
        result = response.json()
        assert "answer" in result
        assert "query_path" in result
        assert "execution_time" in result
        assert "mode" in result
        assert result["mode"] == "hybrid"
        assert isinstance(result["execution_time"], float)
        assert result["execution_time"] > 0
    
    def test_execute_query_local(self, client):
        """Test POST /api/query/ with local mode"""
        query_request = {
            "query": "What causes hypertension?",
            "mode": "local",
            "top_k": 30
        }
        
        response = client.post("/api/query/", json=query_request)
        assert response.status_code == 200
        assert response.json()["mode"] == "local"
    
    def test_execute_query_global(self, client):
        """Test POST /api/query/ with global mode"""
        query_request = {
            "query": "How are diseases related?",
            "mode": "global",
            "top_k": 30
        }
        
        response = client.post("/api/query/", json=query_request)
        assert response.status_code == 200
        assert response.json()["mode"] == "global"
    
    def test_execute_query_naive(self, client):
        """Test POST /api/query/ with naive mode"""
        query_request = {
            "query": "What is a disease?",
            "mode": "naive",
            "top_k": 20
        }
        
        response = client.post("/api/query/", json=query_request)
        assert response.status_code == 200
        assert response.json()["mode"] == "naive"
    
    def test_query_history(self, client):
        """Test GET /api/query/history"""
        # Execute a query first
        query_request = {
            "query": "Test query for history",
            "mode": "hybrid"
        }
        client.post("/api/query/", json=query_request)
        
        # Get history
        response = client.get("/api/query/history?limit=10")
        assert response.status_code == 200
        
        history = response.json()
        assert "queries" in history
        assert "total" in history
        assert isinstance(history["queries"], list)
        assert history["total"] > 0
        
        if history["queries"]:
            query_item = history["queries"][0]
            assert "id" in query_item
            assert "query" in query_item
            assert "mode" in query_item
            assert "timestamp" in query_item
            assert "execution_time" in query_item
    
    def test_clear_history(self, client):
        """Test DELETE /api/query/history"""
        # Execute a query
        query_request = {"query": "Test", "mode": "hybrid"}
        client.post("/api/query/", json=query_request)
        
        # Clear history
        response = client.delete("/api/query/history")
        assert response.status_code == 200
        assert response.json()["status"] == "success"
        
        # Verify history is empty
        response = client.get("/api/query/history")
        assert response.status_code == 200
        assert response.json()["total"] == 0
    
    def test_query_validation_errors(self, client):
        """Test query validation"""
        # Empty query
        response = client.post("/api/query/", json={"query": ""})
        assert response.status_code == 422
        
        # Invalid mode
        response = client.post("/api/query/", json={"query": "test", "mode": "invalid"})
        assert response.status_code == 422
        
        # Invalid top_k
        response = client.post("/api/query/", json={"query": "test", "top_k": 0})
        assert response.status_code == 422
        
        response = client.post("/api/query/", json={"query": "test", "top_k": 999})
        assert response.status_code == 422


class TestErrorHandling:
    """Test error handling across all endpoints"""
    
    def test_404_errors(self, client):
        """Test 404 error handling"""
        # Non-existent node
        response = client.get("/api/graph/nodes/fake-id")
        assert response.status_code == 404
        
        # Non-existent edge
        response = client.get("/api/graph/edges/fake-source-fake-target")
        assert response.status_code == 404
        
        # Non-existent endpoint
        response = client.get("/api/nonexistent")
        assert response.status_code == 404
    
    def test_422_validation_errors(self, client):
        """Test validation error responses"""
        # Invalid query parameters
        response = client.get("/api/graph/nodes?limit=abc")
        assert response.status_code == 422
        
        error = response.json()
        assert "error" in error or "detail" in error


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
