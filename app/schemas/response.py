from typing import Any, Optional, Generic, TypeVar, List
from pydantic import BaseModel, Field

T = TypeVar('T')


class ResponseModel(BaseModel, Generic[T]):
    """通用响应模型"""
    code: int = Field(200, description="响应状态码")
    message: str = Field("操作成功", description="响应消息")
    data: Optional[T] = Field(None, description="响应数据")
    timestamp: Optional[str] = Field(None, description="响应时间戳")


class ListResponseModel(BaseModel, Generic[T]):
    """列表响应模型"""
    code: int = Field(200, description="响应状态码")
    message: str = Field("操作成功", description="响应消息")
    data: Optional['ListData[T]'] = Field(None, description="响应数据")
    timestamp: Optional[str] = Field(None, description="响应时间戳")


class ListData(BaseModel, Generic[T]):
    """列表数据模型"""
    items: List[T] = Field(default_factory=list, description="数据列表")
    total: int = Field(0, description="总记录数")
    page: int = Field(1, description="当前页码")
    page_size: int = Field(20, description="每页数量")
    total_pages: int = Field(0, description="总页数")


# 更新前向引用
ListResponseModel.model_rebuild()