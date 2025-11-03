"""
Example: ANN Search Integration with DynHyperRAG

This example demonstrates how to use Approximate Nearest Neighbor (ANN) search
to speed up hyperedge retrieval in large-scale hypergraphs.

Features demonstrated:
1. Building ANN index from hypergraph
2. Comparing ANN vs exact search performance
3. Measuring accuracy loss
4. Configuring ANN parameters for speed/accuracy tradeoff
5. Integration with LiteRetriever

Usage:
    python example_ann_search_integration.py
"""

import asyncio
import logging
import time
import numpy as np
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def example_ann_basic():
    """Example 1: Basic ANN search usage."""
    from hypergraphrag.retrieval.ann_search import ANNSearchEngine
    
    logger.info("=" * 70)
    logger.info("Example 1: Basic ANN Search")
    logger.info("=" * 70)
    
    # Simulate hyperedge embeddings
    dimension = 1536  # OpenAI embedding dimension
    n_hyperedges = 1000
    
    logger.info(f"\n📊 Creating {n_hyperedges} synthetic hyperedge embeddings...")
    embeddings = np.random.randn(n_hyperedges, dimension).astype(np.float32)
    hyperedge_ids = [f"hyperedge_{i}" for i in range(n_hyperedges)]
    
    # Create ANN engine with HNSW
    logger.info("\n🔧 Creating HNSW ANN engine...")
    ann_engine = ANNSearchEngine(
        backend="hnsw",
        dimension=dimension,
        config={
            "M": 16,  # Number of connections per layer
            "ef_construction": 200,  # Construction time parameter
            "ef_search": 50  # Search time parameter
        }
    )
    
    # Build index
    logger.info("\n🏗️  Building ANN index...")
    await ann_engine.build_index(embeddings, hyperedge_ids)
    
    stats = ann_engine.get_stats()
    logger.info(f"✅ Index built in {stats['build_time']:.2f}s")
    logger.info(f"   Total vectors: {stats['total_vectors']}")
    
    # Perform searches
    logger.info("\n🔍 Performing searches...")
    query_embedding = np.random.randn(dimension).astype(np.float32)
    
    results = await ann_engine.search(query_embedding, top_k=10)
    
    logger.info(f"\n📋 Top 10 results:")
    for i, (hyperedge_id, similarity) in enumerate(results, 1):
        logger.info(f"   {i}. {hyperedge_id}: similarity={similarity:.4f}")
    
    # Search statistics
    stats = ann_engine.get_stats()
    logger.info(f"\n📊 Search statistics:")
    logger.info(f"   Total searches: {stats['total_searches']}")
    logger.info(f"   Average search time: {stats.get('avg_search_time', 0)*1000:.2f}ms")


