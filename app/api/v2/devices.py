#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
设备管理模块 API v2
实现设备信息管理、设备类型管理、设备监控等功能的RESTful API
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
import asyncio
import json
import jwt

from fastapi import APIRouter, Query, Body, HTTPException, Request, Depends, WebSocket, WebSocketDisconnect
from tortoise.expressions import Q
from tortoise.exceptions import DoesNotExist

from app.controllers.device import device_controller
from app.core.dependency import DependAuth
from app.core.response_formatter_v2 import ResponseFormatterV2, create_formatter
from app.schemas.devices import (
    DeviceCreate,
    DeviceUpdate,
    DeviceResponse,
    DeviceQuery,
    DeviceStatistics,
    DeviceBatchImport,
    BatchImportResult,
    DeviceTypeCreate,
    DeviceTypeUpdate,
    DeviceTypeResponse,
    DeviceTypeDetailResponse,
    DeviceFieldCreate,
    DeviceFieldUpdate,
    DeviceFieldResponse
)
from app.schemas.base import BatchDeleteRequest
from app.models.device import DeviceInfo, DeviceType, DeviceField, DeviceDataModel, DeviceFieldMapping
from app.models.admin import User

logger = logging.getLogger(__name__)

router = APIRouter()


# =====================================================
# 设备信息管理 API v2
# =====================================================

@router.get("", summary="获取设备列表", response_model=None)
async def get_devices(
    request: Request,
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=2000, description="每页数量"),
    device_code: Optional[str] = Query(None, description="设备编号搜索"),
    device_name: Optional[str] = Query(None, description="设备名称搜索"),
    device_type: Optional[str] = Query(None, description="设备类型搜索"),
    manufacturer: Optional[str] = Query(None, description="制造商搜索"),
    install_location: Optional[str] = Query(None, description="安装位置搜索"),
    team_name: Optional[str] = Query(None, description="班组名称搜索"),
    is_locked: Optional[bool] = Query(None, description="锁定状态搜索"),
    device_model: Optional[str] = Query(None, description="设备型号搜索"),
    online_address: Optional[str] = Query(None, description="在线地址搜索"),
    search: Optional[str] = Query(None, description="通用搜索（设备名称或编号）"),
    current_user: User = DependAuth
):
    """
    获取设备列表，支持多条件查询和分页
    
    - **page**: 页码，从1开始
    - **page_size**: 每页数量，最大100
    - **device_code**: 设备编号模糊搜索
    - **device_name**: 设备名称模糊搜索
    - **device_type**: 设备类型搜索
    - **manufacturer**: 制造商模糊搜索
    - **install_location**: 安装位置模糊搜索
    - **team_name**: 班组名称搜索
    - **is_locked**: 锁定状态筛选
    - **device_model**: 设备型号模糊搜索
    - **online_address**: 在线地址模糊搜索
    - **search**: 通用搜索（匹配设备名称或编号）
    """
    try:
        formatter = create_formatter(request)
        
        # 构建查询条件
        q = Q()
        
        # 通用搜索（优先级较高，与其他条件是AND关系，但在内部是OR）
        if search:
            q &= (Q(device_name__contains=search) | Q(device_code__contains=search))
            
        if device_code:
            q &= Q(device_code__contains=device_code)
        if device_name:
            q &= Q(device_name__contains=device_name)
        if device_type:
            q &= Q(device_type__contains=device_type)
        if manufacturer:
            q &= Q(manufacturer__contains=manufacturer)
        if install_location:
            q &= Q(install_location__contains=install_location)
        if team_name:
            q &= Q(team_name__contains=team_name)
        if is_locked is not None:
            q &= Q(is_locked=is_locked)
        if device_model:
            q &= Q(device_model__contains=device_model)
        if online_address:
            q &= Q(online_address__contains=online_address)

        # 获取分页数据
        total, device_objs = await device_controller.get_multi_with_total(
            page=page, 
            page_size=page_size, 
            search=q
        )
        
        # 转换为响应格式
        data = []
        for device in device_objs:
            device_dict = await device.to_dict()
            data.append(device_dict)

        # 构建查询参数用于HATEOAS链接
        query_params = {}
        if device_code:
            query_params['device_code'] = device_code
        if device_name:
            query_params['device_name'] = device_name
        if device_type:
            query_params['device_type'] = device_type
        if manufacturer:
            query_params['manufacturer'] = manufacturer
        if install_location:
            query_params['install_location'] = install_location
        if team_name:
            query_params['team_name'] = team_name
        if is_locked is not None:
            query_params['is_locked'] = is_locked
        if device_model:
            query_params['device_model'] = device_model
        if online_address:
            query_params['online_address'] = online_address

        return formatter.paginated_success(
            data=data,
            total=total,
            page=page,
            page_size=page_size,
            message="获取设备列表成功",
            resource_type="devices",
            query_params=query_params
        )

    except Exception as e:
        logger.error(f"获取设备列表失败: {str(e)}", exc_info=True)
        formatter = create_formatter(request)
        return formatter.internal_error(f"获取设备列表失败: {str(e)}")


# =====================================================
# 设备类型管理 API v2 (归并到设备模块)
# =====================================================

