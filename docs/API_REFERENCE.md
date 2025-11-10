# DynHyperRAG API Reference

This document provides comprehensive API documentation for the DynHyperRAG system modules.

## Table of Contents

1. [Quality Assessment Module](#quality-assessment-module)
2. [Dynamic Update Module](#dynamic-update-module)
3. [Efficient Retrieval Module](#efficient-retrieval-module)
4. [Evaluation Framework](#evaluation-framework)
5. [Data Processing Module](#data-processing-module)

---

## Quality Assessment Module

The quality assessment module (`hypergraphrag.quality`) provides functionality for evaluating hyperedge quality based on graph structure features and semantic coherence.

### QualityScorer

Main class for computing hyperedge quality scores.

**Import:**
```python
from hypergraphrag.quality import QualityScorer
```

**Constructor:**
```python
QualityScorer(
    knowledge_graph_inst: BaseGraphStorage,
    embedding_func: Callable,
    config: Optional[Dict] = None
)
```

**Parameters:**
- `knowledge_graph_inst`: Knowledge graph storage instance
- `embedding_func`: Function for computing text embeddings
- `config`: Configuration dictionary with keys:
  - `quality_mode`: 'unsupervised' or 'supervised' (default: 'unsupervised')
  - `quality_feature_weights`: Dict of feature weights (default: see below)

**Default Feature Weights:**
```python
{
    'degree_centrality': 0.2,
    'betweenness': 0.15,
    'clustering': 0.15,
    'coherence': 0.3,
    'text_quality': 0.2
}
```

**Methods:**

#### compute_quality_score()

Compute quality score for a hyperedge.

```python
async def compute_quality_score(hyperedge_id: str) -> Dict
```

**Parameters:**
- `hyperedge_id`: ID of the hyperedge node

**Returns:**
Dictionary containing:
- `quality_score`: Float between 0 and 1
- `features`: Dict of normalized feature values
- `mode`: 'unsupervised' or 'supervised'

**Example:**
```python
from hypergraphrag.quality import QualityScorer

scorer = QualityScorer(graph, embedding_func, config={
    'quality_mode': 'unsupervised',
    'quality_feature_weights': {
        'degree_centrality': 0.2,
        'betweenness': 0.15,
        'clustering': 0.15,
        'coherence': 0.3,
        'text_quality': 0.2
    }
})

result = await scorer.compute_quality_score('hyperedge_123')
print(f"Quality score: {result['quality_score']:.3f}")
print(f"Features: {result['features']}")
```

#### batch_compute_quality_scores()

Compute quality scores for multiple hyperedges in parallel.

```python
async def batch_compute_quality_scores(
    hyperedge_ids: List[str],
    show_progress: bool = True
) -> Dict[str, Dict]
```

**Parameters:**
- `hyperedge_ids`: List of hyperedge IDs
- `show_progress`: Whether to show progress bar

**Returns:**
Dictionary mapping hyperedge IDs to quality score results

**Example:**
```python
hyperedge_ids = ['he_1', 'he_2', 'he_3']
results = await scorer.batch_compute_quality_scores(hyperedge_ids)

for he_id, result in results.items():
    print(f"{he_id}: {result['quality_score']:.3f}")
```

### GraphFeatureExtractor

Extracts graph structure features for quality assessment.

**Import:**
```python
from hypergraphrag.quality import GraphFeatureExtractor
```

**Constructor:**
```python
GraphFeatureExtractor(knowledge_graph_inst: BaseGraphStorage)
```

**Methods:**

#### compute_degree_centrality()
```python
async def compute_degree_centrality(hyperedge_id: str) -> float
```

Compute normalized degree centrality (0-1).

#### compute_betweenness()
```python
async def compute_betweenness(hyperedge_id: str) -> float
```

Compute edge betweenness centrality using NetworkX.

#### compute_clustering()
```python
async def compute_clustering(hyperedge_id: str) -> float
```

Compute local clustering coefficient.

#### compute_text_quality()
```python
async def compute_text_quality(hyperedge_id: str) -> float
```

Evaluate text quality based on length and completeness.

### CoherenceMetric

Measures semantic coherence of entities within a hyperedge.

**Import:**
```python
from hypergraphrag.quality import CoherenceMetric
```

**Constructor:**
```python
CoherenceMetric(
    embedding_func: Callable,
    knowledge_graph_inst: BaseGraphStorage
)
```

**Methods:**

#### compute_coherence()
```python
async def compute_coherence(hyperedge_id: str) -> float
```

Compute hyperedge coherence score (0-1) based on entity embedding similarity.

**Example:**
```python
from hypergraphrag.quality import CoherenceMetric

coherence_metric = CoherenceMetric(embedding_func, graph)
coherence = await coherence_metric.compute_coherence('hyperedge_123')
print(f"Coherence: {coherence:.3f}")
```

### FeatureAnalyzer

Analyzes feature importance using SHAP values.

**Import:**
```python
from hypergraphrag.quality import FeatureAnalyzer
```

**Constructor:**
```python
FeatureAnalyzer(scorer: QualityScorer)
```

**Methods:**

#### analyze_feature_importance()
```python
async def analyze_feature_importance(
    hyperedges: List[str],
    ground_truth: Dict[str, float],
    method: str = 'shap'
) -> Dict
```

Analyze which features are most important for quality prediction.

**Parameters:**
- `hyperedges`: List of hyperedge IDs
- `ground_truth`: Dict mapping hyperedge IDs to true quality labels
- `method`: 'shap' or 'permutation'

**Returns:**
Dictionary containing:
- `feature_importance`: Dict of feature names to importance scores
- `shap_values`: SHAP values array (if method='shap')
- `model`: Trained model

**Example:**
```python
from hypergraphrag.quality import FeatureAnalyzer

analyzer = FeatureAnalyzer(scorer)
ground_truth = {'he_1': 0.8, 'he_2': 0.3, 'he_3': 0.9}
result = await analyzer.analyze_feature_importance(
    hyperedge_ids,
    ground_truth,
    method='shap'
)

print("Feature Importance:")
for feature, importance in result['feature_importance'].items():
    print(f"  {feature}: {importance:.3f}")
```

---

## Dynamic Update Module

The dynamic update module (`hypergraphrag.dynamic`) provides functionality for dynamically adjusting hyperedge weights based on retrieval feedback.

### WeightUpdater

Implements dynamic weight adjustment with multiple strategies.

**Import:**
```python
from hypergraphrag.dynamic import WeightUpdater
```

**Constructor:**
```python
WeightUpdater(graph: BaseGraphStorage, config: dict)
```

**Parameters:**
- `graph`: Graph storage instance
- `config`: Configuration dictionary with keys:
  - `strategy`: 'ema', 'additive', or 'multiplicative' (default: 'ema')
  - `update_alpha`: Learning rate (0 < α ≤ 1, default: 0.1)
  - `decay_factor`: Decay factor (0 < decay ≤ 1, default: 0.99)
  - `min_weight_ratio`: Minimum weight ratio (default: 0.5)
  - `max_weight_ratio`: Maximum weight ratio (default: 2.0)
  - `track_history`: Whether to track update history (default: True)

**Methods:**

#### update_weights()
```python
async def update_weights(
    hyperedge_id: str,
    feedback_signal: float,
    metadata: Optional[Dict] = None
) -> float
```

Update hyperedge weight based on feedback signal.

**Parameters:**
- `hyperedge_id`: ID of the hyperedge
- `feedback_signal`: Feedback value (0-1, higher = more useful)
- `metadata`: Optional metadata about the update

**Returns:**
New weight value

**Example:**
```python
from hypergraphrag.dynamic import WeightUpdater

updater = WeightUpdater(graph, config={
    'strategy': 'ema',
    'update_alpha': 0.1,
    'decay_factor': 0.99
})

# Positive feedback: hyperedge was useful
new_weight = await updater.update_weights('he_1', feedback_signal=0.8)
print(f"Updated weight: {new_weight:.3f}")

# Negative feedback: hyperedge was not useful
new_weight = await updater.update_weights('he_2', feedback_signal=0.2)
```

#### batch_update_weights()
```python
async def batch_update_weights(
    feedback_signals: Dict[str, float],
    metadata: Optional[Dict] = None
) -> Dict[str, float]
```

Update weights for multiple hyperedges in parallel.

**Example:**
```python
feedback = {
    'he_1': 0.9,  # Very useful
    'he_2': 0.3,  # Not useful
    'he_3': 0.7   # Moderately useful
}

new_weights = await updater.batch_update_weights(feedback)
```

### FeedbackExtractor

Extracts feedback signals from LLM generation.

**Import:**
```python
from hypergraphrag.dynamic import FeedbackExtractor
```

**Constructor:**
```python
FeedbackExtractor(embedding_func: Callable, config: dict)
```

**Parameters:**
- `embedding_func`: Function for computing embeddings
- `config`: Configuration dictionary with keys:
  - `feedback_method`: 'embedding', 'citation', or 'attention' (default: 'embedding')
  - `feedback_threshold`: Similarity threshold (default: 0.7)

**Methods:**

#### extract_feedback()
```python
async def extract_feedback(
    answer: str,
    retrieved_hyperedges: List[Dict]
) -> Dict[str, float]
```

Extract feedback signals indicating which hyperedges were useful.

**Parameters:**
- `answer`: Generated answer text
- `retrieved_hyperedges`: List of retrieved hyperedge dicts

**Returns:**
Dictionary mapping hyperedge IDs to feedback signals (0-1)

**Example:**
```python
from hypergraphrag.dynamic import FeedbackExtractor

extractor = FeedbackExtractor(embedding_func, config={
    'feedback_method': 'embedding',
    'feedback_threshold': 0.7
})

answer = "The patient has diabetes and hypertension..."
retrieved = [
    {'id': 'he_1', 'hyperedge': 'diabetes treatment'},
    {'id': 'he_2', 'hyperedge': 'cancer symptoms'}
]

feedback = await extractor.extract_feedback(answer, retrieved)
# feedback = {'he_1': 0.85, 'he_2': 0.25}
```

### HyperedgeRefiner

Filters and refines low-quality hyperedges.

**Import:**
```python
from hypergraphrag.dynamic import HyperedgeRefiner
```

**Constructor:**
```python
HyperedgeRefiner(graph: BaseGraphStorage, config: dict)
```

**Parameters:**
- `graph`: Graph storage instance
- `config`: Configuration dictionary with keys:
  - `quality_threshold`: Minimum quality score (default: 0.5)
  - `soft_filter`: Use soft filtering (default: True)
  - `threshold_strategy`: 'fixed', 'percentile', or 'f1_optimal' (default: 'fixed')

**Methods:**

#### filter_low_quality()
```python
async def filter_low_quality(hyperedge_ids: List[str]) -> Dict
```

Filter hyperedges below quality threshold.

**Returns:**
Dictionary containing:
- `filtered`: List of filtered hyperedge IDs
- `kept`: List of kept hyperedge IDs
- `filter_rate`: Proportion of hyperedges filtered

**Example:**
```python
from hypergraphrag.dynamic import HyperedgeRefiner

refiner = HyperedgeRefiner(graph, config={
    'quality_threshold': 0.5,
    'soft_filter': True
})

result = await refiner.filter_low_quality(all_hyperedge_ids)
print(f"Filtered {len(result['filtered'])} low-quality hyperedges")
print(f"Filter rate: {result['filter_rate']:.1%}")
```

---

## Efficient Retrieval Module

The efficient retrieval module (`hypergraphrag.retrieval`) provides optimized retrieval using entity type filtering and quality-aware ranking.

### EntityTypeFilter

Filters hyperedges by entity types to reduce search space.

**Import:**
```python
from hypergraphrag.retrieval import EntityTypeFilter
```

**Constructor:**
```python
EntityTypeFilter(
    graph: BaseGraphStorage,
    llm_model_func: Optional[Callable],
    config: dict
)
```

**Parameters:**
- `graph`: Graph storage instance
- `llm_model_func`: Optional LLM function for type classification
- `config`: Configuration dictionary with keys:
  - `domain`: 'legal' or 'academic' (default: 'legal')
  - `entity_taxonomy`: Dict mapping domains to entity types
  - `use_llm_classification`: Whether to use LLM (default: False)

**Methods:**

#### identify_relevant_types()
```python
async def identify_relevant_types(query: str) -> List[str]
```

Identify relevant entity types from query.

#### filter_hyperedges_by_type()
```python
async def filter_hyperedges_by_type(
    hyperedge_ids: List[str],
    relevant_types: List[str]
) -> List[str]
```

Filter hyperedges to only those connecting relevant entity types.

**Example:**
```python
from hypergraphrag.retrieval import EntityTypeFilter

filter = EntityTypeFilter(graph, llm_func, config={
    'domain': 'legal',
    'entity_taxonomy': {
        'legal': ['law', 'article', 'court', 'party', 'crime', 'penalty']
    }
})

# Identify relevant types from query
query = "What are the penalties for theft?"
relevant_types = await filter.identify_relevant_types(query)
# relevant_types = ['crime', 'penalty']

# Filter hyperedges
filtered_ids = await filter.filter_hyperedges_by_type(
    all_hyperedge_ids,
    relevant_types
)
print(f"Reduced search space from {len(all_hyperedge_ids)} to {len(filtered_ids)}")
```

### QualityAwareRanker

Ranks hyperedges using composite scoring function.

**Import:**
```python
from hypergraphrag.retrieval import QualityAwareRanker
```

**Constructor:**
```python
QualityAwareRanker(config: dict)
```

**Parameters:**
- `config`: Configuration dictionary with keys:
  - `similarity_weight` (α): Weight for similarity (default: 0.5)
  - `quality_weight` (β): Weight for quality (default: 0.3)
  - `dynamic_weight` (γ): Weight for dynamic weight (default: 0.2)
  - `normalize_scores`: Whether to normalize (default: True)
  - `provide_explanation`: Include explanations (default: False)

**Scoring Function:**
```
score = α × similarity + β × quality + γ × dynamic_weight
```

**Methods:**

#### rank_hyperedges()
```python
async def rank_hyperedges(
    query: str,
    hyperedges: List[Dict],
    graph: Optional[BaseGraphStorage] = None
) -> List[Dict]
```

Rank hyperedges using quality-aware scoring.

**Example:**
```python
from hypergraphrag.retrieval import QualityAwareRanker

ranker = QualityAwareRanker(config={
    'similarity_weight': 0.5,
    'quality_weight': 0.3,
    'dynamic_weight': 0.2
})

# Retrieved hyperedges from vector search
retrieved = [
    {'id': 'he_1', 'distance': 0.9, 'quality_score': 0.7, 'dynamic_weight': 1.2},
    {'id': 'he_2', 'distance': 0.8, 'quality_score': 0.9, 'dynamic_weight': 1.5}
]

ranked = await ranker.rank_hyperedges(query, retrieved)
# Results sorted by final_score
```

### LiteRetriever

Lightweight retriever for resource-constrained environments.

**Import:**
```python
from hypergraphrag.retrieval import LiteRetriever
```

**Constructor:**
```python
LiteRetriever(
    graph: BaseGraphStorage,
    vdb: BaseVectorStorage,
    embedding_func: Callable,
    config: dict
)
```

**Features:**
- Simplified quality features (degree + coherence only)
- Simple dictionary caching
- Faster but slightly less accurate than full retriever

**Methods:**

#### retrieve()
```python
async def retrieve(query: str, top_k: int = 10) -> List[Dict]
```

Perform lightweight retrieval.

**Example:**
```python
from hypergraphrag.retrieval import LiteRetriever

lite_retriever = LiteRetriever(graph, vdb, embedding_func, config={
    'cache_size': 1000
})

results = await lite_retriever.retrieve("diabetes treatment", top_k=10)
```

### PerformanceMonitor

Monitors and tracks retrieval performance metrics.

**Import:**
```python
from hypergraphrag.retrieval import PerformanceMonitor, get_global_monitor
```

**Usage:**
```python
from hypergraphrag.retrieval import get_global_monitor

# Get global monitor instance
monitor = get_global_monitor()

# Track a retrieval operation
with monitor.track_retrieval(query="test query"):
    results = await retriever.retrieve(query)

# Get metrics
metrics = monitor.get_metrics()
print(f"Average retrieval time: {metrics.avg_retrieval_time:.3f}s")
print(f"Total retrievals: {metrics.total_retrievals}")
```

---

## Evaluation Framework

The evaluation framework (`hypergraphrag.evaluation`) provides comprehensive metrics and experiment pipelines.

### IntrinsicMetrics

Metrics for evaluating hyperedge quality.

**Import:**
```python
from hypergraphrag.evaluation import IntrinsicMetrics
```

**Methods:**

#### precision_recall_f1()
```python
@staticmethod
def precision_recall_f1(
    predicted: set,
    ground_truth: set
) -> Dict[str, float]
```

Compute precision, recall, and F1 score.

#### quality_score_correlation()
```python
@staticmethod
def quality_score_correlation(
    predicted_scores: Dict[str, float],
    ground_truth_labels: Dict[str, float]
) -> float
```

Compute Spearman correlation between predicted and true quality.

#### roc_auc()
```python
@staticmethod
def roc_auc(
    predicted_scores: Dict[str, float],
    ground_truth_labels: Dict[str, float]
) -> float
```

Compute ROC AUC score.

**Example:**
```python
from hypergraphrag.evaluation import IntrinsicMetrics

predicted = {'he_1', 'he_2', 'he_3'}
ground_truth = {'he_1', 'he_3', 'he_4'}

metrics = IntrinsicMetrics.precision_recall_f1(predicted, ground_truth)
print(f"Precision: {metrics['precision']:.3f}")
print(f"Recall: {metrics['recall']:.3f}")
print(f"F1: {metrics['f1']:.3f}")
```

### ExtrinsicMetrics

Metrics for evaluating end-to-end retrieval performance.

**Import:**
```python
from hypergraphrag.evaluation import ExtrinsicMetrics
```

**Methods:**

#### mean_reciprocal_rank()
```python
@staticmethod
def mean_reciprocal_rank(
    results: List[List[str]],
    ground_truth: List[str]
) -> float
```

Compute Mean Reciprocal Rank (MRR).

#### precision_at_k()
```python
@staticmethod
def precision_at_k(
    results: List[List[str]],
    ground_truth: List[set],
    k: int
) -> float
```

Compute Precision@K.

**Example:**
```python
from hypergraphrag.evaluation import ExtrinsicMetrics

results = [['he_1', 'he_2', 'he_3'], ['he_4', 'he_5', 'he_6']]
ground_truth = [{'he_1', 'he_3'}, {'he_4'}]

mrr = ExtrinsicMetrics.mean_reciprocal_rank(results, ['he_1', 'he_4'])
p_at_3 = ExtrinsicMetrics.precision_at_k(results, ground_truth, k=3)

print(f"MRR: {mrr:.3f}")
print(f"Precision@3: {p_at_3:.3f}")
```

### EfficiencyMetrics

Metrics for measuring computational efficiency.

**Import:**
```python
from hypergraphrag.evaluation import EfficiencyMetrics
```

**Methods:**

#### measure_retrieval_time()
```python
@staticmethod
def measure_retrieval_time(
    retrieval_func: Callable,
    queries: List[str]
) -> Dict[str, float]
```

Measure retrieval time statistics.

**Returns:**
- `mean_time`: Average retrieval time
- `std_time`: Standard deviation
- `median_time`: Median time
- `p95_time`: 95th percentile time

**Example:**
```python
from hypergraphrag.evaluation import EfficiencyMetrics

async def retrieval_func(query):
    return await retriever.retrieve(query)

queries = ["query 1", "query 2", "query 3"]
time_stats = EfficiencyMetrics.measure_retrieval_time(retrieval_func, queries)

print(f"Mean time: {time_stats['mean_time']:.3f}s")
print(f"P95 time: {time_stats['p95_time']:.3f}s")
```

### ExperimentPipeline

Automated experiment pipeline for reproducible research.

**Import:**
```python
from hypergraphrag.evaluation import ExperimentPipeline
```

**Constructor:**
```python
ExperimentPipeline(config: dict)
```

**Methods:**

#### run_full_pipeline()
```python
async def run_full_pipeline(dataset_name: str) -> Dict
```

Run complete experiment pipeline including data loading, extraction, evaluation, and reporting.

**Example:**
```python
from hypergraphrag.evaluation import ExperimentPipeline

pipeline = ExperimentPipeline(config={
    'data_dir': 'expr/cail2019',
    'output_dir': 'outputs/experiments'
})

report = await pipeline.run_full_pipeline('cail2019')
print(f"Experiment complete. Results saved to {report['output_path']}")
```

### AblationStudyRunner

Runs ablation studies to measure feature/module contributions.

**Import:**
```python
from hypergraphrag.evaluation import AblationStudyRunner, run_ablation_studies
```

**Quick Usage:**
```python
from hypergraphrag.evaluation import run_ablation_studies

results = await run_ablation_studies(
    graph=graph,
    embedding_func=embedding_func,
    test_queries=queries,
    config=config
)

print("Feature Ablation Results:")
for feature, metrics in results['feature_ablation'].items():
    print(f"  Without {feature}: MRR = {metrics['mrr']:.3f}")
```

---

## Data Processing Module

The data processing module (`hypergraphrag.data`) provides loaders for different datasets.

### CAIL2019Loader

Loader for CAIL2019 legal dataset.

**Import:**
```python
from hypergraphrag.data import CAIL2019Loader
```

**Constructor:**
```python
CAIL2019Loader(data_path: str, config: Optional[Dict] = None)
```

**Methods:**

#### load_and_clean()
```python
def load_and_clean() -> Dict
```

Load and clean CAIL2019 data.

**Returns:**
Dictionary containing:
- `train`: Training data
- `val`: Validation data
- `test`: Test data
- `statistics`: Dataset statistics

**Example:**
```python
from hypergraphrag.data import CAIL2019Loader

loader = CAIL2019Loader('data/CAIL2019/阅读理解/data')
data = loader.load_and_clean()

print(f"Train samples: {len(data['train'])}")
print(f"Val samples: {len(data['val'])}")
print(f"Test samples: {len(data['test'])}")
print(f"Statistics: {data['statistics']}")
```

### AcademicLoader

Loader for academic datasets (PubMed/AMiner).

**Import:**
```python
from hypergraphrag.data import AcademicLoader
```

**Constructor:**
```python
AcademicLoader(
    data_source: str,
    data_path: str,
    config: Optional[Dict] = None
)
```

**Parameters:**
- `data_source`: 'pubmed' or 'aminer'
- `data_path`: Path to data files
- `config`: Optional configuration

**Example:**
```python
from hypergraphrag.data import AcademicLoader

loader = AcademicLoader('pubmed', 'data/pubmed')
data = loader.load_and_process()

print(f"Papers: {len(data['papers'])}")
print(f"Authors: {len(data['authors'])}")
```

---

## Complete Usage Example

Here's a complete example showing how to use DynHyperRAG:

```python
import asyncio
from hypergraphrag import HyperGraphRAG
from hypergraphrag.quality import QualityScorer
from hypergraphrag.dynamic import WeightUpdater, FeedbackExtractor
from hypergraphrag.retrieval import EntityTypeFilter, QualityAwareRanker

async def main():
    # 1. Initialize HyperGraphRAG
    rag = HyperGraphRAG(
        working_dir="expr/example",
        embedding_func=embedding_func,
        llm_model_func=llm_func
    )
    
    # 2. Build knowledge graph
    await rag.insert(documents)
    
    # 3. Initialize DynHyperRAG components
    scorer = QualityScorer(rag.knowledge_graph_inst, embedding_func)
    updater = WeightUpdater(rag.knowledge_graph_inst, config={
        'strategy': 'ema',
        'update_alpha': 0.1
    })
    extractor = FeedbackExtractor(embedding_func, config={
        'feedback_method': 'embedding'
    })
    ranker = QualityAwareRanker(config={
        'similarity_weight': 0.5,
        'quality_weight': 0.3,
        'dynamic_weight': 0.2
    })
    
    # 4. Compute quality scores for all hyperedges
    hyperedge_ids = await rag.knowledge_graph_inst.get_all_hyperedge_ids()
    quality_results = await scorer.batch_compute_quality_scores(hyperedge_ids)
    
    # 5. Query with quality-aware retrieval
    query = "What are the symptoms of diabetes?"
    results = await rag.query(query)
    
    # 6. Extract feedback and update weights
    feedback = await extractor.extract_feedback(
        results['answer'],
        results['retrieved_hyperedges']
    )
    await updater.batch_update_weights(feedback)
    
    print(f"Answer: {results['answer']}")
    print(f"Updated {len(feedback)} hyperedge weights")

if __name__ == "__main__":
    asyncio.run(main())
```

---

## Configuration Reference

### Complete Configuration Example

```python
config = {
    # Quality Assessment
    'quality_mode': 'unsupervised',  # or 'supervised'
    'quality_feature_weights': {
        'degree_centrality': 0.2,
        'betweenness': 0.15,
        'clustering': 0.15,
        'coherence': 0.3,
        'text_quality': 0.2
    },
    
    # Dynamic Update
    'strategy': 'ema',  # 'ema', 'additive', 'multiplicative'
    'update_alpha': 0.1,
    'decay_factor': 0.99,
    'min_weight_ratio': 0.5,
    'max_weight_ratio': 2.0,
    
    # Feedback Extraction
    'feedback_method': 'embedding',  # 'embedding', 'citation', 'attention'
    'feedback_threshold': 0.7,
    
    # Entity Type Filtering
    'domain': 'legal',  # 'legal', 'academic'
    'entity_taxonomy': {
        'legal': ['law', 'article', 'court', 'party', 'crime', 'penalty'],
        'academic': ['paper', 'author', 'institution', 'keyword', 'conference']
    },
    
    # Quality-Aware Ranking
    'similarity_weight': 0.5,
    'quality_weight': 0.3,
    'dynamic_weight': 0.2,
    
    # Hyperedge Refinement
    'quality_threshold': 0.5,
    'soft_filter': True,
    'threshold_strategy': 'fixed'  # 'fixed', 'percentile', 'f1_optimal'
}
```

---

## Error Handling

All async methods may raise exceptions. Use try-except blocks:

```python
try:
    result = await scorer.compute_quality_score(hyperedge_id)
except Exception as e:
    logger.error(f"Quality computation failed: {e}")
    # Use default score
    result = {'quality_score': 0.5, 'features': {}}
```

---

## Performance Tips

1. **Use batch operations** when processing multiple hyperedges
2. **Enable caching** for frequently accessed data
3. **Use LiteRetriever** for production environments with strict latency requirements
4. **Monitor performance** using PerformanceMonitor
5. **Adjust weights** (α, β, γ) based on your specific use case

---

## Further Reading

- [User Guide](USER_GUIDE.md) - Step-by-step tutorials
- [Configuration Guide](CONFIGURATION_GUIDE.md) - Detailed configuration options
- [FAQ](FAQ.md) - Frequently asked questions
- [Thesis Overview](THESIS_OVERVIEW.md) - Research background and methodology

---

**Last Updated:** 2025-01-10
**Version:** 1.0.0
