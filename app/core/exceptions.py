from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import ValidationError
from fastapi.exceptions import (
    HTTPException,
    RequestValidationError,
    ResponseValidationError,
)
from fastapi.requests import Request
from fastapi.responses import JSONResponse
from tortoise.exceptions import DoesNotExist, IntegrityError
from app.schemas.base import APIError, error_response
from app.core.error_logger import ErrorLogger, error_metrics
from loguru import logger


class SettingNotFound(Exception):
    pass

# 自定义异常类
class APIException(Exception):
    """基础API异常类"""
    def __init__(self, message: str, code: int = 400, details: dict = None, error_code: str = None):
        self.message = message
        self.code = code
        self.details = details or {}
        self.error_code = error_code or f"API_{code}"
        super().__init__(message)

class ValidationException(APIException):
    """验证异常"""
    def __init__(self, message: str, field: str = None, details: dict = None):
        super().__init__(
            message=message,
            code=422,
            details={"field": field, **(details or {})},
            error_code="VALIDATION_ERROR"
        )

class AuthenticationException(APIException):
    """认证异常"""
    def __init__(self, message: str = "认证失败", details: dict = None):
        super().__init__(
            message=message,
            code=401,
            details=details,
            error_code="AUTHENTICATION_ERROR"
        )

class AuthorizationException(APIException):
    """授权异常"""
    def __init__(self, message: str = "权限不足", details: dict = None):
        super().__init__(
            message=message,
            code=403,
            details=details,
            error_code="AUTHORIZATION_ERROR"
        )

class ResourceNotFoundException(APIException):
    """资源未找到异常"""
    def __init__(self, message: str = "资源未找到", resource_type: str = None, resource_id: str = None):
        details = {}
        if resource_type:
            details["resource_type"] = resource_type
        if resource_id:
            details["resource_id"] = resource_id
        
        super().__init__(
            message=message,
            code=404,
            details=details,
            error_code="RESOURCE_NOT_FOUND"
        )

class BusinessLogicException(APIException):
    """业务逻辑异常"""
    def __init__(self, message: str, business_code: str = None, details: dict = None):
        super().__init__(
            message=message,
            code=400,
            details=details,
            error_code=business_code or "BUSINESS_LOGIC_ERROR"
        )

class DatabaseException(APIException):
    """数据库异常"""
    def __init__(self, message: str = "数据库操作失败", details: dict = None):
        super().__init__(
            message=message,
            code=500,
            details=details,
            error_code="DATABASE_ERROR"
        )

class ExternalServiceException(APIException):
    """外部服务异常"""
    def __init__(self, message: str = "外部服务调用失败", service_name: str = None, details: dict = None):
        if service_name and details:
            details["service_name"] = service_name
        elif service_name:
            details = {"service_name": service_name}
        
        super().__init__(
            message=message,
            code=502,
            details=details,
            error_code="EXTERNAL_SERVICE_ERROR"
        )


