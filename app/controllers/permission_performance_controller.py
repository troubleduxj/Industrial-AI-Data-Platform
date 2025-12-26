"""
权限系统性能优化控制器
"""
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from pydantic import BaseModel, Field
from app.core.auth_dependencies import get_current_user
from app.models.admin import User
from app.services.permission_performance_service import permission_performance_service
from app.services.async_permission_processor import permission_task_manager, TaskPriority
from app.services.permission_monitor_service import permission_monitor_service, AlertRule
from app.core.unified_logger import get_logger

logger = get_logger(__name__)


router = APIRouter(tags=["权限系统性能优化"])


class BatchPermissionCheckRequest(BaseModel):
    """批量权限检查请求"""
    user_permission_pairs: List[List[Any]] = Field(..., description="用户权限对列表")


class PreloadUsersRequest(BaseModel):
    """预加载用户请求"""
    user_ids: List[int] = Field(..., description="用户ID列表")


class AsyncPermissionCheckRequest(BaseModel):
    """异步权限检查请求"""
    user_id: int = Field(..., description="用户ID")
    permission_code: str = Field(..., description="权限代码")
    priority: str = Field("NORMAL", description="任务优先级")
    timeout: float = Field(5.0, description="超时时间")


class AlertRuleRequest(BaseModel):
    """告警规则请求"""
    name: str = Field(..., description="规则名称")
    metric: str = Field(..., description="监控指标")
    threshold: float = Field(..., description="阈值")
    operator: str = Field(..., description="操作符")
    duration: int = Field(..., description="持续时间")
    enabled: bool = Field(True, description="是否启用")


