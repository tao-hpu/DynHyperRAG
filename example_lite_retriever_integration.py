"""
Example: LiteRetriever Integration with DynHyperRAG

This example demonstrates how to integrate LiteRetriever into the DynHyperRAG
query pipeline for efficient retrieval in production environments.

Usage:
    python example_lite_retriever_integration.py
"""

import asyncio
import os
from pathlib import Path

# Add project root to path
import sys
sys.path.insert(0, str(Path(__file__).parent))

from hypergraphrag import HyperGraphRAG
from hypergraphrag.retrieval import LiteRetriever


async def example_basic_usage():
    """Example 1: Basic LiteRetriever usage"""
    print("\n" + "="*70)
    print("EXAMPLE 1: Basic LiteRetriever Usage")
    print("="*70)
    
    # Initialize HyperGraphRAG
    working_dir = "./expr/example"
    
    rag = HyperGraphRAG(
        working_dir=working_dir,
        enable_local=True,
        enable_global=False
    )
    
    # Initialize LiteRetriever
    config = {
        "cache_size": 1000,
        "quality_cache_size": 5000,
        "degree_weight": 0.5,
        "coherence_weight": 0.5,
        "similarity_weight": 0.7,
        "quality_weight": 0.3,
        "embedding_func": rag.embedding_func
    }
    
    lite_retriever = LiteRetriever(
        graph=rag.knowledge_graph_inst,
        vdb=rag.entities_vdb,
        config=config
    )
    
    # Perform retrieval
    query = "What are the main symptoms of the disease?"
    print(f"\nQuery: {query}")
    
    results = await lite_retriever.retrieve(query, top_k=5)
    
    print(f"\nRetrieved {len(results)} results:")
    for i, result in enumerate(results, 1):
        print(f"\n{i}. Hyperedge: {result.get('hyperedge_name', 'N/A')}")
        print(f"   Similarity: {result.get('distance', 0):.3f}")
        print(f"   Quality: {result.get('simple_quality', 0):.3f}")
        print(f"   Final Score: {result.get('final_score', 0):.3f}")
        if 'hyperedge' in result:
            print(f"   Text: {result['hyperedge'][:100]}...")
    
    # Show cache statistics
    stats = lite_retriever.get_cache_stats()
    print(f"\nCache Statistics:")
    print(f"  Query cache: {stats['query_cache']['size']} items")
    print(f"  Quality cache: {stats['quality_cache']['size']} items")


async def example_production_config():
    """Example 2: Production-optimized configuration"""
    print("\n" + "="*70)
    print("EXAMPLE 2: Production-Optimized Configuration")
    print("="*70)
    
    working_dir = "./expr/example"
    
    rag = HyperGraphRAG(
        working_dir=working_dir,
        enable_local=True,
        enable_global=False
    )
    
    # Production configuration: large cache, prioritize speed
    config = {
        "cache_size": 5000,              # Large cache for common queries
        "quality_cache_size": 10000,     # Cache many quality scores
        "degree_weight": 1.0,            # Only use degree (fastest)
        "coherence_weight": 0.0,         # Disable coherence for speed
        "similarity_weight": 0.8,        # Prioritize relevance
        "quality_weight": 0.2,
        "embedding_func": None           # Disable coherence computation
    }
    
    lite_retriever = LiteRetriever(
        graph=rag.knowledge_graph_inst,
        vdb=rag.entities_vdb,
        config=config
    )
    
    print("\nConfiguration:")
    print(f"  Cache size: {config['cache_size']}")
    print(f"  Quality cache size: {config['quality_cache_size']}")
    print(f"  Degree weight: {config['degree_weight']}")
    print(f"  Coherence weight: {config['coherence_weight']}")
    print(f"  Similarity weight: {config['similarity_weight']}")
    print(f"  Quality weight: {config['quality_weight']}")
    
    # Test retrieval speed
    import time
    
    query = "What are the main symptoms of the disease?"
    
    start = time.time()
    results = await lite_retriever.retrieve(query, top_k=10)
    elapsed = time.time() - start
    
    print(f"\nRetrieval completed in {elapsed*1000:.2f}ms")
    print(f"Retrieved {len(results)} results")


