"""
审计日志控制器
"""
from datetime import datetime, timedelta
from typing import Optional, List
from fastapi import APIRouter, Depends, Query, HTTPException
from app.core.auth_dependencies import get_current_user
from app.services.audit_service import audit_service
from app.models.admin import User
from app.core.unified_logger import get_logger

logger = get_logger(__name__)


router = APIRouter(tags=["权限审计系统"])


@router.get("/logs")
async def get_audit_logs(
    user_id: Optional[int] = Query(None, description="用户ID"),
    action_type: Optional[str] = Query(None, description="操作类型"),
    risk_level: Optional[str] = Query(None, description="风险等级"),
    start_time: Optional[datetime] = Query(None, description="开始时间"),
    end_time: Optional[datetime] = Query(None, description="结束时间"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(50, ge=1, le=200, description="每页数量"),
    current_user: User = Depends(get_current_user)
):
    """获取审计日志列表"""
    try:
        # 检查权限 - 只有管理员可以查看审计日志
        if not current_user.is_superuser:
            # 普通用户只能查看自己的日志
            user_id = current_user.id
        
        # 记录查询审计日志的操作
        logger.info(f"用户 {current_user.username} 查询审计日志")
        
        result = await audit_service.get_audit_logs(
            user_id=user_id,
            action_type=action_type,
            start_time=start_time,
            end_time=end_time,
            risk_level=risk_level,
            page=page,
            page_size=page_size
        )
        
        return {
            "code": 200,
            "message": "获取审计日志成功",
            "data": result
        }
        
    except Exception as e:
        logger.error(f"获取审计日志失败: {e}")
        raise HTTPException(status_code=500, detail="获取审计日志失败")


@router.get("/security-events")
async def get_security_events(
    event_type: Optional[str] = Query(None, description="事件类型"),
    event_level: Optional[str] = Query(None, description="事件级别"),
    status: Optional[str] = Query(None, description="处理状态"),
    start_time: Optional[datetime] = Query(None, description="开始时间"),
    end_time: Optional[datetime] = Query(None, description="结束时间"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(50, ge=1, le=200, description="每页数量"),
    current_user: User = Depends(get_current_user)
):
    """获取安全事件列表"""
    try:
        # 检查权限 - 只有超级管理员可以查看安全事件
        if not current_user.is_superuser:
            raise HTTPException(status_code=403, detail="权限不足")
        
        logger.info(f"用户 {current_user.username} 查询安全事件")
        
        result = await audit_service.get_security_events(
            event_type=event_type,
            event_level=event_level,
            status=status,
            start_time=start_time,
            end_time=end_time,
            page=page,
            page_size=page_size
        )
        
        return {
            "code": 200,
            "message": "获取安全事件成功",
            "data": result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取安全事件失败: {e}")
        raise HTTPException(status_code=500, detail="获取安全事件失败")


@router.get("/statistics")
async def get_audit_statistics(
    days: int = Query(7, ge=1, le=90, description="统计天数"),
    current_user: User = Depends(get_current_user)
):
    """获取审计统计信息"""
    try:
        # 检查权限
        if not current_user.is_superuser:
            raise HTTPException(status_code=403, detail="权限不足")
        
        logger.info(f"用户 {current_user.username} 查询审计统计")
        
        # 计算时间范围
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(days=days)
        
        # 获取基础统计
        total_logs = await audit_service.get_audit_logs(
            start_time=start_time,
            end_time=end_time,
            page_size=1
        )
        
        # 获取高风险日志统计
        high_risk_logs = await audit_service.get_audit_logs(
            risk_level="HIGH",
            start_time=start_time,
            end_time=end_time,
            page_size=1
        )
        
        critical_risk_logs = await audit_service.get_audit_logs(
            risk_level="CRITICAL",
            start_time=start_time,
            end_time=end_time,
            page_size=1
        )
        
        # 获取安全事件统计
        security_events = await audit_service.get_security_events(
            start_time=start_time,
            end_time=end_time,
            page_size=1
        )
        
        # 获取未处理的安全事件
        pending_events = await audit_service.get_security_events(
            status="PENDING",
            start_time=start_time,
            end_time=end_time,
            page_size=1
        )
        
        statistics = {
            "time_range": {
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "days": days
            },
            "audit_logs": {
                "total": total_logs["total"],
                "high_risk": high_risk_logs["total"],
                "critical_risk": critical_risk_logs["total"]
            },
            "security_events": {
                "total": security_events["total"],
                "pending": pending_events["total"]
            }
        }
        
        return {
            "code": 200,
            "message": "获取审计统计成功",
            "data": statistics
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取审计统计失败: {e}")
        raise HTTPException(status_code=500, detail="获取审计统计失败")


@router.get("/action-types")
async def get_action_types(
    current_user: User = Depends(get_current_user)
):
    """获取操作类型列表"""
    try:
        if not current_user.is_superuser:
            raise HTTPException(status_code=403, detail="权限不足")
        
        action_types = [
            {"value": "LOGIN", "label": "用户登录"},
            {"value": "LOGOUT", "label": "用户登出"},
            {"value": "PERMISSION_CHECK", "label": "权限验证"},
            {"value": "API_ACCESS", "label": "API访问"},
            {"value": "MENU_ACCESS", "label": "菜单访问"},
            {"value": "ROLE_CHANGE", "label": "角色变更"},
            {"value": "PERMISSION_CHANGE", "label": "权限变更"},
            {"value": "BATCH_OPERATION", "label": "批量操作"},
            {"value": "SENSITIVE_OPERATION", "label": "敏感操作"}
        ]
        
        return {
            "code": 200,
            "message": "获取操作类型成功",
            "data": action_types
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取操作类型失败: {e}")
        raise HTTPException(status_code=500, detail="获取操作类型失败")


@router.get("/risk-levels")
async def get_risk_levels(
    current_user: User = Depends(get_current_user)
):
    """获取风险等级列表"""
    try:
        if not current_user.is_superuser:
            raise HTTPException(status_code=403, detail="权限不足")
        
        risk_levels = [
            {"value": "LOW", "label": "低风险", "color": "success"},
            {"value": "MEDIUM", "label": "中风险", "color": "warning"},
            {"value": "HIGH", "label": "高风险", "color": "error"},
            {"value": "CRITICAL", "label": "严重风险", "color": "error"}
        ]
        
        return {
            "code": 200,
            "message": "获取风险等级成功",
            "data": risk_levels
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取风险等级失败: {e}")
        raise HTTPException(status_code=500, detail="获取风险等级失败")


@router.post("/security-events/{event_id}/handle")
async def handle_security_event(
    event_id: int,
    handle_note: str = Query(..., description="处理备注"),
    current_user: User = Depends(get_current_user)
):
    """处理安全事件"""
    try:
        # 检查权限
        if not current_user.is_superuser:
            raise HTTPException(status_code=403, detail="权限不足")
        
        # 使用audit_service处理安全事件
        result = await audit_service.handle_security_event(
            event_id=event_id,
            handled_by=current_user.id,
            handle_note=handle_note
        )
        
        if not result:
            raise HTTPException(status_code=404, detail="安全事件不存在")
        
        logger.info(f"用户 {current_user.username} 处理安全事件 {event_id}")
        
        return {
            "code": 200,
            "message": "处理安全事件成功",
            "data": result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"处理安全事件失败: {e}")
        raise HTTPException(status_code=500, detail="处理安全事件失败")


@router.get("/export")
async def export_audit_logs(
    user_id: Optional[int] = Query(None, description="用户ID"),
    action_type: Optional[str] = Query(None, description="操作类型"),
    risk_level: Optional[str] = Query(None, description="风险等级"),
    start_time: Optional[datetime] = Query(None, description="开始时间"),
    end_time: Optional[datetime] = Query(None, description="结束时间"),
    current_user: User = Depends(get_current_user)
):
    """导出审计日志"""
    try:
        # 检查权限
        if not current_user.is_superuser:
            raise HTTPException(status_code=403, detail="权限不足")
        
        logger.info(f"用户 {current_user.username} 导出审计日志")
        
        # 获取所有符合条件的日志（不分页）
        result = await audit_service.get_audit_logs(
            user_id=user_id,
            action_type=action_type,
            start_time=start_time,
            end_time=end_time,
            risk_level=risk_level,
            page=1,
            page_size=10000  # 设置一个较大的值
        )
        
        # 这里可以根据需要实现CSV或Excel导出
        # 目前返回JSON格式
        return {
            "code": 200,
            "message": "导出审计日志成功",
            "data": {
                "export_time": datetime.utcnow().isoformat(),
                "total_records": result["total"],
                "logs": result["logs"]
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"导出审计日志失败: {e}")
        raise HTTPException(status_code=500, detail="导出审计日志失败")