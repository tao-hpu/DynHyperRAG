# DynHyperRAG Frequently Asked Questions (FAQ)

## Table of Contents

1. [General Questions](#general-questions)
2. [Installation and Setup](#installation-and-setup)
3. [Quality Assessment](#quality-assessment)
4. [Dynamic Updates](#dynamic-updates)
5. [Retrieval and Performance](#retrieval-and-performance)
6. [Evaluation and Experiments](#evaluation-and-experiments)
7. [Troubleshooting](#troubleshooting)
8. [Advanced Usage](#advanced-usage)

---

## General Questions

### What is DynHyperRAG?

DynHyperRAG is a quality-aware dynamic hypergraph RAG system that extends the static HyperGraphRAG (NeurIPS 2025) with three key innovations:

1. **Graph-structure-based quality assessment** - Automatically evaluate hyperedge quality
2. **Quality-aware dynamic weight updates** - Adjust weights based on retrieval feedback
3. **Efficient retrieval with entity type filtering** - Optimize retrieval speed by 30%+

### How is DynHyperRAG different from HyperGraphRAG?

| Feature | HyperGraphRAG | DynHyperRAG |
|---------|---------------|-------------|
| Graph Structure | Static | Dynamic |
| Quality Assessment | None | Automatic (5 features) |
| Weight Updates | None | Feedback-driven |
| Retrieval Optimization | Basic | Entity filtering + quality ranking |
| Efficiency | Baseline | 30%+ faster |

### When should I use DynHyperRAG vs standard RAG?

Use DynHyperRAG when:
- You need to model complex n-ary relationships (not just binary)
- Your domain has rich entity relationships (legal, medical, academic)
- You want the system to improve over time with usage
- Retrieval quality is more important than simplicity

Use standard RAG when:
- Simple document retrieval is sufficient
- You have limited computational resources
- You don't need relationship modeling

### What are the system requirements?

**Minimum:**
- Python 3.11+
- 8GB RAM
- 10GB disk space
- OpenAI API key

**Recommended:**
- Python 3.11+
- 16GB+ RAM
- 50GB+ disk space
- GPU (optional, for faster embedding computation)

---

## Installation and Setup

### How do I install DynHyperRAG?

```bash
# Clone repository
git clone https://github.com/tao-hpu/HyperGraphRAG.git
cd HyperGraphRAG

# Create environment
conda create -n dynhyperrag python=3.11
conda activate dynhyperrag

# Install dependencies
pip install -r requirements.txt

# Configure API
cp .env.example .env
# Edit .env with your API key
```

See [Setup Guide](SETUP.md) for detailed instructions.

### Can I use a different LLM provider?

Yes! DynHyperRAG supports any OpenAI-compatible API:

```bash
# .env file
OPENAI_API_KEY=your_key
OPENAI_BASE_URL=https://your-provider.com/v1
LLM_MODEL=your-model-name
```

Tested providers:
- OpenAI
- Azure OpenAI
- Local models via LM Studio
- Ollama (with OpenAI compatibility)

### Do I need a GPU?

No, GPU is optional. DynHyperRAG works fine on CPU, but GPU can speed up:
- Embedding computation (if using local models)
- Large-scale quality assessment

### How much does it cost to run?

Costs depend on your usage:

**Small project (100 documents):**
- Construction: ~$0.50-1.00
- Queries: ~$0.01-0.05 per query

**Medium project (1000 documents):**
- Construction: ~$5-10
- Queries: ~$0.02-0.10 per query

**Large project (10000 documents):**
- Construction: ~$50-100
- Queries: ~$0.05-0.20 per query

Tips to reduce costs:
- Enable LLM caching
- Use smaller models (gpt-4o-mini)
- Use LiteRetriever for production

---

## Quality Assessment

### What are the 5 quality features?

1. **Degree Centrality** (20%): Number of entities connected
2. **Betweenness** (15%): Importance for graph connectivity
3. **Clustering** (15%): Density of neighborhood
4. **Coherence** (30%): Semantic similarity of entities
5. **Text Quality** (20%): Quality of source text

### How do I interpret quality scores?

Quality scores range from 0 to 1:
- **0.8-1.0**: Excellent quality, highly reliable
- **0.6-0.8**: Good quality, generally reliable
- **0.4-0.6**: Moderate quality, use with caution
- **0.2-0.4**: Low quality, likely unreliable
- **0.0-0.2**: Very low quality, should be filtered

### Can I customize feature weights?

Yes! Adjust weights based on your domain:

```python
# Coherence-focused (for academic papers)
config = {
    'quality_feature_weights': {
        'degree_centrality': 0.15,
        'betweenness': 0.1,
        'clustering': 0.1,
        'coherence': 0.5,
        'text_quality': 0.15
    }
}

# Structure-focused (for legal documents)
config = {
    'quality_feature_weights': {
        'degree_centrality': 0.3,
        'betweenness': 0.25,
        'clustering': 0.25,
        'coherence': 0.1,
        'text_quality': 0.1
    }
}
```

### How long does quality assessment take?

Depends on graph size:
- **Small (100 hyperedges)**: ~10-30 seconds
- **Medium (1000 hyperedges)**: ~2-5 minutes
- **Large (10000 hyperedges)**: ~20-60 minutes

Speed up with:
- Batch processing
- Disable slow features (betweenness, clustering)
- Use LiteRetriever

### Should I use supervised or unsupervised mode?

**Unsupervised (default):**
- No labeled data needed
- Fixed feature weights
- Good for most cases

**Supervised:**
- Requires labeled quality data (500+ samples)
- Learns optimal feature weights
- Better accuracy if you have labels

---

## Dynamic Updates

### How do dynamic weight updates work?

1. Query retrieves hyperedges
2. LLM generates answer
3. System extracts feedback (which hyperedges were useful)
4. Weights are updated based on feedback
5. Future queries benefit from updated weights

### What update strategy should I use?

**EMA (Exponential Moving Average)** - Recommended:
```python
config = {'strategy': 'ema', 'update_alpha': 0.1}
```
- Smooth updates
- Good balance of stability and adaptation

**Additive** - For conservative updates:
```python
config = {'strategy': 'additive', 'update_alpha': 0.05}
```
- Direct addition of feedback
- More stable but slower adaptation

**Multiplicative** - For aggressive updates:
```python
config = {'strategy': 'multiplicative', 'update_alpha': 0.15}
```
- Proportional updates
- Faster adaptation but less stable

### How do I tune the learning rate (alpha)?

**Higher alpha (0.2-0.5):**
- Faster adaptation
- More responsive to recent feedback
- Risk of instability

**Lower alpha (0.05-0.1):**
- Slower adaptation
- More stable
- Better for noisy feedback

**Recommended:** Start with 0.1 and adjust based on results.

### What is the decay factor?

Decay factor prevents weights from growing unbounded:
- **0.99** (default): Slow decay, weights persist longer
- **0.95**: Moderate decay
- **0.90**: Fast decay, weights fade quickly

### Can I disable dynamic updates?

Yes, set `update_alpha=0` or don't use WeightUpdater:

```python
# Static mode (no updates)
rag = HyperGraphRAG(working_dir="expr/project")
result = await rag.query(query)  # No weight updates
```

---

## Retrieval and Performance

### What is entity type filtering?

Entity type filtering reduces search space by only considering hyperedges that connect relevant entity types:

```python
# Query: "What are penalties for theft?"
# Relevant types: ['crime', 'penalty']
# Filter: Only hyperedges connecting crime/penalty entities
# Result: 70% reduction in search space
```

### How much faster is DynHyperRAG?

Typical improvements:
- **Entity filtering**: 30-50% faster retrieval
- **Quality ranking**: 10-20% faster (better results with fewer iterations)
- **Combined**: 40-60% faster overall

### When should I use LiteRetriever?

Use LiteRetriever when:
- Production environment with strict latency requirements
- Limited computational resources
- Willing to trade 5-10% accuracy for 50%+ speed

```python
from hypergraphrag.retrieval import LiteRetriever

lite = LiteRetriever(graph, vdb, embedding_func, config={
    'cache_size': 1000
})
results = await lite.retrieve(query, top_k=10)
```

### How do I optimize for speed?

```python
speed_config = {
    # Disable slow features
    'quality_feature_weights': {
        'degree_centrality': 0.5,
        'coherence': 0.5,
        'betweenness': 0.0,  # Slow
        'clustering': 0.0,   # Slow
        'text_quality': 0.0
    },
    
    # Use lite retriever
    'use_lite_retriever': True,
    'cache_size': 2000,
    
    # Async updates
    'async_updates': True,
    'batch_update_size': 200
}
```

### How do I optimize for accuracy?

```python
accuracy_config = {
    # All features enabled
    'quality_feature_weights': {
        'degree_centrality': 0.2,
        'betweenness': 0.15,
        'clustering': 0.15,
        'coherence': 0.3,
        'text_quality': 0.2
    },
    
    # Full retriever
    'use_lite_retriever': False,
    'use_llm_classification': True,
    
    # Conservative updates
    'strategy': 'ema',
    'update_alpha': 0.05
}
```

### What are the ranking weights (α, β, γ)?

Ranking score = α × similarity + β × quality + γ × dynamic_weight

**Balanced (default):**
```python
α=0.5, β=0.3, γ=0.2
```

**Similarity-focused:**
```python
α=0.7, β=0.2, γ=0.1
```

**Quality-focused:**
```python
α=0.3, β=0.5, γ=0.2
```

**Dynamic-focused (after many queries):**
```python
α=0.3, β=0.2, γ=0.5
```

---

## Evaluation and Experiments

### How do I evaluate my system?

```python
from hypergraphrag.evaluation import ExperimentPipeline

pipeline = ExperimentPipeline(config={
    'data_dir': 'expr/cail2019',
    'output_dir': 'outputs/experiments'
})

report = await pipeline.run_full_pipeline('cail2019')
print(f"MRR: {report['metrics']['mrr']:.3f}")
```

### What metrics should I use?

**Retrieval metrics:**
- MRR (Mean Reciprocal Rank)
- Precision@K
- Recall@K

**Answer quality:**
- BLEU
- ROUGE
- BERTScore

**Efficiency:**
- Retrieval time
- Memory usage
- API cost

### How do I run ablation studies?

```python
from hypergraphrag.evaluation import run_ablation_studies

results = await run_ablation_studies(
    graph=graph,
    embedding_func=embedding_func,
    test_queries=queries,
    config=config
)

# See which features/modules contribute most
print(results['feature_ablation'])
print(results['module_ablation'])
```

### How many queries do I need for evaluation?

**Minimum:** 50 queries
**Recommended:** 100-200 queries
**Ideal:** 500+ queries

More queries = more reliable statistics.

### How do I compare with baselines?

```python
from hypergraphrag.evaluation import BaselineComparator

comparator = BaselineComparator(config)
results = await comparator.compare_all_baselines(
    test_queries=queries,
    ground_truth=ground_truth
)

# Results include:
# - Static HyperGraphRAG
# - LLM confidence baseline
# - Rule-based baseline
# - Random baseline
```

---

## Troubleshooting

### Error: "Out of memory"

**Solutions:**
1. Use LiteRetriever
2. Reduce batch size
3. Reduce cache size
4. Process documents in smaller batches

```python
config = {
    'batch_size': 20,
    'cache_size': 500,
    'use_lite_retriever': True
}
```

### Error: "API rate limit exceeded"

**Solutions:**
1. Enable LLM caching
2. Add retry logic
3. Reduce concurrent requests
4. Use smaller batches

```python
# Enable caching
rag = HyperGraphRAG(
    working_dir="expr/project",
    enable_llm_cache=True
)

# Retry logic
import time

async def query_with_retry(rag, query, max_retries=3):
    for attempt in range(max_retries):
        try:
            return await rag.query(query)
        except Exception as e:
            if "rate limit" in str(e).lower() and attempt < max_retries - 1:
                wait_time = 2 ** attempt
                time.sleep(wait_time)
            else:
                raise
```

### Quality scores are all low

**Possible causes:**
1. Feature weights not tuned for your domain
2. Graph structure is sparse
3. Text quality is poor

**Solutions:**
```python
# Check feature distributions
from hypergraphrag.quality import compute_quality_statistics

stats = await compute_quality_statistics(scorer, hyperedge_ids)
print(stats)

# Adjust weights based on distributions
# If coherence is consistently low, reduce its weight
```

### Retrieval is slow

**Solutions:**
1. Use entity type filtering
2. Use LiteRetriever
3. Enable caching
4. Disable slow features

```python
# Fast configuration
config = {
    'use_lite_retriever': True,
    'cache_size': 2000,
    'quality_feature_weights': {
        'degree_centrality': 0.5,
        'coherence': 0.5,
        'betweenness': 0.0,
        'clustering': 0.0,
        'text_quality': 0.0
    }
}
```

### Weights are not updating

**Check:**
1. Is WeightUpdater initialized?
2. Is feedback extraction working?
3. Is alpha too small?

```python
# Debug weight updates
updater = WeightUpdater(graph, config={'strategy': 'ema', 'update_alpha': 0.1})

# Check feedback
feedback = await extractor.extract_feedback(answer, retrieved)
print(f"Feedback signals: {feedback}")

# Check updates
new_weights = await updater.batch_update_weights(feedback)
print(f"New weights: {new_weights}")
```

---

## Advanced Usage

### Can I add custom quality features?

Yes! Extend GraphFeatureExtractor:

```python
from hypergraphrag.quality import GraphFeatureExtractor

class CustomFeatureExtractor(GraphFeatureExtractor):
    async def compute_custom_feature(self, hyperedge_id: str) -> float:
        # Your custom logic
        node = await self.graph.get_node(hyperedge_id)
        # Example: entity diversity
        edges = await self.graph.get_node_edges(hyperedge_id)
        entity_types = set()
        for _, entity_id in edges:
            entity = await self.graph.get_node(entity_id)
            entity_types.add(entity.get('entity_type', 'unknown'))
        return len(entity_types) / 10.0  # Normalize
```

### Can I use multiple domains?

Yes! Configure entity taxonomy for multiple domains:

```python
config = {
    'entity_taxonomy': {
        'legal': ['law', 'article', 'court'],
        'medical': ['disease', 'symptom', 'treatment'],
        'academic': ['paper', 'author', 'institution']
    }
}

# Switch domains dynamically
filter = EntityTypeFilter(graph, llm_func, config)
filter.domain = 'medical'  # Switch to medical domain
```

### How do I integrate with existing systems?

DynHyperRAG provides a simple API:

```python
# Initialize once
rag = HyperGraphRAG(working_dir="expr/project")
scorer = QualityScorer(rag.knowledge_graph_inst, rag.embedding_func)
updater = WeightUpdater(rag.knowledge_graph_inst, config)

# Use in your application
async def answer_question(question: str) -> str:
    result = await rag.query(question)
    # Extract feedback and update weights
    # ...
    return result
```

### Can I export the knowledge graph?

Yes! Export to various formats:

```python
# Export to GraphML
import networkx as nx

G = nx.Graph()
async for node_id, node_data in rag.knowledge_graph_inst.nodes():
    G.add_node(node_id, **node_data)

async for source, target, edge_data in rag.knowledge_graph_inst.edges():
    G.add_edge(source, target, **edge_data)

nx.write_graphml(G, "knowledge_graph.graphml")

# Export to JSON
import json

graph_data = {
    'nodes': [],
    'edges': []
}

async for node_id, node_data in rag.knowledge_graph_inst.nodes():
    graph_data['nodes'].append({'id': node_id, **node_data})

async for source, target, edge_data in rag.knowledge_graph_inst.edges():
    graph_data['edges'].append({'source': source, 'target': target, **edge_data})

with open('knowledge_graph.json', 'w') as f:
    json.dump(graph_data, f, indent=2)
```

### How do I contribute to DynHyperRAG?

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

See [CONTRIBUTING.md](../CONTRIBUTING.md) for details.

---

## Getting More Help

### Documentation

- [API Reference](API_REFERENCE.md) - Complete API documentation
- [User Guide](USER_GUIDE.md) - Step-by-step tutorials
- [Configuration Guide](CONFIGURATION_GUIDE.md) - All configuration options
- [Thesis Overview](THESIS_OVERVIEW.md) - Research background

### Examples

Check the `examples/` directory for complete working examples:
- `example_quality_assessment.py`
- `example_dynamic_updates.py`
- `example_efficient_retrieval.py`
- `example_ablation_studies.py`

### Support

- **GitHub Issues**: [Report bugs or request features](https://github.com/tao-hpu/HyperGraphRAG/issues)
- **Discussions**: [Ask questions](https://github.com/tao-hpu/HyperGraphRAG/discussions)
- **Email**: Contact maintainer

### Citation

If you use DynHyperRAG in your research, please cite:

```bibtex
@phdthesis{an2025dynhyperrag,
      title={DynHyperRAG: Quality-Aware Dynamic Hypergraph for Efficient Retrieval-Augmented Generation},
      author={Tao An},
      year={2025},
      school={[University Name]},
      note={PhD Thesis, Expected June 2025}
}
```

---

**Last Updated:** 2025-01-10
**Version:** 1.0.0

**Have a question not answered here?** [Open an issue](https://github.com/tao-hpu/HyperGraphRAG/issues/new) and we'll add it to the FAQ!
