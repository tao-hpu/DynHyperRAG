# Hyperedge Refiner Module

## Overview

The `HyperedgeRefiner` module provides functionality for filtering and improving the quality of the knowledge graph by removing or downweighting low-quality hyperedges. This is a critical component of the DynHyperRAG system that helps maintain graph quality over time.

## Features

### Filtering Modes

1. **Hard Filtering**: Permanently deletes low-quality hyperedges from the graph
   - Use when you're confident about quality scores
   - Reduces graph size and improves retrieval speed
   - Cannot be undone (hyperedges are deleted)

2. **Soft Filtering**: Reduces dynamic weight but keeps hyperedges
   - Use when you want to be conservative
   - Allows for later restoration if needed
   - Hyperedges remain in graph but with reduced influence

### Threshold Selection Strategies

1. **Fixed Threshold**: Use a predefined quality score threshold
   - Simple and interpretable
   - Good when you know the quality distribution
   - Example: Filter all hyperedges with quality < 0.5

2. **Percentile-Based**: Filter bottom X% of hyperedges
   - Adaptive to quality distribution
   - Good for maintaining graph size
   - Example: Filter bottom 25% by quality

3. **F1-Optimal**: Find threshold that maximizes F1 score
   - Requires ground truth labels
   - Optimal for supervised scenarios
   - Balances precision and recall

## Usage

### Basic Usage

```python
from hypergraphrag.dynamic.refiner import HyperedgeRefiner

# Configure refiner
config = {
    'quality_threshold': 0.5,
    'filter_mode': 'soft',  # or 'hard'
    'threshold_strategy': 'fixed',  # or 'percentile', 'f1_optimal'
}

# Initialize
refiner = HyperedgeRefiner(graph, config)

# Filter hyperedges
hyperedge_ids = ['he1', 'he2', 'he3', ...]
result = await refiner.filter_low_quality(hyperedge_ids)

print(f"Filtered: {result['filtered']}")
print(f"Kept: {result['kept']}")
print(f"Filter rate: {result['filter_rate']:.1%}")
```

### Soft Filtering Example

```python
# Soft filtering - reduces weight but keeps hyperedges
config = {
    'quality_threshold': 0.5,
    'filter_mode': 'soft',
    'threshold_strategy': 'fixed',
    'soft_filter_weight_multiplier': 0.1,  # Reduce to 10% of original
}

refiner = HyperedgeRefiner(graph, config)
result = await refiner.filter_low_quality(hyperedge_ids)

# Later, restore if needed
restored_count = await refiner.restore_filtered_hyperedges(result['filtered'])
```

### Hard Filtering Example

```python
# Hard filtering - permanently deletes hyperedges
config = {
    'quality_threshold': 0.5,
    'filter_mode': 'hard',
    'threshold_strategy': 'fixed',
}

refiner = HyperedgeRefiner(graph, config)
result = await refiner.filter_low_quality(hyperedge_ids)

# Hyperedges in result['filtered'] are now deleted
```

### Percentile-Based Filtering

```python
# Filter bottom 25% of hyperedges by quality
config = {
    'filter_mode': 'soft',
    'threshold_strategy': 'percentile',
    'percentile': 25,  # Bottom 25%
}

refiner = HyperedgeRefiner(graph, config)
result = await refiner.filter_low_quality(hyperedge_ids)

print(f"Threshold used: {result['threshold_used']:.3f}")
```

### F1-Optimal Filtering

```python
# Find optimal threshold using ground truth
ground_truth = {
    'he1': True,   # Good hyperedge
    'he2': False,  # Bad hyperedge
    'he3': True,
    # ...
}

config = {
    'filter_mode': 'soft',
    'threshold_strategy': 'f1_optimal',
}

refiner = HyperedgeRefiner(graph, config)
result = await refiner.filter_low_quality(hyperedge_ids, ground_truth)

print(f"Optimal threshold: {result['threshold_used']:.3f}")
```

### Batch Filtering

