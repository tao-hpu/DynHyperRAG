# DynHyperRAG Configuration Guide

This guide provides detailed information about all configuration options in DynHyperRAG.

## Table of Contents

1. [Environment Configuration](#environment-configuration)
2. [Quality Assessment Configuration](#quality-assessment-configuration)
3. [Dynamic Update Configuration](#dynamic-update-configuration)
4. [Retrieval Configuration](#retrieval-configuration)
5. [Evaluation Configuration](#evaluation-configuration)
6. [Performance Tuning](#performance-tuning)
7. [Domain-Specific Configurations](#domain-specific-configurations)

---

## Environment Configuration

### .env File

Create a `.env` file in the project root:

```bash
# Required: OpenAI API Configuration
OPENAI_API_KEY=your_api_key_here
OPENAI_BASE_URL=https://api.openai.com/v1

# Models
EMBEDDING_MODEL=text-embedding-3-small
LLM_MODEL=gpt-4o-mini

# Optional: Rate Limiting
MAX_REQUESTS_PER_MINUTE=60
MAX_TOKENS_PER_MINUTE=90000

# Optional: Caching
ENABLE_LLM_CACHE=true
CACHE_DIR=.cache

# Optional: Logging
LOG_LEVEL=INFO
LOG_FILE=hypergraphrag.log
```

### Python Configuration

```python
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Access configuration
api_key = os.getenv('OPENAI_API_KEY')
model = os.getenv('LLM_MODEL', 'gpt-4o-mini')
```

---

## Quality Assessment Configuration

### Basic Configuration

```python
quality_config = {
    # Mode: 'unsupervised' or 'supervised'
    'quality_mode': 'unsupervised',
    
    # Feature weights (must sum to 1.0)
    'quality_feature_weights': {
        'degree_centrality': 0.2,
        'betweenness': 0.15,
        'clustering': 0.15,
        'coherence': 0.3,
        'text_quality': 0.2
    },
    
    # Coherence computation
    'coherence_variance_penalty': 0.5,
    'coherence_min_entities': 2,
    
    # Text quality thresholds
    'min_text_length': 10,
    'max_text_length': 500,
    
    # Performance
    'batch_size': 50,
    'show_progress': True
}
```

### Feature Weight Presets

**Balanced (Default):**
```python
'quality_feature_weights': {
    'degree_centrality': 0.2,
    'betweenness': 0.15,
    'clustering': 0.15,
    'coherence': 0.3,
    'text_quality': 0.2
}
```

**Coherence-Focused:**
```python
'quality_feature_weights': {
    'degree_centrality': 0.15,
    'betweenness': 0.1,
    'clustering': 0.1,
    'coherence': 0.5,
    'text_quality': 0.15
}
```

**Structure-Focused:**
```python
'quality_feature_weights': {
    'degree_centrality': 0.3,
    'betweenness': 0.25,
    'clustering': 0.25,
    'coherence': 0.1,
    'text_quality': 0.1
}
```

**Fast (Lightweight):**
```python
'quality_feature_weights': {
    'degree_centrality': 0.5,
    'betweenness': 0.0,  # Disabled (slow)
    'clustering': 0.0,   # Disabled (slow)
    'coherence': 0.5,
    'text_quality': 0.0
}
```

### Supervised Mode Configuration

```python
supervised_config = {
    'quality_mode': 'supervised',
    
    # Model selection
    'supervised_model': 'random_forest',  # or 'linear_regression', 'gradient_boosting'
    
    # Model hyperparameters
    'model_params': {
        'n_estimators': 100,
        'max_depth': 10,
        'random_state': 42
    },
    
    # Training
    'train_test_split': 0.8,
    'cross_validation_folds': 5,
    
    # Feature selection
    'feature_selection': True,
    'max_features': 5
}
```

---

## Dynamic Update Configuration

### Weight Update Configuration

```python
dynamic_config = {
    # Update strategy
    'strategy': 'ema',  # 'ema', 'additive', 'multiplicative'
    
    # Learning rate
    'update_alpha': 0.1,  # Range: (0, 1]
    
    # Decay factor
    'decay_factor': 0.99,  # Range: (0, 1]
    
    # Weight constraints
    'min_weight_ratio': 0.5,  # Minimum weight = quality_score * 0.5
    'max_weight_ratio': 2.0,  # Maximum weight = quality_score * 2.0
    
    # History tracking
    'track_history': True,
    'max_history_length': 100,
    
    # Batch updates
    'batch_update_size': 100,
    'async_updates': True
}
```

### Strategy-Specific Parameters

**EMA (Exponential Moving Average):**
```python
{
    'strategy': 'ema',
    'update_alpha': 0.1,  # Higher = faster adaptation
    'decay_factor': 0.99  # Higher = slower decay
}
```

**Additive:**
```python
{
    'strategy': 'additive',
    'update_alpha': 0.05,  # Smaller for stability
    'decay_factor': 0.95   # More aggressive decay
}
```

**Multiplicative:**
```python
{
    'strategy': 'multiplicative',
    'update_alpha': 0.1,
    'decay_factor': 0.99
}
```

### Feedback Extraction Configuration

```python
feedback_config = {
    # Method: 'embedding', 'citation', 'attention'
    'feedback_method': 'embedding',
    
    # Embedding-based
    'feedback_threshold': 0.7,  # Similarity threshold
    'embedding_batch_size': 32,
    
    # Citation-based
    'citation_fuzzy_match': True,
    'citation_min_length': 10,
    
    # Attention-based (if supported)
    'attention_aggregation': 'mean',  # 'mean', 'max', 'sum'
    'attention_threshold': 0.5
}
```

### Hyperedge Refinement Configuration

```python
refiner_config = {
    # Filtering
    'quality_threshold': 0.5,
    'soft_filter': True,  # False = hard delete
    
    # Threshold strategy
    'threshold_strategy': 'fixed',  # 'fixed', 'percentile', 'f1_optimal'
    'percentile_value': 25,  # For 'percentile' strategy
    
    # Iterative refinement
    'enable_iterative_refinement': False,
    'max_refinement_iterations': 3,
    
    # Statistics
    'track_filter_statistics': True
}
```

---

## Retrieval Configuration

### Entity Type Filtering Configuration

```python
entity_filter_config = {
    # Domain
    'domain': 'legal',  # 'legal', 'academic', 'medical'
    
    # Entity taxonomy
    'entity_taxonomy': {
        'legal': ['law', 'article', 'court', 'party', 'crime', 'penalty'],
        'academic': ['paper', 'author', 'institution', 'keyword', 'conference'],
        'medical': ['disease', 'symptom', 'treatment', 'drug', 'procedure']
    },
    
    # Classification method
    'use_llm_classification': False,  # True = use LLM, False = keyword-based
    'llm_classification_prompt': "Identify entity types in: {query}",
    
    # Fallback
    'fallback_to_all_types': True,  # If no types identified
    'min_types_threshold': 1
}
```

### Quality-Aware Ranking Configuration

```python
ranking_config = {
    # Weights (must sum to 1.0)
    'similarity_weight': 0.5,  # α
    'quality_weight': 0.3,     # β
    'dynamic_weight': 0.2,     # γ
    
    # Normalization
    'normalize_scores': True,
    'normalization_method': 'min_max',  # 'min_max', 'z_score'
    
    # Explanation
    'provide_explanation': False,
    'explanation_detail_level': 'summary',  # 'summary', 'detailed'
    
    # Re-ranking
    'rerank_top_k': 100,  # Re-rank top K results
    'final_top_k': 10     # Return top K after re-ranking
}
```

### Lightweight Retrieval Configuration

```python
lite_config = {
    # Caching
    'cache_size': 1000,
    'cache_ttl': 3600,  # seconds
    
    # Simplified features
    'use_simplified_features': True,
    'simplified_features': ['degree', 'coherence'],
    
    # ANN search (if enabled)
    'use_ann_search': False,
    'ann_index_type': 'hnsw',  # 'hnsw', 'ivf'
    'ann_ef_search': 50,
    
    # Performance
    'max_concurrent_requests': 10,
    'timeout': 5.0  # seconds
}
```

### Performance Monitoring Configuration

```python
monitor_config = {
    # Tracking
    'enable_monitoring': True,
    'track_retrieval_time': True,
    'track_memory_usage': True,
    
    # Metrics
    'metrics_window_size': 1000,  # Keep last N operations
    'compute_percentiles': [50, 90, 95, 99],
    
    # Logging
    'log_slow_queries': True,
    'slow_query_threshold': 5.0,  # seconds
    
    # Export
    'export_metrics': True,
    'export_interval': 300,  # seconds
    'export_path': 'logs/performance_metrics.jsonl'
}
```

---

## Evaluation Configuration

### Metrics Configuration

```python
metrics_config = {
    # Intrinsic metrics
    'compute_intrinsic': True,
    'intrinsic_metrics': ['precision', 'recall', 'f1', 'roc_auc'],
    
    # Extrinsic metrics
    'compute_extrinsic': True,
    'extrinsic_metrics': ['mrr', 'precision_at_k', 'recall_at_k'],
    'k_values': [5, 10, 20],
    
    # Efficiency metrics
    'compute_efficiency': True,
    'efficiency_metrics': ['retrieval_time', 'memory_usage', 'api_cost'],
    
    # Answer quality
    'compute_answer_quality': True,
    'answer_metrics': ['bleu', 'rouge', 'bertscore'],
    
    # Statistical tests
    'run_statistical_tests': True,
    'significance_level': 0.05,
    'test_method': 'wilcoxon'  # 'wilcoxon', 't_test'
}
```

### Experiment Pipeline Configuration

```python
pipeline_config = {
    # Data
    'data_dir': 'expr/cail2019',
    'output_dir': 'outputs/experiments',
    'dataset_name': 'cail2019',
    
    # Experiment
    'random_seed': 42,
    'num_runs': 5,  # Multiple runs for statistical significance
    
    # Stages
    'stages': ['load', 'extract', 'score', 'retrieve', 'evaluate'],
    'skip_existing': True,
    
    # Baselines
    'run_baselines': True,
    'baseline_methods': ['llm_confidence', 'rule_based', 'random', 'static_hypergraphrag'],
    
    # Reporting
    'generate_report': True,
    'report_format': 'markdown',  # 'markdown', 'latex', 'html'
    'include_visualizations': True
}
```

### Ablation Study Configuration

```python
ablation_config = {
    # Feature ablation
    'run_feature_ablation': True,
    'features_to_ablate': [
        'degree_centrality',
        'betweenness',
        'clustering',
        'coherence',
        'text_quality'
    ],
    
    # Module ablation
    'run_module_ablation': True,
    'modules_to_ablate': [
        'quality_assessment',
        'dynamic_update',
        'entity_filtering',
        'quality_ranking'
    ],
    
    # Comparison
    'compare_with_full_system': True,
    'compute_contribution': True,  # Compute each component's contribution
    
    # Output
    'save_ablation_results': True,
    'output_path': 'outputs/ablation_results.json'
}
```

---

## Performance Tuning

### For Speed

```python
speed_config = {
    # Quality assessment
    'quality_feature_weights': {
        'degree_centrality': 0.5,
        'coherence': 0.5,
        'betweenness': 0.0,  # Disable slow features
        'clustering': 0.0,
        'text_quality': 0.0
    },
    
    # Retrieval
    'use_lite_retriever': True,
    'cache_size': 2000,
    'use_ann_search': True,
    
    # Updates
    'async_updates': True,
    'batch_update_size': 200,
    
    # Monitoring
    'enable_monitoring': False  # Disable in production
}
```

### For Accuracy

```python
accuracy_config = {
    # Quality assessment
    'quality_mode': 'supervised',
    'quality_feature_weights': {
        'degree_centrality': 0.2,
        'betweenness': 0.15,
        'clustering': 0.15,
        'coherence': 0.3,
        'text_quality': 0.2
    },
    
    # Retrieval
    'use_lite_retriever': False,
    'use_llm_classification': True,
    'rerank_top_k': 200,
    
    # Updates
    'strategy': 'ema',
    'update_alpha': 0.05,  # Slower, more stable
    
    # Ranking
    'similarity_weight': 0.4,
    'quality_weight': 0.4,
    'dynamic_weight': 0.2
}
```

### For Memory Efficiency

```python
memory_config = {
    # Caching
    'cache_size': 500,
    'cache_ttl': 1800,
    
    # Batch processing
    'batch_size': 20,
    'max_concurrent_requests': 5,
    
    # History
    'track_history': False,
    'max_history_length': 50,
    
    # Monitoring
    'metrics_window_size': 500
}
```

---

## Domain-Specific Configurations

### Legal Domain (CAIL2019)

```python
legal_config = {
    # Entity types
    'domain': 'legal',
    'entity_taxonomy': {
        'legal': ['law', 'article', 'court', 'party', 'crime', 'penalty', 'evidence']
    },
    
    # Quality weights (structure-focused)
    'quality_feature_weights': {
        'degree_centrality': 0.25,
        'betweenness': 0.2,
        'clustering': 0.2,
        'coherence': 0.25,
        'text_quality': 0.1
    },
    
    # Retrieval
    'similarity_weight': 0.4,
    'quality_weight': 0.4,
    'dynamic_weight': 0.2,
    
    # Updates
    'strategy': 'ema',
    'update_alpha': 0.1
}
```

### Academic Domain (PubMed/AMiner)

```python
academic_config = {
    # Entity types
    'domain': 'academic',
    'entity_taxonomy': {
        'academic': ['paper', 'author', 'institution', 'keyword', 'conference', 'journal']
    },
    
    # Quality weights (coherence-focused)
    'quality_feature_weights': {
        'degree_centrality': 0.15,
        'betweenness': 0.15,
        'clustering': 0.15,
        'coherence': 0.4,
        'text_quality': 0.15
    },
    
    # Retrieval
    'similarity_weight': 0.5,
    'quality_weight': 0.3,
    'dynamic_weight': 0.2,
    
    # Updates
    'strategy': 'multiplicative',
    'update_alpha': 0.15
}
```

### Medical Domain

```python
medical_config = {
    # Entity types
    'domain': 'medical',
    'entity_taxonomy': {
        'medical': ['disease', 'symptom', 'treatment', 'drug', 'procedure', 'anatomy']
    },
    
    # Quality weights (balanced)
    'quality_feature_weights': {
        'degree_centrality': 0.2,
        'betweenness': 0.15,
        'clustering': 0.15,
        'coherence': 0.3,
        'text_quality': 0.2
    },
    
    # Retrieval
    'similarity_weight': 0.5,
    'quality_weight': 0.3,
    'dynamic_weight': 0.2,
    
    # Updates
    'strategy': 'ema',
    'update_alpha': 0.1
}
```

---

## Complete Configuration Example

```python
# Complete DynHyperRAG configuration
complete_config = {
    # Quality Assessment
    'quality': {
        'mode': 'unsupervised',
        'feature_weights': {
            'degree_centrality': 0.2,
            'betweenness': 0.15,
            'clustering': 0.15,
            'coherence': 0.3,
            'text_quality': 0.2
        },
        'batch_size': 50,
        'show_progress': True
    },
    
    # Dynamic Update
    'dynamic': {
        'strategy': 'ema',
        'update_alpha': 0.1,
        'decay_factor': 0.99,
        'min_weight_ratio': 0.5,
        'max_weight_ratio': 2.0,
        'track_history': True
    },
    
    # Feedback Extraction
    'feedback': {
        'method': 'embedding',
        'threshold': 0.7
    },
    
    # Retrieval
    'retrieval': {
        'domain': 'legal',
        'entity_taxonomy': {
            'legal': ['law', 'article', 'court', 'party', 'crime', 'penalty']
        },
        'use_llm_classification': False,
        'similarity_weight': 0.5,
        'quality_weight': 0.3,
        'dynamic_weight': 0.2
    },
    
    # Refinement
    'refinement': {
        'quality_threshold': 0.5,
        'soft_filter': True,
        'threshold_strategy': 'fixed'
    },
    
    # Performance
    'performance': {
        'enable_monitoring': True,
        'cache_size': 1000,
        'batch_update_size': 100
    },
    
    # Evaluation
    'evaluation': {
        'metrics': ['mrr', 'precision_at_k', 'recall_at_k'],
        'k_values': [5, 10, 20],
        'run_statistical_tests': True
    }
}
```

### Loading Configuration from File

```python
import yaml
import json

# From YAML
with open('config.yaml', 'r') as f:
    config = yaml.safe_load(f)

# From JSON
with open('config.json', 'r') as f:
    config = json.load(f)

# Use configuration
from hypergraphrag.quality import QualityScorer

scorer = QualityScorer(
    graph,
    embedding_func,
    config=config['quality']
)
```

---

## Validation

Validate your configuration:

```python
def validate_config(config):
    """Validate configuration dictionary."""
    errors = []
    
    # Check feature weights sum to 1.0
    if 'quality' in config:
        weights = config['quality']['feature_weights']
        weight_sum = sum(weights.values())
        if abs(weight_sum - 1.0) > 0.01:
            errors.append(f"Feature weights sum to {weight_sum}, not 1.0")
    
    # Check ranking weights sum to 1.0
    if 'retrieval' in config:
        alpha = config['retrieval']['similarity_weight']
        beta = config['retrieval']['quality_weight']
        gamma = config['retrieval']['dynamic_weight']
        total = alpha + beta + gamma
        if abs(total - 1.0) > 0.01:
            errors.append(f"Ranking weights sum to {total}, not 1.0")
    
    # Check alpha in valid range
    if 'dynamic' in config:
        alpha = config['dynamic']['update_alpha']
        if not (0.0 < alpha <= 1.0):
            errors.append(f"update_alpha must be in (0, 1], got {alpha}")
    
    return errors

# Validate
errors = validate_config(complete_config)
if errors:
    print("Configuration errors:")
    for error in errors:
        print(f"  - {error}")
else:
    print("Configuration is valid!")
```

---

## Environment-Specific Configurations

### Development

```python
dev_config = {
    'enable_monitoring': True,
    'show_progress': True,
    'log_level': 'DEBUG',
    'cache_size': 100,
    'batch_size': 10
}
```

### Testing

```python
test_config = {
    'enable_monitoring': False,
    'show_progress': False,
    'log_level': 'WARNING',
    'random_seed': 42,
    'deterministic': True
}
```

### Production

```python
prod_config = {
    'enable_monitoring': True,
    'show_progress': False,
    'log_level': 'INFO',
    'cache_size': 2000,
    'batch_size': 100,
    'use_lite_retriever': True,
    'async_updates': True
}
```

---

**Last Updated:** 2025-01-10
**Version:** 1.0.0
