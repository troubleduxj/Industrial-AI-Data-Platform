"""
API v4兼容层
实现v2/v3到v4的路由映射，添加废弃警告响应头

Requirements: 6.5
"""
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass
from datetime import datetime
from fastapi import APIRouter, Request, Response, Depends
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import logging

from app.core.unified_logger import get_logger

logger = get_logger(__name__)


# =====================================================
# 路由映射配置
# =====================================================

@dataclass
class RouteMapping:
    """路由映射配置"""
    old_path: str
    new_path: str
    method: str
    old_version: str  # v2 or v3
    deprecated: bool = True
    removal_date: Optional[str] = None
    notes: Optional[str] = None


# v2/v3到v4的路由映射
ROUTE_MAPPINGS: List[RouteMapping] = [
    # 资产类别API映射
    RouteMapping(
        old_path="/api/v3/asset-categories",
        new_path="/api/v4/categories",
        method="GET",
        old_version="v3",
        deprecated=True,
        removal_date="2025-06-01",
        notes="请使用 /api/v4/categories"
    ),
    RouteMapping(
        old_path="/api/v3/asset-categories",
        new_path="/api/v4/categories",
        method="POST",
        old_version="v3",
        deprecated=True,
        removal_date="2025-06-01"
    ),
    RouteMapping(
        old_path="/api/v3/asset-categories/{id}",
        new_path="/api/v4/categories/{id}",
        method="GET",
        old_version="v3",
        deprecated=True,
        removal_date="2025-06-01"
    ),
    RouteMapping(
        old_path="/api/v3/asset-categories/{id}",
        new_path="/api/v4/categories/{id}",
        method="PUT",
        old_version="v3",
        deprecated=True,
        removal_date="2025-06-01"
    ),
    RouteMapping(
        old_path="/api/v3/asset-categories/{id}",
        new_path="/api/v4/categories/{id}",
        method="DELETE",
        old_version="v3",
        deprecated=True,
        removal_date="2025-06-01"
    ),
    
    # 资产API映射
    RouteMapping(
        old_path="/api/v3/assets",
        new_path="/api/v4/assets",
        method="GET",
        old_version="v3",
        deprecated=True,
        removal_date="2025-06-01"
    ),
    RouteMapping(
        old_path="/api/v3/assets",
        new_path="/api/v4/assets",
        method="POST",
        old_version="v3",
        deprecated=True,
        removal_date="2025-06-01"
    ),
    RouteMapping(
        old_path="/api/v3/assets/{id}",
        new_path="/api/v4/assets/{id}",
        method="GET",
        old_version="v3",
        deprecated=True,
        removal_date="2025-06-01"
    ),
    RouteMapping(
        old_path="/api/v3/assets/{id}",
        new_path="/api/v4/assets/{id}",
        method="PUT",
        old_version="v3",
        deprecated=True,
        removal_date="2025-06-01"
    ),
    RouteMapping(
        old_path="/api/v3/assets/{id}",
        new_path="/api/v4/assets/{id}",
        method="DELETE",
        old_version="v3",
        deprecated=True,
        removal_date="2025-06-01"
    ),
    
    # v2设备API到v4资产API映射
    RouteMapping(
        old_path="/api/v2/devices",
        new_path="/api/v4/assets",
        method="GET",
        old_version="v2",
        deprecated=True,
        removal_date="2025-03-01",
        notes="设备API已重命名为资产API"
    ),
    RouteMapping(
        old_path="/api/v2/device-types",
        new_path="/api/v4/categories",
        method="GET",
        old_version="v2",
        deprecated=True,
        removal_date="2025-03-01",
        notes="设备类型API已重命名为资产类别API"
    ),
]


# =====================================================
# 兼容层中间件
# =====================================================

