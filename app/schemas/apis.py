from pydantic import BaseModel, Field
from typing import Optional, List
from app.models.enums import MethodType


class ApiCreate(BaseModel):
    """创建API请求模型"""
    path: str = Field(..., description="API路径", example="/api/v2/users", max_length=255)
    method: MethodType = Field(..., description="HTTP方法", example="GET")
    summary: str = Field(..., description="API摘要", example="获取用户列表", max_length=200)
    description: Optional[str] = Field(None, description="API详细描述", max_length=500)
    tags: Optional[str] = Field(None, description="API标签", example="用户管理", max_length=100)
    group_id: Optional[int] = Field(1, description="API分组ID", ge=1)
    is_active: bool = Field(True, description="是否启用")


class ApiUpdate(BaseModel):
    """更新API请求模型"""
    path: Optional[str] = Field(None, description="API路径", max_length=255)
    method: Optional[MethodType] = Field(None, description="HTTP方法")
    summary: Optional[str] = Field(None, description="API摘要", max_length=200)
    description: Optional[str] = Field(None, description="API详细描述", max_length=500)
    tags: Optional[str] = Field(None, description="API标签", max_length=100)
    group_id: Optional[int] = Field(None, description="API分组ID", ge=1)
    is_active: Optional[bool] = Field(None, description="是否启用")


class ApiBatchCreate(BaseModel):
    """批量创建API请求模型"""
    apis: List[ApiCreate] = Field(..., description="API列表", min_items=1, max_items=50)


class ApiUpdateItem(BaseModel):
    """单个API更新项模型"""
    id: int = Field(..., description="API ID")
    path: Optional[str] = Field(None, description="API路径", max_length=255)
    method: Optional[MethodType] = Field(None, description="HTTP方法")
    summary: Optional[str] = Field(None, description="API摘要", max_length=200)
    description: Optional[str] = Field(None, description="API详细描述", max_length=500)
    tags: Optional[str] = Field(None, description="API标签", max_length=100)
    group_id: Optional[int] = Field(None, description="API分组ID", ge=1)
    is_active: Optional[bool] = Field(None, description="是否启用")


class ApiBatchUpdate(BaseModel):
    """批量更新API请求模型"""
    updates: List[ApiUpdateItem] = Field(..., description="更新数据列表", min_items=1, max_items=50)


class ApiBatchDelete(BaseModel):
    """批量删除API请求模型"""
    ids: List[int] = Field(..., description="API ID列表", min_items=1, max_items=100)


class ApiResponse(BaseModel):
    """API响应模型"""
    id: int = Field(..., description="API ID")
    path: str = Field(..., description="API路径")
    method: str = Field(..., description="HTTP方法")
    summary: str = Field(..., description="API摘要")
    description: Optional[str] = Field(None, description="API详细描述")
    tags: Optional[str] = Field(None, description="API标签")
    group_id: int = Field(..., description="API分组ID")
    is_active: bool = Field(..., description="是否启用")
    created_at: Optional[str] = Field(None, description="创建时间")
    updated_at: Optional[str] = Field(None, description="更新时间")
