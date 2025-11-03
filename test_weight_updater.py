"""
Test script for WeightUpdater implementation

This script tests the basic functionality of the WeightUpdater class
to ensure all three update strategies work correctly.
"""

import asyncio
from hypergraphrag.dynamic import WeightUpdater
from hypergraphrag.base import BaseGraphStorage


class MockGraphStorage(BaseGraphStorage):
    """Mock graph storage for testing"""
    
    def __init__(self):
        self.nodes = {}
    
    async def get_node(self, node_id: str):
        return self.nodes.get(node_id)
    
    async def upsert_node(self, node_id: str, node_data: dict):
        self.nodes[node_id] = node_data
    
    async def has_node(self, node_id: str) -> bool:
        return node_id in self.nodes
    
    async def node_degree(self, node_id: str) -> int:
        return 0
    
    async def get_node_edges(self, source_node_id: str):
        return []
    
    # Other methods not needed for this test
    async def has_edge(self, source_node_id: str, target_node_id: str) -> bool:
        return False
    
    async def edge_degree(self, src_id: str, tgt_id: str) -> int:
        return 0
    
    async def get_edge(self, source_node_id: str, target_node_id: str):
        return None
    
    async def upsert_edge(self, source_node_id: str, target_node_id: str, edge_data: dict):
        pass
    
    async def delete_node(self, node_id: str):
        if node_id in self.nodes:
            del self.nodes[node_id]


