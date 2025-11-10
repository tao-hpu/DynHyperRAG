# DynHyperRAG User Guide

Welcome to the DynHyperRAG User Guide! This guide will walk you through using the DynHyperRAG system step by step, from installation to advanced usage.

## Table of Contents

1. [Getting Started](#getting-started)
2. [Basic Usage](#basic-usage)
3. [Quality Assessment](#quality-assessment)
4. [Dynamic Weight Updates](#dynamic-weight-updates)
5. [Efficient Retrieval](#efficient-retrieval)
6. [Evaluation and Experiments](#evaluation-and-experiments)
7. [Advanced Topics](#advanced-topics)
8. [Troubleshooting](#troubleshooting)

---

## Getting Started

### Prerequisites

Before you begin, ensure you have:
- Python 3.11 or higher
- OpenAI API key (or compatible API endpoint)
- At least 8GB RAM
- 10GB free disk space

### Installation

1. **Clone the repository:**
```bash
git clone https://github.com/tao-hpu/HyperGraphRAG.git
cd HyperGraphRAG
```

2. **Create a virtual environment:**
```bash
conda create -n dynhyperrag python=3.11
conda activate dynhyperrag
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
```

4. **Configure API credentials:**
```bash
cp .env.example .env
# Edit .env with your API key
```

### Quick Test

Verify your installation:
```bash
python -c "import hypergraphrag; print('Installation successful!')"
```

---

## Basic Usage

### Step 1: Build a Knowledge Hypergraph

Create a simple knowledge graph from documents:

```python
import asyncio
from hypergraphrag import HyperGraphRAG, QueryParam

async def build_graph():
    # Initialize HyperGraphRAG
    rag = HyperGraphRAG(
        working_dir="expr/my_project",
        enable_llm_cache=True
    )
    
    # Prepare documents
    documents = [
        "Diabetes is a chronic disease that affects blood sugar levels.",
        "Type 2 diabetes is the most common form, often linked to obesity.",
        "Treatment includes medication, diet changes, and exercise."
    ]
    
    # Build knowledge graph
    await rag.insert(documents)
    print("Knowledge graph built successfully!")
    
    return rag

# Run
rag = asyncio.run(build_graph())
```

### Step 2: Query the Knowledge Graph

```python
async def query_graph(rag):
    # Simple query
    result = await rag.query(
        "What is diabetes and how is it treated?",
        param=QueryParam(mode="hybrid", top_k=10)
    )
    
    print(f"Answer: {result}")

# Run
asyncio.run(query_graph(rag))
```

---

## Quality Assessment

### Understanding Quality Scores

DynHyperRAG evaluates hyperedge quality using 5 features:

1. **Degree Centrality** (20%): How many entities the hyperedge connects
2. **Betweenness** (15%): How important the hyperedge is for graph connectivity
3. **Clustering** (15%): How densely connected the hyperedge's neighborhood is
4. **Coherence** (30%): How semantically similar the connected entities are
5. **Text Quality** (20%): Quality of the source text

### Computing Quality Scores

```python
from hypergraphrag.quality import QualityScorer

async def assess_quality(rag):
    # Initialize quality scorer
    scorer = QualityScorer(
        knowledge_graph_inst=rag.knowledge_graph_inst,
        embedding_func=rag.embedding_func,
        config={
            'quality_mode': 'unsupervised',
            'quality_feature_weights': {
                'degree_centrality': 0.2,
                'betweenness': 0.15,
                'clustering': 0.15,
                'coherence': 0.3,
                'text_quality': 0.2
            }
        }
    )
    
    # Get all hyperedge IDs
    hyperedge_ids = []
    async for node_id, node_data in rag.knowledge_graph_inst.nodes():
        if node_data.get('role') == 'hyperedge':
            hyperedge_ids.append(node_id)
    
    # Compute quality scores
    results = await scorer.batch_compute_quality_scores(
        hyperedge_ids,
        show_progress=True
    )
    
    # Analyze results
    scores = [r['quality_score'] for r in results.values()]
    print(f"Average quality: {sum(scores)/len(scores):.3f}")
    print(f"Min quality: {min(scores):.3f}")
    print(f"Max quality: {max(scores):.3f}")
    
    return results

# Run
quality_results = asyncio.run(assess_quality(rag))
```

### Analyzing Feature Importance

```python
from hypergraphrag.quality import FeatureAnalyzer

async def analyze_features(rag, scorer):
    # Prepare ground truth (example)
    ground_truth = {
        'hyperedge_1': 0.8,  # High quality
        'hyperedge_2': 0.3,  # Low quality
        'hyperedge_3': 0.9   # High quality
    }
    
    # Analyze feature importance
    analyzer = FeatureAnalyzer(scorer)
    result = await analyzer.analyze_feature_importance(
        hyperedges=list(ground_truth.keys()),
        ground_truth=ground_truth,
        method='shap'
    )
    
    # Print results
    print("\nFeature Importance:")
    for feature, importance in result['feature_importance'].items():
        print(f"  {feature}: {importance:.3f}")

# Run
asyncio.run(analyze_features(rag, scorer))
```

---

## Dynamic Weight Updates

### Understanding Dynamic Weights

Dynamic weights adjust based on retrieval feedback:
- **Positive feedback**: Hyperedge was useful → weight increases
- **Negative feedback**: Hyperedge was not useful → weight decreases

### Setting Up Weight Updates

```python
from hypergraphrag.dynamic import WeightUpdater, FeedbackExtractor

async def setup_dynamic_updates(rag):
    # Initialize weight updater
    updater = WeightUpdater(
        graph=rag.knowledge_graph_inst,
        config={
            'strategy': 'ema',  # Exponential Moving Average
            'update_alpha': 0.1,  # Learning rate
            'decay_factor': 0.99  # Prevent unbounded growth
        }
    )
    
    # Initialize feedback extractor
    extractor = FeedbackExtractor(
        embedding_func=rag.embedding_func,
        config={
            'feedback_method': 'embedding',
            'feedback_threshold': 0.7
        }
    )
    
    return updater, extractor

# Run
updater, extractor = asyncio.run(setup_dynamic_updates(rag))
```

### Query with Dynamic Updates

```python
async def query_with_updates(rag, updater, extractor):
    # Perform query
    query = "What causes diabetes?"
    result = await rag.query(query)
    
    # Extract feedback signals
    # Note: You need to track which hyperedges were retrieved
    retrieved_hyperedges = [
        {'id': 'he_1', 'hyperedge': 'diabetes causes'},
        {'id': 'he_2', 'hyperedge': 'cancer treatment'}
    ]
    
    feedback = await extractor.extract_feedback(
        answer=result,
        retrieved_hyperedges=retrieved_hyperedges
    )
    
    # Update weights
    new_weights = await updater.batch_update_weights(feedback)
    
    print(f"Updated {len(new_weights)} hyperedge weights")
    for he_id, weight in new_weights.items():
        print(f"  {he_id}: {weight:.3f}")

# Run
asyncio.run(query_with_updates(rag, updater, extractor))
```

### Update Strategies

**EMA (Exponential Moving Average)** - Recommended for most cases:
```python
config = {'strategy': 'ema', 'update_alpha': 0.1}
```

**Additive** - Direct addition of feedback:
```python
config = {'strategy': 'additive', 'update_alpha': 0.05}
```

**Multiplicative** - Proportional updates:
```python
config = {'strategy': 'multiplicative', 'update_alpha': 0.1}
```

---

## Efficient Retrieval

### Entity Type Filtering

Reduce search space by filtering hyperedges based on entity types:

```python
from hypergraphrag.retrieval import EntityTypeFilter

async def use_entity_filtering(rag):
    # Initialize filter
    entity_filter = EntityTypeFilter(
        graph=rag.knowledge_graph_inst,
        llm_model_func=rag.llm_model_func,
        config={
            'domain': 'legal',
            'entity_taxonomy': {
                'legal': ['law', 'article', 'court', 'party', 'crime', 'penalty']
            },
            'use_llm_classification': False
        }
    )
    
    # Identify relevant types from query
    query = "What are the penalties for theft?"
    relevant_types = await entity_filter.identify_relevant_types(query)
    print(f"Relevant entity types: {relevant_types}")
    
    # Get all hyperedge IDs
    all_hyperedge_ids = []
    async for node_id, node_data in rag.knowledge_graph_inst.nodes():
        if node_data.get('role') == 'hyperedge':
            all_hyperedge_ids.append(node_id)
    
    # Filter hyperedges
    filtered_ids = await entity_filter.filter_hyperedges_by_type(
        all_hyperedge_ids,
        relevant_types
    )
    
    reduction = (1 - len(filtered_ids) / len(all_hyperedge_ids)) * 100
    print(f"Search space reduced by {reduction:.1f}%")
    
    return filtered_ids

# Run
filtered_ids = asyncio.run(use_entity_filtering(rag))
```

### Quality-Aware Ranking

Rank results by combining similarity, quality, and dynamic weight:

```python
from hypergraphrag.retrieval import QualityAwareRanker

async def use_quality_ranking(rag):
    # Initialize ranker
    ranker = QualityAwareRanker(config={
        'similarity_weight': 0.5,  # α
        'quality_weight': 0.3,     # β
        'dynamic_weight': 0.2,     # γ
        'provide_explanation': True
    })
    
    # Simulate retrieved hyperedges
    retrieved = [
        {
            'id': 'he_1',
            'distance': 0.9,
            'quality_score': 0.7,
            'dynamic_weight': 1.2
        },
        {
            'id': 'he_2',
            'distance': 0.8,
            'quality_score': 0.9,
            'dynamic_weight': 1.5
        }
    ]
    
    # Rank hyperedges
    ranked = await ranker.rank_hyperedges(
        query="test query",
        hyperedges=retrieved
    )
    
    # Print results
    for i, he in enumerate(ranked, 1):
        print(f"{i}. {he['id']}: score={he['final_score']:.3f}")
        if 'explanation' in he:
            print(f"   {he['explanation']}")

# Run
asyncio.run(use_quality_ranking(rag))
```

### Lightweight Retrieval

For production environments with strict latency requirements:

```python
from hypergraphrag.retrieval import LiteRetriever

async def use_lite_retriever(rag):
    # Initialize lite retriever
    lite_retriever = LiteRetriever(
        graph=rag.knowledge_graph_inst,
        vdb=rag.chunks_vdb,
        embedding_func=rag.embedding_func,
        config={'cache_size': 1000}
    )
    
    # Perform retrieval
    results = await lite_retriever.retrieve(
        query="diabetes treatment",
        top_k=10
    )
    
    print(f"Retrieved {len(results)} hyperedges")
    return results

# Run
results = asyncio.run(use_lite_retriever(rag))
```

---

## Evaluation and Experiments

### Running Experiments

```python
from hypergraphrag.evaluation import ExperimentPipeline

async def run_experiment():
    # Initialize pipeline
    pipeline = ExperimentPipeline(config={
        'data_dir': 'expr/cail2019',
        'output_dir': 'outputs/experiments',
        'random_seed': 42
    })
    
    # Run full pipeline
    report = await pipeline.run_full_pipeline('cail2019')
    
    print(f"Experiment complete!")
    print(f"Results saved to: {report['output_path']}")
    print(f"MRR: {report['metrics']['mrr']:.3f}")
    print(f"Precision@10: {report['metrics']['precision_at_10']:.3f}")

# Run
asyncio.run(run_experiment())
```

### Ablation Studies

Measure the contribution of each feature:

```python
from hypergraphrag.evaluation import run_ablation_studies

async def run_ablation():
    # Prepare test queries
    test_queries = [
        "What is diabetes?",
        "How to treat hypertension?",
        "What causes cancer?"
    ]
    
    # Run ablation studies
    results = await run_ablation_studies(
        graph=rag.knowledge_graph_inst,
        embedding_func=rag.embedding_func,
        test_queries=test_queries,
        config=config
    )
    
    # Print feature ablation results
    print("\nFeature Ablation Results:")
    for feature, metrics in results['feature_ablation'].items():
        print(f"  Without {feature}:")
        print(f"    MRR: {metrics['mrr']:.3f}")
        print(f"    Precision@10: {metrics['precision_at_10']:.3f}")
    
    # Print module ablation results
    print("\nModule Ablation Results:")
    for module, metrics in results['module_ablation'].items():
        print(f"  Without {module}:")
        print(f"    MRR: {metrics['mrr']:.3f}")
        print(f"    Retrieval time: {metrics['avg_time']:.3f}s")

# Run
asyncio.run(run_ablation())
```

### Performance Monitoring

Track retrieval performance in real-time:

```python
from hypergraphrag.retrieval import get_global_monitor

# Get global monitor
monitor = get_global_monitor()

# Track retrieval
async def monitored_retrieval(rag, query):
    with monitor.track_retrieval(query=query):
        result = await rag.query(query)
    return result

# Get metrics
metrics = monitor.get_metrics()
print(f"Total retrievals: {metrics.total_retrievals}")
print(f"Average time: {metrics.avg_retrieval_time:.3f}s")
print(f"P95 time: {metrics.p95_retrieval_time:.3f}s")
```

---

## Advanced Topics

### Custom Quality Features

Add your own quality features:

```python
from hypergraphrag.quality import GraphFeatureExtractor

class CustomFeatureExtractor(GraphFeatureExtractor):
    async def compute_custom_feature(self, hyperedge_id: str) -> float:
        """Compute a custom quality feature."""
        # Your custom logic here
        node = await self.graph.get_node(hyperedge_id)
        # Example: length-based feature
        text_length = len(node.get('hyperedge', ''))
        return min(1.0, text_length / 100.0)

# Use custom extractor
extractor = CustomFeatureExtractor(rag.knowledge_graph_inst)
custom_score = await extractor.compute_custom_feature('hyperedge_1')
```

### Custom Update Strategies

Implement your own weight update strategy:

```python
from hypergraphrag.dynamic import WeightUpdater

class CustomWeightUpdater(WeightUpdater):
    def _custom_update(self, current: float, feedback: float) -> float:
        """Custom update strategy."""
        # Your custom logic here
        # Example: sigmoid-based update
        import math
        delta = self.alpha * (feedback - 0.5)
        return current * (1 + math.tanh(delta))

# Use custom updater
updater = CustomWeightUpdater(rag.knowledge_graph_inst, config)
```

### Batch Processing

Process large datasets efficiently:

```python
async def batch_process_documents(documents, batch_size=10):
    """Process documents in batches."""
    rag = HyperGraphRAG(working_dir="expr/large_project")
    
    for i in range(0, len(documents), batch_size):
        batch = documents[i:i+batch_size]
        await rag.insert(batch)
        print(f"Processed batch {i//batch_size + 1}")
    
    return rag

# Run
documents = [...]  # Your large document list
rag = asyncio.run(batch_process_documents(documents))
```

### Multi-Domain Support

Handle multiple domains in one system:

```python
# Configure for multiple domains
config = {
    'entity_taxonomy': {
        'legal': ['law', 'article', 'court', 'party', 'crime', 'penalty'],
        'medical': ['disease', 'symptom', 'treatment', 'drug', 'procedure'],
        'academic': ['paper', 'author', 'institution', 'keyword', 'conference']
    }
}

# Switch domains dynamically
async def query_multi_domain(rag, query, domain):
    entity_filter = EntityTypeFilter(
        graph=rag.knowledge_graph_inst,
        llm_model_func=rag.llm_model_func,
        config={'domain': domain, 'entity_taxonomy': config['entity_taxonomy']}
    )
    
    # Use domain-specific filtering
    relevant_types = await entity_filter.identify_relevant_types(query)
    # ... continue with retrieval
```

---

## Troubleshooting

### Common Issues

#### Issue 1: Out of Memory

**Symptom:** Python crashes with memory error

**Solution:**
```python
# Use LiteRetriever for large graphs
from hypergraphrag.retrieval import LiteRetriever

lite_retriever = LiteRetriever(graph, vdb, embedding_func, config={
    'cache_size': 500  # Reduce cache size
})
```

#### Issue 2: Slow Quality Computation

**Symptom:** Quality scoring takes too long

**Solution:**
```python
# Disable expensive features
config = {
    'quality_feature_weights': {
        'degree_centrality': 0.4,  # Fast
        'coherence': 0.6,          # Moderate
        'betweenness': 0.0,        # Disable (slow)
        'clustering': 0.0,         # Disable (slow)
        'text_quality': 0.0        # Disable
    }
}
```

#### Issue 3: API Rate Limits

**Symptom:** OpenAI API rate limit errors

**Solution:**
```python
# Enable LLM caching
rag = HyperGraphRAG(
    working_dir="expr/project",
    enable_llm_cache=True  # Cache LLM responses
)

# Add retry logic
import time

async def query_with_retry(rag, query, max_retries=3):
    for attempt in range(max_retries):
        try:
            return await rag.query(query)
        except Exception as e:
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt
                print(f"Retry in {wait_time}s...")
                time.sleep(wait_time)
            else:
                raise
```

#### Issue 4: Low Quality Scores

**Symptom:** All hyperedges have low quality scores

**Solution:**
```python
# Check feature distributions
from hypergraphrag.quality import compute_quality_statistics

stats = await compute_quality_statistics(
    scorer,
    hyperedge_ids
)

print("Feature Statistics:")
for feature, stat in stats.items():
    print(f"  {feature}: mean={stat['mean']:.3f}, std={stat['std']:.3f}")

# Adjust feature weights if needed
```

### Getting Help

- **Documentation**: Check [API Reference](API_REFERENCE.md)
- **Examples**: See `examples/` directory
- **Issues**: Open an issue on [GitHub](https://github.com/tao-hpu/HyperGraphRAG/issues)
- **Email**: Contact maintainer at [your-email]

---

## Best Practices

### 1. Start Small

Begin with a small dataset to understand the system:
```python
# Start with 10-20 documents
test_documents = documents[:20]
await rag.insert(test_documents)
```

### 2. Monitor Performance

Always track performance metrics:
```python
from hypergraphrag.retrieval import get_global_monitor

monitor = get_global_monitor()
# ... perform operations ...
metrics = monitor.get_metrics()
```

### 3. Use Appropriate Configurations

Choose configurations based on your use case:

**For Research (Accuracy Priority):**
```python
config = {
    'quality_mode': 'supervised',
    'strategy': 'ema',
    'similarity_weight': 0.4,
    'quality_weight': 0.4,
    'dynamic_weight': 0.2
}
```

**For Production (Speed Priority):**
```python
config = {
    'quality_mode': 'unsupervised',
    'strategy': 'additive',
    'similarity_weight': 0.6,
    'quality_weight': 0.3,
    'dynamic_weight': 0.1,
    'use_lite_retriever': True
}
```

### 4. Regular Maintenance

Periodically refine your knowledge graph:
```python
from hypergraphrag.dynamic import HyperedgeRefiner

refiner = HyperedgeRefiner(graph, config={
    'quality_threshold': 0.5,
    'soft_filter': True
})

# Filter low-quality hyperedges monthly
result = await refiner.filter_low_quality(all_hyperedge_ids)
print(f"Filtered {len(result['filtered'])} hyperedges")
```

### 5. Version Control

Track your experiments:
```python
import json
from datetime import datetime

experiment_metadata = {
    'timestamp': datetime.now().isoformat(),
    'config': config,
    'dataset': 'cail2019',
    'git_commit': 'abc123',  # Track code version
    'results': results
}

with open('outputs/experiment_metadata.json', 'w') as f:
    json.dump(experiment_metadata, f, indent=2)
```

---

## Next Steps

Now that you've learned the basics, explore:

1. **[API Reference](API_REFERENCE.md)** - Detailed API documentation
2. **[Configuration Guide](CONFIGURATION_GUIDE.md)** - All configuration options
3. **[Examples](../examples/)** - Complete working examples
4. **[FAQ](FAQ.md)** - Frequently asked questions
5. **[Thesis Overview](THESIS_OVERVIEW.md)** - Research methodology

---

**Happy researching with DynHyperRAG!** 🚀

---

**Last Updated:** 2025-01-10
**Version:** 1.0.0
