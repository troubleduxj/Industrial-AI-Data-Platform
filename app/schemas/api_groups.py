from typing import Optional, List
from pydantic import BaseModel, Field
from app.schemas.base import BatchDeleteRequest


class ApiGroupCreate(BaseModel):
    """创建API分组的数据模型"""
    group_name: str = Field(..., description="分组名称", min_length=1, max_length=100)
    group_code: str = Field(..., description="分组代码", min_length=1, max_length=50)
    description: Optional[str] = Field(None, description="分组描述", max_length=500)


class ApiGroupUpdate(BaseModel):
    """更新API分组的数据模型"""
    group_name: Optional[str] = Field(None, description="分组名称", min_length=1, max_length=100)
    group_code: Optional[str] = Field(None, description="分组代码", min_length=1, max_length=50)
    description: Optional[str] = Field(None, description="分组描述", max_length=500)


class ApiGroupPatch(BaseModel):
    """部分更新API分组的数据模型"""
    group_name: Optional[str] = Field(None, description="分组名称", min_length=1, max_length=100)
    group_code: Optional[str] = Field(None, description="分组代码", min_length=1, max_length=50)
    description: Optional[str] = Field(None, description="分组描述", max_length=500)


class ApiGroupResponse(BaseModel):
    """API分组响应数据模型"""
    id: int = Field(..., description="分组ID")
    group_name: str = Field(..., description="分组名称")
    group_code: str = Field(..., description="分组代码")
    description: Optional[str] = Field(None, description="分组描述")
    api_count: int = Field(0, description="该分组下的API数量")
    created_at: Optional[str] = Field(None, description="创建时间")
    updated_at: Optional[str] = Field(None, description="更新时间")


class ApiGroupBatchDelete(BatchDeleteRequest):
    """批量删除API分组请求模型 - 继承标准化批量删除格式"""
    pass