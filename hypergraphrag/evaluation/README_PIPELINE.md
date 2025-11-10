# Experiment Pipeline for DynHyperRAG

This document describes the automated experiment pipeline for evaluating DynHyperRAG performance.

## Overview

The `ExperimentPipeline` class provides a comprehensive framework for running reproducible experiments that evaluate DynHyperRAG against baseline methods. It automates the entire experimental workflow from data loading to statistical analysis.

## Features

- **Automated Workflow**: Complete pipeline from data loading to report generation
- **YAML Configuration**: Experiment configuration via YAML files for reproducibility
- **Baseline Comparison**: Automatic comparison with multiple baseline methods
- **Statistical Testing**: Built-in statistical significance tests (t-test, Wilcoxon)
- **Comprehensive Metrics**: Intrinsic quality, retrieval performance, and efficiency metrics
- **Experiment Tracking**: Metadata tracking including git commit, timestamps, and configuration
- **Result Persistence**: Automatic saving of results in JSON and Markdown formats

## Pipeline Stages

The experiment pipeline consists of 9 stages:

1. **Data Loading**: Load and preprocess dataset (CAIL2019, PubMed, AMiner)
2. **Hyperedge Extraction**: Extract hyperedges from documents using LLM
3. **Quality Scoring**: Compute quality scores for all hyperedges
4. **Intrinsic Evaluation**: Evaluate hyperedge quality against ground truth
5. **Retrieval Evaluation**: Evaluate end-to-end retrieval and generation performance
6. **Efficiency Evaluation**: Measure computational efficiency and resource usage
7. **Baseline Comparison**: Compare with LLM confidence, rule-based, and static baselines
8. **Statistical Testing**: Perform significance tests on performance differences
9. **Report Generation**: Generate comprehensive experiment reports

## Usage

### Basic Usage

```python
from hypergraphrag.evaluation import ExperimentPipeline

# Create configuration
config = {
    "experiment_name": "dynhyperrag_test",
    "dataset": {
        "name": "cail2019",
        "path": "expr/cail2019",
    },
    "model": {
        "llm_model": "gpt-4o-mini",
        "embedding_model": "text-embedding-3-small",
    },
    "evaluation": {
        "metrics": ["mrr", "precision_at_k", "recall_at_k"],
        "k_values": [1, 5, 10],
    },
    "output_dir": "expr/experiments",
    "random_seed": 42,
}

# Initialize and run pipeline
pipeline = ExperimentPipeline(config)
results = await pipeline.run_full_pipeline("cail2019")
```

### Using YAML Configuration

```python
from hypergraphrag.evaluation import run_experiment_from_config

# Run experiment from YAML file
results = await run_experiment_from_config(
    "examples/experiment_config_example.yaml",
    "cail2019"
)
```

### Running Ablation Studies

```python
# Test different feature combinations
configs = {
    "full": {"quality": True, "dynamic": True, "filtering": True},
    "no_quality": {"quality": False, "dynamic": True, "filtering": True},
    "no_dynamic": {"quality": True, "dynamic": False, "filtering": True},
    "static": {"quality": False, "dynamic": False, "filtering": False},
}

results_all = {}
for name, features in configs.items():
    config["experiment_name"] = f"ablation_{name}"
    config["dynhyperrag"] = features
    
    pipeline = ExperimentPipeline(config)
    results_all[name] = await pipeline.run_full_pipeline("cail2019")
```

## Configuration

### YAML Configuration Format