class DeprecationMiddleware(BaseHTTPMiddleware):
    """
    废弃警告中间件
    
    为使用旧版API的请求添加废弃警告响应头
    """
    
    def __init__(self, app, mappings: List[RouteMapping] = None):
        super().__init__(app)
        self.mappings = mappings or ROUTE_MAPPINGS
        self._build_mapping_index()
    
    def _build_mapping_index(self):
        """构建映射索引以提高查找效率"""
        self.mapping_index: Dict[str, RouteMapping] = {}
        for mapping in self.mappings:
            # 将路径模式转换为正则表达式友好的格式
            key = f"{mapping.method}:{mapping.old_path}"
            self.mapping_index[key] = mapping
    
    def _find_mapping(self, method: str, path: str) -> Optional[RouteMapping]:
        """查找匹配的路由映射"""
        # 精确匹配
        key = f"{method}:{path}"
        if key in self.mapping_index:
            return self.mapping_index[key]
        
        # 模式匹配（处理路径参数）
        for mapping in self.mappings:
            if mapping.method != method:
                continue
            
            # 简单的路径模式匹配
            old_parts = mapping.old_path.split("/")
            path_parts = path.split("/")
            
            if len(old_parts) != len(path_parts):
                continue
            
            match = True
            for old_part, path_part in zip(old_parts, path_parts):
                if old_part.startswith("{") and old_part.endswith("}"):
                    continue  # 路径参数，跳过
                if old_part != path_part:
                    match = False
                    break
            
            if match:
                return mapping
        
        return None
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """处理请求，添加废弃警告"""
        response = await call_next(request)
        
        # 查找映���
        mapping = self._find_mapping(request.method, request.url.path)
        
        if mapping and mapping.deprecated:
            # 添加废弃警告响应头
            response.headers["Deprecation"] = "true"
            response.headers["Sunset"] = mapping.removal_date or "2025-12-31"
            response.headers["Link"] = f'<{mapping.new_path}>; rel="successor-version"'
            response.headers["X-Deprecated-Message"] = (
                f"This API endpoint is deprecated. "
                f"Please migrate to {mapping.new_path} before {mapping.removal_date or 'removal'}."
            )
            
            # 记录废弃API使用
            logger.warning(
                f"Deprecated API called: {request.method} {request.url.path} "
                f"-> should use {mapping.new_path}"
            )
        
        return response


# =====================================================
# 兼容层路由
# =====================================================

router = APIRouter()


@router.get("/compatibility/mappings", summary="获取API映射列表")
async def get_api_mappings() -> JSONResponse:
    """
    获取v2/v3到v4的API映射列表
    """
    mappings = []
    for mapping in ROUTE_MAPPINGS:
        mappings.append({
            "old_path": mapping.old_path,
            "new_path": mapping.new_path,
            "method": mapping.method,
            "old_version": mapping.old_version,
            "deprecated": mapping.deprecated,
            "removal_date": mapping.removal_date,
            "notes": mapping.notes
        })
    
    return JSONResponse(
        status_code=200,
        content={
            "code": 0,
            "message": "success",
            "data": {
                "mappings": mappings,
                "total": len(mappings)
            }
        }
    )


@router.get("/compatibility/check", summary="检查API兼容性")
async def check_api_compatibility(
    path: str,
    method: str = "GET"
) -> JSONResponse:
    """
    检查指定API的兼容性状态
    """
    # 查找映射
    for mapping in ROUTE_MAPPINGS:
        if mapping.old_path == path and mapping.method == method.upper():
            return JSONResponse(
                status_code=200,
                content={
                    "code": 0,
                    "message": "success",
                    "data": {
                        "path": path,
                        "method": method,
                        "deprecated": mapping.deprecated,
                        "new_path": mapping.new_path,
                        "removal_date": mapping.removal_date,
                        "notes": mapping.notes,
                        "recommendation": f"请迁移到 {mapping.new_path}"
                    }
                }
            )
    
    return JSONResponse(
        status_code=200,
        content={
            "code": 0,
            "message": "success",
            "data": {
                "path": path,
                "method": method,
                "deprecated": False,
                "notes": "此API路径未在兼容层映射中"
            }
        }
    )


