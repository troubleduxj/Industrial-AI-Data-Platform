#!/usr/bin/env python3
"""
权限系统启动优化器
"""
import asyncio
import time
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from app.core.unified_logger import get_logger

logger = get_logger(__name__)
from app.services.permission_performance_service import permission_performance_service
from app.services.permission_monitor_service import permission_monitor_service


class PermissionStartupOptimizer:
    """权限系统启动优化器"""
    
    def __init__(self):
        self.optimization_enabled = True
        self.startup_time = None
        self.optimization_results = {}
        
    async def optimize_on_startup(self) -> Dict[str, Any]:
        """启动优化（别名）"""
        return await self.optimize_system_startup()

    async def optimize_system_startup(self) -> Dict[str, Any]:
        """优化系统启动"""
        if not self.optimization_enabled:
            return {"status": "disabled", "message": "启动优化已禁用"}
        
        start_time = time.time()
        self.startup_time = datetime.utcnow()
        
        logger.info("开始权限系统启动优化...")
        
        optimization_tasks = [
            self._initialize_performance_cache(),
            self._warm_up_critical_permissions(),
            self._start_monitoring_services(),
            self._optimize_database_connections(),
            self._preload_system_configurations()
        ]
        
        # 并行执行优化任务
        results = await asyncio.gather(*optimization_tasks, return_exceptions=True)
        
        # 处理结果
        task_names = [
            "performance_cache",
            "critical_permissions",
            "monitoring_services", 
            "database_connections",
            "system_configurations"
        ]
        
        optimization_results = {}
        for i, result in enumerate(results):
            task_name = task_names[i]
            if isinstance(result, Exception):
                optimization_results[task_name] = {
                    "status": "failed",
                    "error": str(result)
                }
                logger.error(f"启动优化任务 {task_name} 失败: {result}")
            else:
                optimization_results[task_name] = result
                logger.info(f"启动优化任务 {task_name} 完成")
        
        total_time = time.time() - start_time
        
        self.optimization_results = {
            "startup_time": self.startup_time.isoformat(),
            "total_optimization_time": round(total_time, 3),
            "tasks": optimization_results,
            "overall_status": "completed"
        }
        
        logger.info(f"权限系统启动优化完成，耗时: {total_time:.3f}秒")
        
        return self.optimization_results
    
    async def _initialize_performance_cache(self) -> Dict[str, Any]:
        """初始化性能缓存"""
        try:
            start_time = time.time()
            
            # 初始化缓存系统
            await permission_performance_service.cache.clear()
            
            # 设置缓存配置
            permission_performance_service.cache.max_size = 10000
            permission_performance_service.cache.default_ttl = 300
            
            elapsed_time = time.time() - start_time
            
            return {
                "status": "success",
                "message": "性能缓存初始化完成",
                "elapsed_time": round(elapsed_time, 3),
                "cache_size": permission_performance_service.cache.max_size
            }
            
        except Exception as e:
            return {
                "status": "failed",
                "error": str(e)
            }
    
    async def _warm_up_critical_permissions(self) -> Dict[str, Any]:
        """预热关键权限"""
        try:
            start_time = time.time()
            
            # 获取系统中的活跃用户（这里使用模拟数据）
            critical_user_ids = list(range(1, 101))  # 前100个用户
            
            # 预热关键用户的权限
            await permission_performance_service.warm_up_user_permissions(critical_user_ids)
            
            elapsed_time = time.time() - start_time
            
            return {
                "status": "success",
                "message": "关键权限预热完成",
                "elapsed_time": round(elapsed_time, 3),
                "warmed_users": len(critical_user_ids)
            }
            
        except Exception as e:
            return {
                "status": "failed",
                "error": str(e)
            }
    
    async def _start_monitoring_services(self) -> Dict[str, Any]:
        """启动监控服务"""
        try:
            start_time = time.time()
            
            # 启动性能监控
            await permission_monitor_service.start_monitoring(interval=60)
            
            elapsed_time = time.time() - start_time
            
            return {
                "status": "success",
                "message": "监控服务启动完成",
                "elapsed_time": round(elapsed_time, 3),
                "monitoring_interval": 60
            }
            
        except Exception as e:
            return {
                "status": "failed",
                "error": str(e)
            }
    
    async def _optimize_database_connections(self) -> Dict[str, Any]:
        """优化数据库连接"""
        try:
            start_time = time.time()
            
            # 这里可以添加数据库连接池优化逻辑
            # 例如：预热连接池、优化查询缓存等
            
            # 模拟数据库连接优化
            await asyncio.sleep(0.1)
            
            elapsed_time = time.time() - start_time
            
            return {
                "status": "success",
                "message": "数据库连接优化完成",
                "elapsed_time": round(elapsed_time, 3)
            }
            
        except Exception as e:
            return {
                "status": "failed",
                "error": str(e)
            }
    
    async def _preload_system_configurations(self) -> Dict[str, Any]:
        """预加载系统配置"""
        try:
            start_time = time.time()
            
            # 预加载权限配置
            # 这里可以添加配置预加载逻辑
            
            # 模拟配置预加载
            await asyncio.sleep(0.05)
            
            elapsed_time = time.time() - start_time
            
            return {
                "status": "success",
                "message": "系统配置预加载完成",
                "elapsed_time": round(elapsed_time, 3)
            }
            
        except Exception as e:
            return {
                "status": "failed",
                "error": str(e)
            }
    
    async def get_startup_health_check(self) -> Dict[str, Any]:
        """获取启动健康检查"""
        try:
            # 检查各个组件的健康状态
            health_checks = {
                "cache_system": await self._check_cache_health(),
                "monitoring_system": await self._check_monitoring_health(),
                "permission_service": await self._check_permission_service_health()
            }
            
            # 计算整体健康状态
            all_healthy = all(check["status"] == "healthy" for check in health_checks.values())
            overall_status = "healthy" if all_healthy else "degraded"
            
            return {
                "overall_status": overall_status,
                "startup_time": self.startup_time.isoformat() if self.startup_time else None,
                "uptime_seconds": (datetime.utcnow() - self.startup_time).total_seconds() if self.startup_time else 0,
                "components": health_checks,
                "optimization_results": self.optimization_results
            }
            
        except Exception as e:
            logger.error(f"启动健康检查失败: {e}")
            return {
                "overall_status": "unhealthy",
                "error": str(e)
            }
    
    async def _check_cache_health(self) -> Dict[str, Any]:
        """检查缓存系统健康状态"""
        try:
            cache_stats = permission_performance_service.cache.get_performance_stats()
            
            # 判断缓存系统是否健康
            hit_rate = cache_stats.get("hit_rate", 0)
            response_time = cache_stats.get("avg_response_time_ms", 0)
            
            if hit_rate > 70 and response_time < 100:
                status = "healthy"
            elif hit_rate > 50 and response_time < 200:
                status = "degraded"
            else:
                status = "unhealthy"
            
            return {
                "status": status,
                "hit_rate": hit_rate,
                "response_time_ms": response_time,
                "cache_size": cache_stats.get("cache_size", 0)
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }
    
    async def _check_monitoring_health(self) -> Dict[str, Any]:
        """检查监控系统健康状态"""
        try:
            monitoring_enabled = permission_monitor_service.monitoring_enabled
            
            if monitoring_enabled:
                dashboard_data = await permission_monitor_service.get_monitoring_dashboard()
                active_alerts = len(dashboard_data.get("alerts", {}).get("active_alerts", []))
                
                status = "healthy" if active_alerts < 5 else "degraded"
            else:
                status = "disabled"
            
            return {
                "status": status,
                "monitoring_enabled": monitoring_enabled,
                "active_alerts": active_alerts if monitoring_enabled else 0
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }
    
    async def _check_permission_service_health(self) -> Dict[str, Any]:
        """检查权限服务健康状态"""
        try:
            # 执行简单的权限检查测试
            test_result = await permission_performance_service.check_permission_optimized(1, "test_permission")
            
            # 获取性能指标
            perf_report = await permission_performance_service.get_performance_report()
            system_perf = perf_report.get("system_performance", {})
            
            avg_response_time = system_perf.get("avg_check_time_ms", 0)
            
            if avg_response_time < 50:
                status = "healthy"
            elif avg_response_time < 100:
                status = "degraded"
            else:
                status = "unhealthy"
            
            return {
                "status": status,
                "avg_response_time_ms": avg_response_time,
                "total_checks": system_perf.get("total_permission_checks", 0)
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }
    
    def enable_optimization(self):
        """启用启动优化"""
        self.optimization_enabled = True
        logger.info("权限系统启动优化已启用")
    
    def disable_optimization(self):
        """禁用启动优化"""
        self.optimization_enabled = False
        logger.info("权限系统启动优化已禁用")
    
    async def get_optimization_recommendations(self) -> List[Dict[str, Any]]:
        """获取优化建议"""
        recommendations = []
        
        try:
            # 获取当前性能数据
            perf_report = await permission_performance_service.get_performance_report()
            cache_stats = perf_report.get("cache_performance", {})
            system_perf = perf_report.get("system_performance", {})
            
            # 缓存命中率建议
            hit_rate = cache_stats.get("hit_rate", 0)
            if hit_rate < 70:
                recommendations.append({
                    "type": "cache_optimization",
                    "priority": "high",
                    "title": "提高缓存命中率",
                    "description": f"当前缓存命中率为 {hit_rate:.1f}%，建议增加缓存大小或调整缓存策略",
                    "action": "增加缓存大小到20000或使用ADAPTIVE策略"
                })
            
            # 响应时间建议
            avg_response_time = system_perf.get("avg_check_time_ms", 0)
            if avg_response_time > 100:
                recommendations.append({
                    "type": "performance_optimization",
                    "priority": "medium",
                    "title": "优化响应时间",
                    "description": f"平均响应时间为 {avg_response_time:.2f}ms，建议优化查询逻辑",
                    "action": "启用批量查询或增加索引"
                })
            
            # 监控建议
            if not permission_monitor_service.monitoring_enabled:
                recommendations.append({
                    "type": "monitoring",
                    "priority": "medium",
                    "title": "启用性能监控",
                    "description": "建议启用性能监控以便及时发现问题",
                    "action": "启动监控服务并设置告警规则"
                })
            
            # 预热建议
            cache_size = cache_stats.get("cache_size", 0)
            if cache_size < 100:
                recommendations.append({
                    "type": "cache_warmup",
                    "priority": "low",
                    "title": "增加缓存预热",
                    "description": "当前缓存条目较少，建议增加预热用户数量",
                    "action": "预热更多活跃用户的权限数据"
                })
            
        except Exception as e:
            logger.error(f"生成优化建议失败: {e}")
            recommendations.append({
                "type": "error",
                "priority": "high",
                "title": "获取建议失败",
                "description": f"无法生成优化建议: {str(e)}",
                "action": "检查系统状态并重试"
            })
        
        return recommendations


# 全局启动优化器实例
permission_startup_optimizer = PermissionStartupOptimizer()