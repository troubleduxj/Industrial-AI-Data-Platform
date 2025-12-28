#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工业AI数据平台性能监控和优化服务
提供API响应时间监控、数据库查询优化和缓存策略

需求映射：
- 需求9.1: API响应时间亚秒级保证
- 需求9.2: 水平扩展支持
- 需求9.3: 并发会话支持
- 需求9.4: 历史数据查询性能
"""

import time
import asyncio
import functools
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Callable, Union
from dataclasses import dataclass, field
from collections import defaultdict, deque
from enum import Enum
import threading
import json

from app.core.unified_logger import get_logger
from app.core.redis_cache import redis_cache_manager

logger = get_logger(__name__)


class MetricType(Enum):
    """指标类型"""
    API_RESPONSE_TIME = "api_response_time"
    DB_QUERY_TIME = "db_query_time"
    CACHE_HIT_RATE = "cache_hit_rate"
    CONCURRENT_REQUESTS = "concurrent_requests"
    ERROR_RATE = "error_rate"
    THROUGHPUT = "throughput"


@dataclass
class APIMetric:
    """API性能指标"""
    endpoint: str
    method: str
    duration_ms: float
    status_code: int
    timestamp: datetime
    user_id: Optional[int] = None
    request_size: int = 0
    response_size: int = 0
    cache_hit: bool = False
    error_message: Optional[str] = None


@dataclass
class QueryMetric:
    """数据库查询指标"""
    query_type: str
    table_name: str
    duration_ms: float
    rows_affected: int
    timestamp: datetime
    is_slow: bool = False
    query_hash: Optional[str] = None


@dataclass
class CacheMetric:
    """缓存指标"""
    cache_key: str
    operation: str  # get, set, delete
    hit: bool
    duration_ms: float
    timestamp: datetime
    ttl: Optional[int] = None


class PerformanceThresholds:
    """性能阈值配置"""
    API_RESPONSE_WARNING_MS = 500  # API响应警告阈值
    API_RESPONSE_CRITICAL_MS = 1000  # API响应严重阈值
    DB_QUERY_WARNING_MS = 100  # 数据库查询警告阈值
    DB_QUERY_CRITICAL_MS = 500  # 数据库查询严重阈值
    CACHE_HIT_RATE_WARNING = 0.7  # 缓存命中率警告阈值
    ERROR_RATE_WARNING = 0.01  # 错误率警告阈值
    ERROR_RATE_CRITICAL = 0.05  # 错误率严重阈值


class PlatformPerformanceService:
    """平台性能监控服务"""
    
    def __init__(self, max_metrics: int = 10000):
        self.max_metrics = max_metrics
        
        # 指标存储
        self.api_metrics: deque = deque(maxlen=max_metrics)
        self.query_metrics: deque = deque(maxlen=max_metrics)
        self.cache_metrics: deque = deque(maxlen=max_metrics)
        
        # 统计数据
        self.endpoint_stats: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
            'count': 0,
            'total_duration': 0.0,
            'avg_duration': 0.0,
            'min_duration': float('inf'),
            'max_duration': 0.0,
            'error_count': 0,
            'cache_hits': 0,
            'last_called': None
        })
        
        self.query_stats: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
            'count': 0,
            'total_duration': 0.0,
            'avg_duration': 0.0,
            'slow_count': 0,
            'total_rows': 0
        })
        
        self.cache_stats = {
            'total_operations': 0,
            'hits': 0,
            'misses': 0,
            'hit_rate': 0.0
        }
        
        # 并发请求计数
        self._concurrent_requests = 0
        self._max_concurrent_requests = 0
        self._lock = threading.Lock()
        
        # 缓存配置
        self.cache_config = {
            'asset_category': {'ttl': 300, 'prefix': 'platform:category:'},
            'asset': {'ttl': 60, 'prefix': 'platform:asset:'},
            'signal_definition': {'ttl': 300, 'prefix': 'platform:signal:'},
            'ai_model': {'ttl': 120, 'prefix': 'platform:model:'},
            'feature_view': {'ttl': 180, 'prefix': 'platform:feature:'},
            'prediction': {'ttl': 30, 'prefix': 'platform:prediction:'},
        }
    
    def record_api_metric(self, metric: APIMetric):
        """记录API性能指标"""
        with self._lock:
            self.api_metrics.append(metric)
            
            # 更新端点统计
            endpoint_key = f"{metric.method} {metric.endpoint}"
            stats = self.endpoint_stats[endpoint_key]
            
            stats['count'] += 1
            stats['total_duration'] += metric.duration_ms
            stats['avg_duration'] = stats['total_duration'] / stats['count']
            stats['min_duration'] = min(stats['min_duration'], metric.duration_ms)
            stats['max_duration'] = max(stats['max_duration'], metric.duration_ms)
            stats['last_called'] = metric.timestamp
            
            if metric.status_code >= 400:
                stats['error_count'] += 1
            
            if metric.cache_hit:
                stats['cache_hits'] += 1
            
            # 检查性能阈值
            if metric.duration_ms > PerformanceThresholds.API_RESPONSE_CRITICAL_MS:
                logger.warning(
                    f"API响应时间超过严重阈值: {endpoint_key}, "
                    f"duration={metric.duration_ms}ms"
                )
            elif metric.duration_ms > PerformanceThresholds.API_RESPONSE_WARNING_MS:
                logger.info(
                    f"API响应时间超过警告阈值: {endpoint_key}, "
                    f"duration={metric.duration_ms}ms"
                )
    
    def record_query_metric(self, metric: QueryMetric):
        """记录数据库查询指标"""
        with self._lock:
            self.query_metrics.append(metric)
            
            # 更新查询统计
            query_key = f"{metric.query_type}:{metric.table_name}"
            stats = self.query_stats[query_key]
            
            stats['count'] += 1
            stats['total_duration'] += metric.duration_ms
            stats['avg_duration'] = stats['total_duration'] / stats['count']
            stats['total_rows'] += metric.rows_affected
            
            if metric.is_slow:
                stats['slow_count'] += 1
                logger.warning(
                    f"慢查询检测: {query_key}, duration={metric.duration_ms}ms"
                )
    
    def record_cache_metric(self, metric: CacheMetric):
        """记录缓存指标"""
        with self._lock:
            self.cache_metrics.append(metric)
            
            # 更新缓存统计
            self.cache_stats['total_operations'] += 1
            
            if metric.operation == 'get':
                if metric.hit:
                    self.cache_stats['hits'] += 1
                else:
                    self.cache_stats['misses'] += 1
                
                total_gets = self.cache_stats['hits'] + self.cache_stats['misses']
                if total_gets > 0:
                    self.cache_stats['hit_rate'] = self.cache_stats['hits'] / total_gets
    
    def increment_concurrent_requests(self):
        """增加并发请求计数"""
        with self._lock:
            self._concurrent_requests += 1
            self._max_concurrent_requests = max(
                self._max_concurrent_requests,
                self._concurrent_requests
            )
    
    def decrement_concurrent_requests(self):
        """减少并发请求计数"""
        with self._lock:
            self._concurrent_requests = max(0, self._concurrent_requests - 1)
    
    def get_concurrent_requests(self) -> int:
        """获取当前并发请求数"""
        return self._concurrent_requests
    
    def get_performance_summary(self, minutes: int = 60) -> Dict[str, Any]:
        """
        获取性能摘要
        
        Args:
            minutes: 统计时间范围（分钟）
            
        Returns:
            Dict: 性能摘要
        """
        cutoff_time = datetime.now() - timedelta(minutes=minutes)
        
        with self._lock:
            # 过滤最近的API指标
            recent_api_metrics = [
                m for m in self.api_metrics
                if m.timestamp > cutoff_time
            ]
            
            # 过滤最近的查询指标
            recent_query_metrics = [
                m for m in self.query_metrics
                if m.timestamp > cutoff_time
            ]
            
            # 计算API统计
            api_durations = [m.duration_ms for m in recent_api_metrics]
            api_errors = [m for m in recent_api_metrics if m.status_code >= 400]
            
            api_summary = {
                'total_requests': len(recent_api_metrics),
                'avg_response_time_ms': sum(api_durations) / len(api_durations) if api_durations else 0,
                'min_response_time_ms': min(api_durations) if api_durations else 0,
                'max_response_time_ms': max(api_durations) if api_durations else 0,
                'error_count': len(api_errors),
                'error_rate': len(api_errors) / len(recent_api_metrics) if recent_api_metrics else 0,
                'requests_under_1s': len([d for d in api_durations if d < 1000]),
                'requests_under_1s_rate': len([d for d in api_durations if d < 1000]) / len(api_durations) if api_durations else 1.0
            }
            
            # 计算查询统计
            query_durations = [m.duration_ms for m in recent_query_metrics]
            slow_queries = [m for m in recent_query_metrics if m.is_slow]
            
            query_summary = {
                'total_queries': len(recent_query_metrics),
                'avg_query_time_ms': sum(query_durations) / len(query_durations) if query_durations else 0,
                'slow_query_count': len(slow_queries),
                'slow_query_rate': len(slow_queries) / len(recent_query_metrics) if recent_query_metrics else 0
            }
            
            return {
                'time_range_minutes': minutes,
                'timestamp': datetime.now().isoformat(),
                'api': api_summary,
                'database': query_summary,
                'cache': dict(self.cache_stats),
                'concurrent_requests': {
                    'current': self._concurrent_requests,
                    'max': self._max_concurrent_requests
                }
            }
    
    def get_slow_endpoints(self, threshold_ms: float = 500, limit: int = 10) -> List[Dict[str, Any]]:
        """获取慢端点列表"""
        with self._lock:
            slow_endpoints = []
            
            for endpoint, stats in self.endpoint_stats.items():
                if stats['avg_duration'] > threshold_ms:
                    slow_endpoints.append({
                        'endpoint': endpoint,
                        'avg_duration_ms': stats['avg_duration'],
                        'max_duration_ms': stats['max_duration'],
                        'call_count': stats['count'],
                        'error_rate': stats['error_count'] / stats['count'] if stats['count'] > 0 else 0
                    })
            
            slow_endpoints.sort(key=lambda x: x['avg_duration_ms'], reverse=True)
            return slow_endpoints[:limit]
    
    def get_endpoint_stats(self, endpoint: Optional[str] = None) -> Dict[str, Any]:
        """获取端点统计"""
        with self._lock:
            if endpoint:
                return dict(self.endpoint_stats.get(endpoint, {}))
            return {k: dict(v) for k, v in self.endpoint_stats.items()}
    
    async def get_cached_data(
        self,
        resource_type: str,
        resource_id: str,
        fetch_func: Callable,
        *args,
        **kwargs
    ) -> Any:
        """
        获取缓存数据
        
        Args:
            resource_type: 资源类型
            resource_id: 资源ID
            fetch_func: 数据获取函数
            
        Returns:
            缓存或新获取的数据
        """
        config = self.cache_config.get(resource_type, {'ttl': 60, 'prefix': 'platform:'})
        cache_key = f"{config['prefix']}{resource_id}"
        
        start_time = time.time()
        
        try:
            # 尝试从缓存获取
            redis = await self._get_redis()
            if redis:
                cached = await redis.get(cache_key)
                if cached:
                    duration_ms = (time.time() - start_time) * 1000
                    self.record_cache_metric(CacheMetric(
                        cache_key=cache_key,
                        operation='get',
                        hit=True,
                        duration_ms=duration_ms,
                        timestamp=datetime.now()
                    ))
                    return json.loads(cached)
            
            # 缓存未命中，获取数据
            duration_ms = (time.time() - start_time) * 1000
            self.record_cache_metric(CacheMetric(
                cache_key=cache_key,
                operation='get',
                hit=False,
                duration_ms=duration_ms,
                timestamp=datetime.now()
            ))
            
            # 调用获取函数
            if asyncio.iscoroutinefunction(fetch_func):
                data = await fetch_func(*args, **kwargs)
            else:
                data = fetch_func(*args, **kwargs)
            
            # 存入缓存
            if redis and data is not None:
                await redis.setex(
                    cache_key,
                    config['ttl'],
                    json.dumps(data, default=str)
                )
            
            return data
            
        except Exception as e:
            logger.error(f"缓存操作失败: {e}")
            # 降级到直接获取
            if asyncio.iscoroutinefunction(fetch_func):
                return await fetch_func(*args, **kwargs)
            return fetch_func(*args, **kwargs)
    
    async def invalidate_cache(self, resource_type: str, resource_id: str):
        """使缓存失效"""
        config = self.cache_config.get(resource_type, {'prefix': 'platform:'})
        cache_key = f"{config['prefix']}{resource_id}"
        
        try:
            redis = await self._get_redis()
            if redis:
                await redis.delete(cache_key)
                logger.debug(f"缓存已失效: {cache_key}")
        except Exception as e:
            logger.error(f"缓存失效操作失败: {e}")
    
    async def invalidate_cache_pattern(self, resource_type: str):
        """使匹配模式的缓存失效"""
        config = self.cache_config.get(resource_type, {'prefix': 'platform:'})
        pattern = f"{config['prefix']}*"
        
        try:
            redis = await self._get_redis()
            if redis:
                keys = await redis.keys(pattern)
                if keys:
                    await redis.delete(*keys)
                    logger.debug(f"批量缓存已失效: {pattern}, count={len(keys)}")
        except Exception as e:
            logger.error(f"批量缓存失效操作失败: {e}")
    
    async def _get_redis(self):
        """获取Redis连接"""
        try:
            await redis_cache_manager.redis_manager.ensure_connection()
            return redis_cache_manager.redis_manager.redis
        except Exception as e:
            logger.warning(f"Redis连接失败: {e}")
            return None
    
    def check_health(self) -> Dict[str, Any]:
        """
        检查性能健康状态
        
        Returns:
            Dict: 健康状态报告
        """
        summary = self.get_performance_summary(minutes=5)
        
        issues = []
        status = "healthy"
        
        # 检查API响应时间
        if summary['api']['avg_response_time_ms'] > PerformanceThresholds.API_RESPONSE_CRITICAL_MS:
            issues.append({
                'type': 'api_response_time',
                'severity': 'critical',
                'message': f"API平均响应时间过高: {summary['api']['avg_response_time_ms']:.2f}ms"
            })
            status = "critical"
        elif summary['api']['avg_response_time_ms'] > PerformanceThresholds.API_RESPONSE_WARNING_MS:
            issues.append({
                'type': 'api_response_time',
                'severity': 'warning',
                'message': f"API平均响应时间偏高: {summary['api']['avg_response_time_ms']:.2f}ms"
            })
            if status == "healthy":
                status = "warning"
        
        # 检查错误率
        if summary['api']['error_rate'] > PerformanceThresholds.ERROR_RATE_CRITICAL:
            issues.append({
                'type': 'error_rate',
                'severity': 'critical',
                'message': f"API错误率过高: {summary['api']['error_rate']*100:.2f}%"
            })
            status = "critical"
        elif summary['api']['error_rate'] > PerformanceThresholds.ERROR_RATE_WARNING:
            issues.append({
                'type': 'error_rate',
                'severity': 'warning',
                'message': f"API错误率偏高: {summary['api']['error_rate']*100:.2f}%"
            })
            if status == "healthy":
                status = "warning"
        
        # 检查缓存命中率
        if summary['cache']['hit_rate'] < PerformanceThresholds.CACHE_HIT_RATE_WARNING:
            issues.append({
                'type': 'cache_hit_rate',
                'severity': 'warning',
                'message': f"缓存命中率偏低: {summary['cache']['hit_rate']*100:.2f}%"
            })
            if status == "healthy":
                status = "warning"
        
        # 检查亚秒级响应率
        if summary['api']['requests_under_1s_rate'] < 0.95:
            issues.append({
                'type': 'response_time_sla',
                'severity': 'warning',
                'message': f"亚秒级响应率未达标: {summary['api']['requests_under_1s_rate']*100:.2f}%"
            })
            if status == "healthy":
                status = "warning"
        
        return {
            'status': status,
            'timestamp': datetime.now().isoformat(),
            'issues': issues,
            'summary': summary
        }


# 全局性能服务实例
platform_performance_service = PlatformPerformanceService()


def monitor_api_performance(endpoint: str = None):
    """
    API性能监控装饰器
    
    Args:
        endpoint: 端点名称，默认使用函数名
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            # 获取请求信息
            request = None
            for arg in args:
                if hasattr(arg, 'method') and hasattr(arg, 'url'):
                    request = arg
                    break
            
            endpoint_name = endpoint or func.__name__
            method = request.method if request else "UNKNOWN"
            
            platform_performance_service.increment_concurrent_requests()
            start_time = time.time()
            status_code = 200
            error_message = None
            
            try:
                result = await func(*args, **kwargs)
                if hasattr(result, 'status_code'):
                    status_code = result.status_code
                return result
            except Exception as e:
                status_code = 500
                error_message = str(e)
                raise
            finally:
                duration_ms = (time.time() - start_time) * 1000
                platform_performance_service.decrement_concurrent_requests()
                
                metric = APIMetric(
                    endpoint=endpoint_name,
                    method=method,
                    duration_ms=duration_ms,
                    status_code=status_code,
                    timestamp=datetime.now(),
                    error_message=error_message
                )
                platform_performance_service.record_api_metric(metric)
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            endpoint_name = endpoint or func.__name__
            
            platform_performance_service.increment_concurrent_requests()
            start_time = time.time()
            status_code = 200
            error_message = None
            
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                status_code = 500
                error_message = str(e)
                raise
            finally:
                duration_ms = (time.time() - start_time) * 1000
                platform_performance_service.decrement_concurrent_requests()
                
                metric = APIMetric(
                    endpoint=endpoint_name,
                    method="SYNC",
                    duration_ms=duration_ms,
                    status_code=status_code,
                    timestamp=datetime.now(),
                    error_message=error_message
                )
                platform_performance_service.record_api_metric(metric)
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator


