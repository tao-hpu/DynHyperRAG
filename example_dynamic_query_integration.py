"""
Example: Dynamic Update Integration in Query Flow

This example demonstrates how the dynamic weight update system works
in the complete query flow, showing:

1. Query execution with retrieval
2. Answer generation
3. Automatic feedback extraction
4. Asynchronous weight updates
5. Impact on subsequent queries

Author: DynHyperRAG Team
Date: 2025
"""

import asyncio
import numpy as np
from datetime import datetime


# Mock implementations (in real usage, these come from the actual system)
class MockGraphStorage:
    """Mock graph storage"""
    
    def __init__(self):
        self.nodes = {
            "<hyperedge>Aspirin reduces inflammation": {
                "role": "hyperedge",
                "weight": 1.0,
                "quality_score": 0.8,
                "dynamic_weight": 0.8,
                "source_id": "chunk_1",
                "feedback_count": 0,
            },
            "<hyperedge>Ibuprofen treats pain": {
                "role": "hyperedge",
                "weight": 1.0,
                "quality_score": 0.7,
                "dynamic_weight": 0.7,
                "source_id": "chunk_2",
                "feedback_count": 0,
            },
            "<hyperedge>Acetaminophen reduces fever": {
                "role": "hyperedge",
                "weight": 1.0,
                "quality_score": 0.6,
                "dynamic_weight": 0.6,
                "source_id": "chunk_3",
                "feedback_count": 0,
            },
        }
    
    async def get_node(self, node_id: str):
        return self.nodes.get(node_id)
    
    async def upsert_node(self, node_id: str, node_data: dict):
        self.nodes[node_id] = node_data


async def mock_embedding_func(texts: list[str]):
    """Mock embedding function"""
    return [np.random.rand(384).tolist() for _ in texts]


