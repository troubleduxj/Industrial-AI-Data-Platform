#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
错误日志记录系统
提供统一的错误日志记录和追踪功能
"""

import json
import traceback
from datetime import datetime
from typing import Any, Dict, Optional
from starlette.requests import Request
from loguru import logger


class ErrorLogger:
    """错误日志记录器"""
    
    @staticmethod
    def log_error(
        request: Request,
        error: Exception,
        error_context: Optional[Dict[str, Any]] = None,
        user_id: Optional[int] = None,
        severity: str = "ERROR"
    ) -> str:
        """
        记录错误日志
        
        Args:
            request: FastAPI请求对象
            error: 异常对象
            error_context: 错误上下文信息
            user_id: 用户ID
            severity: 错误严重程度 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        
        Returns:
            str: 错误追踪ID
        """
        
        # 获取请求ID
        request_id = getattr(request.state, 'request_id', 'unknown')
        api_version = getattr(request.state, 'api_version', 'unknown')
        
        # 构建错误日志数据
        error_data = {
            "request_id": request_id,
            "api_version": api_version,
            "timestamp": datetime.now().isoformat(),
            "error_type": type(error).__name__,
            "error_message": str(error),
            "error_code": getattr(error, 'code', None),
            "error_details": getattr(error, 'details', None),
            "request_info": {
                "method": request.method,
                "url": str(request.url),
                "path": request.url.path,
                "query_params": dict(request.query_params),
                "headers": dict(request.headers),
                "client_ip": request.client.host if request.client else None,
                "user_agent": request.headers.get("user-agent"),
            },
            "user_id": user_id,
            "context": error_context or {},
            "traceback": traceback.format_exc() if severity in ["ERROR", "CRITICAL"] else None
        }
        
        # 过滤敏感信息
        error_data = ErrorLogger._sanitize_log_data(error_data)
        
        # 根据严重程度选择日志级别
        log_message = f"API Error [{request_id}]: {error_data['error_type']} - {error_data['error_message']}"
        
        if severity == "CRITICAL":
            logger.critical(log_message, extra={"error_data": error_data})
        elif severity == "ERROR":
            logger.error(log_message, extra={"error_data": error_data})
        elif severity == "WARNING":
            logger.warning(log_message, extra={"error_data": error_data})
        elif severity == "INFO":
            logger.info(log_message, extra={"error_data": error_data})
        else:
            logger.debug(log_message, extra={"error_data": error_data})
        
        return request_id
    
    @staticmethod
    def log_validation_error(
        request: Request,
        validation_errors: list,
        user_id: Optional[int] = None
    ) -> str:
        """记录验证错误"""
        
        error_context = {
            "validation_errors": validation_errors,
            "error_category": "validation"
        }
        
        # 创建一个虚拟的验证异常
        class ValidationError(Exception):
            def __init__(self, errors):
                self.errors = errors
                super().__init__(f"Validation failed with {len(errors)} errors")
        
        validation_exception = ValidationError(validation_errors)
        
        return ErrorLogger.log_error(
            request=request,
            error=validation_exception,
            error_context=error_context,
            user_id=user_id,
            severity="WARNING"
        )
    
    @staticmethod
    def log_business_error(
        request: Request,
        business_rule: str,
        error_message: str,
        user_id: Optional[int] = None,
        additional_context: Optional[Dict[str, Any]] = None
    ) -> str:
        """记录业务逻辑错误"""
        
        error_context = {
            "business_rule": business_rule,
            "error_category": "business_logic",
            **(additional_context or {})
        }
        
        # 创建业务逻辑异常
        class BusinessLogicError(Exception):
            def __init__(self, rule, message):
                self.rule = rule
                super().__init__(message)
        
        business_exception = BusinessLogicError(business_rule, error_message)
        
        return ErrorLogger.log_error(
            request=request,
            error=business_exception,
            error_context=error_context,
            user_id=user_id,
            severity="WARNING"
        )
    
    @staticmethod
    def log_security_event(
        request: Request,
        event_type: str,
        description: str,
        user_id: Optional[int] = None,
        severity: str = "WARNING"
    ) -> str:
        """记录安全相关事件"""
        
        error_context = {
            "event_type": event_type,
            "description": description,
            "error_category": "security",
            "client_info": {
                "ip": request.client.host if request.client else None,
                "user_agent": request.headers.get("user-agent"),
                "referer": request.headers.get("referer")
            }
        }
        
        # 创建安全事件异常
        class SecurityEvent(Exception):
            def __init__(self, event_type, description):
                self.event_type = event_type
                super().__init__(f"Security event: {event_type} - {description}")
        
        security_exception = SecurityEvent(event_type, description)
        
        return ErrorLogger.log_error(
            request=request,
            error=security_exception,
            error_context=error_context,
            user_id=user_id,
            severity=severity
        )
    
    @staticmethod
    def _sanitize_log_data(data: Dict[str, Any]) -> Dict[str, Any]:
        """清理日志数据中的敏感信息"""
        
        # 需要过滤的敏感字段
        sensitive_fields = {
            'password', 'token', 'authorization', 'cookie', 'session',
            'secret', 'key', 'private', 'credential', 'auth'
        }
        
        def sanitize_dict(obj: Any) -> Any:
            if isinstance(obj, dict):
                sanitized = {}
                for key, value in obj.items():
                    key_lower = key.lower()
                    if any(sensitive in key_lower for sensitive in sensitive_fields):
                        sanitized[key] = "***REDACTED***"
                    else:
                        sanitized[key] = sanitize_dict(value)
                return sanitized
            elif isinstance(obj, list):
                return [sanitize_dict(item) for item in obj]
            elif isinstance(obj, str) and len(obj) > 1000:
                # 截断过长的字符串
                return obj[:1000] + "...[TRUNCATED]"
            else:
                return obj
        
        return sanitize_dict(data)
    
    @staticmethod
    def get_error_metrics(
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        api_version: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        获取错误统计指标
        注意：这是一个示例方法，实际实现需要根据日志存储方式调整
        """
        
        # 这里应该实现从日志系统或数据库中查询错误统计的逻辑
        # 目前返回示例数据
        return {
            "total_errors": 0,
            "error_by_type": {},
            "error_by_endpoint": {},
            "error_by_user": {},
            "error_trends": [],
            "most_common_errors": [],
            "critical_errors": 0,
            "api_version": api_version,
            "date_range": {
                "start": start_date.isoformat() if start_date else None,
                "end": end_date.isoformat() if end_date else None
            }
        }


class ErrorMetrics:
    """错误指标收集器"""
    
    def __init__(self):
        self._error_counts = {}
        self._error_types = {}
        self._endpoint_errors = {}
    
    def record_error(
        self,
        error_type: str,
        endpoint: str,
        api_version: str = "v1"
    ):
        """记录错误指标"""
        
        # 总错误计数
        key = f"{api_version}_{error_type}"
        self._error_counts[key] = self._error_counts.get(key, 0) + 1
        
        # 错误类型统计
        self._error_types[error_type] = self._error_types.get(error_type, 0) + 1
        
        # 端点错误统计
        endpoint_key = f"{api_version}_{endpoint}"
        self._endpoint_errors[endpoint_key] = self._endpoint_errors.get(endpoint_key, 0) + 1
    
    def get_metrics(self) -> Dict[str, Any]:
        """获取错误指标"""
        return {
            "error_counts": self._error_counts,
            "error_types": self._error_types,
            "endpoint_errors": self._endpoint_errors,
            "timestamp": datetime.now().isoformat()
        }
    
    def reset_metrics(self):
        """重置指标"""
        self._error_counts.clear()
        self._error_types.clear()
        self._endpoint_errors.clear()


# 全局错误指标收集器实例
error_metrics = ErrorMetrics()