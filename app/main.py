"""
Main FastAPI application.

Configures and initializes the FastAPI application with all routes,
middleware, and settings.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.api.v1.api import api_router


def create_application() -> FastAPI:
    """
    Create and configure the FastAPI application.
    
    Returns:
        Configured FastAPI application instance
    """
    settings = get_settings()
    
    # Create FastAPI app
    app = FastAPI(
        title="Lead Management API",
        description="API for managing attorney lead submissions with resume uploads",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json"
    )
    
    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.get_cors_origins(),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include API router
    app.include_router(api_router, prefix="/api/v1")
    
    # Health check endpoint
    @app.get("/health", tags=["health"])
    async def health_check():
        """Health check endpoint."""
        return {"status": "healthy"}
    
    return app


# Create app instance
app = create_application()


__all__ = ["app", "create_application"]
