"""
Performance tests for API endpoints

Tests response times and throughput.
"""

import pytest
from fastapi.testclient import TestClient
import asyncio
import time

# Mark all tests in this module as performance tests
pytestmark = [pytest.mark.performance, pytest.mark.slow]


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


class TestGraphAPIPerformance:
    """Performance tests for Graph API"""
    
    def test_get_stats_performance(self, client):
        """Test /api/graph/stats response time"""
        start = time.time()
        response = client.get("/api/graph/stats")
        elapsed = time.time() - start
        
        assert response.status_code == 200
        assert elapsed < 1.0, f"Stats endpoint too slow: {elapsed:.2f}s"
        print(f"\n  Stats response time: {elapsed:.3f}s")
    
    def test_get_nodes_performance(self, client):
        """Test /api/graph/nodes response time"""
        start = time.time()
        response = client.get("/api/graph/nodes?limit=100")
        elapsed = time.time() - start
        
        assert response.status_code == 200
        assert elapsed < 2.0, f"Nodes endpoint too slow: {elapsed:.2f}s"
        print(f"\n  Nodes (100) response time: {elapsed:.3f}s")
    
    def test_get_edges_performance(self, client):
        """Test /api/graph/edges response time"""
        start = time.time()
        response = client.get("/api/graph/edges?limit=100")
        elapsed = time.time() - start
        
        assert response.status_code == 200
        assert elapsed < 2.0, f"Edges endpoint too slow: {elapsed:.2f}s"
        print(f"\n  Edges (100) response time: {elapsed:.3f}s")
    
    def test_search_performance(self, client):
        """Test /api/graph/search response time"""
        start = time.time()
        response = client.get("/api/graph/search?keyword=test&limit=20")
        elapsed = time.time() - start
        
        assert response.status_code == 200
        assert elapsed < 3.0, f"Search endpoint too slow: {elapsed:.2f}s"
        print(f"\n  Search response time: {elapsed:.3f}s")
    
    def test_subgraph_performance(self, client):
        """Test /api/graph/subgraph response time"""
        # Get a node ID first
        response = client.get("/api/graph/nodes?limit=1")
        if response.status_code == 200 and response.json():
            node_id = response.json()[0]["id"]
            
            start = time.time()
            response = client.get(f"/api/graph/subgraph?center_node_id={node_id}&depth=1")
            elapsed = time.time() - start
            
            assert response.status_code == 200
            assert elapsed < 2.0, f"Subgraph endpoint too slow: {elapsed:.2f}s"
            print(f"\n  Subgraph response time: {elapsed:.3f}s")
    
    def test_pagination_performance(self, client):
        """Test pagination performance"""
        times = []
        
        for offset in [0, 100, 200]:
            start = time.time()
            response = client.get(f"/api/graph/nodes?limit=100&offset={offset}")
            elapsed = time.time() - start
            times.append(elapsed)
            
            assert response.status_code == 200
        
        avg_time = sum(times) / len(times)
        print(f"\n  Average pagination time: {avg_time:.3f}s")
        assert avg_time < 2.0, f"Pagination too slow: {avg_time:.2f}s"


class TestQueryAPIPerformance:
    """Performance tests for Query API"""
    
    def test_query_hybrid_performance(self, client):
        """Test hybrid query performance"""
        query_request = {
            "query": "What is hypertension?",
            "mode": "hybrid",
            "top_k": 60
        }
        
        start = time.time()
        response = client.post("/api/query/", json=query_request)
        elapsed = time.time() - start
        
        assert response.status_code == 200
        
        result = response.json()
        execution_time = result["execution_time"]
        
        print(f"\n  Hybrid query time: {execution_time:.3f}s (total: {elapsed:.3f}s)")
        
        # Query should complete in reasonable time
        # Note: This depends on LLM API latency
        assert execution_time < 30.0, f"Query too slow: {execution_time:.2f}s"
    
    def test_query_local_performance(self, client):
        """Test local query performance"""
        query_request = {
            "query": "What causes disease?",
            "mode": "local",
            "top_k": 30
        }
        
        response = client.post("/api/query/", json=query_request)
        assert response.status_code == 200
        
        execution_time = response.json()["execution_time"]
        print(f"\n  Local query time: {execution_time:.3f}s")
    
    def test_query_global_performance(self, client):
        """Test global query performance"""
        query_request = {
            "query": "How are entities related?",
            "mode": "global",
            "top_k": 30
        }
        
        response = client.post("/api/query/", json=query_request)
        assert response.status_code == 200
        
        execution_time = response.json()["execution_time"]
        print(f"\n  Global query time: {execution_time:.3f}s")
    
    def test_query_naive_performance(self, client):
        """Test naive query performance"""
        query_request = {
            "query": "What is a medical condition?",
            "mode": "naive",
            "top_k": 20
        }
        
        response = client.post("/api/query/", json=query_request)
        assert response.status_code == 200
        
        execution_time = response.json()["execution_time"]
        print(f"\n  Naive query time: {execution_time:.3f}s")
    
    def test_history_performance(self, client):
        """Test query history performance"""
        # Add some queries to history
        for i in range(5):
            query_request = {
                "query": f"Test query {i}",
                "mode": "hybrid",
                "top_k": 20
            }
            client.post("/api/query/", json=query_request)
        
        # Test history retrieval
        start = time.time()
        response = client.get("/api/query/history?limit=10")
        elapsed = time.time() - start
        
        assert response.status_code == 200
        assert elapsed < 0.5, f"History endpoint too slow: {elapsed:.2f}s"
        print(f"\n  History response time: {elapsed:.3f}s")


class TestConcurrency:
    """Test concurrent request handling"""
    
    def test_concurrent_stats_requests(self, client):
        """Test multiple concurrent stats requests"""
        import concurrent.futures
        
        def make_request():
            return client.get("/api/graph/stats")
        
        start = time.time()
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request) for _ in range(10)]
            results = [f.result() for f in futures]
        elapsed = time.time() - start
        
        assert all(r.status_code == 200 for r in results)
        print(f"\n  10 concurrent stats requests: {elapsed:.3f}s")
        assert elapsed < 5.0, f"Concurrent requests too slow: {elapsed:.2f}s"
    
    def test_concurrent_node_requests(self, client):
        """Test multiple concurrent node requests"""
        import concurrent.futures
        
        def make_request(offset):
            return client.get(f"/api/graph/nodes?limit=10&offset={offset}")
        
        start = time.time()
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(make_request, i*10) for i in range(5)]
            results = [f.result() for f in futures]
        elapsed = time.time() - start
        
        assert all(r.status_code == 200 for r in results)
        print(f"\n  5 concurrent node requests: {elapsed:.3f}s")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
