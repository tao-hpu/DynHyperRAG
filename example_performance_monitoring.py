"""
Example: Retrieval Performance Monitoring

This script demonstrates how to use the PerformanceMonitor to track and analyze
retrieval performance in DynHyperRAG.

Features demonstrated:
- Basic performance tracking
- Phase timing (vector search, filtering, ranking)
- Statistics and reporting
- Export capabilities
- Integration with retrieval components
"""

import asyncio
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def example_basic_tracking():
    """Example 1: Basic performance tracking"""
    print("\n" + "=" * 80)
    print("EXAMPLE 1: Basic Performance Tracking")
    print("=" * 80 + "\n")
    
    from hypergraphrag.retrieval import PerformanceMonitor
    
    # Initialize monitor
    monitor = PerformanceMonitor(
        enable_logging=True,
        log_file="logs/example_performance.jsonl",
        log_interval=5
    )
    
    # Simulate multiple queries
    test_queries = [
        "What is the penalty for theft?",
        "Who is the author of this paper?",
        "What are the symptoms of diabetes?",
        "What is the legal definition of fraud?",
        "How is hypertension treated?",
    ]
    
    for query in test_queries:
        async with monitor.track_retrieval(query) as tracker:
            # Simulate retrieval operation
            await asyncio.sleep(0.1)  # Simulate vector search
            
            # Simulate filtering
            await asyncio.sleep(0.02)  # Simulate filtering
            
            # Simulate ranking
            await asyncio.sleep(0.01)  # Simulate ranking
            
            # Record metrics
            tracker.set_candidates(total=100, filtered=60, final=10)
            tracker.set_filter_used(True)
            tracker.set_ranker_used(True)
    
    # Get statistics
    stats = monitor.get_statistics()
    
    print("\nPerformance Statistics:")
    print(f"  Total Queries: {stats['total_queries']}")
    print(f"  Average Retrieval Time: {stats['avg_retrieval_time']:.3f}s")
    print(f"  Median Retrieval Time: {stats['median_retrieval_time']:.3f}s")
    print(f"  P95 Retrieval Time: {stats['p95_retrieval_time']:.3f}s")
    print(f"  Entity Filter Usage: {stats['entity_filter_usage']:.1f}%")
    print(f"  Quality Ranker Usage: {stats['quality_ranker_usage']:.1f}%")
    print(f"  Average Filter Reduction: {stats['avg_filter_reduction']:.1f}%")
    
    return monitor


async def example_phase_timing():
    """Example 2: Detailed phase timing"""
    print("\n" + "=" * 80)
    print("EXAMPLE 2: Detailed Phase Timing")
    print("=" * 80 + "\n")
    
    from hypergraphrag.retrieval import PerformanceMonitor
    
    monitor = PerformanceMonitor(enable_logging=False)
    
    query = "What is the penalty for theft?"
    
    async with monitor.track_retrieval(query) as tracker:
        # Vector search phase
        tracker.start_phase("vector_search")
        await asyncio.sleep(0.08)  # Simulate vector search
        tracker.end_phase("vector_search")
        
        # Filtering phase
        tracker.start_phase("filtering")
        await asyncio.sleep(0.03)  # Simulate filtering
        tracker.end_phase("filtering")
        
        # Ranking phase
        tracker.start_phase("ranking")
        await asyncio.sleep(0.02)  # Simulate ranking
        tracker.end_phase("ranking")
        
        # Record metrics
        tracker.set_candidates(total=100, filtered=55, final=10)
        tracker.set_filter_used(True)
        tracker.set_ranker_used(True)
    
    # Get recent metrics
    recent = monitor.get_recent_metrics(1)[0]
    
    print(f"Query: {recent.query}")
    print(f"\nTiming Breakdown:")
    print(f"  Total Time: {recent.retrieval_time:.3f}s")
    print(f"  Vector Search: {recent.vector_search_time:.3f}s ({recent.vector_search_time/recent.retrieval_time*100:.1f}%)")
    print(f"  Filtering: {recent.filtering_time:.3f}s ({recent.filtering_time/recent.retrieval_time*100:.1f}%)")
    print(f"  Ranking: {recent.ranking_time:.3f}s ({recent.ranking_time/recent.retrieval_time*100:.1f}%)")
    
    print(f"\nCandidate Flow:")
    print(f"  Initial: {recent.total_candidates}")
    print(f"  After Filtering: {recent.filtered_candidates} ({recent.filter_reduction_rate:.1f}% reduction)")
    print(f"  Final Results: {recent.final_results}")


