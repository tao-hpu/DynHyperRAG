"""
Performance Comparison Test: Full vs Lite Retriever

This script compares the performance of the full DynHyperRAG retrieval system
(with complete quality assessment) against the lightweight LiteRetriever variant.

Metrics measured:
- Accuracy: Precision@K, Recall@K, MRR
- Speed: Average retrieval time, throughput
- Memory: Peak memory usage
- Resource efficiency: Quality computations, cache efficiency

Requirements: 3.3
"""

import asyncio
import sys
import time
import psutil
import json
from typing import List, Dict, Tuple
from collections import defaultdict
import numpy as np

# Mock implementations for testing
class MockGraphStorage:
    """Mock graph storage with realistic data"""
    
    def __init__(self, num_hyperedges: int = 100):
        self.nodes = {}
        self.edges = {}
        
        # Generate mock hyperedges
        for i in range(num_hyperedges):
            he_id = f"he{i}"
            self.nodes[he_id] = {
                "role": "hyperedge",
                "hyperedge": f"Hyperedge {i} content with entities",
                "weight": 50 + (i % 50),
                "quality_score": 0.3 + (i % 7) * 0.1,
                "dynamic_weight": 0.4 + (i % 6) * 0.1
            }
            
            # Create 2-4 entity connections
            num_entities = 2 + (i % 3)
            self.edges[he_id] = [
                (he_id, f"entity{i}_{j}") for j in range(num_entities)
            ]
        
        # Generate mock entities
        for i in range(num_hyperedges):
            num_entities = 2 + (i % 3)
            for j in range(num_entities):
                entity_id = f"entity{i}_{j}"
                self.nodes[entity_id] = {
                    "role": "entity",
                    "entity_name": f"Entity {i}_{j}",
                    "entity_type": ["disease", "medication", "symptom"][j % 3],
                    "description": f"Description for entity {i}_{j}"
                }
    
    async def get_node(self, node_id: str):
        return self.nodes.get(node_id)
    
    async def get_node_edges(self, node_id: str):
        return self.edges.get(node_id, [])
    
    async def node_degree(self, node_id: str):
        return len(self.edges.get(node_id, []))


class MockVectorStorage:
    """Mock vector storage with realistic retrieval"""
    
    def __init__(self, num_hyperedges: int = 100):
        self.num_hyperedges = num_hyperedges
    
    async def query(self, query: str, top_k: int) -> List[dict]:
        # Simulate retrieval with varying similarity scores
        results = []
        for i in range(min(top_k, self.num_hyperedges)):
            # Simulate decreasing similarity
            similarity = 0.95 - (i * 0.05)
            results.append({
                "hyperedge_name": f"he{i}",
                "hyperedge": f"Hyperedge {i} content with entities",
                "distance": max(0.1, similarity),
                "weight": 50 + (i % 50),
                "quality_score": 0.3 + (i % 7) * 0.1,
                "dynamic_weight": 0.4 + (i % 6) * 0.1
            })
        return results


async def mock_embedding_func(texts: List[str]):
    """Mock embedding function"""
    # Simulate embedding computation time
    await asyncio.sleep(0.001 * len(texts))
    return [np.random.rand(384) for _ in texts]


class PerformanceMetrics:
    """Track and compute performance metrics"""
    
    def __init__(self):
        self.retrieval_times = []
        self.memory_usage = []
        self.quality_computations = 0
        self.cache_hits = 0
        self.cache_misses = 0
    
    def record_retrieval(self, time_ms: float, memory_mb: float):
        self.retrieval_times.append(time_ms)
        self.memory_usage.append(memory_mb)
    
    def get_summary(self) -> Dict:
        if not self.retrieval_times:
            return {}
        
        return {
            "avg_time_ms": np.mean(self.retrieval_times),
            "median_time_ms": np.median(self.retrieval_times),
            "p95_time_ms": np.percentile(self.retrieval_times, 95),
            "min_time_ms": np.min(self.retrieval_times),
            "max_time_ms": np.max(self.retrieval_times),
            "std_time_ms": np.std(self.retrieval_times),
            "avg_memory_mb": np.mean(self.memory_usage),
            "peak_memory_mb": np.max(self.memory_usage),
            "quality_computations": self.quality_computations,
            "cache_hit_rate": self.cache_hits / (self.cache_hits + self.cache_misses) 
                              if (self.cache_hits + self.cache_misses) > 0 else 0
        }


