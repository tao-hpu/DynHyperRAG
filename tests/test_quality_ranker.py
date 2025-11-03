"""
Test suite for QualityAwareRanker

Tests the quality-aware ranking algorithm that combines similarity,
quality scores, and dynamic weights.
"""

import asyncio
from hypergraphrag.retrieval.quality_ranker import QualityAwareRanker, rank_by_quality


class TestQualityAwareRanker:
    """Test cases for QualityAwareRanker class"""
    
    def test_initialization_default_weights(self):
        """Test ranker initialization with default weights"""
        config = {}
        ranker = QualityAwareRanker(config)
        
        assert ranker.alpha == 0.5
        assert ranker.beta == 0.3
        assert ranker.gamma == 0.2
        assert ranker.normalize_scores is True
        assert ranker.provide_explanation is False
    
    def test_initialization_custom_weights(self):
        """Test ranker initialization with custom weights"""
        config = {
            "similarity_weight": 0.4,
            "quality_weight": 0.4,
            "dynamic_weight": 0.2,
            "normalize_scores": False,
            "provide_explanation": True
        }
        ranker = QualityAwareRanker(config)
        
        assert ranker.alpha == 0.4
        assert ranker.beta == 0.4
        assert ranker.gamma == 0.2
        assert ranker.normalize_scores is False
        assert ranker.provide_explanation is True
    
    def test_rank_empty_list(self):
        """Test ranking with empty hyperedge list"""
        async def run_test():
            ranker = QualityAwareRanker({})
            result = await ranker.rank_hyperedges("test query", [])
            assert result == []
        
        asyncio.run(run_test())
    
    def test_rank_single_hyperedge(self):
        """Test ranking with single hyperedge"""
        async def run_test():
            ranker = QualityAwareRanker({
                "similarity_weight": 0.5,
                "quality_weight": 0.3,
                "dynamic_weight": 0.2
            })
            
            hyperedges = [
                {
                    "hyperedge_name": "<hyperedge>Test relation",
                    "distance": 0.8,
                    "quality_score": 0.7,
                    "dynamic_weight": 0.9
                }
            ]
            
            result = await ranker.rank_hyperedges("test query", hyperedges)
            
            assert len(result) == 1
            assert "final_score" in result[0]
            
            # Expected: 0.5*0.8 + 0.3*0.7 + 0.2*0.9 = 0.4 + 0.21 + 0.18 = 0.79
            expected_score = 0.5 * 0.8 + 0.3 * 0.7 + 0.2 * 0.9
            assert abs(result[0]["final_score"] - expected_score) < 0.001
        
        asyncio.run(run_test())
    
    def test_rank_multiple_hyperedges(self):
        """Test ranking with multiple hyperedges"""
        async def run_test():
            ranker = QualityAwareRanker({
                "similarity_weight": 0.5,
                "quality_weight": 0.3,
                "dynamic_weight": 0.2
            })
            
            hyperedges = [
                {
                    "hyperedge_name": "<hyperedge>Low quality",
                    "distance": 0.9,
                    "quality_score": 0.3,
                    "dynamic_weight": 0.4
                },
                {
                    "hyperedge_name": "<hyperedge>High quality",
                    "distance": 0.7,
                    "quality_score": 0.9,
                    "dynamic_weight": 0.8
                },
                {
                    "hyperedge_name": "<hyperedge>Medium quality",
                    "distance": 0.6,
                    "quality_score": 0.6,
                    "dynamic_weight": 0.6
                }
            ]
            
            result = await ranker.rank_hyperedges("test query", hyperedges)
            
            assert len(result) == 3
            
            # Check all have final_score
            for he in result:
                assert "final_score" in he
            
            # Check sorted in descending order
            scores = [he["final_score"] for he in result]
            assert scores == sorted(scores, reverse=True)
            
            # High quality should rank first
            assert result[0]["hyperedge_name"] == "<hyperedge>High quality"
        
        asyncio.run(run_test())
    
    def test_rank_with_missing_fields(self):
        """Test ranking when some fields are missing (uses defaults)"""
        async def run_test():
            ranker = QualityAwareRanker({})
            
            hyperedges = [
                {
                    "hyperedge_name": "<hyperedge>Only similarity",
                    "distance": 0.8
                    # Missing quality_score and dynamic_weight
                },
                {
                    "hyperedge_name": "<hyperedge>Only quality",
                    "quality_score": 0.9
                    # Missing distance and dynamic_weight
                },
                {
                    "hyperedge_name": "<hyperedge>Complete",
                    "distance": 0.7,
                    "quality_score": 0.7,
                    "dynamic_weight": 0.7
                }
            ]
            
            result = await ranker.rank_hyperedges("test query", hyperedges)
            
            assert len(result) == 3
            
            # All should have final_score
            for he in result:
                assert "final_score" in he
                assert 0.0 <= he["final_score"] <= 1.0
        
        asyncio.run(run_test())
    
    def test_rank_with_explanation(self):
        """Test ranking with explanation enabled"""
        async def run_test():
            ranker = QualityAwareRanker({
                "similarity_weight": 0.5,
                "quality_weight": 0.3,
                "dynamic_weight": 0.2,
                "provide_explanation": True
            })
            
            hyperedges = [
                {
                    "hyperedge_name": "<hyperedge>Test",
                    "distance": 0.8,
                    "quality_score": 0.7,
                    "dynamic_weight": 0.9
                }
            ]
            
            result = await ranker.rank_hyperedges("test query", hyperedges)
            
            assert len(result) == 1
            assert "ranking_components" in result[0]
            
            components = result[0]["ranking_components"]
            assert "similarity" in components
            assert "quality" in components
            assert "dynamic_weight" in components
            assert "weights" in components
            assert "computation" in components
            
            # Check values
            assert components["similarity"] == 0.8
            assert components["quality"] == 0.7
            assert components["dynamic_weight"] == 0.9
        
        asyncio.run(run_test())
    
    def test_rank_with_weight_fallback(self):
        """Test that quality_score is used as fallback for dynamic_weight, then original weight"""
        async def run_test():
            ranker = QualityAwareRanker({})
            
            # Test 1: quality_score is used as fallback for dynamic_weight
            hyperedges1 = [
                {
                    "hyperedge_name": "<hyperedge>With quality score",
                    "distance": 0.8,
                    "quality_score": 0.7,
                    "weight": 85.0  # Should NOT be used since quality_score exists
                }
            ]
            
            result1 = await ranker.rank_hyperedges("test query", hyperedges1)
            
            assert len(result1) == 1
            # Expected: 0.5*0.8 + 0.3*0.7 + 0.2*0.7 = 0.4 + 0.21 + 0.14 = 0.75
            expected_score1 = 0.5 * 0.8 + 0.3 * 0.7 + 0.2 * 0.7
            assert abs(result1[0]["final_score"] - expected_score1) < 0.001
            
            # Test 2: original weight is used when quality_score is missing
            hyperedges2 = [
                {
                    "hyperedge_name": "<hyperedge>With original weight only",
                    "distance": 0.8,
                    "weight": 85.0  # Should be normalized to 0.85
                }
            ]
            
            result2 = await ranker.rank_hyperedges("test query", hyperedges2)
            
            assert len(result2) == 1
            # Expected: 0.5*0.8 + 0.3*0.5 + 0.2*0.85 = 0.4 + 0.15 + 0.17 = 0.72
            expected_score2 = 0.5 * 0.8 + 0.3 * 0.5 + 0.2 * 0.85
            assert abs(result2[0]["final_score"] - expected_score2) < 0.001
        
        asyncio.run(run_test())
    
    def test_rank_normalization(self):
        """Test score normalization to [0, 1]"""
        async def run_test():
            ranker = QualityAwareRanker({
                "similarity_weight": 1.0,
                "quality_weight": 1.0,
                "dynamic_weight": 1.0,
                "normalize_scores": True
            })
            
            hyperedges = [
                {
                    "hyperedge_name": "<hyperedge>High scores",
                    "distance": 1.0,
                    "quality_score": 1.0,
                    "dynamic_weight": 1.0
                }
            ]
            
            result = await ranker.rank_hyperedges("test query", hyperedges)
            
            # Without normalization, score would be 3.0
            # With normalization, should be capped at 1.0
            assert result[0]["final_score"] == 1.0
        
        asyncio.run(run_test())
    
    def test_set_weights(self):
        """Test updating weights after initialization"""
        ranker = QualityAwareRanker({})
        
        ranker.set_weights(0.6, 0.3, 0.1)
        
        assert ranker.alpha == 0.6
        assert ranker.beta == 0.3
        assert ranker.gamma == 0.1
    
    def test_get_weights(self):
        """Test getting current weights"""
        ranker = QualityAwareRanker({
            "similarity_weight": 0.4,
            "quality_weight": 0.4,
            "dynamic_weight": 0.2
        })
        
        weights = ranker.get_weights()
        
        assert weights["alpha"] == 0.4
        assert weights["beta"] == 0.4
        assert weights["gamma"] == 0.2
    
    def test_explain_ranking(self):
        """Test ranking explanation generation"""
        ranker = QualityAwareRanker({
            "similarity_weight": 0.5,
            "quality_weight": 0.3,
            "dynamic_weight": 0.2,
            "provide_explanation": True
        })
        
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
        
        assert "Final Score: 0.79" in explanation
        assert "Similarity: 0.8" in explanation
        assert "Quality: 0.7" in explanation
        assert "Dynamic Weight: 0.9" in explanation
    
    def test_convenience_function(self):
        """Test the convenience rank_by_quality function"""
        async def run_test():
            hyperedges = [
                {
                    "hyperedge_name": "<hyperedge>Test 1",
                    "distance": 0.9,
                    "quality_score": 0.5,
                    "dynamic_weight": 0.6
                },
                {
                    "hyperedge_name": "<hyperedge>Test 2",
                    "distance": 0.7,
                    "quality_score": 0.9,
                    "dynamic_weight": 0.8
                }
            ]
            
            result = await rank_by_quality(
                hyperedges,
                query="test query",
                similarity_weight=0.5,
                quality_weight=0.3,
                dynamic_weight=0.2
            )
            
            assert len(result) == 2
            assert all("final_score" in he for he in result)
            
            # Test 2 should rank higher due to better quality and dynamic weight
            assert result[0]["hyperedge_name"] == "<hyperedge>Test 2"
        
        asyncio.run(run_test())


