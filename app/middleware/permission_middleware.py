#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
权限中间件
实现主权限中间件，支持JWT验证和API权限检查，批量删除权限中间件，白名单路径处理等
"""

import re
import time
import json
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
from fastapi import Request, Response, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.services.auth_service import auth_service
from app.services.permission_service import permission_service
from app.core.unified_logger import get_logger

logger = get_logger(__name__)


class PermissionMiddleware(BaseHTTPMiddleware):
    """主权限中间件
    
    集成JWT验证和API权限检查功能
    """
    
    def __init__(self, app, config: Optional[Dict[str, Any]] = None):
        super().__init__(app)
        
        # 配置参数
        config = config or {}
        self.enable_performance_monitoring = config.get("enable_performance_monitoring", True)
        self.enable_audit_logging = config.get("enable_audit_logging", True)
        self.slow_request_threshold = config.get("slow_request_threshold", 1000)  # 毫秒
        
        # 白名单路径
        self.whitelist_paths = config.get("whitelist_paths", [
            "/",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/api/v1/health",
            "/api/v2/health",
            "/api/v1/auth/login",
            "/api/v2/auth/login",
            "/api/v1/auth/refresh",
            "/api/v2/auth/refresh",
            "/api/v1/auth/logout",
            "/api/v2/auth/logout",
            "/favicon.ico",
            "/static",
        ])
        
        # 超级用户路径（只有超级用户可以访问）
        self.superuser_paths = config.get("superuser_paths", [
            "/api/v2/admin",
            "/api/v2/system",
            "/api/v2/config",
        ])
        
        # 编译正则表达式模式以提高性能
        self.whitelist_patterns = [
            re.compile(path.replace("*", ".*")) for path in self.whitelist_paths
        ]
        self.superuser_patterns = [
            re.compile(path.replace("*", ".*")) for path in self.superuser_paths
        ]
        
        # 性能统计
        self.request_stats = {
            "total_requests": 0,
            "authenticated_requests": 0,
            "permission_denied": 0,
            "avg_response_time": 0.0,
            "slow_requests": 0
        }
    
    def _is_whitelisted_path(self, path: str) -> bool:
        """检查路径是否在白名单中"""
        for pattern in self.whitelist_patterns:
            if pattern.match(path) or pattern.search(path):
                return True
        return False
    
    def _is_superuser_path(self, path: str) -> bool:
        """检查路径是否需要超级用户权限"""
        for pattern in self.superuser_patterns:
            if pattern.match(path) or pattern.search(path):
                return True
        return False
    
    def _extract_token_from_request(self, request: Request) -> Optional[str]:
        """从请求中提取JWT令牌"""
        # 1. 从Authorization头提取
        authorization = request.headers.get("Authorization")
        if authorization and authorization.startswith("Bearer "):
            return authorization[7:]
        
        # 2. 从X-Token头提取
        x_token = request.headers.get("X-Token")
        if x_token:
            return x_token
        
        # 3. 从token头提取
        token_header = request.headers.get("token")
        if token_header:
            return token_header
        
        # 4. 从查询参数提取（不推荐，但支持）
        token_param = request.query_params.get("token")
        if token_param:
            return token_param
        
        return None
    
    def _build_permission_key(self, request: Request) -> str:
        """构建权限键"""
        method = request.method
        path = request.url.path
        return f"{method} {path}"
    
    def _create_error_response(
        self, 
        message: str, 
        status_code: int = 403, 
        error_code: str = None
    ) -> JSONResponse:
        """创建错误响应"""
        return JSONResponse(
            status_code=status_code,
            content={
                "success": False,
                "message": message,
                "code": error_code or status_code,
                "data": None,
                "timestamp": datetime.now().isoformat()
            }
        )
    
    async def _extract_user_info(self, request: Request) -> Dict[str, Any]:
        """提取用户信息"""
        token = self._extract_token_from_request(request)
        
        # 开发模式支持
        if token == "dev":
            logger.warning(f"使用开发模式令牌访问: {request.method} {request.url.path}")
            return {
                "user_id": 1,
                "username": "dev_user",
                "is_active": True,
                "is_superuser": True,
                "token": token
            }
        
        if not token:
            raise HTTPException(
                status_code=401,
                detail="缺少访问令牌"
            )
        
        # 验证令牌
        user = await auth_service.get_user_from_token(token)
        if not user:
            raise HTTPException(
                status_code=401,
                detail="无效或已过期的访问令牌"
            )
        
        return {
            "user_id": user.id,
            "username": user.username,
            "is_active": user.is_active,
            "is_superuser": user.is_superuser,
            "token": token,
            "user": user
        }
    
    async def _check_permission(self, user_info: Dict[str, Any], permission_key: str) -> Tuple[bool, str]:
        """检查用户权限"""
        user_id = user_info["user_id"]
        
        # 超级用户拥有所有权限
        if user_info.get("is_superuser", False):
            return True, "超级用户权限"
        
        # 检查API权限
        has_permission = await permission_service.has_permission(user_id, permission_key)
        
        if has_permission:
            return True, "拥有API权限"
        else:
            return False, f"缺少权限: {permission_key}"
    
    def _log_request(
        self, 
        request: Request, 
        user_info: Optional[Dict[str, Any]], 
        status_code: int,
        response_time: float,
        permission_result: Optional[Tuple[bool, str]] = None
    ):
        """记录请求日志"""
        if not self.enable_audit_logging:
            return
        
        log_data = {
            "method": request.method,
            "path": request.url.path,
            "query_params": dict(request.query_params),
            "user_id": user_info.get("user_id") if user_info else None,
            "username": user_info.get("username") if user_info else None,
            "status_code": status_code,
            "response_time_ms": round(response_time, 2),
            "timestamp": datetime.now().isoformat(),
            "client_ip": request.client.host if request.client else None,
            "user_agent": request.headers.get("User-Agent"),
        }
        
        if permission_result:
            log_data["permission_granted"] = permission_result[0]
            log_data["permission_reason"] = permission_result[1]
        
        # 根据状态码选择日志级别
        if status_code >= 500:
            logger.error(f"权限中间件请求: {json.dumps(log_data, ensure_ascii=False)}")
        elif status_code >= 400:
            logger.warning(f"权限中间件请求: {json.dumps(log_data, ensure_ascii=False)}")
        else:
            logger.info(f"权限中间件请求: {json.dumps(log_data, ensure_ascii=False)}")
    
    def _update_stats(self, response_time: float, is_authenticated: bool, permission_denied: bool):
        """更新性能统计"""
        if not self.enable_performance_monitoring:
            return
        
        self.request_stats["total_requests"] += 1
        
        if is_authenticated:
            self.request_stats["authenticated_requests"] += 1
        
        if permission_denied:
            self.request_stats["permission_denied"] += 1
        
        if response_time > self.slow_request_threshold:
            self.request_stats["slow_requests"] += 1
        
        # 更新平均响应时间
        total_time = self.request_stats["avg_response_time"] * (self.request_stats["total_requests"] - 1)
        self.request_stats["avg_response_time"] = (total_time + response_time) / self.request_stats["total_requests"]
    
    async def dispatch(self, request: Request, call_next) -> Response:
        """中间件主要逻辑"""
        start_time = time.time()
        path = request.url.path
        method = request.method
        
        user_info = None
        permission_result = None
        status_code = 200
        
        try:
            # 1. 检查白名单路径
            if self._is_whitelisted_path(path):
                response = await call_next(request)
                response_time = (time.time() - start_time) * 1000
                self._update_stats(response_time, False, False)
                return response
            
            # 2. JWT令牌验证和用户信息提取
            try:
                user_info = await self._extract_user_info(request)
            except HTTPException as e:
                status_code = e.status_code
                response_time = (time.time() - start_time) * 1000
                self._log_request(request, None, status_code, response_time)
                self._update_stats(response_time, False, False)
                return self._create_error_response(e.detail, e.status_code)
            
            # 3. 用户状态检查
            if not user_info.get("is_active", False):
                status_code = 401
                response_time = (time.time() - start_time) * 1000
                self._log_request(request, user_info, status_code, response_time)
                self._update_stats(response_time, True, False)
                return self._create_error_response("用户账户已被禁用", 401)
            
            # 4. 超级用户路径检查
            if self._is_superuser_path(path):
                if not user_info.get("is_superuser", False):
                    status_code = 403
                    permission_result = (False, "需要超级用户权限")
                    response_time = (time.time() - start_time) * 1000
                    self._log_request(request, user_info, status_code, response_time, permission_result)
                    self._update_stats(response_time, True, True)
                    return self._create_error_response("需要超级用户权限", 403)
            
            # 5. API权限验证
            permission_key = self._build_permission_key(request)
            permission_result = await self._check_permission(user_info, permission_key)
            
            if not permission_result[0]:
                status_code = 403
                response_time = (time.time() - start_time) * 1000
                self._log_request(request, user_info, status_code, response_time, permission_result)
                self._update_stats(response_time, True, True)
                return self._create_error_response(permission_result[1], 403)
            
            # 6. 设置请求状态
            request.state.user = user_info.get("user")
            request.state.user_id = user_info["user_id"]
            request.state.username = user_info["username"]
            request.state.is_authenticated = True
            request.state.is_superuser = user_info.get("is_superuser", False)
            request.state.permission_key = permission_key
            
            # 7. 执行请求
            response = await call_next(request)
            status_code = response.status_code
            
            response_time = (time.time() - start_time) * 1000
            self._log_request(request, user_info, status_code, response_time, permission_result)
            self._update_stats(response_time, True, False)
            
            return response
            
        except Exception as e:
            status_code = 500
            response_time = (time.time() - start_time) * 1000
            logger.error(f"权限中间件异常: {e}")
            self._log_request(request, user_info, status_code, response_time)
            self._update_stats(response_time, user_info is not None, False)
            return self._create_error_response("服务器内部错误", 500)
    
    def get_stats(self) -> Dict[str, Any]:
        """获取性能统计"""
        return {
            **self.request_stats,
            "timestamp": datetime.now().isoformat()
        }


class BatchDeletePermissionMiddleware(BaseHTTPMiddleware):
    """批量删除权限中间件
    
    专门处理批量删除操作的权限控制
    """
    
    def __init__(self, app, config: Optional[Dict[str, Any]] = None):
        super().__init__(app)
        
        config = config or {}
        
        # 批量删除路径模式
        self.batch_delete_patterns = [
            re.compile(r'/api/v[12]/\w+/batch-delete'),
            re.compile(r'/api/v[12]/\w+/batch_delete'),
            re.compile(r'/api/v[12]/\w+/delete-batch'),
        ]
        
        # 受保护的资源类型
        self.protected_resources = config.get("protected_resources", [
            "users",
            "roles", 
            "menus",
            "departments",
            "system_configs"
        ])
        
        # 系统关键数据保护
        self.critical_data_protection = config.get("critical_data_protection", True)
    
    def _is_batch_delete_operation(self, request: Request) -> bool:
        """检查是否为批量删除操作"""
        path = request.url.path
        method = request.method
        
        # 只检查POST/DELETE请求
        if method not in ["POST", "DELETE"]:
            return False
        
        # 检查路径模式
        for pattern in self.batch_delete_patterns:
            if pattern.search(path):
                return True
        
        return False
    
    def _extract_resource_type(self, request: Request) -> str:
        """提取资源类型"""
        path = request.url.path
        
        # 从路径中提取资源类型
        # 例如: /api/v2/users/batch-delete -> users
        parts = path.split('/')
        for i, part in enumerate(parts):
            if part in ['api', 'v1', 'v2']:
                continue
            if i + 1 < len(parts) and 'batch' in parts[i + 1]:
                return part
        
        return "unknown"
    
    def _create_error_response(self, message: str, status_code: int = 403) -> JSONResponse:
        """创建错误响应"""
        return JSONResponse(
            status_code=status_code,
            content={
                "success": False,
                "message": message,
                "code": status_code,
                "data": None,
                "timestamp": datetime.now().isoformat()
            }
        )
    
    async def dispatch(self, request: Request, call_next) -> Response:
        """中间件主要逻辑"""
        # 检查是否为批量删除操作
        if not self._is_batch_delete_operation(request):
            return await call_next(request)
        
        # 获取用户信息（应该已经通过主权限中间件验证）
        user_id = getattr(request.state, 'user_id', None)
        is_superuser = getattr(request.state, 'is_superuser', False)
        
        if not user_id:
            logger.error("批量删除中间件: 缺少用户信息")
            return self._create_error_response("认证信息缺失", 401)
        
        # 提取资源类型
        resource_type = self._extract_resource_type(request)
        
        # 检查是否为受保护的资源
        if resource_type in self.protected_resources and not is_superuser:
            logger.warning(f"用户 {user_id} 尝试批量删除受保护资源: {resource_type}")
            return self._create_error_response(f"资源 '{resource_type}' 受保护，需要超级用户权限", 403)
        
        # 检查批量删除权限
        has_permission, reason = await permission_service.check_batch_permission(
            user_id, resource_type, "delete"
        )
        
        if not has_permission:
            logger.warning(f"用户 {user_id} 批量删除权限检查失败: {reason}")
            return self._create_error_response(reason, 403)
        
        # 记录批量删除操作
        logger.info(f"批量删除操作: 用户={user_id}, 资源={resource_type}, 路径={request.url.path}")
        
        # 设置批量操作标识
        request.state.is_batch_operation = True
        request.state.batch_resource_type = resource_type
        
        return await call_next(request)


class DataPermissionMiddleware(BaseHTTPMiddleware):
    """数据权限中间件
    
    实现多租户权限隔离和数据权限过滤
    """
    
    def __init__(self, app, config: Optional[Dict[str, Any]] = None):
        super().__init__(app)
        
        config = config or {}
        
        # 需要数据权限检查的路径模式
        self.data_permission_patterns = [
            re.compile(r'/api/v[12]/users'),
            re.compile(r'/api/v[12]/departments'),
            re.compile(r'/api/v[12]/devices'),
            re.compile(r'/api/v[12]/reports'),
        ]
        
        # 排除的路径（不需要数据权限检查）
        self.exclude_patterns = [
            re.compile(r'/api/v[12]/auth'),
            re.compile(r'/api/v[12]/health'),
            re.compile(r'/api/v[12]/system'),
        ]
    
    def _needs_data_permission_check(self, request: Request) -> bool:
        """检查是否需要数据权限检查"""
        path = request.url.path
        
        # 检查排除模式
        for pattern in self.exclude_patterns:
            if pattern.search(path):
                return False
        
        # 检查需要检查的模式
        for pattern in self.data_permission_patterns:
            if pattern.search(path):
                return True
        
        return False
    
    async def dispatch(self, request: Request, call_next) -> Response:
        """中间件主要逻辑"""
        # 检查是否需要数据权限检查
        if not self._needs_data_permission_check(request):
            return await call_next(request)
        
        # 获取用户信息
        user_id = getattr(request.state, 'user_id', None)
        is_superuser = getattr(request.state, 'is_superuser', False)
        
        if not user_id:
            return await call_next(request)
        
        # 超级用户跳过数据权限检查
        if is_superuser:
            return await call_next(request)
        
        # 获取用户数据权限范围
        data_scope = await permission_service.get_user_data_scope(user_id)
        
        # 设置数据权限信息到请求状态
        request.state.data_scope = data_scope
        
        logger.debug(f"数据权限中间件: 用户={user_id}, 权限范围={data_scope}")
        
        return await call_next(request)


def create_permission_middleware(config: Optional[Dict[str, Any]] = None):
    """创建权限中间件"""
    def middleware_factory(app):
        return PermissionMiddleware(app, config)
    return middleware_factory


def create_batch_delete_middleware(config: Optional[Dict[str, Any]] = None):
    """创建批量删除权限中间件"""
    def middleware_factory(app):
        return BatchDeletePermissionMiddleware(app, config)
    return middleware_factory


def create_data_permission_middleware(config: Optional[Dict[str, Any]] = None):
    """创建数据权限中间件"""
    def middleware_factory(app):
        return DataPermissionMiddleware(app, config)
    return middleware_factory


# 中间件配置示例
DEFAULT_PERMISSION_CONFIG = {
    "enable_performance_monitoring": True,
    "enable_audit_logging": True,
    "slow_request_threshold": 1000,  # 毫秒
    "whitelist_paths": [
        "/",
        "/docs",
        "/redoc", 
        "/openapi.json",
        "/api/v1/health",
        "/api/v2/health",
        "/api/v1/auth/login",
        "/api/v2/auth/login",
        "/api/v1/auth/refresh",
        "/api/v2/auth/refresh",
        "/api/v1/auth/logout",
        "/api/v2/auth/logout",
        "/favicon.ico",
        "/static/*",
    ],
    "superuser_paths": [
        "/api/v2/admin/*",
        "/api/v2/system/*",
        "/api/v2/config/*",
    ]
}

DEFAULT_BATCH_DELETE_CONFIG = {
    "protected_resources": [
        "users",
        "roles",
        "menus", 
        "departments",
        "system_configs"
    ],
    "critical_data_protection": True
}

DEFAULT_DATA_PERMISSION_CONFIG = {
    "enable_data_isolation": True,
    "default_scope": "dept"
}