def compute_accuracy_metrics(
    retrieved: List[List[str]],
    ground_truth: List[List[str]]
) -> Dict:
    """
    Compute accuracy metrics.
    
    Args:
        retrieved: List of retrieved hyperedge ID lists for each query
        ground_truth: List of relevant hyperedge ID lists for each query
    
    Returns:
        Dict with precision@k, recall@k, MRR
    """
    metrics = {}
    
    # Precision@K and Recall@K
    for k in [1, 5, 10]:
        precisions = []
        recalls = []
        
        for ret, truth in zip(retrieved, ground_truth):
            ret_k = set(ret[:k])
            truth_set = set(truth)
            
            if len(ret_k) > 0:
                precision = len(ret_k & truth_set) / len(ret_k)
                precisions.append(precision)
            
            if len(truth_set) > 0:
                recall = len(ret_k & truth_set) / len(truth_set)
                recalls.append(recall)
        
        metrics[f"precision@{k}"] = np.mean(precisions) if precisions else 0.0
        metrics[f"recall@{k}"] = np.mean(recalls) if recalls else 0.0
    
    # Mean Reciprocal Rank (MRR)
    reciprocal_ranks = []
    for ret, truth in zip(retrieved, ground_truth):
        truth_set = set(truth)
        for i, item in enumerate(ret):
            if item in truth_set:
                reciprocal_ranks.append(1.0 / (i + 1))
                break
        else:
            reciprocal_ranks.append(0.0)
    
    metrics["mrr"] = np.mean(reciprocal_ranks) if reciprocal_ranks else 0.0
    
    return metrics


async def test_full_retriever(
    graph: MockGraphStorage,
    vdb: MockVectorStorage,
    queries: List[str],
    top_k: int = 10
) -> Tuple[List[List[str]], PerformanceMetrics]:
    """
    Test full retriever with complete quality assessment.
    """
    from hypergraphrag.retrieval.quality_ranker import QualityAwareRanker
    
    print("\n" + "="*60)
    print("Testing FULL Retriever (Complete Quality Assessment)")
    print("="*60)
    
    # Initialize ranker
    config = {
        "similarity_weight": 0.5,
        "quality_weight": 0.3,
        "dynamic_weight": 0.2,
        "provide_explanation": False
    }
    ranker = QualityAwareRanker(config)
    
    metrics = PerformanceMetrics()
    all_results = []
    
    process = psutil.Process()
    
    for i, query in enumerate(queries):
        # Get memory before
        mem_before = process.memory_info().rss / 1024 / 1024
        
        # Time retrieval
        start = time.time()
        
        # Vector retrieval
        vector_results = await vdb.query(query, top_k=top_k * 2)
        
        # Quality-aware ranking
        ranked_results = await ranker.rank_hyperedges(query, vector_results)
        ranked_results = ranked_results[:top_k]
        
        elapsed = (time.time() - start) * 1000  # ms
        
        # Get memory after
        mem_after = process.memory_info().rss / 1024 / 1024
        
        # Record metrics
        metrics.record_retrieval(elapsed, mem_after)
        
        # Extract IDs
        result_ids = [r.get("hyperedge_name") or r.get("id") for r in ranked_results]
        all_results.append(result_ids)
        
        if (i + 1) % 10 == 0:
            print(f"  Processed {i+1}/{len(queries)} queries...")
    
    print(f"\n✓ Completed {len(queries)} queries")
    
    return all_results, metrics


