from fastapi import APIRouter

from .v1 import v1_router
from .v2 import v2_router

api_router = APIRouter()
api_router.include_router(v1_router, prefix="/v1")
api_router.include_router(v2_router, prefix="/v2")


__all__ = ["api_router"]