# 标准化异常处理器
async def api_exception_handler(request: Request, exc: APIException) -> JSONResponse:
    """处理自定义API异常"""
    api_version = getattr(request.state, 'api_version', 'v1')
    
    # 记录错误日志
    user_id = getattr(request.state, 'user_id', None)
    error_context = {
        "exception_type": type(exc).__name__,
        "error_code": exc.error_code,
        "details": exc.details
    }
    
    # 根据错误严重程度确定日志级别
    severity = "ERROR" if exc.code >= 500 else "WARNING"
    if isinstance(exc, (AuthenticationException, AuthorizationException)):
        severity = "WARNING"  # 认证/授权错误通常不是系统错误
    
    request_id = ErrorLogger.log_error(
        request=request,
        error=exc,
        error_context=error_context,
        user_id=user_id,
        severity=severity
    )
    
    # 记录错误指标
    error_metrics.record_error(
        error_type=type(exc).__name__,
        endpoint=request.url.path,
        api_version=api_version
    )
    
    # 根据API版本返回不同格式的响应
    if api_version == 'v2':
        # v2版本使用ResponseFormatterV2生成标准化响应格式
        from app.core.response_formatter_v2 import ResponseFormatterV2, APIv2ErrorDetail
        formatter = ResponseFormatterV2(request)
        
        # 根据异常类型选择合适的响应方法
        if isinstance(exc, AuthenticationException):
            return formatter.unauthorized(
                message=exc.message,
                suggestion="请提供有效的认证凭据或重新登录"
            )
        elif isinstance(exc, AuthorizationException):
            return formatter.forbidden(
                message=exc.message,
                suggestion="请联系管理员获取相应权限"
            )
        elif isinstance(exc, ResourceNotFoundException):
            return formatter.not_found(
                message=exc.message,
                resource_type=exc.details.get("resource_type"),
                resource_id=exc.details.get("resource_id")
            )
        elif isinstance(exc, ValidationException):
            # 构建验证错误详情
            details = []
            if exc.details.get("field"):
                details.append(APIv2ErrorDetail(
                    field=exc.details["field"],
                    code=exc.error_code,
                    message=exc.message,
                    value=exc.details.get("value")
                ))
            return formatter.validation_error(
                message=exc.message,
                details=details
            )
        elif exc.code >= 500:
            return formatter.internal_error(
                message=exc.message,
                error_id=request_id,
                error_detail=str(exc.details) if exc.details else None
            )
        else:
            # 其他客户端错误
            return formatter.bad_request(
                message=exc.message,
                details=[APIv2ErrorDetail(
                    field="general",
                    code=exc.error_code,
                    message=exc.message,
                    value=exc.details
                )] if exc.details else None
            )
    else:
        # v1版本保持原有格式兼容性
        content = {
            "code": exc.code,
            "msg": exc.message,
            "data": None
        }
        return JSONResponse(content=content, status_code=exc.code)

async def DoesNotExistHandle(req: Request, exc: DoesNotExist) -> JSONResponse:
    """处理Tortoise ORM DoesNotExist异常"""
    api_version = getattr(req.state, 'api_version', 'v1')
    
    # 记录错误日志
    user_id = getattr(req.state, 'user_id', None)
    request_id = ErrorLogger.log_error(
        request=req,
        error=exc,
        error_context={"query_params": dict(req.query_params)},
        user_id=user_id,
        severity="INFO"  # 资源不存在通常不是系统错误
    )
    
    # 记录错误指标
    error_metrics.record_error(
        error_type="DoesNotExist",
        endpoint=req.url.path,
        api_version=api_version
    )
    
    if api_version == 'v2':
        from app.core.response_formatter_v2 import ResponseFormatterV2
        formatter = ResponseFormatterV2(req)
        return formatter.not_found(
            message="请求的资源不存在",
            suggestion="请检查资源ID是否正确或资源是否已被删除"
        )
    else:
        # 保持v1版本兼容性
        content = dict(
            code=404,
            msg=f"Object has not found, exc: {exc}, query_params: {req.query_params}",
        )
        return JSONResponse(content=content, status_code=404)

async def IntegrityHandle(req: Request, exc: IntegrityError) -> JSONResponse:
    """处理数据库完整性约束异常"""
    api_version = getattr(req.state, 'api_version', 'v1')
    
    # 记录错误日志
    user_id = getattr(req.state, 'user_id', None)
    request_id = ErrorLogger.log_error(
        request=req,
        error=exc,
        error_context={"constraint_violation": str(exc)},
        user_id=user_id,
        severity="WARNING"
    )
    
    # 记录错误指标
    error_metrics.record_error(
        error_type="IntegrityError",
        endpoint=req.url.path,
        api_version=api_version
    )
    
    if api_version == 'v2':
        from app.core.response_formatter_v2 import ResponseFormatterV2
        formatter = ResponseFormatterV2(req)
        return formatter.conflict(
            message="数据完整性约束冲突",
            suggestion="请检查数据是否重复或违反了业务规则"
        )
    else:
        # 保持v1版本兼容性
        content = dict(
            code=500,
            msg=f"IntegrityError，{exc}",
        )
        return JSONResponse(content=content, status_code=500)