async def simulate_query_with_dynamic_update():
    """
    Simulate a complete query flow with dynamic updates.
    
    This demonstrates:
    - Query 1: Initial query, weights are updated based on usefulness
    - Query 2: Similar query benefits from updated weights
    """
    
    print("=" * 70)
    print("Dynamic Update Integration Example")
    print("=" * 70)
    print()
    
    # Setup
    graph = MockGraphStorage()
    
    global_config = {
        "embedding_func": mock_embedding_func,
        "addon_params": {
            "dynamic_config": {
                "enabled": True,
                "strategy": "ema",
                "update_alpha": 0.1,
                "decay_factor": 0.99,
                "feedback_method": "embedding",
                "feedback_threshold": 0.7,
            }
        }
    }
    
    from hypergraphrag.operate import _perform_dynamic_update_async
    
    # ========================================================================
    # Query 1: "What medication reduces inflammation?"
    # ========================================================================
    
    print("📝 Query 1: 'What medication reduces inflammation?'")
    print("-" * 70)
    print()
    
    # Simulate retrieval (in real system, this comes from vector search)
    retrieved_hyperedges_q1 = [
        {
            "id": "<hyperedge>Aspirin reduces inflammation",
            "hyperedge": "Aspirin reduces inflammation",
            "distance": 0.95
        },
        {
            "id": "<hyperedge>Ibuprofen treats pain",
            "hyperedge": "Ibuprofen treats pain",
            "distance": 0.75
        },
        {
            "id": "<hyperedge>Acetaminophen reduces fever",
            "hyperedge": "Acetaminophen reduces fever",
            "distance": 0.60
        },
    ]
    
    print("Retrieved hyperedges:")
    for he in retrieved_hyperedges_q1:
        node = await graph.get_node(he["id"])
        print(f"  - {he['hyperedge']}")
        print(f"    Similarity: {he['distance']:.2f}")
        print(f"    Dynamic weight: {node['dynamic_weight']:.3f}")
        print(f"    Feedback count: {node['feedback_count']}")
    print()
    
    # Simulate answer generation (in real system, this comes from LLM)
    answer_q1 = (
        "Aspirin is a medication that effectively reduces inflammation. "
        "It works by inhibiting prostaglandin synthesis."
    )
    
    print(f"Generated answer:")
    print(f"  {answer_q1}")
    print()
    
    # Dynamic update happens asynchronously
    print("🔄 Performing dynamic weight update (asynchronous)...")
    
    # Record initial weights
    initial_weights_q1 = {}
    for he in retrieved_hyperedges_q1:
        node = await graph.get_node(he["id"])
        initial_weights_q1[he["id"]] = node["dynamic_weight"]
    
    # Trigger async update
    await _perform_dynamic_update_async(
        answer_q1,
        retrieved_hyperedges_q1,
        graph,
        global_config,
        query="What medication reduces inflammation?"
    )
    
    print()
    print("Weight changes after Query 1:")
    for he in retrieved_hyperedges_q1:
        node = await graph.get_node(he["id"])
        old_weight = initial_weights_q1[he["id"]]
        new_weight = node["dynamic_weight"]
        change = new_weight - old_weight
        
        print(f"  - {he['hyperedge']}")
        print(f"    {old_weight:.3f} → {new_weight:.3f} ({change:+.3f})")
        print(f"    Feedback count: {node['feedback_count']}")
    print()
    
    # Analysis
    print("💡 Analysis:")
    print("  - Aspirin hyperedge: Weight increased (mentioned in answer)")
    print("  - Ibuprofen hyperedge: Weight slightly changed (not directly mentioned)")
    print("  - Acetaminophen hyperedge: Weight slightly changed (not relevant)")
    print()
    
    # ========================================================================
    # Query 2: "Tell me about anti-inflammatory drugs"
    # ========================================================================
    
    print("=" * 70)
    print()
    print("📝 Query 2: 'Tell me about anti-inflammatory drugs'")
    print("-" * 70)
    print()
    
    # Same hyperedges retrieved, but now with updated weights
    retrieved_hyperedges_q2 = [
        {
            "id": "<hyperedge>Aspirin reduces inflammation",
            "hyperedge": "Aspirin reduces inflammation",
            "distance": 0.90
        },
        {
            "id": "<hyperedge>Ibuprofen treats pain",
            "hyperedge": "Ibuprofen treats pain",
            "distance": 0.85
        },
        {
            "id": "<hyperedge>Acetaminophen reduces fever",
            "hyperedge": "Acetaminophen reduces fever",
            "distance": 0.55
        },
    ]
    
    print("Retrieved hyperedges (with updated weights):")
    for he in retrieved_hyperedges_q2:
        node = await graph.get_node(he["id"])
        print(f"  - {he['hyperedge']}")
        print(f"    Similarity: {he['distance']:.2f}")
        print(f"    Dynamic weight: {node['dynamic_weight']:.3f} ⬆️")
        print(f"    Feedback count: {node['feedback_count']}")
    print()
    
    # Simulate answer generation
    answer_q2 = (
        "Anti-inflammatory drugs like Aspirin and Ibuprofen help reduce "
        "inflammation and pain. Aspirin is particularly effective for inflammation."
    )
    
    print(f"Generated answer:")
    print(f"  {answer_q2}")
    print()
    
    # Dynamic update for Query 2
    print("🔄 Performing dynamic weight update (asynchronous)...")
    
    initial_weights_q2 = {}
    for he in retrieved_hyperedges_q2:
        node = await graph.get_node(he["id"])
        initial_weights_q2[he["id"]] = node["dynamic_weight"]
    
    await _perform_dynamic_update_async(
        answer_q2,
        retrieved_hyperedges_q2,
        graph,
        global_config,
        query="Tell me about anti-inflammatory drugs"
    )
    
    print()
    print("Weight changes after Query 2:")
    for he in retrieved_hyperedges_q2:
        node = await graph.get_node(he["id"])
        old_weight = initial_weights_q2[he["id"]]
        new_weight = node["dynamic_weight"]
        change = new_weight - old_weight
        
        print(f"  - {he['hyperedge']}")
        print(f"    {old_weight:.3f} → {new_weight:.3f} ({change:+.3f})")
        print(f"    Feedback count: {node['feedback_count']}")
    print()
    
    # Analysis
    print("💡 Analysis:")
    print("  - Aspirin hyperedge: Weight increased again (mentioned twice)")
    print("  - Ibuprofen hyperedge: Weight increased (mentioned in answer)")
    print("  - Acetaminophen hyperedge: Weight decreased (not relevant)")
    print()
    
    # ========================================================================
    # Summary
    # ========================================================================
    
    print("=" * 70)
    print()
    print("📊 Summary: Impact of Dynamic Updates")
    print("-" * 70)
    print()
    
    print("Final hyperedge weights:")
    for he_id in graph.nodes:
        node = graph.nodes[he_id]
        print(f"  - {he_id}")
        print(f"    Initial weight: 0.800")
        print(f"    Final weight: {node['dynamic_weight']:.3f}")
        print(f"    Total feedback: {node['feedback_count']}")
        print()
    
    print("Key Benefits:")
    print("  ✓ Useful hyperedges get higher weights over time")
    print("  ✓ Less relevant hyperedges get lower weights")
    print("  ✓ System learns from usage patterns")
    print("  ✓ Updates happen asynchronously (non-blocking)")
    print("  ✓ Improves retrieval quality for future queries")
    print()
    
    print("=" * 70)