@router.get("/metrics")
async def get_performance_metrics(
    current_user: Admin = Depends(get_current_user)
):
    """获取性能指标"""
    try:
        # 检查权限
        if not current_user.is_superuser:
            raise HTTPException(status_code=403, detail="权限不足")
        
        # 获取各种性能指标
        perf_metrics = permission_performance_service.get_performance_metrics()
        task_stats = permission_task_manager.get_stats()
        monitor_metrics = permission_monitor_service.get_current_metrics()
        
        return {
            "code": 200,
            "message": "获取性能指标成功",
            "data": {
                "permission_service": perf_metrics,
                "async_processor": task_stats,
                "system_monitor": monitor_metrics,
                "timestamp": monitor_metrics.get("timestamp")
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取性能指标失败: {e}")
        raise HTTPException(status_code=500, detail="获取性能指标失败")


@router.post("/batch-check")
async def batch_permission_check(
    request: BatchPermissionCheckRequest,
    current_user: Admin = Depends(get_current_user)
):
    """批量权限检查"""
    try:
        # 转换请求格式
        user_permission_pairs = [tuple(pair) for pair in request.user_permission_pairs]
        
        # 执行批量检查
        results = await permission_performance_service.batch_check_permissions(
            user_permission_pairs
        )
        
        # 转换结果格式
        formatted_results = {}
        for (user_id, permission_code), result in results.items():
            key = f"{user_id}:{permission_code}"
            formatted_results[key] = result
        
        return {
            "code": 200,
            "message": "批量权限检查完成",
            "data": {
                "results": formatted_results,
                "total_checked": len(user_permission_pairs),
                "performance_metrics": permission_performance_service.get_performance_metrics()
            }
        }
        
    except Exception as e:
        logger.error(f"批量权限检查失败: {e}")
        raise HTTPException(status_code=500, detail="批量权限检查失败")


@router.post("/preload-users")
async def preload_user_permissions(
    request: PreloadUsersRequest,
    current_user: Admin = Depends(get_current_user)
):
    """预加载用户权限"""
    try:
        # 检查权限
        if not current_user.is_superuser:
            raise HTTPException(status_code=403, detail="权限不足")
        
        # 执行预加载
        await permission_performance_service.preload_user_permissions(request.user_ids)
        
        return {
            "code": 200,
            "message": f"预加载{len(request.user_ids)}个用户权限完成",
            "data": {
                "preloaded_users": len(request.user_ids),
                "user_ids": request.user_ids
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"预加载用户权限失败: {e}")
        raise HTTPException(status_code=500, detail="预加载用户权限失败")


@router.post("/warm-up-cache")
async def warm_up_cache(
    current_user: Admin = Depends(get_current_user)
):
    """缓存预热"""
    try:
        # 检查权限
        if not current_user.is_superuser:
            raise HTTPException(status_code=403, detail="权限不足")
        
        # 执行缓存预热
        await permission_performance_service.warm_up_cache()
        
        return {
            "code": 200,
            "message": "缓存预热完成",
            "data": {
                "status": "completed",
                "performance_metrics": permission_performance_service.get_performance_metrics()
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"缓存预热失败: {e}")
        raise HTTPException(status_code=500, detail="缓存预热失败")


@router.post("/optimize-patterns")
async def optimize_query_patterns(
    current_user: Admin = Depends(get_current_user)
):
    """优化查询模式"""
    try:
        # 检查权限
        if not current_user.is_superuser:
            raise HTTPException(status_code=403, detail="权限不足")
        
        # 执行查询模式优化
        await permission_performance_service.optimize_query_patterns()
        
        return {
            "code": 200,
            "message": "查询模式优化完成",
            "data": {
                "status": "completed",
                "performance_metrics": permission_performance_service.get_performance_metrics()
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"查询模式优化失败: {e}")
        raise HTTPException(status_code=500, detail="查询模式优化失败")


@router.post("/async-check")
async def async_permission_check(
    request: AsyncPermissionCheckRequest,
    current_user: Admin = Depends(get_current_user)
):
    """异步权限检查"""
    try:
        # 转换优先级
        priority_map = {
            "LOW": TaskPriority.LOW,
            "NORMAL": TaskPriority.NORMAL,
            "HIGH": TaskPriority.HIGH,
            "CRITICAL": TaskPriority.CRITICAL
        }
        priority = priority_map.get(request.priority.upper(), TaskPriority.NORMAL)
        
        # 提交异步任务
        task_id = await permission_task_manager.check_permission_async(
            user_id=request.user_id,
            permission_code=request.permission_code,
            priority=priority,
            timeout=request.timeout
        )
        
        return {
            "code": 200,
            "message": "异步权限检查任务已提交",
            "data": {
                "task_id": task_id,
                "status": "submitted",
                "estimated_completion": f"{request.timeout}s"
            }
        }
        
    except Exception as e:
        logger.error(f"异步权限检查失败: {e}")
        raise HTTPException(status_code=500, detail="异步权限检查失败")


@router.get("/async-result/{task_id}")
async def get_async_result(
    task_id: str,
    timeout: float = Query(5.0, description="等待超时时间"),
    current_user: Admin = Depends(get_current_user)
):
    """获取异步任务结果"""
    try:
        # 获取任务状态
        status = permission_task_manager.get_task_status(task_id)
        
        if status == "not_found":
            raise HTTPException(status_code=404, detail="任务不存在")
        
        # 获取任务结果
        result = await permission_task_manager.get_task_result(task_id, timeout)
        
        return {
            "code": 200,
            "message": "获取异步任务结果成功",
            "data": {
                "task_id": task_id,
                "status": status,
                "result": result,
                "has_result": result is not None
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取异步任务结果失败: {e}")
        raise HTTPException(status_code=500, detail="获取异步任务结果失败")


@router.get("/monitor/summary")
async def get_performance_summary(
    current_user: Admin = Depends(get_current_user)
):
    """获取性能摘要"""
    try:
        # 检查权限
        if not current_user.is_superuser:
            raise HTTPException(status_code=403, detail="权限不足")
        
        summary = permission_monitor_service.get_performance_summary()
        
        return {
            "code": 200,
            "message": "获取性能摘要成功",
            "data": summary
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取性能摘要失败: {e}")
        raise HTTPException(status_code=500, detail="获取性能摘要失败")


@router.get("/monitor/history/{metric}")
async def get_metrics_history(
    metric: str,
    hours: int = Query(1, ge=1, le=24, description="历史数据小时数"),
    current_user: Admin = Depends(get_current_user)
):
    """获取指标历史数据"""
    try:
        # 检查权限
        if not current_user.is_superuser:
            raise HTTPException(status_code=403, detail="权限不足")
        
        history = permission_monitor_service.get_metrics_history(metric, hours)
        
        return {
            "code": 200,
            "message": f"获取{metric}历史数据成功",
            "data": {
                "metric": metric,
                "period_hours": hours,
                "data_points": len(history),
                "history": history
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取指标历史数据失败: {e}")
        raise HTTPException(status_code=500, detail="获取指标历史数据失败")


@router.get("/monitor/alerts")
async def get_recent_alerts(
    hours: int = Query(24, ge=1, le=168, description="查询小时数"),
    current_user: Admin = Depends(get_current_user)
):
    """获取最近告警"""
    try:
        # 检查权限
        if not current_user.is_superuser:
            raise HTTPException(status_code=403, detail="权限不足")
        
        alerts = permission_monitor_service.get_recent_alerts(hours)
        
        return {
            "code": 200,
            "message": "获取最近告警成功",
            "data": {
                "period_hours": hours,
                "alert_count": len(alerts),
                "alerts": alerts
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取最近告警失败: {e}")
        raise HTTPException(status_code=500, detail="获取最近告警失败")


@router.get("/monitor/alert-rules")
async def get_alert_rules(
    current_user: Admin = Depends(get_current_user)
):
    """获取告警规则"""
    try:
        # 检查权限
        if not current_user.is_superuser:
            raise HTTPException(status_code=403, detail="权限不足")
        
        rules = permission_monitor_service.get_alert_rules()
        
        return {
            "code": 200,
            "message": "获取告警规则成功",
            "data": {
                "rule_count": len(rules),
                "rules": rules
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取告警规则失败: {e}")
        raise HTTPException(status_code=500, detail="获取告警规则失败")


@router.post("/monitor/alert-rules")
async def add_alert_rule(
    request: AlertRuleRequest,
    current_user: Admin = Depends(get_current_user)
):
    """添加告警规则"""
    try:
        # 检查权限
        if not current_user.is_superuser:
            raise HTTPException(status_code=403, detail="权限不足")
        
        # 创建告警规则
        rule = AlertRule(
            name=request.name,
            metric=request.metric,
            threshold=request.threshold,
            operator=request.operator,
            duration=request.duration,
            enabled=request.enabled
        )
        
        permission_monitor_service.add_alert_rule(rule)
        
        return {
            "code": 200,
            "message": "添加告警规则成功",
            "data": {
                "rule_name": request.name,
                "status": "added"
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"添加告警规则失败: {e}")
        raise HTTPException(status_code=500, detail="添加告警规则失败")


@router.put("/monitor/alert-rules/{rule_name}")
async def update_alert_rule(
    rule_name: str,
    enabled: Optional[bool] = Body(None, description="是否启用"),
    threshold: Optional[float] = Body(None, description="阈值"),
    duration: Optional[int] = Body(None, description="持续时间"),
    current_user: Admin = Depends(get_current_user)
):
    """更新告警规则"""
    try:
        # 检查权限
        if not current_user.is_superuser:
            raise HTTPException(status_code=403, detail="权限不足")
        
        # 构建更新参数
        update_params = {}
        if enabled is not None:
            update_params["enabled"] = enabled
        if threshold is not None:
            update_params["threshold"] = threshold
        if duration is not None:
            update_params["duration"] = duration
        
        if not update_params:
            raise HTTPException(status_code=400, detail="没有提供更新参数")
        
        # 更新规则
        success = permission_monitor_service.update_alert_rule(rule_name, **update_params)
        
        if not success:
            raise HTTPException(status_code=404, detail="告警规则不存在")
        
        return {
            "code": 200,
            "message": "更新告警规则成功",
            "data": {
                "rule_name": rule_name,
                "updated_params": update_params
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新告警规则失败: {e}")
        raise HTTPException(status_code=500, detail="更新告警规则失败")


@router.post("/clear-cache/{user_id}")
async def clear_user_cache(
    user_id: int,
    current_user: Admin = Depends(get_current_user)
):
    """清除用户缓存"""
    try:
        # 检查权限
        if not current_user.is_superuser:
            raise HTTPException(status_code=403, detail="权限不足")
        
        # 清除用户缓存
        await permission_performance_service.clear_user_cache(user_id)
        
        return {
            "code": 200,
            "message": f"清除用户{user_id}缓存成功",
            "data": {
                "user_id": user_id,
                "status": "cleared"
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"清除用户缓存失败: {e}")
        raise HTTPException(status_code=500, detail="清除用户缓存失败")


@router.post("/reset-metrics")
async def reset_performance_metrics(
    current_user: Admin = Depends(get_current_user)
):
    """重置性能指标"""
    try:
        # 检查权限
        if not current_user.is_superuser:
            raise HTTPException(status_code=403, detail="权限不足")
        
        # 重置各种指标
        permission_performance_service.reset_metrics()
        permission_task_manager.processor.reset_stats()
        
        return {
            "code": 200,
            "message": "重置性能指标成功",
            "data": {
                "status": "reset",
                "timestamp": permission_monitor_service.get_current_metrics().get("timestamp")
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"重置性能指标失败: {e}")
        raise HTTPException(status_code=500, detail="重置性能指标失败")


@router.get("/health")
async def permission_system_health_check(
    current_user: Admin = Depends(get_current_user)
):
    """权限系统健康检查"""
    try:
        # 执行健康检查
        health_result = await permission_performance_service.health_check()
        
        return {
            "code": 200,
            "message": "权限系统健康检查完成",
            "data": health_result
        }
        
    except Exception as e:
        logger.error(f"权限系统健康检查失败: {e}")
        return {
            "code": 500,
            "message": "权限系统健康检查失败",
            "data": {
                "status": "unhealthy",
                "error": str(e)
            }
        }