#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
设备字段动态参数展示 API
实现基于元数据驱动的设备类型参数动态展示功能
"""

import logging
from typing import List

from fastapi import APIRouter, Path, Request, Depends, HTTPException

from app.core.dependency import DependAuth
from app.core.response_formatter_v2 import create_formatter
from app.schemas.device_field import DeviceFieldMonitoringResponse
from app.models.device import DeviceField, DeviceType
from app.models.admin import User

logger = logging.getLogger(__name__)

# 全局共享连接器实例
_shared_connector = None

def get_shared_connector():
    """获取全局共享的TDengine连接器实例"""
    global _shared_connector
    if _shared_connector is None:
        from app.settings.config import TDengineCredentials
        from app.core.tdengine_connector import TDengineConnector
        
        # 缓存凭证以避免重复读取环境变量
        if not hasattr(get_shared_connector, "tdengine_creds"):
             get_shared_connector.tdengine_creds = TDengineCredentials()
        creds = get_shared_connector.tdengine_creds
        
        _shared_connector = TDengineConnector(
            host=creds.host,
            port=creds.port,
            user=creds.user,
            password=creds.password,
            database=creds.database
        )
    return _shared_connector

router = APIRouter()


@router.get(
    "/device-fields/monitoring-keys/{device_type_code}",
    summary="获取设备类型的监测关键字段",
    description="根据设备类型代码查询该类型的监测关键字段配置，用于实时监测页面的动态参数展示",
    response_model=None
)
async def get_monitoring_keys(
    request: Request,
    device_type_code: str = Path(..., description="设备类型代码"),
    current_user: User = DependAuth
):
    """
    获取指定设备类型的监测关键字段配置
    
    **验收标准**:
    - 只返回 is_monitoring_key=true 且 is_active=true 的字段
    - 按 sort_order 升序排序
    - 响应时间 < 200ms
    
    **返回字段**:
    - field_name: 字段显示名称
    - field_code: 字段代码（用于数据匹配）
    - field_type: 字段类型（float/int/string/boolean）
    - unit: 单位
    - sort_order: 显示顺序
    - display_config: 显示配置（icon, color等）
    """
    try:
        formatter = create_formatter(request)
        
        # 验证设备类型是否存在
        device_type = await DeviceType.get_or_none(type_code=device_type_code)
        if not device_type:
            return formatter.not_found(f"设备类型 {device_type_code} 不存在")
        
        # 查询监测关键字段
        fields = await DeviceField.filter(
            device_type_code=device_type_code,
            is_monitoring_key=True,
            is_active=True
        ).order_by('sort_order').all()
        
        # 构建响应数据
        field_list = []
        for field in fields:
            field_data = {
                "id": field.id,
                "device_type_code": field.device_type_code,
                "field_name": field.field_name,
                "field_code": field.field_code,
                "field_type": field.field_type,
                "unit": field.unit,
                "sort_order": field.sort_order,
                "display_config": field.display_config,
                "field_category": field.field_category,
                "field_group": field.field_group,  # ✅ 添加字段分组
                "is_default_visible": field.is_default_visible,  # ✅ 添加默认显示
                "group_order": field.group_order,  # ✅ 添加分组排序
                "description": field.description,
                "data_range": field.data_range,
                "alarm_threshold": field.alarm_threshold,
                "is_monitoring_key": field.is_monitoring_key,
                "is_active": field.is_active
            }
            field_list.append(field_data)
        
        logger.info(
            f"获取设备类型 {device_type_code} 的监测关键字段成功，"
            f"共 {len(field_list)} 个字段"
        )
        
        return formatter.success(
            data=field_list,
            message=f"获取设备类型 {device_type_code} 的监测关键字段成功"
        )
        
    except Exception as e:
        logger.error(f"获取监测关键字段失败: {str(e)}", exc_info=True)
        return formatter.internal_error(f"获取监测关键字段失败: {str(e)}")


@router.get(
    "/device-fields/monitoring-keys",
    summary="获取所有设备类型的监测关键字段",
    description="获取所有激活的设备类型的监测关键字段配置",
    response_model=None
)
async def get_all_monitoring_keys(
    request: Request,
    current_user: User = DependAuth
):
    """
    获取所有设备类型的监测关键字段配置
    
    返回格式：
    {
      "WELD_MACHINE": {
        "device_type_name": "焊机",
        "fields": [...]
      },
      ...
    }
    """
    try:
        formatter = create_formatter(request)
        
        # 获取所有激活的设备类型
        device_types = await DeviceType.filter(is_active=True).all()
        
        result = {}
        for device_type in device_types:
            # 查询该类型的监测关键字段
            fields = await DeviceField.filter(
                device_type_code=device_type.type_code,
                is_monitoring_key=True,
                is_active=True
            ).order_by('sort_order').all()
            
            field_list = []
            for field in fields:
                field_data = {
                    "id": field.id,
                    "device_type_code": field.device_type_code,
                    "field_name": field.field_name,
                    "field_code": field.field_code,
                    "field_type": field.field_type,
                    "unit": field.unit,
                    "sort_order": field.sort_order,
                    "display_config": field.display_config,
                    "field_category": field.field_category,
                    "field_group": field.field_group,  # ✅ 添加字段分组
                    "is_default_visible": field.is_default_visible,  # ✅ 添加默认显示
                "group_order": field.group_order,  # ✅ 添加分组排序
                "description": field.description,
                "data_range": field.data_range,
                "alarm_threshold": field.alarm_threshold
            }
                field_list.append(field_data)
            
            result[device_type.type_code] = {
                "device_type_name": device_type.type_name,
                "device_type_code": device_type.type_code,
                "fields": field_list
            }
        
        logger.info(f"获取所有设备类型的监测关键字段成功，共 {len(result)} 种设备类型")
        
        return formatter.success(
            data=result,
            message="获取所有设备类型的监测关键字段成功"
        )
        
    except Exception as e:
        logger.error(f"获取所有监测关键字段失败: {str(e)}", exc_info=True)
        return formatter.internal_error(f"获取所有监测关键字段失败: {str(e)}")



# =====================================================
# 设备实时数据及配置 API (TASK-3)
# =====================================================

@router.get(
    "/devices/{device_code}/realtime-with-config",
    summary="获取设备实时数据及字段配置",
    description="一次性返回设备的实时数据和字段配置，用于动态参数展示",
    response_model=None
)
async def get_realtime_with_config(
    request: Request,
    device_code: str = Path(..., description="设备编码"),
    current_user: User = DependAuth
):
    """
    获取设备实时数据及字段配置
    
    **验收标准**:
    - 返回内容包含: 设备信息、监测字段配置、实时数据
    - 实时数据从 TDengine 查询最新一条记录
    - 字段配置根据设备类型自动匹配
    - 响应时间 < 500ms
    
    **返回数据**:
    - device_code: 设备编码
    - device_name: 设备名称
    - device_type: 设备类型代码
    - monitoring_fields: 监测字段配置列表
    - realtime_data: 实时数据字典
    """
    try:
        formatter = create_formatter(request)
        
        # 1. 查询设备信息
        from app.models.device import DeviceInfo
        device = await DeviceInfo.get_or_none(device_code=device_code)
        if not device:
            return formatter.not_found(f"设备 {device_code} 不存在")
        
        # 2. 查询设备类型的监测字段配置（包含监测字段和AI特征字段）
        from tortoise.expressions import Q
        monitoring_fields = await DeviceField.filter(
            Q(is_monitoring_key=True) | Q(is_ai_feature=True),
            device_type_code=device.device_type,
            is_active=True
        ).order_by('sort_order').all()
        
        # 构建字段配置列表
        field_list = []
        field_codes = []
        for field in monitoring_fields:
            field_data = {
                "id": field.id,
                "device_type_code": field.device_type_code,
                "field_name": field.field_name,
                "field_code": field.field_code,
                "field_type": field.field_type,
                "unit": field.unit,
                "sort_order": field.sort_order,
                "display_config": field.display_config,
                "field_category": field.field_category,
                "field_group": field.field_group,  # ✅ 添加字段分组
                "is_default_visible": field.is_default_visible,  # ✅ 添加默认显示
                "group_order": field.group_order,  # ✅ 添加分组排序
                "description": field.description,
                "data_range": field.data_range,
                "alarm_threshold": field.alarm_threshold
            }
            field_list.append(field_data)
            field_codes.append(field.field_code)
        
        # 3. 从 TDengine 查询实时数据（最新一条记录）
        realtime_data = {}
        
        try:
            # 使用全局共享连接器
            connector = get_shared_connector()
            
            # 构建查询语句 - 使用反引号包裹表名以支持 UUID 格式（包含连字符）
            table_name = f"`device_{device.device_code}`"
            sql = f"SELECT last_row(*) FROM {table_name}"
            
            # logger.info(f"查询设备 {device_code} 实时数据: {sql}")
            res = await connector.query_data(sql)
            
            if res and res.get('code') == 0 and res.get('data') and len(res['data']) > 0:
                row = res['data'][0]
                cols = [c[0] for c in res['column_meta']]
                
                # 解析数据
                for i, col_full in enumerate(cols):
                    # 提取字段名: last_row(field) -> field
                    field_key = col_full
                    if field_key.startswith('last_row(') and field_key.endswith(')'):
                        field_key = field_key[9:-1]
                        
                    realtime_data[field_key] = row[i]
            else:
                # logger.warning(f"TDengine 查询无数据或失败: {res}")
                # 降级方案：如果没有查到数据，尝试从 PostgreSQL 获取（仅作为备用）
                from app.models.device import DeviceRealTimeData
                latest_data = await DeviceRealTimeData.filter(
                    device_id=device.id
                ).order_by('-data_timestamp').first()
                
                if latest_data:
                    metrics = latest_data.metrics or {}
                    for field_code in field_codes:
                        if field_code in metrics:
                            realtime_data[field_code] = metrics[field_code]
                        elif hasattr(latest_data, field_code):
                            realtime_data[field_code] = getattr(latest_data, field_code)

        except Exception as e:
            logger.warning(f"查询设备 {device_code} 的实时数据失败: {str(e)}")
            # 异常情况下也尝试降级到 PostgreSQL
            try:
                from app.models.device import DeviceRealTimeData
                latest_data = await DeviceRealTimeData.filter(
                    device_id=device.id
                ).order_by('-data_timestamp').first()
                if latest_data and latest_data.metrics:
                    realtime_data.update(latest_data.metrics)
            except:
                pass
        
        # 确保所有字段都有值（至少为None）
        for field_code in field_codes:
            if field_code not in realtime_data:
                realtime_data[field_code] = None
        
        # 4. 组装返回数据
        result = {
            "device_code": device.device_code,
            "device_name": device.device_name,
            "device_type": device.device_type,
            "monitoring_fields": field_list,
            "realtime_data": realtime_data
        }
        
        logger.info(
            f"获取设备 {device_code} 的实时数据及配置成功，"
            f"共 {len(field_list)} 个监测字段"
        )
        
        return formatter.success(
            data=result,
            message=f"获取设备 {device_code} 的实时数据及配置成功"
        )
        
    except Exception as e:
        logger.error(f"获取设备实时数据及配置失败: {str(e)}", exc_info=True)
        return formatter.internal_error(f"获取设备实时数据及配置失败: {str(e)}")


# =====================================================
# 批量查询设备实时数据 API (TASK-4)
# =====================================================

@router.post(
    "/devices/batch-realtime-with-config",
    summary="批量获取设备实时数据及配置",
    description="批量查询多个设备的实时数据和字段配置，优化性能",
    response_model=None
)
async def batch_get_realtime_with_config(
    request: Request,
    device_codes: List[str],
    current_user: User = DependAuth
):
    """
    批量获取设备实时数据及配置
    
    **验收标准**:
    - 按设备类型分组查询字段配置，避免重复查询
    - 支持最多 100 个设备同时查询
    - 响应时间 < 500ms (50个设备)
    
    **性能优化**:
    - 相同设备类型的字段配置只查询一次
    - 批量查询设备信息
    - 批量查询实时数据
    """
    try:
        formatter = create_formatter(request)
        
        # 验证设备数量
        if len(device_codes) > 100:
            return formatter.bad_request("设备数量不能超过 100 个")
        
        if not device_codes:
            return formatter.bad_request("设备编码列表不能为空")
        
        # 1. 批量查询设备信息
        from app.models.device import DeviceInfo
        devices = await DeviceInfo.filter(device_code__in=device_codes).all()
        
        if not devices:
            return formatter.not_found("未找到任何设备")
        
        # 2. 按设备类型分组
        device_type_map = {}
        device_map = {}
        for device in devices:
            device_map[device.device_code] = device
            if device.device_type not in device_type_map:
                device_type_map[device.device_type] = []
            device_type_map[device.device_type].append(device)
        
        # 3. 查询每种设备类型的字段配置（只查询一次）
        from tortoise.expressions import Q
        field_config_cache = {}
        for device_type in device_type_map.keys():
            fields = await DeviceField.filter(
                Q(is_monitoring_key=True) | Q(is_ai_feature=True),
                device_type_code=device_type,
                is_active=True
            ).order_by('sort_order').all()
            
            field_list = []
            for field in fields:
                field_data = {
                    "id": field.id,
                    "device_type_code": field.device_type_code,
                    "field_name": field.field_name,
                    "field_code": field.field_code,
                    "field_type": field.field_type,
                    "unit": field.unit,
                    "sort_order": field.sort_order,
                    "display_config": field.display_config,
                    "field_category": field.field_category,
                    "field_group": field.field_group,  # ✅ 添加字段分组
                    "is_default_visible": field.is_default_visible,  # ✅ 添加默认显示
                    "group_order": field.group_order,  # ✅ 添加分组排序
                    "description": field.description,
                    "data_range": field.data_range,
                    "alarm_threshold": field.alarm_threshold
                }
                field_list.append(field_data)
            
            field_config_cache[device_type] = field_list
        
        # 4. 批量查询实时数据
        # TODO: 实际实现时需要从 TDengine 批量查询
        # 这里先使用 PostgreSQL 的 DeviceRealTimeData 作为临时方案
        device_ids = [device.id for device in devices]
        realtime_data_map = {}
        
        try:
            from app.models.device import DeviceRealTimeData
            from tortoise.functions import Max
            
            # 查询每个设备的最新数据
            for device in devices:
                latest_data = await DeviceRealTimeData.filter(
                    device_id=device.id
                ).order_by('-data_timestamp').first()
                
                if latest_data:
                    # 提取所有字段的数据
                    data_dict = {}
                    field_list = field_config_cache.get(device.device_type, [])
                    for field in field_list:
                        field_code = field['field_code']
                        if hasattr(latest_data, field_code):
                            data_dict[field_code] = getattr(latest_data, field_code)
                        elif latest_data.metrics and isinstance(latest_data.metrics, dict) and field_code in latest_data.metrics:
                            data_dict[field_code] = latest_data.metrics[field_code]
                        else:
                            data_dict[field_code] = None
                    realtime_data_map[device.device_code] = data_dict
                else:
                    # 如果没有数据，返回空字典
                    realtime_data_map[device.device_code] = {}
                    
        except Exception as e:
            logger.warning(f"批量查询实时数据失败: {str(e)}")
            # 如果查询失败，返回空数据
            for device in devices:
                realtime_data_map[device.device_code] = {}
        
        # 5. 组装返回数据
        result = []
        for device_code in device_codes:
            device = device_map.get(device_code)
            if device:
                device_data = {
                    "device_code": device.device_code,
                    "device_name": device.device_name,
                    "device_type": device.device_type,
                    "monitoring_fields": field_config_cache.get(device.device_type, []),
                    "realtime_data": realtime_data_map.get(device.device_code, {})
                }
                result.append(device_data)
        
        logger.info(
            f"批量获取设备实时数据及配置成功，"
            f"共 {len(result)} 个设备，{len(device_type_map)} 种设备类型"
        )
        
        return formatter.success(
            data=result,
            message=f"批量获取设备实时数据及配置成功"
        )
        
    except Exception as e:
        logger.error(f"批量获取设备实时数据及配置失败: {str(e)}", exc_info=True)
        return formatter.internal_error(f"批量获取设备实时数据及配置失败: {str(e)}")
