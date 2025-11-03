"""
Example: Ranking Visualization and Explanation

This script demonstrates the ranking explanation and visualization features
of the QualityAwareRanker, showing how different factors contribute to
the final ranking scores.

Usage:
    python example_ranking_visualization.py
"""

import asyncio
from hypergraphrag.retrieval.quality_ranker import QualityAwareRanker
from hypergraphrag.retrieval.ranking_visualizer import RankingVisualizer, create_ranking_dashboard


# Mock data generator
def generate_mock_results(n: int = 20):
    """Generate mock retrieval results with varying scores"""
    import random
    random.seed(42)
    
    results = []
    for i in range(n):
        # Generate varied scores to show different ranking scenarios
        similarity = random.uniform(0.5, 0.95)
        quality = random.uniform(0.3, 0.95)
        dynamic_weight = random.uniform(0.4, 0.95)
        
        results.append({
            "hyperedge_name": f"<hyperedge>Relation_{i+1}",
            "distance": similarity,
            "quality_score": quality,
            "dynamic_weight": dynamic_weight,
            "hyperedge": f"Entity A has relationship type {i+1} with Entity B through mechanism C"
        })
    
    return results


async def example_basic_explanation():
    """Example 1: Basic ranking explanation"""
    print("=" * 80)
    print("Example 1: Basic Ranking Explanation")
    print("=" * 80)
    
    # Generate mock data
    results = generate_mock_results(10)
    
    # Configure ranker with explanations enabled
    config = {
        "similarity_weight": 0.5,
        "quality_weight": 0.3,
        "dynamic_weight": 0.2,
        "provide_explanation": True  # Enable explanations
    }
    ranker = QualityAwareRanker(config)
    
    # Rank results
    ranked = await ranker.rank_hyperedges("test query", results)
    
    # Show explanation for top 3 results
    print("\nTop 3 Results with Explanations:")
    print("-" * 80)
    
    for i, he in enumerate(ranked[:3], 1):
        print(f"\n#{i} - {he['hyperedge_name']}")
        print(ranker.explain_ranking(he))
        print()


async def example_text_report():
    """Example 2: Generate text-based ranking report"""
    print("=" * 80)
    print("Example 2: Text-Based Ranking Report")
    print("=" * 80)
    
    results = generate_mock_results(15)
    
    config = {
        "similarity_weight": 0.5,
        "quality_weight": 0.3,
        "dynamic_weight": 0.2,
        "provide_explanation": True
    }
    ranker = QualityAwareRanker(config)
    ranked = await ranker.rank_hyperedges("test query", results)
    
    # Generate text report
    visualizer = RankingVisualizer()
    report = visualizer.generate_text_report(ranked, top_k=5)
    
    print("\n" + report)


async def example_component_visualization():
    """Example 3: Visualize ranking components"""
    print("=" * 80)
    print("Example 3: Component Contribution Visualization")
    print("=" * 80)
    
    results = generate_mock_results(15)
    
    config = {
        "similarity_weight": 0.5,
        "quality_weight": 0.3,
        "dynamic_weight": 0.2,
        "provide_explanation": True
    }
    ranker = QualityAwareRanker(config)
    ranked = await ranker.rank_hyperedges("test query", results)
    
    # Create visualizer
    visualizer = RankingVisualizer()
    
    # Plot component contributions
    print("\nGenerating component contribution plot...")
    fig = visualizer.plot_ranking_components(ranked, top_k=10)
    visualizer.save_visualization("ranking_components.png")
    print("✓ Saved to: ranking_components.png")


async def example_score_distribution():
    """Example 4: Visualize score distribution"""
    print("=" * 80)
    print("Example 4: Score Distribution Visualization")
    print("=" * 80)
    
    results = generate_mock_results(50)  # More results for better distribution
    
    config = {
        "similarity_weight": 0.5,
        "quality_weight": 0.3,
        "dynamic_weight": 0.2,
        "provide_explanation": True
    }
    ranker = QualityAwareRanker(config)
    ranked = await ranker.rank_hyperedges("test query", results)
    
    visualizer = RankingVisualizer()
    
    print("\nGenerating score distribution plot...")
    fig = visualizer.plot_score_distribution(ranked, bins=15)
    visualizer.save_visualization("score_distribution.png")
    print("✓ Saved to: score_distribution.png")


