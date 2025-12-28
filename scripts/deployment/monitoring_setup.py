#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
监控和告警设置
实现系统监控、性能指标收集和告警通知
"""

import asyncio
import time
from datetime import datetime
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from loguru import logger


class AlertLevel(Enum):
    """告警级别"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass
class MetricPoint:
    """指标数据点"""
    name: str
    value: float
    timestamp: datetime
    tags: Dict[str, str] = field(default_factory=dict)


@dataclass
class Alert:
    """告警"""
    level: AlertLevel
    title: str
    message: str
    timestamp: datetime
    metric_name: Optional[str] = None
    metric_value: Optional[float] = None
    threshold: Optional[float] = None


class MetricsCollector:
    """指标收集器"""
    
    def __init__(self):
        self.metrics: Dict[str, List[MetricPoint]] = {}
        self.max_history = 1000  # 每个指标最多保留1000个数据点
    
    def record(self, name: str, value: float, tags: Dict[str, str] = None):
        """记录指标"""
        point = MetricPoint(
            name=name,
            value=value,
            timestamp=datetime.now(),
            tags=tags or {}
        )
        
        if name not in self.metrics:
            self.metrics[name] = []
        
        self.metrics[name].append(point)
        
        # 限制历史数据量
        if len(self.metrics[name]) > self.max_history:
            self.metrics[name] = self.metrics[name][-self.max_history:]
    
    def get_latest(self, name: str) -> Optional[MetricPoint]:
        """获取最新指标值"""
        if name in self.metrics and self.metrics[name]:
            return self.metrics[name][-1]
        return None
    
    def get_average(self, name: str, count: int = 10) -> Optional[float]:
        """获取最近N个数据点的平均值"""
        if name not in self.metrics or not self.metrics[name]:
            return None
        
        points = self.metrics[name][-count:]
        return sum(p.value for p in points) / len(points)
    
    def get_all_metrics(self) -> Dict[str, Any]:
        """获取所有指标的最新值"""
        result = {}
        for name, points in self.metrics.items():
            if points:
                latest = points[-1]
                result[name] = {
                    "value": latest.value,
                    "timestamp": latest.timestamp.isoformat(),
                    "tags": latest.tags
                }
        return result


class AlertManager:
    """告警管理器"""
    
    def __init__(self):
        self.alerts: List[Alert] = []
        self.handlers: List[Callable[[Alert], None]] = []
        self.max_alerts = 100
    
    def add_handler(self, handler: Callable[[Alert], None]):
        """添加告警处理器"""
        self.handlers.append(handler)
    
    def send_alert(self, alert: Alert):
        """发送告警"""
        self.alerts.append(alert)
        
        # 限制告警历史
        if len(self.alerts) > self.max_alerts:
            self.alerts = self.alerts[-self.max_alerts:]
        
        # 调用所有处理器
        for handler in self.handlers:
            try:
                handler(alert)
            except Exception as e:
                logger.error(f"告警处理器执行失败: {e}")
        
        # 记录日志
        log_method = {
            AlertLevel.INFO: logger.info,
            AlertLevel.WARNING: logger.warning,
            AlertLevel.CRITICAL: logger.error
        }.get(alert.level, logger.info)
        
        log_method(f"[{alert.level.value.upper()}] {alert.title}: {alert.message}")
    
    def get_recent_alerts(self, count: int = 20) -> List[Dict[str, Any]]:
        """获取最近的告警"""
        return [
            {
                "level": a.level.value,
                "title": a.title,
                "message": a.message,
                "timestamp": a.timestamp.isoformat(),
                "metric_name": a.metric_name,
                "metric_value": a.metric_value,
                "threshold": a.threshold
            }
            for a in self.alerts[-count:]
        ]


