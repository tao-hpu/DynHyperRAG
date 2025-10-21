"""
Graph Data Models

Pydantic models for hypergraph nodes, edges, and related data structures.
"""

from pydantic import BaseModel, Field, validator
from typing import List, Optional


class Node(BaseModel):
    """
    Entity node in the hypergraph
    
    Represents an entity extracted from documents with its metadata.
    """
    id: str = Field(..., description="Unique node identifier")
    label: str = Field(..., description="Display name of the entity")
    type: str = Field(default="", description="Entity type (e.g., PERSON, ORGANIZATION)")
    description: str = Field(default="", description="Entity description")
    weight: float = Field(default=1.0, ge=0.0, description="Node importance weight")
    relevance_score: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Relevance score in query context (0-1)"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "ent-abc123",
                "label": "Hypertension",
                "type": "DISEASE",
                "description": "A condition characterized by elevated blood pressure",
                "weight": 0.85,
                "relevance_score": 0.92
            }
        }


class Edge(BaseModel):
    """
    Hyperedge in the hypergraph
    
    Represents a relationship that can connect 2 or more entities.
    When entities list has 3+ items, it's a true hyperedge.
    """
    id: str = Field(..., description="Unique edge identifier")
    source: str = Field(..., description="Source node ID")
    target: str = Field(..., description="Target node ID")
    relation: str = Field(default="", description="Relationship type")
    description: str = Field(default="", description="Relationship description")
    weight: float = Field(default=1.0, ge=0.0, description="Edge importance weight")
    entities: List[str] = Field(
        default_factory=list,
        description="All entity IDs connected by this hyperedge"
    )
    is_hyperedge: bool = Field(
        default=False,
        serialization_alias="isHyperedge",
        description="True if this edge connects 3+ entities"
    )
    
    @validator('is_hyperedge', pre=True, always=True)
    @classmethod
    def compute_is_hyperedge(cls, v, values):
        """Automatically determine if this is a hyperedge based on entities count"""
        entities = values.get('entities', [])
        return len(entities) >= 3
    
    class Config:
        populate_by_name = True  # Allow both snake_case and camelCase
        json_schema_extra = {
            "example": {
                "id": "edge-xyz789",
                "source": "ent-abc123",
                "target": "ent-def456",
                "relation": "TREATS",
                "description": "Medication treats disease",
                "weight": 0.75,
                "entities": ["ent-abc123", "ent-def456", "ent-ghi789"],
                "isHyperedge": True
            }
        }


class GraphData(BaseModel):
    """
    Complete graph data structure
    
    Contains nodes and edges for rendering a (sub)graph.
    """
    nodes: List[Node] = Field(default_factory=list, description="List of nodes")
    edges: List[Edge] = Field(default_factory=list, description="List of edges")
    
    class Config:
        json_schema_extra = {
            "example": {
                "nodes": [
                    {
                        "id": "ent-1",
                        "label": "Hypertension",
                        "type": "DISEASE",
                        "weight": 0.9
                    }
                ],
                "edges": [
                    {
                        "id": "edge-1",
                        "source": "ent-1",
                        "target": "ent-2",
                        "relation": "CAUSES",
                        "weight": 0.8,
                        "entities": ["ent-1", "ent-2"]
                    }
                ]
            }
        }


class GraphStats(BaseModel):
    """
    Hypergraph statistics
    
    Provides overview metrics about the graph structure.
    """
    num_nodes: int = Field(..., ge=0, description="Total number of nodes")
    num_edges: int = Field(..., ge=0, description="Total number of edges")
    num_hyperedges: int = Field(..., ge=0, description="Number of hyperedges (3+ entities)")
    avg_degree: float = Field(..., ge=0.0, description="Average node degree")
    density: float = Field(..., ge=0.0, le=1.0, description="Graph density (0-1)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "num_nodes": 1523,
                "num_edges": 3847,
                "num_hyperedges": 892,
                "avg_degree": 5.05,
                "density": 0.0034
            }
        }


class NodeSearchResult(BaseModel):
    """
    Search result for node queries
    
    Extends Node with search-specific metadata.
    """
    node: Node = Field(..., description="The matched node")
    score: float = Field(..., ge=0.0, le=1.0, description="Search relevance score")
    matched_field: str = Field(
        default="label",
        description="Field that matched the search query"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "node": {
                    "id": "ent-abc123",
                    "label": "Hypertension",
                    "type": "DISEASE",
                    "weight": 0.85
                },
                "score": 0.95,
                "matched_field": "label"
            }
        }


class PaginationParams(BaseModel):
    """
    Pagination parameters for list endpoints
    """
    limit: int = Field(default=100, ge=1, le=10000, description="Maximum items to return")
    offset: int = Field(default=0, ge=0, description="Number of items to skip")
    
    class Config:
        json_schema_extra = {
            "example": {
                "limit": 100,
                "offset": 0
            }
        }


class FilterParams(BaseModel):
    """
    Filter parameters for graph queries
    """
    entity_type: Optional[str] = Field(
        default=None,
        description="Filter by entity type"
    )
    min_weight: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Minimum weight threshold"
    )
    max_weight: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Maximum weight threshold"
    )
    
    @validator('max_weight')
    @classmethod
    def validate_weight_range(cls, v, values):
        """Ensure max_weight >= min_weight"""
        min_weight = values.get('min_weight')
        if v is not None and min_weight is not None and v < min_weight:
            raise ValueError('max_weight must be >= min_weight')
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "entity_type": "DISEASE",
                "min_weight": 0.5,
                "max_weight": 1.0
            }
        }
