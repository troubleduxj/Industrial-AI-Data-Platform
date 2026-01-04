"""
系统管理API v4
实现健康检查、配置管理端点，使用统一响应格式

Requirements: 6.1
"""
from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from datetime import datetime
import time
import os
import platform

from app.core.auth_dependencies import get_current_active_user
from app.core.unified_logger import get_logger
from app.models.admin import User

from .schemas import (
    ErrorCodes,
    create_response,
    create_error_response
)

logger = get_logger(__name__)
router = APIRouter()

# 服务启动时间
_start_time = time.time()


# =====================================================
# 健康检查API
# =====================================================

@router.get("/health", summary="健康检查")
async def health_check() -> JSONResponse:
    """
    系统健康检查
    
    检查各依赖服务的连接状态
    """
    try:
        services = {}
        overall_status = "healthy"
        
        # 检查数据库连接
        try:
            from tortoise import Tortoise
            conn = Tortoise.get_connection("default")
            await conn.execute_query("SELECT 1")
            services["postgresql"] = "healthy"
        except Exception as e:
            services["postgresql"] = f"unhealthy: {str(e)}"
            overall_status = "degraded"
        
        # 检查TDengine连接
        try:
            from app.core.tdengine_connector import td_client
            await td_client.query("SELECT SERVER_VERSION()")
            services["tdengine"] = "healthy"
        except Exception as e:
            services["tdengine"] = f"unhealthy: {str(e)}"
            # TDengine不可用不影响整体状态
        
        # 检查Redis连接（如果配置）
        try:
            from app.core.redis_client import redis_client
            if redis_client:
                await redis_client.ping()
                services["redis"] = "healthy"
            else:
                services["redis"] = "not_configured"
        except Exception as e:
            services["redis"] = f"unhealthy: {str(e)}"
        
        # 计算运行时间
        uptime = time.time() - _start_time
        
        return JSONResponse(
            status_code=200,
            content=create_response(
                data={
                    "status": overall_status,
                    "version": "v4.0.0",
                    "uptime": round(uptime, 2),
                    "timestamp": datetime.now().isoformat(),
                    "services": services
                },
                message="健康检查完成"
            )
        )
        
    except Exception as e:
        logger.error(f"健康检查失败: {e}")
        return JSONResponse(
            status_code=500,
            content=create_error_response(
                code=ErrorCodes.INTERNAL_ERROR,
                message=f"健康检查失败: {str(e)}"
            )
        )


@router.get("/health/live", summary="存活检查")
async def liveness_check() -> JSONResponse:
    """
    Kubernetes存活探针
    
    仅检查服务是否运行
    """
    return JSONResponse(
        status_code=200,
        content=create_response(
            data={"status": "alive"},
            message="服务存活"
        )
    )


@router.get("/health/ready", summary="就绪检查")
async def readiness_check() -> JSONResponse:
    """
    Kubernetes就绪探针
    
    检查服务是否准备好接收请求
    """
    try:
        # 检查数据库连接
        from tortoise import Tortoise
        conn = Tortoise.get_connection("default")
        await conn.execute_query("SELECT 1")
        
        return JSONResponse(
            status_code=200,
            content=create_response(
                data={"status": "ready"},
                message="服务就绪"
            )
        )
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content=create_error_response(
                code=ErrorCodes.SERVICE_UNAVAILABLE,
                message=f"服务未就绪: {str(e)}"
            )
        )


# =====================================================
# 系统配置API
# =====================================================

@router.get("/config", summary="获取系统配置")
async def get_system_config(
    current_user: User = Depends(get_current_active_user)
) -> JSONResponse:
    """
    获取系统配置信息
    """
    try:
        # 获取环境变量配置
        environment = os.getenv("ENVIRONMENT", "development")
        
        # 功能开关
        features = {
            "ai_engine": True,
            "realtime_push": True,
            "feature_engineering": True,
            "decision_engine": True,
            "model_storage": True,
            "data_ingestion": True
        }
        
        # 限制配置
        limits = {
            "max_page_size": 100,
            "max_batch_size": 1000,
            "max_upload_size_mb": 100,
            "max_query_range_days": 30
        }
        
        return JSONResponse(
            status_code=200,
            content=create_response(
                data={
                    "api_version": "v4.0.0",
                    "environment": environment,
                    "features": features,
                    "limits": limits
                },
                message="获取成功"
            )
        )
        
    except Exception as e:
        logger.error(f"获取系统配置失败: {e}")
        return JSONResponse(
            status_code=500,
            content=create_error_response(
                code=ErrorCodes.INTERNAL_ERROR,
                message=f"获取失败: {str(e)}"
            )
        )


