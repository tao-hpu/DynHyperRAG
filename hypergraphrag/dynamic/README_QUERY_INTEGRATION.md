# Dynamic Update Query Integration Guide

## Overview

This guide explains how dynamic weight updates are integrated into the HyperGraphRAG query flow. The integration enables the system to learn from retrieval feedback and continuously improve hyperedge quality.

## Architecture

### Query Flow with Dynamic Updates

```
┌─────────────────────────────────────────────────────────────┐
│                     Query Execution                          │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  1. Extract Keywords from Query                             │
│     ↓                                                        │
│  2. Retrieve Hyperedges (tracked)                           │
│     ↓                                                        │
│  3. Build Context                                           │
│     ↓                                                        │
│  4. Generate Answer with LLM                                │
│     ↓                                                        │
│  5. Save to Cache                                           │
│     ↓                                                        │
│  6. Return Answer ← User gets response immediately          │
│     │                                                        │
│     └──→ [Background Task]                                  │
│          ├─ Extract Feedback Signals                        │
│          ├─ Update Hyperedge Weights                        │
│          └─ Log Update Statistics                           │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## Key Components

### 1. Query Function (`kg_query`)

The main query function in `hypergraphrag/operate.py` orchestrates the entire flow:

```python
async def kg_query(
    query,
    knowledge_graph_inst: BaseGraphStorage,
    entities_vdb: BaseVectorStorage,
    hyperedges_vdb: BaseVectorStorage,
    text_chunks_db: BaseKVStorage[TextChunkSchema],
    query_param: QueryParam,
    global_config: dict,
    hashing_kv: BaseKVStorage = None,
) -> str:
    # ... query processing ...
    
    # Dynamic update happens asynchronously after response
    asyncio.create_task(
        _perform_dynamic_update_async(
            response,
            retrieved_hyperedges,
            knowledge_graph_inst,
            global_config,
            query
        )
    )
    
    return response  # Returns immediately
```

### 2. Async Update Function (`_perform_dynamic_update_async`)

Handles the background update process:

```python
async def _perform_dynamic_update_async(
    answer: str,
    retrieved_hyperedges: list[dict],
    knowledge_graph_inst: BaseGraphStorage,
    global_config: dict,
    query: str = None
):
    # 1. Check if enabled
    # 2. Initialize FeedbackExtractor
    # 3. Initialize WeightUpdater
    # 4. Extract feedback signals
    # 5. Update weights
    # 6. Log results
```

### 3. Hyperedge Tracking

Hyperedges are tracked throughout the retrieval process:

```python
# In _get_edge_data()
retrieved_hyperedges = [
    {
        "id": e["hyperedge"],
        "hyperedge": e["hyperedge"],
        "distance": e.get("rank", 0.5)
    }
    for e in edge_datas
]
```

## Configuration

### Enable/Disable Dynamic Updates

```python
global_config = {
    "addon_params": {
        "dynamic_config": {
            "enabled": True,  # Set to False to disable
            # ... other config ...
        }
    }
}
```

### Update Strategy

Choose from three strategies:

```python
"strategy": "ema"  # Exponential Moving Average (recommended)
"strategy": "additive"  # Direct addition
"strategy": "multiplicative"  # Proportional scaling
```

### Feedback Method

Choose feedback extraction method:

```python
"feedback_method": "embedding"  # Semantic similarity (recommended)
"feedback_method": "citation"  # Text matching
"feedback_method": "hybrid"  # Combination of both
```

### Learning Rate

Control how quickly weights adapt:

```python
"update_alpha": 0.1  # Higher = faster adaptation (0.0 - 1.0)
"decay_factor": 0.99  # Prevents unbounded growth (0.0 - 1.0)
```

## Usage Examples

### Basic Usage

```python
from hypergraphrag.operate import kg_query
from hypergraphrag.base import QueryParam

# Setup configuration
global_config = {
    "llm_model_func": your_llm_function,
    "embedding_func": your_embedding_function,
    "addon_params": {
        "dynamic_config": {
            "enabled": True,
            "strategy": "ema",
            "update_alpha": 0.1,
            "decay_factor": 0.99,
            "feedback_method": "embedding",
            "feedback_threshold": 0.7,
        }
    }
}

# Execute query
query_param = QueryParam(mode="hybrid", top_k=10)
answer = await kg_query(
    query="What is the relationship between A and B?",
    knowledge_graph_inst=graph,
    entities_vdb=entities_vdb,
    hyperedges_vdb=hyperedges_vdb,
    text_chunks_db=text_chunks_db,
    query_param=query_param,
    global_config=global_config,
)

# Answer returns immediately
# Weight updates happen in background
```

### Monitoring Updates

Check logs for update information:

```python
import logging

# Enable debug logging
logging.getLogger("hypergraphrag").setLevel(logging.DEBUG)

