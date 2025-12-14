"""
Main FastAPI application.

Configures and initializes the FastAPI application with all routes,
middleware, exception handlers, logging, and settings.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.api.v1.api import api_router
from app.utils.exception_handlers import register_exception_handlers
from app.utils.logging_config import setup_logging, get_logger, log_startup, log_shutdown
from app.utils.middleware import RequestLoggingMiddleware, ErrorTrackingMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    
    Handles startup and shutdown events for the application.
    """
    settings = get_settings()
    logger = get_logger(__name__)
    
    # Startup
    log_startup(logger, settings.ENVIRONMENT, settings.DEBUG)
    
    yield
    
    # Shutdown
    log_shutdown(logger)


def create_application() -> FastAPI:
    """
    Create and configure the FastAPI application.
    
    Returns:
        Configured FastAPI application instance
    """
    settings = get_settings()
    
    # Initialize logging
    setup_logging()
    logger = get_logger(__name__)
    
    # Create FastAPI app
    app = FastAPI(
        title="Lead Management API",
        description="API for managing attorney lead submissions with resume uploads",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        debug=settings.DEBUG,
        lifespan=lifespan
    )
    
    # Add request logging middleware (first to capture all requests)
    app.add_middleware(RequestLoggingMiddleware)
    
    # Add error tracking middleware
    app.add_middleware(ErrorTrackingMiddleware)
    
    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.get_cors_origins(),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Register exception handlers
    register_exception_handlers(app)
    
    # Include API router
    app.include_router(api_router, prefix="/api/v1")
    
    # Health check endpoint
    @app.get("/health", tags=["health"])
    async def health_check():
        """Health check endpoint."""
        logger.debug("Health check requested")
        return {
            "status": "healthy",
            "version": "1.0.0",
            "environment": settings.ENVIRONMENT
        }
    
    return app


# Create app instance
app = create_application()


__all__ = ["app", "create_application"]
