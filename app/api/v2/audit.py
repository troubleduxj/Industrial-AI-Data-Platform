"""
权限审计系统 v2接口
提供权限审计日志和安全事件的RESTful接口
"""
from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Request, Depends, Query, HTTPException
from app.controllers.audit_controller import router as audit_controller_router
from app.core.response_formatter_v2 import ResponseFormatterV2
from app.core.auth_dependencies import get_current_user
from app.models.admin import User

# 创建路由器
router = APIRouter()

# 直接包含审计控制器的路由，但去掉前缀
router.include_router(audit_controller_router, prefix="")

# 添加一些额外的便捷接口

@router.get("/dashboard", summary="获取审计仪表板数据")
async def get_audit_dashboard(
    request: Request,
    days: int = Query(7, ge=1, le=90, description="统计天数"),
    current_user: Admin = Depends(get_current_user)
):
    """获取审计仪表板数据"""
    formatter = ResponseFormatterV2(request)
    
    try:
        # 检查权限
        if not current_user.is_superuser:
            return formatter.forbidden("权限不足")
        
        from app.services.audit_service import audit_service
        
        # 计算时间范围
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(days=days)
        
        # 获取基础统计
        total_logs = await audit_service.get_audit_logs(
            start_time=start_time,
            end_time=end_time,
            page_size=1
        )
        
        # 获取各风险等级的日志统计
        risk_stats = {}
        for risk_level in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]:
            risk_logs = await audit_service.get_audit_logs(
                risk_level=risk_level,
                start_time=start_time,
                end_time=end_time,
                page_size=1
            )
            risk_stats[risk_level.lower()] = risk_logs["total"]
        
        # 获取各操作类型的统计
        action_stats = {}
        action_types = ["LOGIN", "LOGOUT", "PERMISSION_CHECK", "API_ACCESS", "SENSITIVE_OPERATION", "BATCH_OPERATION"]
        for action_type in action_types:
            action_logs = await audit_service.get_audit_logs(
                action_type=action_type,
                start_time=start_time,
                end_time=end_time,
                page_size=1
            )
            action_stats[action_type.lower()] = action_logs["total"]
        
        # 获取安全事件统计
        security_events = await audit_service.get_security_events(
            start_time=start_time,
            end_time=end_time,
            page_size=1
        )
        
        # 获取待处理的安全事件
        pending_events = await audit_service.get_security_events(
            status="PENDING",
            start_time=start_time,
            end_time=end_time,
            page_size=1
        )
        
        # 获取最近的高风险日志
        recent_high_risk = await audit_service.get_audit_logs(
            risk_level="HIGH",
            start_time=start_time,
            end_time=end_time,
            page=1,
            page_size=5
        )
        
        # 获取最近的安全事件
        recent_events = await audit_service.get_security_events(
            start_time=start_time,
            end_time=end_time,
            page=1,
            page_size=5
        )
        
        dashboard_data = {
            "time_range": {
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "days": days
            },
            "overview": {
                "total_logs": total_logs["total"],
                "total_events": security_events["total"],
                "pending_events": pending_events["total"],
                "high_risk_logs": risk_stats.get("high", 0) + risk_stats.get("critical", 0)
            },
            "risk_distribution": risk_stats,
            "action_distribution": action_stats,
            "recent_high_risk_logs": recent_high_risk["logs"],
            "recent_security_events": recent_events["events"]
        }
        
        return formatter.success(
            data=dashboard_data,
            message="获取审计仪表板数据成功"
        )
        
    except Exception as e:
        return formatter.internal_error(f"获取审计仪表板数据失败: {str(e)}")


