#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
设备维护管理 API v2
实现设备维护记录、维护计划、维护提醒等功能的RESTful API
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

from fastapi import APIRouter, Query, Body, HTTPException, Request, Depends
from tortoise.expressions import Q
from tortoise.exceptions import DoesNotExist
from tortoise.transactions import in_transaction
from tortoise.functions import Count

from app.controllers.device import device_controller
from app.core.dependency import DependAuth
from app.core.response_formatter_v2 import ResponseFormatterV2, create_formatter
from app.models.admin import User
from app.schemas.devices import (
    DeviceMaintenanceRecordCreate,
    DeviceMaintenanceRecordUpdate,
    DeviceMaintenanceRecordResponse,
    DeviceMaintenancePlanCreate,
    DeviceMaintenancePlanUpdate,
    DeviceMaintenancePlanResponse,
    DeviceMaintenanceReminderResponse,
    DeviceMaintenanceQuery,
    DeviceMaintenanceStatistics
)
from app.models.device import (
    DeviceInfo,
    DeviceMaintenanceRecord,
    DeviceMaintenancePlan,
    DeviceMaintenanceReminder
)

logger = logging.getLogger(__name__)

router = APIRouter()


# =====================================================
# 设备维护记录管理 API v2
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
        
        # 构建查询条件
        query = DeviceMaintenanceRecord.all().select_related('device')
        
        if device_id:
            query = query.filter(device_id=device_id)
        
        if device_code:
            query = query.filter(device__device_code__contains=device_code)
        
        if maintenance_type:
            query = query.filter(maintenance_type=maintenance_type)
        
        if maintenance_status:
            query = query.filter(maintenance_status=maintenance_status)
        
        if priority:
            query = query.filter(priority=priority)
        
        if assigned_to:
            query = query.filter(assigned_to__contains=assigned_to)
        
        if maintenance_team:
            query = query.filter(maintenance_team__contains=maintenance_team)
        
        if start_time:
            query = query.filter(planned_start_time__gte=start_time)
        
        if end_time:
            query = query.filter(planned_end_time__lte=end_time)
        
        # 分页查询
        offset = (page - 1) * page_size
        records = await query.offset(offset).limit(page_size).order_by('-created_at')
        total = await query.count()
        
        # 转换为响应格式
        data = []
        for record in records:
            device_info = await record.device
            record_data = {
                "id": record.id,
                "device_id": record.device_id,
                "device_code": device_info.device_code,
                "device_name": device_info.device_name,
                "maintenance_type": record.maintenance_type,
                "maintenance_title": record.maintenance_title,
                "maintenance_description": record.maintenance_description,
                "maintenance_status": record.maintenance_status,
                "priority": record.priority,
                "planned_start_time": record.planned_start_time.isoformat() if record.planned_start_time else None,
                "planned_end_time": record.planned_end_time.isoformat() if record.planned_end_time else None,
                "actual_start_time": record.actual_start_time.isoformat() if record.actual_start_time else None,
                "actual_end_time": record.actual_end_time.isoformat() if record.actual_end_time else None,
                "assigned_to": record.assigned_to,
                "maintenance_team": record.maintenance_team,
                "estimated_cost": float(record.estimated_cost) if record.estimated_cost else None,
                "actual_cost": float(record.actual_cost) if record.actual_cost else None,
                "maintenance_result": record.maintenance_result,
                "parts_replaced": record.parts_replaced,
                "next_maintenance_date": record.next_maintenance_date.isoformat() if record.next_maintenance_date else None,
                "notes": record.notes,
                "created_at": record.created_at.isoformat() if record.created_at else None,
                "updated_at": record.updated_at.isoformat() if record.updated_at else None
            }
            data.append(record_data)

        # 构建查询参数
        query_params = {}
        if device_id:
            query_params['device_id'] = device_id
        if device_code:
            query_params['device_code'] = device_code
        if maintenance_type:
            query_params['maintenance_type'] = maintenance_type
        if maintenance_status:
            query_params['maintenance_status'] = maintenance_status
        if priority:
            query_params['priority'] = priority
        if assigned_to:
            query_params['assigned_to'] = assigned_to
        if maintenance_team:
            query_params['maintenance_team'] = maintenance_team
        if start_time:
            query_params['start_time'] = start_time.isoformat()
        if end_time:
            query_params['end_time'] = end_time.isoformat()

        return formatter.paginated_success(
            data=data,
            total=total,
            page=page,
            page_size=page_size,
            message="获取设备维护记录列表成功",
            resource_type="devices/maintenance/records",
            query_params=query_params
        )

    except Exception as e:
        logger.error(f"获取设备维护记录列表失败: {str(e)}", exc_info=True)
        formatter = create_formatter(request)
        return formatter.internal_error(f"获取设备维护记录列表失败: {str(e)}")


