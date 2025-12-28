from fastapi import APIRouter

from .v1 import v1_router
from .v2 import v2_router
from .v3 import v3_router

api_router = APIRouter()
api_router.include_router(v1_router, prefix="/v1")
api_router.include_router(v2_router, prefix="/v2")
api_router.include_router(v3_router, prefix="/v3")


__all__ = ["api_router"]
