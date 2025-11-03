"""
Example: Integrating HyperedgeRefiner with DynHyperRAG

This example demonstrates how to use the HyperedgeRefiner module
in conjunction with QualityScorer and WeightUpdater for complete
knowledge graph quality management.

Usage:
    python example_refiner_integration.py
"""

import asyncio
from typing import Dict, List


# Mock implementations for demonstration
class MockGraphStorage:
    """Mock graph storage for demonstration."""
    
    def __init__(self):
        self.nodes = {}
        self.namespace = "demo"
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
    
    async def get_node_edges(self, node_id: str):
        # Mock: return some edges
        return [('hyperedge', 'entity1'), ('hyperedge', 'entity2')]
    
    async def node_degree(self, node_id: str) -> int:
        edges = await self.get_node_edges(node_id)
        return len(edges) if edges else 0


async def mock_embedding_func(texts: List[str]):
    """Mock embedding function."""
    import numpy as np
    # Return random embeddings for demonstration
    return [np.random.rand(384) for _ in texts]


async def demo_complete_workflow():
    """
    Demonstrate complete workflow:
    1. Score hyperedges
    2. Update weights based on feedback
    3. Filter low-quality hyperedges
    """
    print("="*70)
    print("COMPLETE DYNHYPERRAG WORKFLOW DEMONSTRATION")
    print("="*70)
    
    # Setup
    graph = MockGraphStorage()
    
    # Create sample hyperedges with varying quality
    sample_hyperedges = [
        ('he1', 0.9, 'High quality hyperedge about entity relationships'),
        ('he2', 0.7, 'Medium-high quality hyperedge'),
        ('he3', 0.5, 'Medium quality hyperedge'),
        ('he4', 0.3, 'Low quality hyperedge'),
        ('he5', 0.1, 'Very low quality hyperedge'),
        ('he6', 0.8, 'Another high quality hyperedge'),
        ('he7', 0.4, 'Below average quality hyperedge'),
        ('he8', 0.6, 'Slightly above average hyperedge'),
    ]
    
    # Initialize graph with hyperedges
    for he_id, quality, description in sample_hyperedges:
        graph.nodes[he_id] = {
            'role': 'hyperedge',
            'hyperedge': description,
            'quality_score': quality,
            'weight': 1.0,
            'dynamic_weight': quality,  # Initialize with quality score
            'quality_features': {
                'degree_centrality': quality * 0.8,
                'betweenness': quality * 0.9,
                'clustering': quality * 0.7,
                'coherence': quality,
                'text_quality': quality * 0.85,
            }
        }
    
    print(f"\nInitialized graph with {len(sample_hyperedges)} hyperedges")
    print("\nInitial quality distribution:")
    for he_id, quality, _ in sample_hyperedges:
        print(f"  {he_id}: quality={quality:.2f}")
    
    # Step 1: Quality Scoring (already done in initialization)
    print("\n" + "-"*70)
    print("STEP 1: Quality Scoring")
    print("-"*70)
    print("✓ Quality scores already computed and stored")
    
    # Step 2: Simulate retrieval and feedback
    print("\n" + "-"*70)
    print("STEP 2: Simulate Retrieval and Feedback")
    print("-"*70)
    
    # Simulate a query that retrieves some hyperedges
    retrieved_ids = ['he1', 'he3', 'he5', 'he6']
    print(f"\nRetrieved hyperedges: {retrieved_ids}")
    
    # Simulate feedback (high quality ones get positive feedback)
    from hypergraphrag.dynamic.weight_updater import WeightUpdater
    
    updater_config = {
        'strategy': 'ema',
        'update_alpha': 0.1,
        'decay_factor': 0.99,
    }
    updater = WeightUpdater(graph, updater_config)
    
    # Simulate feedback signals
    feedback_signals = {
        'he1': 0.9,  # High quality, positive feedback
        'he3': 0.6,  # Medium quality, neutral feedback
        'he5': 0.2,  # Low quality, negative feedback
        'he6': 0.85, # High quality, positive feedback
    }
    
    print("\nUpdating weights based on feedback...")
    for he_id, feedback in feedback_signals.items():
        new_weight = await updater.update_weights(he_id, feedback)
        print(f"  {he_id}: feedback={feedback:.2f} -> new_weight={new_weight:.3f}")
    
    # Step 3: Filter low-quality hyperedges
    print("\n" + "-"*70)
    print("STEP 3: Filter Low-Quality Hyperedges")
    print("-"*70)
    
    from hypergraphrag.dynamic.refiner import HyperedgeRefiner
    
    # Strategy 1: Fixed threshold
    print("\n--- Strategy 1: Fixed Threshold (0.5) ---")
    refiner_config_fixed = {
        'quality_threshold': 0.5,
        'filter_mode': 'soft',
        'threshold_strategy': 'fixed',
    }
    refiner_fixed = HyperedgeRefiner(graph, refiner_config_fixed)
    
    all_ids = [he_id for he_id, _, _ in sample_hyperedges]
    result_fixed = await refiner_fixed.filter_low_quality(all_ids)
    
    print(f"Filtered: {result_fixed['filtered']}")
    print(f"Kept: {result_fixed['kept']}")
    print(f"Filter rate: {result_fixed['filter_rate']:.1%}")
    
    # Strategy 2: Percentile-based
    print("\n--- Strategy 2: Percentile-Based (bottom 25%) ---")
    
    # Reset graph for fair comparison
    for he_id, quality, description in sample_hyperedges:
        if he_id in graph.nodes:
            graph.nodes[he_id]['dynamic_weight'] = quality
            graph.nodes[he_id]['filtered'] = False
    
    refiner_config_percentile = {
        'filter_mode': 'soft',
        'threshold_strategy': 'percentile',
        'percentile': 25,
    }
    refiner_percentile = HyperedgeRefiner(graph, refiner_config_percentile)
    
    result_percentile = await refiner_percentile.filter_low_quality(all_ids)
    
    print(f"Filtered: {result_percentile['filtered']}")
    print(f"Kept: {result_percentile['kept']}")
    print(f"Filter rate: {result_percentile['filter_rate']:.1%}")
    print(f"Threshold used: {result_percentile['threshold_used']:.3f}")
    
    # Step 4: Analyze results
    print("\n" + "-"*70)
    print("STEP 4: Analysis and Statistics")
    print("-"*70)
    
    from hypergraphrag.dynamic.refiner import analyze_quality_distribution
    
    quality_scores = {he_id: quality for he_id, quality, _ in sample_hyperedges}
    dist_stats = analyze_quality_distribution(quality_scores)
    
    print("\nQuality Distribution:")
    print(f"  Mean: {dist_stats['mean']:.3f}")
    print(f"  Std: {dist_stats['std']:.3f}")
    print(f"  Min: {dist_stats['min']:.3f}")
    print(f"  Max: {dist_stats['max']:.3f}")
    print(f"  Below 0.5: {dist_stats['below_0.5']}")
    print(f"  Above 0.7: {dist_stats['above_0.7']}")
    
    # Filtering statistics
    stats = refiner_percentile.get_filtering_statistics()
    print("\nFiltering Statistics:")
    print(f"  Total decisions: {stats['total_decisions']}")
    print(f"  Filtered: {stats['filtered_count']}")
    print(f"  Kept: {stats['kept_count']}")
    print(f"  Avg quality (filtered): {stats['avg_quality_filtered']:.3f}")
    print(f"  Avg quality (kept): {stats['avg_quality_kept']:.3f}")
    
    # Step 5: Demonstrate restoration
    print("\n" + "-"*70)
    print("STEP 5: Restore Filtered Hyperedges")
    print("-"*70)
    
    print(f"\nRestoring {len(result_percentile['filtered'])} filtered hyperedges...")
    restored_count = await refiner_percentile.restore_filtered_hyperedges(
        result_percentile['filtered']
    )
    print(f"✓ Restored {restored_count} hyperedges")
    
    # Verify restoration
    print("\nVerifying restoration:")
    for he_id in result_percentile['filtered'][:3]:  # Check first 3
        node = await graph.get_node(he_id)
        print(f"  {he_id}: dynamic_weight={node['dynamic_weight']:.3f}, "
              f"filtered={node.get('filtered', False)}")
    
    print("\n" + "="*70)
    print("WORKFLOW COMPLETE")
    print("="*70)
    print("\nKey Takeaways:")
    print("1. Quality scores guide filtering decisions")
    print("2. Dynamic weights adapt based on feedback")
    print("3. Multiple filtering strategies available")
    print("4. Soft filtering allows restoration")
    print("5. Comprehensive statistics for analysis")


