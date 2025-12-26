"""重试管理器

提供统一的重试机制，支持多种重试策略和条件判断。
"""

import asyncio
import logging
import time
from enum import Enum
from typing import Any, Callable, Dict, Optional, Union, Awaitable
from datetime import datetime, timedelta
import random
import math


class RetryStrategy(Enum):
    """重试策略枚举"""
    EXPONENTIAL = "exponential"  # 指数退避
    LINEAR = "linear"           # 线性增长
    FIXED = "fixed"             # 固定间隔
    RANDOM = "random"           # 随机间隔


class RetryConfig:
    """重试配置"""
    
    def __init__(
        self,
        max_attempts: int = 3,
        strategy: RetryStrategy = RetryStrategy.EXPONENTIAL,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        backoff_multiplier: float = 2.0,
        jitter: bool = True,
        retryable_exceptions: tuple = (Exception,)
    ):
        self.max_attempts = max_attempts
        self.strategy = strategy
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.backoff_multiplier = backoff_multiplier
        self.jitter = jitter
        self.retryable_exceptions = retryable_exceptions


class RetryResult:
    """重试执行结果"""
    
    def __init__(
        self,
        success: bool,
        result: Any = None,
        attempts: int = 0,
        total_delay: float = 0.0,
        last_error: Optional[Exception] = None
    ):
        self.success = success
        self.result = result
        self.attempts = attempts
        self.total_delay = total_delay
        self.last_error = last_error
        # 保持向后兼容
        self.error = last_error
        self.total_duration = total_delay
        self.retry_delays = []