async def example_factor_comparison():
    """Example 5: Compare factor values"""
    print("=" * 80)
    print("Example 5: Factor Comparison Visualization")
    print("=" * 80)
    
    results = generate_mock_results(15)
    
    config = {
        "similarity_weight": 0.5,
        "quality_weight": 0.3,
        "dynamic_weight": 0.2,
        "provide_explanation": True
    }
    ranker = QualityAwareRanker(config)
    ranked = await ranker.rank_hyperedges("test query", results)
    
    visualizer = RankingVisualizer()
    
    print("\nGenerating factor comparison plot...")
    fig = visualizer.plot_factor_comparison(ranked, top_k=10)
    visualizer.save_visualization("factor_comparison.png")
    print("✓ Saved to: factor_comparison.png")


async def example_weight_impact():
    """Example 6: Visualize weight impact with pie charts"""
    print("=" * 80)
    print("Example 6: Weight Impact Visualization")
    print("=" * 80)
    
    results = generate_mock_results(10)
    
    config = {
        "similarity_weight": 0.5,
        "quality_weight": 0.3,
        "dynamic_weight": 0.2,
        "provide_explanation": True
    }
    ranker = QualityAwareRanker(config)
    ranked = await ranker.rank_hyperedges("test query", results)
    
    visualizer = RankingVisualizer()
    
    print("\nGenerating weight impact plot...")
    fig = visualizer.plot_weight_impact(ranked, top_k=6)
    visualizer.save_visualization("weight_impact.png")
    print("✓ Saved to: weight_impact.png")


async def example_comprehensive_dashboard():
    """Example 7: Create comprehensive dashboard"""
    print("=" * 80)
    print("Example 7: Comprehensive Ranking Dashboard")
    print("=" * 80)
    
    results = generate_mock_results(30)
    
    config = {
        "similarity_weight": 0.5,
        "quality_weight": 0.3,
        "dynamic_weight": 0.2,
        "provide_explanation": True
    }
    ranker = QualityAwareRanker(config)
    ranked = await ranker.rank_hyperedges("test query", results)
    
    print("\nGenerating comprehensive dashboard...")
    create_ranking_dashboard(ranked, output_path="ranking_dashboard.png", top_k=10)
    print("✓ Saved to: ranking_dashboard.png")


async def example_export_data():
    """Example 8: Export ranking data"""
    print("=" * 80)
    print("Example 8: Export Ranking Data")
    print("=" * 80)
    
    results = generate_mock_results(20)
    
    config = {
        "similarity_weight": 0.5,
        "quality_weight": 0.3,
        "dynamic_weight": 0.2,
        "provide_explanation": True
    }
    ranker = QualityAwareRanker(config)
    ranked = await ranker.rank_hyperedges("test query", results)
    
    visualizer = RankingVisualizer()
    
    # Export as JSON
    print("\nExporting ranking data as JSON...")
    visualizer.export_ranking_data(ranked, "ranking_results.json", format="json")
    print("✓ Saved to: ranking_results.json")
    
    # Export as CSV
    print("\nExporting ranking data as CSV...")
    visualizer.export_ranking_data(ranked, "ranking_results.csv", format="csv")
    print("✓ Saved to: ranking_results.csv")