async def example_feature_comparison():
    """Example 3: Compare different retrieval configurations"""
    print("\n" + "=" * 80)
    print("EXAMPLE 3: Feature Comparison")
    print("=" * 80 + "\n")
    
    from hypergraphrag.retrieval import PerformanceMonitor
    
    # Test different configurations
    configs = [
        {"name": "Standard", "filter": False, "ranker": False, "lite": False},
        {"name": "With Filter", "filter": True, "ranker": False, "lite": False},
        {"name": "With Ranker", "filter": False, "ranker": True, "lite": False},
        {"name": "Full (Filter + Ranker)", "filter": True, "ranker": True, "lite": False},
        {"name": "Lite Mode", "filter": False, "ranker": False, "lite": True},
    ]
    
    results = []
    
    for config in configs:
        monitor = PerformanceMonitor(enable_logging=False)
        
        # Run 10 queries with this configuration
        for i in range(10):
            query = f"Test query {i}"
            
            async with monitor.track_retrieval(query) as tracker:
                # Simulate retrieval with different timings based on config
                base_time = 0.10
                
                if config["filter"]:
                    await asyncio.sleep(base_time + 0.02)  # Filter adds time
                    tracker.set_filter_used(True)
                    tracker.set_candidates(total=100, filtered=60, final=10)
                elif config["ranker"]:
                    await asyncio.sleep(base_time + 0.015)  # Ranker adds time
                    tracker.set_ranker_used(True)
                    tracker.set_candidates(total=100, final=10)
                elif config["lite"]:
                    await asyncio.sleep(base_time * 0.6)  # Lite is faster
                    tracker.set_lite_mode(True)
                    tracker.set_candidates(total=100, final=10)
                else:
                    await asyncio.sleep(base_time)
                    tracker.set_candidates(total=100, final=10)
        
        stats = monitor.get_statistics()
        results.append({
            "config": config["name"],
            "avg_time": stats["avg_retrieval_time"],
            "filter_usage": stats["entity_filter_usage"],
            "ranker_usage": stats["quality_ranker_usage"],
            "lite_usage": stats["lite_mode_usage"],
        })
    
    # Print comparison table
    print("\nConfiguration Comparison:")
    print(f"{'Configuration':<25} {'Avg Time':<12} {'Filter':<10} {'Ranker':<10} {'Lite':<10}")
    print("-" * 75)
    
    for result in results:
        print(
            f"{result['config']:<25} "
            f"{result['avg_time']:.3f}s      "
            f"{result['filter_usage']:>5.1f}%    "
            f"{result['ranker_usage']:>5.1f}%    "
            f"{result['lite_usage']:>5.1f}%"
        )
    
    # Find fastest configuration
    fastest = min(results, key=lambda x: x["avg_time"])
    print(f"\nFastest Configuration: {fastest['config']} ({fastest['avg_time']:.3f}s)")


async def example_report_generation():
    """Example 4: Generate performance report"""
    print("\n" + "=" * 80)
    print("EXAMPLE 4: Report Generation")
    print("=" * 80 + "\n")
    
    from hypergraphrag.retrieval import PerformanceMonitor
    
    monitor = PerformanceMonitor(enable_logging=False)
    
    # Simulate various queries
    for i in range(20):
        query = f"Test query {i}"
        
        async with monitor.track_retrieval(query) as tracker:
            # Vary timing and features
            import random
            
            await asyncio.sleep(random.uniform(0.05, 0.15))
            
            use_filter = random.random() > 0.3
            use_ranker = random.random() > 0.2
            use_cache = random.random() > 0.8
            
            tracker.set_filter_used(use_filter)
            tracker.set_ranker_used(use_ranker)
            tracker.set_cache_hit(use_cache)
            
            if use_filter:
                total = 100
                filtered = random.randint(40, 70)
                final = 10
            else:
                total = 100
                filtered = 100
                final = 10
            
            tracker.set_candidates(total=total, filtered=filtered, final=final)
    
    # Generate report
    report = monitor.generate_report()
    print(report)
    
    # Save report to file
    report_dir = Path("reports")
    report_dir.mkdir(exist_ok=True)
    
    report_file = report_dir / "example_performance_report.txt"
    monitor.generate_report(output_file=str(report_file))
    print(f"\nReport saved to: {report_file}")