@router.get("/types", summary="获取设备类型列表", response_model=None)
async def get_device_types(
    request: Request,
    is_active: Optional[bool] = Query(None, description="是否激活状态筛选"),
    type_name: Optional[str] = Query(None, description="类型名称搜索"),
    type_code: Optional[str] = Query(None, description="类型编码搜索"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    include_counts: bool = Query(False, description="是否包含统计数据"),
    current_user: User = DependAuth
):
    """
    获取设备类型列表
    
    - **is_active**: 激活状态筛选
    - **type_name**: 类型名称模糊搜索
    - **type_code**: 类型编码模糊搜索
    - **page**: 页码
    - **page_size**: 每页数量
    - **include_counts**: 是否包含设备数量统计
    """
    try:
        formatter = create_formatter(request)
        
        # 构建查询条件
        query = DeviceType.all()
        if is_active is not None:
            query = query.filter(is_active=is_active)
        if type_name:
            query = query.filter(type_name__icontains=type_name)
        if type_code:
            query = query.filter(type_code__icontains=type_code)
        
        # 分页查询
        offset = (page - 1) * page_size
        device_types = await query.offset(offset).limit(page_size).order_by('created_at')
        total = await query.count()
        
        result = []
        for device_type in device_types:
            type_data = {
                "id": device_type.id,
                "type_name": device_type.type_name,
                "type_code": device_type.type_code,
                "tdengine_stable_name": device_type.tdengine_stable_name,
                "description": device_type.description,
                "icon": device_type.icon,
                "is_active": device_type.is_active,
                "created_at": device_type.created_at.isoformat() if device_type.created_at else None,
                "updated_at": device_type.updated_at.isoformat() if device_type.updated_at else None
            }
            
            if include_counts:
                type_data["device_count"] = device_type.device_count
                # 获取字段数量
                field_count = await DeviceField.filter(device_type_code=device_type.type_code).count()
                type_data["field_count"] = field_count
            else:
                type_data["device_count"] = 0
                type_data["field_count"] = 0
            
            result.append(type_data)

        # 构建查询参数
        query_params = {}
        if is_active is not None:
            query_params['is_active'] = is_active
        if type_name:
            query_params['type_name'] = type_name
        if type_code:
            query_params['type_code'] = type_code
        if include_counts:
            query_params['include_counts'] = include_counts

        return formatter.paginated_success(
            data=result,
            total=total,
            page=page,
            page_size=page_size,
            message="获取设备类型列表成功",
            resource_type="devices/types",
            query_params=query_params
        )

    except Exception as e:
        logger.error(f"获取设备类型列表失败: {str(e)}", exc_info=True)
        formatter = create_formatter(request)
        return formatter.internal_error(f"获取设备类型列表失败: {str(e)}")


@router.get("/types/{type_code}", summary="获取设备类型详情", response_model=None, dependencies=[DependAuth])
async def get_device_type_detail(
    request: Request,
    type_code: str,
    current_user: User = DependAuth
):
    """
    获取设备类型详情，包含字段定义
    
    - **type_code**: 设备类型编码
    """
    try:
        formatter = create_formatter(request)
        
        # 获取设备类型
        try:
            device_type = await DeviceType.get(type_code=type_code)
        except DoesNotExist:
            return formatter.not_found(f"设备类型 {type_code} 不存在", "device_type")
        
        # 获取字段定义
        fields = await DeviceField.filter(device_type_code=type_code).order_by('sort_order', 'field_name')
        
        # 构建字段列表
        field_list = []
        for field in fields:
            field_data = {
                "id": field.id,
                "device_type_code": field.device_type_code,
                "field_name": field.field_name,
                "field_type": field.field_type,
                "field_description": field.field_description,
                "is_required": field.is_required,
                "is_tag": field.is_tag,
                "sort_order": field.sort_order,
                "created_at": field.created_at.isoformat() if field.created_at else None,
                "updated_at": field.updated_at.isoformat() if field.updated_at else None
            }
            field_list.append(field_data)
        
        # 构建响应数据
        result = {
            "id": device_type.id,
            "type_name": device_type.type_name,
            "type_code": device_type.type_code,
            "tdengine_stable_name": device_type.tdengine_stable_name,
            "description": device_type.description,
            "icon": device_type.icon,
            "is_active": device_type.is_active,
            "device_count": device_type.device_count,
            "field_count": len(field_list),
            "created_at": device_type.created_at.isoformat() if device_type.created_at else None,
            "updated_at": device_type.updated_at.isoformat() if device_type.updated_at else None,
            "fields": field_list
        }
        
        return formatter.success(
            data=result,
            message="获取设备类型详情成功",
            resource_id=type_code,
            resource_type="devices/types"
        )

    except Exception as e:
        logger.error(f"获取设备类型详情失败: {str(e)}", exc_info=True)
        formatter = create_formatter(request)
        return formatter.internal_error(f"获取设备类型详情失败: {str(e)}")


@router.post("/types", summary="创建设备类型", response_model=None, dependencies=[DependAuth])
async def create_device_type(
    request: Request,
    device_type_data: DeviceTypeCreate,
    current_user: User = DependAuth
):
    """
    创建新的设备类型
    
    - **type_name**: 设备类型名称
    - **type_code**: 设备类型编码，必须唯一
    - **tdengine_stable_name**: TDengine超级表名
    - **description**: 类型描述（可选）
    - **is_active**: 是否激活（默认true）
    """
    try:
        formatter = create_formatter(request)
        
        # 检查类型代码是否已存在
        if await DeviceType.filter(type_code=device_type_data.type_code).exists():
            return formatter.error(
                f"设备类型代码 {device_type_data.type_code} 已存在",
                code=400,
                error_type="ValidationError"
            )
        
        # 创建设备类型
        device_type = await DeviceType.create(**device_type_data.model_dump())
        
        return formatter.success(
            data={"id": device_type.id, "type_code": device_type.type_code},
            message="设备类型创建成功",
            code=201,
            resource_id=device_type.type_code,
            resource_type="devices/types"
        )

    except Exception as e:
        logger.error(f"创建设备类型失败: {str(e)}", exc_info=True)
        formatter = create_formatter(request)
        return formatter.internal_error(f"创建设备类型失败: {str(e)}")


@router.put("/types/{type_code}", summary="更新设备类型", response_model=None, dependencies=[DependAuth])
async def update_device_type(
    request: Request,
    type_code: str,
    device_type_data: DeviceTypeUpdate,
    current_user: User = DependAuth
):
    """
    更新设备类型信息
    
    - **type_code**: 设备类型编码
    - 其他字段与创建设备类型相同，均为可选
    """
    try:
        formatter = create_formatter(request)
        
        # 获取设备类型
        try:
            device_type = await DeviceType.get(type_code=type_code)
        except DoesNotExist:
            return formatter.not_found(f"设备类型 {type_code} 不存在", "device_type")
        
        # 更新字段
        update_data = device_type_data.model_dump(exclude_unset=True)
        if update_data:
            await device_type.update_from_dict(update_data)
            await device_type.save()
        
        return formatter.success(
            message="设备类型更新成功",
            resource_id=type_code,
            resource_type="devices/types"
        )

    except Exception as e:
        logger.error(f"更新设备类型失败: {str(e)}", exc_info=True)
        formatter = create_formatter(request)
        return formatter.internal_error(f"更新设备类型失败: {str(e)}")


@router.post("/types/batch-delete", summary="批量删除设备类型", response_model=None, dependencies=[DependAuth])
async def batch_delete_device_types(
    request: Request,
    batch_req: BatchDeleteRequest,
    cascade: bool = Query(False, description="是否级联删除关联设备"),
    current_user: User = DependAuth
):
    """
    批量删除设备类型
    
    - **ids**: 设备类型ID列表 (注意：虽然模型用 type_code 标识，但 BatchDeleteRequest 传的是 ids。如果前端传 type_code，需调整)
    """
    # Wait, DeviceType uses type_code as key in URL, but has ID PK?
    # Model: `class DeviceType(TimestampMixin, BaseModel): ... type_code ...`
    # BaseModel has `id` (Int).
    # So we can delete by ID.
    # But `delete_device_type` uses `type_code`.
    # The frontend `BatchDeleteRequest` sends `ids` (integers).
    # So I should delete by ID.
    
    try:
        formatter = create_formatter(request)
        ids = batch_req.ids
        
        if not ids:
            return formatter.validation_error("ID列表不能为空")
            
        success_count = 0
        failed_count = 0
        errors = []
        
        from tortoise.transactions import in_transaction
        
        async with in_transaction("default"):
            for type_id in ids:
                try:
                    # Get type to find type_code (needed for cascade)
                    device_type = await DeviceType.get_or_none(id=type_id)
                    if not device_type:
                        failed_count += 1
                        errors.append(f"ID {type_id}: 类型不存在")
                        continue
                        
                    type_code = device_type.type_code
                    
                    # Check/Cascade logic (Same as single delete)
                    device_count = await DeviceInfo.filter(device_type=type_code).count()
                    
                    if device_count > 0:
                        if not cascade:
                            failed_count += 1
                            errors.append(f"ID {type_id} ({type_code}): 还有 {device_count} 个设备，需确认级联删除")
                            continue
                        
                        # Cascade delete devices
                        devices = await DeviceInfo.filter(device_type=type_code).all()
                        for device in devices:
                            await device_controller.delete_device(device.id)
                    
                    # Cascade delete metadata
                    await DeviceField.filter(device_type_code=type_code).delete()
                    await DeviceDataModel.filter(device_type_code=type_code).delete()
                    await DeviceFieldMapping.filter(device_type_code=type_code).delete()
                    
                    # Delete Type
                    await device_type.delete()
                    success_count += 1
                    
                except Exception as e:
                    failed_count += 1
                    errors.append(f"ID {type_id}: {str(e)}")
        
        return formatter.success(
            message=f"批量删除完成: 成功 {success_count}, 失败 {failed_count}",
            data={
                "success_count": success_count, 
                "failed_count": failed_count,
                "errors": errors
            },
            resource_type="devices/types"
        )

    except Exception as e:
        logger.error(f"批量删除设备类型失败: {str(e)}", exc_info=True)
        formatter = create_formatter(request)
        return formatter.internal_error(f"批量删除设备类型失败: {str(e)}")


@router.delete("/types/{type_code}", summary="删除设备类型", response_model=None, dependencies=[DependAuth])
async def delete_device_type(
    request: Request,
    type_code: str,
    cascade: bool = Query(False, description="是否级联删除关联设备"),
    current_user: User = DependAuth
):
    """
    删除设备类型（软删除，设置为非激活状态）
    
    - **type_code**: 设备类型编码
    - **cascade**: 是否级联删除关联设备
    """
    try:
        formatter = create_formatter(request)
        
        # 检查是否有关联的设备
        device_count = await DeviceInfo.filter(device_type=type_code).count()
        if device_count > 0:
            if not cascade:
                return formatter.error(
                    f"该设备类型下还有 {device_count} 个设备，无法删除",
                    code=400,
                    error_type="ValidationError"
                )
            
            # 级联删除所有关联设备
            # 使用 device_controller.delete_device 以确保清理所有关联数据
            devices = await DeviceInfo.filter(device_type=type_code).all()
            from tortoise.transactions import in_transaction
            async with in_transaction("default"):
                for device in devices:
                    await device_controller.delete_device(device.id)

        # 获取设备类型
        try:
            device_type = await DeviceType.get(type_code=type_code)
        except DoesNotExist:
            return formatter.not_found(f"设备类型 {type_code} 不存在", "device_type")
        
        # 物理删除（包括关联元数据清理）
        from tortoise.transactions import in_transaction
        async with in_transaction("default"):
            # 如果是级联删除，设备已经在上面被删除了（或者上面逻辑有误？）
            # Wait, my previous code block:
            # if device_count > 0:
            #    if not cascade: return error
            #    for device in devices: delete_device(device.id)
            #
            # This block is BEFORE "获取设备类型".
            # If cascade=True, devices are gone.
            # Now we delete the type and metadata.
            
            # 级联删除元数据配置
            await DeviceField.filter(device_type_code=type_code).delete()
            await DeviceDataModel.filter(device_type_code=type_code).delete()
            await DeviceFieldMapping.filter(device_type_code=type_code).delete()
            
            # 物理删除设备类型
            await device_type.delete()
        
        return formatter.success(
            message="设备类型删除成功",
            resource_type="devices/types"
        )

    except Exception as e:
        logger.error(f"删除设备类型失败: {str(e)}", exc_info=True)
        formatter = create_formatter(request)
        return formatter.internal_error(f"删除设备类型失败: {str(e)}")


# =====================================================


@router.get("/alarms", summary="获取设备报警信息", response_model=None)
async def get_device_alarms(
    request: Request,
    device_code: Optional[str] = Query(None, description="设备编号筛选"),
    start_time: Optional[datetime] = Query(None, description="开始时间"),
    end_time: Optional[datetime] = Query(None, description="结束时间"),
    date_from: Optional[str] = Query(None, description="开始时间（字符串格式）"),
    date_to: Optional[str] = Query(None, description="结束时间（字符串格式）"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    current_user: User = DependAuth
):
    """
    获取设备报警信息
    
    - **device_code**: 设备编号筛选（可选）
    - **start_time**: 开始时间（可选）
    - **end_time**: 结束时间（可选）
    - **page**: 页码
    - **page_size**: 每页数量
    """
    try:
        formatter = create_formatter(request)
        
        # 构建查询条件
        from app.models.device import WeldingAlarmHistory
        from datetime import datetime
        query = WeldingAlarmHistory.all()
        
        # 处理设备编号筛选
        if device_code:
            query = query.filter(prod_code__contains=device_code)
        
        # 处理搜索关键词
        if search:
            query = query.filter(prod_code__contains=search)
        
        # 处理时间范围 - 优先使用date_from/date_to，其次使用start_time/end_time
        if date_from:
            try:
                # 支持多种时间格式
                if 'T' in date_from:
                    # ISO格式：2025-07-31T16:00:00
                    parsed_start_time = datetime.fromisoformat(date_from.replace('Z', '+00:00'))
                else:
                    # 标准格式：2025-07-31 16:00:00
                    parsed_start_time = datetime.strptime(date_from, '%Y-%m-%d %H:%M:%S')
                query = query.filter(alarm_time__gte=parsed_start_time)
                logger.info(f"应用开始时间过滤: {parsed_start_time}")
            except (ValueError, TypeError) as e:
                logger.warning(f"解析开始时间失败: {date_from}, 错误: {e}")
        elif start_time:
            query = query.filter(alarm_time__gte=start_time)
            
        if date_to:
            try:
                # 支持多种时间格式
                if 'T' in date_to:
                    # ISO格式：2025-07-31T16:00:00
                    parsed_end_time = datetime.fromisoformat(date_to.replace('Z', '+00:00'))
                else:
                    # 标准格式：2025-07-31 16:00:00
                    parsed_end_time = datetime.strptime(date_to, '%Y-%m-%d %H:%M:%S')
                query = query.filter(alarm_time__lte=parsed_end_time)
                logger.info(f"应用结束时间过滤: {parsed_end_time}")
            except (ValueError, TypeError) as e:
                logger.warning(f"解析结束时间失败: {date_to}, 错误: {e}")
        elif end_time:
            query = query.filter(alarm_time__lte=end_time)

        # 分页查询
        offset = (page - 1) * page_size
        alarms = await query.offset(offset).limit(page_size).order_by('-alarm_time')
        total = await query.count()
        
        # 转换数据格式
        result = []
        for alarm in alarms:
            item = {
                "id": alarm.id,
                "prod_code": alarm.prod_code,
                "alarm_time": alarm.alarm_time.isoformat() if alarm.alarm_time else None,
                "alarm_end_time": alarm.alarm_end_time.isoformat() if alarm.alarm_end_time else None,
                "alarm_duration_sec": alarm.alarm_duration_sec,
                "alarm_code": alarm.alarm_code,
                "alarm_message": alarm.alarm_message,
                "alarm_solution": alarm.alarm_solution,
                "created_at": alarm.created_at.isoformat() if alarm.created_at else None
            }
            result.append(item)

        # 构建查询参数
        query_params = {}
        if device_code:
            query_params['device_code'] = device_code
        if start_time:
            query_params['start_time'] = start_time.isoformat()
        if end_time:
            query_params['end_time'] = end_time.isoformat()

        return formatter.paginated_success(
            data=result,
            total=total,
            page=page,
            page_size=page_size,
            message="获取设备报警信息成功",
            resource_type="devices/alarms",
            query_params=query_params
        )

    except Exception as e:
        logger.error(f"获取设备报警信息失败: {str(e)}", exc_info=True)
        formatter = create_formatter(request)
        return formatter.internal_error(f"获取设备报警信息失败: {str(e)}")


@router.get("/statistics", summary="设备统计信息", response_model=None)
async def get_device_statistics(
    request: Request,
    device_type: Optional[str] = Query(None, description="设备类型筛选"),
    team_name: Optional[str] = Query(None, description="班组名称筛选"),
    current_user: User = DependAuth
):
    """
    获取设备统计信息
    
    包括：
    - 设备总数
    - 锁定/未锁定设备数
    - 在线/离线设备数
    - 预警/故障设备数
    - 维护中设备数
    - 按类型统计
    - 按班组统计
    
    可选参数：
    - device_type: 按设备类型筛选统计
    - team_name: 按班组名称筛选统计
    """
    try:
        formatter = create_formatter(request)
        
        # 构建基础查询条件
        base_query = Q()
        if device_type:
            base_query &= Q(device_type=device_type)
        if team_name:
            base_query &= Q(team_name=team_name)
        
        # 总设备数
        total_devices = await device_controller.count(search=base_query)

        # 锁定设备数
        locked_query = base_query & Q(is_locked=True)
        locked_count = await device_controller.count(search=locked_query)
        unlocked_count = total_devices - locked_count

        # 获取在线设备数（通过实时数据表统计）
        from app.models.device import DeviceRealTimeData
        from datetime import timedelta
        
        # 获取符合筛选条件的设备ID列表
        filtered_device_ids = None
        if device_type or team_name:
            devices = await DeviceInfo.filter(base_query).values_list('id', flat=True)
            filtered_device_ids = list(devices)
        
        # 最近5分钟有数据的设备视为在线
        recent_time = datetime.now() - timedelta(minutes=5)
        online_devices_query = DeviceRealTimeData.filter(
            data_timestamp__gte=recent_time,
            status="online"
        )
        if filtered_device_ids is not None:
            online_devices_query = online_devices_query.filter(device_id__in=filtered_device_ids)
        online_devices = await online_devices_query.distinct().values_list('device_id', flat=True)
        online_count = len(set(online_devices))
        offline_count = total_devices - online_count
        
        # 预警设备数（状态为warning）
        warning_devices_query = DeviceRealTimeData.filter(
            data_timestamp__gte=recent_time,
            status="warning"
        )
        if filtered_device_ids is not None:
            warning_devices_query = warning_devices_query.filter(device_id__in=filtered_device_ids)
        warning_devices = await warning_devices_query.distinct().values_list('device_id', flat=True)
        warning_count = len(set(warning_devices))
        
        # 故障设备数（状态为error或alarm）
        error_devices_query = DeviceRealTimeData.filter(
            data_timestamp__gte=recent_time,
            status__in=["error", "alarm", "fault"]
        )
        if filtered_device_ids is not None:
            error_devices_query = error_devices_query.filter(device_id__in=filtered_device_ids)
        error_devices = await error_devices_query.distinct().values_list('device_id', flat=True)
        error_count = len(set(error_devices))
        
        # 维护中设备数（状态为maintenance）
        maintenance_devices_query = DeviceRealTimeData.filter(
            data_timestamp__gte=recent_time,
            status="maintenance"
        )
        if filtered_device_ids is not None:
            maintenance_devices_query = maintenance_devices_query.filter(device_id__in=filtered_device_ids)
        maintenance_devices = await maintenance_devices_query.distinct().values_list('device_id', flat=True)
        maintenance_count = len(set(maintenance_devices))

        # 按类型统计
        type_stats = await device_controller.get_type_statistics()

        # 按班组统计
        team_stats = await device_controller.get_team_statistics()

        statistics = {
            "total_devices": total_devices,
            "locked_devices": locked_count,
            "unlocked_devices": unlocked_count,
            "online_devices": online_count,
            "offline_devices": offline_count,
            "warning_devices": warning_count,
            "error_devices": error_count,
            "maintenance_devices": maintenance_count,
            "device_types": type_stats,
            "teams": team_stats
        }

        return formatter.success(
            data=statistics,
            message="获取设备统计信息成功",
            resource_type="devices"
        )

    except Exception as e:
        logger.error(f"获取设备统计信息失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="获取设备统计信息失败")


@router.get("/{device_id}", summary="获取设备详情", response_model=None, dependencies=[DependAuth])
async def get_device(
    request: Request,
    device_id: int,
    current_user: User = DependAuth
):
    """
    根据设备ID获取设备详细信息
    
    - **device_id**: 设备ID
    """
    try:
        formatter = create_formatter(request)
        
        device_obj = await device_controller.get(id=device_id)
        if not device_obj:
            return formatter.not_found("设备不存在", "device")

        device_dict = await device_obj.to_dict()
        
        return formatter.success(
            data=device_dict,
            message="获取设备详情成功",
            resource_id=str(device_id),
            resource_type="devices"
        )

    except Exception as e:
        logger.error(f"获取设备详情失败: {str(e)}", exc_info=True)
        formatter = create_formatter(request)
        return formatter.internal_error(f"获取设备详情失败: {str(e)}")


@router.post("", summary="创建设备", response_model=None, dependencies=[DependAuth])
async def create_device(
    request: Request,
    device_in: DeviceCreate,
    current_user: User = DependAuth
):
    """
    创建新设备
    
    - **device_code**: 设备编号，必须唯一
    - **device_name**: 设备名称
    - **device_model**: 设备型号（可选）
    - **device_type**: 设备类型（可选）
    - **manufacturer**: 制造商（可选）
    - **production_date**: 出厂日期（可选）
    - **install_date**: 安装日期（可选）
    - **install_location**: 安装位置（可选）
    - **online_address**: 在线地址（可选）
    - **team_name**: 所属班组（可选）
    - **is_locked**: 是否锁定（默认false）
    - **description**: 备注信息（可选）
    """
    try:
        formatter = create_formatter(request)
        
        device_obj = await device_controller.create_device(obj_in=device_in)
        
        return formatter.success(
            data={"id": device_obj.id, "device_code": device_obj.device_code},
            message="设备创建成功",
            code=201,
            resource_id=str(device_obj.id),
            resource_type="devices"
        )

    except HTTPException as e:
        formatter = create_formatter(request)
        if e.status_code == 400:
            return formatter.error(str(e.detail), code=400, error_type="ValidationError")
        elif e.status_code == 404:
            return formatter.not_found(str(e.detail))
        else:
            return formatter.internal_error(str(e.detail))
    except Exception as e:
        logger.error(f"创建设备失败: {str(e)}", exc_info=True)
        formatter = create_formatter(request)
        return formatter.internal_error(f"创建设备失败: {str(e)}")


@router.put("/{device_id}", summary="更新设备", response_model=None, dependencies=[DependAuth])
async def update_device(
    request: Request,
    device_id: int,
    device_in: DeviceUpdate,
    current_user: User = DependAuth
):
    """
    更新设备信息
    
    - **device_id**: 设备ID
    - 其他字段与创建设备相同，均为可选
    """
    try:
        formatter = create_formatter(request)
        
        # 检查设备是否存在
        device_obj = await device_controller.get(id=device_id)
        if not device_obj:
            return formatter.not_found("设备不存在", "device")

        await device_controller.update_device(id=device_id, obj_in=device_in)
        
        return formatter.success(
            data={"id": device_id},
            message="设备更新成功",
            resource_id=str(device_id),
            resource_type="devices"
        )

    except HTTPException as e:
        formatter = create_formatter(request)
        if e.status_code == 400:
            return formatter.error(str(e.detail), code=400, error_type="ValidationError")
        elif e.status_code == 404:
            return formatter.not_found(str(e.detail))
        else:
            return formatter.internal_error(str(e.detail))
    except Exception as e:
        logger.error(f"更新设备失败: {str(e)}", exc_info=True)
        formatter = create_formatter(request)
        return formatter.internal_error(f"更新设备失败: {str(e)}")


@router.get("/{device_id}/related-counts", summary="获取设备关联数据统计", response_model=None, dependencies=[DependAuth])
async def get_device_related_counts(
    request: Request,
    device_id: int,
    current_user: User = DependAuth
):
    """获取设备关联数据统计"""
    try:
        formatter = create_formatter(request)
        counts = await device_controller.get_related_counts(device_id)
        return formatter.success(data=counts)
    except Exception as e:
        logger.error(f"获取关联统计失败: {str(e)}", exc_info=True)
        formatter = create_formatter(request)
        return formatter.internal_error(f"获取关联统计失败: {str(e)}")


@router.delete("/{device_id}", summary="删除设备", response_model=None, dependencies=[DependAuth])
async def delete_device(
    request: Request,
    device_id: int,
    current_user: User = DependAuth
):
    """
    删除设备
    
    - **device_id**: 设备ID
    """
    try:
        formatter = create_formatter(request)
        
        # 检查设备是否存在
        device_obj = await device_controller.get(id=device_id)
        if not device_obj:
            return formatter.not_found("设备不存在", "device")

        await device_controller.delete_device(id=device_id)
        
        return formatter.success(
            message="设备删除成功",
            resource_type="devices"
        )

    except HTTPException as e:
        formatter = create_formatter(request)
        if e.status_code == 404:
            return formatter.not_found(str(e.detail))
        else:
            return formatter.internal_error(str(e.detail))
    except Exception as e:
        logger.error(f"删除设备失败: {str(e)}", exc_info=True)
        formatter = create_formatter(request)
        return formatter.internal_error(f"删除设备失败: {str(e)}")


@router.post("/batch-delete", summary="批量删除设备", response_model=None, dependencies=[DependAuth])
async def batch_delete_devices(
    request: Request,
    batch_req: BatchDeleteRequest,
    current_user: User = DependAuth
):
    """
    批量删除设备
    
    - **ids**: 设备ID列表
    """
    try:
        formatter = create_formatter(request)
        ids = batch_req.ids
        
        if not ids:
            return formatter.validation_error("ID列表不能为空")
            
        success_count = 0
        failed_count = 0
        errors = []
        
        from tortoise.transactions import in_transaction

        # 使用事务包裹批量操作
        # 注意：controller.delete_device 内部也有事务，这里使用 default 连接
        async with in_transaction("default"):
            for device_id in ids:
                try:
                    # 检查设备是否存在
                    device_obj = await device_controller.get(id=device_id)
                    if not device_obj:
                        failed_count += 1
                        errors.append(f"ID {device_id}: 设备不存在")
                        continue
                        
                    await device_controller.delete_device(id=device_id)
                    success_count += 1
                except Exception as e:
                    failed_count += 1
                    errors.append(f"ID {device_id}: {str(e)}")
        
        message = f"批量删除完成: 成功 {success_count}, 失败 {failed_count}"
        
        return formatter.success(
            message=message,
            data={
                "success_count": success_count, 
                "failed_count": failed_count,
                "errors": errors
            },
            resource_type="devices"
        )

    except Exception as e:
        logger.error(f"批量删除设备失败: {str(e)}", exc_info=True)
        formatter = create_formatter(request)
        return formatter.internal_error(f"批量删除设备失败: {str(e)}")


@router.post("/batch", summary="批量操作设备", response_model=None)
async def batch_devices(
    request: Request,
    devices: List[DeviceCreate] = Body(..., description="设备列表"),
    update_existing: bool = Body(False, description="是否更新已存在的设备"),
    current_user: User = DependAuth
):
    """
    批量导入设备信息
    
    - **devices**: 设备列表
    - **update_existing**: 是否更新已存在的设备
      - false（默认）: 跳过已存在设备
      - true: 更新已存在设备的数据
    """
    try:
        formatter = create_formatter(request)
        
        success_count = 0
        failed_items = []

        for i, device_data in enumerate(devices):
            try:
                # 检查设备编号是否已存在
                existing_device = await device_controller.get_by_device_code(device_code=device_data.device_code)
                if existing_device:
                    if update_existing:
                        # 更新现有设备
                        await device_controller.update_device(
                            id=existing_device.id, 
                            obj_in=DeviceUpdate(**device_data.model_dump())
                        )
                        success_count += 1
                        logger.info(f"成功更新设备: {existing_device.id} - {existing_device.device_code}")
                    else:
                        failed_items.append({
                            "index": i + 1,
                            "device_code": device_data.device_code,
                            "error": "设备编号已存在"
                        })
                    continue

                # 创建设备
                device_obj = await device_controller.create_device(obj_in=device_data)
                success_count += 1
                logger.info(f"成功导入设备: {device_obj.id} - {device_obj.device_code}")

            except HTTPException as e:
                failed_items.append({
                    "index": i + 1,
                    "device_code": device_data.device_code,
                    "error": str(e.detail)
                })
            except Exception as e:
                logger.error(f"导入设备失败: {str(e)}", exc_info=True)
                failed_items.append({
                    "index": i + 1,
                    "device_code": device_data.device_code,
                    "error": str(e),
                    "error_type": type(e).__name__
                })

        result = {
            "total_count": len(devices),
            "success_count": success_count,
            "failed_count": len(failed_items),
            "failed_items": failed_items
        }

        message = f"批量导入完成，成功{success_count}条，失败{len(failed_items)}条"
        
        return formatter.success(
            data=result,
            message=message,
            resource_type="devices"
        )

    except Exception as e:
        logger.error(f"批量导入设备失败: {str(e)}", exc_info=True)
        formatter = create_formatter(request)
        return formatter.internal_error(f"批量导入设备失败: {str(e)}")


@router.get("/search", summary="高级搜索设备", response_model=None)
async def search_devices(
    request: Request,
    keyword: str = Query("", description="关键词，搜索设备编号、名称、型号"),
    device_type: str = Query("", description="设备类型"),
    manufacturer: str = Query("", description="制造商"),
    install_location: str = Query("", description="安装位置"),
    team_name: str = Query("", description="班组名称"),
    is_locked: Optional[bool] = Query(None, description="是否锁定"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    current_user: User = DependAuth
):
    """
    多条件搜索设备
    
    - **keyword**: 关键词搜索，匹配设备编号、名称、型号
    - **device_type**: 设备类型筛选
    - **manufacturer**: 制造商筛选
    - **install_location**: 安装位置筛选
    - **team_name**: 班组名称筛选
    - **is_locked**: 锁定状态筛选
    - **page**: 页码
    - **page_size**: 每页数量
    """
    try:
        formatter = create_formatter(request)
        
        total, device_objs = await device_controller.search_devices(
            keyword=keyword,
            device_type=device_type,
            manufacturer=manufacturer,
            team_name=team_name,
            is_locked=is_locked,
            page=page,
            page_size=page_size
        )
        
        # 转换为响应格式
        data = []
        for device in device_objs:
            device_dict = await device.to_dict()
            data.append(device_dict)

        # 构建查询参数
        query_params = {}
        if keyword:
            query_params['keyword'] = keyword
        if device_type:
            query_params['device_type'] = device_type
        if manufacturer:
            query_params['manufacturer'] = manufacturer
        if install_location:
            query_params['install_location'] = install_location
        if team_name:
            query_params['team_name'] = team_name
        if is_locked is not None:
            query_params['is_locked'] = is_locked

        return formatter.paginated_success(
            data=data,
            total=total,
            page=page,
            page_size=page_size,
            message="搜索设备成功",
            resource_type="devices/search",
            query_params=query_params
        )

    except Exception as e:
        logger.error(f"搜索设备失败: {str(e)}", exc_info=True)
        formatter = create_formatter(request)
        return formatter.internal_error(f"搜索设备失败: {str(e)}")


@router.get("/statistics/dashboard/online-welding-rate", summary="获取在线率和焊接率统计数据", response_model=None)
async def get_online_welding_rate_statistics(
    request: Request,
    start_time: str = Query(..., description="开始时间 (YYYY-MM-DD)"),
    end_time: str = Query(..., description="结束时间 (YYYY-MM-DD)"),
    current_user: User = DependAuth
):
    """
    获取在线率和焊接率统计数据 (V2版本)
    
    Args:
        start_time: 开始时间 (YYYY-MM-DD)
        end_time: 结束时间 (YYYY-MM-DD)
        
    Returns:
        包含设备总数、焊接设备数、开机设备数、关机设备数、在线率、焊接率的数据
        响应格式符合V2标准，包含success、code、message、data、meta等字段
    """
    try:
        formatter = create_formatter(request)
        
        # 使用现有的controller方法
        from app.controllers.device_data import DeviceDataController
        controller = DeviceDataController()
        result = await controller.get_online_welding_rate_statistics(start_time, end_time)
        
        return formatter.success(
            data=result,
            message="获取在线率和焊接率统计数据成功",
            resource_type="devices/statistics/dashboard"
        )
        
    except Exception as e:
        logger.error(f"获取在线率和焊接率统计数据失败: {str(e)}", exc_info=True)
        formatter = create_formatter(request)
        return formatter.internal_error(f"获取在线率和焊接率统计数据失败: {str(e)}")


@router.get("/statistics/dashboard/alarm-category-summary", summary="获取报警类型分布统计")
async def get_alarm_category_summary(
    request: Request,
    start_time: str = Query(..., description="开始时间"),
    end_time: str = Query(..., description="结束时间")
):
    """
    获取报警类型分布统计数据
    
    Args:
        start_time: 开始时间
        end_time: 结束时间
    
    Returns:
        报警类型分布统计数据
    """
    try:
        # 复用V1控制器的逻辑
        from app.controllers.device_data import DeviceDataController
        controller = DeviceDataController()
        result = await controller.get_alarm_category_summary(start_time, end_time)
        
        formatter = create_formatter(request)
        return formatter.success(data=result, message="获取报警类型分布统计数据成功")
        
    except Exception as e:
        logger.error(f"获取报警类型分布统计数据失败: {str(e)}", exc_info=True)
        formatter = create_formatter(request)
        return formatter.internal_error(f"获取报警类型分布统计数据失败: {str(e)}")


@router.get("/statistics/dashboard/alarm-record-top", summary="获取报警记录Top排名")
async def get_alarm_record_top(
    request: Request,
    start_time: str = Query(..., description="开始时间"),
    end_time: str = Query(..., description="结束时间"),
    top: int = Query(10, description="Top数量")
):
    """
    获取报警记录Top排名统计数据
    
    Args:
        start_time: 开始时间
        end_time: 结束时间
        top: Top数量
    
    Returns:
        报警记录Top排名统计数据
    """
    try:
        # 复用V1控制器的逻辑
        from app.controllers.device_data import DeviceDataController
        controller = DeviceDataController()
        result = await controller.get_alarm_record_top(start_time, end_time, top)
        
        formatter = create_formatter(request)
        return formatter.success(data=result, message="获取报警记录Top排名统计数据成功")
        
    except Exception as e:
        logger.error(f"获取报警记录Top排名统计数据失败: {str(e)}", exc_info=True)
        formatter = create_formatter(request)
        return formatter.internal_error(f"获取报警记录Top排名统计数据失败: {str(e)}")


@router.get("/statistics/daily-report/summary", summary="获取焊机日报汇总")
async def get_welding_daily_report_summary(
    request: Request,
    report_date: str = Query(..., description="报告日期"),
    device_type: str = Query("welding", description="设备类型")
):
    """
    获取焊机日报汇总数据
    
    Args:
        report_date: 报告日期
        device_type: 设备类型
    
    Returns:
        焊机日报汇总数据
    """
    try:
        from app.controllers.welding_daily_report import WeldingDailyReportController
        from datetime import datetime
        
        # 验证设备类型
        if device_type != "welding":
            formatter = create_formatter(request)
            return formatter.error(
                message="设备类型必须为welding",
                code=400,
                error_type="ValidationError"
            )
        
        # 转换日期格式
        try:
            report_date_obj = datetime.strptime(report_date, "%Y-%m-%d").date()
        except ValueError:
            formatter = create_formatter(request)
            return formatter.error(
                message="日期格式错误，请使用YYYY-MM-DD格式",
                code=400,
                error_type="ValidationError"
            )
        
        # 使用正确的控制器
        controller = WeldingDailyReportController()
        result = await controller.get_daily_report_summary(report_date_obj)
        
        # 转换为字典格式
        if hasattr(result, 'model_dump'):
            summary_data = result.model_dump()
        elif hasattr(result, 'dict'):
            summary_data = result.dict()
        else:
            summary_data = {
                "total_duration": result.total_duration,
                "total_wire": result.total_wire,
                "total_gas": result.total_gas,
                "total_energy": result.total_energy
            }
        
        formatter = create_formatter(request)
        return formatter.success(data=summary_data, message="获取焊机日报汇总数据成功")
        
    except Exception as e:
        logger.error(f"获取焊机日报汇总数据失败: {str(e)}", exc_info=True)
        formatter = create_formatter(request)
        return formatter.internal_error(f"获取焊机日报汇总数据失败: {str(e)}")


@router.get("/statistics/daily-report/detail", summary="获取焊机日报详情")
async def get_welding_daily_report_detail(
    request: Request,
    report_date: str = Query(..., description="报告日期"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页数量"),
    prod_code: Optional[str] = Query(None, description="设备编码筛选"),
    device_type: str = Query("welding", description="设备类型")
):
    """
    获取焊机日报详情数据
    
    Args:
        report_date: 报告日期
        page: 页码
        page_size: 每页数量
        prod_code: 设备编码（可选）
        device_type: 设备类型
    
    Returns:
        焊机日报详情数据列表
    """
    try:
        from app.controllers.welding_daily_report import WeldingDailyReportController
        from datetime import datetime
        
        # 验证设备类型
        if device_type != "welding":
            formatter = create_formatter(request)
            return formatter.error(
                message="设备类型必须为welding",
                code=400,
                error_type="ValidationError"
            )
        
        # 转换日期格式
        try:
            report_date_obj = datetime.strptime(report_date, "%Y-%m-%d").date()
        except ValueError:
            formatter = create_formatter(request)
            return formatter.error(
                message="日期格式错误，请使用YYYY-MM-DD格式",
                code=400,
                error_type="ValidationError"
            )
        
        # 使用正确的控制器
        controller = WeldingDailyReportController()
        result = await controller.get_daily_report_detail(
            report_date=report_date_obj,
            page=page,
            page_size=page_size,
            prod_code=prod_code
        )
        
        # 转换为字典格式并直接返回数据数组
        if hasattr(result, 'model_dump'):
            detail_data = result.model_dump()
        elif hasattr(result, 'dict'):
            detail_data = result.dict()
        else:
            detail_data = {
                "data": [item.model_dump() if hasattr(item, 'model_dump') else item.dict() if hasattr(item, 'dict') else item for item in result.data],
                "total": result.total
            }
        
        # 提取数据数组和分页信息
        data_list = detail_data.get('data', [])
        total_count = detail_data.get('total', 0)
        
        formatter = create_formatter(request)
        # 使用V2标准的分页响应格式
        return formatter.paginated_success(
            data=data_list,
            total=total_count,
            page=page,
            page_size=page_size,
            message="获取焊机日报详情数据成功",
            resource_type="devices/statistics/daily-report/detail"
        )
        
    except Exception as e:
        logger.error(f"获取焊机日报详情数据失败: {str(e)}", exc_info=True)
        formatter = create_formatter(request)
        return formatter.internal_error(f"获取焊机日报详情数据失败: {str(e)}")


@router.get("/statistics/realtime/device-status", summary="获取设备实时状态统计")
async def get_realtime_device_status(
    request: Request,
    device_type: str = Query("welding", description="设备类型")
):
    """
    获取设备实时状态统计数据
    
    Args:
        device_type: 设备类型
    
    Returns:
        设备实时状态统计数据
    """
    try:
        # 复用V1控制器的逻辑
        from app.controllers.device_data import DeviceDataController
        controller = DeviceDataController()
        result = await controller.get_realtime_device_status(device_type)
        
        formatter = create_formatter(request)
        return formatter.success(data=result, message="获取设备实时状态统计数据成功")
        
    except Exception as e:
        logger.error(f"获取设备实时状态统计数据失败: {str(e)}", exc_info=True)
        formatter = create_formatter(request)
        return formatter.internal_error(f"获取设备实时状态统计数据失败: {str(e)}")


# 重复的函数定义已删除


@router.get("/{device_id}/status", summary="获取设备状态", response_model=None, dependencies=[DependAuth])
async def get_device_status(
    request: Request,
    device_id: int,
    current_user: User = DependAuth
):
    """
    获取设备状态信息
    
    - **device_id**: 设备ID
    """
    try:
        formatter = create_formatter(request)
        
        device_obj = await device_controller.get(id=device_id)
        if not device_obj:
            return formatter.not_found("设备不存在", "device")

        # 获取设备基本状态
        status_info = {
            "device_id": device_obj.id,
            "device_code": device_obj.device_code,
            "device_name": device_obj.device_name,
            "is_locked": device_obj.is_locked,
            "install_location": device_obj.install_location,
            "team_name": device_obj.team_name,
            "online_address": device_obj.online_address,
            "last_updated": device_obj.updated_at
        }

        return formatter.success(
            data=status_info,
            message="获取设备状态成功",
            resource_id=str(device_id),
            resource_type="devices"
        )

    except Exception as e:
        logger.error(f"获取设备状态失败: {str(e)}", exc_info=True)
        formatter = create_formatter(request)
        return formatter.internal_error(f"获取设备状态失败: {str(e)}")


@router.post("/{device_id}/toggle-lock", summary="切换设备锁定状态", response_model=None, dependencies=[DependAuth])
async def toggle_device_lock(
    request: Request,
    device_id: int,
    current_user: User = DependAuth
):
    """
    切换设备锁定状态
    
    - **device_id**: 设备ID
    """
    try:
        formatter = create_formatter(request)
        
        device_obj = await device_controller.toggle_device_lock(id=device_id)
        status = "锁定" if device_obj.is_locked else "解锁"
        
        return formatter.success(
            data={"is_locked": device_obj.is_locked},
            message=f"设备{status}成功",
            resource_id=str(device_id),
            resource_type="devices"
        )

    except HTTPException as e:
        formatter = create_formatter(request)
        if e.status_code == 404:
            return formatter.not_found(str(e.detail))
        else:
            return formatter.internal_error(str(e.detail))
    except Exception as e:
        logger.error(f"切换设备锁定状态失败: {str(e)}", exc_info=True)
        formatter = create_formatter(request)
        return formatter.internal_error(f"切换设备锁定状态失败: {str(e)}")


# 设备监控 API v2
# =====================================================

@router.get("/{device_id}/monitoring", summary="获取设备监控数据", response_model=None)
async def get_device_monitoring(
    request: Request,
    device_id: int,
    start_time: Optional[datetime] = Query(None, description="开始时间"),
    end_time: Optional[datetime] = Query(None, description="结束时间"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=2000, description="每页数量"),
    current_user: User = DependAuth
):
    """
    获取设备监控数据
    
    - **device_id**: 设备ID
    - **start_time**: 开始时间（可选）
    - **end_time**: 结束时间（可选）
    - **page**: 页码
    - **page_size**: 每页数量
    """
    try:
        formatter = create_formatter(request)
        
        # 检查设备是否存在
        device_obj = await device_controller.get(id=device_id)
        if not device_obj:
            return formatter.not_found("设备不存在", "device")

        # 使用 DeviceDataController 查询 TDengine 历史数据
        from app.controllers.device_data import DeviceDataController
        data_controller = DeviceDataController()
        
        # 调用 get_device_history_data (支持 device_id)
        total, history_data = await data_controller.get_device_history_data(
            device_id=device_id,
            device_code=device_obj.device_code, # 传入 device_code 以便查找表名
            start_time=start_time,
            end_time=end_time,
            page=page,
            page_size=page_size
        )
        
        # 转换为响应格式
        # 注意：TDengine 返回的数据字段已经是扁平的字典
        data = history_data

        # 构建查询参数
        query_params = {}
        if start_time:
            query_params['start_time'] = start_time.isoformat()
        if end_time:
            query_params['end_time'] = end_time.isoformat()

        return formatter.paginated_success(
            data=data,
            total=total,
            page=page,
            page_size=page_size,
            message="获取设备监控数据成功",
            resource_type=f"devices/{device_id}/monitoring",
            query_params=query_params
        )

    except Exception as e:
        logger.error(f"获取设备监控数据失败: {str(e)}", exc_info=True)
        formatter = create_formatter(request)
        return formatter.internal_error(f"获取设备监控数据失败: {str(e)}")


@router.get("/monitoring/realtime", summary="获取实时监控数据", response_model=None)
async def get_realtime_monitoring(
    request: Request,
    device_codes: Optional[str] = Query(None, description="设备编号列表，逗号分隔"),
    device_type: Optional[str] = Query(None, description="设备类型筛选"),
    status: Optional[str] = Query(None, description="设备状态筛选"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    current_user: User = DependAuth
):
    """
    获取实时监控数据
    
    - **device_codes**: 设备编号列表，逗号分隔（可选）
    - **device_type**: 设备类型筛选（可选）
    - **status**: 设备状态筛选（可选）
    - **page**: 页码
    - **page_size**: 每页数量
    """
    try:
        formatter = create_formatter(request)
        
        from app.models.device import DeviceRealTimeData
        
        # 构建查询条件
        query = DeviceRealTimeData.all().select_related('device')
        
        if device_codes:
            code_list = [code.strip() for code in device_codes.split(',')]
            query = query.filter(device__device_code__in=code_list)
        
        if device_type:
            query = query.filter(device__device_type=device_type)
        
        if status:
            query = query.filter(status=status)
        
        # 分页查询
        offset = (page - 1) * page_size
        monitoring_data = await query.offset(offset).limit(page_size).order_by('-data_timestamp')
        total = await query.count()
        
        # 转换为响应格式
        data = []
        for item in monitoring_data:
            device_info = await item.device
            # 从 metrics JSON 字段中提取数据，如果不存在则使用默认值
            metrics = item.metrics or {}
            data.append({
                "id": item.id,
                "device_id": item.device_id,
                "device_code": device_info.device_code,
                "device_name": device_info.device_name,
                "device_type": device_info.device_type,
                "voltage": metrics.get("voltage"),
                "current": metrics.get("current"),
                "power": metrics.get("power"),
                "temperature": metrics.get("temperature"),
                "pressure": metrics.get("pressure"),
                "vibration": metrics.get("vibration"),
                "status": item.status,
                "error_code": item.error_code,
                "error_message": item.error_message,
                "realtime_data": item.metrics,  # Add dynamic metrics
                "data_timestamp": item.data_timestamp.isoformat() if item.data_timestamp else None,
                "created_at": item.created_at.isoformat() if item.created_at else None
            })

        # 构建查询参数
        query_params = {}
        if device_codes:
            query_params['device_codes'] = device_codes
        if device_type:
            query_params['device_type'] = device_type
        if status:
            query_params['status'] = status

        return formatter.paginated_success(
            data=data,
            total=total,
            page=page,
            page_size=page_size,
            message="获取实时监控数据成功",
            resource_type="devices/monitoring/realtime",
            query_params=query_params
        )

    except Exception as e:
        logger.error(f"获取实时监控数据失败: {str(e)}", exc_info=True)
        formatter = create_formatter(request)
        return formatter.internal_error(f"获取实时监控数据失败: {str(e)}")


@router.get("/monitoring/summary", summary="获取监控数据汇总", response_model=None)
async def get_monitoring_summary(
    request: Request,
    device_type: Optional[str] = Query(None, description="设备类型筛选"),
    team_name: Optional[str] = Query(None, description="班组筛选"),
    current_user: User = DependAuth
):
    """
    获取监控数据汇总
    
    - **device_type**: 设备类型筛选（可选）
    - **team_name**: 班组筛选（可选）
    """
    try:
        formatter = create_formatter(request)
        
        from app.models.device import DeviceRealTimeData
        from tortoise.functions import Count
        
        # 构建设备查询条件
        device_query = DeviceInfo.all()
        if device_type:
            device_query = device_query.filter(device_type=device_type)
        if team_name:
            device_query = device_query.filter(team_name=team_name)
        
        devices = await device_query
        device_ids = [device.id for device in devices]
        
        if not device_ids:
            return formatter.success(
                data={
                    "total_devices": 0,
                    "online_devices": 0,
                    "offline_devices": 0,
                    "error_devices": 0,
                    "maintenance_devices": 0,
                    "status_distribution": {}
                },
                message="获取监控数据汇总成功"
            )
        
        # 获取最新状态统计
        from tortoise.query_utils import Q
        
        # 统计各状态设备数量
        online_count = await DeviceRealTimeData.filter(
            device_id__in=device_ids, status="online"
        ).distinct().count()
        
        offline_count = await DeviceRealTimeData.filter(
            device_id__in=device_ids, status="offline"
        ).distinct().count()
        
        error_count = await DeviceRealTimeData.filter(
            device_id__in=device_ids, status="error"
        ).distinct().count()
        
        maintenance_count = await DeviceRealTimeData.filter(
            device_id__in=device_ids, status="maintenance"
        ).distinct().count()
        
        # 构建汇总数据
        summary = {
            "total_devices": len(device_ids),
            "online_devices": online_count,
            "offline_devices": offline_count,
            "error_devices": error_count,
            "maintenance_devices": maintenance_count,
            "status_distribution": {
                "online": online_count,
                "offline": offline_count,
                "error": error_count,
                "maintenance": maintenance_count
            }
        }

        return formatter.success(
            data=summary,
            message="获取监控数据汇总成功",
            resource_type="devices/monitoring"
        )

    except Exception as e:
        logger.error(f"获取监控数据汇总失败: {str(e)}", exc_info=True)
        formatter = create_formatter(request)
        return formatter.internal_error(f"获取监控数据汇总失败: {str(e)}")


# =====================================================
# 设备字段管理 API v2
# =====================================================

@router.get("/types/{type_code}/fields", summary="获取设备类型字段列表", response_model=None)
async def get_device_type_fields(
    request: Request,
    type_code: str,
    current_user: User = DependAuth
):
    """
    获取指定设备类型的字段定义列表
    
    - **type_code**: 设备类型编码
    """
    try:
        formatter = create_formatter(request)
        
        # 检查设备类型是否存在
        if not await DeviceType.filter(type_code=type_code).exists():
            return formatter.not_found(f"设备类型 {type_code} 不存在", "device_type")
        
        # 获取字段列表
        fields = await DeviceField.filter(device_type_code=type_code).order_by('sort_order', 'field_name')
        
        result = []
        for field in fields:
            field_data = {
                "id": field.id,
                "device_type_code": field.device_type_code,
                "field_name": field.field_name,
                "field_type": field.field_type,
                "field_description": field.field_description,
                "is_required": field.is_required,
                "is_tag": field.is_tag,
                "sort_order": field.sort_order,
                "created_at": field.created_at.isoformat() if field.created_at else None,
                "updated_at": field.updated_at.isoformat() if field.updated_at else None
            }
            result.append(field_data)
        
        return formatter.success(
            data=result,
            message="获取设备字段列表成功",
            resource_type=f"devices/types/{type_code}/fields"
        )

    except Exception as e:
        logger.error(f"获取设备字段列表失败: {str(e)}", exc_info=True)
        formatter = create_formatter(request)
        return formatter.internal_error(f"获取设备字段列表失败: {str(e)}")


@router.post("/types/{type_code}/fields", summary="添加设备字段", response_model=None)
async def create_device_field(
    request: Request,
    type_code: str,
    field_data: DeviceFieldCreate,
    current_user: User = DependAuth
):
    """
    为指定设备类型添加字段定义
    
    - **type_code**: 设备类型编码
    - **field_name**: 字段名称
    - **field_type**: 字段类型
    - **field_description**: 字段描述（可选）
    - **is_required**: 是否必填（默认false）
    - **is_tag**: 是否为标签字段（默认false）
    - **sort_order**: 排序顺序（默认0）
    """
    try:
        formatter = create_formatter(request)
        
        # 检查设备类型是否存在
        if not await DeviceType.filter(type_code=type_code).exists():
            return formatter.not_found(f"设备类型 {type_code} 不存在", "device_type")
        
        # 检查字段是否已存在
        if await DeviceField.filter(device_type_code=type_code, field_name=field_data.field_name).exists():
            return formatter.error(
                f"字段 {field_data.field_name} 已存在",
                code=400,
                error_type="ValidationError"
            )
        
        # 创建字段
        field_dict = field_data.model_dump()
        field_dict["device_type_code"] = type_code
        field = await DeviceField.create(**field_dict)
        
        return formatter.success(
            data={"id": field.id, "field_name": field.field_name},
            message="设备字段创建成功",
            code=201,
            resource_id=str(field.id),
            resource_type=f"devices/types/{type_code}/fields"
        )

    except Exception as e:
        logger.error(f"创建设备字段失败: {str(e)}", exc_info=True)
        formatter = create_formatter(request)
        return formatter.internal_error(f"创建设备字段失败: {str(e)}")


@router.put("/types/{type_code}/fields/{field_id}", summary="更新设备字段", response_model=None)
async def update_device_field(
    request: Request,
    type_code: str,
    field_id: int,
    field_data: DeviceFieldUpdate,
    current_user: User = DependAuth
):
    """
    更新设备字段定义
    
    - **type_code**: 设备类型编码
    - **field_id**: 字段ID
    - 其他字段与创建设备字段相同，均为可选
    """
    try:
        formatter = create_formatter(request)
        
        # 获取字段
        try:
            field = await DeviceField.get(id=field_id, device_type_code=type_code)
        except DoesNotExist:
            return formatter.not_found("字段不存在", "device_field")
        
        # 更新字段
        update_data = field_data.model_dump(exclude_unset=True)
        if update_data:
            await field.update_from_dict(update_data)
            await field.save()
        
        return formatter.success(
            message="设备字段更新成功",
            resource_id=str(field_id),
            resource_type=f"devices/types/{type_code}/fields"
        )

    except Exception as e:
        logger.error(f"更新设备字段失败: {str(e)}", exc_info=True)
        formatter = create_formatter(request)
        return formatter.internal_error(f"更新设备字段失败: {str(e)}")


@router.delete("/types/{type_code}/fields/{field_id}", summary="删除设备字段", response_model=None)
async def delete_device_field(
    request: Request,
    type_code: str,
    field_id: int,
    current_user: User = DependAuth
):
    """
    删除设备字段定义
    
    - **type_code**: 设备类型编码
    - **field_id**: 字段ID
    """
    try:
        formatter = create_formatter(request)
        
        # 获取字段
        try:
            field = await DeviceField.get(id=field_id, device_type_code=type_code)
        except DoesNotExist:
            return formatter.not_found("字段不存在", "device_field")
        
        # 删除字段
        await field.delete()
        
        return formatter.success(
            message="设备字段删除成功",
            resource_type=f"devices/types/{type_code}/fields"
        )

    except Exception as e:
        logger.error(f"删除设备字段失败: {str(e)}", exc_info=True)
        formatter = create_formatter(request)
        return formatter.internal_error(f"删除设备字段失败: {str(e)}")
# =====================================================
# 设备维护管理 API v2
# =====================================================

@router.get("/maintenance/records", summary="获取设备维护记录列表", response_model=None)
async def get_maintenance_records(
    request: Request,
    device_id: Optional[int] = Query(None, description="设备ID筛选"),
    device_code: Optional[str] = Query(None, description="设备编号筛选"),
    maintenance_type: Optional[str] = Query(None, description="维护类型筛选"),
    maintenance_status: Optional[str] = Query(None, description="维护状态筛选"),
    priority: Optional[str] = Query(None, description="优先级筛选"),
    assigned_to: Optional[str] = Query(None, description="负责人筛选"),
    maintenance_team: Optional[str] = Query(None, description="维护团队筛选"),
    start_time: Optional[datetime] = Query(None, description="开始时间筛选"),
    end_time: Optional[datetime] = Query(None, description="结束时间筛选"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    current_user: User = DependAuth
):
    """
    获取设备维护记录列表
    
    - **device_id**: 设备ID筛选（可选）
    - **device_code**: 设备编号筛选（可选）
    - **maintenance_type**: 维护类型筛选（可选）
    - **maintenance_status**: 维护状态筛选（可选）
    - **priority**: 优先级筛选（可选）
    - **assigned_to**: 负责人筛选（可选）
    - **maintenance_team**: 维护团队筛选（可选）
    - **start_time**: 开始时间筛选（可选）
    - **end_time**: 结束时间筛选（可选）
    - **page**: 页码
    - **page_size**: 每页数量
    """
    try:
        formatter = create_formatter(request)
        
        from app.models.device import DeviceMaintenanceRecord
        
        # 构建查询条件
        query = DeviceMaintenanceRecord.all()
        
        # 应用筛选条件
        if device_id:
            query = query.filter(device_id=device_id)
        if device_code:
            query = query.filter(device_code__icontains=device_code)
        if maintenance_type:
            query = query.filter(maintenance_type=maintenance_type)
        if maintenance_status:
            query = query.filter(maintenance_status=maintenance_status)
        if priority:
            query = query.filter(priority=priority)
        if assigned_to:
            query = query.filter(assigned_to__icontains=assigned_to)
        if start_date:
            query = query.filter(created_at__gte=start_date)
        if end_date:
            query = query.filter(created_at__lte=end_date)
        
        # 获取总数
        total = await query.count()
        
        # 应用分页
        offset = (page - 1) * page_size
        records = await query.offset(offset).limit(page_size).order_by('-created_at')
        
        # 构建响应数据
        data = []
        for record in records:
            data.append({
                "id": record.id,
                "device_id": record.device_id,
                "device_code": record.device_code,
                "maintenance_type": record.maintenance_type,
                "maintenance_status": record.maintenance_status,
                "priority": record.priority,
                "assigned_to": record.assigned_to,
                "description": record.description,
                "scheduled_date": record.scheduled_date.isoformat() if record.scheduled_date else None,
                "completed_date": record.completed_date.isoformat() if record.completed_date else None,
                "created_at": record.created_at.isoformat(),
                "updated_at": record.updated_at.isoformat()
            })
        
        return formatter.success(
            data=data,
            meta={
                "total": total,
                "page": page,
                "pageSize": page_size,
                "hasNext": offset + page_size < total,
                "hasPrev": page > 1
            },
            message="获取设备维护记录列表成功",
            resource_type="devices/maintenance/records"
        )

    except Exception as e:
        logger.error(f"获取设备维护记录列表失败: {str(e)}", exc_info=True)
        formatter = create_formatter(request)
        return formatter.internal_error(f"获取设备维护记录列表失败: {str(e)}")


# =====================================================
# 设备字段管理 API v2
# =====================================================

@router.get("/types/{type_code}/fields", summary="获取设备类型字段列表", response_model=None)
async def get_device_type_fields(
    request: Request,
    type_code: str,
    current_user: User = DependAuth
):
    """
    获取指定设备类型的字段定义列表
    
    - **type_code**: 设备类型编码
    """
    try:
        formatter = create_formatter(request)
        
        # 检查设备类型是否存在
        if not await DeviceType.filter(type_code=type_code).exists():
            return formatter.not_found(f"设备类型 {type_code} 不存在", "device_type")
        
        # 获取字段列表
        fields = await DeviceField.filter(device_type_code=type_code).order_by('sort_order', 'field_name')
        
        result = []
        for field in fields:
            field_data = {
                "id": field.id,
                "device_type_code": field.device_type_code,
                "field_name": field.field_name,
                "field_type": field.field_type,
                "field_description": field.field_description,
                "is_required": field.is_required,
                "is_tag": field.is_tag,
                "sort_order": field.sort_order,
                "created_at": field.created_at.isoformat() if field.created_at else None,
                "updated_at": field.updated_at.isoformat() if field.updated_at else None
            }
            result.append(field_data)
        
        return formatter.success(
            data=result,
            message="获取设备字段列表成功",
            resource_type="devices/types/fields"
        )

    except Exception as e:
        logger.error(f"获取设备字段列表失败: {str(e)}", exc_info=True)
        formatter = create_formatter(request)
        return formatter.internal_error(f"获取设备字段列表失败: {str(e)}")


# =====================================================
# 设备监控 API v2
# =====================================================

@router.get("/{device_id}/realtime", summary="获取设备实时数据", response_model=None)
async def get_device_realtime_data(
    request: Request,
    device_id: int,
    current_user: User = DependAuth
):
    """
    获取设备实时数据
    
    - **device_id**: 设备ID
    """
    try:
        formatter = create_formatter(request)
        
        # 检查设备是否存在
        device_obj = await device_controller.get(id=device_id)
        if not device_obj:
            return formatter.not_found("设备不存在", "device")

        # 获取最新的实时数据
        from app.models.device import DeviceRealTimeData
        realtime_data = await DeviceRealTimeData.filter(device_id=device_id).order_by('-data_timestamp').first()
        
        if not realtime_data:
            # 如果没有实时数据，返回设备基本信息
            result = {
                "device_id": device_obj.id,
                "device_code": device_obj.device_code,
                "device_name": device_obj.device_name,
                "status": "offline",
                "message": "暂无实时数据"
            }
        else:
            # 转换实时数据
            # 从 metrics JSON 字段中提取数据，如果不存在则使用默认值
            metrics = realtime_data.metrics or {}
            
            result = {
                "device_id": realtime_data.device_id,
                "device_code": device_obj.device_code,
                "device_name": device_obj.device_name,
                "voltage": metrics.get("voltage"),
                "current": metrics.get("current"),
                "power": metrics.get("power"),
                "temperature": metrics.get("temperature"),
                "pressure": metrics.get("pressure"),
                "vibration": metrics.get("vibration"),
                "status": realtime_data.status,
                "error_code": realtime_data.error_code,
                "error_message": realtime_data.error_message,
                "data_timestamp": realtime_data.data_timestamp.isoformat() if realtime_data.data_timestamp else None
            }

        return formatter.success(
            data=result,
            message="获取设备实时数据成功",
            resource_id=str(device_id),
            resource_type="devices"
        )

    except Exception as e:
        logger.error(f"获取设备实时数据失败: {str(e)}", exc_info=True)
        formatter = create_formatter(request)
        return formatter.internal_error(f"获取设备实时数据失败: {str(e)}")


@router.get("/{device_id}/history", summary="获取设备历史数据", response_model=None)
async def get_device_history_data(
    request: Request,
    device_id: int,
    start_time: Optional[datetime] = Query(None, description="开始时间"),
    end_time: Optional[datetime] = Query(None, description="结束时间"),
    status: Optional[str] = Query(None, description="设备状态筛选"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=10000, description="每页数量"),
    current_user: User = DependAuth
):
    """
    获取设备历史数据（从TDengine查询）
    
    - **device_id**: 设备ID
    - **start_time**: 开始时间（可选）
    - **end_time**: 结束时间（可选）
    - **status**: 设备状态筛选（可选）
    - **page**: 页码
    - **page_size**: 每页数量（图表模式可以设置为10000获取所有数据）
    """
    logger.info(f"🔍 [历史数据API] 收到请求: device_id={device_id}, start_time={start_time}, end_time={end_time}, page={page}, page_size={page_size}")
    try:
        formatter = create_formatter(request)
        
        # 检查设备是否存在并获取device_code
        device_obj = await device_controller.get(id=device_id)
        if not device_obj:
            return formatter.not_found("设备不存在", "device")

        device_code = device_obj.device_code
        logger.info(f"查询设备历史数据: device_id={device_id}, device_code={device_code}, start_time={start_time}, end_time={end_time}, page={page}, page_size={page_size}")

        # 调用控制器方法从TDengine查询历史数据
        from app.controllers.device_data import device_data_controller
        
        total, history_data = await device_data_controller.get_device_history_data(
            device_id=device_id,
            device_code=device_code,
            start_time=start_time,
            end_time=end_time,
            status=status,
            page=page,
            page_size=page_size
        )
        
        logger.info(f"查询到 {len(history_data)} 条历史数据，总数: {total}")

        # 构建查询参数
        query_params = {}
        if start_time:
            query_params['start_time'] = start_time.isoformat()
        if end_time:
            query_params['end_time'] = end_time.isoformat()
        if status:
            query_params['status'] = status

        return formatter.paginated_success(
            data=history_data,
            total=total,
            page=page,
            page_size=page_size,
            message="获取设备历史数据成功",
            resource_type=f"devices/{device_id}/history",
            query_params=query_params
        )

    except Exception as e:
        logger.error(f"获取设备历史数据失败: {str(e)}", exc_info=True)
        formatter = create_formatter(request)
        return formatter.internal_error(f"获取设备历史数据失败: {str(e)}")


@router.get("/monitoring/overview", summary="设备监控概览", response_model=None)
async def get_monitoring_overview(
    request: Request,
    device_type: Optional[str] = Query(None, description="设备类型筛选"),
    team_name: Optional[str] = Query(None, description="班组筛选"),
    current_user: User = DependAuth
):
    """
    获取设备监控概览信息
    
    - **device_type**: 设备类型筛选（可选）
    - **team_name**: 班组筛选（可选）
    """
    try:
        formatter = create_formatter(request)
        
        # 构建设备查询条件
        device_query = DeviceInfo.all()
        if device_type:
            device_query = device_query.filter(device_type=device_type)
        if team_name:
            device_query = device_query.filter(team_name=team_name)

        # 获取设备总数
        total_devices = await device_query.count()
        
        # 获取锁定设备数
        locked_devices = await device_query.filter(is_locked=True).count()
        
        # 获取在线设备数（通过实时数据表统计）
        from app.models.device import DeviceRealTimeData
        from datetime import datetime, timedelta
        
        # 最近5分钟有数据的设备视为在线
        recent_time = datetime.now() - timedelta(minutes=5)
        online_devices_query = DeviceRealTimeData.filter(
            data_timestamp__gte=recent_time,
            status="online"
        )
        
        if device_type or team_name:
            # 需要关联设备表进行筛选
            device_ids = await device_query.values_list('id', flat=True)
            online_devices_query = online_devices_query.filter(device_id__in=device_ids)
        
        online_devices = await online_devices_query.distinct().count()
        offline_devices = total_devices - online_devices
        
        # 按状态统计
        status_stats = {
            "total": total_devices,
            "online": online_devices,
            "offline": offline_devices,
            "locked": locked_devices,
            "unlocked": total_devices - locked_devices
        }
        
        # 按类型统计（如果没有指定类型筛选）
        type_stats = []
        if not device_type:
            type_data = await device_controller.get_type_statistics()
            type_stats = type_data
        
        # 按班组统计（如果没有指定班组筛选）
        team_stats = []
        if not team_name:
            team_data = await device_controller.get_team_statistics()
            team_stats = team_data

        result = {
            "status_statistics": status_stats,
            "type_statistics": type_stats,
            "team_statistics": team_stats,
            "last_updated": datetime.now().isoformat()
        }

        return formatter.success(
            data=result,
            message="获取设备监控概览成功",
            resource_type="devices/monitoring"
        )

    except Exception as e:
        logger.error(f"获取设备监控概览失败: {str(e)}", exc_info=True)
        formatter = create_formatter(request)
        return formatter.internal_error(f"获取设备监控概览失败: {str(e)}")





@router.get("/statistics/use-record/list", summary="获取设备使用记录列表", response_model=None)
async def get_device_use_records(
    request: Request,
    device_code: Optional[str] = Query(None, description="设备编号筛选"),
    device_type: Optional[str] = Query("welding", description="设备类型"),
    start_time: str = Query(..., description="开始时间 (YYYY-MM-DD HH:mm:ss)"),
    end_time: str = Query(..., description="结束时间 (YYYY-MM-DD HH:mm:ss)"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页数量"),
    current_user: User = DependAuth
):
    """
    获取设备使用记录列表（焊接记录）
    
    - **device_code**: 设备编号筛选（可选）
    - **device_type**: 设备类型（默认welding）
    - **start_time**: 开始时间
    - **end_time**: 结束时间
    - **page**: 页码
    - **page_size**: 每页数量
    """
    try:
        formatter = create_formatter(request)
        
        # 导入TDengine连接器
        from app.core.tdengine_connector import TDengineConnector
        from app.core.dependency import get_tdengine_connector
        from datetime import datetime
        
        # 获取TDengine连接器
        td_connector = await get_tdengine_connector()
        
        # 添加调试日志
        logger.info(f"接收到的查询参数: device_code={device_code}, start_time={start_time}, end_time={end_time}, page={page}, page_size={page_size}")
        
        # 构建子表名
        if device_code:
            sub_table_name = f"record_{device_code}"
        else:
            # 没有指定设备编号时，查询超级表
            sub_table_name = "welding_record_his"

        # 构建查询SQL
        start_dt = datetime.strptime(start_time, '%Y-%m-%d %H:%M:%S')
        end_dt = datetime.strptime(end_time, '%Y-%m-%d %H:%M:%S')

        if start_dt > end_dt:
            return formatter.error(
                message="开始时间不能晚于结束时间",
                code=400,
                error_type="ValidationError"
            )

        # TDengine时间格式：使用毫秒精度（.000后缀）
        start_time_str = start_dt.strftime('%Y-%m-%d %H:%M:%S') + '.000'
        end_time_str = end_dt.strftime('%Y-%m-%d %H:%M:%S') + '.999'  # 结束时间用.999确保包含当秒内的所有数据
        
        logger.info(f"时间范围转换: {start_time} -> {start_time_str}, {end_time} -> {end_time_str}")

        # 步骤1：先查询总数（优化：只查COUNT，不获取数据）
        count_sql = f"SELECT COUNT(*) as total FROM hlzg_db.{sub_table_name} WHERE ts >= '{start_time_str}' AND ts <= '{end_time_str}'"
        if device_code:
            count_sql += f" AND device_code = '{device_code}'"
        
        logger.info(f"执行COUNT查询: {count_sql}")
        count_result = await td_connector.query_data(count_sql, db_name="hlzg_db")
        
        # 获取总数
        total = 0
        if count_result and isinstance(count_result, dict) and "data" in count_result and count_result["data"]:
            total = count_result["data"][0][0] if count_result["data"][0] else 0
        
        logger.info(f"总记录数: {total}")
        
        # 步骤2：使用数据库级分页查询（LIMIT + OFFSET）
        offset = (page - 1) * page_size
        sql = f"SELECT device_code, ts, weld_end_time, team_name, shift_name, spec_match_rate, avg_current, avg_voltage, operator_name, workpiece_code, wire_consumption, duration_sec, operator_card_id, operator_code FROM hlzg_db.{sub_table_name} WHERE ts >= '{start_time_str}' AND ts <= '{end_time_str}'"
        if device_code:
            sql += f" AND device_code = '{device_code}'"
        sql += f" ORDER BY ts DESC LIMIT {page_size} OFFSET {offset}"
        
        # 添加SQL日志
        logger.info(f"执行分页查询SQL: {sql}")

        # 执行查询（只查询当前页的数据）
        result = await td_connector.query_data(sql, db_name="hlzg_db")
        logger.info(f"TDengine返回数据行数: {len(result.get('data', [])) if isinstance(result, dict) else 0}")
        
        # 提取数据
        data = []
        logger.info(f"TDengine query result type: {type(result)}")
        logger.info(f"TDengine query result keys: {result.keys() if isinstance(result, dict) else 'N/A'}")
        
        if result and isinstance(result, dict):
            # 检查TDengine返回的状态码
            status_code = result.get("code", 0)
            if status_code != 0:
                error_msg = result.get("desc", "Unknown error")
                logger.error(f"TDengine查询失败: code={status_code}, desc={error_msg}")
                return formatter.error(
                    message=f"TDengine查询失败: {error_msg}",
                    code=500
                )
            
            # 确保 result 是字典，并且包含 'data' 键
            if "data" in result and isinstance(result["data"], list):
                logger.info(f"TDengine返回数据行数: {len(result['data'])}")
                # 获取列名
                columns = [col[0] for col in result.get("column_meta", [])] if isinstance(result.get("column_meta"), list) else []
                logger.info(f"列名: {columns}")
                
                for row in result["data"]:
                    row_dict = dict(zip(columns, row))
                    # 格式化时间戳（TDengine可能返回字符串或时间戳）
                    if 'ts' in row_dict:
                        if isinstance(row_dict['ts'], int):
                            row_dict['ts'] = datetime.fromtimestamp(row_dict['ts'] / 1000).isoformat()
                        elif isinstance(row_dict['ts'], str):
                            # 如果已经是字符串，保持原样
                            pass
                    
                    if 'weld_end_time' in row_dict:
                        if isinstance(row_dict['weld_end_time'], int):
                            row_dict['weld_end_time'] = datetime.fromtimestamp(row_dict['weld_end_time'] / 1000).isoformat()
                        elif isinstance(row_dict['weld_end_time'], str):
                            pass

                    data.append(row_dict)
                
                logger.info(f"成功解析数据: {len(data)} 条")
            else:
                logger.warning(f"TDengine query result does not contain 'data' key or 'data' is not a list. Keys: {result.keys()}")
        else:
            logger.warning(f"TDengine query result is not a dictionary or is empty. Type: {type(result)}")

        # 数据已经通过数据库分页，直接使用
        paginated_data = data

        # 构建查询参数
        query_params = {
            "device_code": device_code,
            "device_type": device_type,
            "start_time": start_time,
            "end_time": end_time
        }

        return formatter.paginated_success(
            data=paginated_data,
            total=total,
            page=page,
            page_size=page_size,
            message="获取设备使用记录成功",
            resource_type="devices/statistics/use-record",
            query_params=query_params
        )

    except Exception as e:
        logger.error(f"获取设备使用记录失败: {str(e)}", exc_info=True)
        formatter = create_formatter(request)
        return formatter.internal_error(f"获取设备使用记录失败: {str(e)}")


# =====================================================
# 焊机日报统计 API v2 (重复定义已删除)
# =====================================================


# 重复的daily-report detail API定义已删除


# =====================================================
# WebSocket 实时数据推送 API v2
# =====================================================

async def websocket_auth_v2(token: Optional[str]) -> tuple[Optional[User], Optional[str]]:
    """WebSocket认证函数 V2版本，返回(用户对象, 错误信息)"""
    logger.debug(f"WebSocket V2认证开始，token: {token[:50] if token else 'None'}...")

    if not token:
        logger.debug("认证失败：缺少token")
        return None, "Missing authentication token"

    try:
        if token == "dev":
            logger.debug("使用开发模式认证")
            user = await User.filter().first()
        else:
            logger.debug(f"开始解码JWT token...")
            from app.settings import settings
            decode_data = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
            logger.debug(f"JWT解码成功，数据: {decode_data}")
            user_id = decode_data.get("user_id")
            logger.debug(f"查找用户ID: {user_id}")
            user = await User.filter(id=user_id).first()

        if not user:
            logger.debug("认证失败：用户不存在")
            return None, "Authentication failed"

        logger.debug(f"认证成功，用户: {user.username}")
        return user, None
    except jwt.DecodeError as e:
        logger.debug(f"JWT解码错误: {str(e)}")
        return None, "无效的Token"
    except jwt.ExpiredSignatureError as e:
        logger.debug(f"JWT过期错误: {str(e)}")
        return None, "登录已过期"
    except Exception as e:
        logger.debug(f"认证异常: {repr(e)}")
        return None, f"认证异常: {repr(e)}"


class ConnectionManagerV2:
    """WebSocket连接管理器 V2版本"""

    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.device_subscriptions: dict = {}

    async def connect(
        self,
        websocket: WebSocket,
        device_code: Optional[str] = None,
        device_codes: Optional[List[str]] = None,
        type_code: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ):
        """建立WebSocket连接"""
        await websocket.accept()
        self.active_connections.append(websocket)

        # 创建设备查询参数
        from app.schemas.devices import DeviceRealtimeQuery
        
        # 如果没有指定type_code，默认使用welding（焊接设备）
        # 不要使用"all"，因为这会查询所有设备类型，造成性能问题
        effective_type_code = type_code or "welding"
        
        query = DeviceRealtimeQuery(
            device_code=device_code,
            device_codes=device_codes,
            type_code=effective_type_code,
            page=page,
            page_size=page_size,
            paged=True,  # 启用分页查询
        )
        
        logger.info(f"WebSocket订阅参数: type_code={effective_type_code}, page={page}, page_size={page_size}, device_codes={device_codes}")

        self.device_subscriptions[websocket] = {
            "device_code": device_code,
            "device_codes": device_codes,
            "type_code": type_code,
            "query": query,
        }

        device_info = (
            device_code or f"{len(device_codes) if device_codes else 0}个指定设备" if device_codes else "全部设备"
        )
        logger.info(f"WebSocket V2连接已建立，设备类型: {type_code or 'welding'}，设备编号: {device_info}")

    def disconnect(self, websocket: WebSocket):
        """断开WebSocket连接"""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        
        type_code = None
        device_info = "未知"
        
        if websocket in self.device_subscriptions:
            subscription = self.device_subscriptions[websocket]
            type_code = subscription.get("type_code")
            device_code = subscription.get("device_code")
            device_codes = subscription.get("device_codes")
            device_info = (
                device_code or f"{len(device_codes) if device_codes else 0}个指定设备" if device_codes else "全部设备"
            )
            del self.device_subscriptions[websocket]

        logger.info(f"WebSocket V2连接已断开，设备类型: {type_code or 'welding'}，设备编号: {device_info}")

    async def send_personal_message(self, message: str, websocket: WebSocket):
        """发送个人消息"""
        try:
            await websocket.send_text(message)
        except Exception as e:
            logger.error(f"发送WebSocket V2消息失败: {str(e)}")
            self.disconnect(websocket)


# 全局连接管理器实例
manager_v2 = ConnectionManagerV2()


@router.websocket("/realtime-data/ws")
async def websocket_realtime_data_v2(
    websocket: WebSocket,
    device_code: Optional[str] = Query(None, description="设备编号，不提供则订阅所有设备"),
    device_codes: Optional[str] = Query(None, description="设备编号列表，逗号分隔，用于订阅指定设备"),
    type_code: Optional[str] = Query(None, description="设备类型代码，不提供则默认为焊接设备"),
    page: int = Query(1, description="页码", ge=1),
    page_size: int = Query(20, description="每页数量", ge=1, le=100),
    token: Optional[str] = Query(None, description="JWT认证token"),
):
    """WebSocket实时数据推送端点 V2版本"""
    # 先进行认证
    user, auth_error = await websocket_auth_v2(token)
    if auth_error:
        logger.error(f"WebSocket V2认证失败: {auth_error}")
        await websocket.close(code=1008, reason=f"Authentication failed: {auth_error}")
        return

    logger.info(f"WebSocket V2认证成功，用户: {user.username}")

    # 处理device_codes参数（从逗号分隔的字符串转换为列表）
    device_codes_list = None
    if device_codes:
        device_codes_list = [code.strip() for code in device_codes.split(",") if code.strip()]
        if len(device_codes_list) > 100:  # 限制最大设备数量
            await websocket.close(code=1008, reason="设备数量超过限制（最大100个）")
            return

    await manager_v2.connect(websocket, device_code, device_codes_list, type_code, page, page_size)
    
    # 初始化复用的TDengine连接器
    from app.settings.config import TDengineCredentials
    from app.core.tdengine_connector import TDengineConnector
    
    td_connector = None
    try:
        tdengine_creds = TDengineCredentials()
        td_connector = TDengineConnector(
            host=tdengine_creds.host,
            port=tdengine_creds.port,
            user=tdengine_creds.user,
            password=tdengine_creds.password,
            database=tdengine_creds.database,
        )
        logger.info("WebSocket V2: TDengine连接器初始化完成 (复用模式)")
    except Exception as e:
        logger.error(f"WebSocket V2: TDengine连接器初始化失败: {e}")
        await websocket.close(code=1011, reason="Database connection failed")
        return

    try:
        # 立即推送一次初始数据
        first_push = True
        
        while True:
            try:
                # 获取订阅信息
                subscription = manager_v2.device_subscriptions.get(websocket)
                if not subscription:
                    break

                query = subscription["query"]

                # 确保type_code参数正确传递
                # 如果没有指定具体的设备编码，获取该类型的所有设备（但限制在指定类型内）
                if not query.device_code and not query.device_codes:
                    # 使用分页查询，避免一次性获取过多数据
                    # ⚠️ 不要覆盖query.page，它已经在连接时由用户指定
                    # query.page = 1  # ❌ 不要强制设置为1
                    # 注意：query.type_code 和 query.page 应该已经在连接时设置好了
                    logger.debug(f"WebSocket查询参数: type_code={query.type_code}, page={query.page}, page_size={query.page_size}")

                # 获取设备实时数据
                from app.controllers.device_data import DeviceDataController
                controller = DeviceDataController()
                
                try:
                    # 传入复用的连接器
                    result = await controller.get_device_realtime_data(query, td_connector=td_connector)
                    
                    # 检查是否有错误信息
                    if isinstance(result, dict) and "error" in result:
                        # 发送错误消息，但不关闭连接
                        logger.warning(f"查询返回错误: {result.get('error')}")
                        error_message = json.dumps(
                            {
                                "type": "error",
                                "timestamp": datetime.now().isoformat(),
                                "message": result.get("error"),
                                "data": result,
                                "version": "v2"
                            },
                            ensure_ascii=False,
                        )
                        await manager_v2.send_personal_message(error_message, websocket)
                    else:
                        # 发送正常数据（使用V2格式，包含分页信息）
                        message = json.dumps(
                            {
                                "type": "realtime_data",
                                "timestamp": datetime.now().isoformat(),
                                "device_type": subscription.get("type_code", "welding"),
                                "data": {
                                    "items": result.get("items", []),
                                    "total": result.get("total", 0),
                                    "page": query.page,
                                    "page_size": query.page_size,
                                },
                                "version": "v2",  # 标识V2版本
                            },
                            ensure_ascii=False,
                            default=str,
                        )
                        await manager_v2.send_personal_message(message, websocket)

                    # 第一次推送后立即进入正常循环
                    if first_push:
                        first_push = False
                        logger.info(f"WebSocket V2初始数据已推送，设备类型: {subscription.get('type_code', 'welding')}")
                    
                except HTTPException as http_ex:
                    # 捕获HTTP异常，发送错误消息而不关闭连接
                    logger.error(f"WebSocket查询数据失败(HTTP): {http_ex.detail}")
                    error_message = json.dumps(
                        {
                            "type": "error",
                            "timestamp": datetime.now().isoformat(),
                            "message": str(http_ex.detail),
                            "code": http_ex.status_code,
                            "version": "v2"
                        },
                        ensure_ascii=False,
                    )
                    await manager_v2.send_personal_message(error_message, websocket)
                
                # 缩短轮询间隔以实现实时性 (原为60s，改为3s)
                await asyncio.sleep(3)

            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"WebSocket V2数据推送错误: {str(e)}", exc_info=True)
                error_message = json.dumps(
                    {
                        "type": "error", 
                        "timestamp": datetime.now().isoformat(), 
                        "message": f"数据获取失败: {str(e)}",
                        "version": "v2"
                    },
                    ensure_ascii=False,
                )
                await manager_v2.send_personal_message(error_message, websocket)
                await asyncio.sleep(5)  # 错误后等待5秒再重试

    except WebSocketDisconnect:
        pass
    finally:
        if td_connector:
            await td_connector.close()
            logger.info("WebSocket V2: TDengine连接器已关闭")
        manager_v2.disconnect(websocket)