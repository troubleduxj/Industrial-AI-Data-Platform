"""统一日志记录机制

提供统一的日志记录功能，包括执行日志、错误日志、性能指标记录等。
"""

import logging
import json
import time
from datetime import datetime
from typing import Any, Dict, Optional, Union
from enum import Enum
from contextlib import contextmanager, asynccontextmanager
import traceback
import sys
from pathlib import Path
from app.models.enums import ExecutionPhase, LogCategory, LogLevel, ExecutionStatus


class UnifiedLogger:
    """统一日志记录器
    
    提供结构化的日志记录功能，支持多种日志类型和格式。
    """
    
    def __init__(
        self,
        name: str = "unified_logger",
        level: Union[str, int] = logging.INFO,
        log_file: Optional[str] = None,
        enable_console: bool = True,
        enable_structured: bool = True
    ):
        self.name = name
        self.logger = logging.getLogger(name)
        self._logger = self.logger  # 为了兼容测试
        self.logger.setLevel(level)
        self.enable_structured = enable_structured
        self._initialized = False
        
        # 清除现有处理器
        self.logger.handlers.clear()
        
        # 设置格式器
        if enable_structured:
            formatter = self._create_structured_formatter()
        else:
            formatter = self._create_standard_formatter()
        
        # 添加控制台处理器
        if enable_console:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)
        
        # 添加文件处理器
        if log_file:
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
    
    async def initialize(self):
        """初始化日志记录器"""
        self._initialized = True
    
    async def cleanup(self):
        """清理日志记录器"""
        self._initialized = False
    
    def _create_structured_formatter(self) -> logging.Formatter:
        """创建结构化日志格式器"""
        return StructuredFormatter()
    
    def _create_standard_formatter(self) -> logging.Formatter:
        """创建标准日志格式器"""
        return logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    


    
    def info(self, message: str, *args, **kwargs):
        """记录信息级别日志"""
        self.logger.info(message, *args, **kwargs)
    
    def warning(self, message: str, *args, **kwargs):
        """记录警告级别日志"""
        self.logger.warning(message, *args, **kwargs)
    
    def error(self, message: str, *args, **kwargs):
        """记录错误级别日志"""
        self.logger.error(message, *args, **kwargs)
    
    def debug(self, message: str, *args, **kwargs):
        """记录调试级别日志"""
        self.logger.debug(message, *args, **kwargs)
    
    def critical(self, message: str, *args, **kwargs):
        """记录严重错误级别日志"""
        self.logger.critical(message, *args, **kwargs)
    

    def log_retry_attempt(
        self,
        task_name: str,
        attempt_number: int,
        max_attempts: int,
        error_message: str,
        delay_ms: int,
        **kwargs
    ):
        """记录重试尝试日志"""
        structured_data = {
            'category': LogCategory.RETRY.value,
            'task_name': task_name,
            'attempt_number': attempt_number,
            'max_attempts': max_attempts,
            'error_message': error_message,
            'delay_ms': delay_ms,
            **kwargs
        }
        self.logger.warning(
            f"Task '{task_name}' retry attempt {attempt_number}/{max_attempts}: {error_message}. Retrying in {delay_ms}ms.",
            extra={'structured_data': structured_data}
        )

    def log_performance_metrics(
        self,
        event_name: str,
        duration_ms: float,
        data_size_bytes: Optional[int] = None,
        records_processed: Optional[int] = None,
        **kwargs
    ):
        """记录性能指标日志"""
        structured_data = {
            'category': LogCategory.PERFORMANCE.value,
            'event_name': event_name,
            'duration_ms': duration_ms,
            'data_size_bytes': data_size_bytes,
            'records_processed': records_processed,
            **kwargs
        }
        self.logger.info(
            f"Performance: {event_name} took {duration_ms:.2f}ms.",
            extra={'structured_data': structured_data}
        )

    def log_business_event(
        self,
        event_name: str,
        entity_id: str,
        event_data: Dict[str, Any],
        **kwargs
    ):
        """记录业务事件日志"""
        structured_data = {
            'category': LogCategory.BUSINESS.value,
            'event_name': event_name,
            'entity_id': entity_id,
            'event_data': event_data,
            **kwargs
        }
        self.logger.info(
            f"Business Event: {event_name} for entity {entity_id}.",
            extra={'structured_data': structured_data}
        )

    def log_system_event(
        self,
        event_name: str,
        component: str,
        status: str,
        details: Optional[Dict[str, Any]] = None,
        **kwargs
    ):
        """记录系统事件日志"""
        structured_data = {
            'category': LogCategory.SYSTEM.value,
            'event_name': event_name,
            'component': component,
            'status': status,
            'details': details,
            **kwargs
        }
        self.logger.info(
            f"System Event: {event_name} - {component} status: {status}.",
            extra={'structured_data': structured_data}
        )

    def log_security_event(
        self,
        event_name: str,
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        outcome: str = "success",
        details: Optional[Dict[str, Any]] = None,
        **kwargs
    ):
        """记录安全事件日志"""
        structured_data = {
            'category': LogCategory.SECURITY.value,
            'event_name': event_name,
            'user_id': user_id,
            'ip_address': ip_address,
            'outcome': outcome,
            'details': details,
            **kwargs
        }
        self.logger.warning(
            f"Security Event: {event_name} - Outcome: {outcome}.",
            extra={'structured_data': structured_data}
        )

    @contextmanager
    def execution_context(
        self,
        context_id: str,
        operation_name: str,
        category: LogCategory = LogCategory.EXECUTION,
        phase: ExecutionPhase = ExecutionPhase.PROCESS,
        log_level: LogLevel = LogLevel.INFO,
        config: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        parent_context_id: Optional[str] = None,
        collector_id: Optional[str] = None,
        device_id: Optional[str] = None,
        device_type: Optional[str] = None,
        **kwargs
    ):
        """执行上下文管理器"""
        start_time = time.time()
        try:
            self.log_execution_start(
                context_id=context_id,
                operation_name=operation_name,
                category=category,
                phase=phase,
                config=config,
                metadata=metadata,
                parent_context_id=parent_context_id,
                collector_id=collector_id,
                device_id=device_id,
                device_type=device_type,
                **kwargs
            )
            yield
        except Exception as e:
            self.log_execution_error(
                context_id=context_id,
                operation_name=operation_name,
                error=e,
                category=category,
                phase=phase,
                duration_ms=int((time.time() - start_time) * 1000),
                **kwargs
            )
            raise
        else:
            self.log_execution_success(
                context_id=context_id,
                operation_name=operation_name,
                category=category,
                phase=phase,
                duration_ms=int((time.time() - start_time) * 1000),
                **kwargs
            )

    def _hash_config(self, config: Dict[str, Any]) -> str:
        """生成配置哈希值（用于日志记录）"""
        try:
            # 移除敏感信息
            safe_config = self._sanitize_config(config)
            config_str = json.dumps(safe_config, sort_keys=True)
            return str(hash(config_str))
        except Exception:
            return "unknown"
    
    def _sanitize_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """清理配置中的敏感信息"""
        sensitive_keys = {
            'password', 'token', 'secret', 'key', 'auth',
            'credential', 'api_key', 'access_token'
        }
        
        sanitized = {}
        for key, value in config.items():
            if any(sensitive in key.lower() for sensitive in sensitive_keys):
                sanitized[key] = "***"
            elif isinstance(value, dict):
                sanitized[key] = self._sanitize_config(value)
            else:
                sanitized[key] = value
        
        return sanitized
    
    def _summarize_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """生成结果摘要"""
        summary = {
            'status': result.get('status', 'unknown'),
            'data_points': len(result.get('data', [])) if isinstance(result.get('data'), list) else 1,
            'has_error': 'error' in result or 'error_message' in result
        }
        
        # 添加关键指标
        if 'duration_ms' in result:
            summary['duration_ms'] = result['duration_ms']
        if 'records_processed' in result:
            summary['records_processed'] = result['records_processed']
        if 'records_stored' in result:
            summary['records_stored'] = result['records_stored']
        
        return summary


