"""
Exception handlers for FastAPI application.

Provides centralized exception handling with consistent error response format
and automatic HTTP status code mapping for all custom exceptions.
"""

from datetime import datetime, UTC
from typing import Dict, Any

from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.utils.exceptions import LeadManagementException


def create_error_response(
    status_code: int,
    message: str,
    details: Dict[str, Any] = None,
    request_id: str = None
) -> Dict[str, Any]:
    """
    Create standardized error response structure.
    
    Args:
        status_code: HTTP status code
        message: Error message
        details: Optional additional error details
        request_id: Optional request identifier for tracking
        
    Returns:
        Dictionary with standardized error structure
    """
    error_response = {
        "error": {
            "message": message,
            "status_code": status_code,
            "timestamp": datetime.now(UTC).isoformat()
        }
    }
    
    if details:
        error_response["error"]["details"] = details
    
    if request_id:
        error_response["error"]["request_id"] = request_id
    
    return error_response


async def lead_management_exception_handler(
    request: Request,
    exc: LeadManagementException
) -> JSONResponse:
    """
    Handle all custom LeadManagementException errors.
    
    Catches all custom exceptions and returns a standardized error response
    with the appropriate HTTP status code.
    
    Args:
        request: FastAPI request object
        exc: Custom exception instance
        
    Returns:
        JSONResponse with error details
    """
    request_id = request.headers.get("X-Request-ID")
    
    error_response = create_error_response(
        status_code=exc.status_code,
        message=exc.message,
        details=exc.details,
        request_id=request_id
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response
    )


async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError
) -> JSONResponse:
    """
    Handle Pydantic validation errors.
    
    Formats validation errors into a user-friendly structure with details
    about which fields failed validation and why.
    
    Args:
        request: FastAPI request object
        exc: Pydantic validation error
        
    Returns:
        JSONResponse with validation error details
    """
    request_id = request.headers.get("X-Request-ID")
    
    # Extract validation errors
    errors = []
    for error in exc.errors():
        field = " -> ".join(str(loc) for loc in error["loc"])
        errors.append({
            "field": field,
            "message": error["msg"],
            "type": error["type"]
        })
    
    error_response = create_error_response(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        message="Validation error",
        details={"validation_errors": errors},
        request_id=request_id
    )
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=error_response
    )


async def http_exception_handler(
    request: Request,
    exc: StarletteHTTPException
) -> JSONResponse:
    """
    Handle standard HTTP exceptions.
    
    Catches FastAPI/Starlette HTTP exceptions and formats them consistently
    with other error responses.
    
    Args:
        request: FastAPI request object
        exc: HTTP exception
        
    Returns:
        JSONResponse with error details
    """
    request_id = request.headers.get("X-Request-ID")
    
    error_response = create_error_response(
        status_code=exc.status_code,
        message=exc.detail,
        request_id=request_id
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response,
        headers=exc.headers
    )


async def general_exception_handler(
    request: Request,
    exc: Exception
) -> JSONResponse:
    """
    Handle unexpected exceptions.
    
    Catches any unhandled exceptions and returns a generic 500 error
    without exposing sensitive implementation details.
    
    Args:
        request: FastAPI request object
        exc: Any unhandled exception
        
    Returns:
        JSONResponse with generic error message
    """
    request_id = request.headers.get("X-Request-ID")
    
    # Log the actual error for debugging but don't expose to client
    # (This will be logged by the logging middleware)
    
    error_response = create_error_response(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        message="An unexpected error occurred. Please try again later.",
        details={"error_type": exc.__class__.__name__} if request.app.debug else None,
        request_id=request_id
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_response
    )


def register_exception_handlers(app) -> None:
    """
    Register all exception handlers with the FastAPI application.
    
    This should be called during application initialization to set up
    centralized exception handling.
    
    Args:
        app: FastAPI application instance
        
    Example:
        >>> from fastapi import FastAPI
        >>> app = FastAPI()
        >>> register_exception_handlers(app)
    """
    # Custom exception handler for all LeadManagementException subclasses
    app.add_exception_handler(
        LeadManagementException,
        lead_management_exception_handler
    )
    
    # Pydantic validation errors
    app.add_exception_handler(
        RequestValidationError,
        validation_exception_handler
    )
    
    # Standard HTTP exceptions
    app.add_exception_handler(
        StarletteHTTPException,
        http_exception_handler
    )
    
    # Catch-all for unexpected errors
    app.add_exception_handler(
        Exception,
        general_exception_handler
    )


__all__ = [
    "create_error_response",
    "lead_management_exception_handler",
    "validation_exception_handler",
    "http_exception_handler",
    "general_exception_handler",
    "register_exception_handlers",
]
