#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
采集状态监控

实现数据采集层的状态监控和统计信息收集功能。
提供实时状态查询、健康检查和性能指标。

需求: 5.5 - 采集层提供数据采集状态监控和统计接口
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, Any, List, Optional, Callable
import threading

from platform_core.ingestion.adapters.base_adapter import (
    BaseAdapter,
    AdapterStatus,
    AdapterStatistics,
)
from platform_core.ingestion.retry_manager import ErrorLogger, get_error_logger

logger = logging.getLogger(__name__)


class HealthStatus(str, Enum):
    """健康状态枚举"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class AdapterHealthInfo:
    """
    适配器健康信息
    
    Attributes:
        name: 适配器名称
        protocol: 协议类型
        status: 运行状态
        health: 健康状态
        statistics: 统计信息
        last_check_time: 最后检查时间
        issues: 问题列表
    """
    name: str
    protocol: str
    status: AdapterStatus
    health: HealthStatus
    statistics: Dict[str, Any]
    last_check_time: datetime
    issues: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "protocol": self.protocol,
            "status": self.status.value,
            "health": self.health.value,
            "statistics": self.statistics,
            "last_check_time": self.last_check_time.isoformat(),
            "issues": self.issues,
        }


@dataclass
class IngestionMetrics:
    """
    采集指标
    
    Attributes:
        total_data_points: 总数据点数
        data_points_per_second: 每秒数据点数
        total_bytes: 总字节数
        bytes_per_second: 每秒字节数
        error_rate: 错误率
        latency_ms: 延迟（毫秒）
    """
    total_data_points: int = 0
    data_points_per_second: float = 0.0
    total_bytes: int = 0
    bytes_per_second: float = 0.0
    error_rate: float = 0.0
    latency_ms: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_data_points": self.total_data_points,
            "data_points_per_second": round(self.data_points_per_second, 2),
            "total_bytes": self.total_bytes,
            "bytes_per_second": round(self.bytes_per_second, 2),
            "error_rate": round(self.error_rate, 4),
            "latency_ms": round(self.latency_ms, 2),
        }


class IngestionMonitor:
    """
    采集状态监控器
    
    监控所有数据采集适配器的状态和性能。
    
    使用示例:
    ```python
    monitor = IngestionMonitor()
    
    # 注册适配器
    monitor.register_adapter(mqtt_adapter)
    monitor.register_adapter(http_adapter)
    
    # 启动监控
    await monitor.start()
    
    # 获取状态
    status = monitor.get_overall_status()
    health = monitor.get_health_report()
    metrics = monitor.get_metrics()
    ```
    """
    
    def __init__(
        self,
        check_interval: float = 10.0,
        error_logger: Optional[ErrorLogger] = None
    ):
        """
        初始化监控器
        
        Args:
            check_interval: 健康检查间隔（秒）
            error_logger: 错误日志记录器
        """
        self._adapters: Dict[str, BaseAdapter] = {}
        self._health_info: Dict[str, AdapterHealthInfo] = {}
        self._check_interval = check_interval
        self._error_logger = error_logger or get_error_logger()
        
        # 监控状态
        self._running = False
        self._monitor_task: Optional[asyncio.Task] = None
        
        # 指标收集
        self._metrics = IngestionMetrics()
        self._last_metrics_time = datetime.now()
        self._last_data_points = 0
        self._last_bytes = 0
        
        # 回调
        self._on_status_change_callbacks: List[Callable] = []
        self._on_health_change_callbacks: List[Callable] = []
        
        # 健康检查阈值
        self._error_rate_threshold = 0.1  # 10%错误率视为不健康
        self._min_success_rate = 0.9  # 90%成功率视为健康
    
    # =====================================================
    # 适配器管理
    # =====================================================
    
    def register_adapter(self, adapter: BaseAdapter):
        """
        注册适配器
        
        Args:
            adapter: 适配器实例
        """
        self._adapters[adapter.name] = adapter
        
        # 注册状态变更回调
        adapter.on_status_change(
            lambda old, new: self._handle_status_change(adapter.name, old, new)
        )
        
        # 初始化健康信息
        self._update_health_info(adapter)
        
        logger.info(f"已注册适配器: {adapter.name}")
    
    def unregister_adapter(self, name: str):
        """
        注销适配器
        
        Args:
            name: 适配器名称
        """
        if name in self._adapters:
            del self._adapters[name]
            self._health_info.pop(name, None)
            logger.info(f"已注销适配器: {name}")
    
    def get_adapter(self, name: str) -> Optional[BaseAdapter]:
        """获取适配器"""
        return self._adapters.get(name)
    
    def get_all_adapters(self) -> Dict[str, BaseAdapter]:
        """获取所有适配器"""
        return self._adapters.copy()
    
    # =====================================================
    # 监控控制
    # =====================================================
    
    async def start(self):
        """启动监控"""
        if self._running:
            return
        
        self._running = True
        self._monitor_task = asyncio.create_task(self._monitor_loop())
        logger.info("采集监控已启动")
    
    async def stop(self):
        """停止监控"""
        self._running = False
        
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
        
        logger.info("采集监控已停止")
    
    async def _monitor_loop(self):
        """监控循环"""
        while self._running:
            try:
                # 更新所有适配器的健康信息
                for adapter in self._adapters.values():
                    self._update_health_info(adapter)
                
                # 更新指标
                self._update_metrics()
                
                await asyncio.sleep(self._check_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"监控循环错误: {e}")
                await asyncio.sleep(self._check_interval)
    
    # =====================================================
    # 健康检查
    # =====================================================
    
    def _update_health_info(self, adapter: BaseAdapter):
        """更新适配器健康信息"""
        stats = adapter.statistics
        issues = []
        
        # 确定健康状态
        health = self._determine_health(adapter, stats, issues)
        
        self._health_info[adapter.name] = AdapterHealthInfo(
            name=adapter.name,
            protocol=adapter.protocol,
            status=adapter.status,
            health=health,
            statistics=stats.to_dict(),
            last_check_time=datetime.now(),
            issues=issues,
        )
    
    def _determine_health(
        self,
        adapter: BaseAdapter,
        stats: AdapterStatistics,
        issues: List[str]
    ) -> HealthStatus:
        """确定健康状态"""
        # 检查运行状态
        if adapter.status == AdapterStatus.ERROR:
            issues.append("适配器处于错误状态")
            return HealthStatus.UNHEALTHY
        
        if adapter.status == AdapterStatus.STOPPED:
            return HealthStatus.UNKNOWN
        
        if adapter.status == AdapterStatus.RECONNECTING:
            issues.append("适配器正在重连")
            return HealthStatus.DEGRADED
        
        # 检查成功率
        if stats.success_rate < self._min_success_rate:
            issues.append(f"成功率过低: {stats.success_rate:.2%}")
            if stats.success_rate < 0.5:
                return HealthStatus.UNHEALTHY
            return HealthStatus.DEGRADED
        
        # 检查最近错误
        if stats.last_error_time:
            time_since_error = datetime.now() - stats.last_error_time
            if time_since_error < timedelta(minutes=5):
                issues.append(f"最近有错误: {stats.last_error_message}")
                return HealthStatus.DEGRADED
        
        # 检查数据接收
        if adapter.is_running and stats.success_count == 0:
            if stats.uptime_seconds > 60:
                issues.append("运行超过1分钟但未收到数据")
                return HealthStatus.DEGRADED
        
        return HealthStatus.HEALTHY
    
    def _handle_status_change(
        self,
        adapter_name: str,
        old_status: AdapterStatus,
        new_status: AdapterStatus
    ):
        """处理状态变更"""
        logger.info(f"适配器 {adapter_name} 状态变更: {old_status.value} -> {new_status.value}")
        
        # 更新健康信息
        adapter = self._adapters.get(adapter_name)
        if adapter:
            old_health = self._health_info.get(adapter_name)
            self._update_health_info(adapter)
            new_health = self._health_info.get(adapter_name)
            
            # 通知状态变更
            for callback in self._on_status_change_callbacks:
                try:
                    callback(adapter_name, old_status, new_status)
                except Exception as e:
                    logger.error(f"状态变更回调执行失败: {e}")
            
            # 通知健康变更
            if old_health and new_health and old_health.health != new_health.health:
                for callback in self._on_health_change_callbacks:
                    try:
                        callback(adapter_name, old_health.health, new_health.health)
                    except Exception as e:
                        logger.error(f"健康变更回调执行失败: {e}")
    
    # =====================================================
    # 指标收集
    # =====================================================
    
    def _update_metrics(self):
        """更新指标"""
        now = datetime.now()
        elapsed = (now - self._last_metrics_time).total_seconds()
        
        if elapsed <= 0:
            return
        
        # 汇总所有适配器的统计
        total_success = 0
        total_errors = 0
        total_bytes = 0
        
        for adapter in self._adapters.values():
            stats = adapter.statistics
            total_success += stats.success_count
            total_errors += stats.error_count
            total_bytes += stats.total_bytes_received
        
        # 计算速率
        data_points_delta = total_success - self._last_data_points
        bytes_delta = total_bytes - self._last_bytes
        
        self._metrics.total_data_points = total_success
        self._metrics.data_points_per_second = data_points_delta / elapsed
        self._metrics.total_bytes = total_bytes
        self._metrics.bytes_per_second = bytes_delta / elapsed
        
        # 计算错误率
        total = total_success + total_errors
        self._metrics.error_rate = total_errors / total if total > 0 else 0
        
        # 更新上次值
        self._last_metrics_time = now
        self._last_data_points = total_success
        self._last_bytes = total_bytes
    
    # =====================================================
    # 状态查询
    # =====================================================
    
    def get_overall_status(self) -> Dict[str, Any]:
        """
        获取整体状态
        
        Returns:
            Dict: 整体状态信息
        """
        total = len(self._adapters)
        running = sum(1 for a in self._adapters.values() if a.is_running)
        healthy = sum(1 for h in self._health_info.values() if h.health == HealthStatus.HEALTHY)
        degraded = sum(1 for h in self._health_info.values() if h.health == HealthStatus.DEGRADED)
        unhealthy = sum(1 for h in self._health_info.values() if h.health == HealthStatus.UNHEALTHY)
        
        # 确定整体健康状态
        if unhealthy > 0:
            overall_health = HealthStatus.UNHEALTHY
        elif degraded > 0:
            overall_health = HealthStatus.DEGRADED
        elif healthy == total and total > 0:
            overall_health = HealthStatus.HEALTHY
        else:
            overall_health = HealthStatus.UNKNOWN
        
        return {
            "total_adapters": total,
            "running_adapters": running,
            "stopped_adapters": total - running,
            "overall_health": overall_health.value,
            "health_summary": {
                "healthy": healthy,
                "degraded": degraded,
                "unhealthy": unhealthy,
                "unknown": total - healthy - degraded - unhealthy,
            },
            "metrics": self._metrics.to_dict(),
            "timestamp": datetime.now().isoformat(),
        }
    
    def get_health_report(self) -> Dict[str, Any]:
        """
        获取健康报告
        
        Returns:
            Dict: 健康报告
        """
        adapters_health = {
            name: info.to_dict()
            for name, info in self._health_info.items()
        }
        
        # 收集所有问题
        all_issues = []
        for name, info in self._health_info.items():
            for issue in info.issues:
                all_issues.append({
                    "adapter": name,
                    "issue": issue,
                    "health": info.health.value,
                })
        
        return {
            "overall_status": self.get_overall_status(),
            "adapters": adapters_health,
            "issues": all_issues,
            "error_statistics": self._error_logger.get_statistics(),
            "timestamp": datetime.now().isoformat(),
        }
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        获取性能指标
        
        Returns:
            Dict: 性能指标
        """
        # 更新指标
        self._update_metrics()
        
        # 每个适配器的指标
        adapter_metrics = {}
        for name, adapter in self._adapters.items():
            stats = adapter.statistics
            adapter_metrics[name] = {
                "success_count": stats.success_count,
                "error_count": stats.error_count,
                "success_rate": stats.success_rate,
                "total_bytes": stats.total_bytes_received,
                "uptime_seconds": stats.uptime_seconds,
            }
        
        return {
            "overall": self._metrics.to_dict(),
            "adapters": adapter_metrics,
            "timestamp": datetime.now().isoformat(),
        }
    
    def get_adapter_status(self, name: str) -> Optional[Dict[str, Any]]:
        """
        获取指定适配器的状态
        
        Args:
            name: 适配器名称
        
        Returns:
            Dict: 适配器状态信息
        """
        adapter = self._adapters.get(name)
        if not adapter:
            return None
        
        health_info = self._health_info.get(name)
        
        return {
            "name": name,
            "protocol": adapter.protocol,
            "status": adapter.status.value,
            "is_running": adapter.is_running,
            "health": health_info.to_dict() if health_info else None,
            "config": adapter.config,
            "statistics": adapter.statistics.to_dict(),
        }
    
    # =====================================================
    # 回调注册
    # =====================================================
    
    def on_status_change(self, callback: Callable):
        """注册状态变更回调"""
        self._on_status_change_callbacks.append(callback)
    
    def on_health_change(self, callback: Callable):
        """注册健康变更回调"""
        self._on_health_change_callbacks.append(callback)


# 全局监控实例
_default_monitor: Optional[IngestionMonitor] = None


def get_ingestion_monitor() -> IngestionMonitor:
    """获取默认监控实例"""
    global _default_monitor
    if _default_monitor is None:
        _default_monitor = IngestionMonitor()
    return _default_monitor


def set_ingestion_monitor(monitor: IngestionMonitor):
    """设置默认监控实例"""
    global _default_monitor
    _default_monitor = monitor