async def test_lite_retriever(
    graph: MockGraphStorage,
    vdb: MockVectorStorage,
    queries: List[str],
    top_k: int = 10,
    enable_caching: bool = True
) -> Tuple[List[List[str]], PerformanceMetrics]:
    """
    Test lite retriever with simplified quality assessment.
    """
    from hypergraphrag.retrieval.lite_retriever import LiteRetriever
    
    print("\n" + "="*60)
    print(f"Testing LITE Retriever (Simplified, caching={'ON' if enable_caching else 'OFF'})")
    print("="*60)
    
    # Initialize lite retriever
    config = {
        "cache_size": 1000,
        "quality_cache_size": 5000,
        "degree_weight": 0.5,
        "coherence_weight": 0.5,
        "similarity_weight": 0.7,
        "quality_weight": 0.3,
        "embedding_func": mock_embedding_func,
        "enable_caching": enable_caching
    }
    retriever = LiteRetriever(graph, vdb, config)
    
    metrics = PerformanceMetrics()
    all_results = []
    
    process = psutil.Process()
    
    for i, query in enumerate(queries):
        # Get memory before
        mem_before = process.memory_info().rss / 1024 / 1024
        
        # Time retrieval
        start = time.time()
        
        # Lite retrieval
        results = await retriever.retrieve(query, top_k=top_k, use_cache=enable_caching)
        
        elapsed = (time.time() - start) * 1000  # ms
        
        # Get memory after
        mem_after = process.memory_info().rss / 1024 / 1024
        
        # Record metrics
        metrics.record_retrieval(elapsed, mem_after)
        
        # Extract IDs
        result_ids = [r.get("hyperedge_name") or r.get("id") for r in results]
        all_results.append(result_ids)
        
        if (i + 1) % 10 == 0:
            print(f"  Processed {i+1}/{len(queries)} queries...")
    
    # Get cache stats
    cache_stats = retriever.get_cache_stats()
    metrics.cache_hits = cache_stats["query_cache"]["hits"] if cache_stats["query_cache"] else 0
    metrics.cache_misses = cache_stats["query_cache"]["misses"] if cache_stats["query_cache"] else 0
    metrics.quality_computations = cache_stats["retrieval_stats"]["total_quality_computations"]
    
    print(f"\n✓ Completed {len(queries)} queries")
    print(f"  Cache hit rate: {metrics.cache_hits / (metrics.cache_hits + metrics.cache_misses):.2%}" 
          if (metrics.cache_hits + metrics.cache_misses) > 0 else "  No cache")
    
    return all_results, metrics


def generate_test_queries(num_queries: int = 50) -> Tuple[List[str], List[List[str]]]:
    """
    Generate test queries and ground truth.
    
    Returns:
        Tuple of (queries, ground_truth_ids)
    """
    queries = []
    ground_truth = []
    
    for i in range(num_queries):
        # Generate query
        query_type = i % 3
        if query_type == 0:
            query = f"What is the treatment for disease {i}?"
        elif query_type == 1:
            query = f"What are the symptoms of condition {i}?"
        else:
            query = f"What are the side effects of medication {i}?"
        
        queries.append(query)
        
        # Generate ground truth (relevant hyperedges)
        # For simplicity, assume first 5 hyperedges are relevant
        truth = [f"he{j}" for j in range(5)]
        ground_truth.append(truth)
    
    return queries, ground_truth


