"""
Tests for baseline methods implementation.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from hypergraphrag.evaluation.baselines import BaselineMethods, StaticHyperGraphRAG


class TestBaselineMethods:
    """Test baseline methods for hyperedge quality assessment."""
    
    @pytest.fixture
    def mock_graph_storage(self):
        """Create mock graph storage."""
        storage = AsyncMock()
        storage.get_node = AsyncMock()
        storage.node_degree = AsyncMock()
        return storage
    
    @pytest.fixture
    def baseline_methods(self, mock_graph_storage):
        """Create BaselineMethods instance."""
        return BaselineMethods(mock_graph_storage)
    
    @pytest.mark.asyncio
    async def test_llm_confidence_baseline(self, baseline_methods, mock_graph_storage):
        """Test LLM confidence baseline method."""
        # Mock node data
        mock_graph_storage.get_node.return_value = {
            'weight': 75.0,
            'hyperedge': 'test hyperedge'
        }
        
        score = await baseline_methods.llm_confidence_baseline('test_hyperedge')
        
        assert 0.0 <= score <= 1.0
        assert score == 0.75  # 75/100
        mock_graph_storage.get_node.assert_called_once_with('test_hyperedge')
    
    @pytest.mark.asyncio
    async def test_rule_based_baseline(self, baseline_methods, mock_graph_storage):
        """Test rule-based baseline method."""
        # Mock node data and degree
        mock_graph_storage.get_node.return_value = {
            'hyperedge': 'This is a test hyperedge with some content to evaluate quality based on length and connectivity'
        }
        mock_graph_storage.node_degree.return_value = 3
        
        score = await baseline_methods.rule_based_baseline('test_hyperedge')
        
        assert 0.0 <= score <= 1.0
        mock_graph_storage.get_node.assert_called_once_with('test_hyperedge')
        mock_graph_storage.node_degree.assert_called_once_with('test_hyperedge')
    
    @pytest.mark.asyncio
    async def test_random_baseline(self, baseline_methods):
        """Test random baseline method."""
        score1 = await baseline_methods.random_baseline('test_hyperedge_1')
        score2 = await baseline_methods.random_baseline('test_hyperedge_2')
        
        assert 0.0 <= score1 <= 1.0
        assert 0.0 <= score2 <= 1.0
        
        # Same ID should give same random score (reproducible)
        score1_repeat = await baseline_methods.random_baseline('test_hyperedge_1')
        assert score1 == score1_repeat
    
    @pytest.mark.asyncio
    async def test_compute_baseline_scores(self, baseline_methods, mock_graph_storage):
        """Test computing baseline scores for multiple hyperedges."""
        # Mock node data
        mock_graph_storage.get_node.return_value = {
            'weight': 50.0,
            'hyperedge': 'test content'
        }
        mock_graph_storage.node_degree.return_value = 2
        
        hyperedge_ids = ['he1', 'he2', 'he3']
        results = await baseline_methods.compute_baseline_scores(hyperedge_ids, 'all')
        
        assert 'llm_confidence' in results
        assert 'rule_based' in results
        assert 'random' in results
        
        for method_results in results.values():
            assert len(method_results) == 3
            for he_id in hyperedge_ids:
                assert he_id in method_results
                assert 0.0 <= method_results[he_id] <= 1.0


class TestStaticHyperGraphRAG:
    """Test static HyperGraphRAG baseline."""
    
    @pytest.fixture
    def mock_components(self):
        """Create mock components for StaticHyperGraphRAG."""
        graph_storage = AsyncMock()
        entities_vdb = AsyncMock()
        hyperedges_vdb = AsyncMock()
        text_chunks_db = AsyncMock()
        embedding_func = AsyncMock()
        llm_func = AsyncMock()
        
        return {
            'graph_storage': graph_storage,
            'entities_vdb': entities_vdb,
            'hyperedges_vdb': hyperedges_vdb,
            'text_chunks_db': text_chunks_db,
            'embedding_func': embedding_func,
            'llm_func': llm_func
        }
    
    @pytest.fixture
    def static_rag(self, mock_components):
        """Create StaticHyperGraphRAG instance."""
        return StaticHyperGraphRAG(**mock_components)
    
    @pytest.mark.asyncio
    async def test_retrieve(self, static_rag, mock_components):
        """Test static retrieval method."""
        # Mock vector search results
        mock_components['hyperedges_vdb'].query.return_value = [
            {'id': 'he1', 'distance': 0.1, 'hyperedge': 'content1'},
            {'id': 'he2', 'distance': 0.3, 'hyperedge': 'content2'},
            {'id': 'he3', 'distance': 0.2, 'hyperedge': 'content3'}
        ]
        
        results = await static_rag.retrieve('test query', top_k=2)
        
        assert len(results) == 2
        assert results[0]['distance'] == 0.1  # Should be sorted by distance
        assert results[1]['distance'] == 0.2
        
        # Check metadata
        for result in results:
            assert result['method'] == 'static_hypergraphrag'
            assert result['quality_score'] is None
            assert result['dynamic_weight'] is None
            assert result['entity_filtered'] is False
    
    def test_config_disables_dynamic_features(self, static_rag):
        """Test that static RAG disables dynamic features."""
        assert static_rag.config['enable_quality_ranking'] is False
        assert static_rag.config['enable_dynamic_updates'] is False
        assert static_rag.config['enable_entity_filtering'] is False
        assert static_rag.config['enable_hyperedge_refinement'] is False


if __name__ == "__main__":
    pytest.main([__file__])