"""
Error Handler Middleware

Centralized error handling for the API.
"""

from fastapi import Request, status, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
import logging

logger = logging.getLogger(__name__)


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Handle Pydantic validation errors
    
    Returns a 422 response with detailed validation error information.
    """
    logger.warning(f"Validation error on {request.url}: {exc.errors()}")
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "Validation Error",
            "detail": exc.errors(),
            "body": exc.body if hasattr(exc, 'body') else None
        }
    )


async def http_exception_handler(request: Request, exc: HTTPException):
    """
    Handle HTTP exceptions
    
    Returns a JSON response with error details.
    """
    logger.warning(f"HTTP {exc.status_code} on {request.url}: {exc.detail}")
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code
        }
    )


async def general_exception_handler(request: Request, exc: Exception):
    """
    Handle unexpected exceptions
    
    Returns a 500 response and logs the full traceback.
    """
    logger.error(f"Unexpected error on {request.url}: {exc}", exc_info=True)
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal Server Error",
            "message": str(exc)
        }
    )
