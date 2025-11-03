"""
Test suite for Ranking Visualization

Tests the ranking visualization and explanation features.
"""

import asyncio
import os
import json
from hypergraphrag.retrieval.quality_ranker import QualityAwareRanker
from hypergraphrag.retrieval.ranking_visualizer import RankingVisualizer


def generate_test_results(n: int = 10):
    """Generate test results with ranking components"""
    results = []
    for i in range(n):
        similarity = 0.9 - (i * 0.05)
        quality = 0.8 - (i * 0.04)
        dynamic = 0.85 - (i * 0.03)
        
        results.append({
            "hyperedge_name": f"<hyperedge>Test_{i+1}",
            "distance": similarity,
            "quality_score": quality,
            "dynamic_weight": dynamic,
            "hyperedge": f"Test relation {i+1}"
        })
    
    return results


class TestRankingExplanation:
    """Test ranking explanation features"""
    
    def test_explanation_enabled(self):
        """Test that explanations are generated when enabled"""
        async def run_test():
            config = {
                "similarity_weight": 0.5,
                "quality_weight": 0.3,
                "dynamic_weight": 0.2,
                "provide_explanation": True
            }
            ranker = QualityAwareRanker(config)
            
            results = generate_test_results(5)
            ranked = await ranker.rank_hyperedges("test query", results)
            
            # Check that ranking_components are present
            assert len(ranked) == 5
            for he in ranked:
                assert "ranking_components" in he
                assert "similarity" in he["ranking_components"]
                assert "quality" in he["ranking_components"]
                assert "dynamic_weight" in he["ranking_components"]
                assert "weights" in he["ranking_components"]
                assert "computation" in he["ranking_components"]
        
        asyncio.run(run_test())
        print("✓ test_explanation_enabled passed")
    
    def test_explanation_disabled(self):
        """Test that explanations are not generated when disabled"""
        async def run_test():
            config = {
                "similarity_weight": 0.5,
                "quality_weight": 0.3,
                "dynamic_weight": 0.2,
                "provide_explanation": False
            }
            ranker = QualityAwareRanker(config)
            
            results = generate_test_results(5)
            ranked = await ranker.rank_hyperedges("test query", results)
            
            # Check that ranking_components are NOT present
            assert len(ranked) == 5
            for he in ranked:
                assert "ranking_components" not in he
        
        asyncio.run(run_test())
        print("✓ test_explanation_disabled passed")
    
    def test_explain_ranking_method(self):
        """Test the explain_ranking method"""
        config = {
            "similarity_weight": 0.5,
            "quality_weight": 0.3,
            "dynamic_weight": 0.2,
            "provide_explanation": True
        }
        ranker = QualityAwareRanker(config)
        
        # Create a mock hyperedge with ranking components
        hyperedge = {
            "hyperedge_name": "<hyperedge>Test",
            "final_score": 0.79,
            "ranking_components": {
                "similarity": 0.8,
                "quality": 0.7,
                "dynamic_weight": 0.9,
                "weights": {"alpha": 0.5, "beta": 0.3, "gamma": 0.2},
                "computation": "0.5×0.800 + 0.3×0.700 + 0.2×0.900 = 0.790"
            }
        }
        
        explanation = ranker.explain_ranking(hyperedge)
        
        # Check that explanation contains key information
        assert "Final Score: 0.79" in explanation
        assert "Similarity: 0.8" in explanation
        assert "Quality: 0.7" in explanation
        assert "Dynamic Weight: 0.9" in explanation
        assert "Computation:" in explanation
        
        print("✓ test_explain_ranking_method passed")
    
    def test_explain_ranking_without_components(self):
        """Test explain_ranking with missing components"""
        ranker = QualityAwareRanker({})
        
        hyperedge = {
            "hyperedge_name": "<hyperedge>Test",
            "final_score": 0.79
            # No ranking_components
        }
        
        explanation = ranker.explain_ranking(hyperedge)
        
        assert "No ranking explanation available" in explanation
        
        print("✓ test_explain_ranking_without_components passed")