async def example_export_metrics():
    """Example 5: Export metrics for analysis"""
    print("\n" + "=" * 80)
    print("EXAMPLE 5: Export Metrics")
    print("=" * 80 + "\n")
    
    from hypergraphrag.retrieval import PerformanceMonitor
    
    monitor = PerformanceMonitor(enable_logging=False)
    
    # Generate some metrics
    for i in range(15):
        query = f"Query {i}"
        
        async with monitor.track_retrieval(query) as tracker:
            await asyncio.sleep(0.1)
            tracker.set_candidates(total=100, filtered=60, final=10)
            tracker.set_filter_used(True)
            tracker.add_metadata("query_id", i)
            tracker.add_metadata("domain", "legal" if i % 2 == 0 else "medical")
    
    # Export to JSON
    export_dir = Path("exports")
    export_dir.mkdir(exist_ok=True)
    
    json_file = export_dir / "example_metrics.json"
    monitor.export_metrics(str(json_file), format="json")
    print(f"Metrics exported to JSON: {json_file}")
    
    # Export to CSV
    csv_file = export_dir / "example_metrics.csv"
    monitor.export_metrics(str(csv_file), format="csv")
    print(f"Metrics exported to CSV: {csv_file}")
    
    print("\nExported metrics can be analyzed with:")
    print("  - Python: pandas.read_json() or pandas.read_csv()")
    print("  - Command line: jq (for JSON)")
    print("  - Spreadsheet software (for CSV)")


async def example_global_monitor():
    """Example 6: Using global monitor"""
    print("\n" + "=" * 80)
    print("EXAMPLE 6: Global Monitor")
    print("=" * 80 + "\n")
    
    from hypergraphrag.retrieval import get_global_monitor, set_global_monitor, PerformanceMonitor
    
    # Create and set global monitor
    monitor = PerformanceMonitor(enable_logging=False)
    set_global_monitor(monitor)
    
    # Use global monitor from anywhere
    async def some_retrieval_function(query):
        monitor = get_global_monitor()
        
        async with monitor.track_retrieval(query) as tracker:
            await asyncio.sleep(0.1)
            tracker.set_candidates(total=100, final=10)
            return ["result1", "result2"]
    
    # Call from different places
    await some_retrieval_function("Query 1")
    await some_retrieval_function("Query 2")
    await some_retrieval_function("Query 3")
    
    # Get statistics from global monitor
    global_monitor = get_global_monitor()
    stats = global_monitor.get_statistics()
    
    print(f"Global monitor tracked {stats['total_queries']} queries")
    print(f"Average time: {stats['avg_retrieval_time']:.3f}s")


async def main():
    """Run all examples"""
    print("\n" + "=" * 80)
    print("RETRIEVAL PERFORMANCE MONITORING EXAMPLES")
    print("=" * 80)
    
    # Run examples
    await example_basic_tracking()
    await example_phase_timing()
    await example_feature_comparison()
    await example_report_generation()
    await example_export_metrics()
    await example_global_monitor()
    
    print("\n" + "=" * 80)
    print("ALL EXAMPLES COMPLETED")
    print("=" * 80 + "\n")
    
    print("Generated files:")
    print("  - logs/example_performance.jsonl (performance log)")
    print("  - reports/example_performance_report.txt (performance report)")
    print("  - exports/example_metrics.json (metrics in JSON)")
    print("  - exports/example_metrics.csv (metrics in CSV)")


if __name__ == "__main__":
    asyncio.run(main())
