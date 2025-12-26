#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API版本检测中间件
自动检测API版本并设置到request.state中，用于错误处理和响应格式化
"""

import uuid
from typing import Optional
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp


class APIVersionMiddleware(BaseHTTPMiddleware):
    """API版本检测中间件"""
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next) -> Response:
        """处理请求，检测API版本并设置请求ID"""
        
        # 生成唯一的请求ID用于追踪
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        # 检测API版本
        api_version = self._detect_api_version(request)
        request.state.api_version = api_version
        
        # 设置请求开始时间用于性能监控
        import time
        request.state.start_time = time.time()
        
        # 添加请求ID到响应头
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        response.headers["X-API-Version"] = api_version
        
        return response
    
    def _detect_api_version(self, request: Request) -> str:
        """检测API版本"""
        path = request.url.path
        
        # 从路径中检测版本
        if path.startswith('/api/v2/'):
            return 'v2'
        elif path.startswith('/api/v1/'):
            return 'v1'
        
        # 从请求头中检测版本
        api_version_header = request.headers.get('X-API-Version', '').lower()
        if api_version_header in ['v1', 'v2']:
            return api_version_header
        
        # 从查询参数中检测版本
        version_param = request.query_params.get('version', '').lower()
        if version_param in ['v1', 'v2']:
            return version_param
        
        # 默认版本
        return 'v1'