@router.get("/info", summary="获取系统信息")
async def get_system_info(
    current_user: User = Depends(get_current_active_user)
) -> JSONResponse:
    """
    获取系统运行信息
    """
    try:
        import sys
        
        # 计算运行时间
        uptime = time.time() - _start_time
        
        return JSONResponse(
            status_code=200,
            content=create_response(
                data={
                    "api_version": "v4.0.0",
                    "python_version": sys.version,
                    "platform": platform.platform(),
                    "hostname": platform.node(),
                    "uptime_seconds": round(uptime, 2),
                    "start_time": datetime.fromtimestamp(_start_time).isoformat()
                },
                message="获取成功"
            )
        )
        
    except Exception as e:
        logger.error(f"获取系统信息失败: {e}")
        return JSONResponse(
            status_code=500,
            content=create_error_response(
                code=ErrorCodes.INTERNAL_ERROR,
                message=f"获取失败: {str(e)}"
            )
        )


# =====================================================
# 统计信息API
# =====================================================

@router.get("/stats", summary="获取系统统计")
async def get_system_stats(
    current_user: User = Depends(get_current_active_user)
) -> JSONResponse:
    """
    获取系统统计信息
    """
    try:
        stats = {}
        
        # 资产统计
        try:
            from app.models.platform_upgrade import Asset, AssetCategory, SignalDefinition, AIModel
            
            stats["assets"] = {
                "total": await Asset.all().count(),
                "active": await Asset.filter(is_active=True).count(),
                "online": await Asset.filter(status="online").count()
            }
            
            stats["categories"] = {
                "total": await AssetCategory.all().count(),
                "active": await AssetCategory.filter(is_active=True).count()
            }
            
            stats["signals"] = {
                "total": await SignalDefinition.all().count(),
                "active": await SignalDefinition.filter(is_active=True).count(),
                "stored": await SignalDefinition.filter(is_stored=True).count(),
                "realtime": await SignalDefinition.filter(is_realtime=True).count()
            }
            
            stats["models"] = {
                "total": await AIModel.all().count(),
                "active": await AIModel.filter(is_active=True).count(),
                "deployed": await AIModel.filter(status="deployed").count()
            }
        except Exception as e:
            logger.warning(f"获取资产统计失败: {e}")
            stats["error"] = str(e)
        
        return JSONResponse(
            status_code=200,
            content=create_response(
                data=stats,
                message="获取成功"
            )
        )
        
    except Exception as e:
        logger.error(f"获取系统统计失败: {e}")
        return JSONResponse(
            status_code=500,
            content=create_error_response(
                code=ErrorCodes.INTERNAL_ERROR,
                message=f"获取失败: {str(e)}"
            )
        )


# =====================================================
# API版本信息
# =====================================================

@router.get("/version", summary="获取API版本")
async def get_api_version() -> JSONResponse:
    """
    获取API版本信息
    """
    return JSONResponse(
        status_code=200,
        content=create_response(
            data={
                "version": "v4.0.0",
                "release_date": "2024-01-01",
                "supported_versions": ["v2", "v3", "v4"],
                "deprecated_versions": ["v1"],
                "changelog_url": "/docs/api_changelog.json"
            },
            message="获取成功"
        )
    )


# =====================================================
# 缓存管理API
# =====================================================

@router.post("/cache/clear", summary="清除缓存")
async def clear_cache(
    cache_type: Optional[str] = None,
    current_user: User = Depends(get_current_active_user)
) -> JSONResponse:
    """
    清除系统缓存
    
    - cache_type: 缓存类型（all/metadata/schema/session）
    """
    try:
        cleared = []
        
        # 清除Redis缓存
        try:
            from app.core.redis_client import redis_client
            if redis_client:
                if cache_type in [None, "all", "metadata"]:
                    await redis_client.delete("metadata:*")
                    cleared.append("metadata")
                if cache_type in [None, "all", "schema"]:
                    await redis_client.delete("schema:*")
                    cleared.append("schema")
                if cache_type in [None, "all", "session"]:
                    await redis_client.delete("session:*")
                    cleared.append("session")
        except Exception as e:
            logger.warning(f"清除Redis缓存失败: {e}")
        
        logger.info(f"缓存清除: {cleared}, 用户: {current_user.username}")
        
        return JSONResponse(
            status_code=200,
            content=create_response(
                data={"cleared": cleared},
                message="缓存清除成功"
            )
        )
        
    except Exception as e:
        logger.error(f"清除缓存失败: {e}")
        return JSONResponse(
            status_code=500,
            content=create_error_response(
                code=ErrorCodes.INTERNAL_ERROR,
                message=f"清除失败: {str(e)}"
            )
        )
