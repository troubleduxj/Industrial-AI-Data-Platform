"""
安全管理API端点
"""

from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from app.core.dependency import DependAuth, DependPermission
from app.core.security_monitor import security_monitor, SecurityEventType, SecurityLevel
from app.schemas.base import Success


router = APIRouter()


class SecurityEventResponse(BaseModel):
    """安全事件响应模型"""
    event_type: str
    level: str
    timestamp: str
    client_ip: str
    user_agent: str
    path: str
    method: str
    details: Dict[str, Any]
    user_id: Optional[str] = None
    session_id: Optional[str] = None


class SecuritySummaryResponse(BaseModel):
    """安全摘要响应模型"""
    total_events: int
    recent_events_count: int
    unique_ips: int
    event_type_distribution: Dict[str, int]
    level_distribution: Dict[str, int]
    top_threat_ips: List[Dict[str, Any]]


class IPStatisticsResponse(BaseModel):
    """IP统计响应模型"""
    ip: str
    request_count: int
    blocked_count: int
    last_activity: Optional[str]
    event_types: Dict[str, int]
    is_suspicious: bool


@router.get("/security/summary")
async def get_security_summary(
    current_user=DependAuth
):
    """
    获取安全摘要信息
    需要系统安全读取权限
    """
    summary = security_monitor.get_security_summary()
    return Success(data=SecuritySummaryResponse(**summary))


@router.get("/security/events")
async def get_security_events(
    minutes: int = Query(60, description="获取最近多少分钟的事件", ge=1, le=1440),
    event_type: Optional[str] = Query(None, description="事件类型过滤"),
    level: Optional[str] = Query(None, description="安全级别过滤"),
    client_ip: Optional[str] = Query(None, description="客户端IP过滤"),
    limit: int = Query(100, description="返回事件数量限制", ge=1, le=1000),
    current_user=DependAuth
):
    """
    获取安全事件列表
    支持多种过滤条件
    """
    events = security_monitor.get_recent_events(minutes)
    
    # 应用过滤条件
    if event_type:
        try:
            event_type_enum = SecurityEventType(event_type)
            events = [e for e in events if e.event_type == event_type_enum]
        except ValueError:
            raise HTTPException(status_code=400, detail=f"无效的事件类型: {event_type}")
    
    if level:
        try:
            level_enum = SecurityLevel(level)
            events = [e for e in events if e.level == level_enum]
        except ValueError:
            raise HTTPException(status_code=400, detail=f"无效的安全级别: {level}")
    
    if client_ip:
        events = [e for e in events if e.client_ip == client_ip]
    
    # 限制返回数量
    events = events[:limit]
    
    # 转换为响应模型
    event_responses = []
    for event in events:
        event_responses.append(SecurityEventResponse(
            event_type=event.event_type.value,
            level=event.level.value,
            timestamp=event.timestamp.isoformat(),
            client_ip=event.client_ip,
            user_agent=event.user_agent,
            path=event.path,
            method=event.method,
            details=event.details,
            user_id=event.user_id,
            session_id=event.session_id
        ))
    
    return Success(data=event_responses)


@router.get("/security/threats")
async def get_threat_ips(
    limit: int = Query(20, description="返回威胁IP数量", ge=1, le=100),
    current_user=DependAuth
):
    """
    获取威胁IP列表
    按威胁分数排序
    """
    threat_ips = security_monitor.get_top_threat_ips(limit)
    return Success(data=threat_ips)


@router.get("/security/ip/{ip_address}")
async def get_ip_statistics(
    ip_address: str,
    current_user=DependAuth
):
    """
    获取特定IP的统计信息
    """
    stats = security_monitor.get_ip_statistics(ip_address)
    
    if not stats or stats['request_count'] == 0:
        raise HTTPException(status_code=404, detail=f"未找到IP {ip_address} 的统计信息")
    
    response = IPStatisticsResponse(
        ip=ip_address,
        request_count=stats['request_count'],
        blocked_count=stats['blocked_count'],
        last_activity=stats['last_activity'].isoformat() if stats['last_activity'] else None,
        event_types=dict(stats['event_types']),
        is_suspicious=security_monitor.is_ip_suspicious(ip_address)
    )
    
    return Success(data=response)


@router.get("/security/ip/{ip_address}/events")
async def get_ip_events(
    ip_address: str,
    minutes: int = Query(60, description="获取最近多少分钟的事件", ge=1, le=1440),
    current_user=DependAuth
):
    """
    获取特定IP的安全事件
    """
    events = security_monitor.get_recent_events_by_ip(ip_address, minutes)
    
    event_responses = []
    for event in events:
        event_responses.append(SecurityEventResponse(
            event_type=event.event_type.value,
            level=event.level.value,
            timestamp=event.timestamp.isoformat(),
            client_ip=event.client_ip,
            user_agent=event.user_agent,
            path=event.path,
            method=event.method,
            details=event.details,
            user_id=event.user_id,
            session_id=event.session_id
        ))
    
    return Success(data=event_responses)


@router.post("/security/cleanup")
async def cleanup_security_data(
    days: int = Query(7, description="清理多少天前的数据", ge=1, le=30),
    current_user=DependAuth
):
    """
    清理旧的安全数据
    需要系统安全写入权限
    """
    security_monitor.cleanup_old_events(days)
    return Success(message=f"已清理{days}天前的安全数据")


@router.get("/security/config")
async def get_security_config(
    current_user=DependAuth
):
    """
    获取当前安全配置
    """
    from app.core.security_config import security_config_manager
    
    config = {
        'rate_limiting': security_config_manager.get_rate_limit_config(),
        'input_validation': security_config_manager.get_input_validation_config(),
        'security_headers': security_config_manager.get_security_headers_config(),
        'middleware_config': security_config_manager.get_middleware_config()
    }
    
    return Success(data=config)


@router.get("/security/status")
async def get_security_status():
    """
    获取安全状态（无需认证，用于健康检查）
    """
    recent_events = security_monitor.get_recent_events(5)  # 最近5分钟
    critical_events = [
        e for e in recent_events 
        if e.level == SecurityLevel.CRITICAL
    ]
    
    status = "healthy"
    if len(critical_events) > 0:
        status = "critical"
    elif len(recent_events) > 50:  # 5分钟内超过50个事件
        status = "warning"
    
    return {
        "status": status,
        "recent_events_count": len(recent_events),
        "critical_events_count": len(critical_events),
        "timestamp": datetime.now().isoformat()
    }


# 事件类型和级别的枚举值，用于API文档
@router.get("/security/enums")
async def get_security_enums():
    """
    获取安全相关的枚举值
    用于前端下拉选择等
    """
    return {
        "event_types": [e.value for e in SecurityEventType],
        "security_levels": [l.value for l in SecurityLevel]
    }