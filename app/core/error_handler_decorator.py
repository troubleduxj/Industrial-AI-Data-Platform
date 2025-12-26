#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
V2 API错误处理装饰器
提供统一的错误处理和响应格式化
"""

import functools
from typing import Any, Callable, Optional, Type, Union
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from app.core.exceptions import (
    APIException, ValidationException, AuthenticationException,
    AuthorizationException, ResourceNotFoundException, BusinessLogicException,
    DatabaseException, ExternalServiceException
)
from app.core.response_formatter_v2 import ResponseFormatterV2, APIv2ErrorDetail
from app.core.error_logger import ErrorLogger, error_metrics
from app.core.input_validator import InputValidator


def handle_v2_errors(
    log_errors: bool = True,
    catch_all: bool = True,
    custom_error_mapping: Optional[dict] = None
):
    """
    V2 API错误处理装饰器
    
    Args:
        log_errors: 是否记录错误日志
        catch_all: 是否捕获所有未处理的异常
        custom_error_mapping: 自定义错误映射
    """
    
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            request: Optional[Request] = None
            
            # 尝试从参数中获取Request对象
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break
            
            # 如果没有找到Request对象，尝试从kwargs中获取
            if not request:
                request = kwargs.get('request')
            
            # 确保API版本设置为v2
            if request and not hasattr(request.state, 'api_version'):
                request.state.api_version = 'v2'
            
            formatter = ResponseFormatterV2(request)
            
            try:
                # 执行原函数
                result = await func(*args, **kwargs)
                return result
                
            except ValidationError as e:
                # Pydantic验证错误
                if log_errors and request:
                    user_id = getattr(request.state, 'user_id', None)
                    ErrorLogger.log_validation_error(
                        request=request,
                        validation_errors=[{
                            "field": ".".join(str(x) for x in error["loc"]),
                            "message": error["msg"],
                            "type": error["type"],
                            "input": error.get("input")
                        } for error in e.errors()],
                        user_id=user_id
                    )
                
                # 转换为V2错误格式
                error_details = []
                for error in e.errors():
                    error_details.append(APIv2ErrorDetail(
                        field=".".join(str(x) for x in error["loc"]),
                        code=error["type"],
                        message=error["msg"],
                        value=error.get("input")
                    ))
                
                return formatter.validation_error(
                    message="数据验证失败",
                    details=error_details
                )
                
            except APIException as e:
                # 自定义API异常
                if log_errors and request:
                    user_id = getattr(request.state, 'user_id', None)
                    severity = "ERROR" if e.code >= 500 else "WARNING"
                    ErrorLogger.log_error(
                        request=request,
                        error=e,
                        user_id=user_id,
                        severity=severity
                    )
                
                # 根据异常类型返回相应的响应
                if isinstance(e, AuthenticationException):
                    return formatter.unauthorized(
                        message=e.message,
                        suggestion="请提供有效的认证凭据或重新登录"
                    )
                elif isinstance(e, AuthorizationException):
                    return formatter.forbidden(
                        message=e.message,
                        suggestion="请联系管理员获取相应权限"
                    )
                elif isinstance(e, ResourceNotFoundException):
                    return formatter.not_found(
                        message=e.message,
                        resource_type=e.details.get("resource_type"),
                        resource_id=e.details.get("resource_id")
                    )
                elif isinstance(e, ValidationException):
                    details = []
                    if e.details.get("field"):
                        details.append(APIv2ErrorDetail(
                            field=e.details["field"],
                            code=e.error_code,
                            message=e.message,
                            value=e.details.get("value")
                        ))
                    return formatter.validation_error(
                        message=e.message,
                        details=details
                    )
                elif isinstance(e, BusinessLogicException):
                    return formatter.bad_request(
                        message=e.message,
                        suggestion="请检查业务规则或联系管理员"
                    )
                elif isinstance(e, DatabaseException):
                    return formatter.internal_error(
                        message="数据库操作失败",
                        error_detail=e.message
                    )
                elif isinstance(e, ExternalServiceException):
                    return formatter.error(
                        message=e.message,
                        code=502,
                        error_type="EXTERNAL_SERVICE_ERROR",
                        suggestion="外部服务暂时不可用，请稍后重试"
                    )
                else:
                    # 其他API异常
                    if e.code >= 500:
                        return formatter.internal_error(
                            message=e.message,
                            error_detail=str(e.details) if e.details else None
                        )
                    else:
                        return formatter.bad_request(message=e.message)
                        
            except HTTPException as e:
                # FastAPI HTTP异常
                if log_errors and request:
                    user_id = getattr(request.state, 'user_id', None)
                    severity = "ERROR" if e.status_code >= 500 else "WARNING"
                    ErrorLogger.log_error(
                        request=request,
                        error=e,
                        user_id=user_id,
                        severity=severity
                    )
                
                # 根据状态码返回相应的响应
                if e.status_code == 401:
                    return formatter.unauthorized(message=e.detail)
                elif e.status_code == 403:
                    return formatter.forbidden(message=e.detail)
                elif e.status_code == 404:
                    return formatter.not_found(message=e.detail)
                elif e.status_code == 422:
                    return formatter.validation_error(message=e.detail)
                elif e.status_code >= 500:
                    return formatter.internal_error(message=e.detail)
                else:
                    return formatter.bad_request(message=e.detail)
                    
            except Exception as e:
                # 未捕获的异常
                if catch_all:
                    if log_errors and request:
                        user_id = getattr(request.state, 'user_id', None)
                        ErrorLogger.log_error(
                            request=request,
                            error=e,
                            user_id=user_id,
                            severity="CRITICAL"
                        )
                    
                    return formatter.internal_error(
                        message="服务器内部错误",
                        error_detail=f"{type(e).__name__}: {str(e)}"
                    )
                else:
                    # 重新抛出异常
                    raise
        
        return wrapper
    return decorator


def validate_input(validator_class: Type[InputValidator] = None, **validator_kwargs):
    """
    输入验证装饰器
    
    Args:
        validator_class: 验证器类
        **validator_kwargs: 验证器参数
    """
    
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            request: Optional[Request] = None
            
            # 尝试从参数中获取Request对象
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break
            
            if not request:
                request = kwargs.get('request')
            
            # 获取请求数据
            request_data = {}
            if request:
                # 合并查询参数和请求体
                request_data.update(dict(request.query_params))
                
                if request.method in ["POST", "PUT", "PATCH"]:
                    try:
                        body = await request.json()
                        if isinstance(body, dict):
                            request_data.update(body)
                    except Exception:
                        pass
            
            # 创建验证器
            if validator_class:
                validator = validator_class(request)
            else:
                validator = InputValidator(request)
                
                # 应用验证规则
                for field_name, rules in validator_kwargs.items():
                    if isinstance(rules, list):
                        for rule in rules:
                            validator.add_rule(field_name, rule)
                    else:
                        validator.add_rule(field_name, rules)
            
            # 执行验证
            if not validator.validate(request_data):
                formatter = ResponseFormatterV2(request)
                return formatter.validation_error(
                    message="输入验证失败",
                    details=validator.get_errors()
                )
            
            # 验证通过，执行原函数
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


def require_auth(roles: Optional[list] = None, permissions: Optional[list] = None):
    """
    认证和授权装饰器
    
    Args:
        roles: 需要的角色列表
        permissions: 需要的权限列表
    """
    
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            request: Optional[Request] = None
            
            # 尝试从参数中获取Request对象
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break
            
            if not request:
                request = kwargs.get('request')
            
            formatter = ResponseFormatterV2(request)
            
            # 检查认证
            token = request.headers.get("Authorization", "").replace("Bearer ", "")
            if not token:
                return formatter.unauthorized(
                    message="缺少认证令牌",
                    suggestion="请在请求头中提供有效的Authorization令牌"
                )
            
            # 这里应该实现实际的认证逻辑
            # 示例代码，实际实现需要根据项目的认证系统调整
            try:
                from app.core.dependency import AuthControl
                user = await AuthControl.is_authed(token)
                if not user:
                    return formatter.unauthorized(
                        message="认证令牌无效",
                        suggestion="请重新登录获取有效令牌"
                    )
                
                # 设置用户信息到请求状态
                request.state.user_id = user.id
                request.state.user = user
                
                # 检查角色权限（如果指定）
                if roles:
                    user_roles = [role.role_name for role in await user.roles.all()]
                    if not any(role in user_roles for role in roles):
                        return formatter.forbidden(
                            message="权限不足",
                            suggestion=f"需要以下角色之一: {', '.join(roles)}"
                        )
                
                # 检查具体权限（如果指定）
                if permissions:
                    user_permissions = await AuthControl.get_user_permissions(user.id)
                    if not any(perm in user_permissions for perm in permissions):
                        return formatter.forbidden(
                            message="权限不足",
                            suggestion=f"需要以下权限之一: {', '.join(permissions)}"
                        )
                
            except Exception as e:
                return formatter.unauthorized(
                    message="认证失败",
                    suggestion="请检查认证令牌是否有效"
                )
            
            # 认证和授权通过，执行原函数
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


def rate_limit(max_requests: int = 100, window_seconds: int = 60):
    """
    限流装饰器
    
    Args:
        max_requests: 时间窗口内最大请求数
        window_seconds: 时间窗口（秒）
    """
    
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            request: Optional[Request] = None
            
            # 尝试从参数中获取Request对象
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break
            
            if not request:
                request = kwargs.get('request')
            
            # 这里应该实现实际的限流逻辑
            # 示例代码，实际实现需要使用Redis或其他存储
            client_ip = request.client.host if request.client else "unknown"
            
            # 简单的内存限流示例（生产环境应使用Redis）
            import time
            from collections import defaultdict
            
            if not hasattr(rate_limit, '_requests'):
                rate_limit._requests = defaultdict(list)
            
            now = time.time()
            client_requests = rate_limit._requests[client_ip]
            
            # 清理过期的请求记录
            client_requests[:] = [req_time for req_time in client_requests if now - req_time < window_seconds]
            
            # 检查是否超过限制
            if len(client_requests) >= max_requests:
                formatter = ResponseFormatterV2(request)
                return formatter.error(
                    message="请求频率超限",
                    code=429,
                    error_type="RATE_LIMIT_EXCEEDED",
                    suggestion=f"请在{window_seconds}秒后重试"
                )
            
            # 记录当前请求
            client_requests.append(now)
            
            # 执行原函数
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


# 组合装饰器
def v2_api_endpoint(
    require_auth_: bool = True,
    roles: Optional[list] = None,
    permissions: Optional[list] = None,
    validator_class: Type[InputValidator] = None,
    rate_limit_: Optional[tuple] = None,
    log_errors: bool = True,
    **validator_kwargs
):
    """
    V2 API端点组合装饰器
    
    Args:
        require_auth_: 是否需要认证
        roles: 需要的角色列表
        permissions: 需要的权限列表
        validator_class: 验证器类
        rate_limit_: 限流配置 (max_requests, window_seconds)
        log_errors: 是否记录错误日志
        **validator_kwargs: 验证器参数
    """
    
    def decorator(func: Callable) -> Callable:
        # 应用装饰器（注意顺序）
        decorated_func = func
        
        # 1. 错误处理（最外层）
        decorated_func = handle_v2_errors(log_errors=log_errors)(decorated_func)
        
        # 2. 限流
        if rate_limit_:
            max_requests, window_seconds = rate_limit_
            decorated_func = rate_limit(max_requests, window_seconds)(decorated_func)
        
        # 3. 认证和授权
        if require_auth_:
            decorated_func = require_auth(roles, permissions)(decorated_func)
        
        # 4. 输入验证
        if validator_class or validator_kwargs:
            decorated_func = validate_input(validator_class, **validator_kwargs)(decorated_func)
        
        return decorated_func
    
    return decorator