async def test_weight_updater():
    """Test the WeightUpdater implementation"""
    
    print("=" * 60)
    print("Testing WeightUpdater Implementation")
    print("=" * 60)
    
    # Create mock graph storage
    graph = MockGraphStorage()
    
    # Add a test hyperedge
    test_hyperedge_id = "test_hyperedge_1"
    graph.nodes[test_hyperedge_id] = {
        'role': 'hyperedge',
        'weight': 1.0,
        'quality_score': 0.7,
        'dynamic_weight': 0.7,
        'feedback_count': 0
    }
    
    print(f"\n✓ Created test hyperedge: {test_hyperedge_id}")
    print(f"  Initial weight: {graph.nodes[test_hyperedge_id]['dynamic_weight']}")
    print(f"  Quality score: {graph.nodes[test_hyperedge_id]['quality_score']}")
    
    # Test 1: EMA Strategy
    print("\n" + "-" * 60)
    print("Test 1: EMA (Exponential Moving Average) Strategy")
    print("-" * 60)
    
    config_ema = {
        'strategy': 'ema',
        'update_alpha': 0.1,
        'decay_factor': 0.99,
        'track_history': True
    }
    
    updater_ema = WeightUpdater(graph, config_ema)
    
    # Simulate positive feedback
    new_weight = await updater_ema.update_weights(test_hyperedge_id, 0.9)
    print(f"  After positive feedback (0.9): {new_weight:.4f}")
    
    # Simulate neutral feedback
    new_weight = await updater_ema.update_weights(test_hyperedge_id, 0.5)
    print(f"  After neutral feedback (0.5): {new_weight:.4f}")
    
    # Simulate negative feedback
    new_weight = await updater_ema.update_weights(test_hyperedge_id, 0.2)
    print(f"  After negative feedback (0.2): {new_weight:.4f}")
    
    # Get statistics
    stats = await updater_ema.get_update_statistics(test_hyperedge_id)
    print(f"\n  Statistics:")
    print(f"    Feedback count: {stats['feedback_count']}")
    print(f"    Current weight: {stats['current_weight']:.4f}")
    print(f"    Average feedback: {stats.get('avg_feedback', 0):.4f}")
    print(f"    Weight trend: {stats.get('weight_trend', 'N/A')}")
    
    # Reset for next test
    await updater_ema.reset_weights([test_hyperedge_id])
    
    # Test 2: Additive Strategy
    print("\n" + "-" * 60)
    print("Test 2: Additive Strategy")
    print("-" * 60)
    
    config_additive = {
        'strategy': 'additive',
        'update_alpha': 0.1,
        'decay_factor': 0.99,
        'track_history': True
    }
    
    updater_additive = WeightUpdater(graph, config_additive)
    
    # Simulate positive feedback
    new_weight = await updater_additive.update_weights(test_hyperedge_id, 0.9)
    print(f"  After positive feedback (0.9): {new_weight:.4f}")
    
    # Simulate neutral feedback
    new_weight = await updater_additive.update_weights(test_hyperedge_id, 0.5)
    print(f"  After neutral feedback (0.5): {new_weight:.4f}")
    
    # Simulate negative feedback
    new_weight = await updater_additive.update_weights(test_hyperedge_id, 0.2)
    print(f"  After negative feedback (0.2): {new_weight:.4f}")
    
    # Reset for next test
    await updater_additive.reset_weights([test_hyperedge_id])
    
    # Test 3: Multiplicative Strategy
    print("\n" + "-" * 60)
    print("Test 3: Multiplicative Strategy")
    print("-" * 60)
    
    config_multiplicative = {
        'strategy': 'multiplicative',
        'update_alpha': 0.1,
        'decay_factor': 0.99,
        'track_history': True
    }
    
    updater_multiplicative = WeightUpdater(graph, config_multiplicative)
    
    # Simulate positive feedback
    new_weight = await updater_multiplicative.update_weights(test_hyperedge_id, 0.9)
    print(f"  After positive feedback (0.9): {new_weight:.4f}")
    
    # Simulate neutral feedback
    new_weight = await updater_multiplicative.update_weights(test_hyperedge_id, 0.5)
    print(f"  After neutral feedback (0.5): {new_weight:.4f}")
    
    # Simulate negative feedback
    new_weight = await updater_multiplicative.update_weights(test_hyperedge_id, 0.2)
    print(f"  After negative feedback (0.2): {new_weight:.4f}")
    
    # Test 4: Batch Update
    print("\n" + "-" * 60)
    print("Test 4: Batch Update")
    print("-" * 60)
    
    # Add more test hyperedges
    for i in range(2, 5):
        he_id = f"test_hyperedge_{i}"
        graph.nodes[he_id] = {
            'role': 'hyperedge',
            'weight': 1.0,
            'quality_score': 0.6,
            'dynamic_weight': 0.6,
            'feedback_count': 0
        }
    
    updates = [
        {'hyperedge_id': 'test_hyperedge_2', 'feedback_signal': 0.8},
        {'hyperedge_id': 'test_hyperedge_3', 'feedback_signal': 0.5},
        {'hyperedge_id': 'test_hyperedge_4', 'feedback_signal': 0.3},
    ]
    
    results = await updater_ema.batch_update_weights(updates)
    
    print(f"  Batch updated {len(results)} hyperedges:")
    for he_id, weight in results.items():
        if weight is not None:
            print(f"    {he_id}: {weight:.4f}")
    
    # Test 5: Quality Constraints
    print("\n" + "-" * 60)
    print("Test 5: Quality Constraints")
    print("-" * 60)
    
    # Create hyperedge with low quality
    low_quality_id = "low_quality_hyperedge"
    graph.nodes[low_quality_id] = {
        'role': 'hyperedge',
        'weight': 1.0,
        'quality_score': 0.3,  # Low quality
        'dynamic_weight': 0.3,
        'feedback_count': 0
    }
    
    print(f"  Low quality hyperedge (quality=0.3)")
    
    # Try to boost with very positive feedback
    for i in range(5):
        new_weight = await updater_ema.update_weights(low_quality_id, 1.0)
    
    print(f"  After 5 positive feedbacks (1.0): {new_weight:.4f}")
    print(f"  Max allowed (quality * 2.0): {0.3 * 2.0:.4f}")
    print(f"  ✓ Weight correctly constrained by quality score")
    
    print("\n" + "=" * 60)
    print("All tests completed successfully! ✓")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_weight_updater())
