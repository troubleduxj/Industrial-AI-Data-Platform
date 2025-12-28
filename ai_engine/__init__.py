"""
AI Engine Module - 工业AI数据平台AI引擎层

包含以下子模块:
- decision_engine: 决策引擎，将AI预测结果转化为告警和动作
- model_storage: 模型文件存储服务
- feature_hub: 特征工厂，特征存储和血缘追踪
- model_registry: 模型注册和版本管理
- inference: 推理服务和预测存储
"""

__version__ = "2.0.0"

# 导出feature_hub模块
from .feature_hub import (
    FeatureStore,
    FeatureTableNaming,
    FeatureRecord,
    FeatureTableConfig,
    TableNameError,
    LineageTracker,
    FeatureLineage,
    LineageGraph,
)

# 导出decision_engine模块
from .decision_engine import (
    RuleParser,
    Rule,
    Condition,
    ConditionGroup,
    Action,
    ConditionOperator,
    LogicalOperator,
    RuleRuntime,
    ActionExecutor,
    AuditLogger,
    rule_runtime,
    action_executor,
    audit_logger,
)

# 导出model_storage模块
from .model_storage import (
    StorageBackend,
    StorageResult,
    LocalStorage,
    MinIOStorage,
    ModelStorageService,
    get_model_storage_service,
)

# 导出model_registry模块
from .model_registry import (
    ModelRegistry,
    ModelVersionManager,
    ModelInfo,
    VersionInfo,
    ModelRegistryError,
)

# 导出inference模块
from .inference import (
    PredictionStore,
    PredictionStoreError,
    get_prediction_store,
)

__all__ = [
    # Feature Store
    "FeatureStore",
    "FeatureTableNaming",
    "FeatureRecord",
    "FeatureTableConfig",
    "TableNameError",
    # Lineage Tracker
    "LineageTracker",
    "FeatureLineage",
    "LineageGraph",
    # Decision Engine
    "RuleParser",
    "Rule",
    "Condition",
    "ConditionGroup",
    "Action",
    "ConditionOperator",
    "LogicalOperator",
    "RuleRuntime",
    "ActionExecutor",
    "AuditLogger",
    "rule_runtime",
    "action_executor",
    "audit_logger",
    # Model Storage
    "StorageBackend",
    "StorageResult",
    "LocalStorage",
    "MinIOStorage",
    "ModelStorageService",
    "get_model_storage_service",
    # Model Registry
    "ModelRegistry",
    "ModelVersionManager",
    "ModelInfo",
    "VersionInfo",
    "ModelRegistryError",
    # Inference
    "PredictionStore",
    "PredictionStoreError",
    "get_prediction_store",
]