class SystemMonitor:
    """系统监控器"""
    
    def __init__(self):
        self.metrics_collector = MetricsCollector()
        self.alert_manager = AlertManager()
        self.running = False
        self._task = None
        
        # 阈值配置
        self.thresholds = {
            "api_response_time": {"warning": 0.5, "critical": 1.0},
            "cpu_usage": {"warning": 70.0, "critical": 90.0},
            "memory_usage": {"warning": 70.0, "critical": 90.0},
            "disk_usage": {"warning": 80.0, "critical": 95.0},
            "db_connection_pool": {"warning": 80.0, "critical": 95.0},
            "error_rate": {"warning": 1.0, "critical": 5.0}
        }
    
    async def start(self, interval: int = 30):
        """启动监控"""
        self.running = True
        logger.info(f"系统监控已启动，采集间隔: {interval}秒")
        
        while self.running:
            try:
                await self._collect_metrics()
                await self._check_thresholds()
            except Exception as e:
                logger.error(f"监控采集失败: {e}")
            
            await asyncio.sleep(interval)
    
    def stop(self):
        """停止监控"""
        self.running = False
        logger.info("系统监控已停止")
    
    async def _collect_metrics(self):
        """收集系统指标"""
        try:
            import psutil
            
            # CPU使用率
            cpu_percent = psutil.cpu_percent(interval=1)
            self.metrics_collector.record("cpu_usage", cpu_percent)
            
            # 内存使用率
            memory = psutil.virtual_memory()
            self.metrics_collector.record("memory_usage", memory.percent)
            self.metrics_collector.record("memory_available_gb", memory.available / (1024**3))
            
            # 磁盘使用率
            disk = psutil.disk_usage("/")
            self.metrics_collector.record("disk_usage", disk.percent)
            self.metrics_collector.record("disk_free_gb", disk.free / (1024**3))
            
            # 网络IO
            net_io = psutil.net_io_counters()
            self.metrics_collector.record("network_bytes_sent", net_io.bytes_sent)
            self.metrics_collector.record("network_bytes_recv", net_io.bytes_recv)
            
        except ImportError:
            logger.warning("psutil未安装，跳过系统指标收集")
        except Exception as e:
            logger.error(f"收集系统指标失败: {e}")
        
        # 收集应用指标
        await self._collect_app_metrics()
    
    async def _collect_app_metrics(self):
        """收集应用指标"""
        try:
            # 数据库连接状态
            from app.models.platform_upgrade import AssetCategory, Asset
            
            category_count = await AssetCategory.all().count()
            asset_count = await Asset.all().count()
            
            self.metrics_collector.record("asset_category_count", category_count)
            self.metrics_collector.record("asset_count", asset_count)
            
        except Exception as e:
            logger.debug(f"收集应用指标失败: {e}")
    
    async def _check_thresholds(self):
        """检查阈值并发送告警"""
        for metric_name, thresholds in self.thresholds.items():
            latest = self.metrics_collector.get_latest(metric_name)
            if not latest:
                continue
            
            value = latest.value
            warning_threshold = thresholds.get("warning")
            critical_threshold = thresholds.get("critical")
            
            if critical_threshold and value >= critical_threshold:
                self.alert_manager.send_alert(Alert(
                    level=AlertLevel.CRITICAL,
                    title=f"{metric_name} 超过临界阈值",
                    message=f"当前值: {value:.2f}, 阈值: {critical_threshold}",
                    timestamp=datetime.now(),
                    metric_name=metric_name,
                    metric_value=value,
                    threshold=critical_threshold
                ))
            elif warning_threshold and value >= warning_threshold:
                self.alert_manager.send_alert(Alert(
                    level=AlertLevel.WARNING,
                    title=f"{metric_name} 超过警告阈值",
                    message=f"当前值: {value:.2f}, 阈值: {warning_threshold}",
                    timestamp=datetime.now(),
                    metric_name=metric_name,
                    metric_value=value,
                    threshold=warning_threshold
                ))
    
    def record_api_response_time(self, endpoint: str, response_time: float):
        """记录API响应时间"""
        self.metrics_collector.record(
            "api_response_time",
            response_time,
            tags={"endpoint": endpoint}
        )
    
    def record_error(self, error_type: str):
        """记录错误"""
        self.metrics_collector.record(
            "error_count",
            1,
            tags={"type": error_type}
        )
    
    def get_health_status(self) -> Dict[str, Any]:
        """获取健康状态"""
        metrics = self.metrics_collector.get_all_metrics()
        alerts = self.alert_manager.get_recent_alerts(10)
        
        # 判断整体健康状态
        critical_alerts = [a for a in alerts if a["level"] == "critical"]
        warning_alerts = [a for a in alerts if a["level"] == "warning"]
        
        if critical_alerts:
            status = "critical"
        elif warning_alerts:
            status = "warning"
        else:
            status = "healthy"
        
        return {
            "status": status,
            "timestamp": datetime.now().isoformat(),
            "metrics": metrics,
            "recent_alerts": alerts,
            "uptime_seconds": time.time()  # 简化的运行时间
        }


# 全局监控实例
system_monitor = SystemMonitor()


def get_monitor() -> SystemMonitor:
    """获取监控实例"""
    return system_monitor


# 告警处理器示例
def console_alert_handler(alert: Alert):
    """控制台告警处理器"""
    print(f"[ALERT] [{alert.level.value}] {alert.title}: {alert.message}")


def email_alert_handler(alert: Alert):
    """邮件告警处理器（示例）"""
    # 实际实现需要配置SMTP
    pass


def webhook_alert_handler(alert: Alert):
    """Webhook告警处理器（示例）"""
    # 实际实现需要发送HTTP请求
    pass


# 注册默认处理器
system_monitor.alert_manager.add_handler(console_alert_handler)


if __name__ == "__main__":
    # 测试监控
    async def test_monitor():
        monitor = get_monitor()
        
        # 模拟记录一些指标
        monitor.record_api_response_time("/api/v3/assets", 0.15)
        monitor.record_api_response_time("/api/v3/predictions", 0.8)
        
        # 获取健康状态
        health = monitor.get_health_status()
        print("健康状态:", health)
    
    asyncio.run(test_monitor())
