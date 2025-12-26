#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
设备字段 Schema
用于设备字段配置的数据验证和序列化
"""

from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class DeviceFieldBase(BaseModel):
    """设备字段基础模型"""
    field_name: str = Field(..., description="字段显示名称")
    field_code: str = Field(..., description="字段代码")
    field_type: str = Field(..., description="字段类型: float/int/string/boolean")
    unit: Optional[str] = Field(None, description="单位")
    sort_order: int = Field(0, description="显示顺序")
    display_config: Optional[Dict[str, Any]] = Field(None, description="显示配置")


class DeviceFieldMonitoringResponse(DeviceFieldBase):
    """监测关键字段响应模型"""
    id: int = Field(..., description="字段ID")
    device_type_code: str = Field(..., description="设备类型代码")
    field_category: Optional[str] = Field(None, description="字段分类")
    description: Optional[str] = Field(None, description="字段描述")
    is_monitoring_key: bool = Field(True, description="是否为监测关键字段")
    is_active: bool = Field(True, description="是否启用")
    # 字段分组相关
    field_group: Optional[str] = Field('default', description="字段分组: core/temperature/power/other")
    is_default_visible: Optional[bool] = Field(True, description="是否默认显示")
    group_order: Optional[int] = Field(0, description="分组排序顺序")
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "device_type_code": "WELD_MACHINE",
                "field_name": "预设电流",
                "field_code": "preset_current",
                "field_type": "float",
                "unit": "A",
                "sort_order": 1,
                "display_config": {
                    "icon": "⚡",
                    "color": "#1890ff"
                },
                "field_category": "data_collection",
                "description": "焊机预设电流值",
                "is_monitoring_key": True,
                "is_active": True
            }
        }


class DeviceRealtimeDataResponse(BaseModel):
    """设备实时数据响应模型"""
    device_code: str = Field(..., description="设备编码")
    device_name: str = Field(..., description="设备名称")
    device_type: str = Field(..., description="设备类型代码")
    monitoring_fields: list[DeviceFieldMonitoringResponse] = Field(..., description="监测字段配置")
    realtime_data: Dict[str, Any] = Field(..., description="实时数据")
    
    class Config:
        json_schema_extra = {
            "example": {
                "device_code": "WM001",
                "device_name": "1号焊机",
                "device_type": "WELD_MACHINE",
                "monitoring_fields": [
                    {
                        "id": 1,
                        "device_type_code": "WELD_MACHINE",
                        "field_name": "预设电流",
                        "field_code": "preset_current",
                        "field_type": "float",
                        "unit": "A",
                        "sort_order": 1,
                        "display_config": {"icon": "⚡", "color": "#1890ff"}
                    }
                ],
                "realtime_data": {
                    "preset_current": 150.5,
                    "preset_voltage": 28.3
                }
            }
        }


class BatchRealtimeDataRequest(BaseModel):
    """批量查询实时数据请求模型"""
    device_codes: list[str] = Field(..., description="设备编码列表", max_length=100)
    
    class Config:
        json_schema_extra = {
            "example": {
                "device_codes": ["WM001", "WM002", "WM003"]
            }
        }


class PaginatedRealtimeDataRequest(BaseModel):
    """分页查询实时数据请求模型"""
    page: int = Field(1, ge=1, description="页码")
    page_size: int = Field(50, ge=1, le=100, description="每页数量")
    device_type: Optional[str] = Field(None, description="设备类型筛选")
    status: Optional[str] = Field(None, description="设备状态筛选")
    
    class Config:
        json_schema_extra = {
            "example": {
                "page": 1,
                "page_size": 50,
                "device_type": "WELD_MACHINE",
                "status": "online"
            }
        }


class PaginatedRealtimeDataResponse(BaseModel):
    """分页查询实时数据响应模型"""
    items: list[DeviceRealtimeDataResponse] = Field(..., description="设备数据列表")
    total: int = Field(..., description="总数")
    page: int = Field(..., description="当前页码")
    page_size: int = Field(..., description="每页数量")
    total_pages: int = Field(..., description="总页数")
    
    class Config:
        json_schema_extra = {
            "example": {
                "items": [],
                "total": 100,
                "page": 1,
                "page_size": 50,
                "total_pages": 2
            }
        }