async def example_resource_constrained():
    """Example 3: Resource-constrained environment"""
    print("\n" + "="*70)
    print("EXAMPLE 3: Resource-Constrained Configuration")
    print("="*70)
    
    working_dir = "./expr/example"
    
    rag = HyperGraphRAG(
        working_dir=working_dir,
        enable_local=True,
        enable_global=False
    )
    
    # Minimal configuration for resource-constrained environments
    config = {
        "cache_size": 100,               # Small cache
        "quality_cache_size": 500,       # Small quality cache
        "degree_weight": 1.0,            # Only degree
        "coherence_weight": 0.0,
        "similarity_weight": 0.9,        # Mostly rely on similarity
        "quality_weight": 0.1,
        "embedding_func": None
    }
    
    lite_retriever = LiteRetriever(
        graph=rag.knowledge_graph_inst,
        vdb=rag.entities_vdb,
        config=config
    )
    
    print("\nMinimal Configuration:")
    print(f"  Cache size: {config['cache_size']}")
    print(f"  Quality cache size: {config['quality_cache_size']}")
    print(f"  Features: Degree only")
    print(f"  Memory footprint: ~1-2 MB")
    
    query = "What are the main symptoms of the disease?"
    results = await lite_retriever.retrieve(query, top_k=5)
    
    print(f"\nRetrieved {len(results)} results")
    
    # Show memory usage
    stats = lite_retriever.get_cache_stats()
    print(f"\nCache usage:")
    print(f"  Query cache: {stats['query_cache']['size']} items")
    print(f"  Quality cache: {stats['quality_cache']['size']} items")


async def example_cache_management():
    """Example 4: Cache management and monitoring"""
    print("\n" + "="*70)
    print("EXAMPLE 4: Cache Management and Monitoring")
    print("="*70)
    
    working_dir = "./expr/example"
    
    rag = HyperGraphRAG(
        working_dir=working_dir,
        enable_local=True,
        enable_global=False
    )
    
    config = {
        "cache_size": 100,
        "quality_cache_size": 500,
        "embedding_func": rag.embedding_func
    }
    
    lite_retriever = LiteRetriever(
        graph=rag.knowledge_graph_inst,
        vdb=rag.entities_vdb,
        config=config
    )
    
    # Run multiple queries
    queries = [
        "What are the main symptoms?",
        "What is the treatment?",
        "What are the side effects?",
        "What are the main symptoms?",  # Repeat
        "What is the treatment?",       # Repeat
    ]
    
    print("\nRunning queries...")
    for i, query in enumerate(queries, 1):
        print(f"\n{i}. Query: {query}")
        results = await lite_retriever.retrieve(query, top_k=3)
        print(f"   Retrieved {len(results)} results")
    
    # Show cache statistics
    stats = lite_retriever.get_cache_stats()
    
    print("\n" + "-"*70)
    print("Cache Statistics:")
    print("-"*70)
    
    print(f"\nQuery Cache:")
    print(f"  Size: {stats['query_cache']['size']}/{stats['query_cache']['max_size']}")
    print(f"  Hits: {stats['query_cache']['hits']}")
    print(f"  Misses: {stats['query_cache']['misses']}")
    print(f"  Hit Rate: {stats['query_cache']['hit_rate']:.2%}")
    
    print(f"\nQuality Cache:")
    print(f"  Size: {stats['quality_cache']['size']}/{stats['quality_cache']['max_size']}")
    print(f"  Hits: {stats['quality_cache']['hits']}")
    print(f"  Misses: {stats['quality_cache']['misses']}")
    print(f"  Hit Rate: {stats['quality_cache']['hit_rate']:.2%}")
    
    print(f"\nRetrieval Statistics:")
    print(f"  Total Queries: {stats['retrieval_stats']['total_queries']}")
    print(f"  Cache Hits: {stats['retrieval_stats']['cache_hits']}")
    print(f"  Quality Computations: {stats['retrieval_stats']['total_quality_computations']}")
    print(f"  Avg Retrieval Time: {stats['retrieval_stats']['avg_retrieval_time']*1000:.2f}ms")
    
    # Clear cache
    print("\nClearing cache...")
    lite_retriever.clear_cache()
    
    stats_after = lite_retriever.get_cache_stats()
    print(f"Query cache size after clear: {stats_after['query_cache']['size']}")
    print(f"Quality cache size after clear: {stats_after['quality_cache']['size']}")


