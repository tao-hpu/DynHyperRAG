# Retrieval Performance Monitor

## Overview

The Performance Monitor provides comprehensive tracking and analysis of retrieval operations in DynHyperRAG. It records timing metrics, filtering effectiveness, and feature usage to help optimize retrieval performance.

## Features

- **Timing Tracking**: Measure total retrieval time and individual phase times (vector search, filtering, ranking)
- **Filtering Metrics**: Track entity type filtering effectiveness and reduction rates
- **Feature Usage**: Monitor usage of entity filter, quality ranker, lite mode, ANN search, and caching
- **Performance Logging**: Automatic logging to JSONL files for historical analysis
- **Statistics & Reports**: Generate aggregate statistics and detailed performance reports
- **Export Capabilities**: Export metrics to JSON or CSV for external analysis

## Quick Start

### Basic Usage

```python
from hypergraphrag.retrieval import PerformanceMonitor

# Initialize monitor
monitor = PerformanceMonitor(
    enable_logging=True,
    log_file="logs/retrieval_performance.jsonl",
    log_interval=10  # Flush logs every 10 queries
)

# Track a retrieval operation
async with monitor.track_retrieval("What is the penalty for theft?") as tracker:
    # Perform retrieval
    results = await retriever.retrieve(query, top_k=10)
    
    # Record metrics
    tracker.set_candidates(total=100, filtered=50, final=10)
    tracker.set_filter_used(True)
    tracker.set_ranker_used(True)

# Get statistics
stats = monitor.get_statistics()
print(f"Average retrieval time: {stats['avg_retrieval_time']:.3f}s")
print(f"Entity filter usage: {stats['entity_filter_usage']:.1f}%")
print(f"Average filter reduction: {stats['avg_filter_reduction']:.1f}%")
```

### Phase Timing

Track individual phases of retrieval:

```python
async with monitor.track_retrieval(query) as tracker:
    # Vector search phase
    tracker.start_phase("vector_search")
    vector_results = await vdb.query(query, top_k=50)
    tracker.end_phase("vector_search")
    
    # Filtering phase
    tracker.start_phase("filtering")
    filtered_results = await entity_filter.filter_hyperedges_by_type(
        vector_results, relevant_types
    )
    tracker.end_phase("filtering")
    
    # Ranking phase
    tracker.start_phase("ranking")
    ranked_results = await ranker.rank_hyperedges(query, filtered_results)
    tracker.end_phase("ranking")
    
    # Record counts
    tracker.set_candidates(
        total=len(vector_results),
        filtered=len(filtered_results),
        final=len(ranked_results)
    )
```

### Global Monitor

Use a global monitor instance for convenience:

```python
from hypergraphrag.retrieval import get_global_monitor

# Get global monitor (creates one if it doesn't exist)
monitor = get_global_monitor()

# Use it anywhere in your code
async with monitor.track_retrieval(query) as tracker:
    results = await retriever.retrieve(query)
    tracker.set_candidates(total=100, final=10)
```

## Integration with Retrieval Components

### Entity Type Filter Integration

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
    tracker.add_metadata("filter_reduction", stats['reduction_rate'])
```

### Quality Ranker Integration

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

### Lite Retriever Integration

```python
from hypergraphrag.retrieval import LiteRetriever, PerformanceMonitor

monitor = PerformanceMonitor()
lite_retriever = LiteRetriever(graph, vdb, config)

async with monitor.track_retrieval(query) as tracker:
    # Lite retrieval (handles timing internally)
    results = await lite_retriever.retrieve(query, top_k=10)
    
    # Record usage
    tracker.set_lite_mode(True)
    tracker.set_cache_hit(results[0].get('from_cache', False))
    tracker.set_candidates(final=len(results))
    
    # Get lite retriever stats
    lite_stats = lite_retriever.get_cache_stats()
    tracker.add_metadata("lite_cache_hit_rate", lite_stats['query_cache']['hit_rate'])
```

## Statistics and Reporting

### Get Statistics

```python
stats = monitor.get_statistics()

# Available statistics:
# - total_queries: Total number of queries tracked
# - successful_queries: Number of successful queries
# - failed_queries: Number of failed queries
# - avg_retrieval_time: Average total retrieval time
# - median_retrieval_time: Median retrieval time
# - p95_retrieval_time: 95th percentile retrieval time
# - avg_vector_search_time: Average vector search time
# - avg_filtering_time: Average filtering time
# - avg_ranking_time: Average ranking time
# - avg_filter_reduction: Average filter reduction rate
# - entity_filter_usage: % of queries using entity filter
# - quality_ranker_usage: % of queries using quality ranker
# - lite_mode_usage: % of queries using lite mode
# - ann_usage: % of queries using ANN search
# - cache_hit_rate: % of cache hits
```

### Generate Report

```python
# Generate and print report
report = monitor.generate_report()
print(report)

# Save report to file
monitor.generate_report(output_file="reports/retrieval_performance.txt")
```

Example report output:

```
================================================================================
RETRIEVAL PERFORMANCE REPORT
================================================================================

Generated: 2025-01-15T10:30:00
Total Queries: 150
Successful: 148
Failed: 2

--------------------------------------------------------------------------------
TIMING STATISTICS
--------------------------------------------------------------------------------
Average Retrieval Time: 0.245s
Median Retrieval Time: 0.198s
P95 Retrieval Time: 0.512s
Average Vector Search Time: 0.120s
Average Filtering Time: 0.045s
Average Ranking Time: 0.032s