class StructuredFormatter(logging.Formatter):
    """结构化日志格式器"""
    
    def format(self, record):
        # 基础日志信息
        log_entry = {
            'timestamp': datetime.fromtimestamp(record.created).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # 添加结构化数据
        if hasattr(record, 'structured_data'):
            log_entry.update(record.structured_data)
        
        # 添加record对象的自定义属性
        custom_fields = ['category', 'phase']
        for field in custom_fields:
            if hasattr(record, field):
                log_entry[field] = getattr(record, field)
        
        # 添加异常信息
        if record.exc_info:
            if record.exc_info is True:
                # 如果 exc_info 是 True，获取当前异常信息
                import sys
                exc_info = sys.exc_info()
                if exc_info[0] is not None:
                    log_entry['exception'] = self.formatException(exc_info)
            else:
                # 如果 exc_info 是异常信息元组
                log_entry['exception'] = self.formatException(record.exc_info)
        
        return json.dumps(log_entry, ensure_ascii=False, default=str)


# 全局日志记录器实例
_global_logger = None


def get_unified_logger(
    name: str = "unified_logger",
    level: Union[str, int] = logging.INFO,
    log_file: Optional[str] = None
) -> UnifiedLogger:
    """获取统一日志记录器实例
    
    Args:
        name: 日志记录器名称
        level: 日志级别
        log_file: 日志文件路径
        
    Returns:
        UnifiedLogger: 统一日志记录器实例
    """
    global _global_logger
    if _global_logger is None:
        _global_logger = UnifiedLogger(
            name=name,
            level=level,
            log_file=log_file
        )
    return _global_logger


def get_logger(name: str = "unified_logger") -> UnifiedLogger:
    """获取日志记录器实例（兼容性函数）
    
    Args:
        name: 日志记录器名称
        
    Returns:
        UnifiedLogger: 统一日志记录器实例
    """
    return get_unified_logger(name=name)


def setup_logging(
    log_dir: str = "logs",
    log_level: Union[str, int] = logging.INFO,
    enable_file_logging: bool = True,
    enable_structured: bool = True
) -> UnifiedLogger:
    """设置统一日志系统
    
    Args:
        log_dir: 日志目录
        log_level: 日志级别
        enable_file_logging: 是否启用文件日志
        enable_structured: 是否启用结构化日志
        
    Returns:
        UnifiedLogger: 配置好的日志记录器
    """
    # 创建日志目录
    if enable_file_logging:
        log_path = Path(log_dir)
        log_path.mkdir(exist_ok=True)
        log_file = log_path / f"collector_system_{datetime.now().strftime('%Y%m%d')}.log"
    else:
        log_file = None
    
    return get_unified_logger(
        name="unified_logger",
        level=log_level,
        log_file=str(log_file) if log_file else None
    )


class ExecutionContext:
    """执行上下文类
    
    用于管理执行过程中的上下文信息和日志记录。
    """
    
    def __init__(
        self,
        logger: UnifiedLogger,
        context_id: str,
        operation_name: str
    ):
        self.logger = logger
        self.context_id = context_id
        self.operation_name = operation_name
        self.start_time = time.time()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        return False  # 不抑制异常


def sanitize_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """清理配置中的敏感信息
    
    Args:
        config: 原始配置字典
        
    Returns:
        Dict[str, Any]: 清理后的配置字典
    """
    sensitive_keys = {
        'password', 'token', 'secret', 'key',
        'credential', 'api_key', 'access_token'
    }
    
    sanitized = {}
    for key, value in config.items():
        if isinstance(value, dict):
            # 递归处理嵌套字典，即使键名包含敏感词
            sanitized[key] = sanitize_config(value)
        elif any(sensitive in key.lower() for sensitive in sensitive_keys):
            # 只有当值不是字典时才替换为 ***
            sanitized[key] = "***"
        else:
            sanitized[key] = value
    
    return sanitized


def summarize_result(result: Dict[str, Any]) -> Dict[str, Any]:
    """生成结果摘要
    
    Args:
        result: 原始结果字典
        
    Returns:
        Dict[str, Any]: 结果摘要
    """
    summary = {
        'status': result.get('status', 'unknown'),
        'has_error': 'error' in result or 'error_message' in result
    }
    
    # 处理数据计数
    if 'data' in result:
        if isinstance(result['data'], list):
            summary['data_count'] = len(result['data'])
        else:
            summary['data_count'] = 1
    
    # 检查元数据和性能信息
    summary['has_metadata'] = 'metadata' in result
    summary['has_performance'] = 'performance' in result
    
    # 添加关键指标
    if 'duration_ms' in result:
        summary['duration_ms'] = result['duration_ms']
    if 'records_processed' in result:
        summary['records_processed'] = result['records_processed']
    if 'records_stored' in result:
        summary['records_stored'] = result['records_stored']
    
    return summary