# Look for [Async] prefixed messages
# Example output:
# INFO:hypergraphrag:[Async] Updating weights for 5 hyperedges
# DEBUG:hypergraphrag:[Async] Updated <hyperedge>...: feedback=0.850, new_weight=0.723
# INFO:hypergraphrag:[Async] Dynamic update completed: 5/5 hyperedges updated successfully
```

### Checking Weight Changes

```python
# Before query
node_before = await graph.get_node(hyperedge_id)
initial_weight = node_before["dynamic_weight"]

# Execute query
answer = await kg_query(...)

# Wait for async update to complete (optional)
await asyncio.sleep(0.5)

# After query
node_after = await graph.get_node(hyperedge_id)
final_weight = node_after["dynamic_weight"]

print(f"Weight change: {initial_weight:.3f} → {final_weight:.3f}")
print(f"Feedback count: {node_after['feedback_count']}")
```

## Performance Considerations

### Non-Blocking Design

- Query returns immediately after answer generation
- Updates run asynchronously in background
- No impact on query response time

### Concurrency

- Multiple queries can run simultaneously
- Updates are queued and processed independently
- Storage layer handles concurrent updates safely

### Resource Usage

- Feedback extraction: ~50-100ms per query
- Weight updates: ~10-20ms per hyperedge
- Memory: Minimal (no large data structures cached)

## Error Handling

### Graceful Degradation

If dynamic updates fail:
- Query still returns successfully
- Error is logged but doesn't propagate
- System continues to function normally

### Common Issues

1. **Missing embedding function**:
   ```
   WARNING:hypergraphrag:Embedding function not available, skipping dynamic update
   ```
   Solution: Ensure `embedding_func` is in `global_config`

2. **Import errors**:
   ```
   ERROR:hypergraphrag:[Async] Failed to import dynamic modules
   ```
   Solution: Ensure `hypergraphrag.dynamic` module is installed

3. **Storage errors**:
   ```
   ERROR:hypergraphrag:[Async] Failed to update weight for <hyperedge>...
   ```
   Solution: Check storage backend connectivity

## Best Practices

### 1. Start with Conservative Settings

```python
"update_alpha": 0.05,  # Small learning rate
"decay_factor": 0.99,  # Slow decay
```

### 2. Monitor Weight Evolution

Track weight changes over time to ensure stability:

```python
# Check weight history
node = await graph.get_node(hyperedge_id)
history = node.get("weight_history", [])
for entry in history[-5:]:
    print(f"{entry['timestamp']}: {entry['new_weight']:.3f}")
```

### 3. Use Appropriate Feedback Method

- **Embedding**: Best for semantic similarity
- **Citation**: Best for explicit references
- **Hybrid**: Best for comprehensive coverage

### 4. Adjust Based on Domain

Different domains may need different settings:

```python
# Medical domain (conservative)
"update_alpha": 0.05
"feedback_threshold": 0.8

# News domain (aggressive)
"update_alpha": 0.15
"feedback_threshold": 0.6
```

## Testing

### Unit Tests

Run the integration tests:

```bash
python3 test_dynamic_integration.py
```

### Example Scripts

Run the example to see it in action:

```bash
python3 example_dynamic_query_integration.py
```

## Troubleshooting

### Updates Not Happening

1. Check if enabled:
   ```python
   print(global_config["addon_params"]["dynamic_config"]["enabled"])
   ```

2. Check logs for errors:
   ```python
   logging.getLogger("hypergraphrag").setLevel(logging.DEBUG)
   ```

3. Verify hyperedges are being retrieved:
   ```python
   # Add debug logging in _build_query_context
   logger.debug(f"Retrieved {len(retrieved_hyperedges)} hyperedges")
   ```

### Weights Not Changing

1. Check feedback signals:
   - Low similarity may result in minimal changes
   - Increase `update_alpha` for more aggressive updates

2. Check decay factor:
   - High decay (e.g., 0.95) may counteract updates
   - Use 0.99 or higher for stability

3. Check quality constraints:
   - Weights are bounded by quality scores
   - Low quality scores limit weight growth

## Integration with Other Modules

### Quality Assessment

Dynamic updates work with quality scores:

```python
# Quality score sets bounds
min_weight = quality_score * 0.5
max_weight = quality_score * 2.0
```

### Hyperedge Refiner

Can be used together for comprehensive quality management:

```python
# 1. Quality assessment sets initial scores
# 2. Dynamic updates adjust based on usage
# 3. Refiner removes consistently low-quality hyperedges
```

### Efficient Retrieval

Updated weights improve retrieval ranking:

```python
# Retrieval score combines:
score = α × similarity + β × quality + γ × dynamic_weight
```

## References

- Implementation: `hypergraphrag/operate.py`
- Feedback Extractor: `hypergraphrag/dynamic/feedback_extractor.py`
- Weight Updater: `hypergraphrag/dynamic/weight_updater.py`
- Configuration: `config.py`
- Tests: `test_dynamic_integration.py`
- Examples: `example_dynamic_query_integration.py`

## Support

For issues or questions:
1. Check logs for error messages
2. Review configuration settings
3. Run test scripts to verify functionality
4. Consult task summary: `.kiro/specs/dynhyperrag-quality-aware/TASK_9_SUMMARY.md`
