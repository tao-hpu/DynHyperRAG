# Quality-Aware Ranker

## Overview

The `QualityAwareRanker` implements a composite ranking algorithm that combines semantic similarity, quality scores, and dynamic weights to prioritize high-quality hyperedges during retrieval. This is a core component of the DynHyperRAG system's efficient retrieval module.

## Key Features

- **Composite Scoring**: Combines three factors with configurable weights
  - α × similarity (from vector retrieval)
  - β × quality (from quality assessment)
  - γ × dynamic_weight (from feedback-based updates)
- **Flexible Configuration**: Adjustable weight parameters for different use cases
- **Ranking Explanation**: Optional detailed breakdown of scoring components
- **Robust Fallbacks**: Handles missing fields gracefully with sensible defaults

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                  Quality-Aware Ranking                       │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Input: Vector Retrieval Results                            │
│  ┌────────────────────────────────────────────────────┐    │
│  │ Hyperedge 1: distance=0.9, quality=0.7, weight=0.8│    │
│  │ Hyperedge 2: distance=0.8, quality=0.9, weight=0.9│    │
│  │ Hyperedge 3: distance=0.7, quality=0.6, weight=0.7│    │
│  └────────────────────────────────────────────────────┘    │
│                          ↓                                   │
│  ┌────────────────────────────────────────────────────┐    │
│  │         Composite Scoring Function                  │    │
│  │  score = α×sim + β×quality + γ×dynamic_weight     │    │
│  └────────────────────────────────────────────────────┘    │
│                          ↓                                   │
│  Output: Ranked Results                                     │
│  ┌────────────────────────────────────────────────────┐    │
│  │ Hyperedge 2: final_score=0.87 (BEST)              │    │
│  │ Hyperedge 1: final_score=0.80                      │    │
│  │ Hyperedge 3: final_score=0.67                      │    │
│  └────────────────────────────────────────────────────┘    │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## Usage

### Basic Usage

```python
from hypergraphrag.retrieval.quality_ranker import QualityAwareRanker

# Initialize ranker with default weights
config = {
    "similarity_weight": 0.5,  # α
    "quality_weight": 0.3,     # β
    "dynamic_weight": 0.2      # γ
}
ranker = QualityAwareRanker(config)

# Get results from vector retrieval
results = await vdb.query(query, top_k=20)

# Re-rank by quality
ranked_results = await ranker.rank_hyperedges(query, results)

# Use top results
for he in ranked_results[:5]:
    print(f"Score: {he['final_score']:.3f} - {he['hyperedge_name']}")
```

### With Ranking Explanation

```python
config = {
    "similarity_weight": 0.5,
    "quality_weight": 0.3,
    "dynamic_weight": 0.2,
    "provide_explanation": True  # Enable explanations
}
ranker = QualityAwareRanker(config)

ranked_results = await ranker.rank_hyperedges(query, results)

# Get explanation for top result
explanation = ranker.explain_ranking(ranked_results[0])
print(explanation)
```

Output:
```
Final Score: 0.850
  - Similarity: 0.900 (weight: 0.5)
  - Quality: 0.800 (weight: 0.3)
  - Dynamic Weight: 0.850 (weight: 0.2)
Computation: 0.5×0.900 + 0.3×0.800 + 0.2×0.850 = 0.850
```

### Convenience Function

```python
from hypergraphrag.retrieval.quality_ranker import rank_by_quality

# Quick ranking with custom weights
ranked = await rank_by_quality(
    hyperedges=results,
    query=query,
    similarity_weight=0.6,
    quality_weight=0.3,
    dynamic_weight=0.1
)
```

### Dynamic Weight Adjustment

```python
# Initialize with default weights
ranker = QualityAwareRanker({})

# Adjust weights based on use case
if use_case == "high_precision":
    # Prioritize quality over similarity
    ranker.set_weights(alpha=0.3, beta=0.5, gamma=0.2)
elif use_case == "high_recall":
    # Prioritize similarity
    ranker.set_weights(alpha=0.7, beta=0.2, gamma=0.1)
elif use_case == "feedback_driven":
    # Prioritize dynamic weights from user feedback
    ranker.set_weights(alpha=0.4, beta=0.2, gamma=0.4)

# Get current weights
weights = ranker.get_weights()
print(f"Current weights: α={weights['alpha']}, β={weights['beta']}, γ={weights['gamma']}")
```

