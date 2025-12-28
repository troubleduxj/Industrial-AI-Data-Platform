#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
重试管理器

实现数据采集层的连接重试和错误记录功能。
支持指数退避、最大重试次数限制和错误日志记录。

需求: 5.4 - 数据源异常时记录错误并支持重试机制
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, Any, List, Optional, Callable, TypeVar, Awaitable
from functools import wraps
import random

logger = logging.getLogger(__name__)

T = TypeVar('T')


class RetryStrategy(str, Enum):
    """重试策略枚举"""
    FIXED = "fixed"  # 固定间隔
    LINEAR = "linear"  # 线性增长
    EXPONENTIAL = "exponential"  # 指数退避
    EXPONENTIAL_JITTER = "exponential_jitter"  # 指数退避+随机抖动


@dataclass
class RetryConfig:
    """
    重试配置
    
    Attributes:
        max_attempts: 最大重试次数
        initial_delay: 初始延迟（秒）
        max_delay: 最大延迟（秒）
        strategy: 重试策略
        multiplier: 延迟乘数（用于指数退避）
        jitter_factor: 抖动因子（0-1之间）
        retryable_exceptions: 可重试的异常类型列表
    """
    max_attempts: int = 3
    initial_delay: float = 1.0
    max_delay: float = 60.0
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL_JITTER
    multiplier: float = 2.0
    jitter_factor: float = 0.1
    retryable_exceptions: tuple = (Exception,)
    
    def calculate_delay(self, attempt: int) -> float:
        """
        计算重试延迟
        
        Args:
            attempt: 当前重试次数（从1开始）
        
        Returns:
            float: 延迟时间（秒）
        """
        if self.strategy == RetryStrategy.FIXED:
            delay = self.initial_delay
        
        elif self.strategy == RetryStrategy.LINEAR:
            delay = self.initial_delay * attempt
        
        elif self.strategy == RetryStrategy.EXPONENTIAL:
            delay = self.initial_delay * (self.multiplier ** (attempt - 1))
        
        elif self.strategy == RetryStrategy.EXPONENTIAL_JITTER:
            base_delay = self.initial_delay * (self.multiplier ** (attempt - 1))
            jitter = base_delay * self.jitter_factor * random.random()
            delay = base_delay + jitter
        
        else:
            delay = self.initial_delay
        
        return min(delay, self.max_delay)


@dataclass
class ErrorRecord:
    """
    错误记录
    
    Attributes:
        timestamp: 错误发生时间
        error_type: 错误类型
        error_message: 错误信息
        source: 错误来源
        context: 上下文信息
        attempt: 重试次数
        resolved: 是否已解决
    """
    timestamp: datetime
    error_type: str
    error_message: str
    source: str = ""
    context: Dict[str, Any] = field(default_factory=dict)
    attempt: int = 0
    resolved: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp.isoformat(),
            "error_type": self.error_type,
            "error_message": self.error_message,
            "source": self.source,
            "context": self.context,
            "attempt": self.attempt,
            "resolved": self.resolved,
        }


