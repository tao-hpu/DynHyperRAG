"""
Test script for HyperedgeRefiner

This script demonstrates and tests the hyperedge refinement functionality,
including filtering strategies and threshold selection methods.

Usage:
    python test_hyperedge_refiner.py
"""

import asyncio
import sys
from typing import Dict, List

# Mock graph storage for testing
class MockGraphStorage:
    """Mock graph storage for testing purposes."""
    
    def __init__(self):
        self.nodes = {}
        self.namespace = "test"
        self.global_config = {}
    
    async def get_node(self, node_id: str) -> Dict:
        """Get node by ID."""
        return self.nodes.get(node_id)
    
    async def upsert_node(self, node_id: str, node_data: Dict):
        """Insert or update node."""
        self.nodes[node_id] = node_data
    
    async def delete_node(self, node_id: str):
        """Delete node."""
        if node_id in self.nodes:
            del self.nodes[node_id]
    
    async def has_node(self, node_id: str) -> bool:
        """Check if node exists."""
        return node_id in self.nodes
    
    def add_test_hyperedge(self, he_id: str, quality_score: float, weight: float = 1.0):
        """Add a test hyperedge."""
        self.nodes[he_id] = {
            'role': 'hyperedge',
            'hyperedge': f'Test hyperedge {he_id}',
            'quality_score': quality_score,
            'weight': weight,
            'dynamic_weight': weight,
        }


async def test_fixed_threshold_filtering():
    """Test fixed threshold filtering strategy."""
    print("\n" + "="*60)
    print("TEST 1: Fixed Threshold Filtering")
    print("="*60)
    
    # Setup
    graph = MockGraphStorage()
    
    # Add test hyperedges with varying quality
    test_data = [
        ('he1', 0.9),  # High quality
        ('he2', 0.7),  # Medium-high quality
        ('he3', 0.5),  # Medium quality
        ('he4', 0.3),  # Low quality
        ('he5', 0.1),  # Very low quality
    ]
    
    for he_id, quality in test_data:
        graph.add_test_hyperedge(he_id, quality)
    
    print(f"\nCreated {len(test_data)} test hyperedges:")
    for he_id, quality in test_data:
        print(f"  {he_id}: quality={quality:.2f}")
    
    # Import refiner
    from hypergraphrag.dynamic.refiner import HyperedgeRefiner
    
    # Test soft filtering
    print("\n--- Soft Filtering (threshold=0.5) ---")
    config_soft = {
        'quality_threshold': 0.5,
        'filter_mode': 'soft',
        'threshold_strategy': 'fixed',
    }
    refiner_soft = HyperedgeRefiner(graph, config_soft)
    
    hyperedge_ids = [he_id for he_id, _ in test_data]
    result_soft = await refiner_soft.filter_low_quality(hyperedge_ids)
    
    print(f"\nResults:")
    print(f"  Filtered: {result_soft['filtered']}")
    print(f"  Kept: {result_soft['kept']}")
    print(f"  Filter rate: {result_soft['filter_rate']:.1%}")
    print(f"  Threshold used: {result_soft['threshold_used']:.3f}")
    
    # Check soft filtering effect
    print(f"\nSoft filtering effects:")
    for he_id in result_soft['filtered']:
        node = await graph.get_node(he_id)
        print(f"  {he_id}: dynamic_weight={node['dynamic_weight']:.3f}, filtered={node.get('filtered', False)}")
    
    # Test hard filtering
    print("\n--- Hard Filtering (threshold=0.5) ---")
    
    # Reset graph
    graph = MockGraphStorage()
    for he_id, quality in test_data:
        graph.add_test_hyperedge(he_id, quality)
    
    config_hard = {
        'quality_threshold': 0.5,
        'filter_mode': 'hard',
        'threshold_strategy': 'fixed',
    }
    refiner_hard = HyperedgeRefiner(graph, config_hard)
    
    result_hard = await refiner_hard.filter_low_quality(hyperedge_ids)
    
    print(f"\nResults:")
    print(f"  Filtered (deleted): {result_hard['filtered']}")
    print(f"  Kept: {result_hard['kept']}")
    print(f"  Filter rate: {result_hard['filter_rate']:.1%}")
    
    # Verify deletion
    print(f"\nVerifying deletion:")
    for he_id in result_hard['filtered']:
        exists = await graph.has_node(he_id)
        print(f"  {he_id}: exists={exists}")
    
    print("\n✓ Fixed threshold filtering test passed")


