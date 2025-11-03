# DynHyperRAG Configuration Guide

This guide explains how to configure DynHyperRAG features through environment variables.

## Overview

DynHyperRAG extends HyperGraphRAG with three main modules:
1. **Quality Assessment** - Evaluate hyperedge quality using graph structure features
2. **Dynamic Weight Update** - Adjust hyperedge weights based on retrieval feedback
3. **Efficient Retrieval** - Optimize retrieval with entity type filtering and quality-aware ranking

## Configuration File

All configuration is done through the `.env` file. Copy `.env.example` to `.env` and modify as needed:

```bash
cp .env.example .env
```

## Basic Configuration

### Required Settings

```bash
# OpenAI API Configuration
OPENAI_API_KEY=your_api_key_here
OPENAI_BASE_URL=https://api.openai.com/v1

# Model Configuration
EMBEDDING_MODEL=text-embedding-3-small
LLM_MODEL=gpt-4o-mini
```

## DynHyperRAG Modules

### 1. Quality Assessment Module

Evaluates hyperedge quality using 5 graph structure features.

```bash
# Enable/disable quality assessment
DYNHYPERRAG_QUALITY_ENABLED=true

# Feature weights (must sum to 1.0)
QUALITY_WEIGHT_DEGREE=0.2        # Degree centrality
QUALITY_WEIGHT_BETWEENNESS=0.15  # Edge betweenness
QUALITY_WEIGHT_CLUSTERING=0.15   # Local clustering
QUALITY_WEIGHT_COHERENCE=0.3     # Hyperedge coherence
QUALITY_WEIGHT_TEXT=0.2          # Text quality

# Assessment mode
QUALITY_MODE=unsupervised  # Options: unsupervised, supervised
```

**Feature Descriptions:**
- **Degree Centrality**: Number of entities connected by the hyperedge
- **Betweenness**: How many shortest paths pass through this hyperedge
- **Clustering**: Density of connections among neighboring hyperedges
- **Coherence**: Semantic similarity among entities in the hyperedge
- **Text Quality**: Quality of the source text (length, completeness, grammar)

### 2. Dynamic Weight Update Module

Adjusts hyperedge weights based on retrieval feedback.

```bash
# Enable/disable dynamic updates
DYNHYPERRAG_DYNAMIC_ENABLED=true

# Update strategy
DYNAMIC_UPDATE_STRATEGY=ema  # Options: ema, additive, multiplicative

# Learning rate (0 < alpha <= 1)
DYNAMIC_UPDATE_ALPHA=0.1

# Decay factor (0 < decay <= 1)
DYNAMIC_DECAY_FACTOR=0.99

# Feedback extraction method
DYNAMIC_FEEDBACK_METHOD=embedding  # Options: embedding, citation, attention

# Feedback threshold (0-1)
DYNAMIC_FEEDBACK_THRESHOLD=0.7
```

**Update Strategies:**
- **EMA (Exponential Moving Average)**: `w_t = (1-α)w_{t-1} + α·f_t`
- **Additive**: `w_t = w_{t-1} + α(f_t - 0.5)`
- **Multiplicative**: `w_t = w_{t-1} · (1 + α(f_t - 0.5))`

**Feedback Methods:**
- **Embedding**: Compute semantic similarity between answer and hyperedge
- **Citation**: Detect if hyperedge content is mentioned in the answer
- **Attention**: Extract attention weights from LLM (if supported)

### 3. Hyperedge Refinement Module

Filters or refines low-quality hyperedges.

```bash
# Enable/disable refinement
DYNHYPERRAG_REFINER_ENABLED=false

# Quality threshold for filtering (0-1)
REFINER_QUALITY_THRESHOLD=0.5

# Use soft filtering (lower weight) instead of deletion
REFINER_SOFT_FILTER=true
```

**Filtering Modes:**
- **Soft Filter**: Lower the weight of low-quality hyperedges but keep them
- **Hard Filter**: Delete low-quality hyperedges from the graph

### 4. Efficient Retrieval Module

Optimizes retrieval speed through entity type filtering and quality-aware ranking.

```bash
# Enable/disable entity type filtering
DYNHYPERRAG_ENTITY_FILTER_ENABLED=true

# Domain for entity taxonomy
RETRIEVAL_DOMAIN=medical  # Options: medical, legal, academic

# Custom entity types (optional, comma-separated)
# ENTITY_TYPES_MEDICAL=disease,symptom,treatment,medication,procedure,anatomy
# ENTITY_TYPES_LEGAL=law,article,court,party,crime,penalty
# ENTITY_TYPES_ACADEMIC=paper,author,institution,keyword,conference

# Retrieval ranking weights (must sum to 1.0)
RETRIEVAL_SIMILARITY_WEIGHT=0.5  # Semantic similarity
RETRIEVAL_QUALITY_WEIGHT=0.3     # Quality score
RETRIEVAL_DYNAMIC_WEIGHT=0.2     # Dynamic weight
```

**Default Entity Taxonomies:**
- **Medical**: disease, symptom, treatment, medication, procedure, anatomy
- **Legal**: law, article, court, party, crime, penalty
- **Academic**: paper, author, institution, keyword, conference

**Ranking Formula:**
```
score = α × similarity + β × quality + γ × dynamic_weight
```

### 5. Lite Mode

Lightweight variant for resource-constrained environments.

