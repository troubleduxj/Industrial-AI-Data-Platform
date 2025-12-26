#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
JWT认证中间件
提供全局的JWT令牌验证和用户认证功能
"""

import re
from typing import List, Optional
from fastapi import Request, Response, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.services.auth_service import auth_service
from app.core.unified_logger import get_logger

logger = get_logger(__name__)


class JWTAuthMiddleware(BaseHTTPMiddleware):
    """JWT认证中间件"""
    
    def __init__(self, app, whitelist_paths: Optional[List[str]] = None):
        super().__init__(app)
        self.whitelist_paths = whitelist_paths or [
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
            "/favicon.ico",
            "/static",
        ]
        
        # 编译正则表达式模式以提高性能
        self.whitelist_patterns = [
            re.compile(path.replace("*", ".*")) for path in self.whitelist_paths
        ]
    
    def _is_whitelisted_path(self, path: str) -> bool:
        """检查路径是否在白名单中"""
        for pattern in self.whitelist_patterns:
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
    
    def _create_error_response(self, message: str, status_code: int = 401) -> JSONResponse:
        """创建错误响应"""
        return JSONResponse(
            status_code=status_code,
            content={
                "success": False,
                "message": message,
                "code": status_code,
                "data": None,
                "timestamp": None
            }
        )
    
    async def dispatch(self, request: Request, call_next) -> Response:
        """中间件主要逻辑"""
        path = request.url.path
        method = request.method
        
        # 检查是否为白名单路径
        if self._is_whitelisted_path(path):
            return await call_next(request)
        
        # 提取令牌
        token = self._extract_token_from_request(request)
        
        # 开发模式支持
        if token == "dev":
            logger.warning(f"使用开发模式令牌访问: {method} {path}")
            # 设置一个默认用户到请求状态
            request.state.user_id = 1
            request.state.is_authenticated = True
            return await call_next(request)
        
        if not token:
            logger.warning(f"缺少认证令牌: {method} {path}")
            return self._create_error_response("缺少访问令牌", 401)
        
        # 验证令牌
        user = await auth_service.get_user_from_token(token)
        if not user:
            logger.warning(f"令牌验证失败: {method} {path}")
            return self._create_error_response("无效或已过期的访问令牌", 401)
        
        # 检查用户状态
        if not user.is_active:
            logger.warning(f"用户账户已被禁用: {user.username}")
            return self._create_error_response("用户账户已被禁用", 401)
        
        # 将用户信息添加到请求状态
        request.state.user = user
        request.state.user_id = user.id
        request.state.is_authenticated = True
        request.state.is_superuser = user.is_superuser
        
        logger.debug(f"用户认证成功: {user.username} -> {method} {path}")
        
        try:
            response = await call_next(request)
            return response
        except Exception as e:
            logger.error(f"处理请求时发生错误: {e}")
            return self._create_error_response("服务器内部错误", 500)


class OptionalJWTAuthMiddleware(BaseHTTPMiddleware):
    """可选JWT认证中间件
    
    不强制要求认证，但如果提供了令牌会进行验证
    """
    
    def __init__(self, app):
        super().__init__(app)
    
    def _extract_token_from_request(self, request: Request) -> Optional[str]:
        """从请求中提取JWT令牌"""
        # 与JWTAuthMiddleware相同的逻辑
        authorization = request.headers.get("Authorization")
        if authorization and authorization.startswith("Bearer "):
            return authorization[7:]
        
        x_token = request.headers.get("X-Token")
        if x_token:
            return x_token
        
        token_header = request.headers.get("token")
        if token_header:
            return token_header
        
        token_param = request.query_params.get("token")
        if token_param:
            return token_param
        
        return None
    
    async def dispatch(self, request: Request, call_next) -> Response:
        """中间件主要逻辑"""
        # 提取令牌
        token = self._extract_token_from_request(request)
        
        # 初始化请求状态
        request.state.user = None
        request.state.user_id = None
        request.state.is_authenticated = False
        request.state.is_superuser = False
        
        if token:
            # 如果提供了令牌，尝试验证
            user = await auth_service.get_user_from_token(token)
            if user and user.is_active:
                request.state.user = user
                request.state.user_id = user.id
                request.state.is_authenticated = True
                request.state.is_superuser = user.is_superuser
                logger.debug(f"可选认证成功: {user.username}")
        
        return await call_next(request)


def create_jwt_middleware(
    whitelist_paths: Optional[List[str]] = None,
    optional: bool = False
):
    """
    创建JWT认证中间件
    
    Args:
        whitelist_paths: 白名单路径列表
        optional: 是否为可选认证
        
    Returns:
        中间件类
    """
    if optional:
        return OptionalJWTAuthMiddleware
    else:
        def middleware_factory(app):
            return JWTAuthMiddleware(app, whitelist_paths)
        return middleware_factory