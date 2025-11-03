# Entity Type Filter for Efficient Retrieval

## Overview

The `EntityTypeFilter` module implements entity type filtering to reduce search space during hyperedge retrieval. By identifying relevant entity types from queries and filtering hyperedges based on the types of entities they connect, it significantly improves retrieval efficiency without sacrificing accuracy.

## Key Features

- **Keyword-based Type Identification**: Automatically identifies relevant entity types from query text
- **Domain-Specific Taxonomies**: Supports multiple domains (medical, legal, academic) with customizable entity types
- **Hyperedge Filtering**: Filters hyperedges based on connected entity types
- **Performance Metrics**: Tracks search space reduction and filtering statistics
- **LLM Integration**: Optional LLM-based type classification for advanced use cases
- **Batch Processing**: Efficient batch processing for large hyperedge sets

## Architecture

```
Query → Type Identification → Hyperedge Filtering → Reduced Search Space
         ↓                      ↓
    Keyword Match          Get Connected Entities
    LLM Classification     Check Entity Types
                          Filter by Relevance
```

## Installation

The EntityTypeFilter is part of the `hypergraphrag.retrieval` module:

```python
from hypergraphrag.retrieval import EntityTypeFilter
```

## Basic Usage

### 1. Initialize the Filter

```python
from hypergraphrag.retrieval import EntityTypeFilter

# Basic configuration
config = {
    "domain": "medical",
    "entity_taxonomy": {
        "medical": ["disease", "symptom", "treatment", "medication", "procedure", "anatomy"]
    }
}

# Create filter instance
entity_filter = EntityTypeFilter(graph, config)
```

### 2. Identify Relevant Types

```python
# Identify relevant entity types from a query
query = "What medication treats diabetes?"
relevant_types = await entity_filter.identify_relevant_types(query)
# Returns: ['medication', 'treatment']
```

### 3. Filter Hyperedges

```python
# Filter hyperedges by entity types
hyperedge_ids = ["HE1", "HE2", "HE3", "HE4"]
filtered_ids, stats = await entity_filter.filter_hyperedges_by_type(
    hyperedge_ids,
    relevant_types
)

# Check statistics
print(f"Reduced search space by {stats['reduction_rate']:.1f}%")
print(f"Filtered to {stats['filtered_count']} hyperedges")
```

## Configuration

### Environment Variables

Configure entity filtering in your `.env` file:

```bash
# Enable entity filtering
DYNHYPERRAG_ENTITY_FILTER_ENABLED=true

# Set domain
RETRIEVAL_DOMAIN=medical

# Custom entity types (comma-separated)
ENTITY_TYPES_MEDICAL=disease,symptom,treatment,medication,procedure,anatomy
ENTITY_TYPES_LEGAL=law,article,court,party,crime,penalty
ENTITY_TYPES_ACADEMIC=paper,author,institution,keyword,conference
```

### Programmatic Configuration

```python
from config import get_config

# Load configuration
config = get_config()
retrieval_config = config.get_retrieval_config()

# Create filter with loaded config
entity_filter = EntityTypeFilter(graph, retrieval_config)
```

## Domain-Specific Taxonomies

### Medical Domain

```python
medical_types = [
    "disease",      # Diabetes, Cancer, Hypertension
    "symptom",      # Fever, Pain, Fatigue
    "treatment",    # Therapy, Surgery, Rehabilitation
    "medication",   # Insulin, Aspirin, Antibiotics
    "procedure",    # MRI, Blood Test, Biopsy
    "anatomy"       # Heart, Liver, Brain
]
```

### Legal Domain

```python
legal_types = [
    "law",          # Criminal Law, Civil Law
    "article",      # Article 123, Section 5
    "court",        # Supreme Court, District Court
    "party",        # Plaintiff, Defendant
    "crime",        # Theft, Fraud, Assault
    "penalty"       # Fine, Imprisonment, Probation
]
```

### Academic Domain

```python
academic_types = [
    "paper",        # Research Paper, Article
    "author",       # Researcher, Professor
    "institution",  # University, Research Lab
    "keyword",      # Machine Learning, NLP
    "conference"    # NeurIPS, ACL, CVPR
]
```

## Advanced Features

### LLM-Based Type Classification

For more accurate type identification, enable LLM-based classification:

```python
config = {
    "domain": "medical",
    "entity_taxonomy": {...},
    "use_llm_classification": True
}

entity_filter = EntityTypeFilter(
    graph,
    config,
    llm_model_func=llm_func  # Your LLM function
)
```

### Custom Entity Types

Add custom entity types for your specific domain:

```python
# Add a new entity type
entity_filter.add_entity_type("medical", "biomarker")

# Switch domains
entity_filter.set_domain("legal")

# Get types for a domain
types = entity_filter.get_domain_types("academic")
```

### Batch Processing

