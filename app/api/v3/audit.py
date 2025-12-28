#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工业AI数据平台审计日志API
提供操作日志查询、安全事件管理和审计分析接口

需求映射：
- 需求10.3: 敏感数据访问审计
- 需求7.5: 模型生命周期操作审计
"""

from datetime import datetime, timedelta
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field

from app.services.platform_audit_service import (
    platform_audit_service,
    AuditActionType,
    AuditRiskLevel,
    SecurityEventType
)
from app.core.auth_dependencies import get_current_active_user
from app.models.admin import User
from app.core.unified_logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/audit", tags=["审计日志"])


# ==================== 响应模型 ====================

class AuditLogResponse(BaseModel):
    """审计日志响应"""
    id: int = Field(..., description="日志ID")
    user_id: Optional[int] = Field(None, description="用户ID")
    username: str = Field(..., description="用户名")
    user_ip: str = Field(..., description="用户IP")
    action_type: str = Field(..., description="操作类型")
    action_name: str = Field(..., description="操作名称")
    resource_type: str = Field(..., description="资源类型")
    resource_id: Optional[str] = Field(None, description="资源ID")
    permission_result: bool = Field(..., description="权限结果")
    risk_level: str = Field(..., description="风险等级")
    created_at: str = Field(..., description="创建时间")


class SecurityEventResponse(BaseModel):
    """安全事件响应"""
    id: int = Field(..., description="事件ID")
    event_type: str = Field(..., description="事件类型")
    event_level: str = Field(..., description="事件级别")
    event_title: str = Field(..., description="事件标题")
    event_description: str = Field(..., description="事件描述")
    user_id: Optional[int] = Field(None, description="用户ID")
    username: Optional[str] = Field(None, description="用户名")
    user_ip: Optional[str] = Field(None, description="用户IP")
    threat_score: int = Field(..., description="威胁评分")
    status: str = Field(..., description="状态")
    created_at: str = Field(..., description="创建时间")


class HandleEventRequest(BaseModel):
    """处理安全事件请求"""
    handle_note: str = Field(..., description="处理备注")


# ==================== 审计日志接口 ====================

@router.get("/logs", summary="查询审计日志")
async def get_audit_logs(
    user_id: Optional[int] = Query(None, description="用户ID"),
    action_type: Optional[str] = Query(None, description="操作类型"),
    resource_type: Optional[str] = Query(None, description="资源类型"),
    risk_level: Optional[str] = Query(None, description="风险等级"),
    start_time: Optional[datetime] = Query(None, description="开始时间"),
    end_time: Optional[datetime] = Query(None, description="结束时间"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(50, ge=1, le=100, description="每页大小"),
    current_user: User = Depends(get_current_active_user)
):
    """
    查询审计日志
    
    - 支持多条件过滤
    - 支持分页查询
    - 非管理员只能查看自己的日志
    """
    # 非管理员只能查看自己的日志
    if not current_user.is_superuser:
        user_id = current_user.id
    
    result = await platform_audit_service.get_audit_logs(
        user_id=user_id,
        action_type=action_type,
        resource_type=resource_type,
        risk_level=risk_level,
        start_time=start_time,
        end_time=end_time,
        page=page,
        page_size=page_size
    )
    
    return {
        "success": True,
        "message": "查询成功",
        "data": result,
        "timestamp": datetime.now().isoformat()
    }


@router.get("/logs/my", summary="查询我的操作日志")
async def get_my_audit_logs(
    action_type: Optional[str] = Query(None, description="操作类型"),
    start_time: Optional[datetime] = Query(None, description="开始时间"),
    end_time: Optional[datetime] = Query(None, description="结束时间"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(50, ge=1, le=100, description="每页大小"),
    current_user: User = Depends(get_current_active_user)
):
    """
    查询当前用户的操作日志
    """
    result = await platform_audit_service.get_audit_logs(
        user_id=current_user.id,
        action_type=action_type,
        start_time=start_time,
        end_time=end_time,
        page=page,
        page_size=page_size
    )
    
    return {
        "success": True,
        "message": "查询成功",
        "data": result,
        "timestamp": datetime.now().isoformat()
    }


@router.get("/logs/sensitive", summary="查询敏感操作日志")
async def get_sensitive_logs(
    start_time: Optional[datetime] = Query(None, description="开始时间"),
    end_time: Optional[datetime] = Query(None, description="结束时间"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(50, ge=1, le=100, description="每页大小"),
    current_user: User = Depends(get_current_active_user)
):
    """
    查询敏感操作日志
    
    - 需要管理员权限
    - 返回高风险和严重风险的操作日志
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限"
        )
    
    # 查询高风险和严重风险的日志
    high_risk_logs = await platform_audit_service.get_audit_logs(
        risk_level="HIGH",
        start_time=start_time,
        end_time=end_time,
        page=page,
        page_size=page_size
    )
    
    critical_logs = await platform_audit_service.get_audit_logs(
        risk_level="CRITICAL",
        start_time=start_time,
        end_time=end_time,
        page=page,
        page_size=page_size
    )
    
    # 合并结果
    all_logs = high_risk_logs['logs'] + critical_logs['logs']
    all_logs.sort(key=lambda x: x['created_at'], reverse=True)
    
    return {
        "success": True,
        "message": "查询成功",
        "data": {
            "total": high_risk_logs['total'] + critical_logs['total'],
            "page": page,
            "page_size": page_size,
            "logs": all_logs[:page_size]
        },
        "timestamp": datetime.now().isoformat()
    }