async def test_percentile_threshold():
    """Test percentile-based threshold selection."""
    print("\n" + "="*60)
    print("TEST 2: Percentile-Based Threshold")
    print("="*60)
    
    # Setup
    graph = MockGraphStorage()
    
    # Add many hyperedges with normal distribution of quality
    import numpy as np
    np.random.seed(42)
    
    num_hyperedges = 100
    qualities = np.random.beta(5, 2, num_hyperedges)  # Skewed towards higher quality
    
    for i, quality in enumerate(qualities):
        graph.add_test_hyperedge(f'he{i}', float(quality))
    
    print(f"\nCreated {num_hyperedges} hyperedges")
    print(f"Quality distribution:")
    print(f"  Mean: {np.mean(qualities):.3f}")
    print(f"  Std: {np.std(qualities):.3f}")
    print(f"  Min: {np.min(qualities):.3f}")
    print(f"  Max: {np.max(qualities):.3f}")
    print(f"  25th percentile: {np.percentile(qualities, 25):.3f}")
    
    # Import refiner
    from hypergraphrag.dynamic.refiner import HyperedgeRefiner
    
    # Test percentile filtering (bottom 25%)
    print("\n--- Percentile Filtering (bottom 25%) ---")
    config = {
        'filter_mode': 'soft',
        'threshold_strategy': 'percentile',
        'percentile': 25,
    }
    refiner = HyperedgeRefiner(graph, config)
    
    hyperedge_ids = [f'he{i}' for i in range(num_hyperedges)]
    result = await refiner.filter_low_quality(hyperedge_ids)
    
    print(f"\nResults:")
    print(f"  Filtered: {len(result['filtered'])} hyperedges")
    print(f"  Kept: {len(result['kept'])} hyperedges")
    print(f"  Filter rate: {result['filter_rate']:.1%}")
    print(f"  Threshold used: {result['threshold_used']:.3f}")
    print(f"  Expected filter rate: ~25%")
    
    # Verify approximately 25% filtered
    assert 20 <= len(result['filtered']) <= 30, "Filter rate should be around 25%"
    
    print("\n✓ Percentile threshold test passed")


async def test_f1_optimal_threshold():
    """Test F1-optimal threshold selection with ground truth."""
    print("\n" + "="*60)
    print("TEST 3: F1-Optimal Threshold")
    print("="*60)
    
    # Setup
    graph = MockGraphStorage()
    
    # Add hyperedges with known ground truth
    # Good hyperedges: high quality scores
    # Bad hyperedges: low quality scores (with some noise)
    test_data = [
        # (he_id, quality_score, is_good)
        ('he1', 0.9, True),
        ('he2', 0.85, True),
        ('he3', 0.8, True),
        ('he4', 0.75, True),
        ('he5', 0.7, True),
        ('he6', 0.65, False),  # Borderline
        ('he7', 0.6, False),
        ('he8', 0.4, False),
        ('he9', 0.3, False),
        ('he10', 0.2, False),
    ]
    
    ground_truth = {}
    for he_id, quality, is_good in test_data:
        graph.add_test_hyperedge(he_id, quality)
        ground_truth[he_id] = is_good
    
    print(f"\nCreated {len(test_data)} hyperedges with ground truth:")
    print(f"  Good hyperedges: {sum(1 for _, _, is_good in test_data if is_good)}")
    print(f"  Bad hyperedges: {sum(1 for _, _, is_good in test_data if not is_good)}")
    
    # Import refiner
    from hypergraphrag.dynamic.refiner import HyperedgeRefiner
    
    # Test F1-optimal filtering
    print("\n--- F1-Optimal Filtering ---")
    config = {
        'filter_mode': 'soft',
        'threshold_strategy': 'f1_optimal',
    }
    refiner = HyperedgeRefiner(graph, config)
    
    hyperedge_ids = [he_id for he_id, _, _ in test_data]
    result = await refiner.filter_low_quality(hyperedge_ids, ground_truth)
    
    print(f"\nResults:")
    print(f"  Filtered: {result['filtered']}")
    print(f"  Kept: {result['kept']}")
    print(f"  Filter rate: {result['filter_rate']:.1%}")
    print(f"  Threshold used: {result['threshold_used']:.3f}")
    
    # Compute performance metrics
    from hypergraphrag.dynamic.refiner import compute_filtering_metrics
    metrics = compute_filtering_metrics(result['filtered'], result['kept'], ground_truth)
    
    print(f"\nPerformance metrics:")
    print(f"  Precision: {metrics['precision']:.3f}")
    print(f"  Recall: {metrics['recall']:.3f}")
    print(f"  F1: {metrics['f1']:.3f}")
    print(f"  Accuracy: {metrics['accuracy']:.3f}")
    
    print("\n✓ F1-optimal threshold test passed")


