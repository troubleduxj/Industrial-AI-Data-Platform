#!/usr/bin/env python3
"""
权限系统性能优化控制器
"""
import time
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Request, Query, Body
from pydantic import BaseModel, Field
from datetime import datetime, timedelta
from app.core.auth_dependencies import get_current_user
from app.models.admin import User
from app.services.permission_performance_service import permission_performance_service
from app.services.permission_monitor_service import permission_monitor_service
from app.core.unified_logger import get_logger

logger = get_logger(__name__)


router = APIRouter(tags=["权限系统性能优化"])


class PerformanceOptimizationRequest(BaseModel):
    """性能优化请求"""
    user_ids: Optional[List[int]] = Field(None, description="需要预热的用户ID列表")
    cache_strategy: Optional[str] = Field(None, description="缓存策略")
    enable_monitoring: Optional[bool] = Field(None, description="是否启用监控")
    monitoring_interval: Optional[int] = Field(60, description="监控间隔（秒）")


class CacheOperationRequest(BaseModel):
    """缓存操作请求"""
    operation: str = Field(..., description="操作类型: clear, warm_up, invalidate")
    user_ids: Optional[List[int]] = Field(None, description="用户ID列表")
    cache_keys: Optional[List[str]] = Field(None, description="缓存键列表")


class PermissionCheckRequest(BaseModel):
    """权限检查请求"""
    user_id: int = Field(..., description="用户ID")
    permissions: List[str] = Field(..., description="权限列表")
    use_cache: bool = Field(True, description="是否使用缓存")