```bash
# Enable/disable lite mode
DYNHYPERRAG_LITE_MODE=false

# Cache size for frequently accessed hyperedges
LITE_CACHE_SIZE=1000
```

**Lite Mode Optimizations:**
- Simplified quality features (only degree + coherence)
- Approximate nearest neighbor search
- Caching of frequently accessed hyperedges
- Batch processing for updates

## Usage in Code

### Loading Configuration

```python
from config import setup_environment

# Load and validate configuration
config = setup_environment()

# Access DynHyperRAG configuration
dynhyperrag_config = config.get_dynhyperrag_config()
```

### Module-Specific Configuration

```python
# Quality assessment configuration
quality_config = config.get_quality_config()
# Returns: {"enabled": True, "feature_weights": {...}, "mode": "unsupervised"}

# Dynamic update configuration
dynamic_config = config.get_dynamic_config()
# Returns: {"enabled": True, "strategy": "ema", "update_alpha": 0.1, ...}

# Retrieval configuration
retrieval_config = config.get_retrieval_config()
# Returns: {"entity_filter_enabled": True, "domain": "medical", ...}
```

### Using Configuration in Modules

```python
from hypergraphrag.quality import QualityScorer
from hypergraphrag.dynamic import WeightUpdater
from hypergraphrag.retrieval import EntityTypeFilter

# Initialize quality scorer
scorer = QualityScorer(
    graph=knowledge_graph,
    config=config.get_quality_config()
)

# Initialize weight updater
updater = WeightUpdater(
    graph=knowledge_graph,
    config=config.get_dynamic_config()
)

# Initialize entity filter
entity_filter = EntityTypeFilter(
    graph=knowledge_graph,
    config=config.get_retrieval_config()
)
```

## Validation

The configuration system automatically validates:
- Feature weights sum to 1.0
- Valid strategy/method names
- Parameter ranges (e.g., 0 < alpha <= 1)
- Domain exists in taxonomy

Run validation:
```bash
python3 config.py
```

## Examples

### Example 1: Medical Domain with Quality Assessment

```bash
DYNHYPERRAG_QUALITY_ENABLED=true
QUALITY_MODE=unsupervised
RETRIEVAL_DOMAIN=medical
DYNHYPERRAG_ENTITY_FILTER_ENABLED=true
```

### Example 2: Legal Domain with Dynamic Updates

```bash
DYNHYPERRAG_QUALITY_ENABLED=true
DYNHYPERRAG_DYNAMIC_ENABLED=true
DYNAMIC_UPDATE_STRATEGY=ema
DYNAMIC_UPDATE_ALPHA=0.15
RETRIEVAL_DOMAIN=legal
```

### Example 3: Lite Mode for Production

```bash
DYNHYPERRAG_LITE_MODE=true
LITE_CACHE_SIZE=5000
DYNHYPERRAG_QUALITY_ENABLED=true
DYNHYPERRAG_DYNAMIC_ENABLED=false
DYNHYPERRAG_ENTITY_FILTER_ENABLED=true
```

### Example 4: Custom Entity Types

```bash
RETRIEVAL_DOMAIN=medical
ENTITY_TYPES_MEDICAL=disease,symptom,drug,gene,protein,pathway
```

## Troubleshooting

### Configuration Not Loading

**Problem**: Configuration values not being read

**Solution**: 
1. Ensure `.env` file exists in project root
2. Check file encoding (should be UTF-8)
3. Verify no syntax errors in `.env` file

### Validation Errors

**Problem**: "Feature weights must sum to 1.0"

**Solution**: Adjust weights so they sum to exactly 1.0:
```bash
QUALITY_WEIGHT_DEGREE=0.2
QUALITY_WEIGHT_BETWEENNESS=0.15
QUALITY_WEIGHT_CLUSTERING=0.15
QUALITY_WEIGHT_COHERENCE=0.3
QUALITY_WEIGHT_TEXT=0.2
# Sum = 1.0 ✓
```

**Problem**: "Invalid update_strategy"

**Solution**: Use one of the valid strategies:
```bash
DYNAMIC_UPDATE_STRATEGY=ema  # or additive, multiplicative
```

### Performance Issues

**Problem**: Slow retrieval with quality assessment

**Solution**: Enable lite mode:
```bash
DYNHYPERRAG_LITE_MODE=true
```

**Problem**: High memory usage

**Solution**: Reduce cache size:
```bash
LITE_CACHE_SIZE=500
```

## Best Practices

1. **Start with defaults**: Use the default configuration from `.env.example`
2. **Enable features incrementally**: Start with quality assessment, then add dynamic updates
3. **Monitor performance**: Track retrieval time and accuracy
4. **Tune weights**: Adjust feature/ranking weights based on your domain
5. **Use lite mode in production**: For better performance and lower resource usage

## Related Documentation

- [Thesis Overview](THESIS_OVERVIEW.md) - Research background and methodology
- [Setup Guide](SETUP.md) - Installation and basic setup
- [Quick Start](QUICKSTART.md) - Getting started with HyperGraphRAG
- [Architecture](architecture.md) - System architecture and design

## Support

For questions or issues:
- Open an issue on [GitHub](https://github.com/tao-hpu/HyperGraphRAG/issues)
- Check [Troubleshooting Guide](troubleshooting.md)
- Contact: [Tao An](https://tao-hpu.github.io)
