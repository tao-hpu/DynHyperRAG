"""
Query API Routes

REST API endpoints for RAG query execution.
"""

from fastapi import APIRouter, HTTPException, Query
import logging

from api.models.query import (
    QueryRequest,
    QueryResponse,
    QueryHistoryResponse,
)

logger = logging.getLogger(__name__)

# Create router
router = APIRouter()

# Query service will be set by main.py after initialization
query_service = None


@router.post("/", response_model=QueryResponse)
async def execute_query(request: QueryRequest):
    """
    Execute a RAG query
    
    Performs retrieval-augmented generation using the hypergraph knowledge base.
    
    **Request Body:**
    - **query**: Query text (required)
    - **mode**: Query mode - local, global, hybrid, or naive (default: hybrid)
    - **top_k**: Number of entities/relationships to retrieve (default: 60)
    - **max_token_for_text_unit**: Max tokens for text chunks (default: 4000)
    - **max_token_for_local_context**: Max tokens for entity descriptions (default: 4000)
    - **max_token_for_global_context**: Max tokens for relationship descriptions (default: 4000)
    
    **Returns:**
    - Generated answer
    - Query execution path (nodes and edges accessed)
    - Context used for generation
    - Execution time and metadata
    
    **Query Modes:**
    - **local**: Entity-focused retrieval (uses entity descriptions)
    - **global**: Relationship-focused retrieval (uses relationship descriptions)
    - **hybrid**: Combines both local and global (recommended)
    - **naive**: Simple RAG without graph structure
    """
    try:
        logger.info(f"Received query: '{request.query[:50]}...' (mode={request.mode})")
        response = await query_service.execute(request)
        return response
    except RuntimeError as e:
        logger.error(f"Query service not initialized: {e}")
        raise HTTPException(status_code=503, detail="Query service not available")
    except Exception as e:
        logger.error(f"Query execution failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history", response_model=QueryHistoryResponse)
async def get_query_history(
    limit: int = Query(10, ge=1, le=100, description="Maximum number of history items")
):
    """
    Get query history
    
    Returns a list of recent queries with their metadata.
    
    **Query Parameters:**
    - **limit**: Maximum number of history items to return (1-100, default: 10)
    
    **Returns:**
    - List of recent queries (newest first)
    - Total number of queries in history
    """
    try:
        history = await query_service.get_history(limit)
        return history
    except RuntimeError as e:
        logger.error(f"Query service not initialized: {e}")
        raise HTTPException(status_code=503, detail="Query service not available")
    except Exception as e:
        logger.error(f"Failed to get query history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/history")
async def clear_query_history():
    """
    Clear query history
    
    Removes all queries from the history.
    
    **Returns:**
    - Success message
    """
    try:
        await query_service.clear_history()
        return {"message": "Query history cleared", "status": "success"}
    except RuntimeError as e:
        logger.error(f"Query service not initialized: {e}")
        raise HTTPException(status_code=503, detail="Query service not available")
    except Exception as e:
        logger.error(f"Failed to clear query history: {e}")
        raise HTTPException(status_code=500, detail=str(e))