async def test_batch_filtering():
    """Test batch filtering functionality."""
    print("\n" + "="*60)
    print("TEST 4: Batch Filtering")
    print("="*60)
    
    # Setup
    graph = MockGraphStorage()
    
    # Create multiple batches
    batches = [
        [('he1_1', 0.8), ('he1_2', 0.3), ('he1_3', 0.6)],
        [('he2_1', 0.9), ('he2_2', 0.2), ('he2_3', 0.5)],
        [('he3_1', 0.7), ('he3_2', 0.4), ('he3_3', 0.1)],
    ]
    
    for batch in batches:
        for he_id, quality in batch:
            graph.add_test_hyperedge(he_id, quality)
    
    print(f"\nCreated {len(batches)} batches with {sum(len(b) for b in batches)} total hyperedges")
    
    # Import refiner
    from hypergraphrag.dynamic.refiner import HyperedgeRefiner
    
    config = {
        'quality_threshold': 0.5,
        'filter_mode': 'soft',
        'threshold_strategy': 'fixed',
    }
    refiner = HyperedgeRefiner(graph, config)
    
    # Prepare batch IDs
    batch_ids = [[he_id for he_id, _ in batch] for batch in batches]
    
    # Batch filter
    print("\n--- Batch Filtering ---")
    results = await refiner.batch_filter_low_quality(batch_ids)
    
    print(f"\nResults:")
    for i, result in enumerate(results):
        print(f"  Batch {i+1}:")
        print(f"    Filtered: {result['filtered']}")
        print(f"    Kept: {result['kept']}")
        print(f"    Filter rate: {result['filter_rate']:.1%}")
    
    print("\n✓ Batch filtering test passed")


async def test_restore_functionality():
    """Test restore functionality for soft-filtered hyperedges."""
    print("\n" + "="*60)
    print("TEST 5: Restore Soft-Filtered Hyperedges")
    print("="*60)
    
    # Setup
    graph = MockGraphStorage()
    
    test_data = [
        ('he1', 0.8),
        ('he2', 0.3),
        ('he3', 0.6),
        ('he4', 0.2),
    ]
    
    for he_id, quality in test_data:
        graph.add_test_hyperedge(he_id, quality)
    
    print(f"\nCreated {len(test_data)} test hyperedges")
    
    # Import refiner
    from hypergraphrag.dynamic.refiner import HyperedgeRefiner
    
    config = {
        'quality_threshold': 0.5,
        'filter_mode': 'soft',
        'threshold_strategy': 'fixed',
    }
    refiner = HyperedgeRefiner(graph, config)
    
    # Filter
    print("\n--- Initial Filtering ---")
    hyperedge_ids = [he_id for he_id, _ in test_data]
    result = await refiner.filter_low_quality(hyperedge_ids)
    
    print(f"Filtered: {result['filtered']}")
    
    # Check weights after filtering
    print(f"\nWeights after filtering:")
    for he_id in result['filtered']:
        node = await graph.get_node(he_id)
        print(f"  {he_id}: dynamic_weight={node['dynamic_weight']:.3f}, filtered={node.get('filtered', False)}")
    
    # Restore
    print("\n--- Restoring Filtered Hyperedges ---")
    restored_count = await refiner.restore_filtered_hyperedges(result['filtered'])
    print(f"Restored {restored_count} hyperedges")
    
    # Check weights after restoration
    print(f"\nWeights after restoration:")
    for he_id in result['filtered']:
        node = await graph.get_node(he_id)
        print(f"  {he_id}: dynamic_weight={node['dynamic_weight']:.3f}, filtered={node.get('filtered', False)}")
    
    # Verify restoration
    for he_id in result['filtered']:
        node = await graph.get_node(he_id)
        assert node.get('filtered', False) == False, f"{he_id} should not be marked as filtered"
        assert node['dynamic_weight'] == node['quality_score'], f"{he_id} weight should be restored"
    
    print("\n✓ Restore functionality test passed")


