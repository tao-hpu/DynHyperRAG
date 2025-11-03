"""
Tests for Efficient Retrieval Integration

This test file verifies that the efficient retrieval features are properly
integrated into the query flow.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from hypergraphrag.operate import _get_edge_data, _get_node_data, _build_query_context
from hypergraphrag.base import QueryParam


@pytest.fixture
def mock_graph():
    """Mock graph storage."""
    graph = AsyncMock()
    graph.get_node = AsyncMock(return_value={
        "role": "hyperedge",
        "weight": 1.0,
        "source_id": "chunk1",
        "quality_score": 0.8,
        "dynamic_weight": 1.2
    })
    graph.get_node_edges = AsyncMock(return_value=[
        ("hyperedge1", "entity1"),
        ("hyperedge1", "entity2")
    ])
    graph.node_degree = AsyncMock(return_value=5)
    return graph


@pytest.fixture
def mock_vdb():
    """Mock vector database."""
    vdb = AsyncMock()
    vdb.query = AsyncMock(return_value=[
        {"hyperedge_name": "hyperedge1", "distance": 0.9},
        {"hyperedge_name": "hyperedge2", "distance": 0.8},
        {"hyperedge_name": "hyperedge3", "distance": 0.7}
    ])
    return vdb


@pytest.fixture
def mock_text_chunks_db():
    """Mock text chunks database."""
    db = AsyncMock()
    db.get_by_id = AsyncMock(return_value={
        "content": "Sample text content",
        "chunk_order_index": 0
    })
    return db


@pytest.fixture
def query_param():
    """Query parameters."""
    return QueryParam(
        mode="hybrid",
        top_k=10,
        max_token_for_text_unit=4000,
        max_token_for_global_context=4000,
        max_token_for_local_context=4000
    )


@pytest.fixture
def retrieval_config():
    """Retrieval configuration."""
    return {
        "addon_params": {
            "retrieval_config": {
                "entity_filter_enabled": True,
                "domain": "medical",
                "entity_taxonomy": {
                    "medical": ["disease", "symptom", "treatment"]
                },
                "similarity_weight": 0.5,
                "quality_weight": 0.3,
                "dynamic_weight": 0.2
            },
            "lite_config": {
                "enabled": False,
                "cache_size": 1000
            }
        },
        "llm_model_func": AsyncMock(),
        "embedding_func": AsyncMock()
    }


@pytest.mark.asyncio
async def test_get_edge_data_without_config(mock_graph, mock_vdb, mock_text_chunks_db, query_param):
    """Test _get_edge_data works without configuration (backward compatibility)."""
    
    result = await _get_edge_data(
        "test query",
        mock_graph,
        mock_vdb,
        mock_text_chunks_db,
        query_param
    )
    
    # Should return tuple of 4 elements
    assert len(result) == 4
    entities_context, relations_context, text_units_context, hyperedges = result
    
    # Should have called vector database
    mock_vdb.query.assert_called_once()


@pytest.mark.asyncio
async def test_get_edge_data_with_entity_filtering(mock_graph, mock_vdb, mock_text_chunks_db, query_param, retrieval_config):
    """Test _get_edge_data with entity type filtering enabled."""
    
    # Mock entity filter
    with patch('hypergraphrag.operate.EntityTypeFilter') as MockFilter:
        mock_filter = MockFilter.return_value
        mock_filter.identify_relevant_types = AsyncMock(return_value=["disease", "symptom"])
        mock_filter.filter_hyperedges_by_type = AsyncMock(return_value=["hyperedge1", "hyperedge2"])
        
        result = await _get_edge_data(
            "test query",
            mock_graph,
            mock_vdb,
            mock_text_chunks_db,
            query_param,
            global_config=retrieval_config,
            query="What are the symptoms of diabetes?"
        )
        
        # Should have called entity filter
        mock_filter.identify_relevant_types.assert_called_once()
        mock_filter.filter_hyperedges_by_type.assert_called_once()


@pytest.mark.asyncio
async def test_get_edge_data_with_quality_ranking(mock_graph, mock_vdb, mock_text_chunks_db, query_param, retrieval_config):
    """Test _get_edge_data with quality-aware ranking enabled."""
    
    # Mock quality ranker
    with patch('hypergraphrag.operate.QualityAwareRanker') as MockRanker:
        mock_ranker = MockRanker.return_value
        mock_ranker.rank_hyperedges = AsyncMock(return_value=[
            {"hyperedge": "hyperedge1", "rank": 0.9, "final_score": 0.85},
            {"hyperedge": "hyperedge2", "rank": 0.8, "final_score": 0.75}
        ])
        
        result = await _get_edge_data(
            "test query",
            mock_graph,
            mock_vdb,
            mock_text_chunks_db,
            query_param,
            global_config=retrieval_config,
            query="What are the symptoms of diabetes?"
        )
        
        # Should have called quality ranker
        mock_ranker.rank_hyperedges.assert_called_once()


@pytest.mark.asyncio
async def test_get_edge_data_with_lite_mode(mock_graph, mock_vdb, mock_text_chunks_db, query_param, retrieval_config):
    """Test _get_edge_data with lite retriever mode enabled."""
    
    # Enable lite mode
    retrieval_config["addon_params"]["lite_config"]["enabled"] = True
    
    # Mock lite retriever
    with patch('hypergraphrag.operate.LiteRetriever') as MockLite:
        mock_lite = MockLite.return_value
        mock_lite.retrieve = AsyncMock(return_value=[
            {"hyperedge_name": "hyperedge1", "distance": 0.9, "simple_quality": 0.8}
        ])
        
        result = await _get_edge_data(
            "test query",
            mock_graph,
            mock_vdb,
            mock_text_chunks_db,
            query_param,
            global_config=retrieval_config,
            query="What are the symptoms of diabetes?"
        )
        
        # Should have used lite retriever instead of standard vdb
        mock_lite.retrieve.assert_called_once()
        # Standard vdb should not be called
        mock_vdb.query.assert_not_called()


@pytest.mark.asyncio
async def test_get_node_data_without_config(mock_graph, mock_vdb, mock_text_chunks_db, query_param):
    """Test _get_node_data works without configuration (backward compatibility)."""
    
    # Mock entity vector results
    mock_vdb.query = AsyncMock(return_value=[
        {"entity_name": "entity1", "distance": 0.9}
    ])
    
    # Mock graph methods
    mock_graph.get_node = AsyncMock(return_value={
        "role": "entity",
        "entity_type": "disease",
        "description": "Test entity",
        "source_id": "chunk1"
    })
    mock_graph.get_node_edges = AsyncMock(return_value=[])
    
    result = await _get_node_data(
        query_keywords="test query",
        knowledge_graph_inst=mock_graph,
        entities_vdb=mock_vdb,
        text_chunks_db=mock_text_chunks_db,
        query_param=query_param
    )
    
    # Should return tuple of 4 elements
    assert len(result) == 4


@pytest.mark.asyncio
async def test_get_node_data_with_quality_ranking(mock_graph, mock_vdb, mock_text_chunks_db, query_param, retrieval_config):
    """Test _get_node_data with quality-aware ranking for related hyperedges."""
    
    # Mock entity vector results
    mock_vdb.query = AsyncMock(return_value=[
        {"entity_name": "entity1", "distance": 0.9}
    ])
    
    # Mock graph methods
    mock_graph.get_node = AsyncMock(return_value={
        "role": "entity",
        "entity_type": "disease",
        "description": "Test entity",
        "source_id": "chunk1"
    })
    mock_graph.get_node_edges = AsyncMock(return_value=[
        ("hyperedge1", "entity1")
    ])
    mock_graph.get_edge = AsyncMock(return_value={
        "weight": 1.0,
        "source_id": "chunk1"
    })
    mock_graph.edge_degree = AsyncMock(return_value=3)
    
    # Mock quality ranker
    with patch('hypergraphrag.operate.QualityAwareRanker') as MockRanker:
        mock_ranker = MockRanker.return_value
        mock_ranker.rank_hyperedges = AsyncMock(return_value=[
            {"description": "hyperedge1", "rank": 3, "final_score": 0.85}
        ])
        
        result = await _get_node_data(
            query_keywords="test query",
            knowledge_graph_inst=mock_graph,
            entities_vdb=mock_vdb,
            text_chunks_db=mock_text_chunks_db,
            query_param=query_param,
            global_config=retrieval_config,
            query="What are the symptoms of diabetes?"
        )
        
        # Should have called quality ranker for related hyperedges
        mock_ranker.rank_hyperedges.assert_called_once()


@pytest.mark.asyncio
async def test_fallback_on_import_error(mock_graph, mock_vdb, mock_text_chunks_db, query_param, retrieval_config):
    """Test that system falls back gracefully when retrieval modules are not available."""
    
    # Mock import error
    with patch('hypergraphrag.operate.EntityTypeFilter', side_effect=ImportError("Module not found")):
        result = await _get_edge_data(
            "test query",
            mock_graph,
            mock_vdb,
            mock_text_chunks_db,
            query_param,
            global_config=retrieval_config,
            query="What are the symptoms of diabetes?"
        )
        
        # Should still return results (fallback to standard retrieval)
        assert len(result) == 4


@pytest.mark.asyncio
async def test_fallback_on_filtering_error(mock_graph, mock_vdb, mock_text_chunks_db, query_param, retrieval_config):
    """Test that system falls back gracefully when filtering fails."""
    
    # Mock entity filter that raises an error
    with patch('hypergraphrag.operate.EntityTypeFilter') as MockFilter:
        mock_filter = MockFilter.return_value
        mock_filter.identify_relevant_types = AsyncMock(side_effect=Exception("Filtering failed"))
        
        result = await _get_edge_data(
            "test query",
            mock_graph,
            mock_vdb,
            mock_text_chunks_db,
            query_param,
            global_config=retrieval_config,
            query="What are the symptoms of diabetes?"
        )
        
        # Should still return results (fallback to standard retrieval)
        assert len(result) == 4


@pytest.mark.asyncio
async def test_fallback_when_too_few_results(mock_graph, mock_vdb, mock_text_chunks_db, query_param, retrieval_config):
    """Test that system falls back when entity filtering returns too few results."""
    
    # Mock entity filter that returns very few results
    with patch('hypergraphrag.operate.EntityTypeFilter') as MockFilter:
        mock_filter = MockFilter.return_value
        mock_filter.identify_relevant_types = AsyncMock(return_value=["disease"])
        mock_filter.filter_hyperedges_by_type = AsyncMock(return_value=["hyperedge1"])  # Only 1 result
        
        result = await _get_edge_data(
            "test query",
            mock_graph,
            mock_vdb,
            mock_text_chunks_db,
            query_param,
            global_config=retrieval_config,
            query="What are the symptoms of diabetes?"
        )
        
        # Should have fallen back to unfiltered results
        # (implementation logs warning and uses original results)
        assert len(result) == 4


def test_backward_compatibility():
    """Test that new parameters are optional and don't break existing code."""
    
    # This should not raise any errors
    query_param = QueryParam(mode="hybrid", top_k=10)
    assert query_param.mode == "hybrid"
    assert query_param.top_k == 10


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