```yaml
# Experiment metadata
experiment_name: "dynhyperrag_experiment"
description: "Experiment description"

# Dataset configuration
dataset:
  name: "cail2019"
  path: "expr/cail2019"
  split: "test"
  max_samples: null  # null for all, or number for subset

# Model configuration
model:
  llm_model: "gpt-4o-mini"
  embedding_model: "text-embedding-3-small"

# DynHyperRAG features
dynhyperrag:
  quality:
    enabled: true
    mode: "unsupervised"
    feature_weights:
      degree_centrality: 0.2
      betweenness: 0.15
      clustering: 0.15
      coherence: 0.3
      text_quality: 0.2
  
  dynamic:
    enabled: true
    strategy: "ema"
    update_alpha: 0.1
    decay_factor: 0.99
  
  retrieval:
    entity_filter_enabled: true
    domain: "legal"
    similarity_weight: 0.5
    quality_weight: 0.3
    dynamic_weight: 0.2

# Evaluation configuration
evaluation:
  metrics: ["mrr", "precision_at_k", "recall_at_k", "f1_at_k"]
  k_values: [1, 3, 5, 10]
  baselines: ["llm_confidence", "rule_based", "static_hypergraphrag"]
  statistical_tests: ["ttest", "wilcoxon"]

# Output configuration
output:
  dir: "expr/experiments"
  save_intermediate: true
  save_predictions: true

# Reproducibility
random_seed: 42
```

See `examples/experiment_config_example.yaml` for a complete example.

## Output

The pipeline generates the following outputs:

### JSON Report

Complete experimental results in JSON format:

```json
{
  "metadata": {
    "experiment_name": "...",
    "start_time": "...",
    "duration_seconds": 123.45,
    "random_seed": 42,
    "git_commit": "..."
  },
  "results": {
    "intrinsic_metrics": {...},
    "extrinsic_metrics": {...},
    "efficiency_metrics": {...},
    "baseline_comparisons": {...},
    "statistical_tests": {...}
  },
  "summary": {...}
}
```

### Markdown Summary

Human-readable summary in Markdown format:

```markdown
# Experiment Report: dynhyperrag_experiment

## Metadata
- **Experiment Name**: dynhyperrag_experiment
- **Start Time**: 2024-01-01T12:00:00
- **Duration**: 123.45 seconds
- **Random Seed**: 42

## Summary

### Intrinsic Quality
- **f1_score**: 0.8234
- **correlation**: 0.7456

### Retrieval Performance
- **mrr**: 0.6789
- **precision_at_5**: 0.7123
- **recall_at_5**: 0.6543

### Efficiency
- **mean_retrieval_time**: 0.234 seconds
- **memory_usage_mb**: 512.34 MB
```

## Metrics

### Intrinsic Quality Metrics

Evaluate hyperedge extraction quality:

- **Precision/Recall/F1**: Accuracy of hyperedge extraction
- **Quality Score Correlation**: Correlation between predicted and true quality
- **ROC AUC**: Discriminative power of quality scores

### Extrinsic Performance Metrics

Evaluate end-to-end retrieval performance:

- **MRR**: Mean Reciprocal Rank
- **Precision@K**: Precision at top K results
- **Recall@K**: Recall at top K results
- **F1@K**: F1 score at top K results
- **BLEU/ROUGE**: Answer quality metrics
- **Hallucination Rate**: Percentage of unsupported claims
- **Reasoning Completeness**: Coverage of expected entities

### Efficiency Metrics

Evaluate computational efficiency:

- **Retrieval Time**: Mean, median, P95 retrieval latency
- **Resource Usage**: CPU, memory, thread count
- **API Cost**: Token usage for LLM calls
- **Storage Requirements**: Graph and vector database size

## Baseline Methods

The pipeline compares DynHyperRAG against:

1. **LLM Confidence Baseline**: Uses original LLM extraction confidence as quality score
2. **Rule-based Baseline**: Simple heuristics (degree + text length)
3. **Random Baseline**: Random quality assignment (lower bound)
4. **Static HyperGraphRAG**: Original system without dynamic features

## Statistical Testing

The pipeline performs statistical significance tests:

- **Paired t-test**: Parametric test for mean differences
- **Wilcoxon signed-rank test**: Non-parametric alternative
- **Significance level**: α = 0.05 (configurable)

Results include:
- Test statistic
- P-value
- Significance indicator (✓ if p < α)

## Examples

### Example 1: Quick Test

```python
# Run quick test with 10 samples
config = {
    "experiment_name": "quick_test",
    "dataset": {"name": "cail2019", "max_samples": 10},
    "output_dir": "expr/experiments",
    "random_seed": 42,
}

pipeline = ExperimentPipeline(config)
results = await pipeline.run_full_pipeline("cail2019")
```

