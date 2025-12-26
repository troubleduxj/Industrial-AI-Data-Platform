#!/usr/bin/env python3
"""
API版本路由管理器
统一管理v1和v2 API的路由，提供版本切换和兼容性支持
"""

from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.routing import APIRoute
from typing import Dict, Any, Optional, Callable
import logging
import time
from datetime import datetime

from app.api.compatibility.api_compatibility_adapter import compatibility_adapter

logger = logging.getLogger(__name__)

class APIVersionRouter:
    """API版本路由管理器"""
    
    def __init__(self, app: FastAPI):
        self.app = app
        self.v1_enabled = True
        self.v2_enabled = True
        self.compatibility_mode = True
        self.deprecation_warnings = True
        
        # 统计信息
        self.usage_stats = {
            'v1': {'requests': 0, 'errors': 0},
            'v2': {'requests': 0, 'errors': 0},
            'compatibility': {'requests': 0, 'errors': 0}
        }
    
    def setup_version_routing(self):
        """设置版本路由"""
        
        # 添加版本检测中间件
        @self.app.middleware("http")
        async def version_middleware(request: Request, call_next):
            return await self._handle_version_request(request, call_next)
        
        # 添加API版本信息端点
        @self.app.get("/api/version")
        async def get_api_version():
            return {
                "versions": {
                    "v1": {
                        "enabled": self.v1_enabled,
                        "deprecated": True,
                        "removal_date": "2024-12-31",
                        "base_path": "/api/v1"
                    },
                    "v2": {
                        "enabled": self.v2_enabled,
                        "current": True,
                        "base_path": "/api/v2"
                    }
                },
                "compatibility_mode": self.compatibility_mode,
                "usage_stats": self.usage_stats
            }
    
    async def _handle_version_request(self, request: Request, call_next):
        """处理版本请求"""
        start_time = time.time()
        
        try:
            # 检测API版本
            version = self._detect_api_version(request)
            
            if version == "v1":
                return await self._handle_v1_request(request, call_next, start_time)
            elif version == "v2":
                return await self._handle_v2_request(request, call_next, start_time)
            else:
                # 默认处理
                return await call_next(request)
                
        except Exception as e:
            logger.error(f"版本路由处理错误: {e}")
            return await call_next(request)
    
    def _detect_api_version(self, request: Request) -> Optional[str]:
        """检测API版本"""
        path = request.url.path
        
        # 通过URL路径检测
        if path.startswith("/api/v1/"):
            return "v1"
        elif path.startswith("/api/v2/"):
            return "v2"
        
        # 通过请求头检测
        api_version = request.headers.get("API-Version")
        if api_version:
            return f"v{api_version}"
        
        accept_header = request.headers.get("Accept", "")
        if "version=1" in accept_header:
            return "v1"
        elif "version=2" in accept_header:
            return "v2"
        
        # 检查是否是v1格式的路径（兼容模式）
        if self.compatibility_mode and self._is_v1_legacy_path(path):
            return "v1"
        
        return None
    
    def _is_v1_legacy_path(self, path: str) -> bool:
        """检查是否是v1遗留路径"""
        v1_patterns = [
            "/user/", "/role/", "/menu/", "/dept/",
            "/device/", "/statistics/", "/dashboard/"
        ]
        
        return any(pattern in path for pattern in v1_patterns)
    
    async def _handle_v1_request(self, request: Request, call_next, start_time: float):
        """处理v1请求"""
        self.usage_stats['v1']['requests'] += 1
        
        try:
            # 检查v1是否启用
            if not self.v1_enabled:
                raise HTTPException(
                    status_code=410,
                    detail="API v1 已停用，请使用 v2 版本"
                )
            
            # 添加废弃警告头
            if self.deprecation_warnings:
                response = await call_next(request)
                response.headers["X-API-Deprecated"] = "true"
                response.headers["X-API-Deprecation-Date"] = "2024-12-31"
                response.headers["X-API-Replacement"] = self._get_v2_replacement(request.url.path)
                return response
            
            # 如果启用兼容模式，尝试转换到v2
            if self.compatibility_mode:
                return await self._handle_compatibility_request(request, call_next, start_time)
            
            return await call_next(request)
            
        except Exception as e:
            self.usage_stats['v1']['errors'] += 1
            logger.error(f"v1请求处理错误: {e}")
            raise
    
    async def _handle_v2_request(self, request: Request, call_next, start_time: float):
        """处理v2请求"""
        self.usage_stats['v2']['requests'] += 1
        
        try:
            # 检查v2是否启用
            if not self.v2_enabled:
                raise HTTPException(
                    status_code=503,
                    detail="API v2 暂时不可用"
                )
            
            response = await call_next(request)
            
            # 添加v2响应头
            response.headers["X-API-Version"] = "2.0"
            response.headers["X-Response-Time"] = str(int((time.time() - start_time) * 1000))
            
            return response
            
        except Exception as e:
            self.usage_stats['v2']['errors'] += 1
            logger.error(f"v2请求处理错误: {e}")
            raise
    
    async def _handle_compatibility_request(self, request: Request, call_next, start_time: float):
        """处理兼容性请求"""
        self.usage_stats['compatibility']['requests'] += 1
        
        try:
            # 获取API映射
            mapping = compatibility_adapter.get_v2_mapping(
                request.method, 
                request.url.path
            )
            
            if not mapping:
                # 没有映射，直接处理原始请求
                return await call_next(request)
            
            # 转换请求参数
            v1_params = dict(request.query_params)
            if request.method in ["POST", "PUT", "PATCH"]:
                try:
                    v1_body = await request.json()
                    v1_params.update(v1_body)
                except:
                    pass
            
            v2_params = compatibility_adapter.map_request(mapping, v1_params)
            
            # 创建新的请求对象（这里简化处理）
            # 实际实现中需要更复杂的请求转换逻辑
            
            # 调用v2 API
            response = await call_next(request)
            
            # 转换响应格式
            if response.status_code == 200:
                try:
                    v2_response = await response.json()
                    v1_response = compatibility_adapter.map_response(mapping, v2_response)
                    
                    # 创建新的响应
                    from fastapi.responses import JSONResponse
                    new_response = JSONResponse(content=v1_response)
                    
                    # 添加兼容性头
                    new_response.headers["X-API-Compatibility"] = "v1-to-v2"
                    new_response.headers["X-API-Original-Version"] = "v1"
                    new_response.headers["X-API-Target-Version"] = "v2"
                    
                    if mapping.deprecated:
                        new_response.headers["X-API-Deprecated"] = "true"
                        deprecation_info = compatibility_adapter.get_deprecation_info(
                            request.method, request.url.path
                        )
                        if deprecation_info:
                            new_response.headers["X-API-Deprecation-Message"] = deprecation_info['message']
                    
                    return new_response
                    
                except Exception as e:
                    logger.error(f"响应转换错误: {e}")
                    return response
            
            return response
            
        except Exception as e:
            self.usage_stats['compatibility']['errors'] += 1
            logger.error(f"兼容性请求处理错误: {e}")
            return await call_next(request)
    
    def _get_v2_replacement(self, v1_path: str) -> str:
        """获取v2替代路径"""
        # 简单的路径映射
        path_mapping = {
            "/user/list": "/api/v2/users",
            "/user/create": "/api/v2/users",
            "/role/list": "/api/v2/roles",
            "/device/list": "/api/v2/devices",
            "/menu/list": "/api/v2/menus",
            "/dept/list": "/api/v2/departments"
        }
        
        return path_mapping.get(v1_path, "/api/v2/")
    
    def enable_v1(self, enabled: bool = True):
        """启用/禁用v1 API"""
        self.v1_enabled = enabled
        logger.info(f"API v1 {'启用' if enabled else '禁用'}")
    
    def enable_v2(self, enabled: bool = True):
        """启用/禁用v2 API"""
        self.v2_enabled = enabled
        logger.info(f"API v2 {'启用' if enabled else '禁用'}")
    
    def enable_compatibility_mode(self, enabled: bool = True):
        """启用/禁用兼容模式"""
        self.compatibility_mode = enabled
        logger.info(f"兼容模式 {'启用' if enabled else '禁用'}")
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """获取使用统计"""
        total_requests = sum(stats['requests'] for stats in self.usage_stats.values())
        total_errors = sum(stats['errors'] for stats in self.usage_stats.values())
        
        return {
            'total_requests': total_requests,
            'total_errors': total_errors,
            'error_rate': total_errors / total_requests if total_requests > 0 else 0,
            'version_breakdown': self.usage_stats,
            'v1_usage_percentage': (self.usage_stats['v1']['requests'] / total_requests * 100) if total_requests > 0 else 0,
            'v2_usage_percentage': (self.usage_stats['v2']['requests'] / total_requests * 100) if total_requests > 0 else 0,
            'compatibility_usage_percentage': (self.usage_stats['compatibility']['requests'] / total_requests * 100) if total_requests > 0 else 0
        }
    
    def reset_stats(self):
        """重置统计信息"""
        self.usage_stats = {
            'v1': {'requests': 0, 'errors': 0},
            'v2': {'requests': 0, 'errors': 0},
            'compatibility': {'requests': 0, 'errors': 0}
        }
        logger.info("API使用统计已重置")

# 使用示例
def setup_api_versioning(app: FastAPI):
    """设置API版本管理"""
    version_router = APIVersionRouter(app)
    version_router.setup_version_routing()
    
    # 可以根据需要调整配置
    # version_router.enable_compatibility_mode(True)
    # version_router.enable_v1(True)
    # version_router.enable_v2(True)
    
    return version_router