class ErrorLogger:
    """
    错误日志记录器
    
    记录和管理错误日志，支持查询和统计。
    """
    
    def __init__(self, max_records: int = 1000):
        """
        初始化错误日志记录器
        
        Args:
            max_records: 最大记录数量
        """
        self._records: List[ErrorRecord] = []
        self._max_records = max_records
        self._error_counts: Dict[str, int] = {}
    
    def log_error(
        self,
        error: Exception,
        source: str = "",
        context: Optional[Dict[str, Any]] = None,
        attempt: int = 0
    ) -> ErrorRecord:
        """
        记录错误
        
        Args:
            error: 异常对象
            source: 错误来源
            context: 上下文信息
            attempt: 重试次数
        
        Returns:
            ErrorRecord: 错误记录
        """
        record = ErrorRecord(
            timestamp=datetime.now(),
            error_type=type(error).__name__,
            error_message=str(error),
            source=source,
            context=context or {},
            attempt=attempt,
        )
        
        self._records.append(record)
        
        # 更新错误计数
        self._error_counts[record.error_type] = self._error_counts.get(record.error_type, 0) + 1
        
        # 限制记录数量
        if len(self._records) > self._max_records:
            self._records = self._records[-self._max_records:]
        
        # 记录到日志
        logger.error(
            f"[{source}] {record.error_type}: {record.error_message} (attempt={attempt})",
            extra={"context": context}
        )
        
        return record
    
    def get_records(
        self,
        source: Optional[str] = None,
        error_type: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100
    ) -> List[ErrorRecord]:
        """
        查询错误记录
        
        Args:
            source: 按来源过滤
            error_type: 按错误类型过滤
            start_time: 开始时间
            end_time: 结束时间
            limit: 返回数量限制
        
        Returns:
            List[ErrorRecord]: 错误记录列表
        """
        records = self._records
        
        if source:
            records = [r for r in records if r.source == source]
        
        if error_type:
            records = [r for r in records if r.error_type == error_type]
        
        if start_time:
            records = [r for r in records if r.timestamp >= start_time]
        
        if end_time:
            records = [r for r in records if r.timestamp <= end_time]
        
        return records[-limit:]
    
    def get_error_counts(self) -> Dict[str, int]:
        """获取错误类型计数"""
        return self._error_counts.copy()
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        获取错误统计信息
        
        Returns:
            Dict: 统计信息
        """
        total = len(self._records)
        resolved = sum(1 for r in self._records if r.resolved)
        
        # 按来源统计
        by_source: Dict[str, int] = {}
        for record in self._records:
            by_source[record.source] = by_source.get(record.source, 0) + 1
        
        # 最近错误
        recent_errors = self._records[-10:] if self._records else []
        
        return {
            "total_errors": total,
            "resolved_errors": resolved,
            "unresolved_errors": total - resolved,
            "error_types": self._error_counts,
            "by_source": by_source,
            "recent_errors": [r.to_dict() for r in recent_errors],
        }
    
    def clear(self):
        """清除所有记录"""
        self._records.clear()
        self._error_counts.clear()
    
    def mark_resolved(self, source: str):
        """标记来源的所有错误为已解决"""
        for record in self._records:
            if record.source == source:
                record.resolved = True


class RetryManager:
    """
    重试管理器
    
    管理重试逻辑和错误记录。
    
    使用示例:
    ```python
    retry_manager = RetryManager()
    
    # 使用装饰器
    @retry_manager.retry()
    async def connect():
        # 连接逻辑
        pass
    
    # 或直接调用
    result = await retry_manager.execute_with_retry(
        connect,
        source="mqtt_adapter"
    )
    ```
    """
    
    def __init__(
        self,
        config: Optional[RetryConfig] = None,
        error_logger: Optional[ErrorLogger] = None
    ):
        """
        初始化重试管理器
        
        Args:
            config: 重试配置
            error_logger: 错误日志记录器
        """
        self._config = config or RetryConfig()
        self._error_logger = error_logger or ErrorLogger()
        self._retry_counts: Dict[str, int] = {}
    
    @property
    def config(self) -> RetryConfig:
        """获取重试配置"""
        return self._config
    
    @property
    def error_logger(self) -> ErrorLogger:
        """获取错误日志记录器"""
        return self._error_logger
    
    async def execute_with_retry(
        self,
        func: Callable[..., Awaitable[T]],
        *args,
        source: str = "",
        config: Optional[RetryConfig] = None,
        on_retry: Optional[Callable[[int, Exception], None]] = None,
        **kwargs
    ) -> T:
        """
        执行带重试的异步函数
        
        Args:
            func: 要执行的异步函数
            *args: 函数参数
            source: 来源标识
            config: 重试配置（可选，使用默认配置）
            on_retry: 重试回调函数
            **kwargs: 函数关键字参数
        
        Returns:
            函数返回值
        
        Raises:
            Exception: 超过最大重试次数后抛出最后一个异常
        """
        retry_config = config or self._config
        last_exception = None
        
        for attempt in range(1, retry_config.max_attempts + 1):
            try:
                result = await func(*args, **kwargs)
                
                # 成功后重置重试计数
                if source:
                    self._retry_counts[source] = 0
                    self._error_logger.mark_resolved(source)
                
                return result
                
            except retry_config.retryable_exceptions as e:
                last_exception = e
                
                # 记录错误
                self._error_logger.log_error(
                    error=e,
                    source=source,
                    context={"attempt": attempt, "max_attempts": retry_config.max_attempts},
                    attempt=attempt
                )
                
                # 更新重试计数
                if source:
                    self._retry_counts[source] = attempt
                
                # 调用重试回调
                if on_retry:
                    try:
                        on_retry(attempt, e)
                    except Exception as callback_error:
                        logger.warning(f"重试回调执行失败: {callback_error}")
                
                # 如果还有重试机会，等待后重试
                if attempt < retry_config.max_attempts:
                    delay = retry_config.calculate_delay(attempt)
                    logger.info(f"[{source}] 第 {attempt} 次重试失败，{delay:.2f}秒后重试...")
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"[{source}] 达到最大重试次数 {retry_config.max_attempts}，放弃重试")
        
        # 抛出最后一个异常
        raise last_exception
    
    def retry(
        self,
        source: str = "",
        config: Optional[RetryConfig] = None,
        on_retry: Optional[Callable[[int, Exception], None]] = None
    ):
        """
        重试装饰器
        
        Args:
            source: 来源标识
            config: 重试配置
            on_retry: 重试回调函数
        
        Returns:
            装饰器函数
        """
        def decorator(func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
            @wraps(func)
            async def wrapper(*args, **kwargs) -> T:
                return await self.execute_with_retry(
                    func,
                    *args,
                    source=source or func.__name__,
                    config=config,
                    on_retry=on_retry,
                    **kwargs
                )
            return wrapper
        return decorator
    
    def get_retry_count(self, source: str) -> int:
        """获取指定来源的重试计数"""
        return self._retry_counts.get(source, 0)
    
    def reset_retry_count(self, source: str):
        """重置指定来源的重试计数"""
        self._retry_counts[source] = 0
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        获取重试统计信息
        
        Returns:
            Dict: 统计信息
        """
        return {
            "retry_counts": self._retry_counts.copy(),
            "error_statistics": self._error_logger.get_statistics(),
        }


