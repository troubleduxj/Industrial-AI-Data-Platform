import logging
from datetime import datetime
from typing import Dict, Any, Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.settings.config import settings
from app.core.redis import get_redis_client

logger = logging.getLogger(__name__)

router = APIRouter()


class HealthResponse(BaseModel):
    """健康检查响应模型"""
    status: str
    timestamp: datetime
    version: str
    services: Dict[str, Any]





@router.get("/", response_model=HealthResponse)
async def health_check():
    """应用健康检查"""
    try:
        # 检查Redis连接
        redis_status = "healthy"
        try:
            redis_client = await get_redis_client()
            await redis_client.ping()
        except Exception as e:
            redis_status = f"unhealthy: {str(e)}"
            logger.error(f"Redis健康检查失败: {e}")
        

        
        # 整体状态判断
        overall_status = "healthy" if redis_status == "healthy" else "degraded"
        
        return HealthResponse(
            status=overall_status,
            timestamp=datetime.now(),
            version=settings.VERSION,
            services={
                "redis": redis_status,

            }
        )
    except Exception as e:
        logger.error(f"健康检查失败: {e}")
        return HealthResponse(
            status="unhealthy",
            timestamp=datetime.now(),
            version=settings.VERSION,
            services={"error": str(e)}
        )