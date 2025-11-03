"""
Example: Quality-Aware Ranking Integration

This script demonstrates how to integrate the QualityAwareRanker into
the DynHyperRAG retrieval pipeline for improved ranking.

Usage:
    python example_quality_ranker_integration.py
"""

import asyncio
from hypergraphrag.retrieval.quality_ranker import QualityAwareRanker, rank_by_quality


# Mock vector database for demonstration
class MockVectorDB:
    """Mock vector database that returns sample retrieval results"""
    
    async def query(self, query: str, top_k: int = 10):
        """Mock vector query returning hyperedges with varying scores"""
        return [
            {
                "hyperedge_name": "<hyperedge>High quality, medium similarity",
                "distance": 0.75,
                "quality_score": 0.92,
                "dynamic_weight": 0.85,
                "hyperedge": "Entity A has strong relationship with Entity B in medical context"
            },
            {
                "hyperedge_name": "<hyperedge>High similarity, low quality",
                "distance": 0.95,
                "quality_score": 0.45,
                "dynamic_weight": 0.50,
                "hyperedge": "Entity A relates to Entity B"
            },
            {
                "hyperedge_name": "<hyperedge>Medium all around",
                "distance": 0.70,
                "quality_score": 0.65,
                "dynamic_weight": 0.70,
                "hyperedge": "Entity A connects to Entity B through pathway C"
            },
            {
                "hyperedge_name": "<hyperedge>Low similarity, high quality",
                "distance": 0.60,
                "quality_score": 0.88,
                "dynamic_weight": 0.90,
                "hyperedge": "Entity A regulates Entity B via mechanism C with evidence D"
            },
            {
                "hyperedge_name": "<hyperedge>Boosted by feedback",
                "distance": 0.72,
                "quality_score": 0.70,
                "dynamic_weight": 0.95,  # High due to positive user feedback
                "hyperedge": "Entity A interacts with Entity B in disease context"
            }
        ]


async def example_basic_ranking():
    """Example 1: Basic quality-aware ranking"""
    print("=" * 70)
    print("Example 1: Basic Quality-Aware Ranking")
    print("=" * 70)
    
    # Initialize components
    vdb = MockVectorDB()
    config = {
        "similarity_weight": 0.5,
        "quality_weight": 0.3,
        "dynamic_weight": 0.2
    }
    ranker = QualityAwareRanker(config)
    
    # Simulate retrieval
    query = "What is the relationship between Entity A and Entity B?"
    print(f"\nQuery: {query}\n")
    
    # Get initial results from vector retrieval
    results = await vdb.query(query, top_k=10)
    print(f"Retrieved {len(results)} hyperedges from vector search\n")
    
    # Rank by quality
    ranked_results = await ranker.rank_hyperedges(query, results)
    
    # Display results
    print("Ranked Results:")
    print("-" * 70)
    for i, he in enumerate(ranked_results, 1):
        print(f"{i}. Score: {he['final_score']:.3f}")
        print(f"   Similarity: {he['distance']:.2f} | "
              f"Quality: {he['quality_score']:.2f} | "
              f"Dynamic: {he['dynamic_weight']:.2f}")
        print(f"   {he['hyperedge']}")
        print()


async def example_with_explanation():
    """Example 2: Ranking with detailed explanations"""
    print("=" * 70)
    print("Example 2: Ranking with Explanations")
    print("=" * 70)
    
    vdb = MockVectorDB()
    config = {
        "similarity_weight": 0.5,
        "quality_weight": 0.3,
        "dynamic_weight": 0.2,
        "provide_explanation": True  # Enable explanations
    }
    ranker = QualityAwareRanker(config)
    
    query = "What is the relationship between Entity A and Entity B?"
    results = await vdb.query(query, top_k=10)
    ranked_results = await ranker.rank_hyperedges(query, results)
    
    # Show detailed explanation for top result
    print(f"\nTop Result Explanation:")
    print("-" * 70)
    top_result = ranked_results[0]
    print(f"Hyperedge: {top_result['hyperedge']}\n")
    explanation = ranker.explain_ranking(top_result)
    print(explanation)
    print()


async def example_different_strategies():
    """Example 3: Compare different ranking strategies"""
    print("=" * 70)
    print("Example 3: Comparing Ranking Strategies")
    print("=" * 70)
    
    vdb = MockVectorDB()
    query = "What is the relationship between Entity A and Entity B?"
    results = await vdb.query(query, top_k=10)
    
    strategies = {
        "Balanced": {
            "similarity_weight": 0.5,
            "quality_weight": 0.3,
            "dynamic_weight": 0.2
        },
        "Quality-Focused": {
            "similarity_weight": 0.3,
            "quality_weight": 0.5,
            "dynamic_weight": 0.2
        },
        "Similarity-Focused": {
            "similarity_weight": 0.7,
            "quality_weight": 0.2,
            "dynamic_weight": 0.1
        },
        "Feedback-Driven": {
            "similarity_weight": 0.3,
            "quality_weight": 0.3,
            "dynamic_weight": 0.4
        }
    }
    
    print(f"\nComparing strategies for query: {query}\n")
    
    for strategy_name, config in strategies.items():
        ranker = QualityAwareRanker(config)
        ranked = await ranker.rank_hyperedges(query, results)
        
        print(f"{strategy_name} Strategy:")
        print(f"  Weights: α={config['similarity_weight']}, "
              f"β={config['quality_weight']}, γ={config['dynamic_weight']}")
        print(f"  Top Result: {ranked[0]['hyperedge'][:60]}...")
        print(f"  Score: {ranked[0]['final_score']:.3f}")
        print()


