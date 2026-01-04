"""
AI Engine Module - 工业AI数据平台AI引擎层

包含以下子模块:
- model: 模型管理（整合model_registry和model_storage）
- inference: 推理服务和预测存储
- feature: 特征工程（原feature_hub）
- decision: 决策引擎（原decision_engine）

注意: 为保持向后兼容，旧模块名（feature_hub、decision_engine、
model_registry、model_storage）仍可使用，但建议迁移到新模块名。
"""

__version__ = "3.0.0"

# 导出feature模块（新名称）
from .feature import (
    FeatureStore,
    FeatureTableNaming,
    FeatureRecord,
    FeatureTableConfig,
    TableNameError,
    LineageTracker,
    FeatureLineage,
    LineageGraph,
    feature_store,
    lineage_tracker,
)

# 导出decision模块（新名称）
from .decision import (
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

# 导出model模块（整合后的新模块）
from .model import (
    # Model Registry
    ModelRegistry,
    ModelVersionManager,
    ModelInfo,
    VersionInfo,
    ModelRegistryError,
    # Model Storage
    ModelStorage,
    ModelStorageService,
    get_model_storage_service,
    set_model_storage_service,
    # Storage Backends
    StorageBackend,
    StorageResult,
    LocalStorage,
    MinIOStorage,
)

# 导出inference模块
from .inference import (
    PredictionStore,
    PredictionStoreError,
    get_prediction_store,
)

__all__ = [
    # Feature (原feature_hub)
    "FeatureStore",
    "FeatureTableNaming",
    "FeatureRecord",
    "FeatureTableConfig",
    "TableNameError",
    "LineageTracker",
    "FeatureLineage",
    "LineageGraph",
    "feature_store",
    "lineage_tracker",
    # Decision (原decision_engine)
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
    # Model (整合model_registry和model_storage)
    "ModelRegistry",
    "ModelVersionManager",
    "ModelInfo",
    "VersionInfo",
    "ModelRegistryError",
    "ModelStorage",
    "ModelStorageService",
    "get_model_storage_service",
    "set_model_storage_service",
    "StorageBackend",
    "StorageResult",
    "LocalStorage",
    "MinIOStorage",
    # Inference
    "PredictionStore",
    "PredictionStoreError",
    "get_prediction_store",
]