# ==================== 安全事件接口 ====================

@router.get("/events", summary="查询安全事件")
async def get_security_events(
    event_type: Optional[str] = Query(None, description="事件类型"),
    event_level: Optional[str] = Query(None, description="事件级别"),
    status: Optional[str] = Query(None, description="状态"),
    start_time: Optional[datetime] = Query(None, description="开始时间"),
    end_time: Optional[datetime] = Query(None, description="结束时间"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(50, ge=1, le=100, description="每页大小"),
    current_user: User = Depends(get_current_active_user)
):
    """
    查询安全事件
    
    - 需要管理员权限
    - 支持多条件过滤
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限"
        )
    
    result = await platform_audit_service.get_security_events(
        event_type=event_type,
        event_level=event_level,
        status=status,
        start_time=start_time,
        end_time=end_time,
        page=page,
        page_size=page_size
    )
    
    return {
        "success": True,
        "message": "查询成功",
        "data": result,
        "timestamp": datetime.now().isoformat()
    }


@router.get("/events/pending", summary="查询待处理安全事件")
async def get_pending_events(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(50, ge=1, le=100, description="每页大小"),
    current_user: User = Depends(get_current_active_user)
):
    """
    查询待处理的安全事件
    
    - 需要管理员权限
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限"
        )
    
    result = await platform_audit_service.get_security_events(
        status="PENDING",
        page=page,
        page_size=page_size
    )
    
    return {
        "success": True,
        "message": "查询成功",
        "data": result,
        "timestamp": datetime.now().isoformat()
    }


@router.post("/events/{event_id}/handle", summary="处理安全事件")
async def handle_security_event(
    event_id: int,
    handle_data: HandleEventRequest,
    current_user: User = Depends(get_current_active_user)
):
    """
    处理安全事件
    
    - 需要管理员权限
    - 更新事件状态为已处理
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限"
        )
    
    from app.models.audit_log import SecurityEvent
    
    event = await SecurityEvent.get_or_none(id=event_id)
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="安全事件不存在"
        )
    
    event.status = "HANDLED"
    event.handled_by = current_user.id
    event.handled_at = datetime.now()
    event.handle_note = handle_data.handle_note
    await event.save()
    
    # 记录处理操作
    await platform_audit_service.log_operation(
        user_id=current_user.id,
        username=current_user.username,
        action_type=AuditActionType.SYSTEM_CONFIG_CHANGE,
        resource_type="security_event",
        resource_id=str(event_id),
        success=True,
        extra_data={
            "action": "handle_event",
            "handle_note": handle_data.handle_note
        }
    )
    
    return {
        "success": True,
        "message": "安全事件已处理",
        "data": {
            "id": event.id,
            "status": event.status,
            "handled_by": event.handled_by,
            "handled_at": event.handled_at.isoformat()
        },
        "timestamp": datetime.now().isoformat()
    }


# ==================== 统计分析接口 ====================

@router.get("/statistics", summary="获取审计统计")
async def get_audit_statistics(
    start_time: Optional[datetime] = Query(None, description="开始时间"),
    end_time: Optional[datetime] = Query(None, description="结束时间"),
    current_user: User = Depends(get_current_active_user)
):
    """
    获取审计统计信息
    
    - 需要管理员权限
    - 返回操作统计、风险统计、安全事件统计
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限"
        )
    
    result = await platform_audit_service.get_audit_statistics(
        start_time=start_time,
        end_time=end_time
    )
    
    return {
        "success": True,
        "message": "获取统计成功",
        "data": result,
        "timestamp": datetime.now().isoformat()
    }


