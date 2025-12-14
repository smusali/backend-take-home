"""
Middleware for request/response logging and error tracking.

Provides comprehensive request logging with timing, error tracking,
and optional request ID generation for distributed tracing.
"""

import time
import uuid
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.utils.logging_config import get_logger, log_request, log_error


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to log all HTTP requests and responses.
    
    Captures request details, response status, duration, and any errors
    that occur during request processing.
    """
    
    def __init__(self, app: ASGIApp):
        """
        Initialize the middleware.
        
        Args:
            app: ASGI application
        """
        super().__init__(app)
        self.logger = get_logger(__name__)
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request and log details.
        
        Args:
            request: Incoming HTTP request
            call_next: Next middleware/endpoint handler
            
        Returns:
            HTTP response
        """
        # Generate request ID if not provided
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        
        # Add request ID to request state for access in endpoints
        request.state.request_id = request_id
        
        # Get user from request if authenticated
        user = None
        if hasattr(request.state, "user"):
            user = request.state.user.username if request.state.user else None
        
        # Record start time
        start_time = time.time()
        
        # Log incoming request
        self.logger.debug(
            f"Request started | ID: {request_id} | "
            f"{request.method} {request.url.path}"
        )
        
        # Process request
        try:
            response = await call_next(request)
            
            # Calculate duration
            duration_ms = (time.time() - start_time) * 1000
            
            # Log successful request
            log_request(
                logger=self.logger,
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                duration_ms=duration_ms,
                user=user
            )
            
            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id
            
            return response
            
        except Exception as e:
            # Calculate duration
            duration_ms = (time.time() - start_time) * 1000
            
            # Log error
            self.logger.error(
                f"Request failed | ID: {request_id} | "
                f"{request.method} {request.url.path} | "
                f"Duration: {duration_ms:.2f}ms | Error: {e.__class__.__name__}"
            )
            
            log_error(
                logger=self.logger,
                error=e,
                context=f"{request.method} {request.url.path}",
                include_stack=True
            )
            
            # Re-raise to let exception handlers deal with it
            raise


class ErrorTrackingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to track and log application errors.
    
    Captures unhandled exceptions and ensures they are logged
    before being passed to exception handlers.
    """
    
    def __init__(self, app: ASGIApp):
        """
        Initialize the middleware.
        
        Args:
            app: ASGI application
        """
        super().__init__(app)
        self.logger = get_logger(__name__)
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Track errors during request processing.
        
        Args:
            request: Incoming HTTP request
            call_next: Next middleware/endpoint handler
            
        Returns:
            HTTP response
        """
        try:
            response = await call_next(request)
            
            # Log warnings for 4xx status codes (except 401, 404 which are common)
            if 400 <= response.status_code < 500:
                if response.status_code not in [401, 404]:
                    self.logger.warning(
                        f"Client error | {request.method} {request.url.path} | "
                        f"Status: {response.status_code}"
                    )
            
            # Log errors for 5xx status codes
            elif response.status_code >= 500:
                self.logger.error(
                    f"Server error | {request.method} {request.url.path} | "
                    f"Status: {response.status_code}"
                )
            
            return response
            
        except Exception as e:
            # Log unhandled exception
            self.logger.error(
                f"Unhandled exception | {request.method} {request.url.path} | "
                f"Error: {e.__class__.__name__}: {str(e)}"
            )
            
            # Re-raise for exception handlers
            raise


def add_request_id_to_response(request: Request, response: Response) -> None:
    """
    Add request ID to response headers for tracking.
    
    Args:
        request: HTTP request
        response: HTTP response to modify
    """
    request_id = getattr(request.state, "request_id", None)
    if request_id:
        response.headers["X-Request-ID"] = request_id


__all__ = [
    "RequestLoggingMiddleware",
    "ErrorTrackingMiddleware",
    "add_request_id_to_response",
]