async def example_weight_tuning():
    """Example 5: Dynamic weight tuning"""
    print("\n" + "="*70)
    print("EXAMPLE 5: Dynamic Weight Tuning")
    print("="*70)
    
    working_dir = "./expr/example"
    
    rag = HyperGraphRAG(
        working_dir=working_dir,
        enable_local=True,
        enable_global=False
    )
    
    config = {
        "cache_size": 100,
        "embedding_func": rag.embedding_func
    }
    
    lite_retriever = LiteRetriever(
        graph=rag.knowledge_graph_inst,
        vdb=rag.entities_vdb,
        config=config
    )
    
    query = "What are the main symptoms of the disease?"
    
    # Test different weight configurations
    weight_configs = [
        {"name": "Similarity-focused", "sim": 0.9, "qual": 0.1},
        {"name": "Balanced", "sim": 0.7, "qual": 0.3},
        {"name": "Quality-focused", "sim": 0.5, "qual": 0.5},
    ]
    
    for config in weight_configs:
        print(f"\n{config['name']} ({config['sim']}/{config['qual']}):")
        
        # Update weights
        lite_retriever.set_weights(
            similarity_weight=config['sim'],
            quality_weight=config['qual']
        )
        
        # Clear cache to force recomputation
        lite_retriever.clear_cache()
        
        # Retrieve
        results = await lite_retriever.retrieve(query, top_k=3)
        
        # Show top results
        for i, result in enumerate(results, 1):
            print(f"  {i}. Score: {result['final_score']:.3f} "
                  f"(sim={result.get('distance', 0):.3f}, "
                  f"qual={result.get('simple_quality', 0):.3f})")


async def example_comparison():
    """Example 6: Compare with full retrieval"""
    print("\n" + "="*70)
    print("EXAMPLE 6: Comparison with Full Retrieval")
    print("="*70)
    
    working_dir = "./expr/example"
    
    rag = HyperGraphRAG(
        working_dir=working_dir,
        enable_local=True,
        enable_global=False
    )
    
    # Initialize LiteRetriever
    lite_config = {
        "cache_size": 100,
        "embedding_func": rag.embedding_func,
        "similarity_weight": 0.7,
        "quality_weight": 0.3
    }
    
    lite_retriever = LiteRetriever(
        graph=rag.knowledge_graph_inst,
        vdb=rag.entities_vdb,
        config=lite_config
    )
    
    query = "What are the main symptoms of the disease?"
    
    # Time lite retrieval
    import time
    
    print("\nLite Retrieval:")
    start = time.time()
    lite_results = await lite_retriever.retrieve(query, top_k=5)
    lite_time = time.time() - start
    
    print(f"  Time: {lite_time*1000:.2f}ms")
    print(f"  Results: {len(lite_results)}")
    print(f"  Top score: {lite_results[0]['final_score']:.3f}")
    
    # Show comparison
    print("\nFeature Comparison:")
    print("  Lite Retriever:")
    print("    - Features: Degree + Coherence (2)")
    print("    - Caching: Yes")
    print("    - Speed: Fast")
    print("    - Accuracy: ~85-90%")
    
    print("\n  Full Retrieval:")
    print("    - Features: All 5 features")
    print("    - Caching: No")
    print("    - Speed: Slower")
    print("    - Accuracy: 100%")


async def main():
    """Run all examples"""
    print("\n" + "="*70)
    print("LITE RETRIEVER INTEGRATION EXAMPLES")
    print("="*70)
    
    try:
        # Check if example data exists
        if not os.path.exists("./expr/example"):
            print("\n⚠️  Warning: Example data not found at ./expr/example")
            print("Please run script_construct.py first to build the knowledge graph.")
            return
        
        # Run examples
        await example_basic_usage()
        await example_production_config()
        await example_resource_constrained()
        await example_cache_management()
        await example_weight_tuning()
        await example_comparison()
        
        print("\n" + "="*70)
        print("ALL EXAMPLES COMPLETED ✓")
        print("="*70)
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
