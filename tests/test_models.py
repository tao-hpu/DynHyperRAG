"""
Unit tests for Pydantic data models

Tests model validation, field constraints, and computed properties.
"""

import pytest
from pydantic import ValidationError

# Mark all tests in this module as unit tests
pytestmark = pytest.mark.unit
from api.models.graph import (
    Node,
    Edge,
    GraphData,
    GraphStats,
    NodeSearchResult,
    PaginationParams,
    FilterParams,
)
from api.models.query import (
    QueryRequest,
    QueryPath,
    QueryResponse,
    QueryHistoryItem,
)


class TestNodeModel:
    """Tests for Node model"""
    
    def test_node_creation_minimal(self):
        """Test creating node with minimal required fields"""
        node = Node(id="test-1", label="Test Node")
        assert node.id == "test-1"
        assert node.label == "Test Node"
        assert node.type == ""
        assert node.description == ""
        assert node.weight == 1.0
        assert node.relevance_score is None
    
    def test_node_creation_full(self):
        """Test creating node with all fields"""
        node = Node(
            id="test-1",
            label="Hypertension",
            type="DISEASE",
            description="High blood pressure",
            weight=0.85,
            relevance_score=0.92
        )
        assert node.id == "test-1"
        assert node.label == "Hypertension"
        assert node.type == "DISEASE"
        assert node.description == "High blood pressure"
        assert node.weight == 0.85
        assert node.relevance_score == 0.92
    
    def test_node_weight_validation(self):
        """Test weight must be >= 0"""
        with pytest.raises(ValidationError):
            Node(id="test-1", label="Test", weight=-0.1)
    
    def test_node_relevance_score_range(self):
        """Test relevance_score must be between 0 and 1"""
        # Valid scores
        Node(id="test-1", label="Test", relevance_score=0.0)
        Node(id="test-1", label="Test", relevance_score=0.5)
        Node(id="test-1", label="Test", relevance_score=1.0)
        
        # Invalid scores
        with pytest.raises(ValidationError):
            Node(id="test-1", label="Test", relevance_score=-0.1)
        with pytest.raises(ValidationError):
            Node(id="test-1", label="Test", relevance_score=1.1)


class TestEdgeModel:
    """Tests for Edge model"""
    
    def test_edge_creation_minimal(self):
        """Test creating edge with minimal fields"""
        edge = Edge(id="edge-1", source="node-1", target="node-2")
        assert edge.id == "edge-1"
        assert edge.source == "node-1"
        assert edge.target == "node-2"
        assert edge.relation == ""
        assert edge.description == ""
        assert edge.weight == 1.0
        assert edge.entities == []
        assert edge.is_hyperedge is False
    
    def test_edge_is_hyperedge_auto_compute(self):
        """Test is_hyperedge is automatically computed from entities"""
        # Binary edge (2 entities)
        edge1 = Edge(
            id="edge-1",
            source="node-1",
            target="node-2",
            entities=["node-1", "node-2"]
        )
        assert edge1.is_hyperedge is False
        
        # Hyperedge (3+ entities)
        edge2 = Edge(
            id="edge-2",
            source="node-1",
            target="node-2",
            entities=["node-1", "node-2", "node-3"]
        )
        assert edge2.is_hyperedge is True
        
        # Hyperedge (4 entities)
        edge3 = Edge(
            id="edge-3",
            source="node-1",
            target="node-2",
            entities=["node-1", "node-2", "node-3", "node-4"]
        )
        assert edge3.is_hyperedge is True
    
    def test_edge_weight_validation(self):
        """Test weight must be >= 0"""
        with pytest.raises(ValidationError):
            Edge(id="edge-1", source="n1", target="n2", weight=-0.5)


class TestGraphDataModel:
    """Tests for GraphData model"""
    
    def test_graph_data_empty(self):
        """Test creating empty graph data"""
        graph = GraphData()
        assert graph.nodes == []
        assert graph.edges == []
    
    def test_graph_data_with_content(self):
        """Test creating graph data with nodes and edges"""
        nodes = [
            Node(id="n1", label="Node 1"),
            Node(id="n2", label="Node 2"),
        ]
        edges = [
            Edge(id="e1", source="n1", target="n2")
        ]
        graph = GraphData(nodes=nodes, edges=edges)
        assert len(graph.nodes) == 2
        assert len(graph.edges) == 1


class TestGraphStatsModel:
    """Tests for GraphStats model"""
    
    def test_graph_stats_creation(self):
        """Test creating graph statistics"""
        stats = GraphStats(
            num_nodes=100,
            num_edges=250,
            num_hyperedges=50,
            avg_degree=5.0,
            density=0.025
        )
        assert stats.num_nodes == 100
        assert stats.num_edges == 250
        assert stats.num_hyperedges == 50
        assert stats.avg_degree == 5.0
        assert stats.density == 0.025
    
    def test_graph_stats_validation(self):
        """Test field validations"""
        # Negative values not allowed
        with pytest.raises(ValidationError):
            GraphStats(
                num_nodes=-1,
                num_edges=0,
                num_hyperedges=0,
                avg_degree=0.0,
                density=0.0
            )
        
        # Density must be <= 1.0
        with pytest.raises(ValidationError):
            GraphStats(
                num_nodes=10,
                num_edges=20,
                num_hyperedges=5,
                avg_degree=4.0,
                density=1.5
            )


