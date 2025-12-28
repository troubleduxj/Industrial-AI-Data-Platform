"""
数据采集层模块

提供统一的数据采集接口，支持多种协议适配器。
"""

from platform_core.ingestion.adapters.base_adapter import (
    BaseAdapter,
    DataPoint,
    AdapterStatus,
    AdapterStatistics,
)
from platform_core.ingestion.validator import (
    DataValidator,
    DataType,
    SignalDefinitionConfig,
    ValidationResult,
    DataPointValidationResult,
)
from platform_core.ingestion.retry_manager import (
    RetryManager,
    RetryConfig,
    RetryStrategy,
    ErrorLogger,
    ErrorRecord,
    get_retry_manager,
    get_error_logger,
    with_retry,
)
from platform_core.ingestion.monitor import (
    IngestionMonitor,
    HealthStatus,
    AdapterHealthInfo,
    IngestionMetrics,
    get_ingestion_monitor,
)
from platform_core.ingestion.dual_write_config import (
    DualWriteConfigManager,
    CategoryDualWriteConfig,
    get_dual_write_config_manager,
    init_dual_write_config,
)
from platform_core.ingestion.dual_writer import (
    DualWriteAdapter,
    DualWriteResult,
    DualWriteError,
    get_dual_write_adapter,
    create_dual_write_adapter,
)
from platform_core.ingestion.consistency_verifier import (
    ConsistencyVerifier,
    ConsistencyReport,
    DataMismatch,
    verify_dual_write_consistency,
    create_mock_consistency_report,
)

# 为了向后兼容，DualWriter 是 DualWriteAdapter 的别名
DualWriter = DualWriteAdapter

__all__ = [
    # 适配器基类
    "BaseAdapter",
    "DataPoint",
    "AdapterStatus",
    "AdapterStatistics",
    # 验证器
    "DataValidator",
    "DataType",
    "SignalDefinitionConfig",
    "ValidationResult",
    "DataPointValidationResult",
    # 重试管理
    "RetryManager",
    "RetryConfig",
    "RetryStrategy",
    "ErrorLogger",
    "ErrorRecord",
    "get_retry_manager",
    "get_error_logger",
    "with_retry",
    # 监控
    "IngestionMonitor",
    "HealthStatus",
    "AdapterHealthInfo",
    "IngestionMetrics",
    "get_ingestion_monitor",
    # 双写配置
    "DualWriteConfigManager",
    "CategoryDualWriteConfig",
    "get_dual_write_config_manager",
    "init_dual_write_config",
    # 双写适配器
    "DualWriteAdapter",
    "DualWriter",  # 别名
    "DualWriteResult",
    "DualWriteError",
    "get_dual_write_adapter",
    "create_dual_write_adapter",
    # 一致性验证
    "ConsistencyVerifier",
    "ConsistencyReport",
    "DataMismatch",
    "verify_dual_write_consistency",
    "create_mock_consistency_report",
]
