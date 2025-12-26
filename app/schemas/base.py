import json
from datetime import datetime, date
from typing import Any, Optional, Generic, TypeVar, List
from functools import wraps

from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field


class CustomJsonEncoder(json.JSONEncoder):
    """
    自定义JSON编码器，处理datetime对象
    """

    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, date):
            return obj.isoformat()
        return json.JSONEncoder.default(self, obj)


class Success(JSONResponse):
    def __init__(
        self,
        code: int = 200,
        msg: Optional[str] = "OK",
        data: Optional[Any] = None,
        **kwargs,
    ):
        content = {"code": code, "msg": msg, "data": data}
        content.update(kwargs)
        # 直接传递字典，让FastAPI自动处理序列化
        super().__init__(content=content, status_code=200)


class Fail(JSONResponse):
    def __init__(
        self,
        code: int = 400,
        msg: Optional[str] = None,
        data: Optional[Any] = None,
        **kwargs,
    ):
        content = {"code": code, "msg": msg, "data": data}
        content.update(kwargs)
        # 直接传递字典，让FastAPI自动处理序列化
        super().__init__(content=content, status_code=400 if code >= 400 else 200)


class SuccessExtra(JSONResponse):
    def __init__(
        self,
        code: int = 200,
        msg: Optional[str] = None,
        data: Optional[Any] = None,
        total: int = 0,
        page: int = 1,
        page_size: int = 20,
        **kwargs,
    ):
        content = {
            "code": code,
            "msg": msg,
            "data": data,
            "total": total,
            "page": page,
            "page_size": page_size,
        }
        content.update(kwargs)
        # 直接传递字典，让FastAPI自动处理序列化
        super().__init__(content=content, status_code=200)


# 标准化API响应格式
T = TypeVar('T')

class APIResponse(BaseModel, Generic[T]):
    """标准化API响应格式"""
    success: bool = True
    code: int = 200
    message: str = "OK"
    data: Optional[T] = None
    timestamp: str = None
    
    def __init__(self, **data):
        if 'timestamp' not in data:
            data['timestamp'] = datetime.now().isoformat()
        super().__init__(**data)

class APIError(BaseModel):
    """统一的错误响应格式"""
    success: bool = False
    code: int
    message: str
    details: Optional[dict] = None
    timestamp: str = None
    
    def __init__(self, **data):
        if 'timestamp' not in data:
            data['timestamp'] = datetime.now().isoformat()
        super().__init__(**data)

class PaginatedResponse(BaseModel, Generic[T]):
    """分页响应格式"""
    success: bool = True
    code: int = 200
    message: str = "OK"
    data: Optional[list[T]] = None
    total: int = 0
    page: int = 1
    page_size: int = 20
    total_pages: int = 0
    timestamp: str = None
    
    def __init__(self, **data):
        if 'timestamp' not in data:
            data['timestamp'] = datetime.now().isoformat()
        if 'total_pages' not in data and data.get('total', 0) > 0 and data.get('page_size', 20) > 0:
            data['total_pages'] = (data['total'] + data['page_size'] - 1) // data['page_size']
        super().__init__(**data)

# 响应格式化装饰器
def standardize_response(func):
    """装饰器：将现有API返回值包装为标准化格式"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            result = await func(*args, **kwargs)
            
            # 如果已经是标准化响应，直接返回
            if isinstance(result, (APIResponse, APIError, PaginatedResponse, Success, Fail, SuccessExtra)):
                return result
            
            # 如果是JSONResponse，提取内容并标准化
            if isinstance(result, JSONResponse):
                # 保持现有JSONResponse的兼容性
                return result
            
            # 包装普通返回值为标准化格式
            return APIResponse(data=result)
            
        except Exception as e:
            # 统一错误处理
            return APIError(
                code=500,
                message=f"Internal server error: {str(e)}"
            )
    
    return wrapper

def success_response(data: Any = None, message: str = "OK", code: int = 200) -> JSONResponse:
    """创建成功响应"""
    response_data = APIResponse(success=True, code=code, message=message, data=data)
    return JSONResponse(
        content=response_data.model_dump(),
        status_code=code
    )

def error_response(message: str, code: int = 400, details: dict = None) -> JSONResponse:
    """创建错误响应"""
    response_data = APIError(success=False, code=code, message=message, details=details)
    return JSONResponse(
        content=response_data.model_dump(),
        status_code=code
    )

def paginated_response(
    data: list = None, 
    total: int = 0, 
    page: int = 1, 
    page_size: int = 20,
    message: str = "OK",
    code: int = 200
) -> JSONResponse:
    """创建分页响应"""
    response_data = PaginatedResponse(
        data=data or [],
        total=total,
        page=page,
        page_size=page_size,
        message=message,
        code=code
    )
    return JSONResponse(
        content=response_data.model_dump(),
        status_code=code
    )


# 标准化批量删除请求格式
class BatchDeleteRequest(BaseModel):
    """标准化批量删除请求格式 - 所有批量删除API都应使用此格式"""
    ids: List[int] = Field(..., min_items=1, max_items=100, description="要删除的ID列表")
    force: Optional[bool] = Field(False, description="是否强制删除（仅部分资源支持）")


class BatchDeleteFailedItem(BaseModel):
    """批量删除失败项目 - 包含用户友好的错误信息"""
    id: int = Field(..., description="失败项目的ID")
    name: Optional[str] = Field(None, description="失败项目的名称")
    reason: str = Field(..., description="用户友好的失败原因")


class BatchDeleteSuccessItem(BaseModel):
    """批量删除成功项目"""
    id: int = Field(..., description="成功删除项目的ID")
    name: Optional[str] = Field(None, description="成功删除项目的名称")


class BatchDeleteResponse(BaseModel):
    """标准化批量删除响应格式 - 包含用户友好的错误信息"""
    deleted_count: int = Field(..., description="成功删除的数量")
    failed_count: int = Field(0, description="删除失败的数量")
    deleted: List[BatchDeleteSuccessItem] = Field(default_factory=list, description="成功删除的项目列表")
    failed: List[BatchDeleteFailedItem] = Field(default_factory=list, description="删除失败的项目列表")