class TestPaginationParams:
    """Tests for PaginationParams model"""
    
    def test_pagination_defaults(self):
        """Test default pagination values"""
        params = PaginationParams()
        assert params.limit == 100
        assert params.offset == 0
    
    def test_pagination_custom(self):
        """Test custom pagination values"""
        params = PaginationParams(limit=50, offset=100)
        assert params.limit == 50
        assert params.offset == 100
    
    def test_pagination_validation(self):
        """Test pagination constraints"""
        # Limit must be >= 1
        with pytest.raises(ValidationError):
            PaginationParams(limit=0)
        
        # Limit must be <= 10000
        with pytest.raises(ValidationError):
            PaginationParams(limit=10001)
        
        # Offset must be >= 0
        with pytest.raises(ValidationError):
            PaginationParams(offset=-1)


class TestFilterParams:
    """Tests for FilterParams model"""
    
    def test_filter_params_empty(self):
        """Test filter params with no filters"""
        params = FilterParams()
        assert params.entity_type is None
        assert params.min_weight is None
        assert params.max_weight is None
    
    def test_filter_params_with_values(self):
        """Test filter params with values"""
        params = FilterParams(
            entity_type="DISEASE",
            min_weight=0.5,
            max_weight=0.9
        )
        assert params.entity_type == "DISEASE"
        assert params.min_weight == 0.5
        assert params.max_weight == 0.9
    
    def test_filter_weight_range_validation(self):
        """Test max_weight must be >= min_weight"""
        # Valid range
        FilterParams(min_weight=0.3, max_weight=0.7)
        
        # Invalid range
        with pytest.raises(ValidationError):
            FilterParams(min_weight=0.7, max_weight=0.3)


class TestQueryRequest:
    """Tests for QueryRequest model"""
    
    def test_query_request_minimal(self):
        """Test query request with minimal fields"""
        req = QueryRequest(query="What is hypertension?")
        assert req.query == "What is hypertension?"
        assert req.mode == "hybrid"
        assert req.top_k == 60
    
    def test_query_request_full(self):
        """Test query request with all fields"""
        req = QueryRequest(
            query="What is hypertension?",
            mode="local",
            top_k=100,
            max_token_for_text_unit=5000,
            max_token_for_local_context=3000,
            max_token_for_global_context=2000
        )
        assert req.query == "What is hypertension?"
        assert req.mode == "local"
        assert req.top_k == 100
        assert req.max_token_for_text_unit == 5000
    
    def test_query_request_validation(self):
        """Test query request validations"""
        # Empty query not allowed
        with pytest.raises(ValidationError):
            QueryRequest(query="")
        
        # Invalid mode
        with pytest.raises(ValidationError):
            QueryRequest(query="test", mode="invalid")
        
        # top_k out of range
        with pytest.raises(ValidationError):
            QueryRequest(query="test", top_k=0)
        with pytest.raises(ValidationError):
            QueryRequest(query="test", top_k=201)


class TestQueryPath:
    """Tests for QueryPath model"""
    
    def test_query_path_empty(self):
        """Test empty query path"""
        path = QueryPath()
        assert path.nodes == []
        assert path.edges == []
        assert path.scores == {}
        assert path.mode_breakdown is None
    
    def test_query_path_with_data(self):
        """Test query path with data"""
        path = QueryPath(
            nodes=["n1", "n2", "n3"],
            edges=["e1", "e2"],
            scores={"n1": 0.95, "n2": 0.87, "e1": 0.82},
            mode_breakdown={"local": ["n1", "n2"], "global": ["e1"]}
        )
        assert len(path.nodes) == 3
        assert len(path.edges) == 2
        assert path.scores["n1"] == 0.95
        assert "local" in path.mode_breakdown


class TestQueryResponse:
    """Tests for QueryResponse model"""
    
    def test_query_response_creation(self):
        """Test creating query response"""
        response = QueryResponse(
            answer="Hypertension is high blood pressure.",
            query_path=QueryPath(nodes=["n1"], edges=[], scores={"n1": 0.9}),
            context_used=["Context 1", "Context 2"],
            execution_time=2.5,
            mode="hybrid",
            tokens_used=1500
        )
        assert "Hypertension" in response.answer
        assert response.execution_time == 2.5
        assert response.mode == "hybrid"
        assert response.tokens_used == 1500
    
    def test_query_response_validation(self):
        """Test query response validations"""
        # Negative execution time not allowed
        with pytest.raises(ValidationError):
            QueryResponse(
                answer="Test",
                query_path=QueryPath(),
                context_used=[],
                execution_time=-1.0,
                mode="hybrid"
            )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