```python
# Filter multiple batches in parallel
batches = [
    ['he1', 'he2', 'he3'],
    ['he4', 'he5', 'he6'],
    ['he7', 'he8', 'he9'],
]

results = await refiner.batch_filter_low_quality(batches)

for i, result in enumerate(results):
    print(f"Batch {i}: {result['filter_rate']:.1%} filtered")
```

## Configuration Options

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `quality_threshold` | float | 0.5 | Quality score threshold for filtering (0-1) |
| `filter_mode` | str | 'soft' | Filtering mode: 'hard' or 'soft' |
| `threshold_strategy` | str | 'fixed' | Strategy: 'fixed', 'percentile', or 'f1_optimal' |
| `percentile` | int | 25 | Percentile for threshold (0-100) |
| `soft_filter_weight_multiplier` | float | 0.1 | Weight multiplier for soft filtering |
| `track_decisions` | bool | True | Whether to track filtering decisions |

## Result Structure

The `filter_low_quality()` method returns a dictionary with:

```python
{
    'filtered': ['he2', 'he5'],           # List of filtered hyperedge IDs
    'kept': ['he1', 'he3', 'he4'],        # List of kept hyperedge IDs
    'filter_rate': 0.4,                   # Proportion filtered (0-1)
    'threshold_used': 0.5,                # Actual threshold used
    'statistics': {                       # Detailed statistics
        'total_evaluated': 5,
        'filtered_count': 2,
        'kept_count': 3,
        'filter_rate': 0.4,
        'avg_quality_filtered': 0.35,
        'avg_quality_kept': 0.75,
        'filter_mode': 'soft',
        'threshold_strategy': 'fixed',
    }
}
```

## Statistics and Analysis

### Get Filtering Statistics

```python
# Get overall statistics
stats = refiner.get_filtering_statistics()

print(f"Total decisions: {stats['total_decisions']}")
print(f"Filtered: {stats['filtered_count']}")
print(f"Kept: {stats['kept_count']}")
print(f"Filter rate: {stats['filter_rate']:.1%}")
print(f"Avg quality (filtered): {stats['avg_quality_filtered']:.3f}")
print(f"Avg quality (kept): {stats['avg_quality_kept']:.3f}")
```

### Analyze Quality Distribution

```python
from hypergraphrag.dynamic.refiner import analyze_quality_distribution

quality_scores = {
    'he1': 0.8,
    'he2': 0.3,
    'he3': 0.6,
    # ...
}

dist_stats = analyze_quality_distribution(quality_scores)

print(f"Mean: {dist_stats['mean']:.3f}")
print(f"Std: {dist_stats['std']:.3f}")
print(f"Below 0.5: {dist_stats['below_0.5']}")
print(f"Above 0.7: {dist_stats['above_0.7']}")
```

### Compute Filtering Metrics

```python
from hypergraphrag.dynamic.refiner import compute_filtering_metrics

# Evaluate filtering performance against ground truth
metrics = compute_filtering_metrics(
    filtered_ids=['he2', 'he5'],
    kept_ids=['he1', 'he3', 'he4'],
    ground_truth={'he1': True, 'he2': False, 'he3': True, 'he4': True, 'he5': False}
)

print(f"Precision: {metrics['precision']:.3f}")
print(f"Recall: {metrics['recall']:.3f}")
print(f"F1: {metrics['f1']:.3f}")
print(f"Accuracy: {metrics['accuracy']:.3f}")
```

## Best Practices

### 1. Start with Soft Filtering

When first deploying, use soft filtering to be conservative:

```python
config = {
    'filter_mode': 'soft',
    'threshold_strategy': 'percentile',
    'percentile': 25,  # Filter bottom 25%
}
```

### 2. Monitor Filtering Statistics

Regularly check statistics to understand filtering behavior:

```python
stats = refiner.get_filtering_statistics()
if stats['filter_rate'] > 0.5:
    print("Warning: Filtering more than 50% of hyperedges!")
```

### 3. Use Percentile for Adaptive Filtering

Percentile-based filtering adapts to quality distribution:

