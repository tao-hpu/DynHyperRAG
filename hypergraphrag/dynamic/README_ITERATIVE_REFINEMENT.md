# Iterative Hyperedge Refinement

## Overview

The **Iterative Refinement** mechanism automatically improves low-quality hyperedges by triggering re-extraction with improved prompts. This feature is part of the DynHyperRAG quality-aware dynamic hypergraph system.

## Key Features

- **Automatic Quality Detection**: Identifies low-quality hyperedges based on quality scores
- **Source Text Retrieval**: Retrieves original source text chunks for re-extraction
- **Improved Prompts**: Uses quality feedback to generate better extraction prompts
- **Quality Comparison**: Compares new vs. old hyperedge quality scores
- **Selective Replacement**: Only replaces hyperedges if quality improves
- **Multiple Iterations**: Supports iterative refinement with multiple attempts
- **Detailed Statistics**: Provides comprehensive refinement metrics

## How It Works

### 1. Quality Assessment

The system first identifies low-quality hyperedges using the quality scorer:

```python
from hypergraphrag.quality.scorer import QualityScorer

scorer = QualityScorer(graph, config)
quality_result = await scorer.compute_quality_score(hyperedge_id)
```

### 2. Iterative Refinement Process

For each low-quality hyperedge:

1. **Retrieve Source Text**: Get the original text chunks used for extraction
2. **Generate Improved Prompt**: Create a refinement prompt with quality feedback
3. **Re-extract**: Use LLM to extract a new hyperedge with improved prompt
4. **Compute Quality**: Calculate quality score for the new hyperedge
5. **Compare & Replace**: Replace if new quality > old quality
6. **Iterate**: Repeat for multiple iterations if configured

### 3. Improved Prompt Template

The refinement prompt includes:
- Current hyperedge text
- Current quality score
- Specific improvement instructions
- Source text for re-extraction

Example prompt structure:

```
---Role---
You are an expert knowledge extraction assistant tasked with improving 
the quality of extracted knowledge fragments.

---Context---
The following knowledge fragment was previously extracted but has low 
quality (score: 0.30/1.0).
Current fragment: "Alice works somewhere"

---Goal---
Re-extract a higher quality knowledge fragment that:
1. Is more complete and coherent
2. Captures the most important relationships
3. Connects relevant entities clearly
4. Is factually accurate and well-formed

---Source Text---
Alice works at TechCorp as a software engineer. She collaborates with 
Bob on AI projects.

---Output---
[Improved extraction]
```

## Usage

### Basic Usage

```python
from hypergraphrag.dynamic.refiner import HyperedgeRefiner

# Initialize refiner
config = {
    'quality_threshold': 0.5,
    'filter_mode': 'soft',
}
refiner = HyperedgeRefiner(graph, config)

# Perform iterative refinement
result = await refiner.iterative_refine_hyperedges(
    hyperedge_ids=low_quality_ids,
    text_chunks_db=text_chunks_db,
    llm_model_func=llm_func,
    embedding_func=embedding_func,
    quality_scorer=scorer,
    global_config=config,
    max_iterations=2
)

print(f"Improved {result['improved_count']} hyperedges")
print(f"Average improvement: {result['avg_quality_improvement']:.3f}")
```

### Integration with HyperGraphRAG

```python
from hypergraphrag import HyperGraphRAG
from hypergraphrag.dynamic.refiner import HyperedgeRefiner
from hypergraphrag.quality.scorer import QualityScorer

# Initialize system
rag = HyperGraphRAG(working_dir="./workspace")

# Insert documents
await rag.insert(documents)

# Compute quality scores
scorer = QualityScorer(rag.knowledge_graph_inst, quality_config)
quality_scores = {}
for he_id in hyperedge_ids:
    result = await scorer.compute_quality_score(he_id)
    quality_scores[he_id] = result['quality_score']

# Identify low-quality hyperedges
low_quality_ids = [
    he_id for he_id, quality in quality_scores.items()
    if quality < 0.5
]

# Refine low-quality hyperedges
refiner = HyperedgeRefiner(rag.knowledge_graph_inst, refiner_config)
result = await refiner.iterative_refine_hyperedges(
    hyperedge_ids=low_quality_ids,
    text_chunks_db=rag.text_chunks,
    llm_model_func=rag.llm_model_func,
    embedding_func=rag.embedding_func,
    quality_scorer=scorer,
    global_config=rag.global_config,
    max_iterations=2
)
```

## Configuration

### Refiner Configuration

```python
refiner_config = {
    # Quality threshold for filtering
    'quality_threshold': 0.5,
    
    # Filter mode: 'soft' (reduce weight) or 'hard' (delete)
    'filter_mode': 'soft',
    
    # Threshold strategy: 'fixed', 'percentile', or 'f1_optimal'
    'threshold_strategy': 'fixed',
    
    # Percentile for threshold (if using 'percentile' strategy)
    'percentile': 25,
    
    # Weight multiplier for soft filtering
    'soft_filter_weight_multiplier': 0.1,
    
    # Track filtering decisions
    'track_decisions': True,
}
```

### Quality Scorer Configuration

