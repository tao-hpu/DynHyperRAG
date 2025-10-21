"""
FastAPI Application Entry Point

Main application setup with CORS, routes, and lifecycle management.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from contextlib import asynccontextmanager
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# Global service instances (will be initialized on startup)
from api.services.graph_service import GraphService
from api.services.query_service import QueryService

graph_service = GraphService()
query_service = QueryService()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager
    
    Handles startup and shutdown events:
    - Startup: Initialize HyperGraphRAG and load data
    - Shutdown: Cleanup resources
    """
    # Startup
    logger.info("Starting HyperGraphRAG Visualization API...")
    try:
        await graph_service.initialize()
        logger.info("✓ GraphService initialized successfully")
        
        # Initialize QueryService with the same RAG instance
        await query_service.initialize(graph_service.rag)
        logger.info("✓ QueryService initialized successfully")
    except Exception as e:
        logger.error(f"✗ Failed to initialize services: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down HyperGraphRAG Visualization API...")


# Create FastAPI application
app = FastAPI(
    title="HyperGraphRAG Visualization API",
    version="1.0.0",
    description="REST API for HyperGraphRAG visualization and query interface",
    lifespan=lifespan
)


# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3400",  # React dev server
        "http://localhost:5173",  # Vite dev server
        "http://127.0.0.1:3400",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Register error handlers
from api.middleware.error_handler import (
    validation_exception_handler,
    general_exception_handler,
    http_exception_handler,
)

app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)


# Health check endpoint
@app.get("/api/health", tags=["health"])
async def health_check():
    """
    Health check endpoint
    
    Returns:
        dict: Status and service information
    """
    return {
        "status": "ok",
        "service": "HyperGraphRAG Visualization API",
        "version": "1.0.0"
    }


# Root endpoint
@app.get("/", tags=["root"])
async def root():
    """
    Root endpoint with API information
    
    Returns:
        dict: Welcome message and documentation link
    """
    return {
        "message": "HyperGraphRAG Visualization API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/api/health"
    }


# Import and register routes
from api.routes import graph, query

# Set service instances in route modules
graph.graph_service = graph_service
query.query_service = query_service

app.include_router(graph.router, prefix="/api/graph", tags=["graph"])
app.include_router(query.router, prefix="/api/query", tags=["query"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=3401,
        reload=True,
        log_level="info"
    )