def monitor_db_query(query_type: str, table_name: str):
    """
    数据库查询监控装饰器
    
    Args:
        query_type: 查询类型 (SELECT, INSERT, UPDATE, DELETE)
        table_name: 表名
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            rows_affected = 0
            
            try:
                result = await func(*args, **kwargs)
                if isinstance(result, (list, tuple)):
                    rows_affected = len(result)
                elif isinstance(result, int):
                    rows_affected = result
                return result
            finally:
                duration_ms = (time.time() - start_time) * 1000
                is_slow = duration_ms > PerformanceThresholds.DB_QUERY_WARNING_MS
                
                metric = QueryMetric(
                    query_type=query_type,
                    table_name=table_name,
                    duration_ms=duration_ms,
                    rows_affected=rows_affected,
                    timestamp=datetime.now(),
                    is_slow=is_slow
                )
                platform_performance_service.record_query_metric(metric)
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            rows_affected = 0
            
            try:
                result = func(*args, **kwargs)
                if isinstance(result, (list, tuple)):
                    rows_affected = len(result)
                elif isinstance(result, int):
                    rows_affected = result
                return result
            finally:
                duration_ms = (time.time() - start_time) * 1000
                is_slow = duration_ms > PerformanceThresholds.DB_QUERY_WARNING_MS
                
                metric = QueryMetric(
                    query_type=query_type,
                    table_name=table_name,
                    duration_ms=duration_ms,
                    rows_affected=rows_affected,
                    timestamp=datetime.now(),
                    is_slow=is_slow
                )
                platform_performance_service.record_query_metric(metric)
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator
