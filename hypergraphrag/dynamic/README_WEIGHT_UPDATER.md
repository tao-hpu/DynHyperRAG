# WeightUpdater - Quick Reference Guide

## Overview

The `WeightUpdater` class provides dynamic weight adjustment for hyperedges in DynHyperRAG based on retrieval feedback and quality scores.

## Quick Start

```python
from hypergraphrag.dynamic import WeightUpdater

# Initialize with configuration
config = {
    'strategy': 'ema',  # 'ema', 'additive', or 'multiplicative'
    'update_alpha': 0.1,  # Learning rate (0 < α <= 1)
    'decay_factor': 0.99,  # Decay factor (0 < decay <= 1)
}

updater = WeightUpdater(knowledge_graph_inst, config)

# Update a single hyperedge
new_weight = await updater.update_weights(
    hyperedge_id='<hyperedge>some_relation',
    feedback_signal=0.8  # 0.0 (not useful) to 1.0 (very useful)
)

# Batch update multiple hyperedges
updates = [
    {'hyperedge_id': 'he1', 'feedback_signal': 0.9},
    {'hyperedge_id': 'he2', 'feedback_signal': 0.3},
]
results = await updater.batch_update_weights(updates)
```

## Update Strategies

### 1. EMA (Exponential Moving Average)

**Best for**: Smooth, gradual adjustments with momentum

**Formula**: `w_t = (1 - α) * w_{t-1} + α * f_t`

**Characteristics**:
- Recent feedback has more influence
- Historical performance is retained
- Smooth transitions
- Good default choice

**Example**:
```python
config = {'strategy': 'ema', 'update_alpha': 0.1}
# Weight: 0.7 → feedback 0.9 → 0.72 (gradual increase)
```

### 2. Additive

**Best for**: Direct, linear adjustments

**Formula**: `w_t = w_{t-1} + α * (f_t - 0.5)`

**Characteristics**:
- Adds/subtracts fixed amounts
- Feedback > 0.5 increases weight
- Feedback < 0.5 decreases weight
- More aggressive than EMA

**Example**:
```python
config = {'strategy': 'additive', 'update_alpha': 0.1}
# Weight: 0.7 → feedback 0.9 → 0.74 (add 0.04)
# Weight: 0.7 → feedback 0.2 → 0.67 (subtract 0.03)
```

### 3. Multiplicative

**Best for**: Proportional adjustments

**Formula**: `w_t = w_{t-1} * (1 + α * (f_t - 0.5))`

**Characteristics**:
- Scales weight proportionally
- Larger weights change more
- Smaller weights change less
- Good for maintaining relative differences

**Example**:
```python
config = {'strategy': 'multiplicative', 'update_alpha': 0.1}
# Weight: 0.7 → feedback 0.9 → 0.728 (multiply by 1.04)
# Weight: 0.7 → feedback 0.2 → 0.679 (multiply by 0.97)
```

## Configuration Options

```python
config = {
    # Required
    'strategy': 'ema',  # Update strategy
    'update_alpha': 0.1,  # Learning rate
    'decay_factor': 0.99,  # Decay factor
    
    # Optional
    'min_weight_ratio': 0.5,  # Min weight = quality * ratio
    'max_weight_ratio': 2.0,  # Max weight = quality * ratio
    'track_history': True,  # Enable history tracking
    'max_history_length': 100,  # Max history entries
}
```

### Parameter Guidelines

**update_alpha (Learning Rate)**:
- Small (0.01-0.05): Slow, stable updates
- Medium (0.1-0.2): Balanced updates (recommended)
- Large (0.3-0.5): Fast, aggressive updates

**decay_factor**:
- High (0.99-1.0): Slow decay, weights persist longer
- Medium (0.95-0.98): Moderate decay (recommended)
- Low (0.90-0.94): Fast decay, weights decrease quickly

**Weight Constraints**:
- `min_weight_ratio`: Prevents weights from becoming too low
- `max_weight_ratio`: Prevents low-quality hyperedges from dominating
- Default: Weight stays within [0.5 * quality, 2.0 * quality]

## Feedback Signal Guidelines

Feedback signals should be in the range [0.0, 1.0]:

- **1.0**: Hyperedge was highly useful, directly contributed to answer
- **0.8-0.9**: Hyperedge was useful, provided relevant information
- **0.5-0.7**: Hyperedge was somewhat useful, provided context
- **0.3-0.4**: Hyperedge was retrieved but not very useful
- **0.0-0.2**: Hyperedge was not useful, irrelevant to query

## Advanced Usage

### Get Update Statistics

```python
stats = await updater.get_update_statistics('hyperedge_id')

print(f"Feedback count: {stats['feedback_count']}")
print(f"Current weight: {stats['current_weight']}")
print(f"Average feedback: {stats['avg_feedback']}")
print(f"Weight trend: {stats['weight_trend']}")  # 'increasing', 'decreasing', 'stable'
```

### Reset Weights

```python
# Reset specific hyperedges
await updater.reset_weights(['he1', 'he2', 'he3'])

# Reset all hyperedges (not implemented yet)
# await updater.reset_weights(None)
```

### Custom Metadata

```python
new_weight = await updater.update_weights(
    hyperedge_id='he1',
    feedback_signal=0.8,
    metadata={
        'query': 'What is the treatment for disease X?',
        'context': 'medical_query',
        'user_id': 'user123',
        'timestamp': '2025-01-15T10:30:00'
    }
)
```

## Integration with Query Pipeline

```python
async def kg_query_with_dynamic_update(
    query: str,
    knowledge_graph_inst: BaseGraphStorage,
    ...
):
    # 1. Retrieve hyperedges
    retrieved_hyperedges = await retrieve_hyperedges(query)
    
    # 2. Generate answer
    answer = await generate_answer(query, retrieved_hyperedges)
    
    # 3. Extract feedback signals (Task 7)
    feedback_signals = await feedback_extractor.extract_feedback(
        answer, retrieved_hyperedges
    )
    
    # 4. Update weights asynchronously (don't block response)
    asyncio.create_task(
        weight_updater.batch_update_weights(feedback_signals)
    )
    
    return answer
```

## Data Model

### Hyperedge Node Structure

```python
{
    'role': 'hyperedge',
    'weight': 1.0,  # Original weight from LLM
    'quality_score': 0.7,  # From quality assessment module
    
    # Dynamic update fields
    'dynamic_weight': 0.72,  # Current dynamic weight
    'feedback_count': 5,  # Number of updates
    'last_updated': '2025-01-15T10:30:00',  # ISO timestamp
    
    # Optional: Update history
    'weight_history': [
        {
            'timestamp': '2025-01-15T10:30:00',
            'old_weight': 0.7,
            'new_weight': 0.72,
            'feedback': 0.8,
            'strategy': 'ema',
            'metadata': {...}
        },
        ...
    ]
}
```

## Performance Considerations

### Single Update
- **Time**: < 1ms per update
- **Memory**: Minimal (only node data)

### Batch Update
- **Time**: ~1ms per hyperedge (parallel)
- **Memory**: O(n) where n = number of updates
- **Recommended**: Use batch updates for > 10 hyperedges

### History Tracking
- **Memory**: ~100 bytes per history entry
- **Limit**: Default 100 entries per hyperedge
- **Recommendation**: Disable for production if not needed

## Troubleshooting

### Issue: Weights not changing

**Possible causes**:
1. `update_alpha` too small → Increase to 0.1-0.2
2. `decay_factor` too high → Decrease to 0.95-0.98
3. Quality constraints too tight → Adjust `min_weight_ratio` and `max_weight_ratio`

### Issue: Weights growing unbounded

**Possible causes**:
1. `decay_factor` too high → Decrease to < 0.99
2. Quality constraints too loose → Decrease `max_weight_ratio`
3. Always positive feedback → Check feedback extraction logic

### Issue: Low-quality hyperedges dominating

**Solution**: Ensure quality constraints are enabled:
```python
config = {
    'min_weight_ratio': 0.5,
    'max_weight_ratio': 2.0,  # Low-quality hyperedges can't exceed 2x their quality
}
```

## Testing

Run the test script to verify installation:

```bash
python test_weight_updater.py
```

Expected output:
```
============================================================
Testing WeightUpdater Implementation
============================================================
...
All tests completed successfully! ✓
```

## References

- **Design Document**: `.kiro/specs/dynhyperrag-quality-aware/design.md`
- **Requirements**: `.kiro/specs/dynhyperrag-quality-aware/requirements.md`
- **Task Summary**: `.kiro/specs/dynhyperrag-quality-aware/TASK_6_SUMMARY.md`

## Next Steps

1. **Task 7**: Implement `FeedbackExtractor` to automatically extract feedback signals
2. **Task 8**: Implement `HyperedgeRefiner` to filter low-quality hyperedges
3. **Task 9**: Integrate into `operate.py` query pipeline

## Support

For issues or questions:
1. Check the test script: `test_weight_updater.py`
2. Review the implementation: `hypergraphrag/dynamic/weight_updater.py`
3. See the task summary: `TASK_6_SUMMARY.md`
