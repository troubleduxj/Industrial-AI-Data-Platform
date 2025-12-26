#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
权限缓存监控服务
实现缓存命中率监控、性能统计、健康检查和告警功能
"""

import asyncio
import json
from typing import List, Dict, Set, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from collections import defaultdict, deque

from app.core.permission_cache import permission_cache_manager
from app.core.unified_logger import get_logger

logger = get_logger(__name__)


@dataclass
class AlertRule:
    """告警规则"""
    name: str
    metric: str  # 监控指标名称
    operator: str  # 操作符: gt, lt, gte, lte, eq, ne
    threshold: float  # 阈值
    duration: int  # 持续时间（秒）
    enabled: bool = True
    description: str = ""


@dataclass
class Alert:
    """告警信息"""
    rule_name: str
    metric: str
    current_value: float
    threshold: float
    message: str
    level: str  # info, warning, error, critical
    timestamp: datetime
    resolved: bool = False
    resolved_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "rule_name": self.rule_name,
            "metric": self.metric,
            "current_value": self.current_value,
            "threshold": self.threshold,
            "message": self.message,
            "level": self.level,
            "timestamp": self.timestamp.isoformat(),
            "resolved": self.resolved,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None
        }


class PermissionCacheMonitor:
    """权限缓存监控服务"""
    
    def __init__(self):
        self.cache_manager = permission_cache_manager
        
        # 监控配置
        self.monitor_interval = 60  # 监控间隔（秒）
        self.metrics_retention_hours = 24  # 指标保留时间（小时）
        self.alert_retention_hours = 72  # 告警保留时间（小时）
        
        # 监控数据
        self.metrics_history = deque(maxlen=1440)  # 24小时的分钟级数据
        self.alerts = deque(maxlen=1000)  # 最多保存1000条告警
        self.active_alerts = {}  # 活跃告警
        
        # 告警规则
        self.alert_rules = [
            AlertRule(
                name="low_hit_rate",
                metric="hit_rate",
                operator="lt",
                threshold=0.8,  # 命中率低于80%
                duration=300,  # 持续5分钟
                description="缓存命中率过低"
            ),
            AlertRule(
                name="high_error_rate",
                metric="error_rate",
                operator="gt",
                threshold=0.05,  # 错误率高于5%
                duration=180,  # 持续3分钟
                description="缓存错误率过高"
            ),
            AlertRule(
                name="slow_response",
                metric="avg_response_time",
                operator="gt",
                threshold=100,  # 平均响应时间超过100ms
                duration=300,  # 持续5分钟
                description="缓存响应时间过慢"
            ),
            AlertRule(
                name="high_memory_usage",
                metric="memory_usage_percent",
                operator="gt",
                threshold=85,  # 内存使用率超过85%
                duration=600,  # 持续10分钟
                description="Redis内存使用率过高"
            )
        ]
        
        # 监控状态
        self.is_monitoring = False
        self.monitor_task = None
        self.last_metrics = None
    
    async def start_monitoring(self):
        """开始监控"""
        if self.is_monitoring:
            logger.warning("权限缓存监控已在运行")
            return
        
        self.is_monitoring = True
        self.monitor_task = asyncio.create_task(self._monitor_loop())
        logger.info("权限缓存监控已启动")
    
    async def stop_monitoring(self):
        """停止监控"""
        if not self.is_monitoring:
            return
        
        self.is_monitoring = False
        if self.monitor_task:
            self.monitor_task.cancel()
            try:
                await self.monitor_task
            except asyncio.CancelledError:
                pass
        
        logger.info("权限缓存监控已停止")
    
    async def _monitor_loop(self):
        """监控循环"""
        logger.info(f"权限缓存监控循环启动，间隔: {self.monitor_interval}秒")
        
        while self.is_monitoring:
            try:
                # 收集指标
                metrics = await self._collect_metrics()
                
                if metrics:
                    # 保存指标
                    self._save_metrics(metrics)
                    
                    # 检查告警
                    await self._check_alerts(metrics)
                    
                    # 清理过期数据
                    self._cleanup_old_data()
                    
                    self.last_metrics = metrics
                
                # 等待下一次监控
                await asyncio.sleep(self.monitor_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"权限缓存监控循环异常: {e}")
                await asyncio.sleep(self.monitor_interval)
    
    async def _collect_metrics(self) -> Optional[Dict[str, Any]]:
        """收集监控指标"""
        try:
            # 获取缓存统计信息
            cache_stats = await self.cache_manager.get_cache_statistics()
            
            # 获取Redis信息
            redis_info = await self.cache_manager.cache_manager.get_cache_info()
            
            # 获取性能报告
            performance_report = await self.cache_manager.get_performance_report(hours=1)
            
            # 计算衍生指标
            basic_stats = cache_stats.get("basic_stats", {})
            performance = cache_stats.get("performance", {})
            
            # 错误率
            total_requests = basic_stats.get("total_requests", 0)
            errors = basic_stats.get("errors", 0)
            error_rate = (errors / total_requests) if total_requests > 0 else 0
            
            # 内存使用率
            used_memory = redis_info.get("used_memory", 0)
            # 假设最大内存为1GB（实际应该从Redis配置获取）
            max_memory = 1024 * 1024 * 1024
            memory_usage_percent = (used_memory / max_memory * 100) if max_memory > 0 else 0
            
            # 组装指标
            metrics = {
                "timestamp": datetime.now(),
                "hit_rate": basic_stats.get("hit_rate", 0),
                "error_rate": error_rate,
                "avg_response_time": basic_stats.get("avg_response_time", 0),
                "total_requests": total_requests,
                "hits": basic_stats.get("hits", 0),
                "misses": basic_stats.get("misses", 0),
                "errors": errors,
                "sets": basic_stats.get("sets", 0),
                "deletes": basic_stats.get("deletes", 0),
                "memory_usage_bytes": used_memory,
                "memory_usage_percent": memory_usage_percent,
                "connected_clients": redis_info.get("connected_clients", 0),
                "total_cache_keys": cache_stats.get("cache_keys", {}).get("total", 0),
                "slow_queries": performance.get("slow_queries", 0),
                "cache_key_distribution": cache_stats.get("cache_keys", {}).get("by_type", {}),
                "performance_summary": performance_report.get("overall", {}) if isinstance(performance_report, dict) else {}
            }
            
            return metrics
            
        except Exception as e:
            logger.error(f"收集监控指标失败: {e}")
            return None
    
    def _save_metrics(self, metrics: Dict[str, Any]):
        """保存指标数据"""
        # 添加到历史记录
        self.metrics_history.append(metrics)
        
        # 记录关键指标到日志
        logger.debug(
            f"缓存指标: 命中率={metrics['hit_rate']:.2%}, "
            f"错误率={metrics['error_rate']:.2%}, "
            f"响应时间={metrics['avg_response_time']:.2f}ms, "
            f"总请求={metrics['total_requests']}"
        )
    
    async def _check_alerts(self, metrics: Dict[str, Any]):
        """检查告警规则"""
        current_time = datetime.now()
        
        for rule in self.alert_rules:
            if not rule.enabled:
                continue
            
            try:
                # 获取指标值
                metric_value = metrics.get(rule.metric)
                if metric_value is None:
                    continue
                
                # 检查阈值
                should_alert = self._evaluate_threshold(metric_value, rule.operator, rule.threshold)
                
                if should_alert:
                    # 检查是否已有活跃告警
                    if rule.name in self.active_alerts:
                        # 更新现有告警
                        alert = self.active_alerts[rule.name]
                        alert.current_value = metric_value
                        alert.timestamp = current_time
                    else:
                        # 创建新告警
                        alert = Alert(
                            rule_name=rule.name,
                            metric=rule.metric,
                            current_value=metric_value,
                            threshold=rule.threshold,
                            message=f"{rule.description}: {rule.metric}={metric_value}, 阈值={rule.threshold}",
                            level=self._get_alert_level(rule.name),
                            timestamp=current_time
                        )
                        
                        self.active_alerts[rule.name] = alert
                        self.alerts.append(alert)
                        
                        # 记录告警日志
                        logger.warning(f"权限缓存告警: {alert.message}")
                
                else:
                    # 检查是否需要解除告警
                    if rule.name in self.active_alerts:
                        alert = self.active_alerts[rule.name]
                        alert.resolved = True
                        alert.resolved_at = current_time
                        
                        del self.active_alerts[rule.name]
                        
                        logger.info(f"权限缓存告警已解除: {rule.name}")
                
            except Exception as e:
                logger.error(f"检查告警规则失败: {rule.name}, error={e}")
    
    def _evaluate_threshold(self, value: float, operator: str, threshold: float) -> bool:
        """评估阈值条件"""
        if operator == "gt":
            return value > threshold
        elif operator == "lt":
            return value < threshold
        elif operator == "gte":
            return value >= threshold
        elif operator == "lte":
            return value <= threshold
        elif operator == "eq":
            return value == threshold
        elif operator == "ne":
            return value != threshold
        else:
            logger.warning(f"未知的操作符: {operator}")
            return False
    
    def _get_alert_level(self, rule_name: str) -> str:
        """获取告警级别"""
        level_mapping = {
            "low_hit_rate": "warning",
            "high_error_rate": "error",
            "slow_response": "warning",
            "high_memory_usage": "critical"
        }
        return level_mapping.get(rule_name, "info")
    
    def _cleanup_old_data(self):
        """清理过期数据"""
        current_time = datetime.now()
        
        # 清理过期告警
        cutoff_time = current_time - timedelta(hours=self.alert_retention_hours)
        
        # 过滤过期告警
        self.alerts = deque(
            [alert for alert in self.alerts if alert.timestamp >= cutoff_time],
            maxlen=1000
        )
    
    async def get_monitoring_status(self) -> Dict[str, Any]:
        """获取监控状态"""
        try:
            current_time = datetime.now()
            
            # 基本状态
            status = {
                "is_monitoring": self.is_monitoring,
                "monitor_interval": self.monitor_interval,
                "last_check": self.last_metrics["timestamp"].isoformat() if self.last_metrics else None,
                "metrics_count": len(self.metrics_history),
                "active_alerts_count": len(self.active_alerts),
                "total_alerts_count": len(self.alerts)
            }
            
            # 活跃告警
            if self.active_alerts:
                status["active_alerts"] = [
                    alert.to_dict() for alert in self.active_alerts.values()
                ]
            
            # 最新指标
            if self.last_metrics:
                status["latest_metrics"] = {
                    "hit_rate": self.last_metrics["hit_rate"],
                    "error_rate": self.last_metrics["error_rate"],
                    "avg_response_time": self.last_metrics["avg_response_time"],
                    "total_requests": self.last_metrics["total_requests"],
                    "memory_usage_percent": self.last_metrics["memory_usage_percent"],
                    "total_cache_keys": self.last_metrics["total_cache_keys"]
                }
            
            # 告警规则
            status["alert_rules"] = [
                {
                    "name": rule.name,
                    "metric": rule.metric,
                    "operator": rule.operator,
                    "threshold": rule.threshold,
                    "duration": rule.duration,
                    "enabled": rule.enabled,
                    "description": rule.description
                }
                for rule in self.alert_rules
            ]
            
            status["timestamp"] = current_time.isoformat()
            return status
            
        except Exception as e:
            logger.error(f"获取监控状态失败: {e}")
            return {"error": str(e), "timestamp": datetime.now().isoformat()}
    
    async def get_metrics_history(self, hours: int = 1) -> Dict[str, Any]:
        """获取指标历史"""
        try:
            cutoff_time = datetime.now() - timedelta(hours=hours)
            
            # 过滤指定时间范围的指标
            filtered_metrics = [
                metrics for metrics in self.metrics_history
                if metrics["timestamp"] >= cutoff_time
            ]
            
            if not filtered_metrics:
                return {
                    "message": f"过去{hours}小时内无指标数据",
                    "timestamp": datetime.now().isoformat()
                }
            
            # 计算统计信息
            hit_rates = [m["hit_rate"] for m in filtered_metrics]
            error_rates = [m["error_rate"] for m in filtered_metrics]
            response_times = [m["avg_response_time"] for m in filtered_metrics]
            
            return {
                "time_range_hours": hours,
                "data_points": len(filtered_metrics),
                "summary": {
                    "hit_rate": {
                        "avg": sum(hit_rates) / len(hit_rates),
                        "min": min(hit_rates),
                        "max": max(hit_rates)
                    },
                    "error_rate": {
                        "avg": sum(error_rates) / len(error_rates),
                        "min": min(error_rates),
                        "max": max(error_rates)
                    },
                    "response_time": {
                        "avg": sum(response_times) / len(response_times),
                        "min": min(response_times),
                        "max": max(response_times)
                    }
                },
                "metrics": [
                    {
                        "timestamp": m["timestamp"].isoformat(),
                        "hit_rate": m["hit_rate"],
                        "error_rate": m["error_rate"],
                        "avg_response_time": m["avg_response_time"],
                        "total_requests": m["total_requests"],
                        "memory_usage_percent": m["memory_usage_percent"]
                    }
                    for m in filtered_metrics
                ],
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"获取指标历史失败: {e}")
            return {"error": str(e), "timestamp": datetime.now().isoformat()}
    
    async def get_alert_history(self, hours: int = 24) -> Dict[str, Any]:
        """获取告警历史"""
        try:
            cutoff_time = datetime.now() - timedelta(hours=hours)
            
            # 过滤指定时间范围的告警
            filtered_alerts = [
                alert for alert in self.alerts
                if alert.timestamp >= cutoff_time
            ]
            
            # 按级别统计
            level_counts = defaultdict(int)
            for alert in filtered_alerts:
                level_counts[alert.level] += 1
            
            return {
                "time_range_hours": hours,
                "total_alerts": len(filtered_alerts),
                "by_level": dict(level_counts),
                "alerts": [alert.to_dict() for alert in filtered_alerts],
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"获取告警历史失败: {e}")
            return {"error": str(e), "timestamp": datetime.now().isoformat()}
    
    def add_alert_rule(self, rule: AlertRule) -> bool:
        """添加告警规则"""
        try:
            # 检查是否已存在同名规则
            existing_rule = next((r for r in self.alert_rules if r.name == rule.name), None)
            if existing_rule:
                logger.warning(f"告警规则已存在: {rule.name}")
                return False
            
            self.alert_rules.append(rule)
            logger.info(f"添加告警规则: {rule.name}")
            return True
            
        except Exception as e:
            logger.error(f"添加告警规则失败: {e}")
            return False
    
    def update_alert_rule(self, rule_name: str, **kwargs) -> bool:
        """更新告警规则"""
        try:
            rule = next((r for r in self.alert_rules if r.name == rule_name), None)
            if not rule:
                logger.warning(f"告警规则不存在: {rule_name}")
                return False
            
            # 更新规则属性
            for key, value in kwargs.items():
                if hasattr(rule, key):
                    setattr(rule, key, value)
            
            logger.info(f"更新告警规则: {rule_name}")
            return True
            
        except Exception as e:
            logger.error(f"更新告警规则失败: {e}")
            return False
    
    def remove_alert_rule(self, rule_name: str) -> bool:
        """删除告警规则"""
        try:
            rule = next((r for r in self.alert_rules if r.name == rule_name), None)
            if not rule:
                logger.warning(f"告警规则不存在: {rule_name}")
                return False
            
            self.alert_rules.remove(rule)
            
            # 清除相关的活跃告警
            if rule_name in self.active_alerts:
                del self.active_alerts[rule_name]
            
            logger.info(f"删除告警规则: {rule_name}")
            return True
            
        except Exception as e:
            logger.error(f"删除告警规则失败: {e}")
            return False
    
    async def health_check(self) -> Dict[str, Any]:
        """监控服务健康检查"""
        try:
            current_time = datetime.now()
            
            # 检查监控状态
            monitoring_ok = self.is_monitoring
            
            # 检查最近是否有指标数据
            recent_metrics_ok = (
                self.last_metrics is not None and
                (current_time - self.last_metrics["timestamp"]).total_seconds() < self.monitor_interval * 2
            )
            
            # 检查缓存管理器健康状态
            cache_health = await self.cache_manager.health_check()
            cache_ok = cache_health.get("status") == "healthy"
            
            # 整体健康状态
            overall_status = "healthy" if (monitoring_ok and recent_metrics_ok and cache_ok) else "unhealthy"
            
            return {
                "status": overall_status,
                "monitoring": {
                    "is_running": monitoring_ok,
                    "recent_metrics": recent_metrics_ok,
                    "last_check": self.last_metrics["timestamp"].isoformat() if self.last_metrics else None
                },
                "cache": cache_health,
                "active_alerts": len(self.active_alerts),
                "timestamp": current_time.isoformat()
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }


# 全局权限缓存监控服务实例
permission_cache_monitor = PermissionCacheMonitor()


# 便捷函数
async def start_cache_monitoring():
    """启动缓存监控"""
    await permission_cache_monitor.start_monitoring()


async def stop_cache_monitoring():
    """停止缓存监控"""
    await permission_cache_monitor.stop_monitoring()


async def get_cache_monitoring_status() -> Dict[str, Any]:
    """获取缓存监控状态"""
    return await permission_cache_monitor.get_monitoring_status()


if __name__ == "__main__":
    # 测试权限缓存监控
    async def test_monitor():
        from app.core.permission_cache import init_permission_cache
        
        await init_permission_cache()
        
        print("测试权限缓存监控...")
        
        # 启动监控
        await permission_cache_monitor.start_monitoring()
        
        # 等待一段时间收集数据
        await asyncio.sleep(10)
        
        # 获取监控状态
        status = await permission_cache_monitor.get_monitoring_status()
        print(f"监控状态: {json.dumps(status, indent=2, ensure_ascii=False)}")
        
        # 停止监控
        await permission_cache_monitor.stop_monitoring()
        
        print("权限缓存监控测试完成")
    
    asyncio.run(test_monitor())