#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
报警记录管理 API v2
提供报警记录的查询和处理操作
"""

from typing import Optional, List
from datetime import datetime

from fastapi import APIRouter, Query, HTTPException, Depends
from pydantic import BaseModel, Field

from app.models.alarm import AlarmRule, AlarmRecord
from app.core.response_formatter_v2 import create_formatter
from app.core.pagination import get_pagination_params, create_pagination_response
from app.log import logger

router = APIRouter(tags=["报警记录管理"])


# =====================================================
# Pydantic 模型
# =====================================================

class AcknowledgeRequest(BaseModel):
    """确认报警请求"""
    notes: Optional[str] = Field(None, description="确认备注")


class ResolveRequest(BaseModel):
    """解决报警请求"""
    resolution_notes: Optional[str] = Field(None, description="解决备注")


class BatchHandleRequest(BaseModel):
    """批量处理请求"""
    record_ids: List[int] = Field(..., description="报警记录ID列表")
    action: str = Field(..., description="操作: acknowledge/resolve/close")
    notes: Optional[str] = Field(None, description="备注")


# =====================================================
# API 路由
# =====================================================

@router.get("", summary="获取报警记录列表")
async def get_alarm_records(
    device_code: Optional[str] = Query(None, description="设备编码"),
    device_type_code: Optional[str] = Query(None, description="设备类型代码"),
    alarm_level: Optional[str] = Query(None, description="报警级别"),
    status: Optional[str] = Query(None, description="状态"),
    rule_id: Optional[int] = Query(None, description="规则ID"),
    start_time: Optional[str] = Query(None, description="开始时间"),
    end_time: Optional[str] = Query(None, description="结束时间"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    pagination: dict = Depends(get_pagination_params)
):
    """获取报警记录列表"""
    try:
        query = AlarmRecord.all()
        
        if device_code:
            query = query.filter(device_code__icontains=device_code)
        if device_type_code:
            query = query.filter(device_type_code=device_type_code)
        if alarm_level:
            query = query.filter(alarm_level=alarm_level)
        if status:
            query = query.filter(status=status)
        if rule_id:
            query = query.filter(rule_id=rule_id)
        if start_time:
            query = query.filter(triggered_at__gte=start_time)
        if end_time:
            query = query.filter(triggered_at__lte=end_time)
        if search:
            query = query.filter(alarm_title__icontains=search)
        
        total = await query.count()
        records = await query.offset(pagination["offset"]).limit(pagination["limit"]).order_by("-triggered_at")
        
        # 转换为字典列表
        items = []
        for record in records:
            items.append({
                "id": record.id,
                "rule_id": record.rule_id,
                "device_id": record.device_id,
                "device_code": record.device_code,
                "device_name": record.device_name,
                "device_type_code": record.device_type_code,
                "alarm_code": record.alarm_code,
                "alarm_level": record.alarm_level,
                "alarm_title": record.alarm_title,
                "alarm_content": record.alarm_content,
                "field_code": record.field_code,
                "field_name": record.field_name,
                "trigger_value": float(record.trigger_value) if record.trigger_value else None,
                "threshold_value": record.threshold_value,
                "triggered_at": record.triggered_at.isoformat() if record.triggered_at else None,
                "recovered_at": record.recovered_at.isoformat() if record.recovered_at else None,
                "duration_seconds": record.duration_seconds,
                "status": record.status,
                "acknowledged_at": record.acknowledged_at.isoformat() if record.acknowledged_at else None,
                "acknowledged_by_name": record.acknowledged_by_name,
                "resolved_at": record.resolved_at.isoformat() if record.resolved_at else None,
                "resolved_by_name": record.resolved_by_name,
                "resolution_notes": record.resolution_notes,
                "created_at": record.created_at.isoformat() if record.created_at else None,
            })
        
        paginated = create_pagination_response(
            data=items,
            total=total,
            page=pagination["page"],
            page_size=pagination["page_size"]
        )
        
        formatter = create_formatter()
        return formatter.success(data=paginated, message=f"获取报警记录列表成功，共{total}条")
        
    except Exception as e:
        logger.error(f"获取报警记录列表失败: {str(e)}", exc_info=True)
        formatter = create_formatter()
        return formatter.error(message="获取报警记录列表失败")


@router.get("/statistics", summary="获取报警统计")
async def get_alarm_statistics(
    device_type_code: Optional[str] = Query(None, description="设备类型代码"),
    start_time: Optional[str] = Query(None, description="开始时间"),
    end_time: Optional[str] = Query(None, description="结束时间"),
):
    """获取报警统计数据"""
    try:
        from tortoise.functions import Count
        
        query = AlarmRecord.all()
        
        if device_type_code:
            query = query.filter(device_type_code=device_type_code)
        if start_time:
            query = query.filter(triggered_at__gte=start_time)
        if end_time:
            query = query.filter(triggered_at__lte=end_time)
        
        # 统计各状态数量
        total = await query.count()
        active = await query.filter(status="active").count()
        acknowledged = await query.filter(status="acknowledged").count()
        resolved = await query.filter(status="resolved").count()
        closed = await query.filter(status="closed").count()
        
        # 统计各级别数量
        warning = await query.filter(alarm_level="warning").count()
        critical = await query.filter(alarm_level="critical").count()
        emergency = await query.filter(alarm_level="emergency").count()
        
        data = {
            "total": total,
            "by_status": {
                "active": active,
                "acknowledged": acknowledged,
                "resolved": resolved,
                "closed": closed,
            },
            "by_level": {
                "warning": warning,
                "critical": critical,
                "emergency": emergency,
            }
        }
        
        formatter = create_formatter()
        return formatter.success(data=data, message="获取报警统计成功")
        
    except Exception as e:
        logger.error(f"获取报警统计失败: {str(e)}", exc_info=True)
        formatter = create_formatter()
        return formatter.error(message="获取报警统计失败")


@router.get("/{record_id}", summary="获取报警记录详情")
async def get_alarm_record(record_id: int):
    """获取报警记录详情"""
    try:
        record = await AlarmRecord.get_or_none(id=record_id).prefetch_related("rule")
        if not record:
            formatter = create_formatter()
            return formatter.error(message="报警记录不存在", code=404)
        
        data = {
            "id": record.id,
            "rule_id": record.rule_id,
            "rule": None,
            "device_id": record.device_id,
            "device_code": record.device_code,
            "device_name": record.device_name,
            "device_type_code": record.device_type_code,
            "alarm_code": record.alarm_code,
            "alarm_level": record.alarm_level,
            "alarm_title": record.alarm_title,
            "alarm_content": record.alarm_content,
            "field_code": record.field_code,
            "field_name": record.field_name,
            "trigger_value": float(record.trigger_value) if record.trigger_value else None,
            "threshold_value": record.threshold_value,
            "triggered_at": record.triggered_at.isoformat() if record.triggered_at else None,
            "recovered_at": record.recovered_at.isoformat() if record.recovered_at else None,
            "duration_seconds": record.duration_seconds,
            "status": record.status,
            "acknowledged_at": record.acknowledged_at.isoformat() if record.acknowledged_at else None,
            "acknowledged_by": record.acknowledged_by,
            "acknowledged_by_name": record.acknowledged_by_name,
            "resolved_at": record.resolved_at.isoformat() if record.resolved_at else None,
            "resolved_by": record.resolved_by,
            "resolved_by_name": record.resolved_by_name,
            "resolution_notes": record.resolution_notes,
            "notification_sent": record.notification_sent,
            "notification_channels": record.notification_channels,
            "created_at": record.created_at.isoformat() if record.created_at else None,
        }
        
        # 添加关联规则信息
        if record.rule:
            data["rule"] = {
                "id": record.rule.id,
                "rule_name": record.rule.rule_name,
                "rule_code": record.rule.rule_code,
            }
        
        formatter = create_formatter()
        return formatter.success(data=data, message="获取报警记录详情成功")
        
    except Exception as e:
        logger.error(f"获取报警记录详情失败: {str(e)}", exc_info=True)
        formatter = create_formatter()
        return formatter.error(message="获取报警记录详情失败")


@router.post("/{record_id}/acknowledge", summary="确认报警")
async def acknowledge_alarm(record_id: int, request: AcknowledgeRequest = None):
    """确认报警记录"""
    try:
        record = await AlarmRecord.get_or_none(id=record_id)
        if not record:
            formatter = create_formatter()
            return formatter.error(message="报警记录不存在", code=404)
        
        if record.status != "active":
            formatter = create_formatter()
            return formatter.error(message=f"当前状态({record.status})不允许确认操作", code=400)
        
        record.status = "acknowledged"
        record.acknowledged_at = datetime.now()
        record.acknowledged_by_name = "管理员"  # TODO: 从当前用户获取
        record.updated_at = datetime.now()
        await record.save()
        
        logger.info(f"报警记录 {record_id} 已确认")
        
        formatter = create_formatter()
        return formatter.success(data={"id": record.id, "status": record.status}, message="报警已确认")
        
    except Exception as e:
        logger.error(f"确认报警失败: {str(e)}", exc_info=True)
        formatter = create_formatter()
        return formatter.error(message="确认报警失败")


@router.post("/{record_id}/resolve", summary="解决报警")
async def resolve_alarm(record_id: int, request: ResolveRequest = None):
    """解决报警记录"""
    try:
        record = await AlarmRecord.get_or_none(id=record_id)
        if not record:
            formatter = create_formatter()
            return formatter.error(message="报警记录不存在", code=404)
        
        if record.status not in ["active", "acknowledged"]:
            formatter = create_formatter()
            return formatter.error(message=f"当前状态({record.status})不允许解决操作", code=400)
        
        record.status = "resolved"
        record.resolved_at = datetime.now()
        record.resolved_by_name = "管理员"  # TODO: 从当前用户获取
        if request and request.resolution_notes:
            record.resolution_notes = request.resolution_notes
        record.updated_at = datetime.now()
        
        # 计算持续时间
        if record.triggered_at:
            record.duration_seconds = int((datetime.now() - record.triggered_at).total_seconds())
        
        await record.save()
        
        logger.info(f"报警记录 {record_id} 已解决")
        
        formatter = create_formatter()
        return formatter.success(data={"id": record.id, "status": record.status}, message="报警已解决")
        
    except Exception as e:
        logger.error(f"解决报警失败: {str(e)}", exc_info=True)
        formatter = create_formatter()
        return formatter.error(message="解决报警失败")


@router.post("/{record_id}/close", summary="关闭报警")
async def close_alarm(record_id: int):
    """关闭报警记录"""
    try:
        record = await AlarmRecord.get_or_none(id=record_id)
        if not record:
            formatter = create_formatter()
            return formatter.error(message="报警记录不存在", code=404)
        
        record.status = "closed"
        record.updated_at = datetime.now()
        await record.save()
        
        logger.info(f"报警记录 {record_id} 已关闭")
        
        formatter = create_formatter()
        return formatter.success(data={"id": record.id, "status": record.status}, message="报警已关闭")
        
    except Exception as e:
        logger.error(f"关闭报警失败: {str(e)}", exc_info=True)
        formatter = create_formatter()
        return formatter.error(message="关闭报警失败")


@router.post("/batch-handle", summary="批量处理报警")
async def batch_handle_alarms(request: BatchHandleRequest):
    """批量处理报警记录"""
    try:
        action = request.action
        record_ids = request.record_ids
        
        if action not in ["acknowledge", "resolve", "close"]:
            formatter = create_formatter()
            return formatter.error(message="无效的操作类型", code=400)
        
        success_count = 0
        fail_count = 0
        
        for record_id in record_ids:
            try:
                record = await AlarmRecord.get_or_none(id=record_id)
                if not record:
                    fail_count += 1
                    continue
                
                now = datetime.now()
                
                if action == "acknowledge" and record.status == "active":
                    record.status = "acknowledged"
                    record.acknowledged_at = now
                    record.acknowledged_by_name = "管理员"
                elif action == "resolve" and record.status in ["active", "acknowledged"]:
                    record.status = "resolved"
                    record.resolved_at = now
                    record.resolved_by_name = "管理员"
                    if request.notes:
                        record.resolution_notes = request.notes
                    if record.triggered_at:
                        record.duration_seconds = int((now - record.triggered_at).total_seconds())
                elif action == "close":
                    record.status = "closed"
                else:
                    fail_count += 1
                    continue
                
                record.updated_at = now
                await record.save()
                success_count += 1
                
            except Exception as e:
                logger.error(f"处理报警记录 {record_id} 失败: {str(e)}")
                fail_count += 1
        
        formatter = create_formatter()
        return formatter.success(
            data={"success_count": success_count, "fail_count": fail_count},
            message=f"批量处理完成，成功{success_count}条，失败{fail_count}条"
        )
        
    except Exception as e:
        logger.error(f"批量处理报警失败: {str(e)}", exc_info=True)
        formatter = create_formatter()
        return formatter.error(message="批量处理报警失败")