async def HttpExcHandle(req: Request, exc: HTTPException) -> JSONResponse:
    """处理FastAPI HTTP异常"""
    api_version = getattr(req.state, 'api_version', 'v1')
    
    # 记录错误日志
    user_id = getattr(req.state, 'user_id', None)
    severity = "ERROR" if exc.status_code >= 500 else "WARNING"
    request_id = ErrorLogger.log_error(
        request=req,
        error=exc,
        error_context={"status_code": exc.status_code, "detail": exc.detail},
        user_id=user_id,
        severity=severity
    )
    
    # 记录错误指标
    error_metrics.record_error(
        error_type=f"HTTPException_{exc.status_code}",
        endpoint=req.url.path,
        api_version=api_version
    )
    
    if api_version == 'v2':
        from app.core.response_formatter_v2 import ResponseFormatterV2
        formatter = ResponseFormatterV2(req)
        
        # 根据HTTP状态码选择合适的响应方法
        if exc.status_code == 401:
            return formatter.unauthorized(message=exc.detail)
        elif exc.status_code == 403:
            return formatter.forbidden(message=exc.detail)
        elif exc.status_code == 404:
            return formatter.not_found(message=exc.detail)
        elif exc.status_code == 422:
            return formatter.validation_error(message=exc.detail)
        elif exc.status_code >= 500:
            return formatter.internal_error(message=exc.detail, error_id=request_id)
        else:
            return formatter.bad_request(message=exc.detail)
    else:
        # 保持v1版本兼容性
        content = dict(code=exc.status_code, msg=exc.detail, data=None)
        return JSONResponse(content=content, status_code=exc.status_code)

async def ValidationErrorHandle(req: Request, exc: ValidationError) -> JSONResponse:
    """处理Pydantic验证异常"""
    api_version = getattr(req.state, 'api_version', 'v1')
    
    # 添加详细的验证错误日志
    # 检查是否是WebSocket请求（WebSocket对象没有method属性）
    if hasattr(req, 'method'):
        logger.error(f"ValidationError for {req.method} {req.url.path}")
    else:
        logger.error(f"ValidationError for WebSocket {req.url.path}")
    logger.error(f"Raw validation errors: {exc.errors()}")
    
    # 提取验证错误详情
    validation_errors = []
    for error in exc.errors():
        validation_errors.append({
            "field": ".".join(str(x) for x in error["loc"]),
            "message": error["msg"],
            "type": error["type"],
            "input": error.get("input")
        })
    
    logger.error(f"Processed validation errors: {validation_errors}")
    
    # 记录验证错误日志
    user_id = getattr(req.state, 'user_id', None)
    request_id = ErrorLogger.log_validation_error(
        request=req,
        validation_errors=validation_errors,
        user_id=user_id
    )
    
    # 记录错误指标
    error_metrics.record_error(
        error_type="ValidationError",
        endpoint=req.url.path,
        api_version=api_version
    )
    
    if api_version == 'v2':
        # 使用ResponseFormatterV2来生成符合V2标准的错误响应
        from app.core.response_formatter_v2 import ResponseFormatterV2, APIv2ErrorDetail
        formatter = ResponseFormatterV2(req)
        
        # 转换验证错误为APIv2ErrorDetail格式
        error_details = []
        for error in validation_errors:
            error_details.append(APIv2ErrorDetail(
                field=error["field"],
                code=error["type"],
                message=error["message"],
                value=str(error.get("input")) if error.get("input") is not None else None
            ))
        
        return formatter.validation_error(
            message="请求参数验证失败",
            details=error_details
        )
    else:
        # 保持v1版本兼容性
        content = dict(code=422, msg=f"ValidationError, {exc}")
        return JSONResponse(content=content, status_code=422)