class TestRankingScenarios:
    """Test realistic ranking scenarios"""
    
    def test_quality_vs_similarity_tradeoff(self):
        """Test ranking when quality and similarity conflict"""
        async def run_test():
            ranker = QualityAwareRanker({
                "similarity_weight": 0.5,
                "quality_weight": 0.5,
                "dynamic_weight": 0.0
            })
            
            hyperedges = [
                {
                    "hyperedge_name": "<hyperedge>High similarity, low quality",
                    "distance": 0.95,
                    "quality_score": 0.3,
                    "dynamic_weight": 0.5
                },
                {
                    "hyperedge_name": "<hyperedge>Low similarity, high quality",
                    "distance": 0.6,
                    "quality_score": 0.95,
                    "dynamic_weight": 0.5
                }
            ]
            
            result = await ranker.rank_hyperedges("test query", hyperedges)
            
            # With equal weights, high quality should win
            # Score 1: 0.5*0.95 + 0.5*0.3 = 0.625
            # Score 2: 0.5*0.6 + 0.5*0.95 = 0.775
            assert result[0]["hyperedge_name"] == "<hyperedge>Low similarity, high quality"
        
        asyncio.run(run_test())
    
    def test_dynamic_weight_boost(self):
        """Test that dynamic weight can boost ranking"""
        async def run_test():
            ranker = QualityAwareRanker({
                "similarity_weight": 0.4,
                "quality_weight": 0.3,
                "dynamic_weight": 0.3
            })
            
            hyperedges = [
                {
                    "hyperedge_name": "<hyperedge>No feedback",
                    "distance": 0.8,
                    "quality_score": 0.7,
                    "dynamic_weight": 0.5
                },
                {
                    "hyperedge_name": "<hyperedge>Positive feedback",
                    "distance": 0.75,
                    "quality_score": 0.65,
                    "dynamic_weight": 0.95  # Boosted by positive feedback
                }
            ]
            
            result = await ranker.rank_hyperedges("test query", hyperedges)
            
            # Positive feedback should boost the second hyperedge to top
            # Score 1: 0.4*0.8 + 0.3*0.7 + 0.3*0.5 = 0.68
            # Score 2: 0.4*0.75 + 0.3*0.65 + 0.3*0.95 = 0.78
            assert result[0]["hyperedge_name"] == "<hyperedge>Positive feedback"
        
        asyncio.run(run_test())
    
    def test_similarity_dominant_ranking(self):
        """Test ranking when similarity is heavily weighted"""
        async def run_test():
            ranker = QualityAwareRanker({
                "similarity_weight": 0.8,
                "quality_weight": 0.1,
                "dynamic_weight": 0.1
            })
            
            hyperedges = [
                {
                    "hyperedge_name": "<hyperedge>Very relevant",
                    "distance": 0.95,
                    "quality_score": 0.4,
                    "dynamic_weight": 0.4
                },
                {
                    "hyperedge_name": "<hyperedge>High quality but less relevant",
                    "distance": 0.6,
                    "quality_score": 0.9,
                    "dynamic_weight": 0.9
                }
            ]
            
            result = await ranker.rank_hyperedges("test query", hyperedges)
            
            # With high similarity weight, relevance should dominate
            # Score 1: 0.8*0.95 + 0.1*0.4 + 0.1*0.4 = 0.84
            # Score 2: 0.8*0.6 + 0.1*0.9 + 0.1*0.9 = 0.66
            assert result[0]["hyperedge_name"] == "<hyperedge>Very relevant"
        
        asyncio.run(run_test())


