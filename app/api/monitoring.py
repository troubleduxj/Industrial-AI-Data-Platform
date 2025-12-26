# -*- coding: utf-8 -*-
"""
监控API
提供性能指标、系统状态和健康检查接口
"""

from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel, Field

from app.core.monitoring import performance_monitor
from app.core.tdengine_config import tdengine_config_manager
from app.services.tdengine_service import tdengine_service_manager
from app.log import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/api/monitoring", tags=["监控"])


class HealthCheckResponse(BaseModel):
    """健康检查响应模型"""
    status: str = Field(..., description="健康状态")
    timestamp: datetime = Field(..., description="检查时间")
    services: Dict[str, Any] = Field(..., description="服务状态")
    system: Dict[str, Any] = Field(..., description="系统状态")


class PerformanceStatsResponse(BaseModel):
    """性能统计响应模型"""
    total_functions: int = Field(..., description="总函数数")
    total_calls: int = Field(..., description="总调用次数")
    avg_duration_ms: float = Field(..., description="平均执行时间")
    slow_functions: List[Dict[str, Any]] = Field(..., description="慢函数列表")
    error_functions: List[Dict[str, Any]] = Field(..., description="错误函数列表")


@router.get("/health", response_model=HealthCheckResponse, summary="健康检查")
async def health_check():
    """系统健康检查"""
    try:
        health_status = {
            "status": "healthy",
            "timestamp": datetime.now(),
            "services": {},
            "system": {}
        }
        
        # 检查TDengine服务
        try:
            tdengine_health = await tdengine_service_manager.health_check_all()
            health_status["services"]["tdengine"] = {
                "status": "healthy" if any(h.get("status") == "healthy" for h in tdengine_health.values()) else "unhealthy",
                "servers": tdengine_health
            }
        except Exception as e:
            health_status["services"]["tdengine"] = {
                "status": "unhealthy",
                "error": str(e)
            }
        
        # 检查系统资源
        try:
            system_metrics = performance_monitor.collect_system_metrics()
            if system_metrics:
                health_status["system"] = {
                    "cpu_percent": system_metrics.cpu_percent,
                    "memory_percent": system_metrics.memory_percent,
                    "disk_percent": system_metrics.disk_usage_percent,
                    "status": "healthy" if (
                        system_metrics.cpu_percent < 90 and 
                        system_metrics.memory_percent < 90 and 
                        system_metrics.disk_usage_percent < 90
                    ) else "warning"
                }
            else:
                health_status["system"] = {"status": "unknown"}
        except Exception as e:
            health_status["system"] = {
                "status": "error",
                "error": str(e)
            }
        
        # 确定整体状态
        service_statuses = [s.get("status", "unknown") for s in health_status["services"].values()]
        system_status = health_status["system"].get("status", "unknown")
        
        if "unhealthy" in service_statuses or system_status == "error":
            health_status["status"] = "unhealthy"
        elif "warning" in service_statuses or system_status == "warning":
            health_status["status"] = "warning"
        else:
            health_status["status"] = "healthy"
        
        return health_status
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/performance/stats", response_model=PerformanceStatsResponse, summary="性能统计")
async def get_performance_stats(
    slow_threshold_ms: float = Query(1000.0, description="慢函数阈值（毫秒）"),
    limit: int = Query(10, description="返回数量限制")
):
    """获取性能统计信息"""
    try:
        function_stats = performance_monitor.get_function_stats()
        
        # 计算总体统计
        total_functions = len(function_stats)
        total_calls = sum(stats['count'] for stats in function_stats.values())
        total_duration = sum(stats['total_duration'] for stats in function_stats.values())
        avg_duration = total_duration / total_calls if total_calls > 0 else 0
        
        # 获取慢函数和错误函数
        slow_functions = performance_monitor.get_slow_functions(slow_threshold_ms, limit)
        error_functions = performance_monitor.get_error_functions(limit)
        
        return PerformanceStatsResponse(
            total_functions=total_functions,
            total_calls=total_calls,
            avg_duration_ms=avg_duration,
            slow_functions=slow_functions,
            error_functions=error_functions
        )
        
    except Exception as e:
        logger.error(f"Failed to get performance stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/performance/functions", summary="函数性能详情")