```python
quality_config = {
    'feature_weights': {
        'degree_centrality': 0.2,
        'betweenness': 0.15,
        'clustering': 0.15,
        'coherence': 0.3,
        'text_quality': 0.2
    }
}
```

## Return Values

The `iterative_refine_hyperedges` method returns a dictionary with:

```python
{
    'refined_count': int,              # Number of hyperedges processed
    'improved_count': int,             # Number with quality improvement
    'failed_count': int,               # Number of failures
    'improvement_rate': float,         # Proportion improved (0-1)
    'avg_quality_improvement': float,  # Average quality gain
    'quality_improvements': list,      # List of improvements
    'refinement_details': list,        # Detailed refinement info
}
```

### Refinement Details

Each entry in `refinement_details` contains:

```python
{
    'hyperedge_id': str,        # Hyperedge identifier
    'old_quality': float,       # Original quality score
    'new_quality': float,       # New quality score
    'improvement': float,       # Quality improvement
    'old_text': str,           # Original hyperedge text
    'new_text': str,           # New hyperedge text
}
```

## Performance Considerations

### Computational Cost

Iterative refinement is computationally expensive because it:
- Retrieves source text chunks
- Calls LLM for re-extraction (multiple times per hyperedge)
- Computes quality scores for new hyperedges
- Updates graph structure

**Recommendation**: Use selectively on low-quality hyperedges only.

### Optimization Strategies

1. **Batch Processing**: Process multiple hyperedges in parallel
2. **Iteration Limit**: Set reasonable `max_iterations` (1-3)
3. **Quality Threshold**: Only refine hyperedges below threshold
4. **Caching**: Cache LLM responses to avoid redundant calls
5. **Async Operations**: Use asyncio for parallel processing

### Example: Batch Refinement

```python
# Process in batches
batch_size = 10
for i in range(0, len(low_quality_ids), batch_size):
    batch = low_quality_ids[i:i+batch_size]
    result = await refiner.iterative_refine_hyperedges(
        hyperedge_ids=batch,
        text_chunks_db=text_chunks_db,
        llm_model_func=llm_func,
        embedding_func=embedding_func,
        quality_scorer=scorer,
        global_config=config,
        max_iterations=1
    )
    print(f"Batch {i//batch_size + 1}: {result['improved_count']} improved")
```

## Best Practices

### 1. Quality Threshold Selection

Choose an appropriate quality threshold:
- **Conservative (0.3-0.4)**: Only refine very low quality
- **Moderate (0.5-0.6)**: Refine below-average quality
- **Aggressive (0.7+)**: Refine most hyperedges

### 2. Iteration Count

Balance quality improvement vs. computational cost:
- **1 iteration**: Fast, moderate improvement
- **2-3 iterations**: Better improvement, higher cost
- **>3 iterations**: Diminishing returns

### 3. Monitoring

Track refinement metrics:

```python
# Log refinement statistics
logger.info(f"Refinement rate: {result['improvement_rate']:.1%}")
logger.info(f"Avg improvement: {result['avg_quality_improvement']:.3f}")

# Analyze improvements
for detail in result['refinement_details']:
    if detail['improvement'] > 0.2:
        logger.info(f"Significant improvement: {detail['hyperedge_id']}")
```

### 4. Error Handling

Handle refinement failures gracefully:

```python
try:
    result = await refiner.iterative_refine_hyperedges(...)
    
    if result['failed_count'] > 0:
        logger.warning(f"{result['failed_count']} refinements failed")
        
except Exception as e:
    logger.error(f"Refinement error: {e}")
    # Fallback to original hyperedges
```

## Examples

See the following files for complete examples:
- `example_iterative_refinement.py`: Full demonstration
- `test_iterative_refinement.py`: Unit tests

## Limitations

1. **LLM Dependency**: Requires LLM access for re-extraction
2. **Source Text Required**: Cannot refine if source text is missing
3. **Computational Cost**: Expensive for large-scale refinement
4. **Quality Guarantee**: No guarantee of improvement
5. **Entity Changes**: May change connected entities

## Future Enhancements

Potential improvements:
- **Adaptive Prompts**: Learn better prompts from successful refinements
- **Multi-Model Ensemble**: Use multiple LLMs for refinement
- **Incremental Refinement**: Refine only specific parts of hyperedges
- **Quality Prediction**: Predict refinement success before attempting
- **Parallel Refinement**: Distributed refinement for large graphs

## Related Components

- **Quality Scorer** (`hypergraphrag/quality/scorer.py`): Computes quality scores
- **Hyperedge Refiner** (`hypergraphrag/dynamic/refiner.py`): Main refinement logic
- **Weight Updater** (`hypergraphrag/dynamic/weight_updater.py`): Dynamic weight updates
- **Feedback Extractor** (`hypergraphrag/dynamic/feedback_extractor.py`): Extracts feedback signals

## References

- Design Document: `.kiro/specs/dynhyperrag-quality-aware/design.md`
- Requirements: `.kiro/specs/dynhyperrag-quality-aware/requirements.md` (Requirement 2.3)
- Tasks: `.kiro/specs/dynhyperrag-quality-aware/tasks.md` (Task 8.3)
