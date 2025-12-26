from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field
from app.schemas.base import BatchDeleteRequest


# 字典类型相关 Schema
class SysDictTypeBase(BaseModel):
    type_code: str = Field(..., description="字典类型编码")
    type_name: str = Field(..., description="字典类型名称")
    description: Optional[str] = Field(None, description="描述")


class SysDictTypeCreate(SysDictTypeBase):
    """创建字典类型请求 Schema"""

    pass


class SysDictTypeUpdate(SysDictTypeBase):
    """更新字典类型请求 Schema"""

    type_code: Optional[str] = Field(None, description="字典类型编码")
    type_name: Optional[str] = Field(None, description="字典类型名称")


class SysDictTypePatch(BaseModel):
    """部分更新字典类型请求 Schema"""
    
    type_code: Optional[str] = Field(None, description="字典类型编码")
    type_name: Optional[str] = Field(None, description="字典类型名称")
    description: Optional[str] = Field(None, description="描述")


class SysDictTypeBatchCreate(BaseModel):
    """批量创建字典类型请求 Schema"""
    
    dict_types: List[SysDictTypeCreate] = Field(..., description="字典类型列表")


class SysDictTypeBatchUpdate(BaseModel):
    """批量更新字典类型请求 Schema"""
    
    updates: List[dict] = Field(..., description="更新数据列表，每项必须包含id字段")


class SysDictTypeBatchDelete(BatchDeleteRequest):
    """批量删除字典类型请求 Schema - 继承标准化批量删除格式"""
    pass


class BatchDeleteFailedItem(BaseModel):
    """批量删除失败项目"""
    
    id: int = Field(..., description="失败项目的ID")
    reason: str = Field(..., description="失败原因")


class BatchDeleteSkippedItem(BaseModel):
    """批量删除跳过项目"""
    
    id: int = Field(..., description="跳过项目的ID")
    reason: str = Field(..., description="跳过原因")


class BatchDeleteResult(BaseModel):
    """批量删除结果"""
    
    deleted_count: int = Field(..., description="成功删除的数量")
    failed_items: List[BatchDeleteFailedItem] = Field(default=[], description="删除失败的项目")
    skipped_items: List[BatchDeleteSkippedItem] = Field(default=[], description="跳过的项目")


class SysDictTypeBatchResponse(BaseModel):
    """批量操作响应 Schema"""
    
    success_count: int = Field(..., description="成功操作数量")
    error_count: int = Field(..., description="失败操作数量")
    success_data: List[dict] = Field(..., description="成功操作的数据")
    errors: List[dict] = Field(..., description="错误信息列表")


class SysDictTypeInDB(SysDictTypeBase):
    """从数据库读取字典类型 Schema"""

    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
        json_encoders = {datetime: lambda v: v.isoformat()}


# 字典数据相关 Schema
class SysDictDataBase(BaseModel):
    dict_type_id: int = Field(..., description="字典类型ID")
    data_label: str = Field(..., description="字典数据标签")
    data_value: str = Field(..., description="字典数据值")
    sort_order: Optional[int] = Field(0, description="排序")
    description: Optional[str] = Field(None, description="描述")
    is_enabled: Optional[bool] = Field(True, description="是否启用")


class SysDictDataCreate(SysDictDataBase):
    """创建字典数据请求 Schema"""

    pass


class SysDictDataUpdate(SysDictDataBase):
    """更新字典数据请求 Schema"""

    dict_type_id: Optional[int] = Field(None, description="字典类型ID")
    data_label: Optional[str] = Field(None, description="字典数据标签")
    data_value: Optional[str] = Field(None, description="字典数据值")
    sort_order: Optional[int] = Field(None, description="排序")
    is_enabled: Optional[bool] = Field(None, description="是否启用")


class SysDictDataPatch(BaseModel):
    """部分更新字典数据请求 Schema"""
    
    dict_type_id: Optional[int] = Field(None, description="字典类型ID")
    data_label: Optional[str] = Field(None, description="字典数据标签")
    data_value: Optional[str] = Field(None, description="字典数据值")
    sort_order: Optional[int] = Field(None, description="排序")
    description: Optional[str] = Field(None, description="描述")
    is_enabled: Optional[bool] = Field(None, description="是否启用")


class SysDictDataBatchCreate(BaseModel):
    """批量创建字典数据请求 Schema"""
    
    dict_data_list: List[SysDictDataCreate] = Field(..., description="字典数据列表")


class SysDictDataBatchUpdate(BaseModel):
    """批量更新字典数据请求 Schema"""
    
    updates: List[dict] = Field(..., description="更新数据列表，每项必须包含id字段")


class SysDictDataBatchDelete(BatchDeleteRequest):
    """批量删除字典数据请求 Schema - 继承标准化批量删除格式"""
    pass


class SysDictDataBatchToggleStatus(BaseModel):
    """批量切换字典数据状态请求 Schema"""
    
    ids: List[int] = Field(..., description="要切换状态的字典数据ID列表")
    is_enabled: bool = Field(..., description="目标状态")


class SysDictDataBatchResponse(BaseModel):
    """字典数据批量操作响应 Schema"""
    
    success_count: int = Field(..., description="成功操作数量")
    error_count: int = Field(..., description="失败操作数量")
    success_data: List[dict] = Field(..., description="成功操作的数据")
    errors: List[dict] = Field(..., description="错误信息列表")


class SysDictDataByTypeQuery(BaseModel):
    """按字典类型查询字典数据请求 Schema"""
    
    type_code: str = Field(..., description="字典类型编码")
    is_enabled: Optional[bool] = Field(None, description="是否启用过滤")
    sort_by: Optional[str] = Field("sort_order", description="排序字段")
    sort_order: Optional[str] = Field("asc", description="排序方向")


class SysDictDataInDB(SysDictDataBase):
    """从数据库读取字典数据 Schema"""

    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
        json_encoders = {datetime: lambda v: v.isoformat()}


class SysDictDataWithType(SysDictDataInDB):
    """包含关联字典类型的字典数据 Schema"""
    
    dict_type: Optional[SysDictTypeInDB] = Field(None, description="关联的字典类型")
    
    class Config:
        from_attributes = True
        json_encoders = {datetime: lambda v: v.isoformat()}


# 系统配置相关 Schema
class SysConfigBase(BaseModel):
    param_key: str = Field(..., description="参数键")
    param_value: Optional[str] = Field(None, description="参数值")
    param_name: str = Field(..., description="参数名称")
    param_type: str = Field("string", description="参数类型 (string, int, boolean等)")
    description: Optional[str] = Field(None, description="描述")
    is_editable: Optional[bool] = Field(True, description="是否允许前端编辑")
    is_system: Optional[bool] = Field(False, description="是否系统内置")
    is_active: Optional[bool] = Field(True, description="是否启用")


class SysConfigCreate(SysConfigBase):
    """创建系统配置请求 Schema"""

    pass


class SysConfigUpdate(SysConfigBase):
    """更新系统配置请求 Schema"""

    param_value: Optional[str] = Field(None, description="参数值")
    param_name: Optional[str] = Field(None, description="参数名称")
    description: Optional[str] = Field(None, description="描述")
    is_editable: Optional[bool] = Field(None, description="是否允许前端编辑")


class SysConfigBatchDelete(BatchDeleteRequest):
    """批量删除系统配置请求 Schema - 继承标准化批量删除格式"""
    pass


class SysConfigInDB(SysConfigBase):
    """从数据库读取系统配置 Schema"""

    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
        json_encoders = {datetime: lambda v: v.isoformat()}
