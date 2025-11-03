"""
Example: Entity Type Filter Integration

This example demonstrates how to integrate EntityTypeFilter into the
HyperGraphRAG query pipeline for efficient retrieval.

The entity type filter reduces search space by:
1. Identifying relevant entity types from the query
2. Filtering hyperedges to only those connecting relevant entity types
3. Reducing computational cost and improving retrieval speed

Usage:
    python example_entity_filter_integration.py
"""

import asyncio
import logging
from hypergraphrag.retrieval.entity_filter import EntityTypeFilter
from config import get_config

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def example_basic_usage():
    """Example 1: Basic entity type filtering"""
    
    print("\n" + "=" * 70)
    print("Example 1: Basic Entity Type Filtering")
    print("=" * 70)
    
    # Load configuration
    config = get_config()
    retrieval_config = config.get_retrieval_config()
    
    print(f"\nConfiguration:")
    print(f"  Domain: {retrieval_config['domain']}")
    print(f"  Entity Types: {retrieval_config['entity_taxonomy'][retrieval_config['domain']]}")
    
    # Note: In real usage, you would have a graph instance
    # For this example, we'll show the API usage
    
    print("\nStep 1: Initialize EntityTypeFilter")
    print("  filter = EntityTypeFilter(graph, retrieval_config)")
    
    print("\nStep 2: Identify relevant types from query")
    example_query = "What medication treats diabetes?"
    print(f"  Query: '{example_query}'")
    print("  relevant_types = await filter.identify_relevant_types(query)")
    print("  Expected: ['medication', 'treatment'] or similar")
    
    print("\nStep 3: Filter hyperedges by type")
    print("  filtered_ids, stats = await filter.filter_hyperedges_by_type(")
    print("      hyperedge_ids, relevant_types")
    print("  )")
    print("  Result: Reduced list of hyperedges + statistics")


async def example_integration_with_query():
    """Example 2: Integration with query pipeline"""
    
    print("\n" + "=" * 70)
    print("Example 2: Integration with Query Pipeline")
    print("=" * 70)
    
    print("\nIntegration Pattern:")
    print("""
    async def enhanced_query(query: str, graph, vdb, config):
        # 1. Initialize entity filter
        entity_filter = EntityTypeFilter(graph, config)
        
        # 2. Perform initial vector retrieval
        initial_results = await vdb.query(query, top_k=100)
        hyperedge_ids = [r['hyperedge_name'] for r in initial_results]
        
        # 3. Apply entity type filtering
        relevant_types = await entity_filter.identify_relevant_types(query)
        filtered_ids, stats = await entity_filter.filter_hyperedges_by_type(
            hyperedge_ids, relevant_types
        )
        
        print(f"Search space reduced by {stats['reduction_rate']:.1f}%")
        print(f"Processing {len(filtered_ids)} instead of {len(hyperedge_ids)} hyperedges")
        
        # 4. Continue with quality-aware ranking on filtered results
        # ... (quality ranking logic)
        
        return filtered_ids
    """)


async def example_domain_specific():
    """Example 3: Domain-specific filtering"""
    
    print("\n" + "=" * 70)
    print("Example 3: Domain-Specific Entity Type Filtering")
    print("=" * 70)
    
    domains = {
        "medical": {
            "types": ["disease", "symptom", "treatment", "medication", "procedure"],
            "query": "What are the symptoms of diabetes?",
            "expected_types": ["symptom", "disease"]
        },
        "legal": {
            "types": ["law", "article", "court", "party", "crime", "penalty"],
            "query": "What is the penalty for theft?",
            "expected_types": ["crime", "penalty"]
        },
        "academic": {
            "types": ["paper", "author", "institution", "keyword", "conference"],
            "query": "Which papers did John Smith publish?",
            "expected_types": ["paper", "author"]
        }
    }
    
    for domain, info in domains.items():
        print(f"\n{domain.upper()} Domain:")
        print(f"  Entity Types: {info['types']}")
        print(f"  Example Query: '{info['query']}'")
        print(f"  Expected Types: {info['expected_types']}")