@router.get("/maintenance/records/{record_id}", summary="获取维护记录详情", response_model=None)
async def get_maintenance_record(
    request: Request,
    record_id: int,
    user_id: int = DependAuth
):
    """
    获取维护记录详情
    
    - **record_id**: 维护记录ID
    """
    try:
        formatter = create_formatter(request)
        
        try:
            record = await DeviceMaintenanceRecord.filter(id=record_id).select_related('device').first()
        except DoesNotExist:
            return formatter.not_found("维护记录不存在", "maintenance_record")
        
        device_info = await record.device
        
        record_data = {
            "id": record.id,
            "device_id": record.device_id,
            "device_code": device_info.device_code,
            "device_name": device_info.device_name,
            "device_type": device_info.device_type,
            "maintenance_type": record.maintenance_type,
            "maintenance_title": record.maintenance_title,
            "maintenance_description": record.maintenance_description,
            "maintenance_status": record.maintenance_status,
            "priority": record.priority,
            "planned_start_time": record.planned_start_time.isoformat() if record.planned_start_time else None,
            "planned_end_time": record.planned_end_time.isoformat() if record.planned_end_time else None,
            "actual_start_time": record.actual_start_time.isoformat() if record.actual_start_time else None,
            "actual_end_time": record.actual_end_time.isoformat() if record.actual_end_time else None,
            "assigned_to": record.assigned_to,
            "maintenance_team": record.maintenance_team,
            "estimated_cost": float(record.estimated_cost) if record.estimated_cost else None,
            "actual_cost": float(record.actual_cost) if record.actual_cost else None,
            "maintenance_result": record.maintenance_result,
            "parts_replaced": record.parts_replaced,
            "next_maintenance_date": record.next_maintenance_date.isoformat() if record.next_maintenance_date else None,
            "notes": record.notes,
            "created_at": record.created_at.isoformat() if record.created_at else None,
            "updated_at": record.updated_at.isoformat() if record.updated_at else None
        }

        return formatter.success(
            data=record_data,
            message="获取维护记录详情成功",
            resource_id=str(record_id),
            resource_type="devices/maintenance/records"
        )

    except Exception as e:
        logger.error(f"获取维护记录详情失败: {str(e)}", exc_info=True)
        formatter = create_formatter(request)
        return formatter.internal_error(f"获取维护记录详情失败: {str(e)}")


@router.post("/maintenance/records", summary="创建维护记录", response_model=None)
async def create_maintenance_record(
    request: Request,
    record_data: DeviceMaintenanceRecordCreate,
    user_id: int = DependAuth
):
    """
    创建维护记录
    
    - **device_id**: 设备ID
    - **maintenance_type**: 维护类型
    - **maintenance_title**: 维护标题
    - **maintenance_description**: 维护描述（可选）
    - **priority**: 优先级（默认medium）
    - **planned_start_time**: 计划开始时间
    - **planned_end_time**: 计划结束时间
    - **assigned_to**: 负责人（可选）
    - **maintenance_team**: 维护团队（可选）
    - **estimated_cost**: 预估成本（可选）
    - **notes**: 备注信息（可选）
    """
    try:
        formatter = create_formatter(request)
        
        # 检查设备是否存在
        device_obj = await device_controller.get(id=record_data.device_id)
        if not device_obj:
            return formatter.not_found("设备不存在", "device")
        
        # 创建维护记录
        record = await DeviceMaintenanceRecord.create(**record_data.model_dump())
        
        return formatter.success(
            data={"id": record.id, "maintenance_title": record.maintenance_title},
            message="维护记录创建成功",
            code=201,
            resource_id=str(record.id),
            resource_type="devices/maintenance/records"
        )

    except Exception as e:
        logger.error(f"创建维护记录失败: {str(e)}", exc_info=True)
        formatter = create_formatter(request)
        return formatter.internal_error(f"创建维护记录失败: {str(e)}")


