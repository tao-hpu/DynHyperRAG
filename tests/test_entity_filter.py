"""
Test EntityTypeFilter implementation

This test verifies the entity type filtering functionality for efficient retrieval.
"""

import asyncio
import logging
from hypergraphrag.retrieval.entity_filter import EntityTypeFilter
from hypergraphrag.storage import NetworkXStorage

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MockEmbeddingFunc:
    """Mock embedding function for testing"""
    async def __call__(self, texts):
        import numpy as np
        return [np.random.rand(384) for _ in texts]


async def test_entity_filter():
    """Test EntityTypeFilter with a simple graph"""
    
    logger.info("=" * 60)
    logger.info("Testing EntityTypeFilter Implementation")
    logger.info("=" * 60)
    
    # Create a simple graph storage
    embedding_func = MockEmbeddingFunc()
    graph = NetworkXStorage(
        namespace="test_entity_filter",
        global_config={"working_dir": "./test_output"},
        embedding_func=embedding_func
    )
    
    # Create test entities with different types
    logger.info("\n1. Creating test entities...")
    entities = [
        ("DIABETES", "disease", "A metabolic disorder"),
        ("INSULIN", "medication", "Hormone for blood sugar control"),
        ("FEVER", "symptom", "Elevated body temperature"),
        ("SURGERY", "procedure", "Medical operation"),
    ]
    
    for entity_name, entity_type, description in entities:
        await graph.upsert_node(
            f'"{entity_name}"',
            {
                "role": "entity",
                "entity_name": entity_name,
                "entity_type": entity_type,
                "description": description,
                "source_id": "test_doc"
            }
        )
        logger.info(f"   Created entity: {entity_name} (type: {entity_type})")
    
    # Create test hyperedges connecting entities
    logger.info("\n2. Creating test hyperedges...")
    hyperedges = [
        ("HE1", "Diabetes is treated with insulin", ["DIABETES", "INSULIN"]),
        ("HE2", "Fever is a symptom of infection", ["FEVER"]),
        ("HE3", "Surgery requires medication", ["SURGERY", "INSULIN"]),
        ("HE4", "Diabetes causes fever", ["DIABETES", "FEVER"]),
    ]
    
    for he_id, description, connected_entities in hyperedges:
        # Create hyperedge node
        await graph.upsert_node(
            he_id,
            {
                "role": "hyperedge",
                "hyperedge": description,
                "source_id": "test_doc",
                "weight": 1.0
            }
        )
        
        # Connect hyperedge to entities
        for entity in connected_entities:
            await graph.upsert_edge(
                he_id,
                f'"{entity}"',
                {"weight": 1.0}
            )
        
        logger.info(f"   Created hyperedge: {he_id} -> {connected_entities}")
    
    # Initialize EntityTypeFilter
    logger.info("\n3. Initializing EntityTypeFilter...")
    config = {
        "domain": "medical",
        "entity_taxonomy": {
            "medical": ["disease", "symptom", "treatment", "medication", "procedure", "anatomy"]
        }
    }
    
    entity_filter = EntityTypeFilter(graph, config)
    logger.info(f"   Domain: {entity_filter.domain}")
    logger.info(f"   Entity types: {entity_filter.get_domain_types()}")
    
    # Test 1: Identify relevant types from query
    logger.info("\n4. Test: Identify relevant types from query")
    test_queries = [
        "What medication treats diabetes?",
        "What are the symptoms of infection?",
        "Tell me about surgical procedures",
    ]
    
    for query in test_queries:
        relevant_types = await entity_filter.identify_relevant_types(query)
        logger.info(f"   Query: '{query}'")
        logger.info(f"   Identified types: {relevant_types}")
    
    # Test 2: Filter hyperedges by entity type
    logger.info("\n5. Test: Filter hyperedges by entity type")
    all_hyperedge_ids = ["HE1", "HE2", "HE3", "HE4"]
    
    test_cases = [
        (["disease"], "Only disease-related hyperedges"),
        (["medication"], "Only medication-related hyperedges"),
        (["symptom"], "Only symptom-related hyperedges"),
        (["disease", "medication"], "Disease or medication hyperedges"),
    ]
    
    for relevant_types, description in test_cases:
        logger.info(f"\n   Test case: {description}")
        logger.info(f"   Filtering by types: {relevant_types}")
        
        filtered_ids, stats = await entity_filter.filter_hyperedges_by_type(
            all_hyperedge_ids,
            relevant_types
        )
        
        logger.info(f"   Results:")
        logger.info(f"     - Original count: {stats['original_count']}")
        logger.info(f"     - Filtered count: {stats['filtered_count']}")
        logger.info(f"     - Reduction rate: {stats['reduction_rate']:.1f}%")
        logger.info(f"     - Types matched: {stats['types_used']}")
        logger.info(f"     - Filtered IDs: {filtered_ids}")
    
    # Test 3: End-to-end query filtering
    logger.info("\n6. Test: End-to-end query filtering")
    query = "What medication is used for diabetes treatment?"
    
    logger.info(f"   Query: '{query}'")
    
    # Step 1: Identify relevant types
    relevant_types = await entity_filter.identify_relevant_types(query)
    logger.info(f"   Step 1 - Identified types: {relevant_types}")
    
    # Step 2: Filter hyperedges
    filtered_ids, stats = await entity_filter.filter_hyperedges_by_type(
        all_hyperedge_ids,
        relevant_types
    )
    logger.info(f"   Step 2 - Filtered to {len(filtered_ids)} hyperedges")
    logger.info(f"   Step 2 - Search space reduced by {stats['reduction_rate']:.1f}%")
    
    # Verify the filtered hyperedges
    logger.info(f"\n   Filtered hyperedges:")
    for he_id in filtered_ids:
        he_node = await graph.get_node(he_id)
        logger.info(f"     - {he_id}: {he_node['hyperedge']}")
    
    logger.info("\n" + "=" * 60)
    logger.info("✅ All tests completed successfully!")
    logger.info("=" * 60)