The filter automatically processes hyperedges in batches for efficiency:

```python
# Processes in batches of 50 (default)
filtered_ids, stats = await entity_filter.filter_hyperedges_by_type(
    large_hyperedge_list,  # Can be thousands of IDs
    relevant_types
)
```

## Integration with Query Pipeline

### Basic Integration

```python
async def enhanced_query(query: str, graph, vdb, config):
    # 1. Initialize entity filter
    entity_filter = EntityTypeFilter(graph, config)
    
    # 2. Perform initial vector retrieval
    initial_results = await vdb.query(query, top_k=100)
    hyperedge_ids = [r['hyperedge_name'] for r in initial_results]
    
    # 3. Apply entity type filtering
    relevant_types = await entity_filter.identify_relevant_types(query)
    filtered_ids, stats = await entity_filter.filter_hyperedges_by_type(
        hyperedge_ids,
        relevant_types
    )
    
    logger.info(f"Search space reduced by {stats['reduction_rate']:.1f}%")
    
    # 4. Continue with quality-aware ranking
    # ... (quality ranking logic)
    
    return filtered_ids
```

### Integration with operate.py

To integrate into the main query pipeline, modify `operate.py`:

```python
# In _get_edge_data() or kg_query()

# After vector retrieval
if global_config.get("entity_filter_enabled", False):
    from hypergraphrag.retrieval import EntityTypeFilter
    
    entity_filter = EntityTypeFilter(
        knowledge_graph_inst,
        global_config.get("retrieval_config", {})
    )
    
    # Identify relevant types
    relevant_types = await entity_filter.identify_relevant_types(query)
    
    # Filter hyperedges
    hyperedge_ids = [e["hyperedge"] for e in edge_datas]
    filtered_ids, stats = await entity_filter.filter_hyperedges_by_type(
        hyperedge_ids,
        relevant_types
    )
    
    # Update edge_datas to only include filtered hyperedges
    edge_datas = [e for e in edge_datas if e["hyperedge"] in filtered_ids]
    
    logger.info(f"Entity filtering: {stats['reduction_rate']:.1f}% reduction")
```

## Performance Optimization

### Expected Performance Gains

| Scenario | Reduction Rate | Speed Improvement |
|----------|---------------|-------------------|
| Specific query (e.g., "medication for diabetes") | 50-70% | 2-3x faster |
| Broad query (e.g., "tell me about health") | 10-30% | 1.2-1.5x faster |
| Domain-specific query | 60-80% | 3-5x faster |

### Optimization Tips

1. **Define Precise Entity Types**: More specific types lead to better filtering
2. **Monitor Reduction Rates**: Aim for 30-70% reduction for optimal balance
3. **Use Batch Processing**: Automatically handled for large datasets
4. **Cache Entity Information**: Consider caching entity types for frequently accessed entities
5. **Combine with Quality Ranking**: Use filtering first, then quality ranking on reduced set

## Statistics and Metrics

The filter provides detailed statistics:

```python
filtered_ids, stats = await entity_filter.filter_hyperedges_by_type(
    hyperedge_ids,
    relevant_types
)

# Available statistics
stats = {
    "original_count": 100,        # Number of input hyperedges
    "filtered_count": 35,         # Number after filtering
    "reduction_rate": 65.0,       # Percentage reduction
    "types_used": ["disease", "medication"]  # Types that matched
}
```

## Error Handling

The filter handles various edge cases gracefully:

```python
# Empty hyperedge list
filtered_ids, stats = await entity_filter.filter_hyperedges_by_type([], types)
# Returns: ([], {original_count: 0, filtered_count: 0, ...})

# No matching types in query
relevant_types = await entity_filter.identify_relevant_types("random query")
# Returns: All types in domain (fallback behavior)

# Invalid domain
config = {"domain": "invalid_domain", ...}
entity_filter = EntityTypeFilter(graph, config)
# Automatically falls back to first available domain with warning
```

## Testing

Run the test suite:

```bash
python test_entity_filter.py
```

The test suite includes:
- Basic type identification
- Hyperedge filtering
- End-to-end query filtering
- Edge case handling
- Domain switching
- Performance metrics

## Examples

See `example_entity_filter_integration.py` for comprehensive examples:

```bash
python example_entity_filter_integration.py
```

Examples include:
1. Basic usage
2. Integration with query pipeline
3. Domain-specific filtering
4. Performance comparison
5. Configuration options
6. Best practices

## API Reference

### EntityTypeFilter

```python
class EntityTypeFilter:
    def __init__(
        self,
        graph: BaseGraphStorage,
        config: dict,
        llm_model_func: Optional[callable] = None
    )
```

#### Methods

##### `identify_relevant_types(query: str) -> list[str]`

Identify relevant entity types from a query.

**Parameters:**
- `query`: Query string