@router.put("/maintenance/records/{record_id}", summary="更新维护记录", response_model=None)
async def update_maintenance_record(
    request: Request,
    record_id: int,
    record_data: DeviceMaintenanceRecordUpdate,
    user_id: int = DependAuth
):
    """
    更新维护记录
    
    - **record_id**: 维护记录ID
    - 其他字段与创建维护记录相同，均为可选
    """
    try:
        formatter = create_formatter(request)
        
        try:
            record = await DeviceMaintenanceRecord.get(id=record_id)
        except DoesNotExist:
            return formatter.not_found("维护记录不存在", "maintenance_record")
        
        # 更新记录
        update_data = record_data.model_dump(exclude_unset=True)
        if update_data:
            await record.update_from_dict(update_data)
            await record.save()
        
        return formatter.success(
            message="维护记录更新成功",
            resource_id=str(record_id),
            resource_type="devices/maintenance/records"
        )

    except Exception as e:
        logger.error(f"更新维护记录失败: {str(e)}", exc_info=True)
        formatter = create_formatter(request)
        return formatter.internal_error(f"更新维护记录失败: {str(e)}")


@router.delete("/maintenance/records/{record_id}", summary="删除维护记录", response_model=None)
async def delete_maintenance_record(
    request: Request,
    record_id: int,
    user_id: int = DependAuth
):
    """
    删除维护记录
    
    - **record_id**: 维护记录ID
    """
    try:
        formatter = create_formatter(request)
        
        try:
            record = await DeviceMaintenanceRecord.get(id=record_id)
        except DoesNotExist:
            return formatter.not_found("维护记录不存在", "maintenance_record")
        
        await record.delete()
        
        return formatter.success(
            message="维护记录删除成功",
            resource_type="devices/maintenance/records"
        )

    except Exception as e:
        logger.error(f"删除维护记录失败: {str(e)}", exc_info=True)
        formatter = create_formatter(request)
        return formatter.internal_error(f"删除维护记录失败: {str(e)}")


# =====================================================
# 设备维护计划管理 API v2
# =====================================================