## Configuration Options

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `similarity_weight` (α) | float | 0.5 | Weight for semantic similarity from vector retrieval |
| `quality_weight` (β) | float | 0.3 | Weight for quality score from quality assessment |
| `dynamic_weight` (γ) | float | 0.2 | Weight for dynamic weight from feedback updates |
| `normalize_scores` | bool | True | Whether to normalize final scores to [0, 1] |
| `provide_explanation` | bool | False | Whether to include ranking explanations |

**Note**: Weights should ideally sum to 1.0 for interpretability, though the system will work with any positive weights.

## Scoring Formula

The final ranking score is computed as:

```
final_score = α × similarity + β × quality + γ × dynamic_weight
```

Where:
- **similarity**: Semantic similarity from vector retrieval (0-1, higher is better)
- **quality**: Quality score from graph-based quality assessment (0-1)
- **dynamic_weight**: Dynamically updated weight based on feedback (0-1)

### Field Extraction and Fallbacks

The ranker extracts scores from hyperedge dictionaries with the following fallback logic:

1. **Similarity**:
   - Primary: `distance` field (assumed to be similarity score 0-1)
   - Fallback: `similarity` field
   - Default: 0.5

2. **Quality**:
   - Primary: `quality_score` field
   - Default: 0.5

3. **Dynamic Weight**:
   - Primary: `dynamic_weight` field
   - Fallback 1: `quality_score` field
   - Fallback 2: `weight` field (normalized from 0-100 to 0-1)
   - Default: 0.5

## Integration with DynHyperRAG Pipeline

The quality-aware ranker fits into the retrieval pipeline as follows:

```python
# 1. Entity type filtering (optional)
from hypergraphrag.retrieval.entity_filter import EntityTypeFilter

filter = EntityTypeFilter(graph, config)
relevant_types = await filter.identify_relevant_types(query)

# 2. Vector retrieval
results = await vdb.query(query, top_k=50)

# 3. Filter by entity types
hyperedge_ids = [r['hyperedge_name'] for r in results]
filtered_ids, stats = await filter.filter_hyperedges_by_type(
    hyperedge_ids, relevant_types
)

# 4. Get full hyperedge data
filtered_results = [r for r in results if r['hyperedge_name'] in filtered_ids]

# 5. Quality-aware re-ranking
ranker = QualityAwareRanker(config)
ranked_results = await ranker.rank_hyperedges(query, filtered_results)

# 6. Use top-k results
top_results = ranked_results[:10]
```

## Use Case Examples

### 1. Precision-Focused Retrieval

When accuracy is critical (e.g., medical diagnosis, legal research):

```python
config = {
    "similarity_weight": 0.3,  # Lower weight on similarity
    "quality_weight": 0.5,     # Higher weight on quality
    "dynamic_weight": 0.2
}
```

### 2. Recall-Focused Retrieval

When coverage is important (e.g., exploratory search):

```python
config = {
    "similarity_weight": 0.7,  # Higher weight on similarity
    "quality_weight": 0.2,     # Lower weight on quality
    "dynamic_weight": 0.1
}
```

### 3. Feedback-Driven Retrieval

When user feedback is available and reliable:

```python
config = {
    "similarity_weight": 0.3,
    "quality_weight": 0.3,
    "dynamic_weight": 0.4      # Higher weight on feedback
}
```

### 4. Balanced Retrieval

Default balanced approach:

```python
config = {
    "similarity_weight": 0.5,
    "quality_weight": 0.3,
    "dynamic_weight": 0.2
}
```

## Performance Considerations

### Computational Complexity

- **Time Complexity**: O(n) where n is the number of hyperedges to rank
- **Space Complexity**: O(n) for storing ranked results
- **Overhead**: Minimal - simple arithmetic operations per hyperedge

### Optimization Tips

1. **Pre-filter before ranking**: Use entity type filtering to reduce n
2. **Batch processing**: Rank in batches if dealing with very large result sets
3. **Cache ranker instance**: Reuse the same ranker for multiple queries
4. **Disable explanations**: Set `provide_explanation=False` for production

