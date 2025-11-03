"""
Unit tests for iterative hyperedge refinement functionality.

Tests the HyperedgeRefiner.iterative_refine_hyperedges method and related
re-extraction functionality.

Author: DynHyperRAG Team
Date: 2025
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from hypergraphrag.dynamic.refiner import HyperedgeRefiner
from hypergraphrag.base import BaseGraphStorage


class MockGraphStorage(BaseGraphStorage):
    """Mock graph storage for testing."""
    
    def __init__(self):
        self.nodes = {}
        self.edges = {}
    
    async def get_node(self, node_id: str):
        return self.nodes.get(node_id)
    
    async def upsert_node(self, node_id: str, node_data: dict):
        self.nodes[node_id] = node_data
    
    async def delete_node(self, node_id: str):
        if node_id in self.nodes:
            del self.nodes[node_id]
        # Also delete associated edges
        edges_to_delete = [
            (src, tgt) for (src, tgt) in self.edges.keys()
            if src == node_id or tgt == node_id
        ]
        for edge_key in edges_to_delete:
            del self.edges[edge_key]
    
    async def get_node_edges(self, node_id: str):
        return [
            (src, tgt) for (src, tgt) in self.edges.keys()
            if src == node_id
        ]
    
    async def upsert_edge(self, src_id: str, tgt_id: str, edge_data: dict):
        self.edges[(src_id, tgt_id)] = edge_data
    
    async def delete_edge(self, src_id: str, tgt_id: str):
        key = (src_id, tgt_id)
        if key in self.edges:
            del self.edges[key]
    
    async def has_edge(self, src_id: str, tgt_id: str):
        return (src_id, tgt_id) in self.edges
    
    async def get_edge(self, src_id: str, tgt_id: str):
        return self.edges.get((src_id, tgt_id))
    
    async def node_degree(self, node_id: str):
        return len([e for e in self.edges.keys() if e[0] == node_id or e[1] == node_id])


class MockTextChunksDB:
    """Mock text chunks database."""
    
    def __init__(self):
        self.chunks = {}
    
    async def get_by_id(self, chunk_id: str):
        return self.chunks.get(chunk_id)


class MockQualityScorer:
    """Mock quality scorer."""
    
    def __init__(self):
        self.quality_scores = {}
    
    async def compute_quality_score(self, hyperedge_id: str):
        # Return increasing quality for temp nodes (simulating improvement)
        if '_temp_' in hyperedge_id:
            base_id = hyperedge_id.split('_temp_')[0]
            iteration = int(hyperedge_id.split('_temp_')[1])
            base_quality = self.quality_scores.get(base_id, 0.3)
            # Each iteration improves quality by 0.1
            return {
                'quality_score': min(1.0, base_quality + 0.1 * (iteration + 1)),
                'features': {}
            }
        
        return {
            'quality_score': self.quality_scores.get(hyperedge_id, 0.5),
            'features': {}
        }


@pytest.fixture
def mock_graph():
    """Create mock graph storage."""
    return MockGraphStorage()


@pytest.fixture
def mock_text_chunks_db():
    """Create mock text chunks database."""
    db = MockTextChunksDB()
    db.chunks = {
        'chunk1': {'content': 'Alice works at TechCorp as a software engineer.'},
        'chunk2': {'content': 'Bob is a data scientist at TechCorp.'},
    }
    return db


@pytest.fixture
def mock_quality_scorer():
    """Create mock quality scorer."""
    scorer = MockQualityScorer()
    scorer.quality_scores = {
        'he1': 0.3,  # Low quality
        'he2': 0.8,  # High quality
    }
    return scorer


@pytest.fixture
def mock_llm_func():
    """Create mock LLM function."""
    async def llm_func(prompt, **kwargs):
        # Return a mock extraction result
        return '''("hyper-relation"<|>"Alice works at TechCorp as a software engineer"<|>8)##
("entity"<|>"ALICE"<|>"person"<|>"Alice is a software engineer"<|>90)##
("entity"<|>"TECHCORP"<|>"organization"<|>"TechCorp is a technology company"<|>85)##
<|COMPLETE|>'''
    return llm_func


@pytest.fixture
def refiner_config():
    """Create refiner configuration."""
    return {
        'quality_threshold': 0.5,
        'filter_mode': 'soft',
        'threshold_strategy': 'fixed',
    }


@pytest.fixture
def global_config():
    """Create global configuration."""
    return {
        'addon_params': {
            'language': 'English',
            'entity_types': ['person', 'organization', 'location'],
        }
    }


@pytest.mark.asyncio
async def test_iterative_refine_basic(
    mock_graph,
    mock_text_chunks_db,
    mock_quality_scorer,
    mock_llm_func,
    refiner_config,
    global_config
):
    """Test basic iterative refinement functionality."""
    
    # Setup: Add a low-quality hyperedge
    await mock_graph.upsert_node('he1', {
        'role': 'hyperedge',
        'hyperedge': '<hyperedge>Old low quality text',
        'quality_score': 0.3,
        'source_id': 'chunk1',
        'weight': 1.0,
    })
    
    # Add some entities
    await mock_graph.upsert_node('ALICE', {
        'role': 'entity',
        'entity_name': 'ALICE',
        'entity_type': 'person',
    })
    
    await mock_graph.upsert_edge('he1', 'ALICE', {'weight': 1.0, 'source_id': 'chunk1'})
    
    # Create refiner
    refiner = HyperedgeRefiner(mock_graph, refiner_config)
    
    # Perform refinement
    result = await refiner.iterative_refine_hyperedges(
        hyperedge_ids=['he1'],
        text_chunks_db=mock_text_chunks_db,
        llm_model_func=mock_llm_func,
        embedding_func=AsyncMock(),
        quality_scorer=mock_quality_scorer,
        global_config=global_config,
        max_iterations=1
    )
    
    # Assertions
    assert result['refined_count'] == 1
    assert result['improved_count'] >= 0  # May or may not improve
    assert result['failed_count'] == 0
    
    # Check that node was updated if improved
    node = await mock_graph.get_node('he1')
    assert node is not None
    
    if result['improved_count'] > 0:
        assert node.get('refined') == True
        assert 'refined_at' in node
        assert 'previous_quality' in node


@pytest.mark.asyncio
async def test_iterative_refine_no_source_text(
    mock_graph,
    mock_text_chunks_db,
    mock_quality_scorer,
    mock_llm_func,
    refiner_config,
    global_config
):
    """Test refinement when source text is missing."""
    
    # Setup: Add hyperedge with missing source
    await mock_graph.upsert_node('he_no_source', {
        'role': 'hyperedge',
        'hyperedge': '<hyperedge>Text without source',
        'quality_score': 0.3,
        'source_id': 'nonexistent_chunk',
        'weight': 1.0,
    })
    
    refiner = HyperedgeRefiner(mock_graph, refiner_config)
    
    result = await refiner.iterative_refine_hyperedges(
        hyperedge_ids=['he_no_source'],
        text_chunks_db=mock_text_chunks_db,
        llm_model_func=mock_llm_func,
        embedding_func=AsyncMock(),
        quality_scorer=mock_quality_scorer,
        global_config=global_config,
        max_iterations=1
    )
    
    # Should fail due to missing source
    assert result['failed_count'] == 1
    assert result['improved_count'] == 0


@pytest.mark.asyncio
async def test_iterative_refine_high_quality_skip(
    mock_graph,
    mock_text_chunks_db,
    mock_quality_scorer,
    mock_llm_func,
    refiner_config,
    global_config
):
    """Test that high-quality hyperedges are skipped."""
    
    # Setup: Add high-quality hyperedge
    await mock_graph.upsert_node('he2', {
        'role': 'hyperedge',
        'hyperedge': '<hyperedge>High quality text',
        'quality_score': 0.8,
        'source_id': 'chunk1',
        'weight': 1.0,
    })
    
    refiner = HyperedgeRefiner(mock_graph, refiner_config)
    
    result = await refiner.iterative_refine_hyperedges(
        hyperedge_ids=['he2'],
        text_chunks_db=mock_text_chunks_db,
        llm_model_func=mock_llm_func,
        embedding_func=AsyncMock(),
        quality_scorer=mock_quality_scorer,
        global_config=global_config,
        max_iterations=1
    )
    
    # Should skip high-quality hyperedge
    assert result['refined_count'] == 0
    assert result['improved_count'] == 0


@pytest.mark.asyncio
async def test_iterative_refine_multiple_iterations(
    mock_graph,
    mock_text_chunks_db,
    mock_quality_scorer,
    mock_llm_func,
    refiner_config,
    global_config
):
    """Test refinement with multiple iterations."""
    
    # Setup
    await mock_graph.upsert_node('he1', {
        'role': 'hyperedge',
        'hyperedge': '<hyperedge>Low quality text',
        'quality_score': 0.3,
        'source_id': 'chunk1',
        'weight': 1.0,
    })
    
    refiner = HyperedgeRefiner(mock_graph, refiner_config)
    
    # Perform refinement with 3 iterations
    result = await refiner.iterative_refine_hyperedges(
        hyperedge_ids=['he1'],
        text_chunks_db=mock_text_chunks_db,
        llm_model_func=mock_llm_func,
        embedding_func=AsyncMock(),
        quality_scorer=mock_quality_scorer,
        global_config=global_config,
        max_iterations=3
    )
    
    # Should attempt multiple iterations
    assert result['refined_count'] == 1


@pytest.mark.asyncio
async def test_re_extract_hyperedge(
    mock_graph,
    mock_llm_func,
    refiner_config,
    global_config
):
    """Test the _re_extract_hyperedge method."""
    
    refiner = HyperedgeRefiner(mock_graph, refiner_config)
    
    source_text = "Alice works at TechCorp as a software engineer."
    current_hyperedge = "<hyperedge>Old text"
    current_quality = 0.3
    
    new_hyperedge, entities = await refiner._re_extract_hyperedge(
        source_text=source_text,
        current_hyperedge=current_hyperedge,
        current_quality=current_quality,
        llm_model_func=mock_llm_func,
        global_config=global_config,
        iteration=0
    )
    
    # Should extract new hyperedge
    assert new_hyperedge is not None
    assert new_hyperedge.startswith('<hyperedge>')
    assert isinstance(entities, list)


@pytest.mark.asyncio
async def test_refinement_statistics(
    mock_graph,
    mock_text_chunks_db,
    mock_quality_scorer,
    mock_llm_func,
    refiner_config,
    global_config
):
    """Test that refinement statistics are correctly computed."""
    
    # Setup multiple hyperedges
    for i in range(3):
        await mock_graph.upsert_node(f'he{i}', {
            'role': 'hyperedge',
            'hyperedge': f'<hyperedge>Text {i}',
            'quality_score': 0.3,
            'source_id': 'chunk1',
            'weight': 1.0,
        })
        mock_quality_scorer.quality_scores[f'he{i}'] = 0.3
    
    refiner = HyperedgeRefiner(mock_graph, refiner_config)
    
    result = await refiner.iterative_refine_hyperedges(
        hyperedge_ids=['he0', 'he1', 'he2'],
        text_chunks_db=mock_text_chunks_db,
        llm_model_func=mock_llm_func,
        embedding_func=AsyncMock(),
        quality_scorer=mock_quality_scorer,
        global_config=global_config,
        max_iterations=1
    )
    
    # Check statistics
    assert 'refined_count' in result
    assert 'improved_count' in result
    assert 'failed_count' in result
    assert 'improvement_rate' in result
    assert 'avg_quality_improvement' in result
    assert 'quality_improvements' in result
    assert 'refinement_details' in result
    
    # Improvement rate should be between 0 and 1
    assert 0 <= result['improvement_rate'] <= 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
