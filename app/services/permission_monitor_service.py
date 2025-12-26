"""
权限系统性能监控和调优服务
"""
import asyncio
import time
import psutil
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import deque, defaultdict
from app.core.unified_logger import get_logger

logger = get_logger(__name__)


@dataclass
class PerformanceSnapshot:
    """性能快照"""
    timestamp: datetime
    cpu_usage: float
    memory_usage: float
    cache_hit_rate: float
    avg_response_time: float
    active_connections: int
    queue_size: int
    error_rate: float


@dataclass
class AlertRule:
    """告警规则"""
    name: str
    metric: str
    threshold: float
    operator: str  # '>', '<', '>=', '<=', '=='
    duration: int  # 持续时间（秒）
    enabled: bool = True
    last_triggered: Optional[datetime] = None
    trigger_count: int = 0


class PermissionMonitorService:
    """权限系统性能监控服务"""
    
    def __init__(self):
        self.monitoring = False
        self.snapshots = deque(maxlen=1000)  # 保留最近1000个快照
        self.alert_rules = []
        self.alerts = deque(maxlen=100)  # 保留最近100个告警
        self.metrics_history = defaultdict(deque)
        
        # 监控配置
        self.monitor_interval = 10  # 10秒监控间隔
        self.snapshot_retention = 3600  # 1小时数据保留
        
        # 性能阈值
        self.performance_thresholds = {
            "cpu_usage": 80.0,
            "memory_usage": 85.0,
            "cache_hit_rate": 70.0,
            "avg_response_time": 1.0,
            "error_rate": 5.0
        }
        
        # 初始化默认告警规则
        self._init_default_alert_rules()
    
    def _init_default_alert_rules(self):
        """初始化默认告警规则"""
        self.alert_rules = [
            AlertRule(
                name="高CPU使用率",
                metric="cpu_usage",
                threshold=80.0,
                operator=">",
                duration=60
            ),
            AlertRule(
                name="高内存使用率",
                metric="memory_usage",
                threshold=85.0,
                operator=">",
                duration=60
            ),
            AlertRule(
                name="低缓存命中率",
                metric="cache_hit_rate",
                threshold=70.0,
                operator="<",
                duration=120
            ),
            AlertRule(
                name="高响应时间",
                metric="avg_response_time",
                threshold=1.0,
                operator=">",
                duration=30
            ),
            AlertRule(
                name="高错误率",
                metric="error_rate",
                threshold=5.0,
                operator=">",
                duration=60
            )
        ]
    
    async def start_monitoring(self):
        """启动性能监控"""
        if self.monitoring:
            return
        
        self.monitoring = True
        logger.info("启动权限系统性能监控")
        
        # 启动监控任务
        asyncio.create_task(self._monitoring_loop())
        asyncio.create_task(self._alert_checker())
        asyncio.create_task(self._cleanup_old_data())
    
    async def stop_monitoring(self):
        """停止性能监控"""
        self.monitoring = False
        logger.info("停止权限系统性能监控")
    
    async def _monitoring_loop(self):
        """监控循环"""
        while self.monitoring:
            try:
                # 收集性能数据
                snapshot = await self._collect_performance_data()
                
                # 存储快照
                self.snapshots.append(snapshot)
                
                # 更新指标历史
                self._update_metrics_history(snapshot)
                
                # 检查性能问题
                await self._check_performance_issues(snapshot)
                
                # 等待下次监控
                await asyncio.sleep(self.monitor_interval)
                
            except Exception as e:
                logger.error(f"性能监控循环失败: {e}")
                await asyncio.sleep(self.monitor_interval)
    
    async def _collect_performance_data(self) -> PerformanceSnapshot:
        """收集性能数据"""
        try:
            # 系统资源使用情况
            cpu_usage = psutil.cpu_percent(interval=1)
            memory_info = psutil.virtual_memory()
            memory_usage = memory_info.percent
            
            # 权限系统性能指标
            from app.services.permission_performance_service import permission_performance_service
            from app.services.async_permission_processor import permission_task_manager
            
            perf_metrics = permission_performance_service.get_performance_metrics()
            task_stats = permission_task_manager.get_stats()
            
            # 解析性能指标
            cache_hit_rate = float(perf_metrics.get("cache_hit_rate", "0%").rstrip("%"))
            avg_response_time = float(perf_metrics.get("avg_response_time", "0s").rstrip("s"))
            
            # 计算错误率
            total_tasks = task_stats.get("processed_tasks", 0) + task_stats.get("failed_tasks", 0)
            error_rate = (task_stats.get("failed_tasks", 0) / total_tasks * 100) if total_tasks > 0 else 0
            
            snapshot = PerformanceSnapshot(
                timestamp=datetime.utcnow(),
                cpu_usage=cpu_usage,
                memory_usage=memory_usage,
                cache_hit_rate=cache_hit_rate,
                avg_response_time=avg_response_time,
                active_connections=task_stats.get("workers", 0),
                queue_size=task_stats.get("queue_size", 0),
                error_rate=error_rate
            )
            
            return snapshot
            
        except Exception as e:
            logger.error(f"收集性能数据失败: {e}")
            # 返回默认快照
            return PerformanceSnapshot(
                timestamp=datetime.utcnow(),
                cpu_usage=0.0,
                memory_usage=0.0,
                cache_hit_rate=0.0,
                avg_response_time=0.0,
                active_connections=0,
                queue_size=0,
                error_rate=0.0
            )
    
    def _update_metrics_history(self, snapshot: PerformanceSnapshot):
        """更新指标历史"""
        metrics = {
            "cpu_usage": snapshot.cpu_usage,
            "memory_usage": snapshot.memory_usage,
            "cache_hit_rate": snapshot.cache_hit_rate,
            "avg_response_time": snapshot.avg_response_time,
            "error_rate": snapshot.error_rate
        }
        
        for metric, value in metrics.items():
            history = self.metrics_history[metric]
            history.append((snapshot.timestamp, value))
            
            # 保持历史数据在合理范围内
            while len(history) > 360:  # 保留最近1小时的数据（10秒间隔）
                history.popleft()
    
    async def _check_performance_issues(self, snapshot: PerformanceSnapshot):
        """检查性能问题"""
        issues = []
        
        # 检查各项指标
        if snapshot.cpu_usage > self.performance_thresholds["cpu_usage"]:
            issues.append(f"CPU使用率过高: {snapshot.cpu_usage:.1f}%")
        
        if snapshot.memory_usage > self.performance_thresholds["memory_usage"]:
            issues.append(f"内存使用率过高: {snapshot.memory_usage:.1f}%")
        
        if snapshot.cache_hit_rate < self.performance_thresholds["cache_hit_rate"]:
            issues.append(f"缓存命中率过低: {snapshot.cache_hit_rate:.1f}%")
        
        if snapshot.avg_response_time > self.performance_thresholds["avg_response_time"]:
            issues.append(f"平均响应时间过长: {snapshot.avg_response_time:.3f}s")
        
        if snapshot.error_rate > self.performance_thresholds["error_rate"]:
            issues.append(f"错误率过高: {snapshot.error_rate:.1f}%")
        
        # 记录性能问题
        if issues:
            logger.warning(f"检测到性能问题: {'; '.join(issues)}")
            
            # 触发自动优化
            await self._trigger_auto_optimization(issues, snapshot)
    
    async def _trigger_auto_optimization(self, issues: List[str], snapshot: PerformanceSnapshot):
        """触发自动优化"""
        try:
            from app.services.permission_performance_service import permission_performance_service
            
            # 根据问题类型执行相应的优化策略
            for issue in issues:
                if "缓存命中率" in issue:
                    # 预热缓存
                    logger.info("触发缓存预热优化")
                    await permission_performance_service.warm_up_cache()
                
                elif "响应时间" in issue:
                    # 优化查询模式
                    logger.info("触发查询模式优化")
                    await permission_performance_service.optimize_query_patterns()
                
                elif "CPU使用率" in issue or "内存使用率" in issue:
                    # 调整工作线程数
                    logger.info("触发资源使用优化")
                    await self._optimize_resource_usage()
            
        except Exception as e:
            logger.error(f"自动优化失败: {e}")
    
    async def _optimize_resource_usage(self):
        """优化资源使用"""
        try:
            from app.services.async_permission_processor import permission_task_manager
            
            # 获取当前统计信息
            stats = permission_task_manager.get_stats()
            
            # 如果队列积压严重，建议增加工作线程
            if stats.get("queue_size", 0) > 100:
                logger.info("建议增加异步处理器工作线程数")
            
            # 清理已完成的任务
            permission_task_manager.cleanup_completed_tasks()
            
        except Exception as e:
            logger.error(f"资源使用优化失败: {e}")
    
    async def _alert_checker(self):
        """告警检查器"""
        while self.monitoring:
            try:
                await self._check_alert_rules()
                await asyncio.sleep(30)  # 30秒检查一次告警
            except Exception as e:
                logger.error(f"告警检查失败: {e}")
                await asyncio.sleep(30)
    
    async def _check_alert_rules(self):
        """检查告警规则"""
        if not self.snapshots:
            return
        
        current_time = datetime.utcnow()
        
        for rule in self.alert_rules:
            if not rule.enabled:
                continue
            
            # 获取指定时间范围内的数据
            duration_start = current_time - timedelta(seconds=rule.duration)
            relevant_snapshots = [
                s for s in self.snapshots
                if s.timestamp >= duration_start
            ]
            
            if not relevant_snapshots:
                continue
            
            # 检查是否满足告警条件
            if self._evaluate_alert_condition(rule, relevant_snapshots):
                await self._trigger_alert(rule)
    
    def _evaluate_alert_condition(self, rule: AlertRule, snapshots: List[PerformanceSnapshot]) -> bool:
        """评估告警条件"""
        try:
            # 获取指标值
            values = []
            for snapshot in snapshots:
                value = getattr(snapshot, rule.metric, 0)
                values.append(value)
            
            if not values:
                return False
            
            # 计算平均值
            avg_value = sum(values) / len(values)
            
            # 评估条件
            if rule.operator == ">":
                return avg_value > rule.threshold
            elif rule.operator == "<":
                return avg_value < rule.threshold
            elif rule.operator == ">=":
                return avg_value >= rule.threshold
            elif rule.operator == "<=":
                return avg_value <= rule.threshold
            elif rule.operator == "==":
                return abs(avg_value - rule.threshold) < 0.01
            
            return False
            
        except Exception as e:
            logger.error(f"评估告警条件失败: {e}")
            return False
    
    async def _trigger_alert(self, rule: AlertRule):
        """触发告警"""
        current_time = datetime.utcnow()
        
        # 检查告警频率限制（避免重复告警）
        if rule.last_triggered:
            time_since_last = current_time - rule.last_triggered
            if time_since_last.total_seconds() < 300:  # 5分钟内不重复告警
                return
        
        # 更新告警规则状态
        rule.last_triggered = current_time
        rule.trigger_count += 1
        
        # 创建告警记录
        alert = {
            "rule_name": rule.name,
            "metric": rule.metric,
            "threshold": rule.threshold,
            "operator": rule.operator,
            "triggered_at": current_time,
            "trigger_count": rule.trigger_count
        }
        
        self.alerts.append(alert)
        
        # 记录告警日志
        logger.warning(f"触发告警: {rule.name} - {rule.metric} {rule.operator} {rule.threshold}")
        
        # 这里可以添加告警通知逻辑（邮件、短信、Webhook等）
        await self._send_alert_notification(alert)
    
    async def _send_alert_notification(self, alert: Dict[str, Any]):
        """发送告警通知"""
        try:
            # 这里可以实现具体的通知逻辑
            # 例如：发送邮件、调用Webhook、发送到消息队列等
            logger.info(f"发送告警通知: {alert['rule_name']}")
            
        except Exception as e:
            logger.error(f"发送告警通知失败: {e}")
    
    async def _cleanup_old_data(self):
        """清理旧数据"""
        while self.monitoring:
            try:
                current_time = datetime.utcnow()
                cutoff_time = current_time - timedelta(seconds=self.snapshot_retention)
                
                # 清理旧快照
                while self.snapshots and self.snapshots[0].timestamp < cutoff_time:
                    self.snapshots.popleft()
                
                # 清理旧告警
                while self.alerts and len(self.alerts) > 50:
                    self.alerts.popleft()
                
                # 每小时清理一次
                await asyncio.sleep(3600)
                
            except Exception as e:
                logger.error(f"清理旧数据失败: {e}")
                await asyncio.sleep(3600)
    
    def get_current_metrics(self) -> Dict[str, Any]:
        """获取当前性能指标"""
        if not self.snapshots:
            return {}
        
        latest = self.snapshots[-1]
        return {
            "timestamp": latest.timestamp.isoformat(),
            "cpu_usage": f"{latest.cpu_usage:.1f}%",
            "memory_usage": f"{latest.memory_usage:.1f}%",
            "cache_hit_rate": f"{latest.cache_hit_rate:.1f}%",
            "avg_response_time": f"{latest.avg_response_time:.3f}s",
            "active_connections": latest.active_connections,
            "queue_size": latest.queue_size,
            "error_rate": f"{latest.error_rate:.1f}%"
        }
    
    def get_metrics_history(self, metric: str, hours: int = 1) -> List[Dict[str, Any]]:
        """获取指标历史数据"""
        if metric not in self.metrics_history:
            return []
        
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        history = self.metrics_history[metric]
        
        return [
            {
                "timestamp": timestamp.isoformat(),
                "value": value
            }
            for timestamp, value in history
            if timestamp >= cutoff_time
        ]
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """获取性能摘要"""
        if not self.snapshots:
            return {"status": "no_data"}
        
        # 计算最近1小时的统计数据
        recent_snapshots = [
            s for s in self.snapshots
            if s.timestamp >= datetime.utcnow() - timedelta(hours=1)
        ]
        
        if not recent_snapshots:
            return {"status": "no_recent_data"}
        
        # 计算平均值
        avg_cpu = sum(s.cpu_usage for s in recent_snapshots) / len(recent_snapshots)
        avg_memory = sum(s.memory_usage for s in recent_snapshots) / len(recent_snapshots)
        avg_cache_hit = sum(s.cache_hit_rate for s in recent_snapshots) / len(recent_snapshots)
        avg_response_time = sum(s.avg_response_time for s in recent_snapshots) / len(recent_snapshots)
        avg_error_rate = sum(s.error_rate for s in recent_snapshots) / len(recent_snapshots)
        
        # 评估整体健康状态
        health_score = 100
        if avg_cpu > 80: health_score -= 20
        if avg_memory > 85: health_score -= 20
        if avg_cache_hit < 70: health_score -= 15
        if avg_response_time > 1.0: health_score -= 15
        if avg_error_rate > 5: health_score -= 30
        
        health_status = "excellent" if health_score >= 90 else \
                       "good" if health_score >= 70 else \
                       "fair" if health_score >= 50 else "poor"
        
        return {
            "status": "ok",
            "health_score": max(0, health_score),
            "health_status": health_status,
            "period": "1 hour",
            "sample_count": len(recent_snapshots),
            "averages": {
                "cpu_usage": f"{avg_cpu:.1f}%",
                "memory_usage": f"{avg_memory:.1f}%",
                "cache_hit_rate": f"{avg_cache_hit:.1f}%",
                "response_time": f"{avg_response_time:.3f}s",
                "error_rate": f"{avg_error_rate:.1f}%"
            },
            "recent_alerts": len([
                a for a in self.alerts
                if a["triggered_at"] >= datetime.utcnow() - timedelta(hours=1)
            ])
        }
    
    def get_alert_rules(self) -> List[Dict[str, Any]]:
        """获取告警规则"""
        return [
            {
                "name": rule.name,
                "metric": rule.metric,
                "threshold": rule.threshold,
                "operator": rule.operator,
                "duration": rule.duration,
                "enabled": rule.enabled,
                "trigger_count": rule.trigger_count,
                "last_triggered": rule.last_triggered.isoformat() if rule.last_triggered else None
            }
            for rule in self.alert_rules
        ]
    
    def get_recent_alerts(self, hours: int = 24) -> List[Dict[str, Any]]:
        """获取最近的告警"""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        return [
            {
                **alert,
                "triggered_at": alert["triggered_at"].isoformat()
            }
            for alert in self.alerts
            if alert["triggered_at"] >= cutoff_time
        ]
    
    def update_alert_rule(self, rule_name: str, **kwargs):
        """更新告警规则"""
        for rule in self.alert_rules:
            if rule.name == rule_name:
                for key, value in kwargs.items():
                    if hasattr(rule, key):
                        setattr(rule, key, value)
                logger.info(f"更新告警规则: {rule_name}")
                return True
        
        logger.warning(f"告警规则不存在: {rule_name}")
        return False
    
    def add_alert_rule(self, rule: AlertRule):
        """添加告警规则"""
        self.alert_rules.append(rule)
        logger.info(f"添加告警规则: {rule.name}")


# 全局权限监控服务实例
permission_monitor_service = PermissionMonitorService()