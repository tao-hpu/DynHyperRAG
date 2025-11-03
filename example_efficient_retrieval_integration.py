"""
Example: Efficient Retrieval Integration in Query Flow

This example demonstrates how to use the integrated efficient retrieval features
in the DynHyperRAG query flow, including:
- Entity type filtering
- Quality-aware ranking
- Lite retriever mode

The integration is automatic when the appropriate configuration is enabled.
"""

import asyncio
import os
from hypergraphrag import HyperGraphRAG
from hypergraphrag.operate import kg_query
from hypergraphrag.base import QueryParam


async def example_efficient_retrieval():
    """
    Example of using efficient retrieval in query flow.
    
    The efficient retrieval features are automatically integrated into the
    query flow when enabled in the configuration.
    """
    
    # Configuration with efficient retrieval enabled
    config = {
        "working_dir": "./expr/example",
        "embedding_func": None,  # Will use default
        "llm_model_func": None,  # Will use default
        
        # Enable efficient retrieval features
        "addon_params": {
            # Entity type filtering configuration
            "retrieval_config": {
                "entity_filter_enabled": True,  # Enable entity type filtering
                "domain": "medical",  # Domain for entity taxonomy
                "entity_taxonomy": {
                    "medical": ["disease", "symptom", "treatment", "medication", "procedure", "anatomy"],
                    "legal": ["law", "article", "court", "party", "crime", "penalty"],
                    "academic": ["paper", "author", "institution", "keyword", "conference"]
                },
                # Quality-aware ranking weights
                "similarity_weight": 0.5,  # α: weight for semantic similarity
                "quality_weight": 0.3,     # β: weight for quality score
                "dynamic_weight": 0.2,     # γ: weight for dynamic weight
            },
            
            # Lite mode configuration (optional)
            "lite_config": {
                "enabled": False,  # Set to True for lite mode
                "cache_size": 1000,
            },
        }
    }
    
    # Initialize HyperGraphRAG
    rag = HyperGraphRAG(
        working_dir=config["working_dir"],
        enable_llm_cache=True
    )
    
    # Example queries
    queries = [
        "What are the symptoms of diabetes?",
        "How is hypertension treated?",
        "What medications are used for asthma?"
    ]
    
    print("=" * 80)
    print("Efficient Retrieval Integration Example")
    print("=" * 80)
    print()
    
    for i, query in enumerate(queries, 1):
        print(f"\n{'='*80}")
        print(f"Query {i}: {query}")
        print(f"{'='*80}\n")
        
        # Query with efficient retrieval
        # The integration happens automatically in kg_query
        result = await rag.aquery(
            query,
            param=QueryParam(
                mode="hybrid",
                top_k=10,
                max_token_for_text_unit=4000,
                max_token_for_global_context=4000,
                max_token_for_local_context=4000,
            )
        )
        
        print(f"Result:\n{result}\n")
        print("-" * 80)


async def example_lite_mode():
    """
    Example of using lite retriever mode for faster retrieval.
    
    Lite mode uses simplified quality features and caching for
    improved performance in resource-constrained environments.
    """
    
    config = {
        "working_dir": "./expr/example",
        "addon_params": {
            "retrieval_config": {
                "entity_filter_enabled": False,  # Disable filtering in lite mode
                "similarity_weight": 0.7,
                "quality_weight": 0.3,
                "dynamic_weight": 0.0,
            },
            "lite_config": {
                "enabled": True,  # Enable lite mode
                "cache_size": 1000,
                "use_simple_quality": True,
            },
        }
    }
    
    rag = HyperGraphRAG(
        working_dir=config["working_dir"],
        enable_llm_cache=True
    )
    
    print("\n" + "=" * 80)
    print("Lite Mode Example")
    print("=" * 80)
    print()
    
    query = "What are the symptoms of diabetes?"
    print(f"Query: {query}\n")
    
    result = await rag.aquery(
        query,
        param=QueryParam(mode="hybrid", top_k=10)
    )
    
    print(f"Result:\n{result}\n")


