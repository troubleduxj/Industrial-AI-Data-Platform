#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
设备工艺管理 API v2
实现设备工艺CRUD操作、工艺执行监控、工艺模板管理等功能的RESTful API
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
from app.schemas.devices import (
    DeviceProcessCreate,
    DeviceProcessUpdate,
    DeviceProcessResponse,
    DeviceProcessExecutionCreate,
    DeviceProcessExecutionUpdate,
    DeviceProcessExecutionResponse,
    DeviceProcessTemplateCreate,
    DeviceProcessTemplateUpdate,
    DeviceProcessTemplateResponse,
    DeviceProcessQuery,
    DeviceProcessStatistics
)
from app.models.device import (
    DeviceInfo,
    DeviceProcess,
    DeviceProcessExecution,
    DeviceProcessTemplate,
    DeviceProcessMonitoring
)

logger = logging.getLogger(__name__)

router = APIRouter()


# =====================================================
# 设备工艺管理 API v2
# =====================================================

@router.get("/processes", summary="获取设备工艺列表", response_model=None)
async def get_device_processes(
    request: Request,
    device_id: Optional[int] = Query(None, description="设备ID筛选"),
    device_code: Optional[str] = Query(None, description="设备编号筛选"),
    process_type: Optional[str] = Query(None, description="工艺类型筛选"),
    process_status: Optional[str] = Query(None, description="工艺状态筛选"),
    approval_status: Optional[str] = Query(None, description="审批状态筛选"),
    difficulty_level: Optional[str] = Query(None, description="难度等级筛选"),
    created_by: Optional[str] = Query(None, description="创建人筛选"),
    assigned_team: Optional[str] = Query(None, description="指定团队筛选"),
    is_template: Optional[bool] = Query(None, description="是否为模板筛选"),
    is_active: Optional[bool] = Query(None, description="是否激活筛选"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    user_id: int = DependAuth
):
    """
    获取设备工艺列表
    
    - **device_id**: 设备ID筛选（可选）
    - **device_code**: 设备编号筛选（可选）
    - **process_type**: 工艺类型筛选（可选）
    - **process_status**: 工艺状态筛选（可选）
    - **approval_status**: 审批状态筛选（可选）
    - **difficulty_level**: 难度等级筛选（可选）
    - **created_by**: 创建人筛选（可选）
    - **assigned_team**: 指定团队筛选（可选）
    - **is_template**: 是否为模板筛选（可选）
    - **is_active**: 是否激活筛选（可选）
    - **page**: 页码
    - **page_size**: 每页数量
    """
    try:
        formatter = create_formatter(request)
        
        # 构建查询条件
        query = DeviceProcess.all().select_related('device')
        
        if device_id:
            query = query.filter(device_id=device_id)
        
        if device_code:
            query = query.filter(device__device_code__contains=device_code)
        
        if process_type:
            query = query.filter(process_type=process_type)
        
        if process_status:
            query = query.filter(process_status=process_status)
        
        if approval_status:
            query = query.filter(approval_status=approval_status)
        
        if difficulty_level:
            query = query.filter(difficulty_level=difficulty_level)
        
        if created_by:
            query = query.filter(created_by__contains=created_by)
        
        if assigned_team:
            query = query.filter(assigned_team__contains=assigned_team)
        
        if is_template is not None:
            query = query.filter(is_template=is_template)
        
        if is_active is not None:
            query = query.filter(is_active=is_active)
        
        # 分页查询
        offset = (page - 1) * page_size
        processes = await query.offset(offset).limit(page_size).order_by('-created_at')
        total = await query.count()
        
        # 转换为响应格式
        data = []
        for process in processes:
            device_info = await process.device
            process_data = {
                "id": process.id,
                "device_id": process.device_id,
                "device_code": device_info.device_code,
                "device_name": device_info.device_name,
                "process_name": process.process_name,
                "process_code": process.process_code,
                "process_version": process.process_version,
                "process_description": process.process_description,
                "process_status": process.process_status,
                "process_type": process.process_type,
                "process_category": process.process_category,
                "process_parameters": process.process_parameters,
                "quality_standards": process.quality_standards,
                "safety_requirements": process.safety_requirements,
                "estimated_duration": process.estimated_duration,
                "difficulty_level": process.difficulty_level,
                "required_skills": process.required_skills,
                "created_by": process.created_by,
                "approved_by": process.approved_by,
                "assigned_team": process.assigned_team,
                "parent_process_id": process.parent_process_id,
                "is_template": process.is_template,
                "is_active": process.is_active,
                "approval_status": process.approval_status,
                "approval_date": process.approval_date.isoformat() if process.approval_date else None,
                "approval_notes": process.approval_notes,
                "created_at": process.created_at.isoformat() if process.created_at else None,
                "updated_at": process.updated_at.isoformat() if process.updated_at else None
            }
            data.append(process_data)

        # 构建查询参数
        query_params = {}
        if device_id:
            query_params['device_id'] = device_id
        if device_code:
            query_params['device_code'] = device_code
        if process_type:
            query_params['process_type'] = process_type
        if process_status:
            query_params['process_status'] = process_status
        if approval_status:
            query_params['approval_status'] = approval_status
        if difficulty_level:
            query_params['difficulty_level'] = difficulty_level
        if created_by:
            query_params['created_by'] = created_by
        if assigned_team:
            query_params['assigned_team'] = assigned_team
        if is_template is not None:
            query_params['is_template'] = is_template
        if is_active is not None:
            query_params['is_active'] = is_active

        return formatter.paginated_success(
            data=data,
            total=total,
            page=page,
            page_size=page_size,
            message="获取设备工艺列表成功",
            resource_type="devices/processes",
            query_params=query_params
        )

    except Exception as e:
        logger.error(f"获取设备工艺列表失败: {str(e)}", exc_info=True)
        formatter = create_formatter(request)
        return formatter.internal_error(f"获取设备工艺列表失败: {str(e)}")


@router.get("/processes/{process_id}", summary="获取工艺详情", response_model=None)
async def get_device_process(
    request: Request,
    process_id: int,
    user_id: int = DependAuth
):
    """
    获取工艺详情
    
    - **process_id**: 工艺ID
    """
    try:
        formatter = create_formatter(request)
        
        try:
            process = await DeviceProcess.filter(id=process_id).select_related('device').first()
        except DoesNotExist:
            return formatter.not_found("工艺不存在", "process")
        
        device_info = await process.device
        
        process_data = {
            "id": process.id,
            "device_id": process.device_id,
            "device_code": device_info.device_code,
            "device_name": device_info.device_name,
            "device_type": device_info.device_type,
            "process_name": process.process_name,
            "process_code": process.process_code,
            "process_version": process.process_version,
            "process_description": process.process_description,
            "process_status": process.process_status,
            "process_type": process.process_type,
            "process_category": process.process_category,
            "process_parameters": process.process_parameters,
            "quality_standards": process.quality_standards,
            "safety_requirements": process.safety_requirements,
            "estimated_duration": process.estimated_duration,
            "difficulty_level": process.difficulty_level,
            "required_skills": process.required_skills,
            "created_by": process.created_by,
            "approved_by": process.approved_by,
            "assigned_team": process.assigned_team,
            "parent_process_id": process.parent_process_id,
            "is_template": process.is_template,
            "is_active": process.is_active,
            "approval_status": process.approval_status,
            "approval_date": process.approval_date.isoformat() if process.approval_date else None,
            "approval_notes": process.approval_notes,
            "created_at": process.created_at.isoformat() if process.created_at else None,
            "updated_at": process.updated_at.isoformat() if process.updated_at else None
        }

        return formatter.success(
            data=process_data,
            message="获取工艺详情成功",
            resource_id=str(process_id),
            resource_type="devices/processes"
        )

    except Exception as e:
        logger.error(f"获取工艺详情失败: {str(e)}", exc_info=True)
        formatter = create_formatter(request)
        return formatter.internal_error(f"获取工艺详情失败: {str(e)}")


@router.post("/processes", summary="创建工艺", response_model=None)
async def create_device_process(
    request: Request,
    process_data: DeviceProcessCreate,
    user_id: int = DependAuth
):
    """
    创建工艺
    
    - **device_id**: 设备ID
    - **process_name**: 工艺名称
    - **process_code**: 工艺编码
    - **process_version**: 工艺版本（默认1.0）
    - **process_description**: 工艺描述（可选）
    - **process_type**: 工艺类型
    - **process_category**: 工艺分类（可选）
    - **process_parameters**: 工艺参数（可选）
    - **quality_standards**: 质量标准（可选）
    - **safety_requirements**: 安全要求（可选）
    - **estimated_duration**: 预估执行时间（可选）
    - **difficulty_level**: 难度等级（默认medium）
    - **required_skills**: 所需技能（可选）
    - **created_by**: 创建人（可选）
    - **assigned_team**: 指定团队（可选）
    - **is_template**: 是否为模板（默认false）
    """
    try:
        formatter = create_formatter(request)
        
        # 检查设备是否存在
        device_obj = await device_controller.get(id=process_data.device_id)
        if not device_obj:
            return formatter.not_found("设备不存在", "device")
        
        # 检查工艺编码是否已存在
        if await DeviceProcess.filter(process_code=process_data.process_code).exists():
            return formatter.error(
                f"工艺编码 {process_data.process_code} 已存在",
                code=400,
                error_type="ValidationError"
            )
        
        # 创建工艺
        process = await DeviceProcess.create(**process_data.model_dump())
        
        return formatter.success(
            data={"id": process.id, "process_code": process.process_code},
            message="工艺创建成功",
            code=201,
            resource_id=str(process.id),
            resource_type="devices/processes"
        )

    except Exception as e:
        logger.error(f"创建工艺失败: {str(e)}", exc_info=True)
        formatter = create_formatter(request)
        return formatter.internal_error(f"创建工艺失败: {str(e)}")


@router.put("/processes/{process_id}", summary="更新工艺", response_model=None)
async def update_device_process(
    request: Request,
    process_id: int,
    process_data: DeviceProcessUpdate,
    user_id: int = DependAuth
):
    """
    更新工艺
    
    - **process_id**: 工艺ID
    - 其他字段与创建工艺相同，均为可选
    """
    try:
        formatter = create_formatter(request)
        
        try:
            process = await DeviceProcess.get(id=process_id)
        except DoesNotExist:
            return formatter.not_found("工艺不存在", "process")
        
        # 更新工艺
        update_data = process_data.model_dump(exclude_unset=True)
        if update_data:
            # 如果更新审批状态为approved，设置审批日期
            if update_data.get('approval_status') == 'approved' and not process.approval_date:
                update_data['approval_date'] = datetime.now()
            
            await process.update_from_dict(update_data)
            await process.save()
        
        return formatter.success(
            message="工艺更新成功",
            resource_id=str(process_id),
            resource_type="devices/processes"
        )

    except Exception as e:
        logger.error(f"更新工艺失败: {str(e)}", exc_info=True)
        formatter = create_formatter(request)
        return formatter.internal_error(f"更新工艺失败: {str(e)}")


@router.delete("/processes/{process_id}", summary="删除工艺", response_model=None)
async def delete_device_process(
    request: Request,
    process_id: int,
    user_id: int = DependAuth
):
    """
    删除工艺
    
    - **process_id**: 工艺ID
    """
    try:
        formatter = create_formatter(request)
        
        try:
            process = await DeviceProcess.get(id=process_id)
        except DoesNotExist:
            return formatter.not_found("工艺不存在", "process")
        
        # 检查是否有关联的执行记录
        execution_count = await DeviceProcessExecution.filter(process_id=process_id).count()
        if execution_count > 0:
            return formatter.error(
                f"该工艺下还有 {execution_count} 个执行记录，无法删除",
                code=400,
                error_type="ValidationError"
            )
        
        await process.delete()
        
        return formatter.success(
            message="工艺删除成功",
            resource_type="devices/processes"
        )

    except Exception as e:
        logger.error(f"删除工艺失败: {str(e)}", exc_info=True)
        formatter = create_formatter(request)
        return formatter.internal_error(f"删除工艺失败: {str(e)}")


# =====================================================
# 工艺执行管理 API v2
# =====================================================

@router.get("/processes/executions", summary="获取工艺执行记录列表", response_model=None)
async def get_process_executions(
    request: Request,
    device_id: Optional[int] = Query(None, description="设备ID筛选"),
    process_id: Optional[int] = Query(None, description="工艺ID筛选"),
    execution_status: Optional[str] = Query(None, description="执行状态筛选"),
    operator: Optional[str] = Query(None, description="操作员筛选"),
    execution_team: Optional[str] = Query(None, description="执行团队筛选"),
    quality_result: Optional[str] = Query(None, description="质量结果筛选"),
    start_time: Optional[datetime] = Query(None, description="开始时间筛选"),
    end_time: Optional[datetime] = Query(None, description="结束时间筛选"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    user_id: int = DependAuth
):
    """
    获取工艺执行记录列表
    
    - **device_id**: 设备ID筛选（可选）
    - **process_id**: 工艺ID筛选（可选）
    - **execution_status**: 执行状态筛选（可选）
    - **operator**: 操作员筛选（可选）
    - **execution_team**: 执行团队筛选（可选）
    - **quality_result**: 质量结果筛选（可选）
    - **start_time**: 开始时间筛选（可选）
    - **end_time**: 结束时间筛选（可选）
    - **page**: 页码
    - **page_size**: 每页数量
    """
    try:
        formatter = create_formatter(request)
        
        # 构建查询条件
        query = DeviceProcessExecution.all().select_related('device', 'process')
        
        if device_id:
            query = query.filter(device_id=device_id)
        
        if process_id:
            query = query.filter(process_id=process_id)
        
        if execution_status:
            query = query.filter(execution_status=execution_status)
        
        if operator:
            query = query.filter(operator__contains=operator)
        
        if execution_team:
            query = query.filter(execution_team__contains=execution_team)
        
        if quality_result:
            query = query.filter(quality_result=quality_result)
        
        if start_time:
            query = query.filter(actual_start_time__gte=start_time)
        
        if end_time:
            query = query.filter(actual_end_time__lte=end_time)
        
        # 分页查询
        offset = (page - 1) * page_size
        executions = await query.offset(offset).limit(page_size).order_by('-created_at')
        total = await query.count()
        
        # 转换为响应格式
        data = []
        for execution in executions:
            device_info = await execution.device
            process_info = await execution.process
            
            execution_data = {
                "id": execution.id,
                "device_id": execution.device_id,
                "process_id": execution.process_id,
                "device_code": device_info.device_code,
                "device_name": device_info.device_name,
                "process_name": process_info.process_name,
                "process_code": process_info.process_code,
                "execution_code": execution.execution_code,
                "execution_name": execution.execution_name,
                "execution_description": execution.execution_description,
                "execution_status": execution.execution_status,
                "planned_start_time": execution.planned_start_time.isoformat() if execution.planned_start_time else None,
                "planned_end_time": execution.planned_end_time.isoformat() if execution.planned_end_time else None,
                "actual_start_time": execution.actual_start_time.isoformat() if execution.actual_start_time else None,
                "actual_end_time": execution.actual_end_time.isoformat() if execution.actual_end_time else None,
                "operator": execution.operator,
                "supervisor": execution.supervisor,
                "execution_team": execution.execution_team,
                "execution_result": execution.execution_result,
                "quality_result": execution.quality_result,
                "quality_score": execution.quality_score,
                "quality_notes": execution.quality_notes,
                "estimated_cost": execution.estimated_cost,
                "actual_cost": execution.actual_cost,
                "created_at": execution.created_at.isoformat() if execution.created_at else None,
                "updated_at": execution.updated_at.isoformat() if execution.updated_at else None
            }
            data.append(execution_data)

        # 构建查询参数
        query_params = {}
        if device_id:
            query_params['device_id'] = device_id
        if process_id:
            query_params['process_id'] = process_id
        if execution_status:
            query_params['execution_status'] = execution_status
        if operator:
            query_params['operator'] = operator
        if execution_team:
            query_params['execution_team'] = execution_team
        if quality_result:
            query_params['quality_result'] = quality_result
        if start_time:
            query_params['start_time'] = start_time.isoformat()
        if end_time:
            query_params['end_time'] = end_time.isoformat()

        return formatter.paginated_success(
            data=data,
            total=total,
            page=page,
            page_size=page_size,
            message="获取工艺执行记录列表成功",
            resource_type="devices/processes/executions",
            query_params=query_params
        )

    except Exception as e:
        logger.error(f"获取工艺执行记录列表失败: {str(e)}", exc_info=True)
        formatter = create_formatter(request)
        return formatter.internal_error(f"获取工艺执行记录列表失败: {str(e)}")


@router.post("/processes/executions", summary="创建工艺执行记录", response_model=None)
async def create_process_execution(
    request: Request,
    execution_data: DeviceProcessExecutionCreate,
    user_id: int = DependAuth
):
    """
    创建工艺执行记录
    
    - **device_id**: 设备ID
    - **process_id**: 工艺ID
    - **execution_code**: 执行编号
    - **execution_name**: 执行名称
    - **execution_description**: 执行描述（可选）
    - **planned_start_time**: 计划开始时间（可选）
    - **planned_end_time**: 计划结束时间（可选）
    - **operator**: 操作员（可选）
    - **supervisor**: 监督员（可选）
    - **execution_team**: 执行团队（可选）
    - **estimated_cost**: 预估成本（可选）
    - **notes**: 备注信息（可选）
    """
    try:
        formatter = create_formatter(request)
        
        # 检查设备是否存在
        device_obj = await device_controller.get(id=execution_data.device_id)
        if not device_obj:
            return formatter.not_found("设备不存在", "device")
        
        # 检查工艺是否存在
        try:
            process_obj = await DeviceProcess.get(id=execution_data.process_id)
        except DoesNotExist:
            return formatter.not_found("工艺不存在", "process")
        
        # 检查执行编号是否已存在
        if await DeviceProcessExecution.filter(execution_code=execution_data.execution_code).exists():
            return formatter.error(
                f"执行编号 {execution_data.execution_code} 已存在",
                code=400,
                error_type="ValidationError"
            )
        
        # 创建执行记录
        execution = await DeviceProcessExecution.create(**execution_data.model_dump())
        
        return formatter.success(
            data={"id": execution.id, "execution_code": execution.execution_code},
            message="工艺执行记录创建成功",
            code=201,
            resource_id=str(execution.id),
            resource_type="devices/processes/executions"
        )

    except Exception as e:
        logger.error(f"创建工艺执行记录失败: {str(e)}", exc_info=True)
        formatter = create_formatter(request)
        return formatter.internal_error(f"创建工艺执行记录失败: {str(e)}")


# =====================================================
# 工艺模板管理 API v2
# =====================================================

@router.get("/processes/templates", summary="获取工艺模板列表", response_model=None)
async def get_process_templates(
    request: Request,
    template_category: Optional[str] = Query(None, description="模板分类筛选"),
    device_type: Optional[str] = Query(None, description="适用设备类型筛选"),
    process_type: Optional[str] = Query(None, description="工艺类型筛选"),
    is_active: Optional[bool] = Query(None, description="是否激活筛选"),
    is_public: Optional[bool] = Query(None, description="是否公开筛选"),
    created_by: Optional[str] = Query(None, description="创建人筛选"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    user_id: int = DependAuth
):
    """
    获取工艺模板列表
    
    - **template_category**: 模板分类筛选（可选）
    - **device_type**: 适用设备类型筛选（可选）
    - **process_type**: 工艺类型筛选（可选）
    - **is_active**: 是否激活筛选（可选）
    - **is_public**: 是否公开筛选（可选）
    - **created_by**: 创建人筛选（可选）
    - **page**: 页码
    - **page_size**: 每页数量
    """
    try:
        formatter = create_formatter(request)
        
        # 构建查询条件
        query = DeviceProcessTemplate.all()
        
        if template_category:
            query = query.filter(template_category=template_category)
        
        if device_type:
            query = query.filter(device_type=device_type)
        
        if process_type:
            query = query.filter(process_type=process_type)
        
        if is_active is not None:
            query = query.filter(is_active=is_active)
        
        if is_public is not None:
            query = query.filter(is_public=is_public)
        
        if created_by:
            query = query.filter(created_by__contains=created_by)
        
        # 分页查询
        offset = (page - 1) * page_size
        templates = await query.offset(offset).limit(page_size).order_by('-created_at')
        total = await query.count()
        
        # 转换为响应格式
        data = []
        for template in templates:
            template_data = {
                "id": template.id,
                "template_name": template.template_name,
                "template_code": template.template_code,
                "template_description": template.template_description,
                "template_category": template.template_category,
                "device_type": template.device_type,
                "process_type": template.process_type,
                "template_content": template.template_content,
                "default_parameters": template.default_parameters,
                "parameter_constraints": template.parameter_constraints,
                "is_active": template.is_active,
                "is_public": template.is_public,
                "created_by": template.created_by,
                "maintained_by": template.maintained_by,
                "usage_count": template.usage_count,
                "last_used_date": template.last_used_date.isoformat() if template.last_used_date else None,
                "created_at": template.created_at.isoformat() if template.created_at else None,
                "updated_at": template.updated_at.isoformat() if template.updated_at else None
            }
            data.append(template_data)

        # 构建查询参数
        query_params = {}
        if template_category:
            query_params['template_category'] = template_category
        if device_type:
            query_params['device_type'] = device_type
        if process_type:
            query_params['process_type'] = process_type
        if is_active is not None:
            query_params['is_active'] = is_active
        if is_public is not None:
            query_params['is_public'] = is_public
        if created_by:
            query_params['created_by'] = created_by

        return formatter.paginated_success(
            data=data,
            total=total,
            page=page,
            page_size=page_size,
            message="获取工艺模板列表成功",
            resource_type="devices/processes/templates",
            query_params=query_params
        )

    except Exception as e:
        logger.error(f"获取工艺模板列表失败: {str(e)}", exc_info=True)
        formatter = create_formatter(request)
        return formatter.internal_error(f"获取工艺模板列表失败: {str(e)}")


@router.post("/processes/templates", summary="创建工艺模板", response_model=None)
async def create_process_template(
    request: Request,
    template_data: DeviceProcessTemplateCreate,
    user_id: int = DependAuth
):
    """
    创建工艺模板
    
    - **template_name**: 模板名称
    - **template_code**: 模板编码
    - **template_description**: 模板描述（可选）
    - **template_category**: 模板分类
    - **device_type**: 适用设备类型（可选）
    - **process_type**: 工艺类型
    - **template_content**: 模板内容
    - **default_parameters**: 默认参数（可选）
    - **parameter_constraints**: 参数约束（可选）
    - **is_public**: 是否公开（默认false）
    - **created_by**: 创建人（可选）
    """
    try:
        formatter = create_formatter(request)
        
        # 检查模板编码是否已存在
        if await DeviceProcessTemplate.filter(template_code=template_data.template_code).exists():
            return formatter.error(
                f"模板编码 {template_data.template_code} 已存在",
                code=400,
                error_type="ValidationError"
            )
        
        # 创建模板
        template = await DeviceProcessTemplate.create(**template_data.model_dump())
        
        return formatter.success(
            data={"id": template.id, "template_code": template.template_code},
            message="工艺模板创建成功",
            code=201,
            resource_id=str(template.id),
            resource_type="devices/processes/templates"
        )

    except Exception as e:
        logger.error(f"创建工艺模板失败: {str(e)}", exc_info=True)
        formatter = create_formatter(request)
        return formatter.internal_error(f"创建工艺模板失败: {str(e)}")


# =====================================================
# 工艺统计 API v2
# =====================================================

@router.get("/processes/statistics", summary="获取工艺统计信息", response_model=None)
async def get_process_statistics(
    request: Request,
    device_type: Optional[str] = Query(None, description="设备类型筛选"),
    process_type: Optional[str] = Query(None, description="工艺类型筛选"),
    team_name: Optional[str] = Query(None, description="团队筛选"),
    start_date: Optional[datetime] = Query(None, description="开始日期"),
    end_date: Optional[datetime] = Query(None, description="结束日期"),
    user_id: int = DependAuth
):
    """
    获取工艺统计信息
    
    - **device_type**: 设备类型筛选（可选）
    - **process_type**: 工艺类型筛选（可选）
    - **team_name**: 团队筛选（可选）
    - **start_date**: 开始日期（可选）
    - **end_date**: 结束日期（可选）
    """
    try:
        formatter = create_formatter(request)
        
        # 构建基础查询条件
        process_query = DeviceProcess.all().select_related('device')
        execution_query = DeviceProcessExecution.all().select_related('device', 'process')
        
        if device_type:
            process_query = process_query.filter(device__device_type=device_type)
            execution_query = execution_query.filter(device__device_type=device_type)
        
        if process_type:
            process_query = process_query.filter(process_type=process_type)
            execution_query = execution_query.filter(process__process_type=process_type)
        
        if team_name:
            process_query = process_query.filter(assigned_team=team_name)
            execution_query = execution_query.filter(execution_team=team_name)
        
        if start_date:
            process_query = process_query.filter(created_at__gte=start_date)
            execution_query = execution_query.filter(created_at__gte=start_date)
        
        if end_date:
            process_query = process_query.filter(created_at__lte=end_date)
            execution_query = execution_query.filter(created_at__lte=end_date)
        
        # 获取工艺基础统计
        total_processes = await process_query.count()
        active_processes = await process_query.filter(is_active=True).count()
        template_processes = await process_query.filter(is_template=True).count()
        draft_processes = await process_query.filter(process_status="draft").count()
        approved_processes = await process_query.filter(approval_status="approved").count()
        
        # 按工艺类型统计
        process_types = {}
        type_stats = await process_query.group_by('process_type').values('process_type', count=Count('id'))
        for stat in type_stats:
            process_types[stat['process_type']] = stat['count']
        
        # 按难度等级统计
        difficulty_distribution = {}
        difficulty_stats = await process_query.group_by('difficulty_level').values('difficulty_level', count=Count('id'))
        for stat in difficulty_stats:
            difficulty_distribution[stat['difficulty_level']] = stat['count']
        
        # 按审批状态统计
        approval_status_distribution = {}
        approval_stats = await process_query.group_by('approval_status').values('approval_status', count=Count('id'))
        for stat in approval_stats:
            approval_status_distribution[stat['approval_status']] = stat['count']
        
        # 按团队工作量统计
        team_workload = {}
        team_stats = await process_query.filter(assigned_team__not_isnull=True).group_by('assigned_team').values('assigned_team', count=Count('id'))
        for stat in team_stats:
            team_workload[stat['assigned_team']] = stat['count']
        
        # 获取执行统计
        total_executions = await execution_query.count()
        completed_executions = await execution_query.filter(execution_status="completed").count()
        
        # 计算成功率
        success_rate = (completed_executions / total_executions * 100) if total_executions > 0 else None
        
        # 计算平均执行时间
        completed_with_times = await execution_query.filter(
            execution_status="completed",
            actual_start_time__not_isnull=True,
            actual_end_time__not_isnull=True
        )
        
        total_execution_time = 0
        quality_scores = []
        
        for execution in completed_with_times:
            if execution.actual_start_time and execution.actual_end_time:
                duration = (execution.actual_end_time - execution.actual_start_time).total_seconds() / 3600  # 转换为小时
                total_execution_time += duration
            
            if execution.quality_score:
                quality_scores.append(execution.quality_score)
        
        avg_execution_time = total_execution_time / len(completed_with_times) if completed_with_times else None
        avg_quality_score = sum(quality_scores) / len(quality_scores) if quality_scores else None
        
        # 构建统计结果
        statistics = {
            "total_processes": total_processes,
            "active_processes": active_processes,
            "template_processes": template_processes,
            "draft_processes": draft_processes,
            "approved_processes": approved_processes,
            "process_types": process_types,
            "difficulty_distribution": difficulty_distribution,
            "approval_status_distribution": approval_status_distribution,
            "team_workload": team_workload,
            "total_executions": total_executions,
            "completed_executions": completed_executions,
            "success_rate": success_rate,
            "average_execution_time": avg_execution_time,
            "average_quality_score": avg_quality_score
        }

        return formatter.success(
            data=statistics,
            message="获取工艺统计信息成功",
            resource_type="devices/processes"
        )

    except Exception as e:
        logger.error(f"获取工艺统计信息失败: {str(e)}", exc_info=True)
        formatter = create_formatter(request)
        return formatter.internal_error(f"获取工艺统计信息失败: {str(e)}")