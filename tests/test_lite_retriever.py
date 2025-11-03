"""
Test script for LiteRetriever

This script tests the lightweight retriever functionality including:
- Basic retrieval
- Caching behavior
- Quality scoring
- Performance metrics
"""

import asyncio
import sys
import time
from typing import List

# Mock implementations for testing
class MockGraphStorage:
    """Mock graph storage for testing"""
    
    def __init__(self):
        self.nodes = {
            "he1": {
                "role": "hyperedge",
                "hyperedge": "Disease X is treated with medication Y",
                "weight": 85
            },
            "he2": {
                "role": "hyperedge",
                "hyperedge": "Symptom A indicates disease X",
                "weight": 90
            },
            "he3": {
                "role": "hyperedge",
                "hyperedge": "Medication Y has side effect Z",
                "weight": 75
            },
            "entity1": {
                "role": "entity",
                "entity_name": "Disease X",
                "entity_type": "disease",
                "description": "A chronic condition"
            },
            "entity2": {
                "role": "entity",
                "entity_name": "Medication Y",
                "entity_type": "medication",
                "description": "An effective treatment"
            },
            "entity3": {
                "role": "entity",
                "entity_name": "Symptom A",
                "entity_type": "symptom",
                "description": "Common symptom"
            }
        }
        
        self.edges = {
            "he1": [("he1", "entity1"), ("he1", "entity2")],
            "he2": [("he2", "entity3"), ("he2", "entity1")],
            "he3": [("he3", "entity2")]
        }
    
    async def get_node(self, node_id: str):
        return self.nodes.get(node_id)
    
    async def get_node_edges(self, node_id: str):
        return self.edges.get(node_id, [])
    
    async def node_degree(self, node_id: str):
        return len(self.edges.get(node_id, []))


class MockVectorStorage:
    """Mock vector storage for testing"""
    
    async def query(self, query: str, top_k: int) -> List[dict]:
        # Return mock results
        results = [
            {
                "hyperedge_name": "he1",
                "hyperedge": "Disease X is treated with medication Y",
                "distance": 0.85,
                "weight": 85
            },
            {
                "hyperedge_name": "he2",
                "hyperedge": "Symptom A indicates disease X",
                "distance": 0.78,
                "weight": 90
            },
            {
                "hyperedge_name": "he3",
                "hyperedge": "Medication Y has side effect Z",
                "distance": 0.65,
                "weight": 75
            }
        ]
        return results[:top_k]


async def mock_embedding_func(texts: List[str]):
    """Mock embedding function"""
    import numpy as np
    # Return random embeddings for testing
    return [np.random.rand(384) for _ in texts]


async def test_basic_retrieval():
    """Test basic retrieval functionality"""
    print("\n" + "="*60)
    print("TEST 1: Basic Retrieval")
    print("="*60)
    
    from hypergraphrag.retrieval import LiteRetriever
    
    # Initialize mock storage
    graph = MockGraphStorage()
    vdb = MockVectorStorage()
    
    # Initialize retriever
    config = {
        "cache_size": 100,
        "quality_cache_size": 500,
        "degree_weight": 0.5,
        "coherence_weight": 0.5,
        "similarity_weight": 0.7,
        "quality_weight": 0.3,
        "embedding_func": mock_embedding_func
    }
    
    retriever = LiteRetriever(graph, vdb, config)
    
    # Test retrieval
    query = "What is the treatment for disease X?"
    results = await retriever.retrieve(query, top_k=3)
    
    print(f"\nQuery: {query}")
    print(f"Retrieved {len(results)} results:\n")
    
    for i, result in enumerate(results, 1):
        print(f"{i}. Hyperedge: {result['hyperedge_name']}")
        print(f"   Text: {result['hyperedge']}")
        print(f"   Similarity: {result['distance']:.3f}")
        print(f"   Quality: {result.get('simple_quality', 'N/A'):.3f}")
        print(f"   Final Score: {result['final_score']:.3f}")
        print()
    
    assert len(results) > 0, "Should retrieve at least one result"
    assert "final_score" in results[0], "Results should have final_score"
    assert "simple_quality" in results[0], "Results should have simple_quality"
    
    print("✓ Basic retrieval test passed")
    return retriever


async def test_caching(retriever):
    """Test caching behavior"""
    print("\n" + "="*60)
    print("TEST 2: Caching Behavior")
    print("="*60)
    
    query = "What is the treatment for disease X?"
    
    # First query (cache miss)
    start = time.time()
    results1 = await retriever.retrieve(query, top_k=3)
    time1 = time.time() - start
    
    # Second query (cache hit)
    start = time.time()
    results2 = await retriever.retrieve(query, top_k=3)
    time2 = time.time() - start
    
    print(f"\nFirst query time: {time1*1000:.2f}ms (cache miss)")
    print(f"Second query time: {time2*1000:.2f}ms (cache hit)")
    print(f"Speedup: {time1/time2:.1f}x")
    
    # Get cache stats
    stats = retriever.get_cache_stats()
    print(f"\nCache Statistics:")
    print(f"  Query cache hit rate: {stats['query_cache']['hit_rate']:.2%}")
    print(f"  Query cache size: {stats['query_cache']['size']}")
    print(f"  Quality cache size: {stats['quality_cache']['size']}")
    
    assert len(results1) == len(results2), "Cached results should match"
    assert time2 < time1, "Cached query should be faster"
    assert stats['query_cache']['hits'] > 0, "Should have cache hits"
    
    print("\n✓ Caching test passed")


