"""
Platform Ingestion Module - 数据采集层

提供统一的数据采集接口，支持多种协议适配器。

包含以下组件:
- adapters: 协议适配器 (MQTT, HTTP, Modbus等)
- validator: 数据验证器
- dual_writer: 双写服务
- retry_manager: 重试管理器
- monitor: 采集状态监控

注意: 此模块是 platform_core/ingestion 的别名，
为保持向后兼容性，实际实现位于 platform_core/ingestion。
"""

__version__ = "2.0.0"

# 从 platform_core.ingestion 导入所有组件以保持向后兼容
from platform_core.ingestion import (
    # 适配器基类
    BaseAdapter,
    DataPoint,
    AdapterStatus,
    AdapterStatistics,
    # 验证器
    DataValidator,
    DataType,
    SignalDefinitionConfig,
    ValidationResult,
    DataPointValidationResult,
    # 重试管理
    RetryManager,
    RetryConfig,
    RetryStrategy,
    ErrorLogger,
    ErrorRecord,
    get_retry_manager,
    get_error_logger,
    with_retry,
    # 监控
    IngestionMonitor,
    HealthStatus,
    AdapterHealthInfo,
    IngestionMetrics,
    get_ingestion_monitor,
    # 双写配置
    DualWriteConfigManager,
    CategoryDualWriteConfig,
    get_dual_write_config_manager,
    init_dual_write_config,
    # 双写适配器
    DualWriteAdapter,
    DualWriteResult,
    DualWriteError,
    get_dual_write_adapter,
    create_dual_write_adapter,
    # 一致性验证
    ConsistencyVerifier,
    ConsistencyReport,
    DataMismatch,
    verify_dual_write_consistency,
    create_mock_consistency_report,
)

# 尝试导入具体适配器实现
try:
    from platform_core.ingestion.adapters.mqtt_adapter import MQTTAdapter
except ImportError:
    MQTTAdapter = None  # type: ignore

try:
    from platform_core.ingestion.adapters.http_adapter import HTTPAdapter
except ImportError:
    HTTPAdapter = None  # type: ignore

# 为了向后兼容，也导出DualWriter作为DualWriteAdapter的别名
DualWriter = DualWriteAdapter

__all__ = [
    # 适配器基类
    "BaseAdapter",
    "DataPoint",
    "AdapterStatus",
    "AdapterStatistics",
    # 具体适配器
    "MQTTAdapter",
    "HTTPAdapter",
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
