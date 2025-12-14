"""
API version 1 router.

Combines all v1 endpoints into a single router.
"""

from fastapi import APIRouter

from app.api.v1.endpoints import public


api_router = APIRouter()

# Include public endpoints (no authentication required)
api_router.include_router(
    public.router,
    prefix="",
    tags=["public"]
)


__all__ = ["api_router"]