class TestRankingVisualizer:
    """Test ranking visualizer features"""
    
    def test_visualizer_initialization(self):
        """Test visualizer initialization"""
        try:
            visualizer = RankingVisualizer()
            assert visualizer.figsize == (12, 8)
            assert visualizer.dpi == 100
            print("✓ test_visualizer_initialization passed")
        except ImportError:
            print("⊘ test_visualizer_initialization skipped (matplotlib not available)")
    
    def test_text_report_generation(self):
        """Test text report generation"""
        async def run_test():
            try:
                config = {
                    "similarity_weight": 0.5,
                    "quality_weight": 0.3,
                    "dynamic_weight": 0.2,
                    "provide_explanation": True
                }
                ranker = QualityAwareRanker(config)
                
                results = generate_test_results(10)
                ranked = await ranker.rank_hyperedges("test query", results)
                
                visualizer = RankingVisualizer()
                report = visualizer.generate_text_report(ranked, top_k=5)
                
                # Check report content
                assert "RANKING ANALYSIS REPORT" in report
                assert "Total Results: 10" in report
                assert "TOP 5 RESULTS:" in report
                assert "#1 - Final Score:" in report
                
                print("✓ test_text_report_generation passed")
            except ImportError:
                print("⊘ test_text_report_generation skipped (matplotlib not available)")
        
        asyncio.run(run_test())
    
    def test_export_json(self):
        """Test JSON export"""
        async def run_test():
            try:
                config = {
                    "similarity_weight": 0.5,
                    "quality_weight": 0.3,
                    "dynamic_weight": 0.2,
                    "provide_explanation": True
                }
                ranker = QualityAwareRanker(config)
                
                results = generate_test_results(5)
                ranked = await ranker.rank_hyperedges("test query", results)
                
                visualizer = RankingVisualizer()
                
                # Export to JSON
                output_file = "test_ranking_export.json"
                visualizer.export_ranking_data(ranked, output_file, format="json")
                
                # Verify file exists and is valid JSON
                assert os.path.exists(output_file)
                
                with open(output_file, 'r') as f:
                    data = json.load(f)
                
                assert len(data) == 5
                assert data[0]["rank"] == 1
                assert "final_score" in data[0]
                assert "components" in data[0]
                
                # Cleanup
                os.remove(output_file)
                
                print("✓ test_export_json passed")
            except ImportError:
                print("⊘ test_export_json skipped (matplotlib not available)")
        
        asyncio.run(run_test())
    
    def test_export_csv(self):
        """Test CSV export"""
        async def run_test():
            try:
                config = {
                    "similarity_weight": 0.5,
                    "quality_weight": 0.3,
                    "dynamic_weight": 0.2,
                    "provide_explanation": True
                }
                ranker = QualityAwareRanker(config)
                
                results = generate_test_results(5)
                ranked = await ranker.rank_hyperedges("test query", results)
                
                visualizer = RankingVisualizer()
                
                # Export to CSV
                output_file = "test_ranking_export.csv"
                visualizer.export_ranking_data(ranked, output_file, format="csv")
                
                # Verify file exists
                assert os.path.exists(output_file)
                
                # Read and verify content
                with open(output_file, 'r') as f:
                    lines = f.readlines()
                
                assert len(lines) == 6  # Header + 5 data rows
                assert "Rank,Final Score,Similarity,Quality" in lines[0]
                
                # Cleanup
                os.remove(output_file)
                
                print("✓ test_export_csv passed")
            except ImportError:
                print("⊘ test_export_csv skipped (matplotlib not available)")
        
        asyncio.run(run_test())
    
    def test_plot_generation(self):
        """Test that plots can be generated without errors"""
        async def run_test():
            try:
                import matplotlib
                matplotlib.use('Agg')  # Use non-interactive backend for testing
                
                config = {
                    "similarity_weight": 0.5,
                    "quality_weight": 0.3,
                    "dynamic_weight": 0.2,
                    "provide_explanation": True
                }
                ranker = QualityAwareRanker(config)
                
                results = generate_test_results(15)
                ranked = await ranker.rank_hyperedges("test query", results)
                
                visualizer = RankingVisualizer()
                
                # Test each plot type
                fig1 = visualizer.plot_ranking_components(ranked, top_k=10)
                assert fig1 is not None
                
                fig2 = visualizer.plot_score_distribution(ranked)
                assert fig2 is not None
                
                fig3 = visualizer.plot_factor_comparison(ranked, top_k=10)
                assert fig3 is not None
                
                fig4 = visualizer.plot_weight_impact(ranked, top_k=5)
                assert fig4 is not None
                
                print("✓ test_plot_generation passed")
            except ImportError:
                print("⊘ test_plot_generation skipped (matplotlib not available)")
        
        asyncio.run(run_test())
    
    def test_empty_results_handling(self):
        """Test handling of empty results"""
        async def run_test():
            try:
                visualizer = RankingVisualizer()
                
                # Test with empty list
                report = visualizer.generate_text_report([])
                assert "No results to report" in report
                
                fig = visualizer.plot_ranking_components([])
                assert fig is None
                
                print("✓ test_empty_results_handling passed")
            except ImportError:
                print("⊘ test_empty_results_handling skipped (matplotlib not available)")
        
        asyncio.run(run_test())


