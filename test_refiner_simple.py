"""
Simple test for HyperedgeRefiner - Quick verification
"""

import asyncio

# Mock graph storage
class MockGraphStorage:
    def __init__(self):
        self.nodes = {}
        self.namespace = "test"
        self.global_config = {}
    
    async def get_node(self, node_id: str):
        return self.nodes.get(node_id)
    
    async def upsert_node(self, node_id: str, node_data: dict):
        self.nodes[node_id] = node_data
    
    async def delete_node(self, node_id: str):
        if node_id in self.nodes:
            del self.nodes[node_id]
    
    async def has_node(self, node_id: str) -> bool:
        return node_id in self.nodes


async def test_basic():
    print("Testing HyperedgeRefiner basic functionality...")
    
    # Setup
    graph = MockGraphStorage()
    
    # Add test hyperedges
    graph.nodes['he1'] = {'role': 'hyperedge', 'quality_score': 0.8, 'weight': 1.0, 'dynamic_weight': 1.0}
    graph.nodes['he2'] = {'role': 'hyperedge', 'quality_score': 0.3, 'weight': 1.0, 'dynamic_weight': 1.0}
    graph.nodes['he3'] = {'role': 'hyperedge', 'quality_score': 0.6, 'weight': 1.0, 'dynamic_weight': 1.0}
    
    print(f"Created 3 test hyperedges")
    
    # Import and test
    from hypergraphrag.dynamic.refiner import HyperedgeRefiner
    
    # Test 1: Soft filtering
    print("\n1. Testing soft filtering...")
    config = {
        'quality_threshold': 0.5,
        'filter_mode': 'soft',
        'threshold_strategy': 'fixed',
    }
    refiner = HyperedgeRefiner(graph, config)
    
    result = await refiner.filter_low_quality(['he1', 'he2', 'he3'])
    
    print(f"   Filtered: {result['filtered']}")
    print(f"   Kept: {result['kept']}")
    print(f"   Filter rate: {result['filter_rate']:.1%}")
    
    assert 'he2' in result['filtered'], "he2 should be filtered (quality 0.3 < 0.5)"
    assert 'he1' in result['kept'], "he1 should be kept (quality 0.8 >= 0.5)"
    assert 'he3' in result['kept'], "he3 should be kept (quality 0.6 >= 0.5)"
    
    # Check soft filtering effect
    node2 = await graph.get_node('he2')
    assert node2['dynamic_weight'] < 1.0, "he2 weight should be reduced"
    assert node2.get('filtered') == True, "he2 should be marked as filtered"
    
    print("   ✓ Soft filtering works correctly")
    
    # Test 2: Hard filtering
    print("\n2. Testing hard filtering...")
    graph.nodes['he4'] = {'role': 'hyperedge', 'quality_score': 0.2, 'weight': 1.0, 'dynamic_weight': 1.0}
    
    config_hard = {
        'quality_threshold': 0.5,
        'filter_mode': 'hard',
        'threshold_strategy': 'fixed',
    }
    refiner_hard = HyperedgeRefiner(graph, config_hard)
    
    result = await refiner_hard.filter_low_quality(['he4'])
    
    print(f"   Filtered: {result['filtered']}")
    
    exists = await graph.has_node('he4')
    assert not exists, "he4 should be deleted"
    
    print("   ✓ Hard filtering works correctly")
    
    # Test 3: Percentile threshold
    print("\n3. Testing percentile threshold...")
    
    # Add more hyperedges
    for i in range(10):
        quality = 0.1 * (i + 1)  # 0.1, 0.2, ..., 1.0
        graph.nodes[f'he_p{i}'] = {
            'role': 'hyperedge',
            'quality_score': quality,
            'weight': 1.0,
            'dynamic_weight': 1.0
        }
    
    config_percentile = {
        'filter_mode': 'soft',
        'threshold_strategy': 'percentile',
        'percentile': 30,  # Bottom 30%
    }
    refiner_percentile = HyperedgeRefiner(graph, config_percentile)
    
    he_ids = [f'he_p{i}' for i in range(10)]
    result = await refiner_percentile.filter_low_quality(he_ids)
    
    print(f"   Filtered: {len(result['filtered'])} hyperedges")
    print(f"   Filter rate: {result['filter_rate']:.1%}")
    print(f"   Threshold: {result['threshold_used']:.3f}")
    
    # Should filter approximately 30%
    assert 2 <= len(result['filtered']) <= 4, "Should filter ~30% (3 out of 10)"
    
    print("   ✓ Percentile threshold works correctly")
    
    # Test 4: Statistics
    print("\n4. Testing statistics...")
    stats = refiner_percentile.get_filtering_statistics()
    
    print(f"   Total decisions: {stats['total_decisions']}")
    print(f"   Filtered: {stats['filtered_count']}")
    print(f"   Kept: {stats['kept_count']}")
    
    assert stats['total_decisions'] > 0, "Should have decision history"
    
    print("   ✓ Statistics work correctly")
    
    print("\n✅ All basic tests passed!")


if __name__ == "__main__":
    asyncio.run(test_basic())