### Example 2: Full Evaluation

```python
# Run complete evaluation on full dataset
config = {
    "experiment_name": "full_evaluation",
    "dataset": {"name": "cail2019", "max_samples": null},
    "evaluation": {
        "metrics": ["mrr", "precision_at_k", "recall_at_k", "bleu", "rouge"],
        "k_values": [1, 3, 5, 10, 20],
        "baselines": ["llm_confidence", "rule_based", "static_hypergraphrag"],
    },
    "output_dir": "expr/experiments",
    "random_seed": 42,
}

pipeline = ExperimentPipeline(config)
results = await pipeline.run_full_pipeline("cail2019")
```

### Example 3: Ablation Study

```python
# Compare different feature combinations
for feature_set in ["full", "no_quality", "no_dynamic", "no_filtering"]:
    config["experiment_name"] = f"ablation_{feature_set}"
    # Configure features...
    
    pipeline = ExperimentPipeline(config)
    results = await pipeline.run_full_pipeline("cail2019")
```

## Command-Line Interface

Use the example script for command-line experiments:

```bash
# Simple experiment
python examples/example_experiment_pipeline.py --mode simple --dataset cail2019

# From YAML config
python examples/example_experiment_pipeline.py --mode yaml --config config.yaml --dataset cail2019

# Ablation study
python examples/example_experiment_pipeline.py --mode ablation --dataset cail2019
```

## Integration with Existing Code

The pipeline integrates with existing DynHyperRAG components:

- **Data Loading**: Uses `CAIL2019Loader` and `AcademicLoader` from `hypergraphrag.data`
- **Extraction**: Uses `extract_entities()` from `hypergraphrag.operate`
- **Query**: Uses `kg_query()` from `hypergraphrag.operate`
- **Quality Scoring**: Uses `QualityScorer` from `hypergraphrag.quality`
- **Baselines**: Uses `BaselineMethods` and `StaticHyperGraphRAG` from `hypergraphrag.evaluation.baselines`
- **Metrics**: Uses `IntrinsicMetrics`, `ExtrinsicMetrics`, `EfficiencyMetrics` from `hypergraphrag.evaluation.metrics`

## Best Practices

1. **Use YAML Configuration**: Store experiment configurations in YAML files for reproducibility
2. **Set Random Seeds**: Always set `random_seed` for reproducible results
3. **Track Git Commits**: The pipeline automatically tracks git commits for version control
4. **Save Intermediate Results**: Enable `save_intermediate` to debug issues
5. **Start Small**: Test with `max_samples` before running full experiments
6. **Compare Multiple Runs**: Run experiments with different seeds to assess variance
7. **Document Experiments**: Add descriptions to experiment configurations

## Troubleshooting

### Issue: Pipeline fails during data loading

**Solution**: Ensure dataset is properly formatted and path is correct. Check data loader documentation.

### Issue: Out of memory during extraction

**Solution**: Reduce `max_samples` or enable batch processing. Monitor memory usage with efficiency metrics.

### Issue: Statistical tests show no significance

**Solution**: Increase sample size, check if differences are meaningful, or adjust significance level.

### Issue: Baseline comparison fails

**Solution**: Ensure baseline methods are properly initialized. Check that storage instances are shared.

## Future Enhancements

Planned improvements for the experiment pipeline:

- [ ] Parallel experiment execution
- [ ] Automatic hyperparameter tuning
- [ ] Interactive result visualization
- [ ] Experiment comparison dashboard
- [ ] Cloud experiment tracking (MLflow, Weights & Biases)
- [ ] Automatic report generation with plots

## References

- Design Document: `.kiro/specs/dynhyperrag-quality-aware/design.md`
- Requirements: `.kiro/specs/dynhyperrag-quality-aware/requirements.md`
- Task List: `.kiro/specs/dynhyperrag-quality-aware/tasks.md`

## Support

For issues or questions:
1. Check the example scripts in `examples/`
2. Review the YAML configuration example
3. Consult the design document for architecture details
4. Check logs in the output directory
