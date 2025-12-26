"""
健康检查 API v2
演示版本控制功能
"""
from fastapi import APIRouter, Request
from app.schemas.base import APIResponse, success_response
from app.core.versioning import version_required

router = APIRouter()

@router.get("/", summary="健康检查 v2", description="获取系统健康状态 - v2版本")
@version_required(min_version="v2")
async def health_check_v2(request: Request):
    """
    健康检查 v2版本
    
    新增功能：
    - 返回API版本信息
    - 增强的系统状态检查
    """
    api_version = getattr(request.state, 'api_version', 'v2')
    
    return success_response(
        data={
            "status": "healthy",
            "api_version": api_version,
            "features": [
                "standardized_responses",
                "version_control",
                "enhanced_error_handling"
            ],
            "timestamp": "2025-01-06T00:00:00"
        },
        message="System is healthy - v2"
    )

@router.get("/version", summary="获取API版本信息")
async def get_version_info(request: Request):
    """获取当前API版本详细信息"""
    api_version = getattr(request.state, 'api_version', 'v2')
    
    return success_response(
        data={
            "current_version": api_version,
            "supported_versions": ["v1", "v2"],
            "version_features": {
                "v1": ["basic_functionality", "legacy_responses"],
                "v2": ["standardized_responses", "version_control", "enhanced_error_handling"]
            }
        },
        message="Version information retrieved successfully"
    )