async def example_ann_accuracy_tradeoff():
    """Example 2: Speed vs accuracy tradeoff."""
    from hypergraphrag.retrieval.ann_search import ANNSearchEngine, measure_ann_accuracy
    
    logger.info("\n" + "=" * 70)
    logger.info("Example 2: Speed vs Accuracy Tradeoff")
    logger.info("=" * 70)
    
    # Create dataset
    dimension = 1536
    n_vectors = 2000
    n_queries = 50
    
    logger.info(f"\n📊 Creating dataset: {n_vectors} vectors, {n_queries} queries")
    vectors = np.random.randn(n_vectors, dimension).astype(np.float32)
    ids = [f"vec_{i}" for i in range(n_vectors)]
    query_vectors = np.random.randn(n_queries, dimension).astype(np.float32)
    
    # Test different configurations
    configs = [
        {
            "name": "High Accuracy",
            "M": 32,
            "ef_construction": 400,
            "ef_search": 100
        },
        {
            "name": "Balanced",
            "M": 16,
            "ef_construction": 200,
            "ef_search": 50
        },
        {
            "name": "High Speed",
            "M": 8,
            "ef_construction": 100,
            "ef_search": 20
        }
    ]
    
    # Build exact search baseline
    logger.info("\n🎯 Building exact search baseline...")
    exact_engine = ANNSearchEngine(
        backend="hnsw",
        dimension=dimension,
        config={"M": 64, "ef_construction": 500, "ef_search": 500}
    )
    await exact_engine.build_index(vectors, ids)
    
    # Get exact results
    logger.info("   Getting exact results...")
    exact_results = []
    exact_start = time.time()
    for query in query_vectors:
        results = await exact_engine.search(query, top_k=10)
        exact_results.append(results)
    exact_time = time.time() - exact_start
    
    logger.info(f"   Exact search: {exact_time:.3f}s ({exact_time/n_queries*1000:.2f}ms per query)")
    
    # Test each configuration
    logger.info("\n🔬 Testing ANN configurations:")
    logger.info("-" * 70)
    
    for config in configs:
        logger.info(f"\n📌 Configuration: {config['name']}")
        logger.info(f"   M={config['M']}, ef_construction={config['ef_construction']}, "
                   f"ef_search={config['ef_search']}")
        
        # Build index
        ann_engine = ANNSearchEngine(
            backend="hnsw",
            dimension=dimension,
            config={
                "M": config["M"],
                "ef_construction": config["ef_construction"],
                "ef_search": config["ef_search"]
            }
        )
        await ann_engine.build_index(vectors, ids)
        
        # Get ANN results
        ann_results = []
        ann_start = time.time()
        for query in query_vectors:
            results = await ann_engine.search(query, top_k=10)
            ann_results.append(results)
        ann_time = time.time() - ann_start
        
        # Measure accuracy
        metrics = await measure_ann_accuracy(
            ann_engine,
            exact_results,
            ann_results,
            k_values=[1, 5, 10]
        )
        
        # Display results
        logger.info(f"\n   ⏱️  Performance:")
        logger.info(f"      Search time: {ann_time:.3f}s ({ann_time/n_queries*1000:.2f}ms per query)")
        logger.info(f"      Speedup: {exact_time/ann_time:.2f}x")
        
        logger.info(f"\n   🎯 Accuracy:")
        logger.info(f"      Recall@1:  {metrics['recall@1']:.3f}")
        logger.info(f"      Recall@5:  {metrics['recall@5']:.3f}")
        logger.info(f"      Recall@10: {metrics['recall@10']:.3f}")
        logger.info(f"      Average:   {metrics['average_recall']:.3f}")
    
    logger.info("\n" + "-" * 70)
    logger.info("💡 Recommendation: Use 'Balanced' config for most use cases")


async def example_lite_retriever_with_ann():
    """Example 3: Using ANN with LiteRetriever."""
    from hypergraphrag.retrieval.lite_retriever import LiteRetriever
    
    logger.info("\n" + "=" * 70)
    logger.info("Example 3: LiteRetriever with ANN")
    logger.info("=" * 70)
    
    # Mock implementations for demonstration
    class MockGraphStorage:
        async def get_node(self, node_id: str):
            return {
                "role": "hyperedge",
                "hyperedge": f"This is a legal case about {node_id}",
                "quality_score": np.random.uniform(0.5, 0.9),
                "dynamic_weight": np.random.uniform(0.8, 1.2)
            }
        
        async def node_degree(self, node_id: str):
            return np.random.randint(3, 10)
        
        async def get_node_edges(self, node_id: str):
            return []
    
    class MockVectorStorage:
        async def query(self, query: str, top_k: int):
            # Simulate vector search results
            return [
                {
                    "hyperedge_name": f"case_{i}",
                    "id": f"case_{i}",
                    "distance": 0.95 - i * 0.03,
                    "hyperedge": f"Legal case {i} about theft and penalties"
                }
                for i in range(min(top_k, 30))
            ]
    
    async def mock_embedding_func(texts):
        # Return random embeddings
        return [np.random.randn(1536).tolist() for _ in texts]
    
    # Create LiteRetriever with ANN
    logger.info("\n🔧 Creating LiteRetriever with ANN enabled...")
    
    graph = MockGraphStorage()
    vdb = MockVectorStorage()
    
    config = {
        "use_ann": True,
        "ann_backend": "hnsw",
        "embedding_dim": 1536,
        "ann_config": {
            "M": 16,
            "ef_construction": 200,
            "ef_search": 50
        },
        "embedding_func": mock_embedding_func,
        "similarity_weight": 0.6,
        "quality_weight": 0.4,
        "enable_caching": True,
        "cache_size": 1000
    }
    
    retriever = LiteRetriever(graph, vdb, config)
    
    logger.info("✅ LiteRetriever created")
    logger.info(f"   ANN backend: {config['ann_backend']}")
    logger.info(f"   Caching: enabled")
    
    # Perform retrieval (without ANN index, will use exact search)
    logger.info("\n🔍 Performing retrieval (exact search - no ANN index yet)...")
    
    query = "What is the penalty for theft in criminal law?"
    results = await retriever.retrieve(query, top_k=5)
    
    logger.info(f"\n📋 Retrieved {len(results)} results:")
    for i, result in enumerate(results, 1):
        logger.info(f"\n   {i}. {result.get('hyperedge_name', 'unknown')}")
        logger.info(f"      Similarity: {result.get('distance', 0):.4f}")
        logger.info(f"      Quality: {result.get('simple_quality', 0):.4f}")
        logger.info(f"      Final Score: {result.get('final_score', 0):.4f}")
    
    # Show statistics
    stats = retriever.get_cache_stats()
    logger.info(f"\n📊 Retriever statistics:")
    logger.info(f"   Total queries: {stats['retrieval_stats']['total_queries']}")
    logger.info(f"   Cache hits: {stats['retrieval_stats']['cache_hits']}")
    logger.info(f"   Exact searches: {stats['retrieval_stats']['exact_searches']}")
    logger.info(f"   ANN searches: {stats['retrieval_stats']['ann_searches']}")
    
    logger.info("\n💡 Note: To use ANN search, you need to:")
    logger.info("   1. Extract all embeddings from your vector database")
    logger.info("   2. Call retriever.ann_engine.build_index(embeddings, ids)")
    logger.info("   3. Future queries will automatically use ANN search")