# 全局实例
_default_retry_manager: Optional[RetryManager] = None
_default_error_logger: Optional[ErrorLogger] = None


def get_retry_manager() -> RetryManager:
    """获取默认重试管理器"""
    global _default_retry_manager
    if _default_retry_manager is None:
        _default_retry_manager = RetryManager()
    return _default_retry_manager


def get_error_logger() -> ErrorLogger:
    """获取默认错误日志记录器"""
    global _default_error_logger
    if _default_error_logger is None:
        _default_error_logger = ErrorLogger()
    return _default_error_logger


def set_retry_manager(manager: RetryManager):
    """设置默认重试管理器"""
    global _default_retry_manager
    _default_retry_manager = manager


def set_error_logger(logger: ErrorLogger):
    """设置默认错误日志记录器"""
    global _default_error_logger
    _default_error_logger = logger


# 便捷装饰器
def with_retry(
    source: str = "",
    max_attempts: int = 3,
    initial_delay: float = 1.0,
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL_JITTER
):
    """
    便捷重试装饰器
    
    Args:
        source: 来源标识
        max_attempts: 最大重试次数
        initial_delay: 初始延迟
        strategy: 重试策略
    
    Returns:
        装饰器函数
    """
    config = RetryConfig(
        max_attempts=max_attempts,
        initial_delay=initial_delay,
        strategy=strategy
    )
    
    return get_retry_manager().retry(source=source, config=config)