@router.get("/performance-report")
async def get_performance_report(
    request: Request,
    time_window: int = Query(3600, ge=300, le=86400, description="时间窗口（秒）"),
    current_user: Admin = Depends(get_current_user)
):
    """获取性能报告"""
    try:
        # 检查权限 - 只有管理员可以查看性能报告
        if not current_user.is_superuser:
            raise HTTPException(status_code=403, detail="权限不足")
        
        # 获取权限系统性能报告
        perf_report = await permission_performance_service.get_performance_report()
        
        # 获取监控仪表板数据
        dashboard_data = await permission_monitor_service.get_monitoring_dashboard()
        
        # 生成详细性能报告
        detailed_report = await permission_monitor_service.generate_performance_report(time_window)
        
        return {
            "code": 200,
            "message": "获取性能报告成功",
            "data": {
                "basic_performance": perf_report,
                "monitoring_dashboard": dashboard_data,
                "detailed_analysis": detailed_report,
                "report_time": datetime.utcnow().isoformat()
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取性能报告失败: {e}")
        raise HTTPException(status_code=500, detail="获取性能报告失败")


@router.get("/cache-stats")
async def get_cache_statistics(
    request: Request,
    current_user: Admin = Depends(get_current_user)
):
    """获取缓存统计信息"""
    try:
        # 检查权限
        if not current_user.is_superuser:
            raise HTTPException(status_code=403, detail="权限不足")
        
        # 获取缓存性能统计
        cache_stats = permission_performance_service.cache.get_performance_stats()
        
        # 获取查询优化器统计
        query_stats = permission_performance_service.query_optimizer.get_query_stats()
        
        return {
            "code": 200,
            "message": "获取缓存统计成功",
            "data": {
                "cache_performance": cache_stats,
                "query_optimization": query_stats,
                "cache_health": {
                    "status": "healthy" if cache_stats.get("hit_rate", 0) > 70 else "needs_attention",
                    "recommendations": [
                        "缓存命中率良好" if cache_stats.get("hit_rate", 0) > 80 else "建议优化缓存策略",
                        "响应时间正常" if cache_stats.get("avg_response_time_ms", 0) < 50 else "建议优化查询性能"
                    ]
                }
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取缓存统计失败: {e}")
        raise HTTPException(status_code=500, detail="获取缓存统计失败")


@router.post("/cache-operations")
async def perform_cache_operation(
    request: Request,
    operation_request: CacheOperationRequest,
    current_user: Admin = Depends(get_current_user)
):
    """执行缓存操作"""
    try:
        # 检查权限
        if not current_user.is_superuser:
            raise HTTPException(status_code=403, detail="权限不足")
        
        operation = operation_request.operation.lower()
        result = {"operation": operation, "success": False, "message": ""}
        
        if operation == "clear":
            # 清空缓存
            await permission_performance_service.cache.clear()
            result["success"] = True
            result["message"] = "缓存已清空"
            logger.info(f"用户 {current_user.username} 清空了权限缓存")
            
        elif operation == "warm_up":
            # 预热缓存
            if not operation_request.user_ids:
                raise HTTPException(status_code=400, detail="预热缓存需要提供用户ID列表")
            
            await permission_performance_service.warm_up_user_permissions(operation_request.user_ids)
            result["success"] = True
            result["message"] = f"已预热 {len(operation_request.user_ids)} 个用户的权限缓存"
            logger.info(f"用户 {current_user.username} 预热了 {len(operation_request.user_ids)} 个用户的权限缓存")
            
        elif operation == "invalidate":
            # 使缓存失效
            if not operation_request.user_ids:
                raise HTTPException(status_code=400, detail="使缓存失效需要提供用户ID列表")
            
            for user_id in operation_request.user_ids:
                await permission_performance_service.invalidate_user_permissions(user_id)
            
            result["success"] = True
            result["message"] = f"已使 {len(operation_request.user_ids)} 个用户的权限缓存失效"
            logger.info(f"用户 {current_user.username} 使 {len(operation_request.user_ids)} 个用户的权限缓存失效")
            
        else:
            raise HTTPException(status_code=400, detail=f"不支持的操作: {operation}")
        
        return {
            "code": 200,
            "message": "缓存操作执行成功",
            "data": result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"执行缓存操作失败: {e}")
        raise HTTPException(status_code=500, detail="执行缓存操作失败")


@router.post("/permission-check-optimized")
async def check_permission_optimized(
    request: Request,
    check_request: PermissionCheckRequest,
    current_user: Admin = Depends(get_current_user)
):
    """优化的权限检查"""
    try:
        # 检查权限
        if not current_user.is_superuser:
            raise HTTPException(status_code=403, detail="权限不足")
        
        start_time = time.time()
        
        if len(check_request.permissions) == 1:
            # 单个权限检查
            result = await permission_performance_service.check_permission_optimized(
                check_request.user_id, 
                check_request.permissions[0]
            )
            results = {check_request.permissions[0]: result}
        else:
            # 批量权限检查
            results = await permission_performance_service.check_permissions_batch(
                check_request.user_id,
                check_request.permissions
            )
        
        response_time = (time.time() - start_time) * 1000  # 转换为毫秒
        
        return {
            "code": 200,
            "message": "权限检查完成",
            "data": {
                "user_id": check_request.user_id,
                "permissions": results,
                "response_time_ms": round(response_time, 2),
                "cache_used": check_request.use_cache
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"优化权限检查失败: {e}")
        raise HTTPException(status_code=500, detail="权限检查失败")


@router.post("/monitoring-control")
async def control_monitoring(
    request: Request,
    optimization_request: PerformanceOptimizationRequest,
    current_user: Admin = Depends(get_current_user)
):
    """控制性能监控"""
    try:
        # 检查权限
        if not current_user.is_superuser:
            raise HTTPException(status_code=403, detail="权限不足")
        
        result = {"operations": [], "success": True}
        
        if optimization_request.enable_monitoring is not None:
            if optimization_request.enable_monitoring:
                # 启动监控
                await permission_monitor_service.start_monitoring(
                    optimization_request.monitoring_interval or 60
                )
                result["operations"].append("监控已启动")
                logger.info(f"用户 {current_user.username} 启动了权限系统性能监控")
            else:
                # 停止监控
                await permission_monitor_service.stop_monitoring()
                result["operations"].append("监控已停止")
                logger.info(f"用户 {current_user.username} 停止了权限系统性能监控")
        
        # 预热缓存
        if optimization_request.user_ids:
            await permission_performance_service.warm_up_user_permissions(
                optimization_request.user_ids
            )
            result["operations"].append(f"已预热 {len(optimization_request.user_ids)} 个用户的权限缓存")
        
        return {
            "code": 200,
            "message": "监控控制操作完成",
            "data": result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"监控控制操作失败: {e}")
        raise HTTPException(status_code=500, detail="监控控制操作失败")


@router.get("/monitoring-dashboard")
async def get_monitoring_dashboard(
    request: Request,
    current_user: Admin = Depends(get_current_user)
):
    """获取监控仪表板"""
    try:
        # 检查权限
        if not current_user.is_superuser:
            raise HTTPException(status_code=403, detail="权限不足")
        
        # 获取监控仪表板数据
        dashboard_data = await permission_monitor_service.get_monitoring_dashboard()
        
        return {
            "code": 200,
            "message": "获取监控仪表板成功",
            "data": dashboard_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取监控仪表板失败: {e}")
        raise HTTPException(status_code=500, detail="获取监控仪表板失败")


@router.get("/performance-alerts")
async def get_performance_alerts(
    request: Request,
    active_only: bool = Query(True, description="是否只返回活跃告警"),
    current_user: Admin = Depends(get_current_user)
):
    """获取性能告警"""
    try:
        # 检查权限
        if not current_user.is_superuser:
            raise HTTPException(status_code=403, detail="权限不足")
        
        if active_only:
            alerts = permission_monitor_service.alert_manager.get_active_alerts()
        else:
            alerts = list(permission_monitor_service.alert_manager.alert_history)
        
        alert_data = []
        for alert in alerts:
            alert_data.append({
                "level": alert.level.value,
                "message": alert.message,
                "metric_name": alert.metric_name,
                "current_value": alert.current_value,
                "threshold_value": alert.threshold_value,
                "timestamp": alert.timestamp.isoformat(),
                "resolved": alert.resolved,
                "resolved_at": alert.resolved_at.isoformat() if alert.resolved_at else None
            })
        
        # 获取告警摘要
        alert_summary = permission_monitor_service.alert_manager.get_alert_summary()
        
        return {
            "code": 200,
            "message": "获取性能告警成功",
            "data": {
                "alerts": alert_data,
                "summary": alert_summary,
                "total_count": len(alert_data)
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取性能告警失败: {e}")
        raise HTTPException(status_code=500, detail="获取性能告警失败")


@router.post("/performance-benchmark")
async def run_performance_benchmark(
    request: Request,
    user_count: int = Body(100, ge=1, le=1000, description="测试用户数量"),
    permission_count: int = Body(10, ge=1, le=100, description="每用户权限数量"),
    iterations: int = Body(100, ge=1, le=1000, description="测试迭代次数"),
    current_user: Admin = Depends(get_current_user)
):
    """运行性能基准测试"""
    try:
        # 检查权限
        if not current_user.is_superuser:
            raise HTTPException(status_code=403, detail="权限不足")
        
        import asyncio
        import random
        
        logger.info(f"开始性能基准测试: {user_count}用户, {permission_count}权限/用户, {iterations}次迭代")
        
        # 生成测试数据
        test_users = list(range(1, user_count + 1))
        test_permissions = [f"permission_{i}" for i in range(1, permission_count + 1)]
        
        # 预热缓存
        await permission_performance_service.warm_up_user_permissions(test_users)
        
        # 基准测试
        start_time = time.time()
        total_checks = 0
        
        for i in range(iterations):
            # 随机选择用户和权限
            user_id = random.choice(test_users)
            permissions = random.sample(test_permissions, random.randint(1, min(5, permission_count)))
            
            # 执行权限检查
            await permission_performance_service.check_permissions_batch(user_id, permissions)
            total_checks += len(permissions)
            
            # 每10次迭代休息一下，避免过载
            if i % 10 == 0:
                await asyncio.sleep(0.001)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # 计算性能指标
        checks_per_second = total_checks / total_time
        avg_time_per_check = (total_time / total_checks) * 1000  # 毫秒
        
        # 获取缓存统计
        cache_stats = permission_performance_service.cache.get_performance_stats()
        
        benchmark_result = {
            "test_parameters": {
                "user_count": user_count,
                "permission_count": permission_count,
                "iterations": iterations,
                "total_permission_checks": total_checks
            },
            "performance_metrics": {
                "total_time_seconds": round(total_time, 3),
                "checks_per_second": round(checks_per_second, 2),
                "avg_time_per_check_ms": round(avg_time_per_check, 3),
                "cache_hit_rate": cache_stats.get("hit_rate", 0)
            },
            "cache_statistics": cache_stats,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        logger.info(f"性能基准测试完成: {checks_per_second:.2f} checks/sec, 缓存命中率: {cache_stats.get('hit_rate', 0):.1f}%")
        
        return {
            "code": 200,
            "message": "性能基准测试完成",
            "data": benchmark_result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"性能基准测试失败: {e}")
        raise HTTPException(status_code=500, detail="性能基准测试失败")


@router.get("/system-resources")
async def get_system_resources(
    request: Request,
    current_user: Admin = Depends(get_current_user)
):
    """获取系统资源使用情况"""
    try:
        # 检查权限
        if not current_user.is_superuser:
            raise HTTPException(status_code=403, detail="权限不足")
        
        # 获取系统资源信息
        resource_info = permission_monitor_service.resource_monitor.get_current_resources()
        
        return {
            "code": 200,
            "message": "获取系统资源成功",
            "data": resource_info
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取系统资源失败: {e}")
        raise HTTPException(status_code=500, detail="获取系统资源失败")


@router.post("/optimize-cache-strategy")
async def optimize_cache_strategy(
    request: Request,
    strategy: str = Body(..., description="缓存策略: LRU, LFU, TTL, ADAPTIVE"),
    current_user: Admin = Depends(get_current_user)
):
    """优化缓存策略"""
    try:
        # 检查权限
        if not current_user.is_superuser:
            raise HTTPException(status_code=403, detail="权限不足")
        
        from app.services.permission_performance_service import CacheStrategy
        
        # 验证策略
        strategy_map = {
            "LRU": CacheStrategy.LRU,
            "LFU": CacheStrategy.LFU,
            "TTL": CacheStrategy.TTL,
            "ADAPTIVE": CacheStrategy.ADAPTIVE
        }
        
        if strategy.upper() not in strategy_map:
            raise HTTPException(status_code=400, detail=f"不支持的缓存策略: {strategy}")
        
        # 更新缓存策略
        old_strategy = permission_performance_service.cache.strategy
        permission_performance_service.cache.strategy = strategy_map[strategy.upper()]
        
        logger.info(f"用户 {current_user.username} 将缓存策略从 {old_strategy.value} 更改为 {strategy.upper()}")
        
        return {
            "code": 200,
            "message": "缓存策略优化成功",
            "data": {
                "old_strategy": old_strategy.value,
                "new_strategy": strategy.upper(),
                "status": "updated"
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"优化缓存策略失败: {e}")
        raise HTTPException(status_code=500, detail="优化缓存策略失败")