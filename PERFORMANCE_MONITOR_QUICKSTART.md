# Performance Monitor Quick Start Guide

## Installation

The Performance Monitor is part of the `hypergraphrag.retrieval` module. No additional installation required.

## Basic Usage

### 1. Initialize Monitor

```python
from hypergraphrag.retrieval import PerformanceMonitor

# Create monitor with logging enabled
monitor = PerformanceMonitor(
    enable_logging=True,
    log_file="logs/retrieval_performance.jsonl",
    log_interval=10  # Flush every 10 queries
)
```

### 2. Track Retrieval

```python
async with monitor.track_retrieval("What is the penalty for theft?") as tracker:
    # Perform retrieval
    results = await retriever.retrieve(query, top_k=10)
    
    # Record metrics
    tracker.set_candidates(total=100, filtered=50, final=10)
    tracker.set_filter_used(True)
    tracker.set_ranker_used(True)
```

### 3. Get Statistics

```python
stats = monitor.get_statistics()

print(f"Total Queries: {stats['total_queries']}")
print(f"Average Time: {stats['avg_retrieval_time']:.3f}s")
print(f"Filter Usage: {stats['entity_filter_usage']:.1f}%")
print(f"Cache Hit Rate: {stats['cache_hit_rate']:.1f}%")
```

### 4. Generate Report

```python
# Print report
report = monitor.generate_report()
print(report)

# Save to file
monitor.generate_report(output_file="reports/performance.txt")
```

## Advanced Features

### Phase Timing

Track individual phases of retrieval:

```python
async with monitor.track_retrieval(query) as tracker:
    # Vector search
    tracker.start_phase("vector_search")
    results = await vdb.query(query, top_k=50)
    tracker.end_phase("vector_search")
    
    # Filtering
    tracker.start_phase("filtering")
    filtered = await entity_filter.filter_hyperedges_by_type(results, types)
    tracker.end_phase("filtering")
    
    # Ranking
    tracker.start_phase("ranking")
    ranked = await ranker.rank_hyperedges(query, filtered)
    tracker.end_phase("ranking")
```

### Export Metrics

```python
# Export to JSON
monitor.export_metrics("exports/metrics.json", format="json")

# Export to CSV
monitor.export_metrics("exports/metrics.csv", format="csv")
```

### Global Monitor

Use a global monitor instance:

```python
from hypergraphrag.retrieval import get_global_monitor

# Get global monitor (creates if doesn't exist)
monitor = get_global_monitor()

# Use anywhere in your code
async with monitor.track_retrieval(query) as tracker:
    results = await retriever.retrieve(query)
```

## Integration Examples

### With Entity Filter

```python
from hypergraphrag.retrieval import EntityTypeFilter, PerformanceMonitor

monitor = PerformanceMonitor()
entity_filter = EntityTypeFilter(graph, config)

async with monitor.track_retrieval(query) as tracker:
    # Identify types
    relevant_types = await entity_filter.identify_relevant_types(query)
    
    # Filter with timing
    tracker.start_phase("filtering")
    filtered_ids, stats = await entity_filter.filter_hyperedges_by_type(
        hyperedge_ids, relevant_types
    )
    tracker.end_phase("filtering")
    
    # Record metrics
    tracker.set_filter_used(True)
    tracker.set_candidates(
        total=stats['original_count'],
        filtered=stats['filtered_count']
    )
```

### With Quality Ranker

```python
from hypergraphrag.retrieval import QualityAwareRanker, PerformanceMonitor

monitor = PerformanceMonitor()
ranker = QualityAwareRanker(config)

async with monitor.track_retrieval(query) as tracker:
    # Vector search
    tracker.start_phase("vector_search")
    results = await vdb.query(query, top_k=50)
    tracker.end_phase("vector_search")
    
    # Quality ranking
    tracker.start_phase("ranking")
    ranked = await ranker.rank_hyperedges(query, results)
    tracker.end_phase("ranking")
    
    # Record usage
    tracker.set_ranker_used(True)
    tracker.set_candidates(total=len(results), final=len(ranked[:10]))
```

### With Lite Retriever

```python
from hypergraphrag.retrieval import LiteRetriever, PerformanceMonitor

monitor = PerformanceMonitor()
lite_retriever = LiteRetriever(graph, vdb, config)

async with monitor.track_retrieval(query) as tracker:
    # Lite retrieval
    results = await lite_retriever.retrieve(query, top_k=10)
    
    # Record usage
    tracker.set_lite_mode(True)
    tracker.set_cache_hit(results[0].get('from_cache', False))
    tracker.set_candidates(final=len(results))
```

