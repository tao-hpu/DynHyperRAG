# Ablation Studies for DynHyperRAG

This module implements comprehensive ablation experiments to measure the contribution of individual features and modules to the overall DynHyperRAG system performance.

## Overview

Ablation studies systematically disable components of the system to measure their individual contributions. This helps answer critical research questions:

1. **Which quality features are most important?** (Feature Ablation)
2. **Which modules provide the most value?** (Module Ablation)
3. **Is the complexity of the full system justified?**

## Components

### 1. Feature Ablation Experiment

Tests the contribution of individual quality features by disabling them one at a time.

**Features tested:**
- `degree_centrality`: Node connectivity (default weight: 0.2)
- `betweenness`: Bridge importance (default weight: 0.15)
- `clustering`: Local density (default weight: 0.15)
- `coherence`: Semantic consistency (default weight: 0.3)
- `text_quality`: Text completeness (default weight: 0.2)

**Usage:**
```python
from hypergraphrag.evaluation.ablation import FeatureAblationExperiment
from hypergraphrag.kg import NetworkXStorage

# Initialize
graph_storage = NetworkXStorage()
config = {
    'feature_weights': {
        'degree_centrality': 0.2,
        'betweenness': 0.15,
        'clustering': 0.15,
        'coherence': 0.3,
        'text_quality': 0.2
    }
}

# Create experiment
experiment = FeatureAblationExperiment(graph_storage, config)

# Run ablation study
results = await experiment.run_ablation_study(
    hyperedge_ids=hyperedge_ids,
    ground_truth=ground_truth_scores
)

# Generate report
report = experiment.generate_report(output_path)
```

**Output:**
- Feature importance ranking
- Contribution of each feature (absolute and relative)
- Statistical significance tests
- Markdown report

### 2. Module Ablation Experiment

Tests the contribution of entire modules by comparing different system configurations.

**Modules tested:**
- **Quality Assessment**: Hyperedge quality scoring
- **Dynamic Updates**: Weight adjustment based on feedback
- **Entity Type Filtering**: Pre-filtering by entity types

**Configurations tested:**
1. Full system (all modules enabled)
2. Without quality assessment
3. Without dynamic updates
4. Without entity type filtering
5. Minimal system (static HyperGraphRAG baseline)

**Usage:**
```python
from hypergraphrag.evaluation.ablation import ModuleAblationExperiment

# Initialize
config = {'output_dir': 'outputs/ablation_studies'}
experiment = ModuleAblationExperiment(config)

# Run ablation study
results = await experiment.run_ablation_study(
    test_queries=test_queries,
    expected_answers=expected_answers,
    dynhyperrag_instance=rag_instance
)

# Generate report
report = experiment.generate_report(output_path)
```

**Output:**
- Module importance ranking
- Performance comparison across configurations
- Statistical significance tests
- Markdown report

### 3. Ablation Study Runner

Unified interface to run both feature and module ablation studies together.

**Usage:**
```python
from hypergraphrag.evaluation.ablation import AblationStudyRunner

# Initialize
runner = AblationStudyRunner(graph_storage, config)

# Run all ablation studies
results = await runner.run_all_ablation_studies(
    hyperedge_ids=hyperedge_ids,
    test_queries=test_queries,
    ground_truth=ground_truth,
    expected_answers=expected_answers,
    dynhyperrag_instance=rag_instance
)
```

**Output:**
- Combined results from all ablation studies
- Feature ablation report
- Module ablation report
- Combined summary report
- JSON results file

## Experimental Workflow

### Feature Ablation Workflow

```
1. Evaluate full model (all features enabled)
   ↓
2. For each feature:
   - Disable the feature
   - Re-evaluate quality scores
   - Measure performance drop
   ↓
3. Calculate feature contributions
   ↓
4. Perform statistical tests
   ↓
5. Rank features by importance
   ↓
6. Generate report
```

### Module Ablation Workflow

```
1. Test full system (all modules enabled)
   ↓
2. Test configurations:
   - Without quality assessment
   - Without dynamic updates
   - Without entity filtering
   - Minimal system (no modules)
   ↓
3. Calculate module contributions
   ↓
4. Perform statistical tests
   ↓
5. Rank modules by importance
   ↓
6. Generate report
```

## Statistical Analysis

Both ablation experiments include comprehensive statistical analysis:

