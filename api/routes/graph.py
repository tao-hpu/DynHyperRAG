"""
Graph API Routes

REST API endpoints for hypergraph data access.
"""

from fastapi import APIRouter, Query, HTTPException, Path
from typing import List, Optional
import logging

from api.models.graph import (
    Node,
    Edge,
    GraphData,
    GraphStats,
)

logger = logging.getLogger(__name__)

# Create router
router = APIRouter()

# Graph service will be set by main.py after initialization
graph_service = None


@router.get("/nodes", response_model=List[Node])
async def get_nodes(
    limit: int = Query(100, ge=1, le=10000, description="Maximum number of nodes to return"),
    offset: int = Query(0, ge=0, description="Number of nodes to skip"),
    entity_type: Optional[str] = Query(None, description="Filter by entity type")
):
    """
    Get entity nodes with pagination and filtering
    
    Returns a list of entity nodes from the hypergraph.
    
    - **limit**: Maximum number of nodes (1-10000)
    - **offset**: Pagination offset
    - **entity_type**: Optional filter by entity type (e.g., DISEASE, PERSON)
    """
    try:
        nodes = await graph_service.get_nodes(limit, offset, entity_type)
        return nodes
    except Exception as e:
        logger.error(f"Error getting nodes: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/nodes/{node_id}", response_model=Node)
async def get_node(
    node_id: str = Path(..., description="Node ID")
):
    """
    Get a single node by ID
    
    Returns detailed information about a specific entity node.
    
    - **node_id**: Unique node identifier
    """
    try:
        node = await graph_service.get_node_by_id(node_id)
        if node is None:
            raise HTTPException(status_code=404, detail=f"Node {node_id} not found")
        return node
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting node {node_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/edges", response_model=List[Edge])
async def get_edges(
    limit: int = Query(100, ge=1, le=10000, description="Maximum number of edges to return"),
    offset: int = Query(0, ge=0, description="Number of edges to skip"),
    min_weight: Optional[float] = Query(None, ge=0.0, le=1.0, description="Minimum edge weight")
):
    """
    Get hyperedges with pagination and filtering
    
    Returns a list of edges (including hyperedges) from the graph.
    
    - **limit**: Maximum number of edges (1-10000)
    - **offset**: Pagination offset
    - **min_weight**: Optional minimum weight threshold (0.0-1.0)
    """
    try:
        edges = await graph_service.get_edges(limit, offset, min_weight)
        return edges
    except Exception as e:
        logger.error(f"Error getting edges: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/edges/{edge_id}", response_model=Edge)
async def get_edge(
    edge_id: str = Path(..., description="Edge ID (format: source-target)")
):
    """
    Get a single edge by ID
    
    Returns detailed information about a specific edge or hyperedge.
    
    - **edge_id**: Edge identifier in format "source-target"
    """
    try:
        edge = await graph_service.get_edge_by_id(edge_id)
        if edge is None:
            raise HTTPException(status_code=404, detail=f"Edge {edge_id} not found")
        return edge
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting edge {edge_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats", response_model=GraphStats)
async def get_graph_stats():
    """
    Get hypergraph statistics
    
    Returns overview metrics about the graph structure:
    - Number of nodes and edges
    - Number of hyperedges (3+ entities)
    - Average node degree
    - Graph density
    """
    try:
        stats = await graph_service.get_stats()
        return stats
    except Exception as e:
        logger.error(f"Error getting graph stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/subgraph", response_model=GraphData)
async def get_subgraph(
    center_node_id: str = Query(..., description="Center node ID"),
    depth: int = Query(1, ge=1, le=3, description="Number of hops to expand (1-3)")
):
    """
    Get subgraph around a center node
    
    Extracts a subgraph by expanding from a center node using BFS.
    
    - **center_node_id**: ID of the center node
    - **depth**: Number of hops to expand (1-3)
    
    Returns nodes and edges in the subgraph.
    """
    try:
        subgraph = await graph_service.get_subgraph(center_node_id, depth)
        
        if not subgraph.nodes:
            raise HTTPException(
                status_code=404,
                detail=f"Center node {center_node_id} not found or has no neighbors"
            )
        
        return subgraph
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting subgraph: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search", response_model=List[Node])
async def search_nodes(
    keyword: str = Query(..., min_length=1, description="Search keyword"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of results")
):
    """
    Search entity nodes by keyword
    
    Performs semantic search using vector similarity.
    Falls back to string matching if vector search fails.
    
    - **keyword**: Search query
    - **limit**: Maximum number of results (1-100)
    
    Returns nodes sorted by relevance score.
    """
    try:
        results = await graph_service.search_nodes(keyword, limit)
        return results
    except Exception as e:
        logger.error(f"Error searching nodes: {e}")
        raise HTTPException(status_code=500, detail=str(e))