```python
# Always filter bottom 20%, regardless of absolute quality
config = {
    'threshold_strategy': 'percentile',
    'percentile': 20,
}
```

### 4. Validate with Ground Truth

If you have ground truth, use F1-optimal strategy:

```python
config = {
    'threshold_strategy': 'f1_optimal',
}
result = await refiner.filter_low_quality(hyperedge_ids, ground_truth)
```

### 5. Restore Cautiously

Only restore if you have evidence that filtering was too aggressive:

```python
# Check statistics first
stats = refiner.get_filtering_statistics()
if stats['avg_quality_filtered'] > 0.6:
    # Filtered hyperedges had decent quality, consider restoring
    await refiner.restore_filtered_hyperedges()
```

## Integration with DynHyperRAG

The refiner integrates with other DynHyperRAG components:

```python
from hypergraphrag.quality.scorer import QualityScorer
from hypergraphrag.dynamic.weight_updater import WeightUpdater
from hypergraphrag.dynamic.refiner import HyperedgeRefiner

# 1. Score hyperedges
scorer = QualityScorer(graph, scorer_config)
await scorer.batch_compute_quality_scores(hyperedge_ids)

# 2. Update weights based on feedback
updater = WeightUpdater(graph, updater_config)
await updater.batch_update_weights(updates)

# 3. Filter low-quality hyperedges
refiner = HyperedgeRefiner(graph, refiner_config)
result = await refiner.filter_low_quality(hyperedge_ids)

print(f"Filtered {result['filter_rate']:.1%} of hyperedges")
```

## Performance Considerations

### Batch Processing

For large graphs, use batch processing:

```python
# Process in batches of 1000
batch_size = 1000
for i in range(0, len(all_hyperedge_ids), batch_size):
    batch = all_hyperedge_ids[i:i+batch_size]
    result = await refiner.filter_low_quality(batch)
```

### Parallel Filtering

Filter multiple independent sets in parallel:

```python
batches = [batch1, batch2, batch3]
results = await refiner.batch_filter_low_quality(batches)
```

### Memory Management

Clear history periodically to save memory:

```python
# After processing
refiner.clear_history()
```

## Troubleshooting

### Issue: Too Many Hyperedges Filtered

**Solution**: Adjust threshold or use percentile strategy

```python
# Option 1: Lower threshold
config['quality_threshold'] = 0.3

# Option 2: Use percentile
config['threshold_strategy'] = 'percentile'
config['percentile'] = 10  # Only filter bottom 10%
```

### Issue: Not Enough Filtering

**Solution**: Increase threshold or percentile

```python
# Option 1: Raise threshold
config['quality_threshold'] = 0.7

# Option 2: Increase percentile
config['percentile'] = 40  # Filter bottom 40%
```

### Issue: Accidentally Deleted Important Hyperedges

**Solution**: Use soft filtering instead of hard filtering

```python
# Always use soft filtering initially
config['filter_mode'] = 'soft'

# Can restore later if needed
await refiner.restore_filtered_hyperedges()
```

## Testing

Run the test suite:

```bash
# Simple test
python test_refiner_simple.py

# Comprehensive test
python test_hyperedge_refiner.py
```

## References

- Design Document: `.kiro/specs/dynhyperrag-quality-aware/design.md`
- Requirements: `.kiro/specs/dynhyperrag-quality-aware/requirements.md` (Requirement 2.3)
- Related Modules:
  - `QualityScorer`: Computes quality scores
  - `WeightUpdater`: Updates dynamic weights
  - `FeedbackExtractor`: Extracts feedback signals

## Future Enhancements

Potential improvements for future versions:

1. **Iterative Refinement**: Trigger re-extraction for low-quality hyperedges
2. **Merge Similar Hyperedges**: Combine redundant hyperedges
3. **Active Learning**: Use user feedback to improve filtering
4. **Temporal Filtering**: Consider hyperedge age and usage patterns
5. **Domain-Specific Rules**: Custom filtering rules for different domains