**Returns:**
- List of relevant entity type strings

**Example:**
```python
types = await filter.identify_relevant_types("What treats diabetes?")
# Returns: ['treatment', 'medication']
```

##### `filter_hyperedges_by_type(hyperedge_ids: list[str], relevant_types: list[str]) -> tuple[list[str], dict]`

Filter hyperedges by entity types.

**Parameters:**
- `hyperedge_ids`: List of hyperedge node IDs
- `relevant_types`: List of relevant entity types

**Returns:**
- Tuple of (filtered_ids, statistics_dict)

**Example:**
```python
filtered_ids, stats = await filter.filter_hyperedges_by_type(
    ["HE1", "HE2", "HE3"],
    ["disease", "medication"]
)
```

##### `get_domain_types(domain: Optional[str] = None) -> list[str]`

Get entity types for a domain.

**Parameters:**
- `domain`: Domain name (optional, uses current domain if None)

**Returns:**
- List of entity type strings

##### `set_domain(domain: str)`

Change the current domain.

**Parameters:**
- `domain`: New domain name

**Raises:**
- `ValueError`: If domain not in taxonomy

##### `add_entity_type(domain: str, entity_type: str)`

Add a new entity type to a domain.

**Parameters:**
- `domain`: Domain name
- `entity_type`: Entity type to add

## Best Practices

### 1. Choose Appropriate Entity Types

- Define types that are meaningful for your domain
- Balance between too broad (no filtering) and too narrow (miss results)
- Use 5-10 types per domain for optimal results

### 2. Combine with Quality-Aware Ranking

```python
# Step 1: Entity type filtering (reduce search space)
filtered_ids, stats = await entity_filter.filter_hyperedges_by_type(...)

# Step 2: Quality-aware ranking (rank filtered results)
ranked_results = await quality_ranker.rank_hyperedges(filtered_ids, ...)
```

### 3. Monitor Performance

```python
# Track reduction rates
logger.info(f"Reduction: {stats['reduction_rate']:.1f}%")

# Aim for 30-70% reduction
if stats['reduction_rate'] < 30:
    logger.warning("Low reduction rate - consider more specific types")
elif stats['reduction_rate'] > 80:
    logger.warning("High reduction rate - might miss relevant results")
```

### 4. Handle Domain Switching

```python
# For multi-domain applications
if "legal" in query.lower():
    entity_filter.set_domain("legal")
elif "medical" in query.lower():
    entity_filter.set_domain("medical")
```

### 5. Use Fallback Strategies

```python
# If filtering returns too few results, expand types
if len(filtered_ids) < min_results:
    # Use all types as fallback
    all_types = entity_filter.get_domain_types()
    filtered_ids, stats = await entity_filter.filter_hyperedges_by_type(
        hyperedge_ids,
        all_types
    )
```

## Troubleshooting

### Issue: No hyperedges after filtering

**Solution:** Query might be too specific or entity types too narrow
```python
# Check what types were identified
relevant_types = await entity_filter.identify_relevant_types(query)
print(f"Identified types: {relevant_types}")

# If empty or too specific, use broader types
if not relevant_types or len(filtered_ids) == 0:
    relevant_types = entity_filter.get_domain_types()
```

### Issue: Low reduction rate

**Solution:** Entity types might be too broad
```python
# Define more specific types
config["entity_taxonomy"]["medical"] = [
    "chronic_disease", "acute_disease",  # Instead of just "disease"
    "prescription_medication", "otc_medication"  # Instead of just "medication"
]
```

### Issue: Missing relevant results

**Solution:** Entity types might be too narrow
```python
# Expand entity types
entity_filter.add_entity_type("medical", "condition")
entity_filter.add_entity_type("medical", "diagnosis")
```

## Future Enhancements

Potential improvements for future versions:

1. **Hierarchical Entity Types**: Support parent-child relationships (e.g., "medication" → "prescription", "otc")
2. **Learning-Based Type Identification**: Train a model to identify types from queries
3. **Entity Type Index**: Build an inverted index for faster lookup
4. **Multi-Domain Queries**: Support queries spanning multiple domains
5. **Type Confidence Scores**: Assign confidence scores to identified types

## References

- Design Document: `.kiro/specs/dynhyperrag-quality-aware/design.md`
- Requirements: `.kiro/specs/dynhyperrag-quality-aware/requirements.md` (Requirement 3.1)
- Task List: `.kiro/specs/dynhyperrag-quality-aware/tasks.md` (Task 10)
- Test Suite: `test_entity_filter.py`
- Examples: `example_entity_filter_integration.py`

## Contributing

When extending the EntityTypeFilter:

1. Add new entity types to appropriate domains
2. Update tests to cover new functionality
3. Document new features in this README
4. Update examples with new use cases

## License

Part of the HyperGraphRAG project.
