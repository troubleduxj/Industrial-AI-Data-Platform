"""
API版本控制中间件
支持Header和URL路径版本控制
"""
import re
from typing import Optional
from fastapi import Request, Response
from fastapi.routing import APIRoute
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse


class APIVersioning:
    """API版本控制工具类"""
    
    DEFAULT_VERSION = "v1"
    SUPPORTED_VERSIONS = ["v1", "v2"]
    
    @staticmethod
    def get_version_from_header(request: Request) -> str:
        """从请求头获取API版本"""
        version = request.headers.get("API-Version", APIVersioning.DEFAULT_VERSION)
        return version if version in APIVersioning.SUPPORTED_VERSIONS else APIVersioning.DEFAULT_VERSION
    
    @staticmethod
    def get_version_from_path(path: str) -> str:
        """从URL路径获取API版本"""
        # 匹配 /api/v1/ 或 /api/v2/ 格式
        match = re.match(r'^/api/(v\d+)/', path)
        if match:
            version = match.group(1)
            return version if version in APIVersioning.SUPPORTED_VERSIONS else APIVersioning.DEFAULT_VERSION
        return APIVersioning.DEFAULT_VERSION
    
    @staticmethod
    def get_request_version(request: Request) -> str:
        """获取请求的API版本，优先使用路径版本"""
        path_version = APIVersioning.get_version_from_path(request.url.path)
        if path_version != APIVersioning.DEFAULT_VERSION:
            return path_version
        return APIVersioning.get_version_from_header(request)
    
    @staticmethod
    def normalize_path_for_version(path: str, version: str) -> str:
        """为指定版本规范化路径"""
        # 如果路径已包含版本，直接返回
        if re.match(r'^/api/v\d+/', path):
            return path
        
        # 如果路径以/api/开头但没有版本，添加版本
        if path.startswith('/api/'):
            return path.replace('/api/', f'/api/{version}/', 1)
        
        # 其他情况，添加完整的API版本前缀
        return f'/api/{version}{path}'


class APIVersionMiddleware(BaseHTTPMiddleware):
    """API版本控制中间件"""
    
    def __init__(self, app, default_version: str = "v1"):
        super().__init__(app)
        self.default_version = default_version
    
    async def dispatch(self, request: Request, call_next):
        """处理请求，添加版本信息"""
        
        # 获取请求版本
        api_version = APIVersioning.get_request_version(request)
        
        # 将版本信息添加到请求状态中，供后续处理使用
        request.state.api_version = api_version
        
        # 检查版本是否支持
        if api_version not in APIVersioning.SUPPORTED_VERSIONS:
            return JSONResponse(
                status_code=400,
                content={
                    "success": False,
                    "code": 400,
                    "message": f"Unsupported API version: {api_version}. Supported versions: {', '.join(APIVersioning.SUPPORTED_VERSIONS)}",
                    "timestamp": "2025-01-06T00:00:00"
                }
            )
        
        # 继续处理请求
        response = await call_next(request)
        
        # 在响应头中添加API版本信息
        response.headers["API-Version"] = api_version
        
        return response


# 移除复杂的路由类定制，版本控制通过中间件和URL路径实现


def create_versioned_router(version: str = "v1"):
    """创建支持版本控制的路由器"""
    from fastapi import APIRouter
    
    # 简化版本控制路由器，移除复杂的路由类定制
    router = APIRouter(prefix=f"/v{version.lstrip('v')}")
    router.version = version
    
    return router


# 版本兼容性检查装饰器
def version_required(min_version: str = "v1", max_version: str = None):
    """装饰器：检查API版本要求"""
    def decorator(func):
        async def wrapper(request: Request, *args, **kwargs):
            current_version = getattr(request.state, 'api_version', 'v1')
            
            # 简单的版本比较（假设版本格式为v1, v2等）
            current_num = int(current_version.lstrip('v'))
            min_num = int(min_version.lstrip('v'))
            
            if current_num < min_num:
                return JSONResponse(
                    status_code=400,
                    content={
                        "success": False,
                        "code": 400,
                        "message": f"This endpoint requires API version {min_version} or higher. Current version: {current_version}",
                        "timestamp": "2025-01-06T00:00:00"
                    }
                )
            
            if max_version:
                max_num = int(max_version.lstrip('v'))
                if current_num > max_num:
                    return JSONResponse(
                        status_code=400,
                        content={
                            "success": False,
                            "code": 400,
                            "message": f"This endpoint is deprecated in API version {current_version}. Maximum supported version: {max_version}",
                            "timestamp": "2025-01-06T00:00:00"
                        }
                    )
            
            return await func(request, *args, **kwargs)
        return wrapper
    return decorator


# 版本弃用警告装饰器
def deprecated_version(deprecated_in: str, remove_in: str = None):
    """装饰器：标记API版本弃用"""
    def decorator(func):
        async def wrapper(request: Request, *args, **kwargs):
            current_version = getattr(request.state, 'api_version', 'v1')
            
            response = await func(request, *args, **kwargs)
            
            # 添加弃用警告头
            if hasattr(response, 'headers'):
                response.headers["Deprecation"] = "true"
                response.headers["Sunset"] = remove_in if remove_in else "TBD"
                response.headers["Warning"] = f"299 - \"This API version {current_version} is deprecated since {deprecated_in}\""
            
            return response
        return wrapper
    return decorator