#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API v2 响应格式标准化器
提供增强的响应格式，包含HATEOAS支持、请求追踪等功能
"""

import time
import uuid
import json
from decimal import Decimal
from datetime import datetime
from typing import Any, Optional, Dict, List, Union
from urllib.parse import urlencode

from fastapi import Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict


class DecimalEncoder(json.JSONEncoder):
    """自定义JSON编码器，处理Decimal类型"""
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)


class HATEOASLinks(BaseModel):
    """HATEOAS链接模型"""
    self: Optional[str] = None
    next: Optional[str] = None
    prev: Optional[str] = None
    first: Optional[str] = None
    last: Optional[str] = None
    related: Optional[Dict[str, str]] = None


class ResponseMeta(BaseModel):
    """响应元数据模型"""
    version: str = "v2"
    total: Optional[int] = None
    page: Optional[int] = None
    page_size: Optional[int] = None
    has_next: Optional[bool] = None
    has_prev: Optional[bool] = None
    timestamp: str
    request_id: str
    execution_time: Optional[int] = None  # 执行时间(毫秒)


class APIv2Response(BaseModel):
    """API v2标准响应格式"""
    model_config = ConfigDict(json_encoders={
        datetime: lambda v: v.isoformat(),
        Decimal: lambda v: float(v)
    })
    
    success: bool
    code: int
    message: str
    data: Optional[Any] = None
    meta: ResponseMeta
    links: Optional[HATEOASLinks] = None
    generated_sql: Optional[str] = None  # 用于调试，返回生成的SQL


class APIv2ErrorDetail(BaseModel):
    """API v2错误详情"""
    field: Optional[str] = None
    code: str
    message: str
    value: Optional[Any] = None
    
    # 允许任意类型的值
    model_config = ConfigDict(arbitrary_types_allowed=True)


class APIv2ErrorResponse(BaseModel):
    """API v2错误响应格式"""
    success: bool = False
    code: int
    message: str
    error_type: str
    error: Dict[str, Any]
    meta: ResponseMeta
    links: Optional[Dict[str, str]] = None


class ResponseFormatterV2:
    """API v2响应格式化器"""
    
    def __init__(self, request: Optional[Request] = None):
        self.request = request
        # 优先使用请求中已有的request_id，如果没有则生成新的
        self.request_id = getattr(request.state, 'request_id', str(uuid.uuid4())) if request else str(uuid.uuid4())
        self.start_time = getattr(request.state, 'start_time', time.time()) if request else time.time()
    
    async def format_success_response(
        self,
        request: Request,
        data: Optional[Any] = None,
        message: str = "success",
        status_code: int = 200,
        **kwargs
    ) -> JSONResponse:
        """格式化成功响应 - 兼容旧接口"""
        return self.success(data=data, message=message, code=status_code, **kwargs)
    
    async def format_error_response(
        self,
        request: Request,
        error: Optional[Exception] = None,
        message: str = "error",
        status_code: int = 400,
        **kwargs
    ) -> JSONResponse:
        """格式化错误响应 - 兼容旧接口"""
        if error:
            error_message = f"{message}: {str(error)}"
        else:
            error_message = message
        return self.error(message=error_message, code=status_code, **kwargs)
    
    async def format_list_response(
        self,
        request: Request,
        data: List[Any],
        total: int,
        page: int = 1,
        page_size: int = 20,
        message: str = "success",
        **kwargs
    ) -> JSONResponse:
        """格式化列表响应 - 兼容旧接口"""
        return self.paginated_success(
            data=data,
            total=total,
            page=page,
            page_size=page_size,
            message=message,
            **kwargs
        )
    
    def _get_execution_time(self) -> int:
        """获取执行时间(毫秒)"""
        return int((time.time() - self.start_time) * 1000)
    
    def _build_meta(
        self,
        total: Optional[int] = None,
        page: Optional[int] = None,
        page_size: Optional[int] = None
    ) -> ResponseMeta:
        """构建响应元数据"""
        has_next = None
        has_prev = None
        
        if total is not None and page is not None and page_size is not None:
            has_next = (page * page_size) < total
            has_prev = page > 1
        
        return ResponseMeta(
            version="v2",
            total=total,
            page=page,
            page_size=page_size,
            has_next=has_next,
            has_prev=has_prev,
            timestamp=datetime.now().isoformat(),
            request_id=self.request_id,
            execution_time=self._get_execution_time()
        )
    
    def _build_pagination_links(
        self,
        base_url: str,
        page: int,
        page_size: int,
        total: int,
        query_params: Optional[Dict[str, Any]] = None
    ) -> HATEOASLinks:
        """构建分页HATEOAS链接"""
        if not query_params:
            query_params = {}
        
        total_pages = (total + page_size - 1) // page_size
        
        def build_url(page_num: int) -> str:
            params = {**query_params, 'page': page_num, 'page_size': page_size}
            query_string = urlencode(params)
            return f"{base_url}?{query_string}"
        
        links = HATEOASLinks(
            self=build_url(page),
            first=build_url(1) if total_pages > 0 else None,
            last=build_url(total_pages) if total_pages > 0 else None
        )
        
        if page > 1:
            links.prev = build_url(page - 1)
        
        if page < total_pages:
            links.next = build_url(page + 1)
        
        return links
    
    def _build_resource_links(
        self,
        resource_id: Optional[str] = None,
        resource_type: Optional[str] = None,
        related_resources: Optional[Dict[str, str]] = None
    ) -> HATEOASLinks:
        """构建资源HATEOAS链接"""
        links = HATEOASLinks()
        
        if self.request and resource_type:
            base_path = f"/api/v2/{resource_type}"
            
            if resource_id:
                links.self = f"{base_path}/{resource_id}"
            else:
                links.self = base_path
        
        if related_resources:
            links.related = related_resources
        
        return links
    
    def success(
        self,
        data: Optional[Any] = None,
        message: str = "success",
        code: int = 200,
        resource_id: Optional[str] = None,
        resource_type: Optional[str] = None,
        related_resources: Optional[Dict[str, str]] = None,
        generated_sql: Optional[str] = None
    ) -> JSONResponse:
        """创建成功响应"""
        meta = self._build_meta()
        
        links = None
        if resource_type or related_resources:
            links = self._build_resource_links(
                resource_id=resource_id,
                resource_type=resource_type,
                related_resources=related_resources
            )
        
        response_data = APIv2Response(
            success=True,
            code=code,
            message=message,
            data=data,
            meta=meta,
            links=links,
            generated_sql=generated_sql
        )
        
        # 移除调试信息以避免Content-Length问题
        
        import json
        from datetime import datetime
        from decimal import Decimal
        
        def datetime_serializer(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            if isinstance(obj, Decimal):
                return float(obj)
            raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
        
        try:
            content = response_data.model_dump(exclude_none=True)
        except AttributeError as e:
            raise
        
        return JSONResponse(
            content=json.loads(json.dumps(content, default=datetime_serializer)),
            status_code=code
        )
    
    def paginated_success(
        self,
        data: List[Any],
        total: int,
        page: int = 1,
        page_size: int = 20,
        message: str = "success",
        code: int = 200,
        resource_type: Optional[str] = None,
        query_params: Optional[Dict[str, Any]] = None,
        generated_sql: Optional[str] = None
    ) -> JSONResponse:
        """创建分页成功响应"""
        meta = self._build_meta(total=total, page=page, page_size=page_size)
        
        links = None
        if self.request and resource_type:
            base_url = f"/api/v2/{resource_type}"
            links = self._build_pagination_links(
                base_url=base_url,
                page=page,
                page_size=page_size,
                total=total,
                query_params=query_params
            )
        
        response_data = APIv2Response(
            success=True,
            code=code,
            message=message,
            data=data,
            meta=meta,
            links=links,
            generated_sql=generated_sql
        )
        
        return JSONResponse(
            content=response_data.model_dump(mode='json', exclude_none=True),
            status_code=code
        )
    
    def error(
        self,
        message: str,
        code: int = 400,
        error_type: str = "ValidationError",
        details: Optional[List[APIv2ErrorDetail]] = None,
        help_links: Optional[Dict[str, str]] = None,
        suggestion: Optional[str] = None,
        trace_id: Optional[str] = None
    ) -> JSONResponse:
        """创建错误响应"""
        meta = self._build_meta()
        
        # 默认帮助链接
        default_links = {
            "help": "/api/v2/docs",
            "support": "/api/v2/support"
        }
        
        if help_links:
            default_links.update(help_links)
        
        # 构建错误对象
        error_obj = {
            "code": code,
            "message": message,
            "type": error_type
        }
        
        processed_details = []
        if details:
            for detail in details:
                if hasattr(detail, 'model_dump'):
                    # 如果是Pydantic模型，调用model_dump
                    processed_details.append(detail.model_dump())
                elif isinstance(detail, dict):
                    # 如果是字典，直接添加
                    processed_details.append(detail)
                else:
                    # 其他情况，转换为标准格式
                    processed_details.append({
                        "field": "unknown",
                        "code": "UNKNOWN_ERROR",
                        "message": str(detail),
                        "value": detail
                    })
        error_obj["details"] = processed_details
        
        if suggestion:
            error_obj["suggestion"] = suggestion
            
        if trace_id:
            error_obj["traceId"] = trace_id
        
        # 调试信息：检查各个参数的类型
        # 创建响应数据
        response_data = APIv2ErrorResponse(
            success=False,
            code=code,
            message=message,
            error_type=error_type,
            error=error_obj,
            meta=meta,
            links=default_links
        )
        
        # 根据错误代码确定HTTP状态码
        http_status = code
        if code >= 500:
            http_status = 500
        elif code == 401:
            http_status = 401
        elif code == 403:
            http_status = 403
        elif code == 404:
            http_status = 404
        elif code == 409:
            http_status = 409
        elif code == 422:
            http_status = 422
        else:
            http_status = 400
        
        try:
            content = response_data.model_dump(exclude_none=True)
        except AttributeError as e:
            # 调试信息：如果 response_data 不是 Pydantic 模型
            print(f"DEBUG: response_data type: {type(response_data)}")
            print(f"DEBUG: response_data value: {response_data}")
            raise e
        
        return JSONResponse(
            content=content,
            status_code=http_status
        )
    
    def validation_error(
        self,
        message: str = "Validation failed",
        details: List[APIv2ErrorDetail] = None,
        code: int = 422,
        suggestion: Optional[str] = None
    ) -> JSONResponse:
        """创建验证错误响应"""
        return self.error(
            message=message,
            code=code,
            error_type="VALIDATION_ERROR",
            details=details or [],
            suggestion=suggestion or "请检查输入数据格式是否正确",
            help_links={
                "help": "https://api-docs.example.com/errors/validation",
                "support": "mailto:support@example.com"
            }
        )
    
    def unauthorized(
        self,
        message: str = "Unauthorized access",
        suggestion: Optional[str] = None
    ) -> JSONResponse:
        """创建401错误响应"""
        return self.error(
            message=message,
            code=401,
            error_type="AUTHENTICATION_ERROR",
            suggestion=suggestion or "请提供有效的认证凭据",
            help_links={
                "login": "/api/v2/auth/login",
                "help": "/api/v2/docs/authentication"
            }
        )
    
    def internal_error(
        self,
        message: str = "Internal server error",
        error_id: Optional[str] = None,
        component: Optional[str] = None,
        error_detail: Optional[str] = None
    ) -> JSONResponse:
        """创建500错误响应"""
        if not error_id:
            error_id = self.request_id
        
        details = []
        if component and error_detail:
            details.append(APIv2ErrorDetail(
                field="component",
                code="COMPONENT_ERROR",
                message=error_detail,
                value=component
            ))
        
        return self.error(
            message=message,
            code=500,
            error_type="INTERNAL_SERVER_ERROR",
            details=details if details else None,
            trace_id=error_id,
            help_links={
                "support": "mailto:support@example.com",
                "status": "https://status.example.com"
            }
        )
    
    def created(
        self,
        data: Optional[Any] = None,
        message: str = "Resource created successfully",
        resource_id: Optional[Union[str, List[str]]] = None,
        resource_type: Optional[str] = None,
        related_resources: Optional[Dict[str, str]] = None
    ) -> JSONResponse:
        """创建201创建成功响应"""
        return self.success(
            data=data,
            message=message,
            code=201,
            resource_id=str(resource_id) if resource_id else None,
            resource_type=resource_type,
            related_resources=related_resources
        )
    
    def bad_request(
        self,
        message: str = "Bad request",
        details: Optional[List[APIv2ErrorDetail]] = None,
        suggestion: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None
    ) -> JSONResponse:
        """创建400错误响应"""
        return self.error(
            message=message,
            code=400,
            error_type="BAD_REQUEST",
            details=details,
            suggestion=suggestion
        )
    
    def not_found(
        self,
        message: str = "Resource not found",
        details: Optional[List[APIv2ErrorDetail]] = None,
        suggestion: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None
    ) -> JSONResponse:
        """创建404错误响应"""
        if resource_type:
            message = f"{resource_type.title()} not found"
        
        return self.error(
            message=message,
            code=404,
            error_type="NOT_FOUND",
            details=details,
            suggestion=suggestion
        )
    
    def forbidden(
        self,
        message: str = "Access forbidden",
        details: Optional[List[APIv2ErrorDetail]] = None,
        suggestion: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None
    ) -> JSONResponse:
        """创建403错误响应"""
        return self.error(
            message=message,
            code=403,
            error_type="FORBIDDEN",
            details=details,
            suggestion=suggestion,
            help_links={
                "permissions": "/api/v2/docs/permissions"
            }
        )
    
    def conflict(
        self,
        message: str = "Resource conflict",
        details: Optional[List[APIv2ErrorDetail]] = None,
        suggestion: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None
    ) -> JSONResponse:
        """创建409冲突错误响应"""
        return self.error(
            message=message,
            code=409,
            error_type="CONFLICT",
            details=details,
            suggestion=suggestion,
            help_links={
                "help": "/api/v2/docs/errors/conflict"
            }
        )
    
    def partial_success(
        self,
        data: Optional[Any] = None,
        message: str = "Partial success",
        code: int = 207,
        success_count: int = 0,
        failure_count: int = 0,
        errors: Optional[List[Dict[str, Any]]] = None,
        resource_type: Optional[str] = None
    ) -> JSONResponse:
        """创建部分成功响应（用于批量操作）"""
        meta = self._build_meta()
        
        # 构建响应数据
        response_data = {
            "success": True,  # 部分成功仍然标记为成功
            "code": code,
            "message": message,
            "data": data,
            "meta": meta.model_dump(),
            "stats": {
                "success_count": success_count,
                "failure_count": failure_count,
                "total_count": success_count + failure_count
            }
        }
        
        # 添加错误详情
        if errors:
            response_data["errors"] = errors
        
        # 添加链接
        if resource_type:
            response_data["links"] = {
                "self": f"/api/v2/{resource_type}/batch",
                "help": "/api/v2/docs/batch-operations"
            }
        
        return JSONResponse(
            content=response_data,
            status_code=code
        )


# 便捷函数
def create_formatter(request: Optional[Request] = None) -> ResponseFormatterV2:
    """创建响应格式化器实例"""
    return ResponseFormatterV2(request)


def success_v2(
    data: Optional[Any] = None,
    message: str = "success",
    code: int = 200,
    request: Optional[Request] = None,
    **kwargs
) -> JSONResponse:
    """快速创建v2成功响应"""
    formatter = ResponseFormatterV2(request)
    return formatter.success(data=data, message=message, code=code, **kwargs)


def error_v2(
    message: str,
    code: int = 400,
    error_type: str = "ValidationError",
    request: Optional[Request] = None,
    **kwargs
) -> JSONResponse:
    """快速创建v2错误响应"""
    formatter = ResponseFormatterV2(request)
    return formatter.error(message=message, code=code, error_type=error_type, **kwargs)


def paginated_v2(
    data: List[Any],
    total: int,
    page: int = 1,
    page_size: int = 20,
    message: str = "success",
    request: Optional[Request] = None,
    **kwargs
) -> JSONResponse:
    """快速创建v2分页响应"""
    formatter = ResponseFormatterV2(request)
    return create_formatter(request).paginated_success(
        data=data,
        total=total,
        page=page,
        page_size=page_size,
        message=message,
        **kwargs
    )


# 创建全局实例
response_formatter_v2 = ResponseFormatterV2()