async def example_performance_comparison():
    """Example 4: Performance comparison"""
    
    print("\n" + "=" * 70)
    print("Example 4: Performance Impact")
    print("=" * 70)
    
    print("\nScenario: 1000 hyperedges in knowledge graph")
    print("\nWithout Entity Type Filtering:")
    print("  - Process all 1000 hyperedges")
    print("  - Compute quality scores for 1000 hyperedges")
    print("  - Rank 1000 hyperedges")
    print("  - Time: ~5.0 seconds")
    
    print("\nWith Entity Type Filtering (50% reduction):")
    print("  - Filter to 500 relevant hyperedges")
    print("  - Compute quality scores for 500 hyperedges")
    print("  - Rank 500 hyperedges")
    print("  - Time: ~2.5 seconds (50% faster)")
    
    print("\nWith Entity Type Filtering (70% reduction):")
    print("  - Filter to 300 relevant hyperedges")
    print("  - Compute quality scores for 300 hyperedges")
    print("  - Rank 300 hyperedges")
    print("  - Time: ~1.5 seconds (70% faster)")
    
    print("\nKey Benefits:")
    print("  ✓ Reduced computational cost")
    print("  ✓ Faster query response time")
    print("  ✓ Lower memory usage")
    print("  ✓ Maintained or improved accuracy (by focusing on relevant types)")


async def example_configuration():
    """Example 5: Configuration options"""
    
    print("\n" + "=" * 70)
    print("Example 5: Configuration Options")
    print("=" * 70)
    
    print("\nBasic Configuration:")
    print("""
    config = {
        "domain": "medical",
        "entity_taxonomy": {
            "medical": ["disease", "symptom", "medication"]
        }
    }
    filter = EntityTypeFilter(graph, config)
    """)
    
    print("\nAdvanced Configuration with LLM:")
    print("""
    config = {
        "domain": "legal",
        "entity_taxonomy": {
            "legal": ["law", "article", "court", "crime"]
        },
        "use_llm_classification": True  # Enable LLM-based type identification
    }
    filter = EntityTypeFilter(graph, config, llm_model_func=llm_func)
    """)
    
    print("\nEnvironment Variables (.env):")
    print("""
    # Enable entity filtering
    DYNHYPERRAG_ENTITY_FILTER_ENABLED=true
    
    # Set domain
    RETRIEVAL_DOMAIN=medical
    
    # Custom entity types (comma-separated)
    ENTITY_TYPES_MEDICAL=disease,symptom,treatment,medication,procedure
    ENTITY_TYPES_LEGAL=law,article,court,party,crime,penalty
    """)


async def example_best_practices():
    """Example 6: Best practices"""
    
    print("\n" + "=" * 70)
    print("Example 6: Best Practices")
    print("=" * 70)
    
    print("\n1. Choose Appropriate Entity Types:")
    print("   - Define types that are meaningful for your domain")
    print("   - Balance between too broad (no filtering) and too narrow (miss results)")
    print("   - Example: For medical domain, use 'disease', 'symptom', 'treatment'")
    
    print("\n2. Combine with Quality-Aware Ranking:")
    print("   - Use entity filtering to reduce search space")
    print("   - Then apply quality-aware ranking on filtered results")
    print("   - This gives both speed and accuracy improvements")
    
    print("\n3. Monitor Reduction Rates:")
    print("   - Track the reduction_rate statistic")
    print("   - Aim for 30-70% reduction for optimal balance")
    print("   - Too high reduction might miss relevant results")
    
    print("\n4. Handle Edge Cases:")
    print("   - Queries with no matching types → fallback to all types")
    print("   - Empty result sets → expand entity types")
    print("   - Domain mismatch → use appropriate taxonomy")
    
    print("\n5. Performance Optimization:")
    print("   - Use batch processing for large hyperedge sets")
    print("   - Cache entity type information")
    print("   - Consider building entity type index for faster lookup")


async def main():
    """Run all examples"""
    
    print("\n" + "🔍" * 35)
    print("Entity Type Filter Integration Examples")
    print("🔍" * 35)
    
    await example_basic_usage()
    await example_integration_with_query()
    await example_domain_specific()
    await example_performance_comparison()
    await example_configuration()
    await example_best_practices()
    
    print("\n" + "=" * 70)
    print("Summary")
    print("=" * 70)
    print("\nEntityTypeFilter provides:")
    print("  ✓ Efficient search space reduction")
    print("  ✓ Domain-specific entity type taxonomies")
    print("  ✓ Keyword-based and LLM-based type identification")
    print("  ✓ Easy integration with existing query pipeline")
    print("  ✓ Performance metrics and statistics")
    
    print("\nNext Steps:")
    print("  1. Configure entity types for your domain")
    print("  2. Integrate into query pipeline (see operate.py)")
    print("  3. Combine with QualityAwareRanker (Task 11)")
    print("  4. Monitor performance improvements")
    
    print("\n" + "🎉" * 35)


if __name__ == "__main__":
    asyncio.run(main())