async def example_convenience_function():
    """Example 4: Using the convenience function"""
    print("=" * 70)
    print("Example 4: Using Convenience Function")
    print("=" * 70)
    
    vdb = MockVectorDB()
    query = "What is the relationship between Entity A and Entity B?"
    results = await vdb.query(query, top_k=10)
    
    print(f"\nQuery: {query}\n")
    
    # Quick ranking with custom weights
    ranked = await rank_by_quality(
        hyperedges=results,
        query=query,
        similarity_weight=0.6,
        quality_weight=0.3,
        dynamic_weight=0.1
    )
    
    print("Top 3 Results:")
    print("-" * 70)
    for i, he in enumerate(ranked[:3], 1):
        print(f"{i}. Score: {he['final_score']:.3f}")
        print(f"   {he['hyperedge']}")
        print()


async def example_dynamic_weight_adjustment():
    """Example 5: Dynamically adjusting weights"""
    print("=" * 70)
    print("Example 5: Dynamic Weight Adjustment")
    print("=" * 70)
    
    vdb = MockVectorDB()
    query = "What is the relationship between Entity A and Entity B?"
    results = await vdb.query(query, top_k=10)
    
    # Initialize with default weights
    ranker = QualityAwareRanker({})
    
    print(f"\nQuery: {query}\n")
    
    # Scenario 1: High precision needed
    print("Scenario 1: High Precision (Medical Diagnosis)")
    ranker.set_weights(alpha=0.3, beta=0.5, gamma=0.2)
    ranked1 = await ranker.rank_hyperedges(query, results)
    print(f"  Top result: {ranked1[0]['hyperedge'][:60]}...")
    print(f"  Score: {ranked1[0]['final_score']:.3f}\n")
    
    # Scenario 2: High recall needed
    print("Scenario 2: High Recall (Exploratory Search)")
    ranker.set_weights(alpha=0.7, beta=0.2, gamma=0.1)
    ranked2 = await ranker.rank_hyperedges(query, results)
    print(f"  Top result: {ranked2[0]['hyperedge'][:60]}...")
    print(f"  Score: {ranked2[0]['final_score']:.3f}\n")
    
    # Scenario 3: Trust user feedback
    print("Scenario 3: Feedback-Driven (User Preferences)")
    ranker.set_weights(alpha=0.3, beta=0.3, gamma=0.4)
    ranked3 = await ranker.rank_hyperedges(query, results)
    print(f"  Top result: {ranked3[0]['hyperedge'][:60]}...")
    print(f"  Score: {ranked3[0]['final_score']:.3f}\n")


async def example_full_pipeline():
    """Example 6: Full retrieval pipeline with quality ranking"""
    print("=" * 70)
    print("Example 6: Full Retrieval Pipeline")
    print("=" * 70)
    
    vdb = MockVectorDB()
    query = "What is the relationship between Entity A and Entity B?"
    
    print(f"\nQuery: {query}\n")
    print("Pipeline Steps:")
    print("-" * 70)
    
    # Step 1: Vector retrieval
    print("1. Vector Retrieval...")
    results = await vdb.query(query, top_k=20)
    print(f"   Retrieved {len(results)} hyperedges\n")
    
    # Step 2: (Optional) Entity type filtering would go here
    print("2. Entity Type Filtering (skipped in this example)\n")
    
    # Step 3: Quality-aware ranking
    print("3. Quality-Aware Ranking...")
    config = {
        "similarity_weight": 0.5,
        "quality_weight": 0.3,
        "dynamic_weight": 0.2
    }
    ranker = QualityAwareRanker(config)
    ranked_results = await ranker.rank_hyperedges(query, results)
    print(f"   Ranked {len(ranked_results)} hyperedges\n")
    
    # Step 4: Select top-k
    print("4. Select Top-5 Results:")
    print("-" * 70)
    for i, he in enumerate(ranked_results[:5], 1):
        print(f"{i}. Score: {he['final_score']:.3f}")
        print(f"   {he['hyperedge']}")
        print()


async def main():
    """Run all examples"""
    print("\n" + "=" * 70)
    print("Quality-Aware Ranker Integration Examples")
    print("=" * 70 + "\n")
    
    await example_basic_ranking()
    await example_with_explanation()
    await example_different_strategies()
    await example_convenience_function()
    await example_dynamic_weight_adjustment()
    await example_full_pipeline()
    
    print("=" * 70)
    print("All examples completed successfully!")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
