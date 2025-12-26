#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
设备字段配置管理 API v2
实现设备字段配置的查询和管理，支持数据字典集成和缓存机制
"""

import json
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta

from fastapi import APIRouter, Query, Request, Depends
from tortoise.transactions import in_transaction

from app.core.dependency import DependAuth
from app.core.response_formatter_v2 import create_formatter
from app.schemas.devices import (
    DeviceFieldConfigResponse,
    DeviceFieldConfigQuery,
    DeviceFieldConfigCreate,
    DeviceFieldConfigUpdate
)
from app.models.device import DeviceField, DeviceType
from app.models.system import SysDictType, SysDictData
from app.models.admin import User
from app.core.device_maintenance_permissions import (
    require_device_field_config_read_permission
)
from app.services.device_maintenance_permission_service import (
    device_maintenance_permission_service,
    DeviceMaintenanceAuditAction
)

logger = logging.getLogger(__name__)

router = APIRouter()

# 简单的内存缓存机制
_field_config_cache = {}
_cache_expiry = {}
CACHE_DURATION = timedelta(minutes=30)  # 缓存30分钟


def _is_cache_valid(cache_key: str) -> bool:
    """检查缓存是否有效"""
    if cache_key not in _cache_expiry:
        return False
    return datetime.now() < _cache_expiry[cache_key]


def _set_cache(cache_key: str, data: Any) -> None:
    """设置缓存"""
    _field_config_cache[cache_key] = data
    _cache_expiry[cache_key] = datetime.now() + CACHE_DURATION


def _get_cache(cache_key: str) -> Any:
    """获取缓存"""
    if _is_cache_valid(cache_key):
        return _field_config_cache.get(cache_key)
    return None


def _clear_cache(device_type_code: str = None) -> None:
    """清除缓存"""
    if device_type_code:
        # 清除特定设备类型的缓存
        keys_to_remove = [key for key in _field_config_cache.keys() if device_type_code in key]
        for key in keys_to_remove:
            _field_config_cache.pop(key, None)
            _cache_expiry.pop(key, None)
    else:
        # 清除所有缓存
        _field_config_cache.clear()
        _cache_expiry.clear()


async def _get_dict_options(dict_type_code: str) -> List[Dict[str, str]]:
    """获取数据字典选项"""
    try:
        dict_type = await SysDictType.get_or_none(type_code=dict_type_code)
        if not dict_type:
            return []
        
        dict_data = await SysDictData.filter(
            dict_type=dict_type,
            is_enabled=True
        ).order_by('sort_order')
        
        return [
            {"label": item.data_label, "value": item.data_value}
            for item in dict_data
        ]
    except Exception as e:
        logger.error(f"获取数据字典选项失败: {str(e)}")
        return []


# =====================================================
# 设备字段配置管理 API v2
# =====================================================

@router.get("/device-fields/{device_type_code}", summary="获取设备类型字段配置", response_model=None)
async def get_device_field_config(
    request: Request,
    device_type_code: str,
    field_category: Optional[str] = Query(None, description="字段分类筛选: data_collection/maintenance_record"),
    include_options: bool = Query(True, description="是否包含选项值"),
    use_cache: bool = Query(True, description="是否使用缓存"),
    current_user: User = Depends(require_device_field_config_read_permission)
):
    """
    获取指定设备类型的字段配置，包含数据字典选项
    
    - **device_type_code**: 设备类型代码
    - **field_category**: 字段分类筛选（可选）
    - **include_options**: 是否包含选项值
    - **use_cache**: 是否使用缓存
    """
    try:
        formatter = create_formatter(request)
        
        # 构建缓存键
        cache_key = f"device_fields_{device_type_code}_{field_category or 'all'}_{include_options}"
        
        # 尝试从缓存获取
        if use_cache:
            cached_data = _get_cache(cache_key)
            if cached_data is not None:
                return formatter.success(
                    data=cached_data,
                    message="获取设备字段配置成功（缓存）"
                )
        
        # 验证设备类型是否存在
        device_type = await DeviceType.get_or_none(type_code=device_type_code)
        if not device_type:
            return formatter.not_found("设备类型不存在")
        
        # 构建查询条件
        query = DeviceField.filter(
            device_type_code=device_type_code,
            is_active=True
        )
        
        if field_category:
            query = query.filter(field_category=field_category)
        
        # 获取字段配置
        fields = await query.order_by('sort_order', 'field_name').all()
        
        logger.info(f"查询到 {len(fields)} 个字段")
        
        field_configs = []
        for field in fields:
            field_config = {
                "id": field.id,
                "field_code": field.field_code,
                "field_name": field.field_name,
                "field_type": field.field_type,
                "field_category": field.field_category,
                "field_group": field.field_group,  # ✅ 添加字段分组
                "is_default_visible": field.is_default_visible,  # ✅ 添加默认显示
                "group_order": field.group_order,  # ✅ 添加分组排序
                "is_required": field.is_required,
                "sort_order": field.sort_order,
                "default_value": field.default_value,
                "validation_rule": json.loads(field.validation_rule) if field.validation_rule else None,
                "unit": field.unit,
                "description": field.description,
                "is_monitoring_key": field.is_monitoring_key,
                "is_alarm_enabled": field.is_alarm_enabled,
                "is_ai_feature": field.is_ai_feature,
                "is_active": field.is_active,
                "aggregation_method": field.aggregation_method,
                "data_range": field.data_range,
                "alarm_threshold": field.alarm_threshold,
                "display_config": field.display_config,
                "options": None
            }
            
            # 如果需要包含选项值且是字典选择类型，获取字典数据
            if include_options and field.field_type in ['dict_select', 'select'] and field.validation_rule:
                try:
                    validation_rule = json.loads(field.validation_rule)
                    dict_type_code = validation_rule.get('dict_type')
                    
                    if dict_type_code:
                        options = await _get_dict_options(dict_type_code)
                        field_config['options'] = options
                except Exception as e:
                    logger.warning(f"获取字段 {field.field_code} 的选项值失败: {str(e)}")
            
            field_configs.append(field_config)
        
        # 设置缓存
        if use_cache:
            _set_cache(cache_key, field_configs)
        
        # 记录审计日志
        await device_maintenance_permission_service.create_audit_log(
            user=current_user,
            action=DeviceMaintenanceAuditAction.VIEW_DEVICE_FIELDS,
            request=request,
            request_data={
                "device_type_code": device_type_code,
                "field_category": field_category,
                "include_options": include_options,
                "use_cache": use_cache
            },
            response_data={"field_count": len(field_configs)},
            status_code=200
        )
        
        return formatter.success(
            data=field_configs,
            message="获取设备字段配置成功"
        )
        
    except Exception as e:
        logger.error(f"获取设备字段配置失败: {str(e)}")
        
        # 记录错误审计日志
        await device_maintenance_permission_service.create_audit_log(
            user=current_user,
            action=DeviceMaintenanceAuditAction.VIEW_DEVICE_FIELDS,
            request=request,
            request_data={
                "device_type_code": device_type_code,
                "field_category": field_category
            },
            status_code=500,
            error_message=str(e)
        )
        
        return formatter.internal_error("获取设备字段配置失败")


@router.get("/device-fields", summary="获取所有设备类型字段配置", response_model=None)
async def get_all_device_field_configs(
    request: Request,
    field_category: Optional[str] = Query(None, description="字段分类筛选"),
    include_options: bool = Query(False, description="是否包含选项值"),
    use_cache: bool = Query(True, description="是否使用缓存"),
    current_user: User = Depends(require_device_field_config_read_permission)
):
    """
    获取所有设备类型的字段配置
    
    - **field_category**: 字段分类筛选（可选）
    - **include_options**: 是否包含选项值
    - **use_cache**: 是否使用缓存
    """
    try:
        formatter = create_formatter(request)
        
        # 构建缓存键
        cache_key = f"all_device_fields_{field_category or 'all'}_{include_options}"
        
        # 尝试从缓存获取
        if use_cache:
            cached_data = _get_cache(cache_key)
            if cached_data is not None:
                return formatter.success(
                    data=cached_data,
                    message="获取所有设备字段配置成功（缓存）"
                )
        
        # 获取所有激活的设备类型
        device_types = await DeviceType.filter(is_active=True).order_by('type_name').all()
        
        result = {}
        for device_type in device_types:
            # 构建查询条件
            query = DeviceField.filter(
                device_type_code=device_type.type_code,
                is_active=True
            )
            
            if field_category:
                query = query.filter(field_category=field_category)
            
            # 获取字段配置
            fields = await query.order_by('sort_order', 'field_name').all()
            
            field_configs = []
            for field in fields:
                field_config = {
                    "id": field.id,
                    "field_code": field.field_code,
                    "field_name": field.field_name,
                    "field_type": field.field_type,
                    "field_category": field.field_category,
                    "is_required": field.is_required,
                    "sort_order": field.sort_order,
                    "default_value": field.default_value,
                    "validation_rule": json.loads(field.validation_rule) if field.validation_rule else None,
                    "unit": field.unit,
                    "description": field.description,
                    "is_monitoring_key": field.is_monitoring_key,
                    "is_alarm_enabled": field.is_alarm_enabled,
                    "is_ai_feature": field.is_ai_feature,
                    "is_active": field.is_active,
                    "aggregation_method": field.aggregation_method,
                    "data_range": field.data_range,
                    "alarm_threshold": field.alarm_threshold,
                    "display_config": field.display_config,
                    "options": None
                }
                
                # 如果需要包含选项值且是字典选择类型，获取字典数据
                if include_options and field.field_type in ['dict_select', 'select'] and field.validation_rule:
                    try:
                        validation_rule = json.loads(field.validation_rule)
                        dict_type_code = validation_rule.get('dict_type')
                        
                        if dict_type_code:
                            options = await _get_dict_options(dict_type_code)
                            field_config['options'] = options
                    except Exception as e:
                        logger.warning(f"获取字段 {field.field_code} 的选项值失败: {str(e)}")
                
                field_configs.append(field_config)
            
            result[device_type.type_code] = {
                "device_type_name": device_type.type_name,
                "device_type_code": device_type.type_code,
                "fields": field_configs
            }
        
        # 设置缓存
        if use_cache:
            _set_cache(cache_key, result)
        
        return formatter.success(
            data=result,
            message="获取所有设备字段配置成功"
        )
        
    except Exception as e:
        logger.error(f"获取所有设备字段配置失败: {str(e)}")
        return formatter.internal_error("获取所有设备字段配置失败")


@router.post("/device-fields", summary="创建设备字段配置", response_model=None)
async def create_device_field_config(
    request: Request,
    field_data: DeviceFieldConfigCreate,
    current_user: User = Depends(require_device_field_config_read_permission)
):
    """
    创建设备字段配置
    
    - **field_data**: 字段配置数据
    """
    try:
        formatter = create_formatter(request)
        
        # 验证设备类型是否存在
        device_type = await DeviceType.get_or_none(type_code=field_data.device_type_code)
        if not device_type:
            return formatter.bad_request("设备类型不存在")
        
        # 检查字段代码是否已存在
        existing_field = await DeviceField.get_or_none(
            device_type_code=field_data.device_type_code,
            field_code=field_data.field_code
        )
        if existing_field:
            return formatter.bad_request("字段代码已存在")
        
        # 创建字段配置
        async with in_transaction("default"):
            field_config = await DeviceField.create(
                device_type_code=field_data.device_type_code,
                field_name=field_data.field_name,
                field_code=field_data.field_code,
                field_type=field_data.field_type,
                field_category=field_data.field_category,
                field_group=field_data.field_group,  # ✅ 添加字段分组
                is_default_visible=field_data.is_default_visible,  # ✅ 添加默认显示
                group_order=field_data.group_order,  # ✅ 添加分组排序
                is_required=field_data.is_required,
                sort_order=field_data.sort_order,
                default_value=field_data.default_value,
                validation_rule=json.dumps(field_data.validation_rule) if field_data.validation_rule else None,
                unit=field_data.unit,
                description=field_data.description,
                is_monitoring_key=field_data.is_monitoring_key,
                is_alarm_enabled=field_data.is_alarm_enabled,
                is_ai_feature=field_data.is_ai_feature,
                aggregation_method=field_data.aggregation_method,
                data_range=field_data.data_range,  # JSONField自动处理
                alarm_threshold=field_data.alarm_threshold,  # JSONField自动处理
                display_config=field_data.display_config,  # JSONField自动处理
                is_active=True
            )
        
        # 清除相关缓存
        _clear_cache(field_data.device_type_code)
        
        # 构建响应数据
        response_data = {
            "id": field_config.id,
            "field_code": field_config.field_code,
            "field_name": field_config.field_name,
            "field_type": field_config.field_type,
            "field_category": field_config.field_category,
            "field_group": field_config.field_group,  # ✅ 添加字段分组
            "is_default_visible": field_config.is_default_visible,  # ✅ 添加默认显示
            "group_order": field_config.group_order,  # ✅ 添加分组排序
            "is_required": field_config.is_required,
            "sort_order": field_config.sort_order,
            "default_value": field_config.default_value,
            "validation_rule": json.loads(field_config.validation_rule) if field_config.validation_rule else None,
            "unit": field_config.unit,
            "description": field_config.description,
            "is_alarm_enabled": field_config.is_alarm_enabled,
            "is_active": field_config.is_active,
            "created_at": field_config.created_at,
            "updated_at": field_config.updated_at
        }
        
        return formatter.success(
            data=response_data,
            message="创建设备字段配置成功"
        )
        
    except Exception as e:
        logger.error(f"创建设备字段配置失败: {str(e)}")
        return formatter.internal_error("创建设备字段配置失败")


@router.put("/device-fields/{field_id}", summary="更新设备字段配置", response_model=None)
async def update_device_field_config(
    request: Request,
    field_id: int,
    field_data: DeviceFieldConfigUpdate,
    current_user: User = Depends(require_device_field_config_read_permission)
):
    """
    更新设备字段配置
    
    - **field_id**: 字段配置ID
    - **field_data**: 更新的字段配置数据
    """
    try:
        formatter = create_formatter(request)
        
        # 查询字段配置
        field_config = await DeviceField.get_or_none(id=field_id)
        if not field_config:
            return formatter.not_found("字段配置不存在")
        
        # 更新字段配置
        update_data = field_data.model_dump(exclude_unset=True)
        if update_data:
            # 只处理validation_rule字段（字符串类型），其他JSON字段由Tortoise ORM自动处理
            if 'validation_rule' in update_data and update_data['validation_rule'] is not None:
                update_data['validation_rule'] = json.dumps(update_data['validation_rule'])
            
            async with in_transaction("default"):
                await DeviceField.filter(id=field_id).update(**update_data)
        
        # 清除相关缓存
        _clear_cache(field_config.device_type_code)
        
        # 获取更新后的字段配置
        updated_field = await DeviceField.get(id=field_id)
        
        # 构建响应数据
        response_data = {
            "id": updated_field.id,
            "field_code": updated_field.field_code,
            "field_name": updated_field.field_name,
            "field_type": updated_field.field_type,
            "field_category": updated_field.field_category,
            "field_group": updated_field.field_group,  # ✅ 添加字段分组
            "is_default_visible": updated_field.is_default_visible,  # ✅ 添加默认显示
            "group_order": updated_field.group_order,  # ✅ 添加分组排序
            "is_required": updated_field.is_required,
            "sort_order": updated_field.sort_order,
            "default_value": updated_field.default_value,
            "validation_rule": json.loads(updated_field.validation_rule) if updated_field.validation_rule else None,
            "unit": updated_field.unit,
            "description": updated_field.description,
            "is_alarm_enabled": updated_field.is_alarm_enabled,
            "is_active": updated_field.is_active,
            "created_at": updated_field.created_at,
            "updated_at": updated_field.updated_at
        }
        
        return formatter.success(
            data=response_data,
            message="更新设备字段配置成功"
        )
        
    except Exception as e:
        logger.error(f"更新设备字段配置失败: {str(e)}", exc_info=True)
        logger.error(f"字段ID: {field_id}")
        logger.error(f"更新数据: {field_data.model_dump(exclude_unset=True)}")
        return formatter.internal_error(f"更新设备字段配置失败: {str(e)}")


@router.delete("/device-fields/{field_id}", summary="删除设备字段配置", response_model=None)
async def delete_device_field_config(
    request: Request,
    field_id: int,
    current_user: User = Depends(require_device_field_config_read_permission)
):
    """
    删除设备字段配置
    
    - **field_id**: 字段配置ID
    """
    try:
        formatter = create_formatter(request)
        
        # 查询字段配置
        field_config = await DeviceField.get_or_none(id=field_id)
        if not field_config:
            return formatter.not_found("字段配置不存在")
        
        device_type_code = field_config.device_type_code
        
        # 删除字段配置（软删除，设置is_active=False）
        async with in_transaction("default"):
            await DeviceField.filter(id=field_id).update(is_active=False)
        
        # 清除相关缓存
        _clear_cache(device_type_code)
        
        return formatter.success(
            data={"deleted_id": field_id},
            message="删除设备字段配置成功"
        )
        
    except Exception as e:
        logger.error(f"删除设备字段配置失败: {str(e)}")
        return formatter.internal_error("删除设备字段配置失败")


@router.post("/device-fields/cache/clear", summary="清除字段配置缓存", response_model=None)
async def clear_field_config_cache(
    request: Request,
    device_type_code: Optional[str] = Query(None, description="设备类型代码（可选，不指定则清除所有缓存）"),
    current_user: User = Depends(require_device_field_config_read_permission)
):
    """
    清除字段配置缓存
    
    - **device_type_code**: 设备类型代码（可选）
    """
    try:
        formatter = create_formatter(request)
        
        # 清除缓存
        _clear_cache(device_type_code)
        
        message = f"清除设备类型 {device_type_code} 的字段配置缓存成功" if device_type_code else "清除所有字段配置缓存成功"
        
        return formatter.success(
            data={"cleared": True, "device_type_code": device_type_code},
            message=message
        )
        
    except Exception as e:
        logger.error(f"清除字段配置缓存失败: {str(e)}")
        return formatter.internal_error("清除字段配置缓存失败")


@router.get("/device-fields/cache/status", summary="获取缓存状态", response_model=None)
async def get_cache_status(
    request: Request,
    current_user: User = Depends(require_device_field_config_read_permission)
):
    """
    获取字段配置缓存状态
    """
    try:
        formatter = create_formatter(request)
        
        cache_status = {
            "total_cached_items": len(_field_config_cache),
            "cache_keys": list(_field_config_cache.keys()),
            "cache_expiry_times": {
                key: expiry_time.isoformat() 
                for key, expiry_time in _cache_expiry.items()
            },
            "cache_duration_minutes": CACHE_DURATION.total_seconds() / 60
        }
        
        return formatter.success(
            data=cache_status,
            message="获取缓存状态成功"
        )
        
    except Exception as e:
        logger.error(f"获取缓存状态失败: {str(e)}")
        return formatter.internal_error("获取缓存状态失败")