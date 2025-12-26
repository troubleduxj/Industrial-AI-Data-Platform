"""
Mock数据管理的Pydantic模型
"""

from datetime import datetime
from typing import Optional, Any, Dict
from pydantic import BaseModel, Field, field_validator


class MockDataBase(BaseModel):
    """Mock数据基础模型"""
    name: str = Field(..., max_length=100, description="Mock规则名称")
    description: Optional[str] = Field(None, max_length=500, description="规则描述")
    method: str = Field(..., description="HTTP方法 (GET/POST/PUT/DELETE)")
    url_pattern: str = Field(..., max_length=500, description="URL匹配模式，支持通配符")
    response_data: Dict[str, Any] = Field(..., description="响应数据")
    response_code: int = Field(200, ge=100, le=599, description="HTTP响应状态码")
    delay: int = Field(0, ge=0, le=10000, description="延迟时间(ms)")
    enabled: bool = Field(True, description="是否启用")
    priority: int = Field(0, description="优先级(数字越大越优先)")

    @field_validator('method')
    @classmethod
    def validate_method(cls, v: str) -> str:
        allowed_methods = ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD', 'OPTIONS']
        v_upper = v.upper()
        if v_upper not in allowed_methods:
            raise ValueError(f'Method must be one of {allowed_methods}')
        return v_upper


class MockDataCreate(MockDataBase):
    """创建Mock数据请求模型"""
    pass


class MockDataUpdate(BaseModel):
    """更新Mock数据请求模型"""
    name: Optional[str] = Field(None, max_length=100, description="Mock规则名称")
    description: Optional[str] = Field(None, max_length=500, description="规则描述")
    method: Optional[str] = Field(None, description="HTTP方法")
    url_pattern: Optional[str] = Field(None, max_length=500, description="URL匹配模式")
    response_data: Optional[Dict[str, Any]] = Field(None, description="响应数据")
    response_code: Optional[int] = Field(None, ge=100, le=599, description="HTTP响应状态码")
    delay: Optional[int] = Field(None, ge=0, le=10000, description="延迟时间(ms)")
    enabled: Optional[bool] = Field(None, description="是否启用")
    priority: Optional[int] = Field(None, description="优先级")

    @field_validator('method')
    @classmethod
    def validate_method(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        allowed_methods = ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD', 'OPTIONS']
        v_upper = v.upper()
        if v_upper not in allowed_methods:
            raise ValueError(f'Method must be one of {allowed_methods}')
        return v_upper


class MockDataInDB(MockDataBase):
    """数据库中的Mock数据模型"""
    id: int
    hit_count: int = 0
    last_hit_time: Optional[datetime] = None
    creator_id: Optional[int] = None
    creator_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class MockDataResponse(MockDataInDB):
    """Mock数据响应模型"""
    pass


class MockDataListResponse(BaseModel):
    """Mock数据列表响应"""
    items: list[MockDataResponse]
    total: int
    page: int
    page_size: int


class MockDataToggleRequest(BaseModel):
    """切换Mock启用状态请求"""
    enabled: bool = Field(..., description="启用状态")


class MockDataBatchDeleteRequest(BaseModel):
    """批量删除Mock数据请求"""
    ids: list[int] = Field(..., min_length=1, description="要删除的Mock ID列表")