def print_comparison_table(full_metrics: Dict, lite_metrics: Dict, lite_nocache_metrics: Dict):
    """Print formatted comparison table"""
    print("\n" + "="*80)
    print("PERFORMANCE COMPARISON TABLE")
    print("="*80)
    print(f"{'Metric':<30} {'Full':<15} {'Lite (cache)':<15} {'Lite (no cache)':<15} {'Speedup':<10}")
    print("-"*80)
    
    # Time metrics
    print(f"{'Avg Time (ms)':<30} {full_metrics['avg_time_ms']:>14.2f} "
          f"{lite_metrics['avg_time_ms']:>14.2f} {lite_nocache_metrics['avg_time_ms']:>14.2f} "
          f"{full_metrics['avg_time_ms']/lite_metrics['avg_time_ms']:>9.2f}x")
    
    print(f"{'Median Time (ms)':<30} {full_metrics['median_time_ms']:>14.2f} "
          f"{lite_metrics['median_time_ms']:>14.2f} {lite_nocache_metrics['median_time_ms']:>14.2f} "
          f"{full_metrics['median_time_ms']/lite_metrics['median_time_ms']:>9.2f}x")
    
    print(f"{'P95 Time (ms)':<30} {full_metrics['p95_time_ms']:>14.2f} "
          f"{lite_metrics['p95_time_ms']:>14.2f} {lite_nocache_metrics['p95_time_ms']:>14.2f} "
          f"{full_metrics['p95_time_ms']/lite_metrics['p95_time_ms']:>9.2f}x")
    
    # Memory metrics
    print(f"{'Avg Memory (MB)':<30} {full_metrics['avg_memory_mb']:>14.2f} "
          f"{lite_metrics['avg_memory_mb']:>14.2f} {lite_nocache_metrics['avg_memory_mb']:>14.2f} "
          f"{full_metrics['avg_memory_mb']/lite_metrics['avg_memory_mb']:>9.2f}x")
    
    print(f"{'Peak Memory (MB)':<30} {full_metrics['peak_memory_mb']:>14.2f} "
          f"{lite_metrics['peak_memory_mb']:>14.2f} {lite_nocache_metrics['peak_memory_mb']:>14.2f} "
          f"{full_metrics['peak_memory_mb']/lite_metrics['peak_memory_mb']:>9.2f}x")
    
    # Resource metrics
    print(f"{'Quality Computations':<30} {full_metrics['quality_computations']:>14} "
          f"{lite_metrics['quality_computations']:>14} {lite_nocache_metrics['quality_computations']:>14} "
          f"{full_metrics['quality_computations']/(lite_metrics['quality_computations']+1):>9.2f}x")
    
    print(f"{'Cache Hit Rate':<30} {full_metrics['cache_hit_rate']:>13.2%} "
          f"{lite_metrics['cache_hit_rate']:>13.2%} {lite_nocache_metrics['cache_hit_rate']:>13.2%} "
          f"{'N/A':>10}")
    
    print("="*80)


def print_accuracy_table(full_acc: Dict, lite_acc: Dict, lite_nocache_acc: Dict):
    """Print formatted accuracy comparison table"""
    print("\n" + "="*80)
    print("ACCURACY COMPARISON TABLE")
    print("="*80)
    print(f"{'Metric':<30} {'Full':<15} {'Lite (cache)':<15} {'Lite (no cache)':<15} {'Retention':<10}")
    print("-"*80)
    
    for metric in ["precision@1", "precision@5", "precision@10", "recall@1", "recall@5", "recall@10", "mrr"]:
        full_val = full_acc.get(metric, 0)
        lite_val = lite_acc.get(metric, 0)
        lite_nocache_val = lite_nocache_acc.get(metric, 0)
        retention = (lite_val / full_val * 100) if full_val > 0 else 100
        
        print(f"{metric:<30} {full_val:>14.3f} {lite_val:>14.3f} {lite_nocache_val:>14.3f} {retention:>9.1f}%")
    
    print("="*80)