## Common Patterns

### Compare Configurations

```python
configs = [
    {"name": "Standard", "filter": False, "ranker": False},
    {"name": "With Filter", "filter": True, "ranker": False},
    {"name": "Full", "filter": True, "ranker": True},
]

for config in configs:
    monitor = PerformanceMonitor(enable_logging=False)
    
    # Run queries with this config
    for query in test_queries:
        async with monitor.track_retrieval(query) as tracker:
            # Retrieval with config
            results = await retrieve_with_config(query, config)
            tracker.set_filter_used(config["filter"])
            tracker.set_ranker_used(config["ranker"])
    
    stats = monitor.get_statistics()
    print(f"{config['name']}: {stats['avg_retrieval_time']:.3f}s")
```

### Periodic Reporting

```python
monitor = PerformanceMonitor()

# Every 100 queries, generate report
for i, query in enumerate(queries):
    async with monitor.track_retrieval(query) as tracker:
        results = await retriever.retrieve(query)
    
    if (i + 1) % 100 == 0:
        report = monitor.generate_report(
            output_file=f"reports/perf_{i+1}.txt"
        )
```

### Error Tracking

```python
async with monitor.track_retrieval(query) as tracker:
    try:
        results = await retriever.retrieve(query)
        tracker.set_candidates(final=len(results))
    except Exception as e:
        # Error is automatically recorded
        logger.error(f"Retrieval failed: {e}")
        raise

# Check for errors
stats = monitor.get_statistics()
if stats['failed_queries'] > 0:
    print(f"Warning: {stats['failed_queries']} queries failed")
```

## Log File Format

Metrics are logged in JSONL format (one JSON object per line):

```json
{
  "query": "What is the penalty for theft?",
  "timestamp": "2025-01-15T10:30:00",
  "retrieval_time": 0.245,
  "vector_search_time": 0.120,
  "filtering_time": 0.045,
  "ranking_time": 0.032,
  "total_candidates": 100,
  "filtered_candidates": 58,
  "final_results": 10,
  "filter_reduction_rate": 42.0,
  "use_entity_filter": true,
  "use_quality_ranker": true,
  "use_lite_mode": false,
  "use_ann": false,
  "cache_hit": false,
  "error": null,
  "metadata": {}
}
```

## Analysis Tools

### Command Line (jq)

```bash
# Average retrieval time
cat logs/retrieval_performance.jsonl | jq '.retrieval_time' | awk '{sum+=$1; count++} END {print sum/count}'

# Filter usage rate
cat logs/retrieval_performance.jsonl | jq '.use_entity_filter' | grep true | wc -l

# Queries with errors
cat logs/retrieval_performance.jsonl | jq 'select(.error != null)'
```

### Python (pandas)

```python
import pandas as pd

# Load metrics
df = pd.read_json("logs/retrieval_performance.jsonl", lines=True)

# Average time by feature
print(df.groupby('use_entity_filter')['retrieval_time'].mean())

# Filter reduction distribution
print(df['filter_reduction_rate'].describe())

# Time series plot
df['timestamp'] = pd.to_datetime(df['timestamp'])
df.set_index('timestamp')['retrieval_time'].plot()
```

## Best Practices

1. **Always use context manager**: Ensures metrics are recorded even on errors
2. **Track phases**: Identify bottlenecks with phase timing
3. **Set feature flags**: Enable accurate feature usage analysis
4. **Add metadata**: Include domain, user_id, or other context
5. **Regular reporting**: Generate reports periodically to track trends
6. **Clear history**: For long-running systems, clear history periodically
7. **Export for analysis**: Use JSON/CSV export for detailed analysis

## Troubleshooting

### Metrics not recorded
- Ensure you're using the context manager
- Check that logging is enabled
- Verify log file path is writable

### High memory usage
- Clear history periodically: `monitor.clear_history()`
- Reduce log interval for more frequent flushing
- Export and clear: `monitor.export_metrics(...); monitor.clear_history()`

### Missing phase times
- Ensure both `start_phase()` and `end_phase()` are called
- Phase names must match: "vector_search", "filtering", "ranking"

## See Also

- [Full Documentation](hypergraphrag/retrieval/README_PERFORMANCE_MONITOR.md)
- [Example Script](example_performance_monitoring.py)
- [Test Suite](test_performance_monitor.py)
- [Entity Filter](hypergraphrag/retrieval/README_ENTITY_FILTER.md)
- [Quality Ranker](hypergraphrag/retrieval/README_QUALITY_RANKER.md)
- [Lite Retriever](hypergraphrag/retrieval/README_LITE_RETRIEVER.md)
