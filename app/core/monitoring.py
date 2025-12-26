# -*- coding: utf-8 -*-
"""
性能监控模块
提供性能监控装饰器、指标收集和监控工具
"""

import time
import functools
import asyncio
import psutil
import threading
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Callable, List, Union
from dataclasses import dataclass, field
from collections import defaultdict, deque
import json

from app.log import get_logger

logger = get_logger(__name__)


@dataclass
class PerformanceMetric:
    """性能指标"""
    name: str
    duration_ms: float
    timestamp: datetime
    function_name: str
    module_name: str
    args_count: int
    kwargs_count: int
    success: bool
    error_message: Optional[str] = None
    memory_usage_mb: Optional[float] = None
    cpu_percent: Optional[float] = None
    extra_data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SystemMetrics:
    """系统指标"""
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    memory_used_mb: float
    memory_available_mb: float
    disk_usage_percent: float
    disk_used_gb: float
    disk_free_gb: float
    network_bytes_sent: int
    network_bytes_recv: int
    active_connections: int


class PerformanceMonitor:
    """性能监控器"""
    
    def __init__(self, max_metrics: int = 10000):
        self.max_metrics = max_metrics
        self.metrics: deque = deque(maxlen=max_metrics)
        self.function_stats: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
            'count': 0,
            'total_duration': 0.0,
            'avg_duration': 0.0,
            'min_duration': float('inf'),
            'max_duration': 0.0,
            'error_count': 0,
            'last_called': None
        })
        self.system_metrics: deque = deque(maxlen=1000)  # 保留最近1000个系统指标
        self._lock = threading.Lock()
        self._monitoring_active = False
        self._monitor_thread = None
    
    def add_metric(self, metric: PerformanceMetric):
        """添加性能指标"""
        with self._lock:
            self.metrics.append(metric)
            
            # 更新函数统计
            func_key = f"{metric.module_name}.{metric.function_name}"
            stats = self.function_stats[func_key]
            
            stats['count'] += 1
            stats['total_duration'] += metric.duration_ms
            stats['avg_duration'] = stats['total_duration'] / stats['count']
            stats['min_duration'] = min(stats['min_duration'], metric.duration_ms)
            stats['max_duration'] = max(stats['max_duration'], metric.duration_ms)
            stats['last_called'] = metric.timestamp
            
            if not metric.success:
                stats['error_count'] += 1
            
            # 记录性能日志
            logger.performance(
                f"Function {func_key} executed",
                duration_ms=metric.duration_ms,
                function=metric.function_name,
                module=metric.module_name,
                success=metric.success,
                error=metric.error_message,
                memory_mb=metric.memory_usage_mb,
                cpu_percent=metric.cpu_percent,
                **metric.extra_data
            )
    
    def get_function_stats(self, function_name: Optional[str] = None) -> Dict[str, Any]:
        """获取函数统计信息"""
        with self._lock:
            if function_name:
                return dict(self.function_stats.get(function_name, {}))
            else:
                return {k: dict(v) for k, v in self.function_stats.items()}
    
    def get_recent_metrics(self, limit: int = 100) -> List[PerformanceMetric]:
        """获取最近的性能指标"""
        with self._lock:
            return list(self.metrics)[-limit:]
    
    def get_slow_functions(self, threshold_ms: float = 1000.0, limit: int = 10) -> List[Dict[str, Any]]:
        """获取慢函数列表"""
        with self._lock:
            slow_functions = []
            for func_name, stats in self.function_stats.items():
                if stats['avg_duration'] > threshold_ms:
                    slow_functions.append({
                        'function': func_name,
                        'avg_duration_ms': stats['avg_duration'],
                        'max_duration_ms': stats['max_duration'],
                        'call_count': stats['count'],
                        'error_rate': stats['error_count'] / stats['count'] if stats['count'] > 0 else 0
                    })
            
            # 按平均执行时间排序
            slow_functions.sort(key=lambda x: x['avg_duration_ms'], reverse=True)
            return slow_functions[:limit]
    
    def get_error_functions(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取错误率高的函数"""
        with self._lock:
            error_functions = []
            for func_name, stats in self.function_stats.items():
                if stats['error_count'] > 0:
                    error_rate = stats['error_count'] / stats['count']
                    error_functions.append({
                        'function': func_name,
                        'error_count': stats['error_count'],
                        'total_calls': stats['count'],
                        'error_rate': error_rate,
                        'avg_duration_ms': stats['avg_duration']
                    })
            
            # 按错误率排序
            error_functions.sort(key=lambda x: x['error_rate'], reverse=True)
            return error_functions[:limit]
    
    def collect_system_metrics(self) -> SystemMetrics:
        """收集系统指标"""
        try:
            # CPU使用率
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # 内存信息
            memory = psutil.virtual_memory()
            
            # 磁盘信息
            disk = psutil.disk_usage('/')
            
            # 网络信息
            network = psutil.net_io_counters()
            
            # 网络连接数
            connections = len(psutil.net_connections())
            
            metrics = SystemMetrics(
                timestamp=datetime.now(),
                cpu_percent=cpu_percent,
                memory_percent=memory.percent,
                memory_used_mb=memory.used / 1024 / 1024,
                memory_available_mb=memory.available / 1024 / 1024,
                disk_usage_percent=disk.percent,
                disk_used_gb=disk.used / 1024 / 1024 / 1024,
                disk_free_gb=disk.free / 1024 / 1024 / 1024,
                network_bytes_sent=network.bytes_sent,
                network_bytes_recv=network.bytes_recv,
                active_connections=connections
            )
            
            with self._lock:
                self.system_metrics.append(metrics)
            
            return metrics
            
        except Exception as e:
            logger.error(f"Failed to collect system metrics: {e}")
            return None
    
    def start_system_monitoring(self, interval: int = 60):
        """启动系统监控"""
        if self._monitoring_active:
            return
        
        self._monitoring_active = True
        
        def monitor_loop():
            while self._monitoring_active:
                try:
                    metrics = self.collect_system_metrics()
                    if metrics:
                        logger.info(
                            "System metrics collected",
                            extra={
                                "system_metrics": True,
                                "cpu_percent": metrics.cpu_percent,
                                "memory_percent": metrics.memory_percent,
                                "disk_percent": metrics.disk_usage_percent,
                                "connections": metrics.active_connections
                            }
                        )
                    time.sleep(interval)
                except Exception as e:
                    logger.error(f"System monitoring error: {e}")
                    time.sleep(interval)
        
        self._monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
        self._monitor_thread.start()
        logger.info("System monitoring started")
    
    def stop_system_monitoring(self):
        """停止系统监控"""
        self._monitoring_active = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=5)
        logger.info("System monitoring stopped")
    
    def get_system_metrics_summary(self, minutes: int = 60) -> Dict[str, Any]:
        """获取系统指标摘要"""
        cutoff_time = datetime.now() - timedelta(minutes=minutes)
        
        with self._lock:
            recent_metrics = [m for m in self.system_metrics if m.timestamp > cutoff_time]
        
        if not recent_metrics:
            return {}
        
        cpu_values = [m.cpu_percent for m in recent_metrics]
        memory_values = [m.memory_percent for m in recent_metrics]
        disk_values = [m.disk_usage_percent for m in recent_metrics]
        
        return {
            "time_range_minutes": minutes,
            "sample_count": len(recent_metrics),
            "cpu": {
                "avg": sum(cpu_values) / len(cpu_values),
                "min": min(cpu_values),
                "max": max(cpu_values)
            },
            "memory": {
                "avg": sum(memory_values) / len(memory_values),
                "min": min(memory_values),
                "max": max(memory_values)
            },
            "disk": {
                "avg": sum(disk_values) / len(disk_values),
                "min": min(disk_values),
                "max": max(disk_values)
            },
            "latest_metrics": recent_metrics[-1] if recent_metrics else None
        }
    
    def export_metrics(self, filepath: str):
        """导出指标到文件"""
        with self._lock:
            data = {
                "export_time": datetime.now().isoformat(),
                "performance_metrics": [
                    {
                        "name": m.name,
                        "duration_ms": m.duration_ms,
                        "timestamp": m.timestamp.isoformat(),
                        "function_name": m.function_name,
                        "module_name": m.module_name,
                        "success": m.success,
                        "error_message": m.error_message,
                        "memory_usage_mb": m.memory_usage_mb,
                        "cpu_percent": m.cpu_percent,
                        "extra_data": m.extra_data
                    }
                    for m in self.metrics
                ],
                "function_stats": dict(self.function_stats),
                "system_metrics": [
                    {
                        "timestamp": m.timestamp.isoformat(),
                        "cpu_percent": m.cpu_percent,
                        "memory_percent": m.memory_percent,
                        "memory_used_mb": m.memory_used_mb,
                        "disk_usage_percent": m.disk_usage_percent,
                        "active_connections": m.active_connections
                    }
                    for m in self.system_metrics
                ]
            }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Metrics exported to {filepath}")


# 全局性能监控器实例
performance_monitor = PerformanceMonitor()


def monitor_performance(
    name: Optional[str] = None,
    include_args: bool = False,
    include_memory: bool = False,
    include_cpu: bool = False,
    threshold_ms: Optional[float] = None,
    **extra_data
):
    """
    性能监控装饰器
    
    Args:
        name: 指标名称，默认使用函数名
        include_args: 是否包含参数信息
        include_memory: 是否包含内存使用信息
        include_cpu: 是否包含CPU使用信息
        threshold_ms: 性能阈值，超过时记录警告
        **extra_data: 额外数据
    """
    def decorator(func: Callable) -> Callable:
        metric_name = name or f"{func.__module__}.{func.__name__}"
        
        if asyncio.iscoroutinefunction(func):
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                start_time = time.time()
                start_memory = psutil.Process().memory_info().rss / 1024 / 1024 if include_memory else None
                start_cpu = psutil.cpu_percent() if include_cpu else None
                
                success = True
                error_message = None
                
                try:
                    result = await func(*args, **kwargs)
                    return result
                except Exception as e:
                    success = False
                    error_message = str(e)
                    raise
                finally:
                    end_time = time.time()
                    duration_ms = (end_time - start_time) * 1000
                    
                    # 计算资源使用
                    memory_usage = None
                    cpu_usage = None
                    
                    if include_memory and start_memory:
                        end_memory = psutil.Process().memory_info().rss / 1024 / 1024
                        memory_usage = end_memory - start_memory
                    
                    if include_cpu and start_cpu is not None:
                        cpu_usage = psutil.cpu_percent() - start_cpu
                    
                    # 创建性能指标
                    metric = PerformanceMetric(
                        name=metric_name,
                        duration_ms=duration_ms,
                        timestamp=datetime.now(),
                        function_name=func.__name__,
                        module_name=func.__module__,
                        args_count=len(args) if include_args else 0,
                        kwargs_count=len(kwargs) if include_args else 0,
                        success=success,
                        error_message=error_message,
                        memory_usage_mb=memory_usage,
                        cpu_percent=cpu_usage,
                        extra_data=extra_data
                    )
                    
                    performance_monitor.add_metric(metric)
                    
                    # 检查性能阈值
                    if threshold_ms and duration_ms > threshold_ms:
                        logger.warning(
                            f"Function {metric_name} exceeded threshold",
                            duration_ms=duration_ms,
                            threshold_ms=threshold_ms,
                            function=func.__name__
                        )
            
            return async_wrapper
        else:
            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs):
                start_time = time.time()
                start_memory = psutil.Process().memory_info().rss / 1024 / 1024 if include_memory else None
                start_cpu = psutil.cpu_percent() if include_cpu else None
                
                success = True
                error_message = None
                
                try:
                    result = func(*args, **kwargs)
                    return result
                except Exception as e:
                    success = False
                    error_message = str(e)
                    raise
                finally:
                    end_time = time.time()
                    duration_ms = (end_time - start_time) * 1000
                    
                    # 计算资源使用
                    memory_usage = None
                    cpu_usage = None
                    
                    if include_memory and start_memory:
                        end_memory = psutil.Process().memory_info().rss / 1024 / 1024
                        memory_usage = end_memory - start_memory
                    
                    if include_cpu and start_cpu is not None:
                        cpu_usage = psutil.cpu_percent() - start_cpu
                    
                    # 创建性能指标
                    metric = PerformanceMetric(
                        name=metric_name,
                        duration_ms=duration_ms,
                        timestamp=datetime.now(),
                        function_name=func.__name__,
                        module_name=func.__module__,
                        args_count=len(args) if include_args else 0,
                        kwargs_count=len(kwargs) if include_args else 0,
                        success=success,
                        error_message=error_message,
                        memory_usage_mb=memory_usage,
                        cpu_percent=cpu_usage,
                        extra_data=extra_data
                    )
                    
                    performance_monitor.add_metric(metric)
                    
                    # 检查性能阈值
                    if threshold_ms and duration_ms > threshold_ms:
                        logger.warning(
                            f"Function {metric_name} exceeded threshold",
                            duration_ms=duration_ms,
                            threshold_ms=threshold_ms,
                            function=func.__name__
                        )
            
            return sync_wrapper
    
    return decorator


def monitor_database_query(query_type: str = "unknown"):
    """数据库查询监控装饰器"""
    return monitor_performance(
        name=f"db_query_{query_type}",
        include_memory=True,
        threshold_ms=1000.0,
        query_type=query_type
    )


def monitor_api_endpoint(endpoint: str):
    """API端点监控装饰器"""
    return monitor_performance(
        name=f"api_{endpoint}",
        include_memory=True,
        threshold_ms=5000.0,
        endpoint=endpoint
    )


def monitor_background_task(task_name: str):
    """后台任务监控装饰器"""
    return monitor_performance(
        name=f"task_{task_name}",
        include_memory=True,
        include_cpu=True,
        task_name=task_name
    )


# 启动系统监控
def start_monitoring():
    """启动监控系统"""
    performance_monitor.start_system_monitoring()
    logger.info("Performance monitoring system started")


def stop_monitoring():
    """停止监控系统"""
    performance_monitor.stop_system_monitoring()
    logger.info("Performance monitoring system stopped")