@router.get("/maintenance/plans", summary="获取设备维护计划列表", response_model=None)
async def get_maintenance_plans(
    request: Request,
    device_id: Optional[int] = Query(None, description="设备ID筛选"),
    device_code: Optional[str] = Query(None, description="设备编号筛选"),
    maintenance_type: Optional[str] = Query(None, description="维护类型筛选"),
    is_active: Optional[bool] = Query(None, description="是否激活筛选"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    user_id: int = DependAuth
):
    """
    获取设备维护计划列表
    
    - **device_id**: 设备ID筛选（可选）
    - **device_code**: 设备编号筛选（可选）
    - **maintenance_type**: 维护类型筛选（可选）
    - **is_active**: 是否激活筛选（可选）
    - **page**: 页码
    - **page_size**: 每页数量
    """
    try:
        formatter = create_formatter(request)
        
        # 构建查询条件
        query = DeviceMaintenancePlan.all().select_related('device')
        
        if device_id:
            query = query.filter(device_id=device_id)
        
        if device_code:
            query = query.filter(device__device_code__contains=device_code)
        
        if maintenance_type:
            query = query.filter(maintenance_type=maintenance_type)
        
        if is_active is not None:
            query = query.filter(is_active=is_active)
        
        # 分页查询
        offset = (page - 1) * page_size
        plans = await query.offset(offset).limit(page_size).order_by('-created_at')
        total = await query.count()
        
        # 转换为响应格式
        data = []
        for plan in plans:
            device_info = await plan.device
            plan_data = {
                "id": plan.id,
                "device_id": plan.device_id,
                "device_code": device_info.device_code,
                "device_name": device_info.device_name,
                "plan_name": plan.plan_name,
                "plan_description": plan.plan_description,
                "maintenance_type": plan.maintenance_type,
                "frequency_type": plan.frequency_type,
                "frequency_value": plan.frequency_value,
                "frequency_unit": plan.frequency_unit,
                "next_execution_date": plan.next_execution_date.isoformat() if plan.next_execution_date else None,
                "last_execution_date": plan.last_execution_date.isoformat() if plan.last_execution_date else None,
                "estimated_duration": plan.estimated_duration,
                "assigned_team": plan.assigned_team,
                "is_active": plan.is_active,
                "maintenance_checklist": plan.maintenance_checklist,
                "required_tools": plan.required_tools,
                "required_parts": plan.required_parts,
                "created_at": plan.created_at.isoformat() if plan.created_at else None,
                "updated_at": plan.updated_at.isoformat() if plan.updated_at else None
            }
            data.append(plan_data)

        # 构建查询参数
        query_params = {}
        if device_id:
            query_params['device_id'] = device_id
        if device_code:
            query_params['device_code'] = device_code
        if maintenance_type:
            query_params['maintenance_type'] = maintenance_type
        if is_active is not None:
            query_params['is_active'] = is_active

        return formatter.paginated_success(
            data=data,
            total=total,
            page=page,
            page_size=page_size,
            message="获取设备维护计划列表成功",
            resource_type="devices/maintenance/plans",
            query_params=query_params
        )

    except Exception as e:
        logger.error(f"获取设备维护计划列表失败: {str(e)}", exc_info=True)
        formatter = create_formatter(request)
        return formatter.internal_error(f"获取设备维护计划列表失败: {str(e)}")


@router.post("/maintenance/plans", summary="创建维护计划", response_model=None)
async def create_maintenance_plan(
    request: Request,
    plan_data: DeviceMaintenancePlanCreate,
    user_id: int = DependAuth
):
    """
    创建维护计划
    
    - **device_id**: 设备ID
    - **plan_name**: 计划名称
    - **plan_description**: 计划描述（可选）
    - **maintenance_type**: 维护类型
    - **frequency_type**: 频率类型
    - **frequency_value**: 频率值
    - **frequency_unit**: 频率单位（可选）
    - **estimated_duration**: 预估持续时间（可选）
    - **assigned_team**: 指定团队（可选）
    - **maintenance_checklist**: 维护检查清单（可选）
    - **required_tools**: 所需工具（可选）
    - **required_parts**: 所需零件（可选）
    """
    try:
        formatter = create_formatter(request)
        
        # 检查设备是否存在
        device_obj = await device_controller.get(id=plan_data.device_id)
        if not device_obj:
            return formatter.not_found("设备不存在", "device")
        
        # 创建维护计划
        plan_dict = plan_data.model_dump()
        
        # 计算下次执行日期
        if plan_data.frequency_type and plan_data.frequency_value:
            next_date = datetime.now()
            if plan_data.frequency_type == "daily":
                next_date += timedelta(days=plan_data.frequency_value)
            elif plan_data.frequency_type == "weekly":
                next_date += timedelta(weeks=plan_data.frequency_value)
            elif plan_data.frequency_type == "monthly":
                next_date += timedelta(days=plan_data.frequency_value * 30)
            elif plan_data.frequency_type == "yearly":
                next_date += timedelta(days=plan_data.frequency_value * 365)
            
            plan_dict["next_execution_date"] = next_date
        
        plan = await DeviceMaintenancePlan.create(**plan_dict)
        
        return formatter.success(
            data={"id": plan.id, "plan_name": plan.plan_name},
            message="维护计划创建成功",
            code=201,
            resource_id=str(plan.id),
            resource_type="devices/maintenance/plans"
        )

    except Exception as e:
        logger.error(f"创建维护计划失败: {str(e)}", exc_info=True)
        formatter = create_formatter(request)
        return formatter.internal_error(f"创建维护计划失败: {str(e)}")


# =====================================================
# 设备维护提醒管理 API v2
# =====================================================

@router.get("/maintenance/reminders", summary="获取维护提醒列表", response_model=None)
async def get_maintenance_reminders(
    request: Request,
    device_id: Optional[int] = Query(None, description="设备ID筛选"),
    reminder_type: Optional[str] = Query(None, description="提醒类型筛选"),
    is_sent: Optional[bool] = Query(None, description="是否已发送筛选"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    user_id: int = DependAuth
):
    """
    获取维护提醒列表
    
    - **device_id**: 设备ID筛选（可选）
    - **reminder_type**: 提醒类型筛选（可选）
    - **is_sent**: 是否已发送筛选（可选）
    - **page**: 页码
    - **page_size**: 每页数量
    """
    try:
        formatter = create_formatter(request)
        
        # 构建查询条件
        query = DeviceMaintenanceReminder.all().select_related('device', 'maintenance_plan')
        
        if device_id:
            query = query.filter(device_id=device_id)
        
        if reminder_type:
            query = query.filter(reminder_type=reminder_type)
        
        if is_sent is not None:
            query = query.filter(is_sent=is_sent)
        
        # 分页查询
        offset = (page - 1) * page_size
        reminders = await query.offset(offset).limit(page_size).order_by('-reminder_time')
        total = await query.count()
        
        # 转换为响应格式
        data = []
        for reminder in reminders:
            device_info = await reminder.device
            plan_info = await reminder.maintenance_plan if reminder.maintenance_plan_id else None
            
            reminder_data = {
                "id": reminder.id,
                "device_id": reminder.device_id,
                "device_code": device_info.device_code,
                "device_name": device_info.device_name,
                "maintenance_plan_id": reminder.maintenance_plan_id,
                "plan_name": plan_info.plan_name if plan_info else None,
                "reminder_type": reminder.reminder_type,
                "reminder_title": reminder.reminder_title,
                "reminder_message": reminder.reminder_message,
                "reminder_time": reminder.reminder_time.isoformat() if reminder.reminder_time else None,
                "is_sent": reminder.is_sent,
                "sent_time": reminder.sent_time.isoformat() if reminder.sent_time else None,
                "recipient_users": reminder.recipient_users,
                "recipient_teams": reminder.recipient_teams,
                "created_at": reminder.created_at.isoformat() if reminder.created_at else None
            }
            data.append(reminder_data)

        # 构建查询参数
        query_params = {}
        if device_id:
            query_params['device_id'] = device_id
        if reminder_type:
            query_params['reminder_type'] = reminder_type
        if is_sent is not None:
            query_params['is_sent'] = is_sent

        return formatter.paginated_success(
            data=data,
            total=total,
            page=page,
            page_size=page_size,
            message="获取维护提醒列表成功",
            resource_type="devices/maintenance/reminders",
            query_params=query_params
        )

    except Exception as e:
        logger.error(f"获取维护提醒列表失败: {str(e)}", exc_info=True)
        formatter = create_formatter(request)
        return formatter.internal_error(f"获取维护提醒列表失败: {str(e)}")


# =====================================================
# 设备维护统计 API v2
# =====================================================

@router.get("/maintenance/statistics", summary="获取维护统计信息", response_model=None)
async def get_maintenance_statistics(
    request: Request,
    device_type: Optional[str] = Query(None, description="设备类型筛选"),
    team_name: Optional[str] = Query(None, description="班组筛选"),
    start_date: Optional[datetime] = Query(None, description="开始日期"),
    end_date: Optional[datetime] = Query(None, description="结束日期"),
    user_id: int = DependAuth
):
    """
    获取维护统计信息
    
    - **device_type**: 设备类型筛选（可选）
    - **team_name**: 班组筛选（可选）
    - **start_date**: 开始日期（可选）
    - **end_date**: 结束日期（可选）
    """
    try:
        formatter = create_formatter(request)
        
        # 构建基础查询条件
        record_query = DeviceMaintenanceRecord.all().select_related('device')
        
        if device_type:
            record_query = record_query.filter(device__device_type=device_type)
        
        if team_name:
            record_query = record_query.filter(device__team_name=team_name)
        
        if start_date:
            record_query = record_query.filter(created_at__gte=start_date)
        
        if end_date:
            record_query = record_query.filter(created_at__lte=end_date)
        
        # 获取基础统计
        total_records = await record_query.count()
        completed_records = await record_query.filter(maintenance_status="completed").count()
        in_progress_records = await record_query.filter(maintenance_status="in_progress").count()
        planned_records = await record_query.filter(maintenance_status="planned").count()
        cancelled_records = await record_query.filter(maintenance_status="cancelled").count()
        
        # 即将到期的记录（未来7天内）
        upcoming_date = datetime.now() + timedelta(days=7)
        upcoming_records = await record_query.filter(
            maintenance_status="planned",
            planned_start_time__lte=upcoming_date,
            planned_start_time__gte=datetime.now()
        ).count()
        
        # 按维护类型统计
        maintenance_types = {}
        type_records = await record_query.group_by('maintenance_type').annotate(count=Count('id')).values('maintenance_type', 'count')
        for record in type_records:
            maintenance_types[record['maintenance_type']] = record['count']
        
        # 按优先级统计
        priority_distribution = {}
        priority_records = await record_query.group_by('priority').annotate(count=Count('id')).values('priority', 'count')
        for record in priority_records:
            priority_distribution[record['priority']] = record['count']
        
        # 按团队统计工作量
        team_workload = {}
        team_records = await record_query.filter(maintenance_team__not_isnull=True).group_by('maintenance_team').annotate(count=Count('id')).values('maintenance_team', 'count')
        for record in team_records:
            team_workload[record['maintenance_team']] = record['count']
        
        # 计算平均完成时间和成本
        completed_with_times = await record_query.filter(
            maintenance_status="completed",
            actual_start_time__not_isnull=True,
            actual_end_time__not_isnull=True
        ).all()
        
        total_completion_time = 0
        total_cost = 0
        cost_count = 0
        time_count = 0
        
        for record in completed_with_times:
            if record.actual_start_time and record.actual_end_time:
                duration = (record.actual_end_time - record.actual_start_time).total_seconds() / 3600  # 转换为小时
                total_completion_time += duration
                time_count += 1
            
            if record.actual_cost:
                total_cost += float(record.actual_cost)
                cost_count += 1
        
        avg_completion_time = total_completion_time / time_count if time_count > 0 else None
        avg_cost = total_cost / cost_count if cost_count > 0 else None
        
        # 构建统计结果
        statistics = {
            "total_records": total_records,
            "completed_records": completed_records,
            "in_progress_records": in_progress_records,
            "planned_records": planned_records,
            "cancelled_records": cancelled_records,
            "upcoming_records": upcoming_records,
            "maintenance_types": maintenance_types,
            "priority_distribution": priority_distribution,
            "team_workload": team_workload,
            "average_completion_time": avg_completion_time,
            "total_maintenance_cost": float(total_cost) if total_cost else 0,
            "average_maintenance_cost": float(avg_cost) if avg_cost else None
        }

        return formatter.success(
            data=statistics,
            message="获取维护统计信息成功",
            resource_type="devices/maintenance"
        )

    except Exception as e:
        logger.error(f"获取维护统计信息失败: {str(e)}", exc_info=True)
        formatter = create_formatter(request)
        return formatter.internal_error(f"获取维护统计信息失败: {str(e)}")