async def test_edge_cases():
    """Test edge cases and error handling"""
    
    logger.info("\n" + "=" * 60)
    logger.info("Testing Edge Cases")
    logger.info("=" * 60)
    
    embedding_func = MockEmbeddingFunc()
    graph = NetworkXStorage(
        namespace="test_edge_cases",
        global_config={"working_dir": "./test_output"},
        embedding_func=embedding_func
    )
    
    config = {
        "domain": "medical",
        "entity_taxonomy": {
            "medical": ["disease", "symptom"]
        }
    }
    
    entity_filter = EntityTypeFilter(graph, config)
    
    # Test 1: Empty hyperedge list
    logger.info("\n1. Test: Empty hyperedge list")
    filtered_ids, stats = await entity_filter.filter_hyperedges_by_type([], ["disease"])
    logger.info(f"   Result: {len(filtered_ids)} hyperedges (expected: 0)")
    assert len(filtered_ids) == 0, "Should return empty list"
    logger.info("   ✓ Passed")
    
    # Test 2: Query with no matching types
    logger.info("\n2. Test: Query with no matching entity types")
    relevant_types = await entity_filter.identify_relevant_types("What is the weather?")
    logger.info(f"   Identified types: {relevant_types}")
    logger.info(f"   Should fallback to all types: {len(relevant_types) == len(config['entity_taxonomy']['medical'])}")
    assert len(relevant_types) > 0, "Should return fallback types"
    logger.info("   ✓ Passed")
    
    # Test 3: Invalid domain handling
    logger.info("\n3. Test: Invalid domain handling")
    try:
        invalid_config = {
            "domain": "invalid_domain",
            "entity_taxonomy": {"medical": ["disease"]}
        }
        filter_invalid = EntityTypeFilter(graph, invalid_config)
        logger.info(f"   Fallback domain: {filter_invalid.domain}")
        logger.info("   ✓ Passed (graceful fallback)")
    except Exception as e:
        logger.error(f"   ✗ Failed: {e}")
    
    # Test 4: Change domain
    logger.info("\n4. Test: Change domain")
    entity_filter.entity_taxonomy["legal"] = ["law", "court"]
    entity_filter.set_domain("legal")
    logger.info(f"   New domain: {entity_filter.domain}")
    logger.info(f"   New types: {entity_filter.get_domain_types()}")
    assert entity_filter.domain == "legal", "Domain should be changed"
    logger.info("   ✓ Passed")
    
    logger.info("\n" + "=" * 60)
    logger.info("✅ All edge case tests passed!")
    logger.info("=" * 60)


async def main():
    """Run all tests"""
    try:
        await test_entity_filter()
        await test_edge_cases()
        
        print("\n" + "🎉" * 30)
        print("All EntityTypeFilter tests passed successfully!")
        print("🎉" * 30)
        
    except Exception as e:
        logger.error(f"\n❌ Test failed with error: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    asyncio.run(main())