async def RequestValidationHandle(req: Request, exc: RequestValidationError) -> JSONResponse:
    """处理请求验证异常"""
    api_version = getattr(req.state, 'api_version', 'v1')
    
    # 添加详细的验证错误日志
    logger.error(f"RequestValidationError for {req.method} {req.url.path}")
    logger.error(f"Raw validation errors: {exc.errors()}")
    
    # 提取验证错误详情
    validation_errors = []
    for error in exc.errors():
        validation_errors.append({
            "field": ".".join(str(x) for x in error["loc"]),
            "message": error["msg"],
            "type": error["type"],
            "input": error.get("input")
        })
    
    logger.error(f"Processed validation errors: {validation_errors}")
    
    # 记录验证错误日志
    user_id = getattr(req.state, 'user_id', None)
    request_id = ErrorLogger.log_validation_error(
        request=req,
        validation_errors=validation_errors,
        user_id=user_id
    )
    
    # 记录错误指标
    error_metrics.record_error(
        error_type="RequestValidationError",
        endpoint=req.url.path,
        api_version=api_version
    )
    
    if api_version == 'v2':
        # 使用ResponseFormatterV2来生成符合V2标准的错误响应
        from app.core.response_formatter_v2 import ResponseFormatterV2, APIv2ErrorDetail
        formatter = ResponseFormatterV2(req)
        
        # 转换验证错误为APIv2ErrorDetail格式
        error_details = []
        for error in validation_errors:
            error_details.append(APIv2ErrorDetail(
                field=error["field"],
                code=error["type"],
                message=error["message"],
                value=str(error.get("input")) if error.get("input") is not None else None
            ))
        
        return formatter.validation_error(
            message="请求参数验证失败",
            details=error_details
        )
    else:
        # 保持v1版本兼容性
        content = dict(code=422, msg=f"RequestValidationError, {exc}")
        return JSONResponse(content=content, status_code=422)

async def ResponseValidationHandle(req: Request, exc: ResponseValidationError) -> JSONResponse:
    """处理响应验证异常"""
    api_version = getattr(req.state, 'api_version', 'v1')
    
    # 记录响应验证错误日志
    user_id = getattr(req.state, 'user_id', None)
    request_id = ErrorLogger.log_error(
        request=req,
        error=exc,
        error_context={"validation_errors": exc.errors()},
        user_id=user_id,
        severity="CRITICAL"  # 响应验证错误是严重的系统问题
    )
    
    # 记录错误指标
    error_metrics.record_error(
        error_type="ResponseValidationError",
        endpoint=req.url.path,
        api_version=api_version
    )
    
    if api_version == 'v2':
        from app.core.response_formatter_v2 import ResponseFormatterV2
        formatter = ResponseFormatterV2(req)
        return formatter.internal_error(
            message="服务器响应格式错误",
            error_id=request_id,
            error_detail=str(exc)
        )
    else:
        # 保持v1版本兼容性
        content = dict(code=500, msg=f"ResponseValidationError, {exc}")
        return JSONResponse(content=content, status_code=500)

async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """处理未捕获的通用异常"""
    api_version = getattr(request.state, 'api_version', 'v1')
    
    # 记录未捕获异常日志
    user_id = getattr(request.state, 'user_id', None)
    request_id = ErrorLogger.log_error(
        request=request,
        error=exc,
        error_context={"uncaught_exception": True},
        user_id=user_id,
        severity="CRITICAL"  # 未捕获异常是严重的系统问题
    )
    
    # 记录错误指标
    error_metrics.record_error(
        error_type=type(exc).__name__,
        endpoint=request.url.path,
        api_version=api_version
    )
    
    if api_version == 'v2':
        from app.core.response_formatter_v2 import ResponseFormatterV2
        formatter = ResponseFormatterV2(request)
        return formatter.internal_error(
            message="服务器内部错误",
            error_id=request_id,
            error_detail=f"{type(exc).__name__}: {str(exc)}"
        )
    else:
        # 保持v1版本兼容性
        content = dict(
            code=500,
            msg=f"Internal server error: {str(exc)}",
            data=None
        )
        return JSONResponse(content=content, status_code=500)



