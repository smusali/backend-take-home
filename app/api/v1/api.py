"""
API version 1 router.

Combines all v1 endpoints into a single router.
"""

from fastapi import APIRouter

from app.api.v1.endpoints import public, leads, auth


api_router = APIRouter()

# Include public endpoints (no authentication required)
api_router.include_router(
    public.router,
    prefix="",
    tags=["public"]
)

# Include authentication endpoints
api_router.include_router(
    auth.router,
    prefix="/auth",
    tags=["authentication"]
)

# Include protected endpoints (authentication required)
api_router.include_router(
    leads.router,
    prefix="/leads",
    tags=["leads"]
)


__all__ = ["api_router"]