@router.get("/trends", summary="获取审计趋势数据")
async def get_audit_trends(
    request: Request,
    days: int = Query(30, ge=7, le=90, description="统计天数"),
    current_user: Admin = Depends(get_current_user)
):
    """获取审计趋势数据"""
    formatter = ResponseFormatterV2(request)
    
    try:
        # 检查权限
        if not current_user.is_superuser:
            return formatter.forbidden("权限不足")
        
        from app.services.audit_service import audit_service
        
        # 计算时间范围
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(days=days)
        
        # 按天统计数据
        trends = []
        for i in range(days):
            day_end = end_time - timedelta(days=i)
            day_start = day_end - timedelta(days=1)
            
            # 获取当天的日志统计
            day_logs = await audit_service.get_audit_logs(
                start_time=day_start,
                end_time=day_end,
                page_size=1
            )
            
            # 获取当天的高风险日志
            day_high_risk = await audit_service.get_audit_logs(
                risk_level="HIGH",
                start_time=day_start,
                end_time=day_end,
                page_size=1
            )
            
            # 获取当天的安全事件
            day_events = await audit_service.get_security_events(
                start_time=day_start,
                end_time=day_end,
                page_size=1
            )
            
            trends.append({
                "date": day_start.strftime("%Y-%m-%d"),
                "total_logs": day_logs["total"],
                "high_risk_logs": day_high_risk["total"],
                "security_events": day_events["total"]
            })
        
        # 反转列表，使日期从早到晚排序
        trends.reverse()
        
        return formatter.success(
            data={
                "time_range": {
                    "start_time": start_time.isoformat(),
                    "end_time": end_time.isoformat(),
                    "days": days
                },
                "trends": trends
            },
            message="获取审计趋势数据成功"
        )
        
    except Exception as e:
        return formatter.internal_error(f"获取审计趋势数据失败: {str(e)}")


@router.get("/users/{user_id}/activity", summary="获取用户活动日志")
async def get_user_activity(
    user_id: int,
    request: Request,
    days: int = Query(7, ge=1, le=30, description="统计天数"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    current_user: Admin = Depends(get_current_user)
):
    """获取指定用户的活动日志"""
    formatter = ResponseFormatterV2(request)
    
    try:
        # 检查权限 - 超级管理员可以查看所有用户，普通用户只能查看自己
        if not current_user.is_superuser and current_user.id != user_id:
            return formatter.forbidden("权限不足")
        
        from app.services.audit_service import audit_service
        
        # 计算时间范围
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(days=days)
        
        # 获取用户活动日志
        result = await audit_service.get_audit_logs(
            user_id=user_id,
            start_time=start_time,
            end_time=end_time,
            page=page,
            page_size=page_size
        )
        
        return formatter.paginated_success(
            data=result["logs"],
            total=result["total"],
            page=page,
            page_size=page_size,
            message="获取用户活动日志成功",
            resource_type="user_activity",
            query_params={"user_id": user_id, "days": days}
        )
        
    except Exception as e:
        return formatter.internal_error(f"获取用户活动日志失败: {str(e)}")


@router.get("/summary", summary="获取审计摘要信息")
async def get_audit_summary(
    request: Request,
    current_user: Admin = Depends(get_current_user)
):
    """获取审计摘要信息"""
    formatter = ResponseFormatterV2(request)
    
    try:
        # 检查权限
        if not current_user.is_superuser:
            return formatter.forbidden("权限不足")
        
        from app.services.audit_service import audit_service
        
        # 获取最近24小时的统计
        end_time = datetime.utcnow()
        start_time_24h = end_time - timedelta(hours=24)
        start_time_7d = end_time - timedelta(days=7)
        
        # 24小时统计
        logs_24h = await audit_service.get_audit_logs(
            start_time=start_time_24h,
            end_time=end_time,
            page_size=1
        )
        
        high_risk_24h = await audit_service.get_audit_logs(
            risk_level="HIGH",
            start_time=start_time_24h,
            end_time=end_time,
            page_size=1
        )
        
        events_24h = await audit_service.get_security_events(
            start_time=start_time_24h,
            end_time=end_time,
            page_size=1
        )
        
        # 7天统计
        logs_7d = await audit_service.get_audit_logs(
            start_time=start_time_7d,
            end_time=end_time,
            page_size=1
        )
        
        # 待处理事件
        pending_events = await audit_service.get_security_events(
            status="PENDING",
            page_size=1
        )
        
        summary = {
            "last_24_hours": {
                "total_logs": logs_24h["total"],
                "high_risk_logs": high_risk_24h["total"],
                "security_events": events_24h["total"]
            },
            "last_7_days": {
                "total_logs": logs_7d["total"]
            },
            "pending_events": pending_events["total"],
            "system_status": "normal" if pending_events["total"] == 0 else "attention_required"
        }
        
        return formatter.success(
            data=summary,
            message="获取审计摘要信息成功"
        )
        
    except Exception as e:
        return formatter.internal_error(f"获取审计摘要信息失败: {str(e)}")