def get_error_category(error: Exception) -> str:
    """获取错误类别"""
    error_categories = {
        APIException: "api_error",
        ValidationException: "validation_error",
        AuthenticationException: "authentication_error",
        AuthorizationException: "authorization_error",
        ResourceNotFoundException: "not_found_error",
        BusinessLogicException: "business_error",
        DatabaseException: "database_error",
        ExternalServiceException: "external_service_error",
        DoesNotExist: "not_found_error",
        IntegrityError: "database_error",
        HTTPException: "http_error",
        RequestValidationError: "validation_error",
        ResponseValidationError: "server_error"
    }
    
    for exception_type, category in error_categories.items():
        if isinstance(error, exception_type):
            return category
    
    return "unknown_error"

# 错误码映射
ERROR_CODES = {
    # 认证相关
    "AUTHENTICATION_ERROR": {
        "code": 401,
        "message": "认证失败",
        "description": "用户身份验证失败，请检查登录凭据"
    },
    "AUTHORIZATION_ERROR": {
        "code": 403,
        "message": "权限不足",
        "description": "用户没有执行此操作的权限"
    },
    "TOKEN_EXPIRED": {
        "code": 401,
        "message": "登录已过期",
        "description": "访问令牌已过期，请重新登录"
    },
    "TOKEN_INVALID": {
        "code": 401,
        "message": "无效的访问令牌",
        "description": "提供的访问令牌格式不正确或已失效"
    },
    
    # 验证相关
    "VALIDATION_ERROR": {
        "code": 422,
        "message": "参数验证失败",
        "description": "请求参数不符合要求"
    },
    "REQUIRED_FIELD_MISSING": {
        "code": 422,
        "message": "必填字段缺失",
        "description": "请求中缺少必需的字段"
    },
    "INVALID_FORMAT": {
        "code": 422,
        "message": "格式不正确",
        "description": "字段格式不符合要求"
    },
    
    # 资源相关
    "RESOURCE_NOT_FOUND": {
        "code": 404,
        "message": "资源未找到",
        "description": "请求的资源不存在"
    },
    "RESOURCE_ALREADY_EXISTS": {
        "code": 409,
        "message": "资源已存在",
        "description": "尝试创建的资源已经存在"
    },
    "RESOURCE_CONFLICT": {
        "code": 409,
        "message": "资源冲突",
        "description": "资源状态冲突，无法执行操作"
    },
    
    # 业务逻辑相关
    "BUSINESS_LOGIC_ERROR": {
        "code": 400,
        "message": "业务逻辑错误",
        "description": "操作不符合业务规则"
    },
    "OPERATION_NOT_ALLOWED": {
        "code": 400,
        "message": "操作不被允许",
        "description": "当前状态下不允许执行此操作"
    },
    
    # 系统相关
    "DATABASE_ERROR": {
        "code": 500,
        "message": "数据库错误",
        "description": "数据库操作失败"
    },
    "EXTERNAL_SERVICE_ERROR": {
        "code": 502,
        "message": "外部服务错误",
        "description": "外部服务调用失败"
    },
    "INTERNAL_SERVER_ERROR": {
        "code": 500,
        "message": "服务器内部错误",
        "description": "服务器处理请求时发生未知错误"
    },
    
    # 限流相关
    "RATE_LIMIT_EXCEEDED": {
        "code": 429,
        "message": "请求频率超限",
        "description": "请求过于频繁，请稍后再试"
    },
    
    # API版本相关
    "UNSUPPORTED_API_VERSION": {
        "code": 400,
        "message": "不支持的API版本",
        "description": "请求的API版本不被支持"
    },
    "API_VERSION_DEPRECATED": {
        "code": 400,
        "message": "API版本已弃用",
        "description": "使用的API版本已被弃用，请升级到新版本"
    }
}

def get_error_info(error_code: str) -> dict:
    """根据错误码获取错误信息"""
    return ERROR_CODES.get(error_code, {
        "code": 500,
        "message": "未知错误",
        "description": "发生了未知的错误"
    })
