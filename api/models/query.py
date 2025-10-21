"""
Query Data Models

Pydantic models for RAG query requests and responses.
"""

from pydantic import BaseModel, Field
from typing import Literal, List, Dict, Optional


class QueryRequest(BaseModel):
    """
    RAG query request
    
    Parameters for executing a HyperGraphRAG query.
    """
    query: str = Field(..., min_length=1, description="Query text")
    mode: Literal["local", "global", "hybrid", "naive"] = Field(
        default="hybrid",
        description="Query mode: local (entity-focused), global (relationship-focused), hybrid (both), naive (simple RAG)"
    )
    top_k: int = Field(
        default=60,
        ge=1,
        le=200,
        description="Number of top entities/relationships to retrieve"
    )
    max_token_for_text_unit: int = Field(
        default=4000,
        ge=100,
        le=32000,
        description="Maximum tokens for original text chunks"
    )
    max_token_for_local_context: int = Field(
        default=4000,
        ge=100,
        le=32000,
        description="Maximum tokens for entity descriptions (local mode)"
    )
    max_token_for_global_context: int = Field(
        default=4000,
        ge=100,
        le=32000,
        description="Maximum tokens for relationship descriptions (global mode)"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "What are the treatment options for hypertension?",
                "mode": "hybrid",
                "top_k": 60,
                "max_token_for_text_unit": 4000,
                "max_token_for_local_context": 4000,
                "max_token_for_global_context": 4000
            }
        }


class QueryPath(BaseModel):
    """
    Query execution path information
    
    Tracks which nodes and edges were accessed during query execution.
    """
    nodes: List[str] = Field(
        default_factory=list,
        description="List of node IDs accessed during query"
    )
    edges: List[str] = Field(
        default_factory=list,
        description="List of edge IDs accessed during query"
    )
    scores: Dict[str, float] = Field(
        default_factory=dict,
        description="Relevance scores for nodes/edges (key: node/edge ID, value: score)"
    )
    mode_breakdown: Optional[Dict[str, List[str]]] = Field(
        default=None,
        description="Breakdown of nodes/edges by query mode (local/global)"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "nodes": ["ent-1", "ent-2", "ent-3"],
                "edges": ["edge-1", "edge-2"],
                "scores": {
                    "ent-1": 0.95,
                    "ent-2": 0.87,
                    "ent-3": 0.76,
                    "edge-1": 0.82,
                    "edge-2": 0.71
                },
                "mode_breakdown": {
                    "local": ["ent-1", "ent-2"],
                    "global": ["edge-1", "edge-2"]
                }
            }
        }


class QueryResponse(BaseModel):
    """
    RAG query response
    
    Contains the generated answer and metadata about query execution.
    """
    answer: str = Field(..., description="Generated answer to the query")
    query_path: QueryPath = Field(..., description="Query execution path information")
    context_used: List[str] = Field(
        default_factory=list,
        description="List of context snippets used for generation"
    )
    execution_time: float = Field(
        ...,
        ge=0.0,
        description="Query execution time in seconds"
    )
    mode: str = Field(..., description="Query mode used")
    tokens_used: Optional[int] = Field(
        default=None,
        ge=0,
        description="Total tokens used in LLM calls"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "answer": "Treatment options for hypertension include lifestyle modifications and medications...",
                "query_path": {
                    "nodes": ["ent-1", "ent-2"],
                    "edges": ["edge-1"],
                    "scores": {"ent-1": 0.95, "ent-2": 0.87}
                },
                "context_used": [
                    "Hypertension is treated with ACE inhibitors...",
                    "Lifestyle changes include diet and exercise..."
                ],
                "execution_time": 2.34,
                "mode": "hybrid",
                "tokens_used": 1523
            }
        }


class QueryHistoryItem(BaseModel):
    """
    Single query history entry
    """
    id: str = Field(..., description="Unique query ID")
    query: str = Field(..., description="Original query text")
    mode: str = Field(..., description="Query mode used")
    timestamp: str = Field(..., description="ISO 8601 timestamp")
    execution_time: float = Field(..., ge=0.0, description="Execution time in seconds")
    answer_preview: str = Field(
        ...,
        max_length=200,
        description="First 200 characters of the answer"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "query-abc123",
                "query": "What are the treatment options for hypertension?",
                "mode": "hybrid",
                "timestamp": "2025-10-21T21:30:00Z",
                "execution_time": 2.34,
                "answer_preview": "Treatment options for hypertension include lifestyle modifications..."
            }
        }


class QueryHistoryResponse(BaseModel):
    """
    Query history list response
    """
    queries: List[QueryHistoryItem] = Field(
        default_factory=list,
        description="List of historical queries"
    )
    total: int = Field(..., ge=0, description="Total number of queries in history")
    
    class Config:
        json_schema_extra = {
            "example": {
                "queries": [
                    {
                        "id": "query-1",
                        "query": "What is hypertension?",
                        "mode": "hybrid",
                        "timestamp": "2025-10-21T21:30:00Z",
                        "execution_time": 1.5,
                        "answer_preview": "Hypertension is a condition..."
                    }
                ],
                "total": 1
            }
        }