@router.get("/statistics/daily", summary="获取每日审计统计")
async def get_daily_statistics(
    days: int = Query(7, ge=1, le=30, description="统计天数"),
    current_user: User = Depends(get_current_active_user)
):
    """
    获取每日审计统计
    
    - 需要管理员权限
    - 返回最近N天的每日统计
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限"
        )
    
    daily_stats = []
    
    for i in range(days):
        day_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=i)
        day_end = day_start + timedelta(days=1)
        
        stats = await platform_audit_service.get_audit_statistics(
            start_time=day_start,
            end_time=day_end
        )
        
        daily_stats.append({
            "date": day_start.strftime("%Y-%m-%d"),
            "audit_logs": stats.get('audit_logs', {}).get('total', 0),
            "security_events": stats.get('security_events', {}).get('total', 0),
            "failed_operations": stats.get('audit_logs', {}).get('failed_operations', 0)
        })
    
    # 按日期排序
    daily_stats.sort(key=lambda x: x['date'])
    
    return {
        "success": True,
        "message": "获取每日统计成功",
        "data": daily_stats,
        "timestamp": datetime.now().isoformat()
    }


@router.get("/statistics/user/{user_id}", summary="获取用户审计统计")
async def get_user_statistics(
    user_id: int,
    start_time: Optional[datetime] = Query(None, description="开始时间"),
    end_time: Optional[datetime] = Query(None, description="结束时间"),
    current_user: User = Depends(get_current_active_user)
):
    """
    获取指定用户的审计统计
    
    - 管理员可以查看任何用户
    - 普通用户只能查看自己
    """
    if not current_user.is_superuser and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权查看其他用户的统计"
        )
    
    # 获取用户的审计日志
    logs = await platform_audit_service.get_audit_logs(
        user_id=user_id,
        start_time=start_time,
        end_time=end_time,
        page=1,
        page_size=1000
    )
    
    # 统计操作类型
    action_stats = {}
    risk_stats = {}
    
    for log in logs.get('logs', []):
        action_type = log.get('action_type', 'UNKNOWN')
        risk_level = log.get('risk_level', 'LOW')
        
        action_stats[action_type] = action_stats.get(action_type, 0) + 1
        risk_stats[risk_level] = risk_stats.get(risk_level, 0) + 1
    
    return {
        "success": True,
        "message": "获取用户统计成功",
        "data": {
            "user_id": user_id,
            "total_operations": logs.get('total', 0),
            "by_action_type": action_stats,
            "by_risk_level": risk_stats
        },
        "timestamp": datetime.now().isoformat()
    }


# ==================== 元数据接口 ====================

@router.get("/action-types", summary="获取操作类型列表")
async def get_action_types(
    current_user: User = Depends(get_current_active_user)
):
    """
    获取支持的审计操作类型列表
    """
    action_types = [
        {"key": action.value, "name": action.value}
        for action in AuditActionType
    ]
    
    return {
        "success": True,
        "message": "获取操作类型成功",
        "data": action_types,
        "timestamp": datetime.now().isoformat()
    }


@router.get("/risk-levels", summary="获取风险等级列表")
async def get_risk_levels(
    current_user: User = Depends(get_current_active_user)
):
    """
    获取支持的风险等级列表
    """
    risk_levels = [
        {
            "key": level.value,
            "name": {
                AuditRiskLevel.LOW: "低风险",
                AuditRiskLevel.MEDIUM: "中风险",
                AuditRiskLevel.HIGH: "高风险",
                AuditRiskLevel.CRITICAL: "严重风险"
            }.get(level, level.value)
        }
        for level in AuditRiskLevel
    ]
    
    return {
        "success": True,
        "message": "获取风险等级成功",
        "data": risk_levels,
        "timestamp": datetime.now().isoformat()
    }


@router.get("/event-types", summary="获取安全事件类型列表")
async def get_event_types(
    current_user: User = Depends(get_current_active_user)
):
    """
    获取支持的安全事件类型列表
    """
    event_types = [
        {
            "key": event_type.value,
            "name": {
                SecurityEventType.FAILED_LOGIN: "登录失败",
                SecurityEventType.BRUTE_FORCE_ATTEMPT: "暴力破解尝试",
                SecurityEventType.PERMISSION_DENIED: "权限拒绝",
                SecurityEventType.SUSPICIOUS_ACCESS: "可疑访问",
                SecurityEventType.PRIVILEGE_ESCALATION: "权限提升",
                SecurityEventType.DATA_BREACH_ATTEMPT: "数据泄露尝试",
                SecurityEventType.UNUSUAL_ACTIVITY: "异常活动",
                SecurityEventType.MODEL_TAMPERING: "模型篡改"
            }.get(event_type, event_type.value)
        }
        for event_type in SecurityEventType
    ]
    
    return {
        "success": True,
        "message": "获取事件类型成功",
        "data": event_types,
        "timestamp": datetime.now().isoformat()
    }