async def main():
    """Run performance comparison"""
    print("\n" + "="*80)
    print("PERFORMANCE COMPARISON: FULL vs LITE RETRIEVER")
    print("="*80)
    
    # Configuration
    num_hyperedges = 100
    num_queries = 50
    top_k = 10
    
    print(f"\nTest Configuration:")
    print(f"  Number of hyperedges: {num_hyperedges}")
    print(f"  Number of queries: {num_queries}")
    print(f"  Top-K: {top_k}")
    
    # Initialize mock storage
    print("\nInitializing mock storage...")
    graph = MockGraphStorage(num_hyperedges)
    vdb = MockVectorStorage(num_hyperedges)
    
    # Generate test queries
    print("Generating test queries...")
    queries, ground_truth = generate_test_queries(num_queries)
    
    try:
        # Test full retriever
        full_results, full_metrics = await test_full_retriever(graph, vdb, queries, top_k)
        full_summary = full_metrics.get_summary()
        
        # Test lite retriever with caching
        lite_results, lite_metrics = await test_lite_retriever(graph, vdb, queries, top_k, enable_caching=True)
        lite_summary = lite_metrics.get_summary()
        
        # Test lite retriever without caching
        lite_nocache_results, lite_nocache_metrics = await test_lite_retriever(
            graph, vdb, queries, top_k, enable_caching=False
        )
        lite_nocache_summary = lite_nocache_metrics.get_summary()
        
        # Compute accuracy metrics
        print("\nComputing accuracy metrics...")
        full_accuracy = compute_accuracy_metrics(full_results, ground_truth)
        lite_accuracy = compute_accuracy_metrics(lite_results, ground_truth)
        lite_nocache_accuracy = compute_accuracy_metrics(lite_nocache_results, ground_truth)
        
        # Print comparison tables
        print_comparison_table(full_summary, lite_summary, lite_nocache_summary)
        print_accuracy_table(full_accuracy, lite_accuracy, lite_nocache_accuracy)
        
        # Generate report
        report = {
            "configuration": {
                "num_hyperedges": num_hyperedges,
                "num_queries": num_queries,
                "top_k": top_k
            },
            "full_retriever": {
                "performance": full_summary,
                "accuracy": full_accuracy
            },
            "lite_retriever_cached": {
                "performance": lite_summary,
                "accuracy": lite_accuracy
            },
            "lite_retriever_nocache": {
                "performance": lite_nocache_summary,
                "accuracy": lite_nocache_accuracy
            },
            "speedup": {
                "avg_time": full_summary["avg_time_ms"] / lite_summary["avg_time_ms"],
                "median_time": full_summary["median_time_ms"] / lite_summary["median_time_ms"],
                "p95_time": full_summary["p95_time_ms"] / lite_summary["p95_time_ms"]
            },
            "accuracy_retention": {
                metric: (lite_accuracy[metric] / full_accuracy[metric] * 100) 
                if full_accuracy.get(metric, 0) > 0 else 100
                for metric in full_accuracy.keys()
            }
        }
        
        # Save report
        report_file = "performance_comparison_report.json"
        with open(report_file, "w") as f:
            json.dump(report, f, indent=2)
        
        print(f"\n✓ Report saved to: {report_file}")
        
        # Print summary
        print("\n" + "="*80)
        print("SUMMARY")
        print("="*80)
        print(f"Lite Retriever (with caching) achieves:")
        print(f"  - {report['speedup']['avg_time']:.2f}x speedup (average)")
        print(f"  - {report['speedup']['median_time']:.2f}x speedup (median)")
        print(f"  - {report['speedup']['p95_time']:.2f}x speedup (P95)")
        print(f"  - {report['accuracy_retention']['mrr']:.1f}% MRR retention")
        print(f"  - {report['accuracy_retention']['precision@10']:.1f}% Precision@10 retention")
        print(f"  - {lite_summary['cache_hit_rate']:.1%} cache hit rate")
        
        # Check if meets requirements (Requirement 3.3)
        speedup_ok = report['speedup']['avg_time'] >= 1.5  # At least 50% faster
        accuracy_ok = report['accuracy_retention']['mrr'] >= 80  # At least 80% accuracy
        
        print("\n" + "="*80)
        if speedup_ok and accuracy_ok:
            print("✓ REQUIREMENTS MET (Requirement 3.3)")
            print(f"  ✓ Speedup: {report['speedup']['avg_time']:.2f}x >= 1.5x")
            print(f"  ✓ Accuracy: {report['accuracy_retention']['mrr']:.1f}% >= 80%")
        else:
            print("⚠ REQUIREMENTS NOT FULLY MET")
            if not speedup_ok:
                print(f"  ✗ Speedup: {report['speedup']['avg_time']:.2f}x < 1.5x")
            if not accuracy_ok:
                print(f"  ✗ Accuracy: {report['accuracy_retention']['mrr']:.1f}% < 80%")
        print("="*80)
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