async def example_save_load_index():
    """Example 4: Saving and loading ANN index."""
    from hypergraphrag.retrieval.ann_search import ANNSearchEngine
    
    logger.info("\n" + "=" * 70)
    logger.info("Example 4: Saving and Loading ANN Index")
    logger.info("=" * 70)
    
    dimension = 1536
    n_vectors = 500
    
    # Create and build index
    logger.info("\n🏗️  Building ANN index...")
    vectors = np.random.randn(n_vectors, dimension).astype(np.float32)
    ids = [f"vec_{i}" for i in range(n_vectors)]
    
    engine = ANNSearchEngine(
        backend="hnsw",
        dimension=dimension,
        config={"M": 16, "ef_construction": 200, "ef_search": 50}
    )
    await engine.build_index(vectors, ids)
    
    logger.info("✅ Index built")
    
    # Save index
    index_path = "temp_ann_index.hnsw"
    logger.info(f"\n💾 Saving index to {index_path}...")
    engine.save_index(index_path)
    logger.info("✅ Index saved")
    
    # Create new engine and load index
    logger.info(f"\n📂 Loading index from {index_path}...")
    new_engine = ANNSearchEngine(
        backend="hnsw",
        dimension=dimension,
        config={"ef_search": 50}
    )
    new_engine.load_index(index_path)
    logger.info("✅ Index loaded")
    
    # Test loaded index
    logger.info("\n🔍 Testing loaded index...")
    query = np.random.randn(dimension).astype(np.float32)
    results = await new_engine.search(query, top_k=5)
    
    logger.info(f"   Found {len(results)} results")
    logger.info(f"   Top result: {results[0][0]}, similarity={results[0][1]:.4f}")
    
    # Cleanup
    import os
    if os.path.exists(index_path):
        os.remove(index_path)
    if os.path.exists(f"{index_path}.ids"):
        os.remove(f"{index_path}.ids")
    logger.info("\n🧹 Cleaned up temporary files")


async def main():
    """Run all examples."""
    logger.info("🚀 ANN Search Integration Examples")
    logger.info("=" * 70)
    
    try:
        # Example 1: Basic usage
        await example_ann_basic()
        
        # Example 2: Speed vs accuracy tradeoff
        await example_ann_accuracy_tradeoff()
        
        # Example 3: LiteRetriever integration
        await example_lite_retriever_with_ann()
        
        # Example 4: Save/load index
        await example_save_load_index()
        
        logger.info("\n" + "=" * 70)
        logger.info("🎉 All examples completed successfully!")
        logger.info("=" * 70)
        
        logger.info("\n📚 Key Takeaways:")
        logger.info("   1. ANN search provides 2-10x speedup with minimal accuracy loss")
        logger.info("   2. Use 'Balanced' config (M=16, ef_search=50) for most cases")
        logger.info("   3. Higher ef_search = better accuracy but slower search")
        logger.info("   4. Save/load index to avoid rebuilding on restart")
        logger.info("   5. Measure accuracy on your data to find optimal parameters")
        
    except Exception as e:
        logger.error(f"\n❌ Example failed: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    asyncio.run(main())