## Testing

Run the test suite:

```bash
python test_quality_ranker.py
```

Test coverage includes:
- Initialization with various configurations
- Ranking with complete and missing fields
- Fallback logic for missing scores
- Score normalization
- Ranking explanations
- Realistic ranking scenarios (quality vs. similarity tradeoffs)

## Related Modules

- **EntityTypeFilter** (`entity_filter.py`): Pre-filters hyperedges by entity types
- **QualityScorer** (`hypergraphrag/quality/scorer.py`): Computes quality scores
- **WeightUpdater** (`hypergraphrag/dynamic/weight_updater.py`): Updates dynamic weights
- **FeedbackExtractor** (`hypergraphrag/dynamic/feedback_extractor.py`): Extracts feedback signals

## References

- Design Document: `.kiro/specs/dynhyperrag-quality-aware/design.md`
- Requirements: `.kiro/specs/dynhyperrag-quality-aware/requirements.md` (Requirement 3.2)
- Task: `.kiro/specs/dynhyperrag-quality-aware/tasks.md` (Task 11.1)

## Ranking Visualization

The `RankingVisualizer` module provides comprehensive visualization and explanation tools to help understand ranking decisions.

### Text-Based Reports

```python
from hypergraphrag.retrieval.ranking_visualizer import RankingVisualizer

visualizer = RankingVisualizer()

# Generate text report
report = visualizer.generate_text_report(ranked_results, top_k=10)
print(report)
```

Output:
```
================================================================================
RANKING ANALYSIS REPORT
================================================================================

Total Results: 20
Score Range: [0.450, 0.890]
Mean Score: 0.672

TOP 10 RESULTS:
--------------------------------------------------------------------------------

#1 - Final Score: 0.890
  Similarity: 0.950
  Quality: 0.850
  Dynamic Weight: 0.900
  Computation: 0.5×0.950 + 0.3×0.850 + 0.2×0.900 = 0.890
  Content: Entity A has strong relationship with Entity B...
```

### Visual Plots

#### 1. Component Contribution Chart

Shows how each factor contributes to the final score:

```python
# Generate stacked bar chart
fig = visualizer.plot_ranking_components(ranked_results, top_k=10)
visualizer.save_visualization("ranking_components.png")
```

#### 2. Score Distribution

Visualizes the distribution of final scores:

```python
fig = visualizer.plot_score_distribution(ranked_results, bins=20)
visualizer.save_visualization("score_distribution.png")
```

#### 3. Factor Comparison

Compares raw factor values across top results:

```python
fig = visualizer.plot_factor_comparison(ranked_results, top_k=10)
visualizer.save_visualization("factor_comparison.png")
```

#### 4. Weight Impact Analysis

Shows contribution breakdown with pie charts:

```python
fig = visualizer.plot_weight_impact(ranked_results, top_k=5)
visualizer.save_visualization("weight_impact.png")
```

### Comprehensive Dashboard

Create a multi-panel dashboard with all visualizations:

```python
from hypergraphrag.retrieval.ranking_visualizer import create_ranking_dashboard

create_ranking_dashboard(
    ranked_results,
    output_path="ranking_dashboard.png",
    top_k=10
)
```

### Data Export

Export ranking data for further analysis:

```python
# Export as JSON
visualizer.export_ranking_data(
    ranked_results,
    "ranking_results.json",
    format="json"
)

# Export as CSV
visualizer.export_ranking_data(
    ranked_results,
    "ranking_results.csv",
    format="csv"
)
```

### Visualization Requirements

Install matplotlib for visualization features:

```bash
pip install matplotlib numpy
```

## Future Enhancements

Potential improvements for future versions:

1. **Learned Weights**: Use machine learning to learn optimal weights from user feedback
2. **Context-Aware Ranking**: Adjust weights based on query type or domain
3. **Multi-Objective Ranking**: Support Pareto-optimal ranking for multiple objectives
4. **Ranking Diversity**: Add diversity penalty to avoid redundant results
5. **Temporal Decay**: Reduce scores for outdated hyperedges over time
6. **Interactive Visualizations**: Add interactive plots with Plotly or Bokeh
7. **Real-time Monitoring**: Dashboard for monitoring ranking performance in production