async def get_function_performance(
    function_name: Optional[str] = Query(None, description="函数名称"),
    sort_by: str = Query("avg_duration", description="排序字段"),
    order: str = Query("desc", description="排序顺序"),
    limit: int = Query(50, description="返回数量限制")
):
    """获取函数性能详情"""
    try:
        function_stats = performance_monitor.get_function_stats(function_name)
        
        if function_name:
            # 返回特定函数的统计
            return {
                "function": function_name,
                "stats": function_stats
            }
        else:
            # 返回所有函数的统计
            stats_list = []
            for func_name, stats in function_stats.items():
                stats_item = {
                    "function": func_name,
                    **stats
                }
                stats_list.append(stats_item)
            
            # 排序
            reverse = order.lower() == "desc"
            if sort_by in ["count", "total_duration", "avg_duration", "min_duration", "max_duration", "error_count"]:
                stats_list.sort(key=lambda x: x.get(sort_by, 0), reverse=reverse)
            
            return {
                "functions": stats_list[:limit],
                "total": len(stats_list)
            }
        
    except Exception as e:
        logger.error(f"Failed to get function performance: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/performance/metrics", summary="性能指标")
async def get_performance_metrics(
    limit: int = Query(100, description="返回数量限制"),
    function_name: Optional[str] = Query(None, description="函数名称过滤"),
    success_only: bool = Query(False, description="仅成功的调用")
):
    """获取性能指标"""
    try:
        metrics = performance_monitor.get_recent_metrics(limit * 2)  # 获取更多数据用于过滤
        
        # 过滤指标
        filtered_metrics = []
        for metric in metrics:
            if function_name and function_name not in f"{metric.module_name}.{metric.function_name}":
                continue
            if success_only and not metric.success:
                continue
            
            filtered_metrics.append({
                "name": metric.name,
                "duration_ms": metric.duration_ms,
                "timestamp": metric.timestamp.isoformat(),
                "function_name": metric.function_name,
                "module_name": metric.module_name,
                "success": metric.success,
                "error_message": metric.error_message,
                "memory_usage_mb": metric.memory_usage_mb,
                "cpu_percent": metric.cpu_percent,
                "extra_data": metric.extra_data
            })
            
            if len(filtered_metrics) >= limit:
                break
        
        return {
            "metrics": filtered_metrics,
            "total": len(filtered_metrics)
        }
        
    except Exception as e:
        logger.error(f"Failed to get performance metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/system/metrics", summary="系统指标")
async def get_system_metrics(
    minutes: int = Query(60, description="时间范围（分钟）")
):
    """获取系统指标"""
    try:
        # 获取系统指标摘要
        summary = performance_monitor.get_system_metrics_summary(minutes)
        
        # 获取最新的系统指标
        latest_metrics = performance_monitor.collect_system_metrics()
        
        return {
            "summary": summary,
            "latest": {
                "timestamp": latest_metrics.timestamp.isoformat(),
                "cpu_percent": latest_metrics.cpu_percent,
                "memory_percent": latest_metrics.memory_percent,
                "memory_used_mb": latest_metrics.memory_used_mb,
                "memory_available_mb": latest_metrics.memory_available_mb,
                "disk_usage_percent": latest_metrics.disk_usage_percent,
                "disk_used_gb": latest_metrics.disk_used_gb,
                "disk_free_gb": latest_metrics.disk_free_gb,
                "network_bytes_sent": latest_metrics.network_bytes_sent,
                "network_bytes_recv": latest_metrics.network_bytes_recv,
                "active_connections": latest_metrics.active_connections
            } if latest_metrics else None
        }
        
    except Exception as e:
        logger.error(f"Failed to get system metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/alerts", summary="监控告警")