async def demo_batch_processing():
    """Demonstrate batch processing for large-scale filtering."""
    print("\n" + "="*70)
    print("BATCH PROCESSING DEMONSTRATION")
    print("="*70)
    
    # Setup
    graph = MockGraphStorage()
    
    # Create many hyperedges
    import numpy as np
    np.random.seed(42)
    
    num_hyperedges = 100
    qualities = np.random.beta(5, 2, num_hyperedges)  # Skewed distribution
    
    for i, quality in enumerate(qualities):
        graph.nodes[f'he{i}'] = {
            'role': 'hyperedge',
            'quality_score': float(quality),
            'weight': 1.0,
            'dynamic_weight': float(quality),
        }
    
    print(f"\nCreated {num_hyperedges} hyperedges")
    
    # Batch filtering
    from hypergraphrag.dynamic.refiner import HyperedgeRefiner
    
    config = {
        'filter_mode': 'soft',
        'threshold_strategy': 'percentile',
        'percentile': 20,  # Filter bottom 20%
    }
    refiner = HyperedgeRefiner(graph, config)
    
    # Split into batches
    batch_size = 25
    batches = []
    for i in range(0, num_hyperedges, batch_size):
        batch = [f'he{j}' for j in range(i, min(i + batch_size, num_hyperedges))]
        batches.append(batch)
    
    print(f"\nProcessing {len(batches)} batches of {batch_size} hyperedges each...")
    
    results = await refiner.batch_filter_low_quality(batches)
    
    print("\nBatch Results:")
    total_filtered = 0
    for i, result in enumerate(results):
        print(f"  Batch {i+1}: {len(result['filtered'])} filtered, "
              f"{len(result['kept'])} kept ({result['filter_rate']:.1%})")
        total_filtered += len(result['filtered'])
    
    print(f"\nTotal filtered: {total_filtered} ({total_filtered/num_hyperedges:.1%})")
    print("✓ Batch processing complete")


async def main():
    """Run all demonstrations."""
    try:
        await demo_complete_workflow()
        await demo_batch_processing()
        
        print("\n" + "="*70)
        print("ALL DEMONSTRATIONS COMPLETED SUCCESSFULLY ✓")
        print("="*70)
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