class RetryManager:
    """重试管理器
    
    提供统一的重试机制，支持多种重试策略和条件判断。
    """
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
        self._default_config = RetryConfig()
        self._initialized = False
    
    def should_retry(self, error: Exception, attempt: int, config: RetryConfig) -> bool:
        """判断是否应该重试
        
        Args:
            error: 发生的异常
            attempt: 当前尝试次数
            config: 重试配置
            
        Returns:
            bool: 是否应该重试
        """
        # 检查是否超过最大尝试次数
        if attempt >= config.max_attempts:
            return False
        
        # 检查异常类型是否在可重试异常列表中
        if config.retryable_exceptions:
            return isinstance(error, config.retryable_exceptions)
        
        # 检查异常类型是否可重试
        return self._is_retryable_error(error)
    
    def _is_retryable_error(self, error: Exception) -> bool:
        """判断异常是否可重试
        
        Args:
            error: 异常对象
            
        Returns:
            bool: 是否可重试
        """
        # 网络相关错误通常可重试
        retryable_errors = (
            ConnectionError,
            TimeoutError,
            OSError,
        )
        
        # 检查异常类型
        if isinstance(error, retryable_errors):
            return True
        
        # 检查异常消息中的关键词
        error_message = str(error).lower()
        retryable_keywords = [
            'timeout', 'connection', 'network', 'temporary',
            'unavailable', 'busy', 'overloaded', 'rate limit'
        ]
        
        return any(keyword in error_message for keyword in retryable_keywords)
    
    def calculate_retry_delay(self, attempt: int, config: RetryConfig) -> float:
        """计算重试延迟时间
        
        Args:
            attempt: 当前尝试次数（从1开始）
            config: 重试配置
            
        Returns:
            float: 延迟时间（秒）
        """
        if config.strategy == RetryStrategy.FIXED:
            delay = config.base_delay
        elif config.strategy == RetryStrategy.LINEAR:
            delay = config.base_delay + (config.backoff_multiplier * attempt)
        elif config.strategy == RetryStrategy.EXPONENTIAL:
            delay = config.base_delay * (config.backoff_multiplier ** (attempt - 1))
        elif config.strategy == RetryStrategy.RANDOM:
            delay = random.uniform(config.base_delay, config.max_delay)
        else:
            delay = config.base_delay
        
        # 限制最大延迟
        delay = min(delay, config.max_delay)
        
        # 添加抖动以避免雷群效应
        if config.jitter:
            jitter_range = delay * 0.1  # 10% jitter
            jitter = random.uniform(-jitter_range, jitter_range)
            delay = max(0, delay + jitter)
        
        return delay
    
    def calculate_delay(self, config: RetryConfig, attempt: int) -> float:
        """计算延迟时间（兼容方法）
        
        Args:
            config: 重试配置
            attempt: 尝试次数（从0开始）
            
        Returns:
            float: 延迟时间（秒）
        """
        if config.strategy == RetryStrategy.FIXED:
            delay = config.base_delay
        elif config.strategy == RetryStrategy.LINEAR:
            delay = config.base_delay + (config.backoff_multiplier * attempt)
        elif config.strategy == RetryStrategy.EXPONENTIAL:
            delay = config.base_delay * (config.backoff_multiplier ** attempt)
        elif config.strategy == RetryStrategy.RANDOM:
            delay = random.uniform(config.base_delay, config.max_delay)
        else:
            delay = config.base_delay
        
        # 限制最大延迟
        delay = min(delay, config.max_delay)
        
        # 添加抖动以避免雷群效应
        if config.jitter:
            jitter_range = delay * 0.1  # 10% jitter
            jitter = random.uniform(-jitter_range, jitter_range)
            delay = max(0, delay + jitter)
        
        return delay
    
    async def initialize(self):
        """初始化重试管理器"""
        self._initialized = True
        self.logger.info("重试管理器已初始化")
    
    async def cleanup(self):
        """清理重试管理器"""
        self._initialized = False
        self.logger.info("重试管理器已清理")
    
    async def execute_with_retry(
        self,
        func: Union[Callable[[], Any], Callable[[], Awaitable[Any]]],
        config: Optional[RetryConfig] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> RetryResult:
        """带重试的执行函数
        
        Args:
            func: 要执行的函数（同步或异步）
            config: 重试配置
            context: 执行上下文信息
            
        Returns:
            RetryResult: 执行结果
        """
        config = config or self._default_config
        context = context or {}
        
        start_time = time.time()
        attempts = 0
        retry_delays = []
        last_error = None
        
        while attempts < config.max_attempts:
            attempts += 1
            
            try:
                self.logger.debug(
                    f"执行尝试 {attempts}/{config.max_attempts}",
                    extra={"context": context, "attempt": attempts}
                )
                
                # 执行函数
                if asyncio.iscoroutinefunction(func):
                    result = await func()
                else:
                    result = func()
                
                # 成功执行
                total_duration = time.time() - start_time
                
                self.logger.info(
                    f"执行成功，尝试次数: {attempts}, 总耗时: {total_duration:.2f}秒",
                    extra={
                        "context": context,
                        "attempts": attempts,
                        "total_duration": total_duration,
                        "retry_delays": retry_delays
                    }
                )
                
                return RetryResult(
                    success=True,
                    result=result,
                    attempts=attempts,
                    total_delay=total_duration,
                    last_error=None
                )
                
            except Exception as error:
                last_error = error
                
                self.logger.warning(
                    f"执行失败，尝试 {attempts}/{config.max_attempts}: {str(error)}",
                    extra={
                        "context": context,
                        "attempt": attempts,
                        "error": str(error),
                        "error_type": type(error).__name__
                    }
                )
                
                # 判断是否应该重试
                if not self.should_retry(error, attempts, config):
                    self.logger.error(
                        f"不可重试的错误或达到最大尝试次数: {str(error)}",
                        extra={"context": context, "final_attempt": attempts}
                    )
                    break
                
                # 计算延迟时间
                if attempts < config.max_attempts:
                    delay = self.calculate_retry_delay(attempts, config)
                    retry_delays.append(delay)
                    
                    self.logger.info(
                        f"等待 {delay:.2f} 秒后重试",
                        extra={"context": context, "delay": delay}
                    )
                    
                    await asyncio.sleep(delay)
        
        # 所有尝试都失败
        total_duration = time.time() - start_time
        
        self.logger.error(
            f"执行最终失败，总尝试次数: {attempts}, 总耗时: {total_duration:.2f}秒",
            extra={
                "context": context,
                "attempts": attempts,
                "total_duration": total_duration,
                "final_error": str(last_error),
                "retry_delays": retry_delays
            }
        )
        
        return RetryResult(
            success=False,
            result=None,
            attempts=attempts,
            total_delay=total_duration,
            last_error=last_error
        )
    
    def create_config(
        self,
        max_attempts: int = 3,
        strategy: Union[str, RetryStrategy] = RetryStrategy.EXPONENTIAL,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        **kwargs
    ) -> RetryConfig:
        """创建重试配置
        
        Args:
            max_attempts: 最大尝试次数
            strategy: 重试策略
            base_delay: 基础延迟时间
            max_delay: 最大延迟时间
            **kwargs: 其他配置参数
            
        Returns:
            RetryConfig: 重试配置对象
        """
        if isinstance(strategy, str):
            strategy = RetryStrategy(strategy)
        
        return RetryConfig(
            max_attempts=max_attempts,
            strategy=strategy,
            base_delay=base_delay,
            max_delay=max_delay,
            **kwargs
        )
    
    def get_retry_statistics(self, result: RetryResult) -> Dict[str, Any]:
        """获取重试统计信息
        
        Args:
            result: 重试结果
            
        Returns:
            Dict[str, Any]: 统计信息
        """
        return {
            'success': result.success,
            'attempts': result.attempts,
            'total_duration': result.total_duration,
            'avg_delay': sum(result.retry_delays) / len(result.retry_delays) if result.retry_delays else 0,
            'total_delay': sum(result.retry_delays),
            'retry_count': len(result.retry_delays),
            'error_type': type(result.error).__name__ if result.error else None,
            'error_message': str(result.error) if result.error else None
        }


# 全局重试管理器实例
_global_retry_manager: Optional[RetryManager] = None


def get_retry_manager() -> RetryManager:
    """获取全局重试管理器实例
    
    Returns:
        RetryManager: 重试管理器实例
    """
    global _global_retry_manager
    if _global_retry_manager is None:
        _global_retry_manager = RetryManager()
    return _global_retry_manager


# 独立的延迟计算函数
def calculate_exponential_delay(config: RetryConfig, attempt: int) -> float:
    """计算指数延迟
    
    Args:
        config: 重试配置
        attempt: 尝试次数（从0开始）
        
    Returns:
        float: 延迟时间（秒）
    """
    delay = config.base_delay * (config.backoff_multiplier ** attempt)
    delay = min(delay, config.max_delay)
    
    if config.jitter:
        jitter_range = delay * 0.1  # 10% jitter
        jitter = random.uniform(-jitter_range, jitter_range)
        delay = max(0, delay + jitter)
    
    return delay


def calculate_linear_delay(config: RetryConfig, attempt: int) -> float:
    """计算线性延迟
    
    Args:
        config: 重试配置
        attempt: 尝试次数（从0开始）
        
    Returns:
        float: 延迟时间（秒）
    """
    delay = config.base_delay + (config.backoff_multiplier * attempt)
    delay = min(delay, config.max_delay)
    
    if config.jitter:
        jitter_range = delay * 0.1  # 10% jitter
        jitter = random.uniform(-jitter_range, jitter_range)
        delay = max(0, delay + jitter)
    
    return delay


def calculate_fixed_delay(config: RetryConfig, attempt: int) -> float:
    """计算固定延迟
    
    Args:
        config: 重试配置
        attempt: 尝试次数（从0开始）
        
    Returns:
        float: 延迟时间（秒）
    """
    delay = config.base_delay
    
    if config.jitter:
        jitter_range = delay * 0.1  # 10% jitter
        jitter = random.uniform(-jitter_range, jitter_range)
        delay = max(0, delay + jitter)
    
    return delay


def calculate_random_delay(config: RetryConfig, attempt: int) -> float:
    """计算随机延迟
    
    Args:
        config: 重试配置
        attempt: 尝试次数（从0开始）
        
    Returns:
        float: 延迟时间（秒）
    """
    delay = random.uniform(config.base_delay, config.max_delay)
    
    if config.jitter:
        jitter_range = delay * 0.1  # 10% jitter
        jitter = random.uniform(-jitter_range, jitter_range)
        delay = max(0, delay + jitter)
    
    return delay


# 独立的执行函数
async def execute_with_retry(
    func: Union[Callable[[], Any], Callable[[], Awaitable[Any]]],
    config: Optional[RetryConfig] = None
) -> RetryResult:
    """带重试的执行函数（独立版本）
    
    Args:
        func: 要执行的函数（同步或异步）
        config: 重试配置
        
    Returns:
        RetryResult: 执行结果
    """
    manager = get_retry_manager()
    return await manager.execute_with_retry(func, config)


# 便捷函数
async def retry_async(
    func: Callable[[], Awaitable[Any]],
    max_attempts: int = 3,
    strategy: Union[str, RetryStrategy] = RetryStrategy.EXPONENTIAL,
    base_delay: float = 1.0,
    **kwargs
) -> RetryResult:
    """异步函数重试便捷函数
    
    Args:
        func: 异步函数
        max_attempts: 最大尝试次数
        strategy: 重试策略
        base_delay: 基础延迟时间
        **kwargs: 其他配置参数
        
    Returns:
        RetryResult: 执行结果
    """
    manager = get_retry_manager()
    config = manager.create_config(
        max_attempts=max_attempts,
        strategy=strategy,
        base_delay=base_delay,
        **kwargs
    )
    return await manager.execute_with_retry(func, config)


def retry_sync(
    func: Callable[[], Any],
    max_attempts: int = 3,
    strategy: Union[str, RetryStrategy] = RetryStrategy.EXPONENTIAL,
    base_delay: float = 1.0,
    **kwargs
) -> RetryResult:
    """同步函数重试便捷函数
    
    Args:
        func: 同步函数
        max_attempts: 最大尝试次数
        strategy: 重试策略
        base_delay: 基础延迟时间
        **kwargs: 其他配置参数
        
    Returns:
        RetryResult: 执行结果
    """
    manager = get_retry_manager()
    config = manager.create_config(
        max_attempts=max_attempts,
        strategy=strategy,
        base_delay=base_delay,
        **kwargs
    )
    return asyncio.run(manager.execute_with_retry(func, config))