--------------------------------------------------------------------------------
FEATURE USAGE
--------------------------------------------------------------------------------
Entity Filter Usage: 85.1%
Quality Ranker Usage: 92.6%
Lite Mode Usage: 15.5%
ANN Search Usage: 20.3%
Cache Hit Rate: 12.8%

--------------------------------------------------------------------------------
FILTERING EFFECTIVENESS
--------------------------------------------------------------------------------
Average Filter Reduction: 42.3%

================================================================================
```

### Export Metrics

```python
# Export to JSON
monitor.export_metrics("exports/metrics.json", format="json")

# Export to CSV
monitor.export_metrics("exports/metrics.csv", format="csv")
```

## Performance Analysis Tools

### Recent Metrics

```python
# Get last 10 queries
recent = monitor.get_recent_metrics(n=10)

for metrics in recent:
    print(f"Query: {metrics.query[:50]}...")
    print(f"  Time: {metrics.retrieval_time:.3f}s")
    print(f"  Candidates: {metrics.total_candidates} → {metrics.final_results}")
    print(f"  Filter reduction: {metrics.filter_reduction_rate:.1f}%")
```

### Average Retrieval Time

```python
avg_time = monitor.get_average_retrieval_time()
print(f"Average retrieval time: {avg_time:.3f}s")
```

### Clear History

```python
# Clear all metrics history
monitor.clear_history()
```

## Configuration

### Monitor Configuration

```python
monitor = PerformanceMonitor(
    enable_logging=True,           # Enable file logging
    log_file="logs/perf.jsonl",    # Log file path
    log_interval=10                # Flush logs every N queries
)
```

### Disable Logging

```python
# For production with minimal overhead
monitor = PerformanceMonitor(enable_logging=False)
```

## Log File Format

Metrics are logged in JSONL (JSON Lines) format, one JSON object per line:

```json
{"query": "What is the penalty for theft?", "timestamp": "2025-01-15T10:30:00", "retrieval_time": 0.245, "vector_search_time": 0.120, "filtering_time": 0.045, "ranking_time": 0.032, "total_candidates": 100, "filtered_candidates": 58, "final_results": 10, "filter_reduction_rate": 42.0, "use_entity_filter": true, "use_quality_ranker": true, "use_lite_mode": false, "use_ann": false, "cache_hit": false, "error": null, "metadata": {}}
```

This format is easy to parse and analyze with tools like:
- `jq` for command-line analysis
- Python's `json` module
- Pandas for data analysis
- Log aggregation tools (ELK, Splunk, etc.)

## Best Practices

### 1. Use Context Manager

Always use the `track_retrieval` context manager to ensure metrics are recorded even if errors occur:

```python
async with monitor.track_retrieval(query) as tracker:
    # Retrieval code here
    pass
```

### 2. Record Phase Timing

Track individual phases for detailed performance analysis:

```python
tracker.start_phase("vector_search")
# ... vector search code ...
tracker.end_phase("vector_search")
```

### 3. Set Feature Usage Flags

Always indicate which features were used:

```python
tracker.set_filter_used(True)
tracker.set_ranker_used(True)
tracker.set_lite_mode(False)
tracker.set_ann_used(False)
```

### 4. Add Metadata

Include additional context in metadata:

```python
tracker.add_metadata("domain", "legal")
tracker.add_metadata("user_id", "user123")
tracker.add_metadata("top_k", 10)
```

### 5. Regular Reporting

Generate reports periodically to identify performance trends:

```python
# Every 100 queries
if monitor._query_count % 100 == 0:
    report = monitor.generate_report(
        output_file=f"reports/perf_{monitor._query_count}.txt"
    )
```

## Performance Overhead

The performance monitor is designed to have minimal overhead:

- **Timing**: Uses `time.time()` which has negligible overhead
- **Logging**: Asynchronous file I/O with periodic flushing
- **Memory**: Stores metrics in memory (consider clearing history periodically for long-running systems)

Typical overhead: < 1ms per query

## Integration with operate.py

The performance monitor can be integrated into the main query flow in `operate.py`:

```python
from hypergraphrag.retrieval import get_global_monitor

async def kg_query(...):
    monitor = get_global_monitor()
    
    async with monitor.track_retrieval(query) as tracker:
        # Existing query logic
        context, retrieved_hyperedges = await _build_query_context(...)
        
        # Record metrics
        tracker.set_candidates(final=len(retrieved_hyperedges))
        
        # Generate response
        response = await use_model_func(query, system_prompt=sys_prompt)
        
        return response
```

## Troubleshooting

### Metrics Not Being Recorded

- Ensure you're using the context manager: `async with monitor.track_retrieval(...)`
- Check that logging is enabled: `enable_logging=True`
- Verify log file path is writable

### High Memory Usage

- Clear history periodically: `monitor.clear_history()`
- Reduce log interval: `log_interval=1` (flush more frequently)
- Export and clear: `monitor.export_metrics(...); monitor.clear_history()`

### Missing Phase Times

- Ensure you call both `start_phase()` and `end_phase()`
- Phase names must match: "vector_search", "filtering", "ranking"

## See Also

- [Entity Type Filter](README_ENTITY_FILTER.md)
- [Quality-Aware Ranker](README_QUALITY_RANKER.md)
- [Lite Retriever](README_LITE_RETRIEVER.md)
- [ANN Search](README_ANN_SEARCH.md)