async def example_strategy_comparison():
    """Example 9: Compare different ranking strategies visually"""
    print("=" * 80)
    print("Example 9: Strategy Comparison")
    print("=" * 80)
    
    results = generate_mock_results(15)
    
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
        }
    }
    
    print("\nComparing ranking strategies:")
    print("-" * 80)
    
    for strategy_name, config in strategies.items():
        config["provide_explanation"] = True
        ranker = QualityAwareRanker(config)
        ranked = await ranker.rank_hyperedges("test query", results)
        
        print(f"\n{strategy_name} Strategy:")
        print(f"  Top 3 Results:")
        for i, he in enumerate(ranked[:3], 1):
            print(f"    #{i}: Score={he['final_score']:.3f}, "
                  f"Sim={he['ranking_components']['similarity']:.2f}, "
                  f"Qual={he['ranking_components']['quality']:.2f}, "
                  f"Dyn={he['ranking_components']['dynamic_weight']:.2f}")


async def example_detailed_analysis():
    """Example 10: Detailed analysis of ranking decisions"""
    print("=" * 80)
    print("Example 10: Detailed Ranking Analysis")
    print("=" * 80)
    
    results = generate_mock_results(10)
    
    config = {
        "similarity_weight": 0.5,
        "quality_weight": 0.3,
        "dynamic_weight": 0.2,
        "provide_explanation": True
    }
    ranker = QualityAwareRanker(config)
    ranked = await ranker.rank_hyperedges("test query", results)
    
    print("\nDetailed Analysis of Top 5 Results:")
    print("-" * 80)
    
    for i, he in enumerate(ranked[:5], 1):
        components = he["ranking_components"]
        weights = components["weights"]
        
        print(f"\n#{i} - Final Score: {he['final_score']:.4f}")
        print(f"  Hyperedge: {he['hyperedge_name']}")
        print(f"\n  Raw Factor Values:")
        print(f"    Similarity:      {components['similarity']:.4f}")
        print(f"    Quality:         {components['quality']:.4f}")
        print(f"    Dynamic Weight:  {components['dynamic_weight']:.4f}")
        print(f"\n  Weighted Contributions:")
        print(f"    Similarity:      {components['similarity'] * weights['alpha']:.4f} "
              f"(weight: {weights['alpha']})")
        print(f"    Quality:         {components['quality'] * weights['beta']:.4f} "
              f"(weight: {weights['beta']})")
        print(f"    Dynamic Weight:  {components['dynamic_weight'] * weights['gamma']:.4f} "
              f"(weight: {weights['gamma']})")
        print(f"\n  Computation: {components['computation']}")
        
        # Identify dominant factor
        contributions = {
            "Similarity": components['similarity'] * weights['alpha'],
            "Quality": components['quality'] * weights['beta'],
            "Dynamic": components['dynamic_weight'] * weights['gamma']
        }
        dominant = max(contributions, key=contributions.get)
        print(f"  Dominant Factor: {dominant} ({contributions[dominant]:.4f})")


async def main():
    """Run all examples"""
    print("\n" + "=" * 80)
    print("RANKING EXPLANATION AND VISUALIZATION EXAMPLES")
    print("=" * 80 + "\n")
    
    # Text-based examples (always run)
    await example_basic_explanation()
    await example_text_report()
    await example_strategy_comparison()
    await example_detailed_analysis()
    
    # Check if matplotlib is available for visualizations
    try:
        import matplotlib.pyplot as plt
        
        print("\n" + "=" * 80)
        print("VISUALIZATION EXAMPLES (requires matplotlib)")
        print("=" * 80 + "\n")
        
        await example_component_visualization()
        await example_score_distribution()
        await example_factor_comparison()
        await example_weight_impact()
        await example_comprehensive_dashboard()
        await example_export_data()
        
        print("\n" + "=" * 80)
        print("All visualizations generated successfully!")
        print("=" * 80)
        print("\nGenerated files:")
        print("  - ranking_components.png")
        print("  - score_distribution.png")
        print("  - factor_comparison.png")
        print("  - weight_impact.png")
        print("  - ranking_dashboard.png")
        print("  - ranking_results.json")
        print("  - ranking_results.csv")
        
    except ImportError:
        print("\n" + "=" * 80)
        print("Note: matplotlib not available. Skipping visualization examples.")
        print("Install with: pip install matplotlib")
        print("=" * 80)
    
    print("\n" + "=" * 80)
    print("All examples completed!")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