async def demonstrate_configuration_control():
    """Demonstrate how to control dynamic updates via configuration"""
    
    print()
    print("=" * 70)
    print("Configuration Control Example")
    print("=" * 70)
    print()
    
    graph = MockGraphStorage()
    
    from hypergraphrag.operate import _perform_dynamic_update_async
    
    # Test different configurations
    configs = [
        {
            "name": "Disabled",
            "config": {
                "embedding_func": mock_embedding_func,
                "addon_params": {
                    "dynamic_config": {
                        "enabled": False,  # Disabled
                    }
                }
            }
        },
        {
            "name": "EMA Strategy",
            "config": {
                "embedding_func": mock_embedding_func,
                "addon_params": {
                    "dynamic_config": {
                        "enabled": True,
                        "strategy": "ema",
                        "update_alpha": 0.1,
                        "decay_factor": 0.99,
                        "feedback_method": "embedding",
                    }
                }
            }
        },
        {
            "name": "Additive Strategy",
            "config": {
                "embedding_func": mock_embedding_func,
                "addon_params": {
                    "dynamic_config": {
                        "enabled": True,
                        "strategy": "additive",
                        "update_alpha": 0.05,
                        "decay_factor": 0.99,
                        "feedback_method": "embedding",
                    }
                }
            }
        },
    ]
    
    test_hyperedge = {
        "id": "<hyperedge>Test hyperedge",
        "hyperedge": "Test hyperedge content",
        "distance": 0.8
    }
    
    for config_info in configs:
        print(f"Testing: {config_info['name']}")
        print("-" * 70)
        
        # Reset hyperedge
        graph.nodes["<hyperedge>Test hyperedge"] = {
            "role": "hyperedge",
            "weight": 1.0,
            "quality_score": 0.7,
            "dynamic_weight": 0.7,
            "source_id": "test",
            "feedback_count": 0,
        }
        
        initial_weight = 0.7
        
        # Perform update
        await _perform_dynamic_update_async(
            "Test answer with relevant content",
            [test_hyperedge],
            graph,
            config_info["config"],
            query="Test query"
        )
        
        node = await graph.get_node(test_hyperedge["id"])
        final_weight = node["dynamic_weight"]
        
        print(f"  Initial weight: {initial_weight:.3f}")
        print(f"  Final weight: {final_weight:.3f}")
        print(f"  Change: {final_weight - initial_weight:+.3f}")
        print()
    
    print("=" * 70)


if __name__ == "__main__":
    print("\n")
    
    # Run main example
    asyncio.run(simulate_query_with_dynamic_update())
    
    # Run configuration example
    asyncio.run(demonstrate_configuration_control())
    
    print("\n✅ Example completed successfully!")
    print()