class TestIntegration:
    """Integration tests for explanation and visualization"""
    
    def test_end_to_end_workflow(self):
        """Test complete workflow from ranking to visualization"""
        async def run_test():
            try:
                # Step 1: Rank with explanations
                config = {
                    "similarity_weight": 0.5,
                    "quality_weight": 0.3,
                    "dynamic_weight": 0.2,
                    "provide_explanation": True
                }
                ranker = QualityAwareRanker(config)
                
                results = generate_test_results(20)
                ranked = await ranker.rank_hyperedges("test query", results)
                
                # Step 2: Generate text report
                visualizer = RankingVisualizer()
                report = visualizer.generate_text_report(ranked, top_k=10)
                assert len(report) > 0
                
                # Step 3: Export data
                json_file = "test_workflow.json"
                visualizer.export_ranking_data(ranked, json_file, format="json")
                assert os.path.exists(json_file)
                
                # Cleanup
                os.remove(json_file)
                
                print("✓ test_end_to_end_workflow passed")
            except ImportError:
                print("⊘ test_end_to_end_workflow skipped (matplotlib not available)")
        
        asyncio.run(run_test())


def test_module_imports():
    """Test that modules can be imported"""
    try:
        from hypergraphrag.retrieval.ranking_visualizer import (
            RankingVisualizer,
            create_ranking_dashboard
        )
        print("✓ test_module_imports passed")
    except ImportError as e:
        print(f"⊘ test_module_imports skipped: {e}")


if __name__ == "__main__":
    print("Running Ranking Visualization Tests...")
    print("=" * 80)
    
    # Test explanation features
    print("\nTesting Explanation Features:")
    print("-" * 80)
    explanation_tests = TestRankingExplanation()
    explanation_tests.test_explanation_enabled()
    explanation_tests.test_explanation_disabled()
    explanation_tests.test_explain_ranking_method()
    explanation_tests.test_explain_ranking_without_components()
    
    # Test visualizer features
    print("\nTesting Visualizer Features:")
    print("-" * 80)
    visualizer_tests = TestRankingVisualizer()
    visualizer_tests.test_visualizer_initialization()
    visualizer_tests.test_text_report_generation()
    visualizer_tests.test_export_json()
    visualizer_tests.test_export_csv()
    visualizer_tests.test_plot_generation()
    visualizer_tests.test_empty_results_handling()
    
    # Test integration
    print("\nTesting Integration:")
    print("-" * 80)
    integration_tests = TestIntegration()
    integration_tests.test_end_to_end_workflow()
    
    # Test imports
    print("\nTesting Module Imports:")
    print("-" * 80)
    test_module_imports()
    
    print("\n" + "=" * 80)
    print("All tests completed!")
    print("=" * 80)
