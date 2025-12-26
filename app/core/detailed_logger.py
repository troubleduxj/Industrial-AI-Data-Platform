#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
详细日志记录器
提供环境感知的详细日志记录功能，支持调试信息收集和上下文追踪
"""

import json
import traceback
import uuid
from datetime import datetime
from typing import Any, Dict, Optional, Union
from starlette.requests import Request
from loguru import logger

from app.settings.config import settings


class DetailedLogger:
    """详细日志记录器
    
    提供环境感知的详细日志记录功能，包括：
    - 错误上下文收集
    - 请求参数记录
    - 用户状态追踪
    - 系统环境信息
    - 性能指标收集
    """
    
    def __init__(self):
        self.debug_mode = settings.DEBUG
        self.log_level = getattr(settings, 'LOG_LEVEL', 'INFO').upper()
        self.environment = getattr(settings, 'ENVIRONMENT', 'development')
        
    def log_error_with_context(
        self,
        error: Exception,
        request_context: Optional[Dict[str, Any]] = None,
        user_context: Optional[Dict[str, Any]] = None,
        system_context: Optional[Dict[str, Any]] = None,
        severity: str = "ERROR"
    ) -> str:
        """记录带上下文的错误信息
        
        Args:
            error: 异常对象
            request_context: 请求上下文信息
            user_context: 用户上下文信息
            system_context: 系统上下文信息
            severity: 错误严重程度
            
        Returns:
            str: 错误追踪ID
        """
        error_id = str(uuid.uuid4())
        
        # 构建详细错误信息
        error_details = {
            "error_id": error_id,
            "timestamp": datetime.now().isoformat(),
            "environment": self.environment,
            "error_info": {
                "type": type(error).__name__,
                "message": str(error),
                "code": getattr(error, 'code', None),
                "error_code": getattr(error, 'error_code', None),
                "details": getattr(error, 'details', None)
            },
            "request_context": request_context or {},
            "user_context": user_context or {},
            "system_context": system_context or {},
            "traceback": traceback.format_exc() if severity in ["ERROR", "CRITICAL"] else None
        }
        
        # 清理敏感信息
        error_details = self._sanitize_log_data(error_details)
        
        # 根据环境和严重程度记录日志
        log_message = f"[{error_id}] {type(error).__name__}: {str(error)}"
        
        if severity == "CRITICAL":
            logger.critical(log_message, extra={"error_details": error_details})
        elif severity == "ERROR":
            logger.error(log_message, extra={"error_details": error_details})
        elif severity == "WARNING":
            logger.warning(log_message, extra={"error_details": error_details})
        elif severity == "INFO":
            logger.info(log_message, extra={"error_details": error_details})
        else:
            logger.debug(log_message, extra={"error_details": error_details})
        
        return error_id
    
    def log_request_context(
        self,
        request: Request,
        additional_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """收集请求上下文信息
        
        Args:
            request: FastAPI请求对象
            additional_context: 额外的上下文信息
            
        Returns:
            Dict[str, Any]: 请求上下文信息
        """
        context = {
            "method": request.method,
            "url": str(request.url),
            "path": request.url.path,
            "query_params": dict(request.query_params),
            "headers": dict(request.headers),
            "client_info": {
                "host": request.client.host if request.client else None,
                "port": request.client.port if request.client else None
            },
            "user_agent": request.headers.get("user-agent"),
            "referer": request.headers.get("referer"),
            "content_type": request.headers.get("content-type"),
            "content_length": request.headers.get("content-length"),
            "api_version": getattr(request.state, 'api_version', 'unknown'),
            "request_id": getattr(request.state, 'request_id', str(uuid.uuid4()))
        }
        
        # 添加额外上下文
        if additional_context:
            context.update(additional_context)
        
        return context
    
    def log_user_context(
        self,
        user_id: Optional[int] = None,
        username: Optional[str] = None,
        roles: Optional[list] = None,
        permissions: Optional[list] = None,
        session_info: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """收集用户上下文信息
        
        Args:
            user_id: 用户ID
            username: 用户名
            roles: 用户角色列表
            permissions: 用户权限列表
            session_info: 会话信息
            
        Returns:
            Dict[str, Any]: 用户上下文信息
        """
        context = {
            "user_id": user_id,
            "username": username,
            "roles": roles or [],
            "permissions": permissions or [],
            "session_info": session_info or {},
            "authenticated": user_id is not None
        }
        
        return context
    
    def log_system_context(
        self,
        performance_metrics: Optional[Dict[str, Any]] = None,
        memory_usage: Optional[Dict[str, Any]] = None,
        database_info: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """收集系统上下文信息
        
        Args:
            performance_metrics: 性能指标
            memory_usage: 内存使用情况
            database_info: 数据库信息
            
        Returns:
            Dict[str, Any]: 系统上下文信息
        """
        import psutil
        import os
        
        context = {
            "process_id": os.getpid(),
            "timestamp": datetime.now().isoformat(),
            "environment": self.environment,
            "debug_mode": self.debug_mode,
            "performance_metrics": performance_metrics or {},
            "system_info": {
                "cpu_percent": psutil.cpu_percent(),
                "memory_percent": psutil.virtual_memory().percent,
                "disk_usage": psutil.disk_usage('/').percent if os.name != 'nt' else psutil.disk_usage('C:').percent
            }
        }
        
        if memory_usage:
            context["memory_usage"] = memory_usage
        
        if database_info:
            context["database_info"] = database_info
        
        return context
    
    def log_authentication_debug(
        self,
        token: Optional[str] = None,
        user_info: Optional[Dict[str, Any]] = None,
        auth_result: Optional[str] = None,
        error_details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """记录认证调试信息
        
        Args:
            token: 认证令牌（会被脱敏）
            user_info: 用户信息
            auth_result: 认证结果
            error_details: 错误详情
            
        Returns:
            Dict[str, Any]: 认证调试信息
        """
        debug_info = {
            "timestamp": datetime.now().isoformat(),
            "token_provided": token is not None,
            "token_length": len(token) if token else 0,
            "token_prefix": token[:8] + "..." if token and len(token) > 8 else None,
            "user_info": user_info or {},
            "auth_result": auth_result,
            "error_details": error_details or {}
        }
        
        # 在开发环境记录更详细的信息
        if self.debug_mode:
            logger.debug(f"认证调试信息: {json.dumps(debug_info, ensure_ascii=False, indent=2)}")
        else:
            logger.info(f"认证结果: {auth_result}")
        
        return debug_info
    
    def log_performance_metrics(
        self,
        operation_name: str,
        duration_ms: float,
        additional_metrics: Optional[Dict[str, Any]] = None
    ):
        """记录性能指标
        
        Args:
            operation_name: 操作名称
            duration_ms: 执行时间（毫秒）
            additional_metrics: 额外的性能指标
        """
        metrics = {
            "operation": operation_name,
            "duration_ms": duration_ms,
            "timestamp": datetime.now().isoformat(),
            "environment": self.environment
        }
        
        if additional_metrics:
            metrics.update(additional_metrics)
        
        logger.info(f"性能指标 - {operation_name}: {duration_ms:.2f}ms", extra={"performance_metrics": metrics})
    
    def log_business_event(
        self,
        event_name: str,
        entity_type: str,
        entity_id: str,
        action: str,
        user_id: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """记录业务事件
        
        Args:
            event_name: 事件名称
            entity_type: 实体类型
            entity_id: 实体ID
            action: 操作类型
            user_id: 用户ID
            details: 事件详情
        """
        event_data = {
            "event_name": event_name,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "action": action,
            "user_id": user_id,
            "details": details or {},
            "timestamp": datetime.now().isoformat()
        }
        
        logger.info(f"业务事件 - {event_name}: {action} {entity_type}({entity_id})", extra={"business_event": event_data})
    
    def _sanitize_log_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """清理日志数据中的敏感信息
        
        Args:
            data: 原始日志数据
            
        Returns:
            Dict[str, Any]: 清理后的日志数据
        """
        # 敏感字段列表
        sensitive_fields = {
            'password', 'token', 'authorization', 'cookie', 'session',
            'secret', 'key', 'private', 'credential', 'auth', 'bearer'
        }
        
        def sanitize_dict(obj: Any) -> Any:
            if isinstance(obj, dict):
                sanitized = {}
                for key, value in obj.items():
                    key_lower = key.lower()
                    if any(sensitive in key_lower for sensitive in sensitive_fields):
                        if isinstance(value, str) and len(value) > 8:
                            sanitized[key] = value[:4] + "***" + value[-4:]
                        else:
                            sanitized[key] = "***REDACTED***"
                    else:
                        sanitized[key] = sanitize_dict(value)
                return sanitized
            elif isinstance(obj, list):
                return [sanitize_dict(item) for item in obj]
            elif isinstance(obj, str) and len(obj) > 2000:
                # 截断过长的字符串
                return obj[:2000] + "...[TRUNCATED]"
            else:
                return obj
        
        return sanitize_dict(data)
    
    def get_environment_info(self) -> Dict[str, Any]:
        """获取环境信息
        
        Returns:
            Dict[str, Any]: 环境信息
        """
        return {
            "environment": self.environment,
            "debug_mode": self.debug_mode,
            "log_level": self.log_level,
            "detailed_error_response": self.debug_mode,
            "timestamp": datetime.now().isoformat()
        }


# 全局详细日志记录器实例
detailed_logger = DetailedLogger()