"""
Query Service

Business logic for RAG query execution and history management.
"""

from typing import List, Optional
import time
import logging
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)


class QueryService:
    """
    Service for executing RAG queries
    
    This service wraps HyperGraphRAG query functionality and provides:
    - Query execution with path tracking
    - Query history management
    - Performance metrics
    """
    
    def __init__(self):
        self.rag = None
        self._initialized = False
        self._query_history = []  # In-memory history (could be persisted later)
        self._max_history = 100  # Keep last 100 queries
    
    async def initialize(self, rag_instance):
        """
        Initialize QueryService with HyperGraphRAG instance
        
        Args:
            rag_instance: Initialized HyperGraphRAG instance
        """
        self.rag = rag_instance
        self._initialized = True
        logger.info("QueryService initialized")
    
    def _ensure_initialized(self):
        """Ensure service is initialized before use"""
        if not self._initialized or self.rag is None:
            raise RuntimeError("QueryService not initialized. Call initialize() first.")
    
    async def execute(self, request):
        """
        Execute a RAG query
        
        Args:
            request: QueryRequest object
        
        Returns:
            QueryResponse object with answer and metadata
        """
        self._ensure_initialized()
        
        from api.models.query import QueryResponse, QueryPath
        from hypergraphrag.base import QueryParam
        
        start_time = time.time()
        
        try:
            # Convert API request to HyperGraphRAG QueryParam
            query_param = QueryParam(
                mode=request.mode,
                top_k=request.top_k,
                max_token_for_text_unit=request.max_token_for_text_unit,
                max_token_for_local_context=request.max_token_for_local_context,
                max_token_for_global_context=request.max_token_for_global_context,
            )
            
            # Execute query
            logger.info(f"Executing query: '{request.query[:50]}...' (mode={request.mode})")
            answer = self.rag.query(request.query, param=query_param)
            
            execution_time = time.time() - start_time
            
            # Extract query path information
            # Note: HyperGraphRAG doesn't currently expose path info,
            # so we'll create a placeholder for now
            query_path = QueryPath(
                nodes=[],
                edges=[],
                scores={},
                mode_breakdown=None
            )
            
            # Create response
            response = QueryResponse(
                answer=answer,
                query_path=query_path,
                context_used=[],  # Could be extracted from RAG internals
                execution_time=execution_time,
                mode=request.mode,
                tokens_used=None  # Could be tracked if needed
            )
            
            # Save to history
            await self._save_to_history(request, response)
            
            logger.info(f"Query completed in {execution_time:.2f}s")
            return response
            
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            raise
    
    async def _save_to_history(self, request, response):
        """
        Save query to history
        
        Args:
            request: QueryRequest
            response: QueryResponse
        """
        from api.models.query import QueryHistoryItem
        
        # Create history item
        history_item = QueryHistoryItem(
            id=f"query-{uuid.uuid4().hex[:8]}",
            query=request.query,
            mode=request.mode,
            timestamp=datetime.utcnow().isoformat() + "Z",
            execution_time=response.execution_time,
            answer_preview=response.answer[:200] if len(response.answer) > 200 else response.answer
        )
        
        # Add to history (keep only last N queries)
        self._query_history.append(history_item)
        if len(self._query_history) > self._max_history:
            self._query_history.pop(0)
        
        logger.debug(f"Saved query to history: {history_item.id}")
    
    async def get_history(self, limit: int = 10):
        """
        Get query history
        
        Args:
            limit: Maximum number of history items to return
        
        Returns:
            QueryHistoryResponse with recent queries
        """
        self._ensure_initialized()
        
        from api.models.query import QueryHistoryResponse
        
        # Get most recent queries
        recent_queries = self._query_history[-limit:][::-1]  # Reverse to show newest first
        
        return QueryHistoryResponse(
            queries=recent_queries,
            total=len(self._query_history)
        )
    
    async def clear_history(self):
        """Clear query history"""
        self._ensure_initialized()
        self._query_history.clear()
        logger.info("Query history cleared")