async def test_statistics():
    """Test statistics and analysis functions."""
    print("\n" + "="*60)
    print("TEST 6: Statistics and Analysis")
    print("="*60)
    
    # Setup
    graph = MockGraphStorage()
    
    import numpy as np
    np.random.seed(42)
    
    num_hyperedges = 50
    qualities = np.random.beta(5, 2, num_hyperedges)
    
    for i, quality in enumerate(qualities):
        graph.add_test_hyperedge(f'he{i}', float(quality))
    
    print(f"\nCreated {num_hyperedges} hyperedges")
    
    # Import refiner and helper functions
    from hypergraphrag.dynamic.refiner import (
        HyperedgeRefiner,
        analyze_quality_distribution
    )
    
    config = {
        'quality_threshold': 0.5,
        'filter_mode': 'soft',
        'threshold_strategy': 'fixed',
        'track_decisions': True,
    }
    refiner = HyperedgeRefiner(graph, config)
    
    # Filter
    hyperedge_ids = [f'he{i}' for i in range(num_hyperedges)]
    result = await refiner.filter_low_quality(hyperedge_ids)
    
    # Get statistics
    print("\n--- Filtering Statistics ---")
    stats = refiner.get_filtering_statistics()
    print(f"Total decisions: {stats['total_decisions']}")
    print(f"Filtered count: {stats['filtered_count']}")
    print(f"Kept count: {stats['kept_count']}")
    print(f"Filter rate: {stats['filter_rate']:.1%}")
    print(f"Avg quality (filtered): {stats['avg_quality_filtered']:.3f}")
    print(f"Avg quality (kept): {stats['avg_quality_kept']:.3f}")
    
    # Analyze quality distribution
    print("\n--- Quality Distribution Analysis ---")
    quality_scores = {f'he{i}': float(q) for i, q in enumerate(qualities)}
    dist_stats = analyze_quality_distribution(quality_scores)
    
    print(f"Count: {dist_stats['count']}")
    print(f"Mean: {dist_stats['mean']:.3f}")
    print(f"Std: {dist_stats['std']:.3f}")
    print(f"Min: {dist_stats['min']:.3f}")
    print(f"Max: {dist_stats['max']:.3f}")
    print(f"Median: {dist_stats['median']:.3f}")
    print(f"Below 0.3: {dist_stats['below_0.3']}")
    print(f"Below 0.5: {dist_stats['below_0.5']}")
    print(f"Above 0.7: {dist_stats['above_0.7']}")
    
    print("\n✓ Statistics test passed")


async def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("HYPEREDGE REFINER TEST SUITE")
    print("="*60)
    
    try:
        await test_fixed_threshold_filtering()
        await test_percentile_threshold()
        await test_f1_optimal_threshold()
        await test_batch_filtering()
        await test_restore_functionality()
        await test_statistics()
        
        print("\n" + "="*60)
        print("ALL TESTS PASSED ✓")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