async def get_alerts(
    severity: Optional[str] = Query(None, description="告警级别"),
    limit: int = Query(50, description="返回数量限制")
):
    """获取监控告警"""
    try:
        alerts = []
        
        # 检查慢函数告警
        slow_functions = performance_monitor.get_slow_functions(threshold_ms=5000.0, limit=10)
        for func in slow_functions:
            alerts.append({
                "type": "performance",
                "severity": "warning",
                "message": f"Function {func['function']} is slow (avg: {func['avg_duration_ms']:.2f}ms)",
                "timestamp": datetime.now().isoformat(),
                "details": func
            })
        
        # 检查错误函数告警
        error_functions = performance_monitor.get_error_functions(limit=10)
        for func in error_functions:
            if func['error_rate'] > 0.1:  # 错误率超过10%
                severity_level = "critical" if func['error_rate'] > 0.5 else "warning"
                alerts.append({
                    "type": "error",
                    "severity": severity_level,
                    "message": f"Function {func['function']} has high error rate ({func['error_rate']:.1%})",
                    "timestamp": datetime.now().isoformat(),
                    "details": func
                })
        
        # 检查系统资源告警
        try:
            system_metrics = performance_monitor.collect_system_metrics()
            if system_metrics:
                if system_metrics.cpu_percent > 90:
                    alerts.append({
                        "type": "system",
                        "severity": "critical",
                        "message": f"High CPU usage: {system_metrics.cpu_percent:.1f}%",
                        "timestamp": system_metrics.timestamp.isoformat(),
                        "details": {"cpu_percent": system_metrics.cpu_percent}
                    })
                
                if system_metrics.memory_percent > 90:
                    alerts.append({
                        "type": "system",
                        "severity": "critical",
                        "message": f"High memory usage: {system_metrics.memory_percent:.1f}%",
                        "timestamp": system_metrics.timestamp.isoformat(),
                        "details": {"memory_percent": system_metrics.memory_percent}
                    })
                
                if system_metrics.disk_usage_percent > 90:
                    alerts.append({
                        "type": "system",
                        "severity": "warning",
                        "message": f"High disk usage: {system_metrics.disk_usage_percent:.1f}%",
                        "timestamp": system_metrics.timestamp.isoformat(),
                        "details": {"disk_usage_percent": system_metrics.disk_usage_percent}
                    })
        except Exception:
            pass  # 忽略系统指标收集错误
        
        # 过滤告警级别
        if severity:
            alerts = [alert for alert in alerts if alert['severity'] == severity]
        
        # 按时间排序
        alerts.sort(key=lambda x: x['timestamp'], reverse=True)
        
        return {
            "alerts": alerts[:limit],
            "total": len(alerts),
            "summary": {
                "critical": len([a for a in alerts if a['severity'] == 'critical']),
                "warning": len([a for a in alerts if a['severity'] == 'warning']),
                "info": len([a for a in alerts if a['severity'] == 'info'])
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get alerts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/export", summary="导出监控数据")
async def export_monitoring_data():
    """导出监控数据"""
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"monitoring_export_{timestamp}.json"
        filepath = f"logs/{filename}"
        
        performance_monitor.export_metrics(filepath)
        
        return {
            "success": True,
            "message": "监控数据导出成功",
            "filename": filename,
            "filepath": filepath
        }
        
    except Exception as e:
        logger.error(f"Failed to export monitoring data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/metrics", summary="清理监控数据")
async def clear_monitoring_data(
    confirm: bool = Query(False, description="确认清理")
):
    """清理监控数据"""
    if not confirm:
        raise HTTPException(status_code=400, detail="请设置 confirm=true 确认清理操作")
    
    try:
        # 清理性能指标
        performance_monitor.metrics.clear()
        performance_monitor.function_stats.clear()
        performance_monitor.system_metrics.clear()
        
        logger.info("Monitoring data cleared")
        
        return {
            "success": True,
            "message": "监控数据已清理"
        }
        
    except Exception as e:
        logger.error(f"Failed to clear monitoring data: {e}")
        raise HTTPException(status_code=500, detail=str(e))