def test_module_imports():
    """Test that module can be imported correctly"""
    from hypergraphrag.retrieval.quality_ranker import (
        QualityAwareRanker,
        rank_by_quality
    )
    
    assert QualityAwareRanker is not None
    assert rank_by_quality is not None


if __name__ == "__main__":
    print("Running QualityAwareRanker tests...")
    
    # Run all tests
    test_suite = TestQualityAwareRanker()
    test_suite.test_initialization_default_weights()
    test_suite.test_initialization_custom_weights()
    test_suite.test_rank_empty_list()
    test_suite.test_rank_single_hyperedge()
    test_suite.test_rank_multiple_hyperedges()
    test_suite.test_rank_with_missing_fields()
    test_suite.test_rank_with_explanation()
    test_suite.test_rank_with_weight_fallback()
    test_suite.test_rank_normalization()
    test_suite.test_set_weights()
    test_suite.test_get_weights()
    test_suite.test_explain_ranking()
    test_suite.test_convenience_function()
    
    scenario_tests = TestRankingScenarios()
    scenario_tests.test_quality_vs_similarity_tradeoff()
    scenario_tests.test_dynamic_weight_boost()
    scenario_tests.test_similarity_dominant_ranking()
    
    test_module_imports()
    
    print("\n✅ All tests passed!")