async def test_quality_scoring(retriever):
    """Test quality scoring"""
    print("\n" + "="*60)
    print("TEST 3: Quality Scoring")
    print("="*60)
    
    # Clear cache to force recomputation
    retriever.clear_cache()
    
    query = "What is the treatment for disease X?"
    results = await retriever.retrieve(query, top_k=3)
    
    print("\nQuality Scores:")
    for result in results:
        he_id = result['hyperedge_name']
        quality = result.get('simple_quality', 0)
        print(f"  {he_id}: {quality:.3f}")
    
    # Check that quality scores are in valid range
    for result in results:
        quality = result.get('simple_quality', 0)
        assert 0 <= quality <= 1, f"Quality score should be in [0,1], got {quality}"
    
    print("\n✓ Quality scoring test passed")


async def test_weight_adjustment(retriever):
    """Test dynamic weight adjustment"""
    print("\n" + "="*60)
    print("TEST 4: Weight Adjustment")
    print("="*60)
    
    # Clear cache
    retriever.clear_cache()
    
    query = "What is the treatment for disease X?"
    
    # Test with similarity-focused weights
    retriever.set_weights(similarity_weight=0.9, quality_weight=0.1)
    results1 = await retriever.retrieve(query, top_k=3)
    
    # Clear cache
    retriever.clear_cache()
    
    # Test with quality-focused weights
    retriever.set_weights(similarity_weight=0.3, quality_weight=0.7)
    results2 = await retriever.retrieve(query, top_k=3)
    
    print("\nSimilarity-focused ranking (0.9/0.1):")
    for i, r in enumerate(results1[:2], 1):
        print(f"  {i}. {r['hyperedge_name']}: score={r['final_score']:.3f}")
    
    print("\nQuality-focused ranking (0.3/0.7):")
    for i, r in enumerate(results2[:2], 1):
        print(f"  {i}. {r['hyperedge_name']}: score={r['final_score']:.3f}")
    
    # Rankings might differ
    print("\n✓ Weight adjustment test passed")


async def test_performance_metrics(retriever):
    """Test performance metrics"""
    print("\n" + "="*60)
    print("TEST 5: Performance Metrics")
    print("="*60)
    
    # Clear cache and reset stats by creating new retriever
    from hypergraphrag.retrieval import LiteRetriever
    
    graph = MockGraphStorage()
    vdb = MockVectorStorage()
    
    config = {
        "cache_size": 100,
        "quality_cache_size": 500,
        "embedding_func": mock_embedding_func
    }
    
    fresh_retriever = LiteRetriever(graph, vdb, config)
    
    # Run multiple queries
    queries = [
        "What is the treatment for disease X?",
        "What are the symptoms of disease X?",
        "What are the side effects of medication Y?"
    ]
    
    for query in queries:
        await fresh_retriever.retrieve(query, top_k=3)
    
    # Get statistics
    stats = fresh_retriever.get_cache_stats()
    
    print("\nPerformance Metrics:")
    print(f"  Total queries: {stats['retrieval_stats']['total_queries']}")
    print(f"  Cache hits: {stats['retrieval_stats']['cache_hits']}")
    print(f"  Quality computations: {stats['retrieval_stats']['total_quality_computations']}")
    print(f"  Average retrieval time: {stats['retrieval_stats']['avg_retrieval_time']*1000:.2f}ms")
    
    print(f"\nQuery Cache:")
    print(f"  Size: {stats['query_cache']['size']}/{stats['query_cache']['max_size']}")
    print(f"  Hit rate: {stats['query_cache']['hit_rate']:.2%}")
    
    print(f"\nQuality Cache:")
    print(f"  Size: {stats['quality_cache']['size']}/{stats['quality_cache']['max_size']}")
    print(f"  Hit rate: {stats['quality_cache']['hit_rate']:.2%}")
    
    assert stats['retrieval_stats']['total_queries'] == len(queries), "Should track all queries"
    
    print("\n✓ Performance metrics test passed")


async def test_no_embedding_func():
    """Test retriever without embedding function (degree-only)"""
    print("\n" + "="*60)
    print("TEST 6: Degree-Only Mode (No Embedding Function)")
    print("="*60)
    
    from hypergraphrag.retrieval import LiteRetriever
    
    graph = MockGraphStorage()
    vdb = MockVectorStorage()
    
    # Initialize without embedding function
    config = {
        "cache_size": 100,
        "degree_weight": 1.0,
        "coherence_weight": 0.0,
        "similarity_weight": 0.8,
        "quality_weight": 0.2,
        "embedding_func": None  # No embedding function
    }
    
    retriever = LiteRetriever(graph, vdb, config)
    
    query = "What is the treatment for disease X?"
    results = await retriever.retrieve(query, top_k=3)
    
    print(f"\nQuery: {query}")
    print(f"Retrieved {len(results)} results (degree-only mode):\n")
    
    for i, result in enumerate(results, 1):
        print(f"{i}. {result['hyperedge_name']}: quality={result['simple_quality']:.3f}")
    
    assert len(results) > 0, "Should retrieve results without embedding function"
    
    print("\n✓ Degree-only mode test passed")


async def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("LITE RETRIEVER TEST SUITE")
    print("="*60)
    
    try:
        # Test 1: Basic retrieval
        retriever = await test_basic_retrieval()
        
        # Test 2: Caching
        await test_caching(retriever)
        
        # Test 3: Quality scoring
        await test_quality_scoring(retriever)
        
        # Test 4: Weight adjustment
        await test_weight_adjustment(retriever)
        
        # Test 5: Performance metrics
        await test_performance_metrics(retriever)
        
        # Test 6: No embedding function
        await test_no_embedding_func()
        
        print("\n" + "="*60)
        print("ALL TESTS PASSED ✓")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
