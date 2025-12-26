#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工作流管理 API v2
提供工作流的CRUD操作、执行、调度等功能
"""

from typing import Optional, List
from datetime import datetime
import uuid

from fastapi import APIRouter, Query, HTTPException, Depends
from pydantic import BaseModel, Field

from app.models.workflow import Workflow, WorkflowExecution, WorkflowNodeExecution, WorkflowTemplate, WorkflowSchedule
from app.schemas.workflow import (
    WorkflowCreate, WorkflowUpdate, WorkflowDesignSave,
    WorkflowExecuteRequest, WorkflowTemplateCreate, WorkflowScheduleCreate,
    WorkflowStats, WorkflowValidationResult
)
from app.core.response_formatter_v2 import create_formatter
from app.core.pagination import get_pagination_params, create_pagination_response
from app.log import logger

router = APIRouter(tags=["工作流管理"])


# =====================================================
# 工作流类型和优先级定义
# =====================================================

WORKFLOW_TYPES = {
    "device_monitor": "设备监控流程",
    "alarm_process": "报警处理流程",
    "data_collection": "数据采集流程",
    "maintenance": "维护保养流程",
    "custom": "自定义流程"
}

WORKFLOW_PRIORITIES = {
    "low": "低",
    "medium": "中",
    "high": "高",
    "urgent": "紧急"
}

TRIGGER_TYPES = {
    "manual": "手动触发",
    "schedule": "定时触发",
    "event": "事件触发",
    "webhook": "Webhook触发"
}


# =====================================================
# 工作流 CRUD API
# =====================================================

@router.get("", summary="获取工作流列表")
async def get_workflows(
    type: Optional[str] = Query(None, description="工作流类型"),
    priority: Optional[str] = Query(None, description="优先级"),
    is_active: Optional[bool] = Query(None, description="是否启用"),
    is_published: Optional[bool] = Query(None, description="是否已发布"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    pagination: dict = Depends(get_pagination_params)
):
    """获取工作流列表"""
    try:
        query = Workflow.all()
        
        if type:
            query = query.filter(type=type)
        if priority:
            query = query.filter(priority=priority)
        if is_active is not None:
            query = query.filter(is_active=is_active)
        if is_published is not None:
            query = query.filter(is_published=is_published)
        if search:
            query = query.filter(name__icontains=search)
        
        total = await query.count()
        workflows = await query.offset(pagination["offset"]).limit(pagination["limit"]).order_by("-created_at")
        
        items = []
        for wf in workflows:
            items.append({
                "id": wf.id,
                "name": wf.name,
                "code": wf.code,
                "description": wf.description,
                "type": wf.type,
                "type_label": WORKFLOW_TYPES.get(wf.type, wf.type),
                "category": wf.category,
                "priority": wf.priority,
                "priority_label": WORKFLOW_PRIORITIES.get(wf.priority, wf.priority),
                "trigger_type": wf.trigger_type,
                "trigger_type_label": TRIGGER_TYPES.get(wf.trigger_type, wf.trigger_type),
                "is_active": wf.is_active,
                "is_published": wf.is_published,
                "version": wf.version,
                "accent_color": getattr(wf, "accent_color", None),
                "execution_count": wf.execution_count,
                "success_count": wf.success_count,
                "failure_count": wf.failure_count,
                "last_executed_at": wf.last_executed_at.isoformat() if wf.last_executed_at else None,
                "created_by_name": wf.created_by_name,
                "created_at": wf.created_at.isoformat() if wf.created_at else None,
                "updated_at": wf.updated_at.isoformat() if wf.updated_at else None,
            })
        
        paginated = create_pagination_response(
            data=items,
            total=total,
            page=pagination["page"],
            page_size=pagination["page_size"]
        )
        
        formatter = create_formatter()
        return formatter.success(data=paginated, message=f"获取工作流列表成功，共{total}条")
        
    except Exception as e:
        logger.error(f"获取工作流列表失败: {str(e)}", exc_info=True)
        formatter = create_formatter()
        return formatter.error(message="获取工作流列表失败")


@router.get("/types", summary="获取工作流类型列表")
async def get_workflow_types():
    """获取工作流类型列表"""
    formatter = create_formatter()
    return formatter.success(
        data=[{"value": k, "label": v} for k, v in WORKFLOW_TYPES.items()],
        message="获取工作流类型列表成功"
    )


@router.get("/priorities", summary="获取优先级列表")
async def get_workflow_priorities():
    """获取优先级列表"""
    formatter = create_formatter()
    return formatter.success(
        data=[{"value": k, "label": v} for k, v in WORKFLOW_PRIORITIES.items()],
        message="获取优先级列表成功"
    )


@router.get("/trigger-types", summary="获取触发类型列表")
async def get_trigger_types():
    """获取触发类型列表"""
    formatter = create_formatter()
    return formatter.success(
        data=[{"value": k, "label": v} for k, v in TRIGGER_TYPES.items()],
        message="获取触发类型列表成功"
    )


@router.get("/stats", summary="获取工作流统计信息")
async def get_workflow_stats():
    """获取工作流统计信息"""
    try:
        total = await Workflow.all().count()
        active = await Workflow.filter(is_active=True).count()
        published = await Workflow.filter(is_published=True).count()
        
        # 按类型统计
        by_type = {}
        for wf_type in WORKFLOW_TYPES.keys():
            count = await Workflow.filter(type=wf_type).count()
            by_type[wf_type] = count
        
        # 按优先级统计
        by_priority = {}
        for priority in WORKFLOW_PRIORITIES.keys():
            count = await Workflow.filter(priority=priority).count()
            by_priority[priority] = count
        
        # 执行统计
        total_executions = await WorkflowExecution.all().count()
        success_executions = await WorkflowExecution.filter(status="success").count()
        failed_executions = await WorkflowExecution.filter(status="failed").count()
        running_executions = await WorkflowExecution.filter(status="running").count()
        
        stats = {
            "total_workflows": total,
            "active_workflows": active,
            "published_workflows": published,
            "total_executions": total_executions,
            "success_executions": success_executions,
            "failed_executions": failed_executions,
            "running_executions": running_executions,
            "by_type": by_type,
            "by_priority": by_priority
        }
        
        formatter = create_formatter()
        return formatter.success(data=stats, message="获取统计信息成功")
        
    except Exception as e:
        logger.error(f"获取工作流统计失败: {str(e)}", exc_info=True)
        formatter = create_formatter()
        return formatter.error(message="获取统计信息失败")


# =====================================================
# 工作流模板 API (必须在 /{workflow_id} 之前定义)
# =====================================================

@router.get("/templates", summary="获取工作流模板列表")
async def get_workflow_templates(
    type: Optional[str] = Query(None, description="模板类型"),
    category: Optional[str] = Query(None, description="模板分类"),
    search: Optional[str] = Query(None, description="搜索关键词"),
):
    """获取工作流模板列表"""
    try:
        query = WorkflowTemplate.filter(is_active=True)
        
        if type:
            query = query.filter(type=type)
        if category:
            query = query.filter(category=category)
        if search:
            query = query.filter(name__icontains=search)
        
        templates = await query.order_by("-is_system", "-usage_count")
        
        items = [
            {
                "id": t.id,
                "name": t.name,
                "code": t.code,
                "description": t.description,
                "type": t.type,
                "type_label": WORKFLOW_TYPES.get(t.type, t.type),
                "category": t.category,
                "is_system": t.is_system,
                "usage_count": t.usage_count,
                "node_count": len(t.nodes),
                "created_at": t.created_at.isoformat() if t.created_at else None,
            }
            for t in templates
        ]
        
        formatter = create_formatter()
        return formatter.success(data=items, message="获取模板列表成功")
        
    except Exception as e:
        logger.error(f"获取模板列表失败: {str(e)}", exc_info=True)
        formatter = create_formatter()
        return formatter.error(message="获取模板列表失败")


@router.get("/templates/{template_id}", summary="获取模板详情")
async def get_workflow_template_detail(template_id: int):
    """获取工作流模板详情"""
    try:
        template = await WorkflowTemplate.get_or_none(id=template_id)
        if not template:
            formatter = create_formatter()
            return formatter.error(message="模板不存在", code=404)
        
        data = {
            "id": template.id,
            "name": template.name,
            "code": template.code,
            "description": template.description,
            "type": template.type,
            "category": template.category,
            "nodes": template.nodes,
            "connections": template.connections,
            "default_config": template.default_config,
            "is_system": template.is_system,
            "usage_count": template.usage_count,
            "created_at": template.created_at.isoformat() if template.created_at else None,
        }
        
        formatter = create_formatter()
        return formatter.success(data=data, message="获取模板详情成功")
        
    except Exception as e:
        logger.error(f"获取模板详情失败: {str(e)}", exc_info=True)
        formatter = create_formatter()
        return formatter.error(message="获取模板详情失败")


@router.post("/templates/{template_id}/use", summary="使用模板创建工作流")
async def use_workflow_template_to_create(template_id: int, name: str = Query(..., description="工作流名称")):
    """使用模板创建新工作流"""
    try:
        template = await WorkflowTemplate.get_or_none(id=template_id)
        if not template:
            formatter = create_formatter()
            return formatter.error(message="模板不存在", code=404)
        
        # 生成工作流代码
        code = generate_workflow_code(name)
        
        # 创建工作流
        wf = await Workflow.create(
            name=name,
            code=code,
            description=f"基于模板 [{template.name}] 创建",
            type=template.type,
            category=template.category,
            nodes=template.nodes,
            connections=template.connections,
            trigger_type="manual",
            trigger_config=template.default_config.get("trigger_config", {}),
            execution_config=template.default_config.get("execution_config", {}),
            notification_config=template.default_config.get("notification_config", {}),
        )
        
        # 更新模板使用次数
        template.usage_count += 1
        await template.save()
        
        logger.info(f"使用模板 {template.code} 创建工作流: {wf.code}")
        
        formatter = create_formatter()
        return formatter.success(
            data={"id": wf.id, "code": wf.code},
            message="工作流创建成功"
        )
        
    except Exception as e:
        logger.error(f"使用模板创建工作流失败: {str(e)}", exc_info=True)
        formatter = create_formatter()
        return formatter.error(message="使用模板创建工作流失败")


@router.post("/templates", summary="创建工作流模板")
async def create_workflow_template_new(template_data: WorkflowTemplateCreate):
    """创建工作流模板"""
    try:
        code = template_data.code or generate_workflow_code(f"tpl_{template_data.name}")
        
        existing = await WorkflowTemplate.get_or_none(code=code)
        if existing:
            formatter = create_formatter()
            return formatter.error(message=f"模板代码 {code} 已存在", code=400)
        
        template = await WorkflowTemplate.create(
            name=template_data.name,
            code=code,
            description=template_data.description,
            type=template_data.type,
            category=template_data.category,
            nodes=template_data.nodes,
            connections=template_data.connections,
            default_config=template_data.default_config or {},
        )
        
        logger.info(f"创建工作流模板成功: {template.code}")
        
        formatter = create_formatter()
        return formatter.success(
            data={"id": template.id, "code": template.code},
            message="创建模板成功"
        )
        
    except Exception as e:
        logger.error(f"创建模板失败: {str(e)}", exc_info=True)
        formatter = create_formatter()
        return formatter.error(message="创建模板失败")


# =====================================================
# 工作流详情 API
# =====================================================

@router.get("/{workflow_id}", summary="获取工作流详情")
async def get_workflow(workflow_id: int):
    """获取工作流详情"""
    try:
        wf = await Workflow.get_or_none(id=workflow_id)
        if not wf:
            formatter = create_formatter()
            return formatter.error(message="工作流不存在", code=404)
        
        data = {
            "id": wf.id,
            "name": wf.name,
            "code": wf.code,
            "description": wf.description,
            "type": wf.type,
            "type_label": WORKFLOW_TYPES.get(wf.type, wf.type),
            "category": wf.category,
            "priority": wf.priority,
            "priority_label": WORKFLOW_PRIORITIES.get(wf.priority, wf.priority),
            "nodes": wf.nodes,
            "connections": wf.connections,
            "trigger_type": wf.trigger_type,
            "trigger_type_label": TRIGGER_TYPES.get(wf.trigger_type, wf.trigger_type),
            "trigger_config": wf.trigger_config,
            "execution_config": wf.execution_config,
            "notification_config": wf.notification_config,
            "related_device_types": wf.related_device_types,
            "related_alarm_rules": wf.related_alarm_rules,
            "is_active": wf.is_active,
            "is_published": wf.is_published,
            "version": wf.version,
            "accent_color": getattr(wf, "accent_color", None),
            "timeout_seconds": wf.timeout_seconds,
            "retry_count": wf.retry_count,
            "retry_interval": wf.retry_interval,
            "execution_count": wf.execution_count,
            "success_count": wf.success_count,
            "failure_count": wf.failure_count,
            "last_executed_at": wf.last_executed_at.isoformat() if wf.last_executed_at else None,
            "created_by": wf.created_by,
            "created_by_name": wf.created_by_name,
            "updated_by": wf.updated_by,
            "updated_by_name": wf.updated_by_name,
            "published_by": wf.published_by,
            "published_at": wf.published_at.isoformat() if wf.published_at else None,
            "created_at": wf.created_at.isoformat() if wf.created_at else None,
            "updated_at": wf.updated_at.isoformat() if wf.updated_at else None,
        }
        
        formatter = create_formatter()
        return formatter.success(data=data, message="获取工作流详情成功")
        
    except Exception as e:
        logger.error(f"获取工作流详情失败: {str(e)}", exc_info=True)
        formatter = create_formatter()
        return formatter.error(message="获取工作流详情失败")


def generate_workflow_code(name: str) -> str:
    """生成工作流代码"""
    import re
    import time
    # 移除特殊字符，转换为小写
    base = re.sub(r'[^a-zA-Z0-9]', '_', name.lower())[:20]
    timestamp = int(time.time() * 1000) % 100000
    return f"wf_{base}_{timestamp}"


@router.post("", summary="创建工作流")
async def create_workflow(workflow_data: WorkflowCreate):
    """创建工作流"""
    try:
        # 生成工作流代码
        code = workflow_data.code or generate_workflow_code(workflow_data.name)
        
        # 检查代码是否已存在
        existing = await Workflow.get_or_none(code=code)
        if existing:
            formatter = create_formatter()
            return formatter.error(message=f"工作流代码 {code} 已存在", code=400)
        
        # 创建工作流
        wf = await Workflow.create(
            name=workflow_data.name,
            code=code,
            description=workflow_data.description,
            type=workflow_data.type,
            category=workflow_data.category,
            priority=workflow_data.priority,
            nodes=workflow_data.nodes or [],
            connections=workflow_data.connections or [],
            trigger_type=workflow_data.trigger_type,
            trigger_config=workflow_data.trigger_config or {},
            execution_config=workflow_data.execution_config or {},
            notification_config=workflow_data.notification_config or {},
            related_device_types=workflow_data.related_device_types or [],
            related_alarm_rules=workflow_data.related_alarm_rules or [],
            is_active=workflow_data.is_active,
            accent_color=getattr(workflow_data, "accent_color", None),
        )
        
        logger.info(f"创建工作流成功: {wf.code}")
        
        formatter = create_formatter()
        return formatter.success(
            data={"id": wf.id, "code": wf.code},
            message="创建工作流成功"
        )
        
    except Exception as e:
        logger.error(f"创建工作流失败: {str(e)}", exc_info=True)
        formatter = create_formatter()
        return formatter.error(message="创建工作流失败")


@router.put("/{workflow_id}", summary="更新工作流")
async def update_workflow(workflow_id: int, workflow_data: WorkflowUpdate):
    """更新工作流"""
    try:
        wf = await Workflow.get_or_none(id=workflow_id)
        if not wf:
            formatter = create_formatter()
            return formatter.error(message="工作流不存在", code=404)
        
        # 更新字段
        update_data = workflow_data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(wf, key, value)
        
        wf.updated_at = datetime.now()
        await wf.save()
        
        logger.info(f"更新工作流成功: {wf.code}")
        
        formatter = create_formatter()
        return formatter.success(data={"id": wf.id}, message="更新工作流成功")
        
    except Exception as e:
        logger.error(f"更新工作流失败: {str(e)}", exc_info=True)
        formatter = create_formatter()
        return formatter.error(message="更新工作流失败")


@router.delete("/{workflow_id}", summary="删除工作流")
async def delete_workflow(workflow_id: int):
    """删除工作流"""
    try:
        wf = await Workflow.get_or_none(id=workflow_id)
        if not wf:
            formatter = create_formatter()
            return formatter.error(message="工作流不存在", code=404)
        
        code = wf.code
        await wf.delete()
        
        logger.info(f"删除工作流成功: {code}")
        
        formatter = create_formatter()
        return formatter.success(message="删除工作流成功")
        
    except Exception as e:
        logger.error(f"删除工作流失败: {str(e)}", exc_info=True)
        formatter = create_formatter()
        return formatter.error(message="删除工作流失败")


# =====================================================
# 工作流状态操作 API
# =====================================================

@router.put("/{workflow_id}/toggle", summary="启用/禁用工作流")
async def toggle_workflow(workflow_id: int):
    """切换工作流的启用状态"""
    try:
        wf = await Workflow.get_or_none(id=workflow_id)
        if not wf:
            formatter = create_formatter()
            return formatter.error(message="工作流不存在", code=404)
        
        wf.is_active = not wf.is_active
        wf.updated_at = datetime.now()
        await wf.save()
        
        status = "启用" if wf.is_active else "禁用"
        logger.info(f"工作流 {wf.code} 已{status}")
        
        formatter = create_formatter()
        return formatter.success(
            data={"id": wf.id, "is_active": wf.is_active},
            message=f"工作流已{status}"
        )
        
    except Exception as e:
        logger.error(f"切换工作流状态失败: {str(e)}", exc_info=True)
        formatter = create_formatter()
        return formatter.error(message="切换工作流状态失败")


@router.post("/{workflow_id}/publish", summary="发布工作流")
async def publish_workflow(workflow_id: int):
    """发布工作流"""
    try:
        wf = await Workflow.get_or_none(id=workflow_id)
        if not wf:
            formatter = create_formatter()
            return formatter.error(message="工作流不存在", code=404)
        
        # 验证工作流
        validation = validate_workflow_definition(wf.nodes, wf.connections)
        if not validation["is_valid"]:
            formatter = create_formatter()
            return formatter.error(
                message="工作流验证失败，无法发布",
                data={"errors": validation["errors"]}
            )
        
        wf.is_published = True
        wf.published_at = datetime.now()
        wf.updated_at = datetime.now()
        
        # 版本号递增
        version_parts = wf.version.split(".")
        version_parts[-1] = str(int(version_parts[-1]) + 1)
        wf.version = ".".join(version_parts)
        
        await wf.save()
        
        logger.info(f"工作流 {wf.code} 已发布，版本: {wf.version}")
        
        formatter = create_formatter()
        return formatter.success(
            data={"id": wf.id, "version": wf.version},
            message="工作流发布成功"
        )
        
    except Exception as e:
        logger.error(f"发布工作流失败: {str(e)}", exc_info=True)
        formatter = create_formatter()
        return formatter.error(message="发布工作流失败")


@router.post("/{workflow_id}/unpublish", summary="取消发布工作流")
async def unpublish_workflow(workflow_id: int):
    """取消发布工作流"""
    try:
        wf = await Workflow.get_or_none(id=workflow_id)
        if not wf:
            formatter = create_formatter()
            return formatter.error(message="工作流不存在", code=404)
        
        wf.is_published = False
        wf.updated_at = datetime.now()
        await wf.save()
        
        logger.info(f"工作流 {wf.code} 已取消发布")
        
        formatter = create_formatter()
        return formatter.success(message="工作流已取消发布")
        
    except Exception as e:
        logger.error(f"取消发布工作流失败: {str(e)}", exc_info=True)
        formatter = create_formatter()
        return formatter.error(message="取消发布工作流失败")


@router.post("/{workflow_id}/duplicate", summary="复制工作流")
async def duplicate_workflow(workflow_id: int):
    """复制工作流"""
    try:
        wf = await Workflow.get_or_none(id=workflow_id)
        if not wf:
            formatter = create_formatter()
            return formatter.error(message="工作流不存在", code=404)
        
        # 生成新代码
        new_code = generate_workflow_code(f"{wf.name}_copy")
        
        # 创建副本
        new_wf = await Workflow.create(
            name=f"{wf.name} (副本)",
            code=new_code,
            description=wf.description,
            type=wf.type,
            category=wf.category,
            priority=wf.priority,
            nodes=wf.nodes,
            connections=wf.connections,
            trigger_type=wf.trigger_type,
            trigger_config=wf.trigger_config,
            execution_config=wf.execution_config,
            notification_config=wf.notification_config,
            related_device_types=wf.related_device_types,
            related_alarm_rules=wf.related_alarm_rules,
            is_active=False,
            is_published=False,
        )
        
        logger.info(f"复制工作流成功: {wf.code} -> {new_wf.code}")
        
        formatter = create_formatter()
        return formatter.success(
            data={"id": new_wf.id, "code": new_wf.code},
            message="复制工作流成功"
        )
        
    except Exception as e:
        logger.error(f"复制工作流失败: {str(e)}", exc_info=True)
        formatter = create_formatter()
        return formatter.error(message="复制工作流失败")


# =====================================================
# 工作流设计 API
# =====================================================

@router.put("/{workflow_id}/design", summary="保存工作流设计")
async def save_workflow_design(workflow_id: int, design_data: WorkflowDesignSave):
    """保存工作流设计（节点和连接）"""
    try:
        wf = await Workflow.get_or_none(id=workflow_id)
        if not wf:
            formatter = create_formatter()
            return formatter.error(message="工作流不存在", code=404)
        
        wf.nodes = design_data.nodes
        wf.connections = design_data.connections
        wf.updated_at = datetime.now()
        await wf.save()
        
        logger.info(f"保存工作流设计成功: {wf.code}")
        
        formatter = create_formatter()
        return formatter.success(
            data={
                "id": wf.id,
                "node_count": len(design_data.nodes),
                "connection_count": len(design_data.connections)
            },
            message="保存工作流设计成功"
        )
        
    except Exception as e:
        logger.error(f"保存工作流设计失败: {str(e)}", exc_info=True)
        formatter = create_formatter()
        return formatter.error(message="保存工作流设计失败")


@router.post("/{workflow_id}/validate", summary="验证工作流")
async def validate_workflow(workflow_id: int):
    """验证工作流定义是否有效"""
    try:
        wf = await Workflow.get_or_none(id=workflow_id)
        if not wf:
            formatter = create_formatter()
            return formatter.error(message="工作流不存在", code=404)
        
        result = validate_workflow_definition(wf.nodes, wf.connections)
        
        formatter = create_formatter()
        return formatter.success(data=result, message="验证完成")
        
    except Exception as e:
        logger.error(f"验证工作流失败: {str(e)}", exc_info=True)
        formatter = create_formatter()
        return formatter.error(message="验证工作流失败")


def validate_workflow_definition(nodes: list, connections: list) -> dict:
    """验证工作流定义"""
    errors = []
    warnings = []
    
    node_ids = {node.get("id") for node in nodes}
    node_types = {node.get("id"): node.get("type") for node in nodes}
    
    # 检查是否有开始节点
    has_start = any(node.get("type") == "start" for node in nodes)
    if not has_start:
        errors.append("工作流缺少开始节点")
    
    # 检查是否有结束节点
    has_end = any(node.get("type") == "end" for node in nodes)
    if not has_end:
        errors.append("工作流缺少结束节点")
    
    # 检查开始节点数量
    start_count = sum(1 for node in nodes if node.get("type") == "start")
    if start_count > 1:
        errors.append("工作流只能有一个开始节点")
    
    # 检查连接的有效性
    for conn in connections:
        from_id = conn.get("fromNodeId") or conn.get("from_node_id")
        to_id = conn.get("toNodeId") or conn.get("to_node_id")
        
        if from_id not in node_ids:
            errors.append(f"连接的源节点 {from_id} 不存在")
        if to_id not in node_ids:
            errors.append(f"连接的目标节点 {to_id} 不存在")
    
    # 检查孤立节点
    connected_nodes = set()
    for conn in connections:
        from_id = conn.get("fromNodeId") or conn.get("from_node_id")
        to_id = conn.get("toNodeId") or conn.get("to_node_id")
        connected_nodes.add(from_id)
        connected_nodes.add(to_id)
    
    for node in nodes:
        node_id = node.get("id")
        node_type = node.get("type")
        if node_id not in connected_nodes and node_type not in ["start", "end"]:
            warnings.append(f"节点 {node.get('name', node_id)} 未连接到任何其他节点")
    
    return {
        "is_valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "node_count": len(nodes),
        "connection_count": len(connections),
        "has_start_node": has_start,
        "has_end_node": has_end
    }


# =====================================================
# 工作流执行 API
# =====================================================

@router.post("/{workflow_id}/execute", summary="执行工作流")
async def execute_workflow(workflow_id: int, request: WorkflowExecuteRequest):
    """执行工作流"""
    try:
        from app.services.workflow_engine import get_workflow_engine
        
        wf = await Workflow.get_or_none(id=workflow_id)
        if not wf:
            formatter = create_formatter()
            return formatter.error(message="工作流不存在", code=404)
        
        if not wf.is_active:
            formatter = create_formatter()
            return formatter.error(message="工作流未启用", code=400)
        
        if not wf.is_published:
            formatter = create_formatter()
            return formatter.error(message="工作流未发布", code=400)
        
        # 验证工作流
        validation = validate_workflow_definition(wf.nodes, wf.connections)
        if not validation["is_valid"]:
            formatter = create_formatter()
            return formatter.error(
                message="工作流验证失败，无法执行",
                data={"errors": validation["errors"]}
            )
        
        # 获取执行引擎
        engine = get_workflow_engine()
        
        if request.async_mode:
            # 异步执行 - 使用asyncio.create_task
            import asyncio
            
            # 先创建执行记录返回给前端
            execution_id = f"exec_{uuid.uuid4().hex[:16]}"
            execution = await WorkflowExecution.create(
                workflow=wf,
                execution_id=execution_id,
                status="running",
                trigger_type="manual",
                trigger_data=request.trigger_data or {},
                context=request.variables or {},
                variables=request.variables or {},
                started_at=datetime.now(),
            )
            
            # 创建后台任务执行工作流
            async def run_workflow():
                try:
                    await engine.execute(
                        workflow=wf,
                        context=request.variables or {},
                        trigger_type="manual",
                        trigger_data=request.trigger_data,
                    )
                except Exception as e:
                    logger.error(f"异步执行工作流失败: {e}")
            
            asyncio.create_task(run_workflow())
            
            logger.info(f"工作流 {wf.code} 开始异步执行: {execution_id}")
            
            formatter = create_formatter()
            return formatter.success(
                data={
                    "execution_id": execution_id,
                    "status": "running",
                    "message": "工作流已开始执行"
                },
                message="工作流执行已启动"
            )
        else:
            # 同步执行 - 使用执行引擎
            execution = await engine.execute(
                workflow=wf,
                context=request.variables or {},
                trigger_type="manual",
                trigger_data=request.trigger_data,
            )
            
            result = {
                "execution_id": execution.execution_id,
                "status": execution.status,
                "started_at": execution.started_at.isoformat() if execution.started_at else None,
                "completed_at": execution.completed_at.isoformat() if execution.completed_at else None,
                "duration_ms": execution.duration_ms,
                "result": execution.result,
                "error_message": execution.error_message,
            }
            
            formatter = create_formatter()
            if execution.status == "success":
                return formatter.success(data=result, message="工作流执行完成")
            else:
                return formatter.error(
                    message=f"工作流执行失败: {execution.error_message}",
                    data=result
                )
        
    except Exception as e:
        logger.error(f"执行工作流失败: {str(e)}", exc_info=True)
        formatter = create_formatter()
        return formatter.error(message=f"执行工作流失败: {str(e)}")


async def execute_workflow_sync(workflow: Workflow, execution: WorkflowExecution) -> dict:
    """同步执行工作流"""
    import time
    start_time = time.time()
    
    try:
        execution.status = "running"
        execution.started_at = datetime.now()
        await execution.save()
        
        nodes = workflow.nodes
        connections = workflow.connections
        
        # 找到开始节点
        start_node = next((n for n in nodes if n.get("type") == "start"), None)
        if not start_node:
            raise ValueError("工作流缺少开始节点")
        
        # 执行节点
        current_node_id = start_node.get("id")
        node_states = {}
        
        while current_node_id:
            node = next((n for n in nodes if n.get("id") == current_node_id), None)
            if not node:
                break
            
            # 记录节点执行
            node_execution = await WorkflowNodeExecution.create(
                execution=execution,
                node_id=current_node_id,
                node_type=node.get("type"),
                node_name=node.get("name"),
                status="running",
                started_at=datetime.now(),
                input_data=execution.variables,
            )
            
            # 执行节点逻辑
            try:
                output = await execute_node(node, execution.variables)
                node_execution.status = "success"
                node_execution.output_data = output
                node_states[current_node_id] = {"status": "success", "output": output}
                
                # 更新变量
                if output:
                    execution.variables.update(output)
                    
            except Exception as node_error:
                node_execution.status = "failed"
                node_execution.error_message = str(node_error)
                node_states[current_node_id] = {"status": "failed", "error": str(node_error)}
                raise
            finally:
                node_execution.completed_at = datetime.now()
                node_execution.duration_ms = int((time.time() - start_time) * 1000)
                await node_execution.save()
            
            # 如果是结束节点，退出
            if node.get("type") == "end":
                break
            
            # 找下一个节点
            next_conn = next(
                (c for c in connections if (c.get("fromNodeId") or c.get("from_node_id")) == current_node_id),
                None
            )
            current_node_id = (next_conn.get("toNodeId") or next_conn.get("to_node_id")) if next_conn else None
        
        # 执行成功
        execution.status = "success"
        execution.completed_at = datetime.now()
        execution.duration_ms = int((time.time() - start_time) * 1000)
        execution.node_states = node_states
        execution.result = {"variables": execution.variables}
        await execution.save()
        
        # 更新工作流成功计数
        workflow.success_count += 1
        await workflow.save()
        
        return {
            "execution_id": execution.execution_id,
            "status": "success",
            "duration_ms": execution.duration_ms,
            "result": execution.result
        }
        
    except Exception as e:
        execution.status = "failed"
        execution.completed_at = datetime.now()
        execution.duration_ms = int((time.time() - start_time) * 1000)
        execution.error_message = str(e)
        await execution.save()
        
        # 更新工作流失败计数
        workflow.failure_count += 1
        await workflow.save()
        
        return {
            "execution_id": execution.execution_id,
            "status": "failed",
            "duration_ms": execution.duration_ms,
            "error": str(e)
        }


async def execute_node(node: dict, variables: dict) -> dict:
    """执行单个节点"""
    node_type = node.get("type")
    properties = node.get("properties", {})
    
    if node_type == "start":
        return {"started": True}
    
    elif node_type == "end":
        return {"completed": True}
    
    elif node_type == "process":
        # 处理节点 - 执行自定义逻辑
        return {"processed": True}
    
    elif node_type == "condition":
        # 条件判断节点
        condition = properties.get("condition", "true")
        # 简单的条件评估
        result = eval(condition, {"__builtins__": {}}, variables)
        return {"condition_result": bool(result)}
    
    elif node_type == "delay":
        # 延时节点
        import asyncio
        delay_time = properties.get("delayTime", 1)
        await asyncio.sleep(delay_time)
        return {"delayed": delay_time}
    
    elif node_type == "api":
        # API调用节点
        import aiohttp
        url = properties.get("apiUrl")
        method = properties.get("method", "GET")
        
        if url:
            async with aiohttp.ClientSession() as session:
                async with session.request(method, url) as response:
                    return {"status_code": response.status, "response": await response.text()}
        return {"error": "No URL specified"}
    
    elif node_type == "database":
        # 数据库操作节点 - 需要根据实际情况实现
        return {"db_operation": "executed"}
    
    else:
        return {"node_type": node_type, "executed": True}


# =====================================================
# 执行记录 API
# =====================================================

@router.get("/{workflow_id}/executions", summary="获取工作流执行记录")
async def get_workflow_executions(
    workflow_id: int,
    status: Optional[str] = Query(None, description="执行状态"),
    pagination: dict = Depends(get_pagination_params)
):
    """获取工作流的执行记录列表"""
    try:
        wf = await Workflow.get_or_none(id=workflow_id)
        if not wf:
            formatter = create_formatter()
            return formatter.error(message="工作流不存在", code=404)
        
        query = WorkflowExecution.filter(workflow=wf)
        
        if status:
            query = query.filter(status=status)
        
        total = await query.count()
        executions = await query.offset(pagination["offset"]).limit(pagination["limit"]).order_by("-created_at")
        
        items = []
        for exec in executions:
            items.append({
                "id": exec.id,
                "execution_id": exec.execution_id,
                "status": exec.status,
                "trigger_type": exec.trigger_type,
                "triggered_by_name": exec.triggered_by_name,
                "started_at": exec.started_at.isoformat() if exec.started_at else None,
                "completed_at": exec.completed_at.isoformat() if exec.completed_at else None,
                "duration_ms": exec.duration_ms,
                "error_message": exec.error_message,
                "created_at": exec.created_at.isoformat() if exec.created_at else None,
            })
        
        paginated = create_pagination_response(
            data=items,
            total=total,
            page=pagination["page"],
            page_size=pagination["page_size"]
        )
        
        formatter = create_formatter()
        return formatter.success(data=paginated, message="获取执行记录成功")
        
    except Exception as e:
        logger.error(f"获取执行记录失败: {str(e)}", exc_info=True)
        formatter = create_formatter()
        return formatter.error(message="获取执行记录失败")


@router.get("/executions/{execution_id}", summary="获取执行详情")
async def get_execution_detail(execution_id: str):
    """获取执行详情"""
    try:
        execution = await WorkflowExecution.get_or_none(execution_id=execution_id).prefetch_related("workflow")
        if not execution:
            formatter = create_formatter()
            return formatter.error(message="执行记录不存在", code=404)
        
        # 获取节点执行记录
        node_executions = await WorkflowNodeExecution.filter(execution=execution).order_by("created_at")
        
        data = {
            "id": execution.id,
            "execution_id": execution.execution_id,
            "workflow_id": execution.workflow.id,
            "workflow_name": execution.workflow.name,
            "workflow_code": execution.workflow.code,
            "status": execution.status,
            "trigger_type": execution.trigger_type,
            "trigger_data": execution.trigger_data,
            "triggered_by": execution.triggered_by,
            "triggered_by_name": execution.triggered_by_name,
            "started_at": execution.started_at.isoformat() if execution.started_at else None,
            "completed_at": execution.completed_at.isoformat() if execution.completed_at else None,
            "duration_ms": execution.duration_ms,
            "result": execution.result,
            "error_message": execution.error_message,
            "node_states": execution.node_states,
            "variables": execution.variables,
            "node_executions": [
                {
                    "node_id": ne.node_id,
                    "node_type": ne.node_type,
                    "node_name": ne.node_name,
                    "status": ne.status,
                    "started_at": ne.started_at.isoformat() if ne.started_at else None,
                    "completed_at": ne.completed_at.isoformat() if ne.completed_at else None,
                    "duration_ms": ne.duration_ms,
                    "input_data": ne.input_data,
                    "output_data": ne.output_data,
                    "error_message": ne.error_message,
                }
                for ne in node_executions
            ],
            "created_at": execution.created_at.isoformat() if execution.created_at else None,
        }
        
        formatter = create_formatter()
        return formatter.success(data=data, message="获取执行详情成功")
        
    except Exception as e:
        logger.error(f"获取执行详情失败: {str(e)}", exc_info=True)
        formatter = create_formatter()
        return formatter.error(message="获取执行详情失败")


@router.post("/executions/{execution_id}/cancel", summary="取消执行")
async def cancel_execution(execution_id: str):
    """取消正在执行的工作流"""
    try:
        execution = await WorkflowExecution.get_or_none(execution_id=execution_id)
        if not execution:
            formatter = create_formatter()
            return formatter.error(message="执行记录不存在", code=404)
        
        if execution.status not in ["pending", "running"]:
            formatter = create_formatter()
            return formatter.error(message="只能取消待执行或执行中的工作流", code=400)
        
        execution.status = "cancelled"
        execution.completed_at = datetime.now()
        await execution.save()
        
        logger.info(f"执行已取消: {execution_id}")
        
        formatter = create_formatter()
        return formatter.success(message="执行已取消")
        
    except Exception as e:
        logger.error(f"取消执行失败: {str(e)}", exc_info=True)
        formatter = create_formatter()
        return formatter.error(message="取消执行失败")


@router.post("/{workflow_id}/save-as-template", summary="将工作流保存为模板")
async def save_workflow_as_template(
    workflow_id: int,
    name: str = Query(..., description="模板名称"),
    description: Optional[str] = Query(None, description="模板描述")
):
    """将现有工作流保存为模板"""
    try:
        wf = await Workflow.get_or_none(id=workflow_id)
        if not wf:
            formatter = create_formatter()
            return formatter.error(message="工作流不存在", code=404)
        
        code = generate_workflow_code(f"tpl_{name}")
        
        template = await WorkflowTemplate.create(
            name=name,
            code=code,
            description=description or wf.description,
            type=wf.type,
            category=wf.category,
            nodes=wf.nodes,
            connections=wf.connections,
            default_config={
                "trigger_config": wf.trigger_config,
                "execution_config": wf.execution_config,
                "notification_config": wf.notification_config,
            },
        )
        
        logger.info(f"工作流 {wf.code} 保存为模板: {template.code}")
        
        formatter = create_formatter()
        return formatter.success(
            data={"id": template.id, "code": template.code},
            message="保存为模板成功"
        )
        
    except Exception as e:
        logger.error(f"保存为模板失败: {str(e)}", exc_info=True)
        formatter = create_formatter()
        return formatter.error(message="保存为模板失败")


# =====================================================
# 导入导出 API
# =====================================================

@router.get("/{workflow_id}/export", summary="导出工作流")
async def export_workflow(workflow_id: int):
    """导出工作流为JSON格式"""
    try:
        wf = await Workflow.get_or_none(id=workflow_id)
        if not wf:
            formatter = create_formatter()
            return formatter.error(message="工作流不存在", code=404)
        
        export_data = {
            "name": wf.name,
            "code": wf.code,
            "description": wf.description,
            "type": wf.type,
            "category": wf.category,
            "priority": wf.priority,
            "nodes": wf.nodes,
            "connections": wf.connections,
            "trigger_type": wf.trigger_type,
            "trigger_config": wf.trigger_config,
            "execution_config": wf.execution_config,
            "notification_config": wf.notification_config,
            "related_device_types": wf.related_device_types,
            "related_alarm_rules": wf.related_alarm_rules,
            "version": wf.version,
            "exported_at": datetime.now().isoformat(),
            "export_version": "1.0"
        }
        
        formatter = create_formatter()
        return formatter.success(data=export_data, message="导出成功")
        
    except Exception as e:
        logger.error(f"导出工作流失败: {str(e)}", exc_info=True)
        formatter = create_formatter()
        return formatter.error(message="导出工作流失败")


class WorkflowImportData(BaseModel):
    """导入工作流数据"""
    name: str
    description: Optional[str] = None
    type: str = "custom"
    category: Optional[str] = None
    priority: str = "medium"
    nodes: List[dict] = []
    connections: List[dict] = []
    trigger_type: str = "manual"
    trigger_config: Optional[dict] = None
    execution_config: Optional[dict] = None
    notification_config: Optional[dict] = None
    related_device_types: Optional[List[str]] = None
    related_alarm_rules: Optional[List[int]] = None


@router.post("/import", summary="导入工作流")
async def import_workflow(import_data: WorkflowImportData):
    """从JSON数据导入工作流"""
    try:
        # 生成新代码
        code = generate_workflow_code(import_data.name)
        
        # 创建工作流
        wf = await Workflow.create(
            name=import_data.name,
            code=code,
            description=import_data.description,
            type=import_data.type,
            category=import_data.category,
            priority=import_data.priority,
            nodes=import_data.nodes,
            connections=import_data.connections,
            trigger_type=import_data.trigger_type,
            trigger_config=import_data.trigger_config or {},
            execution_config=import_data.execution_config or {},
            notification_config=import_data.notification_config or {},
            related_device_types=import_data.related_device_types or [],
            related_alarm_rules=import_data.related_alarm_rules or [],
            is_active=False,  # 导入后默认禁用
            is_published=False,
        )
        
        logger.info(f"导入工作流成功: {wf.code}")
        
        formatter = create_formatter()
        return formatter.success(
            data={"id": wf.id, "code": wf.code},
            message="导入工作流成功"
        )
        
    except Exception as e:
        logger.error(f"导入工作流失败: {str(e)}", exc_info=True)
        formatter = create_formatter()
        return formatter.error(message="导入工作流失败")


# =====================================================
# 版本管理 API
# =====================================================

from app.models.workflow import WorkflowVersion


@router.get("/{workflow_id}/versions", summary="获取工作流版本历史")
async def get_workflow_versions(
    workflow_id: int,
    pagination: dict = Depends(get_pagination_params)
):
    """获取工作流的版本历史列表"""
    try:
        wf = await Workflow.get_or_none(id=workflow_id)
        if not wf:
            formatter = create_formatter()
            return formatter.error(message="工作流不存在", code=404)
        
        query = WorkflowVersion.filter(workflow_id=workflow_id)
        total = await query.count()
        versions = await query.offset(pagination["offset"]).limit(pagination["limit"]).order_by("-created_at")
        
        items = []
        for v in versions:
            items.append({
                "id": v.id,
                "version": v.version,
                "version_name": v.version_name,
                "description": v.description,
                "change_type": v.change_type,
                "change_summary": v.change_summary,
                "is_published": v.is_published,
                "is_current": v.is_current,
                "node_count": len(v.snapshot.get("nodes", [])) if v.snapshot else 0,
                "connection_count": len(v.snapshot.get("connections", [])) if v.snapshot else 0,
                "created_by_name": v.created_by_name,
                "created_at": v.created_at.isoformat() if v.created_at else None,
            })
        
        paginated = create_pagination_response(
            data=items,
            total=total,
            page=pagination["page"],
            page_size=pagination["page_size"]
        )
        
        formatter = create_formatter()
        return formatter.success(data=paginated, message=f"获取版本历史成功，共{total}条")
        
    except Exception as e:
        logger.error(f"获取版本历史失败: {str(e)}", exc_info=True)
        formatter = create_formatter()
        return formatter.error(message="获取版本历史失败")


@router.get("/{workflow_id}/versions/{version_id}", summary="获取版本详情")
async def get_workflow_version_detail(workflow_id: int, version_id: int):
    """获取工作流版本详情"""
    try:
        version = await WorkflowVersion.get_or_none(id=version_id, workflow_id=workflow_id)
        if not version:
            formatter = create_formatter()
            return formatter.error(message="版本不存在", code=404)
        
        data = {
            "id": version.id,
            "workflow_id": version.workflow_id,
            "version": version.version,
            "version_name": version.version_name,
            "description": version.description,
            "snapshot": version.snapshot,
            "change_type": version.change_type,
            "change_summary": version.change_summary,
            "is_published": version.is_published,
            "is_current": version.is_current,
            "created_by": version.created_by,
            "created_by_name": version.created_by_name,
            "created_at": version.created_at.isoformat() if version.created_at else None,
        }
        
        formatter = create_formatter()
        return formatter.success(data=data, message="获取版本详情成功")
        
    except Exception as e:
        logger.error(f"获取版本详情失败: {str(e)}", exc_info=True)
        formatter = create_formatter()
        return formatter.error(message="获取版本详情失败")


class CreateVersionRequest(BaseModel):
    """创建版本请求"""
    version_name: Optional[str] = Field(None, description="版本名称")
    description: Optional[str] = Field(None, description="版本描述")
    change_summary: Optional[str] = Field(None, description="变更摘要")


@router.post("/{workflow_id}/versions", summary="创建版本快照")
async def create_workflow_version(workflow_id: int, request: CreateVersionRequest):
    """为工作流创建版本快照"""
    try:
        wf = await Workflow.get_or_none(id=workflow_id)
        if not wf:
            formatter = create_formatter()
            return formatter.error(message="工作流不存在", code=404)
        
        # 将之前的当前版本标记为非当前
        await WorkflowVersion.filter(workflow_id=workflow_id, is_current=True).update(is_current=False)
        
        # 创建快照
        snapshot = {
            "name": wf.name,
            "description": wf.description,
            "type": wf.type,
            "category": wf.category,
            "priority": wf.priority,
            "nodes": wf.nodes,
            "connections": wf.connections,
            "trigger_type": wf.trigger_type,
            "trigger_config": wf.trigger_config,
            "execution_config": wf.execution_config,
            "notification_config": wf.notification_config,
            "related_device_types": wf.related_device_types,
            "related_alarm_rules": wf.related_alarm_rules,
        }
        
        # 创建版本记录
        version = await WorkflowVersion.create(
            workflow_id=workflow_id,
            version=wf.version,
            version_name=request.version_name or f"版本 {wf.version}",
            description=request.description,
            snapshot=snapshot,
            change_type="update",
            change_summary=request.change_summary,
            is_published=wf.is_published,
            is_current=True,
        )
        
        logger.info(f"创建工作流版本成功: {wf.code} v{wf.version}")
        
        formatter = create_formatter()
        return formatter.success(
            data={"id": version.id, "version": version.version},
            message="创建版本成功"
        )
        
    except Exception as e:
        logger.error(f"创建版本失败: {str(e)}", exc_info=True)
        formatter = create_formatter()
        return formatter.error(message="创建版本失败")


@router.post("/{workflow_id}/versions/{version_id}/rollback", summary="回滚到指定版本")
async def rollback_workflow_version(workflow_id: int, version_id: int):
    """回滚工作流到指定版本"""
    try:
        wf = await Workflow.get_or_none(id=workflow_id)
        if not wf:
            formatter = create_formatter()
            return formatter.error(message="工作流不存在", code=404)
        
        version = await WorkflowVersion.get_or_none(id=version_id, workflow_id=workflow_id)
        if not version:
            formatter = create_formatter()
            return formatter.error(message="版本不存在", code=404)
        
        snapshot = version.snapshot
        if not snapshot:
            formatter = create_formatter()
            return formatter.error(message="版本快照数据无效", code=400)
        
        # 先保存当前状态为新版本
        current_snapshot = {
            "name": wf.name,
            "description": wf.description,
            "type": wf.type,
            "category": wf.category,
            "priority": wf.priority,
            "nodes": wf.nodes,
            "connections": wf.connections,
            "trigger_type": wf.trigger_type,
            "trigger_config": wf.trigger_config,
            "execution_config": wf.execution_config,
            "notification_config": wf.notification_config,
            "related_device_types": wf.related_device_types,
            "related_alarm_rules": wf.related_alarm_rules,
        }
        
        # 将之前的当前版本标记为非当前
        await WorkflowVersion.filter(workflow_id=workflow_id, is_current=True).update(is_current=False)
        
        # 保存回滚前的版本
        await WorkflowVersion.create(
            workflow_id=workflow_id,
            version=wf.version,
            version_name=f"回滚前 {wf.version}",
            description=f"回滚到版本 {version.version} 前的状态",
            snapshot=current_snapshot,
            change_type="rollback",
            change_summary=f"回滚到版本 {version.version}",
            is_published=wf.is_published,
            is_current=False,
        )
        
        # 恢复工作流到指定版本
        wf.name = snapshot.get("name", wf.name)
        wf.description = snapshot.get("description")
        wf.type = snapshot.get("type", wf.type)
        wf.category = snapshot.get("category")
        wf.priority = snapshot.get("priority", wf.priority)
        wf.nodes = snapshot.get("nodes", [])
        wf.connections = snapshot.get("connections", [])
        wf.trigger_type = snapshot.get("trigger_type", wf.trigger_type)
        wf.trigger_config = snapshot.get("trigger_config", {})
        wf.execution_config = snapshot.get("execution_config", {})
        wf.notification_config = snapshot.get("notification_config", {})
        wf.related_device_types = snapshot.get("related_device_types", [])
        wf.related_alarm_rules = snapshot.get("related_alarm_rules", [])
        
        # 版本号递增
        version_parts = wf.version.split(".")
        version_parts[-1] = str(int(version_parts[-1]) + 1)
        wf.version = ".".join(version_parts)
        wf.updated_at = datetime.now()
        
        await wf.save()
        
        # 创建回滚后的版本记录
        await WorkflowVersion.create(
            workflow_id=workflow_id,
            version=wf.version,
            version_name=f"回滚自 {version.version}",
            description=f"从版本 {version.version} 回滚",
            snapshot=snapshot,
            change_type="rollback",
            change_summary=f"回滚自版本 {version.version}",
            is_published=False,
            is_current=True,
        )
        
        logger.info(f"工作流 {wf.code} 回滚到版本 {version.version}，新版本: {wf.version}")
        
        formatter = create_formatter()
        return formatter.success(
            data={"id": wf.id, "version": wf.version},
            message=f"回滚成功，当前版本: {wf.version}"
        )
        
    except Exception as e:
        logger.error(f"回滚版本失败: {str(e)}", exc_info=True)
        formatter = create_formatter()
        return formatter.error(message="回滚版本失败")


@router.get("/{workflow_id}/versions/compare", summary="对比两个版本")
async def compare_workflow_versions(
    workflow_id: int,
    version1_id: int = Query(..., description="版本1 ID"),
    version2_id: int = Query(..., description="版本2 ID")
):
    """对比两个工作流版本的差异"""
    try:
        version1 = await WorkflowVersion.get_or_none(id=version1_id, workflow_id=workflow_id)
        version2 = await WorkflowVersion.get_or_none(id=version2_id, workflow_id=workflow_id)
        
        if not version1 or not version2:
            formatter = create_formatter()
            return formatter.error(message="版本不存在", code=404)
        
        snapshot1 = version1.snapshot or {}
        snapshot2 = version2.snapshot or {}
        
        # 计算差异
        differences = {
            "version1": {
                "id": version1.id,
                "version": version1.version,
                "created_at": version1.created_at.isoformat() if version1.created_at else None,
            },
            "version2": {
                "id": version2.id,
                "version": version2.version,
                "created_at": version2.created_at.isoformat() if version2.created_at else None,
            },
            "changes": []
        }
        
        # 对比基本字段
        compare_fields = ["name", "description", "type", "category", "priority", "trigger_type"]
        for field in compare_fields:
            val1 = snapshot1.get(field)
            val2 = snapshot2.get(field)
            if val1 != val2:
                differences["changes"].append({
                    "field": field,
                    "type": "modified",
                    "old_value": val1,
                    "new_value": val2,
                })
        
        # 对比节点数量
        nodes1 = snapshot1.get("nodes", [])
        nodes2 = snapshot2.get("nodes", [])
        if len(nodes1) != len(nodes2):
            differences["changes"].append({
                "field": "nodes",
                "type": "count_changed",
                "old_value": len(nodes1),
                "new_value": len(nodes2),
            })
        
        # 对比连接数量
        conns1 = snapshot1.get("connections", [])
        conns2 = snapshot2.get("connections", [])
        if len(conns1) != len(conns2):
            differences["changes"].append({
                "field": "connections",
                "type": "count_changed",
                "old_value": len(conns1),
                "new_value": len(conns2),
            })
        
        # 对比节点详情
        node_ids1 = {n.get("id") for n in nodes1}
        node_ids2 = {n.get("id") for n in nodes2}
        
        added_nodes = node_ids2 - node_ids1
        removed_nodes = node_ids1 - node_ids2
        
        if added_nodes:
            differences["changes"].append({
                "field": "nodes",
                "type": "added",
                "value": list(added_nodes),
            })
        
        if removed_nodes:
            differences["changes"].append({
                "field": "nodes",
                "type": "removed",
                "value": list(removed_nodes),
            })
        
        differences["summary"] = {
            "total_changes": len(differences["changes"]),
            "nodes_added": len(added_nodes),
            "nodes_removed": len(removed_nodes),
        }
        
        formatter = create_formatter()
        return formatter.success(data=differences, message="版本对比完成")
        
    except Exception as e:
        logger.error(f"版本对比失败: {str(e)}", exc_info=True)
        formatter = create_formatter()
        return formatter.error(message="版本对比失败")


@router.delete("/{workflow_id}/versions/{version_id}", summary="删除版本")
async def delete_workflow_version(workflow_id: int, version_id: int):
    """删除工作流版本（不能删除当前版本）"""
    try:
        version = await WorkflowVersion.get_or_none(id=version_id, workflow_id=workflow_id)
        if not version:
            formatter = create_formatter()
            return formatter.error(message="版本不存在", code=404)
        
        if version.is_current:
            formatter = create_formatter()
            return formatter.error(message="不能删除当前版本", code=400)
        
        await version.delete()
        
        logger.info(f"删除工作流版本成功: workflow_id={workflow_id}, version={version.version}")
        
        formatter = create_formatter()
        return formatter.success(message="删除版本成功")
        
    except Exception as e:
        logger.error(f"删除版本失败: {str(e)}", exc_info=True)
        formatter = create_formatter()
        return formatter.error(message="删除版本失败")