async def example_entity_filtering_only():
    """
    Example of using only entity type filtering without quality ranking.
    
    This is useful when you want to reduce search space but don't need
    the overhead of quality-aware ranking.
    """
    
    config = {
        "working_dir": "./expr/example",
        "addon_params": {
            "retrieval_config": {
                "entity_filter_enabled": True,
                "domain": "medical",
                "entity_taxonomy": {
                    "medical": ["disease", "symptom", "treatment", "medication"]
                },
                # Use standard ranking (no quality weighting)
                "similarity_weight": 1.0,
                "quality_weight": 0.0,
                "dynamic_weight": 0.0,
            },
        }
    }
    
    rag = HyperGraphRAG(
        working_dir=config["working_dir"],
        enable_llm_cache=True
    )
    
    print("\n" + "=" * 80)
    print("Entity Filtering Only Example")
    print("=" * 80)
    print()
    
    query = "What medications treat high blood pressure?"
    print(f"Query: {query}\n")
    
    result = await rag.aquery(
        query,
        param=QueryParam(mode="hybrid", top_k=10)
    )
    
    print(f"Result:\n{result}\n")


async def example_quality_ranking_only():
    """
    Example of using only quality-aware ranking without entity filtering.
    
    This is useful when you want to prioritize high-quality hyperedges
    but don't need entity type filtering.
    """
    
    config = {
        "working_dir": "./expr/example",
        "addon_params": {
            "retrieval_config": {
                "entity_filter_enabled": False,  # Disable filtering
                # Quality-aware ranking weights
                "similarity_weight": 0.4,
                "quality_weight": 0.4,
                "dynamic_weight": 0.2,
            },
        }
    }
    
    rag = HyperGraphRAG(
        working_dir=config["working_dir"],
        enable_llm_cache=True
    )
    
    print("\n" + "=" * 80)
    print("Quality Ranking Only Example")
    print("=" * 80)
    print()
    
    query = "What are the risk factors for heart disease?"
    print(f"Query: {query}\n")
    
    result = await rag.aquery(
        query,
        param=QueryParam(mode="hybrid", top_k=10)
    )
    
    print(f"Result:\n{result}\n")


async def compare_modes():
    """
    Compare different retrieval modes to see the impact of efficient retrieval.
    """
    
    query = "What are the symptoms of diabetes?"
    
    modes = [
        ("Standard", {"entity_filter_enabled": False, "similarity_weight": 1.0, "quality_weight": 0.0, "dynamic_weight": 0.0}),
        ("Entity Filter", {"entity_filter_enabled": True, "similarity_weight": 1.0, "quality_weight": 0.0, "dynamic_weight": 0.0}),
        ("Quality Ranking", {"entity_filter_enabled": False, "similarity_weight": 0.5, "quality_weight": 0.3, "dynamic_weight": 0.2}),
        ("Full Efficient", {"entity_filter_enabled": True, "similarity_weight": 0.5, "quality_weight": 0.3, "dynamic_weight": 0.2}),
    ]
    
    print("\n" + "=" * 80)
    print("Mode Comparison")
    print("=" * 80)
    print(f"\nQuery: {query}\n")
    
    for mode_name, retrieval_config in modes:
        print(f"\n{'-'*80}")
        print(f"Mode: {mode_name}")
        print(f"{'-'*80}")
        
        config = {
            "working_dir": "./expr/example",
            "addon_params": {
                "retrieval_config": {
                    "domain": "medical",
                    **retrieval_config
                },
            }
        }
        
        rag = HyperGraphRAG(
            working_dir=config["working_dir"],
            enable_llm_cache=True
        )
        
        import time
        start = time.time()
        result = await rag.aquery(query, param=QueryParam(mode="hybrid", top_k=10))
        elapsed = time.time() - start
        
        print(f"Time: {elapsed:.3f}s")
        print(f"Result length: {len(result)} characters")
        print(f"Preview: {result[:200]}...")


if __name__ == "__main__":
    print("""
    ╔══════════════════════════════════════════════════════════════════════════════╗
    ║                  Efficient Retrieval Integration Example                     ║
    ║                                                                              ║
    ║  This example demonstrates the integrated efficient retrieval features:     ║
    ║  - Entity type filtering (Task 10)                                          ║
    ║  - Quality-aware ranking (Task 11)                                          ║
    ║  - Lite retriever mode (Task 12)                                            ║
    ║                                                                              ║
    ║  The integration is automatic when enabled in configuration.                ║
    ╚══════════════════════════════════════════════════════════════════════════════╝
    """)
    
    # Run examples
    asyncio.run(example_efficient_retrieval())
    # asyncio.run(example_lite_mode())
    # asyncio.run(example_entity_filtering_only())
    # asyncio.run(example_quality_ranking_only())
    # asyncio.run(compare_modes())