- **Paired t-test**: Parametric test for mean differences
- **Wilcoxon signed-rank test**: Non-parametric alternative
- **Effect size (Cohen's d)**: Magnitude of differences
- **Confidence intervals**: Uncertainty quantification
- **Multiple comparison correction**: Bonferroni and Holm methods

## Report Generation

All experiments generate detailed markdown reports including:

### Feature Ablation Report
- Summary statistics
- Feature importance ranking table
- Detailed results for each feature
- Statistical significance indicators
- Visualization-ready data

### Module Ablation Report
- Summary statistics
- Module importance ranking table
- Configuration comparison table
- Statistical significance indicators
- Performance metrics

### Combined Summary Report
- Key findings from both studies
- Top contributors at feature and module levels
- Overall system improvement analysis
- Links to detailed reports

## Example Usage

See `examples/example_ablation_studies.py` for complete examples:

```bash
# Run ablation study examples
python examples/example_ablation_studies.py
```

This will:
1. Run feature ablation study
2. Run module ablation study
3. Run complete ablation suite
4. Generate all reports in `outputs/ablation_studies/`

## Integration with Experiment Pipeline

Ablation studies can be integrated into the main experiment pipeline:

```python
from hypergraphrag.evaluation.pipeline import ExperimentPipeline
from hypergraphrag.evaluation.ablation import run_ablation_studies

# Run main experiments
pipeline = ExperimentPipeline(config)
main_results = await pipeline.run_full_pipeline("cail2019")

# Run ablation studies
ablation_results = await run_ablation_studies(
    graph_storage=pipeline.graph_storage,
    hyperedge_ids=pipeline.hyperedge_ids,
    test_queries=pipeline.test_queries,
    config=config
)
```

## Output Files

All results are saved to the configured output directory (default: `outputs/ablation_studies/`):

```
outputs/ablation_studies/
├── feature_ablation_report.md      # Feature ablation detailed report
├── module_ablation_report.md       # Module ablation detailed report
├── ablation_summary.md             # Combined summary
└── ablation_results.json           # Complete results in JSON format
```

## Requirements

**Required:**
- `numpy`: Numerical computations
- `scipy`: Statistical tests
- `asyncio`: Asynchronous execution

**Optional (for full functionality):**
- `hypergraphrag.quality.QualityScorer`: For feature ablation
- `hypergraphrag.dynamic.WeightUpdater`: For module ablation
- `hypergraphrag.retrieval`: For module ablation

## Research Applications

Ablation studies support several research objectives:

1. **Feature Analysis**: Identify which graph-theoretic features best predict hyperedge quality
2. **Module Justification**: Demonstrate that each module contributes meaningfully to performance
3. **Complexity Trade-offs**: Quantify the benefit of added complexity
4. **Design Insights**: Guide future system improvements
5. **Publication**: Provide rigorous experimental validation for papers

## Best Practices

1. **Sample Size**: Use sufficient hyperedges/queries for statistical power (n ≥ 30 recommended)
2. **Ground Truth**: Provide ground truth labels when available for more meaningful analysis
3. **Multiple Runs**: Run experiments with different random seeds for robustness
4. **Baseline Comparison**: Always compare against static HyperGraphRAG baseline
5. **Report Everything**: Include both significant and non-significant results

## Troubleshooting

**Issue**: "QualityScorer not available"
- **Solution**: Ensure quality module is implemented (Task 4)

**Issue**: "Not enough samples for statistical tests"
- **Solution**: Increase number of test hyperedges/queries (minimum 3, recommended 30+)

**Issue**: "Mock scores returned"
- **Solution**: Integrate with actual DynHyperRAG instance instead of using placeholders

## References

- Design Document: `.kiro/specs/dynhyperrag-quality-aware/design.md`
- Requirements: `.kiro/specs/dynhyperrag-quality-aware/requirements.md` (Requirement 4.2, 4.3)
- Tasks: `.kiro/specs/dynhyperrag-quality-aware/tasks.md` (Task 22)

## Future Enhancements

Potential extensions for ablation studies:

1. **Interaction Effects**: Test combinations of disabled features/modules
2. **Incremental Ablation**: Build up from minimal to full system
3. **Domain-Specific Analysis**: Separate ablation for legal vs academic domains
4. **Temporal Analysis**: Track feature/module importance over time
5. **Visualization**: Interactive plots of ablation results

---

**Status**: ✅ Implemented (Task 22)
**Last Updated**: 2024