# =====================================================
# 响应格式转换器
# =====================================================

class ResponseConverter:
    """
    响应格式转换器
    
    将v4响应格式转换为v2/v3格式（用于向后兼容）
    """
    
    @staticmethod
    def v4_to_v3(v4_response: Dict[str, Any]) -> Dict[str, Any]:
        """
        将v4响应转换为v3格式
        
        v4格式: {"code": 0, "message": "success", "data": {...}, "meta": {...}}
        v3格式: {"code": 200, "msg": "success", "data": {...}, "total": N, "page": N, "page_size": N}
        """
        v3_response = {
            "code": 200 if v4_response.get("code", 0) == 0 else v4_response.get("code", 500),
            "msg": v4_response.get("message", "success"),
            "data": v4_response.get("data")
        }
        
        # 转换分页信息
        meta = v4_response.get("meta")
        if meta:
            v3_response["total"] = meta.get("total", 0)
            v3_response["page"] = meta.get("page", 1)
            v3_response["page_size"] = meta.get("page_size", 20)
        
        return v3_response
    
    @staticmethod
    def v4_to_v2(v4_response: Dict[str, Any]) -> Dict[str, Any]:
        """
        将v4响应转换为v2格式
        
        v2格式与v3类似，但可能有细微差异
        """
        return ResponseConverter.v4_to_v3(v4_response)
    
    @staticmethod
    def v3_to_v4(v3_response: Dict[str, Any]) -> Dict[str, Any]:
        """
        将v3响应转换为v4格式
        """
        v4_response = {
            "code": 0 if v3_response.get("code", 200) == 200 else v3_response.get("code", 500),
            "message": v3_response.get("msg", "success"),
            "data": v3_response.get("data")
        }
        
        # 转换分页信息
        if "total" in v3_response:
            v4_response["meta"] = {
                "page": v3_response.get("page", 1),
                "page_size": v3_response.get("page_size", 20),
                "total": v3_response.get("total", 0),
                "total_pages": (v3_response.get("total", 0) + v3_response.get("page_size", 20) - 1) // v3_response.get("page_size", 20),
                "timestamp": datetime.now().isoformat()
            }
        
        return v4_response


# =====================================================
# 请求参数转换器
# =====================================================

class RequestConverter:
    """
    请求参数转换器
    
    处理v2/v3请求参数到v4的转换
    """
    
    @staticmethod
    def convert_pagination(params: Dict[str, Any]) -> Dict[str, Any]:
        """
        转换分页参数
        
        v2/v3: limit, offset 或 page, page_size
        v4: page, page_size
        """
        result = {}
        
        # 处理page参数
        if "page" in params:
            result["page"] = params["page"]
        elif "offset" in params and "limit" in params:
            result["page"] = (params["offset"] // params["limit"]) + 1
        else:
            result["page"] = 1
        
        # 处理page_size参数
        if "page_size" in params:
            result["page_size"] = params["page_size"]
        elif "limit" in params:
            result["page_size"] = params["limit"]
        elif "size" in params:
            result["page_size"] = params["size"]
        else:
            result["page_size"] = 20
        
        return result
    
    @staticmethod
    def convert_device_to_asset(params: Dict[str, Any]) -> Dict[str, Any]:
        """
        转换设备参数到资产参数
        
        v2设备API使用device_*命名，v4使用asset命名
        """
        mapping = {
            "device_id": "asset_id",
            "device_code": "code",
            "device_name": "name",
            "device_type_id": "category_id",
            "device_type": "category_code"
        }
        
        result = {}
        for key, value in params.items():
            new_key = mapping.get(key, key)
            result[new_key] = value
        
        return result


# =====================================================
# 导出
# =====================================================

__all__ = [
    "DeprecationMiddleware",
    "ResponseConverter",
    "RequestConverter",
    "ROUTE_MAPPINGS",
    "RouteMapping",
    "router"
]
