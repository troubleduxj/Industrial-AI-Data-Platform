#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强错误处理中间件
提供全局的错误捕获、详细信息记录和环境感知的错误响应
"""

import time
import uuid
import traceback
from datetime import datetime
from typing import Any, Dict, Optional
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from loguru import logger

from app.core.detailed_logger import detailed_logger
from app.core.exceptions import APIException
from app.settings.config import settings


class ErrorEnhancementMiddleware(BaseHTTPMiddleware):
    """增强错误处理中间件
    
    功能：
    1. 全局异常捕获和处理
    2. 详细错误信息记录
    3. 环境感知的错误响应
    4. 请求上下文收集
    5. 性能指标记录
    """
    
    def __init__(self, app):
        super().__init__(app)
        self.debug_mode = settings.DEBUG
        self.environment = getattr(settings, 'ENVIRONMENT', 'development')
        
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        """处理请求并捕获异常"""
        
        # 生成请求ID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        # 记录请求开始时间
        start_time = time.time()
        
        # 收集请求上下文
        request_context = await self._collect_request_context(request)
        
        try:
            # 执行请求
            response = await call_next(request)
            
            # 记录成功的请求
            duration_ms = (time.time() - start_time) * 1000
            await self._log_successful_request(request, response, duration_ms, request_context)
            
            return response
            
        except Exception as exc:
            # 记录异常详情
            duration_ms = (time.time() - start_time) * 1000
            error_id = await self._handle_exception(request, exc, duration_ms, request_context)
            
            # 返回错误响应
            return await self._create_error_response(request, exc, error_id)
    
    async def _collect_request_context(self, request: Request) -> Dict[str, Any]:
        """收集请求上下文信息"""
        
        context = detailed_logger.log_request_context(request)
        
        # 尝试获取请求体（如果适用）
        if request.method in ["POST", "PUT", "PATCH"]:
            try:
                # 注意：这里需要小心处理，因为request.body()只能调用一次
                # 在实际应用中，可能需要在其他地方收集请求体信息
                pass
            except Exception:
                pass
        
        return context
    
    async def _collect_user_context(self, request: Request) -> Dict[str, Any]:
        """收集用户上下文信息"""
        
        user_context = {}
        
        # 尝试从请求状态中获取用户信息
        if hasattr(request.state, 'user'):
            user = request.state.user
            user_context = detailed_logger.log_user_context(
                user_id=getattr(user, 'id', None),
                username=getattr(user, 'username', None),
                roles=getattr(user, 'roles', []),
                permissions=getattr(user, 'permissions', [])
            )
        elif hasattr(request.state, 'user_id'):
            user_context = detailed_logger.log_user_context(
                user_id=request.state.user_id
            )
        
        return user_context
    
    async def _collect_system_context(self, request: Request, duration_ms: float) -> Dict[str, Any]:
        """收集系统上下文信息"""
        
        performance_metrics = {
            "request_duration_ms": duration_ms,
            "endpoint": request.url.path,
            "method": request.method
        }
        
        return detailed_logger.log_system_context(
            performance_metrics=performance_metrics
        )
    
    async def _handle_exception(
        self,
        request: Request,
        exc: Exception,
        duration_ms: float,
        request_context: Dict[str, Any]
    ) -> str:
        """处理异常并记录详细信息"""
        
        # 收集用户上下文
        user_context = await self._collect_user_context(request)
        
        # 收集系统上下文
        system_context = await self._collect_system_context(request, duration_ms)
        
        # 确定错误严重程度
        severity = self._determine_error_severity(exc)
        
        # 记录详细错误信息
        error_id = detailed_logger.log_error_with_context(
            error=exc,
            request_context=request_context,
            user_context=user_context,
            system_context=system_context,
            severity=severity
        )
        
        # 记录性能指标（即使是错误请求）
        detailed_logger.log_performance_metrics(
            operation_name=f"{request.method} {request.url.path}",
            duration_ms=duration_ms,
            additional_metrics={
                "error": True,
                "error_type": type(exc).__name__,
                "error_id": error_id
            }
        )
        
        return error_id
    
    def _determine_error_severity(self, exc: Exception) -> str:
        """确定错误严重程度"""
        
        # 认证/授权错误通常不是系统问题
        if isinstance(exc, APIException):
            if exc.code == 401 or exc.code == 403:
                return "WARNING"
            elif exc.code >= 500:
                return "ERROR"
            else:
                return "WARNING"
        
        # 系统级异常
        if isinstance(exc, (SystemError, MemoryError, OSError)):
            return "CRITICAL"
        
        # 数据库相关异常
        if "database" in str(type(exc)).lower() or "sql" in str(type(exc)).lower():
            return "ERROR"
        
        # 默认为ERROR级别
        return "ERROR"
    
    async def _create_error_response(
        self,
        request: Request,
        exc: Exception,
        error_id: str
    ) -> JSONResponse:
        """创建错误响应"""
        
        # 获取API版本
        api_version = getattr(request.state, 'api_version', 'v1')
        
        # 环境感知的错误响应
        if self.debug_mode or self.environment == 'development':
            # 开发环境：返回详细错误信息
            error_response = {
                "error": True,
                "error_id": error_id,
                "error_type": type(exc).__name__,
                "message": str(exc),
                "details": getattr(exc, 'details', None),
                "traceback": traceback.format_exc().split('\n') if self.debug_mode else None,
                "request_id": getattr(request.state, 'request_id', None),
                "timestamp": datetime.now().isoformat(),
                "environment": self.environment
            }
            
            # 如果是APIException，包含更多信息
            if isinstance(exc, APIException):
                error_response.update({
                    "code": exc.code,
                    "error_code": exc.error_code
                })
                status_code = exc.code
            else:
                status_code = 500
                
        else:
            # 生产环境：返回安全的错误信息
            if isinstance(exc, APIException):
                error_response = {
                    "error": True,
                    "error_id": error_id,
                    "message": exc.message,
                    "code": exc.code,
                    "timestamp": datetime.now().isoformat()
                }
                status_code = exc.code
            else:
                error_response = {
                    "error": True,
                    "error_id": error_id,
                    "message": "服务器内部错误，请联系管理员",
                    "code": 500,
                    "timestamp": datetime.now().isoformat()
                }
                status_code = 500
        
        # 根据API版本调整响应格式
        if api_version == 'v2':
            # V2版本使用标准化响应格式
            response_data = {
                "success": False,
                "error": error_response,
                "data": None,
                "meta": {
                    "request_id": error_id,
                    "timestamp": datetime.now().isoformat(),
                    "api_version": "v2"
                }
            }
        else:
            # V1版本保持兼容性
            response_data = {
                "code": status_code,
                "msg": error_response.get("message", "未知错误"),
                "data": None
            }
        
        return JSONResponse(
            content=response_data,
            status_code=status_code,
            headers={
                "X-Error-ID": error_id,
                "X-Request-ID": getattr(request.state, 'request_id', error_id)
            }
        )
    
    async def _log_successful_request(
        self,
        request: Request,
        response: Response,
        duration_ms: float,
        request_context: Dict[str, Any]
    ):
        """记录成功的请求"""
        
        # 只在调试模式下记录成功请求的详细信息
        if self.debug_mode:
            user_context = await self._collect_user_context(request)
            
            logger.info(
                f"请求成功: {request.method} {request.url.path} - {response.status_code} ({duration_ms:.2f}ms)",
                extra={
                    "request_context": request_context,
                    "user_context": user_context,
                    "response_status": response.status_code,
                    "duration_ms": duration_ms
                }
            )
        
        # 记录性能指标
        detailed_logger.log_performance_metrics(
            operation_name=f"{request.method} {request.url.path}",
            duration_ms=duration_ms,
            additional_metrics={
                "status_code": response.status_code,
                "success": True
            }
        )


class ErrorContextCollector:
    """错误上下文收集器
    
    专门用于收集错误发生时的各种上下文信息
    """
    
    @staticmethod
    async def collect_authentication_context(
        request: Request,
        token: Optional[str] = None,
        user: Optional[Any] = None,
        error: Optional[Exception] = None
    ) -> Dict[str, Any]:
        """收集认证相关的上下文信息"""
        
        context = {
            "authentication": {
                "token_provided": token is not None,
                "token_length": len(token) if token else 0,
                "user_authenticated": user is not None,
                "user_id": getattr(user, 'id', None) if user else None,
                "username": getattr(user, 'username', None) if user else None,
                "error_type": type(error).__name__ if error else None,
                "error_message": str(error) if error else None
            }
        }
        
        return context
    
    @staticmethod
    async def collect_database_context(
        operation: str,
        table: Optional[str] = None,
        query: Optional[str] = None,
        error: Optional[Exception] = None
    ) -> Dict[str, Any]:
        """收集数据库相关的上下文信息"""
        
        context = {
            "database": {
                "operation": operation,
                "table": table,
                "query": query[:500] if query else None,  # 截断长查询
                "error_type": type(error).__name__ if error else None,
                "error_message": str(error) if error else None
            }
        }
        
        return context
    
    @staticmethod
    async def collect_permission_context(
        user_id: Optional[int] = None,
        resource: Optional[str] = None,
        action: Optional[str] = None,
        permissions: Optional[list] = None,
        error: Optional[Exception] = None
    ) -> Dict[str, Any]:
        """收集权限相关的上下文信息"""
        
        context = {
            "permission": {
                "user_id": user_id,
                "resource": resource,
                "action": action,
                "user_permissions": permissions or [],
                "error_type": type(error).__name__ if error else None,
                "error_message": str(error) if error else None
            }
        }
        
        return context


# 全局错误上下文收集器实例
error_context_collector = ErrorContextCollector()