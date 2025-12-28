# 工业AI数据平台 - 核心模型升级
# 基于现有 app/models/device.py 进行扩展
# 实现元数据驱动架构的核心数据模型

from tortoise import fields
from app.models.base import BaseModel, TimestampMixin


# =====================================================
# 阶段1：元数据驱动核心表
# =====================================================

class AssetCategory(TimestampMixin, BaseModel):
    """
    资产类别表 - 替代 DeviceType
    
    核心功能：
    - 定义资产类型的元数据
    - 配置TDengine数据库和超级表
    - 支持多行业资产分类
    """
    
    # 基础字段
    code = fields.CharField(max_length=50, unique=True, description="类别编码", index=True)
    name = fields.CharField(max_length=100, description="类别名称")
    description = fields.TextField(null=True, description="类别描述")
    
    # 平台化字段
    icon = fields.CharField(max_length=100, null=True, description="图标")
    industry = fields.CharField(max_length=50, null=True, description="所属行业", index=True)
    
    # TDengine配置
    tdengine_database = fields.CharField(max_length=100, description="TDengine数据库名")
    tdengine_stable_prefix = fields.CharField(max_length=50, description="超级表前缀")
    
    # 状态字段
    is_active = fields.BooleanField(default=True, description="是否激活", index=True)
    asset_count = fields.IntField(default=0, description="资产数量")
    
    # 扩展配置
    config = fields.JSONField(null=True, description="扩展配置")
    
    class Meta:
        table = "t_asset_category"
        table_description = "资产类别表"
        indexes = [
            ("is_active", "industry"),
            ("code",)
        ]
        app = "models"


class SignalDefinition(TimestampMixin, BaseModel):
    """
    信号定义表 - 升级版 DeviceField
    
    核心功能：
    - 定义资产数据点的元数据
    - 配置数据存储和实时监控
    - 支持特征工程和AI分析
    """
    
    # 关联资产类别
    category = fields.ForeignKeyField(
        "models.AssetCategory", 
        related_name="signals",
        on_delete=fields.CASCADE
    )
    
    # 基础字段
    code = fields.CharField(max_length=50, description="信号编码")
    name = fields.CharField(max_length=100, description="信号名称")
    data_type = fields.CharField(max_length=20, description="数据类型: float/int/bool/string/double/bigint")
    unit = fields.CharField(max_length=20, null=True, description="单位")
    
    # 平台化配置
    is_stored = fields.BooleanField(default=True, description="是否存储到时序数据库")
    is_realtime = fields.BooleanField(default=True, description="是否实时监控")
    is_feature = fields.BooleanField(default=False, description="是否用于特征工程")
    is_alarm_enabled = fields.BooleanField(default=False, description="是否启用报警")
    
    # 数据范围和验证
    value_range = fields.JSONField(null=True, description='值范围: {"min": 0, "max": 100}')
    validation_rules = fields.JSONField(null=True, description="验证规则")
    alarm_threshold = fields.JSONField(null=True, description='报警阈值: {"warning": 80, "critical": 90}')
    
    # 聚合配置
    aggregation_method = fields.CharField(max_length=20, null=True, description="聚合方法: avg/sum/max/min/count")
    
    # 显示配置
    display_config = fields.JSONField(null=True, description="前端显示配置")
    sort_order = fields.IntField(default=0, description="排序")
    
    # 分组配置
    field_group = fields.CharField(max_length=50, default="default", description="字段分组")
    is_default_visible = fields.BooleanField(default=True, description="是否默认显示")
    
    # 状态
    is_active = fields.BooleanField(default=True, description="是否激活", index=True)
    
    class Meta:
        table = "t_signal_definition"
        table_description = "信号定义表"
        unique_together = [("category_id", "code")]
        indexes = [
            ("category_id", "sort_order"),
            ("is_realtime",),
            ("is_feature",),
            ("is_active",)
        ]
        app = "models"


class Asset(TimestampMixin, BaseModel):
    """
    资产表 - 升级版 DeviceInfo
    
    核心功能：
    - 存储资产实例信息
    - 支持动态属性扩展
    - 关联资产类别元数据
    """
    
    # 关联资产类别
    category = fields.ForeignKeyField(
        "models.AssetCategory", 
        related_name="assets",
        on_delete=fields.RESTRICT
    )
    
    # 基础字段
    code = fields.CharField(max_length=100, unique=True, description="资产编号", index=True)
    name = fields.CharField(max_length=100, description="资产名称", index=True)
    
    # 静态属性 (JSONB存储)
    attributes = fields.JSONField(default=dict, description="静态属性")
    
    # 位置和状态
    location = fields.CharField(max_length=255, null=True, description="位置", index=True)
    status = fields.CharField(max_length=20, default="offline", description="状态: online/offline/error/maintenance", index=True)
    
    # 扩展字段
    manufacturer = fields.CharField(max_length=100, null=True, description="制造商")
    model = fields.CharField(max_length=50, null=True, description="型号")
    serial_number = fields.CharField(max_length=100, null=True, description="序列号")
    install_date = fields.DateField(null=True, description="安装日期")
    
    # 组织归属
    department = fields.CharField(max_length=100, null=True, description="所属部门")
    team = fields.CharField(max_length=100, null=True, description="所属班组")
    
    # 网络配置
    ip_address = fields.CharField(max_length=50, null=True, description="IP地址")
    mac_address = fields.CharField(max_length=50, null=True, description="MAC地址")
    
    # 状态标记
    is_locked = fields.BooleanField(default=False, description="是否锁定")
    is_active = fields.BooleanField(default=True, description="是否激活", index=True)
    
    class Meta:
        table = "t_asset"
        table_description = "资产表"
        indexes = [
            ("category_id", "status"),
            ("location",),
            ("is_active",)
        ]
        app = "models"


# =====================================================
# 阶段2：AI引擎核心表
# =====================================================

class AIModel(TimestampMixin, BaseModel):
    """
    AI模型注册表
    
    核心功能：
    - 注册和管理AI模型
    - 配置模型超参数和特征
    - 关联资产类别
    """
    
    # 基础信息
    name = fields.CharField(max_length=100, description="模型名称")
    code = fields.CharField(max_length=50, unique=True, description="模型编码", index=True)
    algorithm = fields.CharField(max_length=50, description="算法类型: isolation_forest/arima/xgboost/lstm")
    target_signal = fields.CharField(max_length=50, description="目标信号")
    description = fields.TextField(null=True, description="模型描述")
    
    # 关联资产类别
    category = fields.ForeignKeyField(
        "models.AssetCategory", 
        related_name="ai_models",
        on_delete=fields.RESTRICT
    )
    
    # 模型配置
    hyperparameters = fields.JSONField(default=dict, description="超参数配置")
    feature_config = fields.JSONField(default=dict, description="特征配置")
    training_config = fields.JSONField(null=True, description="训练配置")
    
    # 状态
    status = fields.CharField(max_length=20, default="draft", description="状态: draft/training/trained/deployed/archived", index=True)
    is_active = fields.BooleanField(default=False, description="是否激活", index=True)
    
    # 审计字段
    created_by = fields.BigIntField(null=True, description="创建人ID")
    updated_by = fields.BigIntField(null=True, description="更新人ID")
    
    class Meta:
        table = "t_ai_model"
        table_description = "AI模型表"
        indexes = [
            ("category_id", "status"),
            ("algorithm",),
            ("is_active",)
        ]
        app = "models"


class AIModelVersion(TimestampMixin, BaseModel):
    """
    AI模型版本表
    
    核心功能：
    - 管理模型版本
    - 存储模型文件路径
    - 记录评估指标
    """
    
    # 关联模型
    model = fields.ForeignKeyField(
        "models.AIModel", 
        related_name="versions",
        on_delete=fields.CASCADE
    )
    
    # 版本信息
    version = fields.CharField(max_length=20, description="版本号")
    file_path = fields.CharField(max_length=500, description="模型文件路径")
    file_size = fields.BigIntField(null=True, description="文件大小(字节)")
    file_hash = fields.CharField(max_length=64, null=True, description="文件哈希值")
    
    # 训练信息
    training_start_time = fields.DatetimeField(null=True, description="训练开始时间")
    training_end_time = fields.DatetimeField(null=True, description="训练结束时间")
    training_data_range = fields.JSONField(null=True, description="训练数据范围")
    training_samples = fields.BigIntField(null=True, description="训练样本数")
    
    # 评估指标
    metrics = fields.JSONField(default=dict, description="评估指标")
    
    # 状态
    status = fields.CharField(max_length=20, default="staging", description="状态: staging/prod/archived", index=True)
    
    # 部署信息
    deployed_at = fields.DatetimeField(null=True, description="部署时间")
    deployed_by = fields.BigIntField(null=True, description="部署人ID")
    
    # 备注
    release_notes = fields.TextField(null=True, description="版本说明")
    
    class Meta:
        table = "t_ai_model_version"
        table_description = "AI模型版本表"
        unique_together = [("model_id", "version")]
        indexes = [
            ("model_id", "status"),
            ("status",)
        ]
        app = "models"


class AIPrediction(TimestampMixin, BaseModel):
    """
    AI预测结果表
    
    核心功能：
    - 存储预测结果
    - 记录输入数据快照
    - 支持预测结果追溯
    """
    
    # 关联
    model_version = fields.ForeignKeyField(
        "models.AIModelVersion", 
        related_name="predictions",
        on_delete=fields.RESTRICT
    )
    asset = fields.ForeignKeyField(
        "models.Asset", 
        related_name="predictions",
        on_delete=fields.CASCADE
    )
    
    # 预测数据
    input_data = fields.JSONField(description="输入数据快照")
    predicted_value = fields.FloatField(description="预测值")
    confidence = fields.FloatField(null=True, description="置信度")
    prediction_details = fields.JSONField(null=True, description="预测详情")
    
    # 时间
    prediction_time = fields.DatetimeField(description="预测时间", index=True)
    target_time = fields.DatetimeField(description="目标时间")
    
    # 实际值（用于模型评估）
    actual_value = fields.FloatField(null=True, description="实际值")
    actual_recorded_at = fields.DatetimeField(null=True, description="实际值记录时间")
    
    # 状态
    is_anomaly = fields.BooleanField(null=True, description="是否异常")
    anomaly_score = fields.FloatField(null=True, description="异常分数")
    
    class Meta:
        table = "t_ai_prediction"
        table_description = "AI预测结果表"
        indexes = [
            ("asset_id", "prediction_time"),
            ("model_version_id", "prediction_time"),
            ("is_anomaly",)
        ]
        app = "models"


# =====================================================
# 阶段3：特征工程表
# =====================================================

class FeatureDefinition(TimestampMixin, BaseModel):
    """
    特征定义表
    
    核心功能：
    - 定义特征计算逻辑
    - 支持JSON DSL配置
    - 关联资产类别
    """
    
    # 关联资产类别
    category = fields.ForeignKeyField(
        "models.AssetCategory", 
        related_name="features",
        on_delete=fields.CASCADE
    )
    
    # 基础信息
    name = fields.CharField(max_length=100, description="特征名称")
    code = fields.CharField(max_length=50, description="特征编码")
    description = fields.TextField(null=True, description="特征描述")
    
    # 计算配置 (JSON DSL)
    calculation_config = fields.JSONField(description="计算配置")
    # 示例: {
    #   "source_signal": "current", 
    #   "function": "avg", 
    #   "window": "1h",
    #   "slide_interval": "10m",
    #   "filters": {},
    #   "group_by": ["asset_id"]
    # }
    
    # 输出配置
    output_type = fields.CharField(max_length=20, default="double", description="输出数据类型")
    output_unit = fields.CharField(max_length=20, null=True, description="输出单位")
    
    # TDengine流计算配置
    stream_name = fields.CharField(max_length=100, null=True, description="流计算名称")
    target_table = fields.CharField(max_length=100, null=True, description="目标表名")
    
    # 状态
    is_active = fields.BooleanField(default=True, description="是否激活", index=True)
    
    class Meta:
        table = "t_feature_definition"
        table_description = "特征定义表"
        unique_together = [("category_id", "code")]
        indexes = [
            ("category_id", "is_active"),
        ]
        app = "models"


class FeatureView(TimestampMixin, BaseModel):
    """
    特征视图表
    
    核心功能：
    - 组织多个特征定义
    - 管理特征视图生命周期
    - 配置流计算任务
    """
    
    # 关联资产类别
    category = fields.ForeignKeyField(
        "models.AssetCategory", 
        related_name="feature_views",
        on_delete=fields.CASCADE
    )
    
    # 基础信息
    name = fields.CharField(max_length=100, description="视图名称")
    code = fields.CharField(max_length=50, description="视图编码")
    description = fields.TextField(null=True, description="视图描述")
    
    # 特征列表
    feature_codes = fields.JSONField(description="包含的特征编码列表")
    
    # TDengine配置
    stream_name = fields.CharField(max_length=100, null=True, description="流计算名称")
    target_stable = fields.CharField(max_length=100, null=True, description="目标超级表名")
    
    # 状态
    status = fields.CharField(max_length=20, default="draft", description="状态: draft/active/paused/archived", index=True)
    is_active = fields.BooleanField(default=True, description="是否激活")
    
    # 质量指标
    last_quality_check = fields.DatetimeField(null=True, description="最后质量检查时间")
    quality_score = fields.FloatField(null=True, description="质量评分")
    
    class Meta:
        table = "t_feature_view"
        table_description = "特征视图表"
        unique_together = [("category_id", "code")]
        indexes = [
            ("category_id", "status"),
        ]
        app = "models"


# =====================================================
# 阶段4：Schema版本控制表
# =====================================================

class SchemaVersion(TimestampMixin, BaseModel):
    """
    Schema版本控制表
    
    核心功能：
    - 记录Schema变更历史
    - 支持Schema回滚
    - 审计Schema操作
    """
    
    # 关联资产类别
    category = fields.ForeignKeyField(
        "models.AssetCategory", 
        related_name="schema_versions",
        on_delete=fields.CASCADE
    )
    
    # 版本信息
    version = fields.CharField(max_length=20, description="版本号")
    change_type = fields.CharField(max_length=20, description="变更类型: create/add_column/modify/drop")
    
    # 变更详情
    change_details = fields.JSONField(description="变更详情")
    # 示例: {
    #   "columns_added": ["new_signal"],
    #   "columns_modified": [],
    #   "previous_schema": {...},
    #   "new_schema": {...}
    # }
    
    # 执行信息
    executed_sql = fields.TextField(null=True, description="执行的SQL")
    execution_status = fields.CharField(max_length=20, description="执行状态: success/failed/rolled_back")
    execution_time = fields.DatetimeField(description="执行时间")
    execution_duration_ms = fields.IntField(null=True, description="执行耗时(毫秒)")
    error_message = fields.TextField(null=True, description="错误信息")
    
    # 审计字段
    executed_by = fields.BigIntField(null=True, description="执行人ID")
    
    class Meta:
        table = "t_schema_version"
        table_description = "Schema版本控制表"
        indexes = [
            ("category_id", "version"),
            ("execution_status",),
            ("execution_time",)
        ]
        app = "models"


# =====================================================
# 阶段5：数据迁移跟踪表
# =====================================================

class MigrationRecord(TimestampMixin, BaseModel):
    """
    数据迁移记录表
    
    核心功能：
    - 跟踪数据迁移进度
    - 记录迁移结果
    - 支持迁移回滚
    """
    
    # 迁移信息
    migration_name = fields.CharField(max_length=100, description="迁移名称")
    migration_type = fields.CharField(max_length=50, description="迁移类型: device_type/device_field/device_info")
    
    # 源和目标
    source_table = fields.CharField(max_length=100, description="源表名")
    target_table = fields.CharField(max_length=100, description="目标表名")
    
    # 迁移统计
    total_records = fields.BigIntField(default=0, description="总记录数")
    migrated_records = fields.BigIntField(default=0, description="已迁移记录数")
    failed_records = fields.BigIntField(default=0, description="失败记录数")
    skipped_records = fields.BigIntField(default=0, description="跳过记录数")
    
    # 状态
    status = fields.CharField(max_length=20, default="pending", description="状态: pending/running/completed/failed/rolled_back", index=True)
    
    # 时间
    started_at = fields.DatetimeField(null=True, description="开始时间")
    completed_at = fields.DatetimeField(null=True, description="完成时间")
    
    # 错误信息
    error_details = fields.JSONField(null=True, description="错误详情")
    
    # 审计字段
    executed_by = fields.BigIntField(null=True, description="执行人ID")
    
    class Meta:
        table = "t_migration_record"
        table_description = "数据迁移记录表"
        indexes = [
            ("status",),
            ("migration_type",),
            ("started_at",)
        ]
        app = "models"


# =====================================================
# 阶段6：决策引擎表 (V2升级)
# =====================================================

class DecisionRule(TimestampMixin, BaseModel):
    """
    决策规则表
    
    核心功能：
    - 存储决策引擎规则配置
    - 支持规则DSL定义
    - 关联资产类别和AI模型
    """
    
    # 规则标识
    rule_id = fields.CharField(max_length=64, unique=True, description="规则ID", index=True)
    name = fields.CharField(max_length=100, description="规则名称")
    description = fields.TextField(null=True, description="规则描述")
    
    # 关联（可选）
    category = fields.ForeignKeyField(
        "models.AssetCategory",
        related_name="decision_rules",
        on_delete=fields.SET_NULL,
        null=True
    )
    model = fields.ForeignKeyField(
        "models.AIModel",
        related_name="decision_rules",
        on_delete=fields.SET_NULL,
        null=True
    )
    
    # 规则配置 (JSON DSL)
    conditions = fields.JSONField(description="条件配置")
    actions = fields.JSONField(description="动作配置")
    
    # 规则属性
    priority = fields.IntField(default=0, description="优先级（数字越小优先级越高）")
    enabled = fields.BooleanField(default=True, description="是否启用", index=True)
    cooldown_seconds = fields.IntField(default=0, description="冷却时间（秒）")
    
    # 审计字段
    created_by = fields.BigIntField(null=True, description="创建人ID")
    updated_by = fields.BigIntField(null=True, description="更新人ID")
    
    class Meta:
        table = "t_decision_rules"
        table_description = "决策规则表"
        indexes = [
            ("enabled", "priority"),
            ("category_id",),
            ("model_id",)
        ]
        app = "models"


class DecisionAuditLog(TimestampMixin, BaseModel):
    """
    决策审计日志表
    
    核心功能：
    - 记录规则触发历史
    - 存储触发时的条件快照
    - 记录执行的动作和结果
    """
    
    # 规则信息
    rule_id = fields.CharField(max_length=64, description="规则ID", index=True)
    rule_name = fields.CharField(max_length=100, null=True, description="规则名称")
    
    # 关联资产（可选）
    asset = fields.ForeignKeyField(
        "models.Asset",
        related_name="decision_audit_logs",
        on_delete=fields.SET_NULL,
        null=True
    )
    
    # 关联预测（可选）
    prediction = fields.ForeignKeyField(
        "models.AIPrediction",
        related_name="decision_audit_logs",
        on_delete=fields.SET_NULL,
        null=True
    )
    
    # 触发信息
    trigger_time = fields.DatetimeField(description="触发时间", index=True)
    trigger_data = fields.JSONField(null=True, description="触发时的数据快照")
    
    # 条件和动作快照
    conditions_snapshot = fields.JSONField(null=True, description="条件配置快照")
    actions_executed = fields.JSONField(null=True, description="执行的动作列表")
    
    # 执行结果
    result = fields.CharField(max_length=20, default="success", description="执行结果: success/partial/failed", index=True)
    error_message = fields.TextField(null=True, description="错误信息")
    
    # 执行详情
    execution_duration_ms = fields.IntField(null=True, description="执行耗时（毫秒）")
    
    class Meta:
        table = "t_decision_audit_logs"
        table_description = "决策审计日志表"
        indexes = [
            ("rule_id", "trigger_time"),
            ("trigger_time",),
            ("result",),
            ("asset_id",)
        ]
        app = "models"


# =====================================================
# 阶段7：数据采集层表 (V2升级)
# =====================================================

class DataSource(TimestampMixin, BaseModel):
    """
    数据源配置表
    
    核心功能：
    - 存储各种协议的数据源配置
    - 管理数据源状态和统计信息
    - 支持MQTT、HTTP、Modbus等协议
    """
    
    # 基础信息
    name = fields.CharField(max_length=100, description="数据源名称")
    description = fields.TextField(null=True, description="描述")
    
    # 协议配置
    protocol = fields.CharField(max_length=20, description="协议类型: mqtt, http, modbus, opcua", index=True)
    config = fields.JSONField(description="协议特定配置")
    
    # 关联资产类别
    category = fields.ForeignKeyField(
        "models.AssetCategory",
        related_name="data_sources",
        on_delete=fields.SET_NULL,
        null=True
    )
    
    # 状态管理
    enabled = fields.BooleanField(default=True, description="是否启用", index=True)
    status = fields.CharField(max_length=20, default="stopped", description="运行状态", index=True)
    
    # 统计信息
    last_connected_at = fields.DatetimeField(null=True, description="最后连接时间")
    last_disconnected_at = fields.DatetimeField(null=True, description="最后断开时间")
    error_count = fields.IntField(default=0, description="错误计数")
    success_count = fields.BigIntField(default=0, description="成功计数")
    total_bytes_received = fields.BigIntField(default=0, description="总接收字节数")
    
    # 重试配置
    retry_config = fields.JSONField(
        default={"max_attempts": 3, "initial_delay": 1.0, "strategy": "exponential_jitter"},
        description="重试配置"
    )
    
    # 数据处理配置
    validation_enabled = fields.BooleanField(default=True, description="是否启用验证")
    transform_config = fields.JSONField(null=True, description="数据转换配置")
    
    # 审计字段
    created_by = fields.BigIntField(null=True, description="创建人ID")
    updated_by = fields.BigIntField(null=True, description="更新人ID")
    
    class Meta:
        table = "t_data_sources"
        table_description = "数据源配置表"
        indexes = [
            ("protocol",),
            ("enabled", "status"),
            ("category_id",)
        ]
        app = "models"


class DualWriteConfig(TimestampMixin, BaseModel):
    """
    双写配置表
    
    核心功能：
    - 管理新旧数据结构的双写模式
    - 支持按资产类别配置
    - 记录一致性验证结果
    """
    
    # 关联资产类别（NULL表示全局配置）
    category = fields.ForeignKeyField(
        "models.AssetCategory",
        related_name="dual_write_configs",
        on_delete=fields.CASCADE,
        null=True
    )
    
    # 配置
    enabled = fields.BooleanField(default=False, description="是否启用双写")
    write_to_new = fields.BooleanField(default=True, description="写入新结构")
    write_to_old = fields.BooleanField(default=True, description="写入旧结构")
    fail_on_old_error = fields.BooleanField(default=False, description="旧结构写入失败是否影响主流程")
    
    # 一致性验证配置
    verify_enabled = fields.BooleanField(default=False, description="是否启用一致性验证")
    verify_interval_hours = fields.IntField(default=24, description="验证间隔（小时）")
    last_verify_time = fields.DatetimeField(null=True, description="最后验证时间")
    last_verify_result = fields.JSONField(null=True, description="最后验证结果")
    
    class Meta:
        table = "t_dual_write_config"
        table_description = "双写配置表"
        unique_together = [("category_id",)]
        app = "models"


class IngestionErrorLog(BaseModel):
    """
    数据采集错误日志表
    
    核心功能：
    - 记录数据采集过程中的错误
    - 支持错误追踪和分析
    """
    
    # 关联数据源
    source = fields.ForeignKeyField(
        "models.DataSource",
        related_name="error_logs",
        on_delete=fields.CASCADE,
        null=True
    )
    source_name = fields.CharField(max_length=100, null=True, description="数据源名称")
    
    # 错误信息
    error_type = fields.CharField(max_length=100, description="错误类型", index=True)
    error_message = fields.TextField(description="错误信息")
    error_stack = fields.TextField(null=True, description="错误堆栈")
    
    # 上下文
    context = fields.JSONField(null=True, description="上下文信息")
    
    # 重试信息
    attempt = fields.IntField(default=0, description="重试次数")
    resolved = fields.BooleanField(default=False, description="是否已解决", index=True)
    resolved_at = fields.DatetimeField(null=True, description="解决时间")
    
    # 时间
    created_at = fields.DatetimeField(auto_now_add=True, description="创建时间", index=True)
    
    class Meta:
        table = "t_ingestion_error_logs"
        table_description = "数据采集错误日志表"
        indexes = [
            ("source_id",),
            ("error_type",),
            ("created_at",),
            ("resolved",)
        ]
        app = "models"


class IngestionStatistics(BaseModel):
    """
    数据采集统计表
    
    核心功能：
    - 存储数据源的历史统计信息
    - 支持按时间段聚合
    """
    
    # 关联数据源
    source = fields.ForeignKeyField(
        "models.DataSource",
        related_name="statistics",
        on_delete=fields.CASCADE
    )
    
    # 统计时间段
    period_start = fields.DatetimeField(description="统计开始时间")
    period_end = fields.DatetimeField(description="统计结束时间")
    period_type = fields.CharField(max_length=20, description="统计周期类型: minute, hour, day", index=True)
    
    # 统计数据
    data_points_count = fields.BigIntField(default=0, description="数据点数量")
    bytes_received = fields.BigIntField(default=0, description="接收字节数")
    error_count = fields.IntField(default=0, description="错误数量")
    success_rate = fields.FloatField(default=0, description="成功率")
    avg_latency_ms = fields.FloatField(default=0, description="平均延迟(毫秒)")
    max_latency_ms = fields.FloatField(default=0, description="最大延迟(毫秒)")
    
    # 时间
    created_at = fields.DatetimeField(auto_now_add=True, description="创建时间")
    
    class Meta:
        table = "t_ingestion_statistics"
        table_description = "数据采集统计表"
        indexes = [
            ("source_id",),
            ("period_start", "period_end"),
            ("period_type",)
        ]
        app = "models"


class AdapterTemplate(TimestampMixin, BaseModel):
    """
    协议适配器配置模板表
    
    核心功能：
    - 存储各协议的默认配置模板
    - 支持前端表单动态生成
    """
    
    # 基础信息
    name = fields.CharField(max_length=100, description="模板名称")
    protocol = fields.CharField(max_length=20, description="协议类型", index=True)
    description = fields.TextField(null=True, description="描述")
    
    # 配置模板
    config_template = fields.JSONField(description="配置模板")
    config_schema = fields.JSONField(null=True, description="配置Schema（用于前端表单生成）")
    
    # 状态
    is_builtin = fields.BooleanField(default=False, description="是否内置模板")
    is_active = fields.BooleanField(default=True, description="是否激活", index=True)
    
    class Meta:
        table = "t_adapter_templates"
        table_description = "协议适配器配置模板表"
        indexes = [
            ("protocol",),
            ("is_active",)
        ]
        app = "models"


# =====================================================
# 阶段8：企业身份集成表 (V2升级)
# =====================================================

class IdentityProvider(TimestampMixin, BaseModel):
    """
    身份提供商配置表
    
    核心功能：
    - 存储LDAP、OAuth2等身份提供商配置
    - 管理组到角色的映射关系
    - 支持多提供商优先级配置
    """
    
    # 基础信息
    name = fields.CharField(max_length=50, unique=True, description="提供商名称", index=True)
    type = fields.CharField(max_length=20, description="提供商类型: ldap, oauth2, saml", index=True)
    
    # 配置
    config = fields.JSONField(default=dict, description="提供商配置")
    # LDAP配置示例: {"server": "ldap://...", "base_dn": "...", "bind_dn": "...", "bind_password": "..."}
    # OAuth2配置示例: {"client_id": "...", "client_secret": "...", "authorization_url": "...", "token_url": "...", "userinfo_url": "..."}
    
    # 状态
    enabled = fields.BooleanField(default=True, description="是否启用", index=True)
    priority = fields.IntField(default=0, description="优先级（数字越小优先级越高）")
    
    # 角色映射
    role_mapping = fields.JSONField(null=True, description="组到角色映射")
    # 示例: {"admin_group": 1, "user_group": 2}
    
    class Meta:
        table = "t_identity_providers"
        table_description = "身份提供商配置表"
        indexes = [
            ("enabled", "priority"),
            ("type",)
        ]
        app = "models"


class UserExternalIdentity(TimestampMixin, BaseModel):
    """
    用户外部身份关联表
    
    核心功能：
    - 关联本地用户与外部身份
    - 记录外部身份信息
    - 跟踪最后登录时间
    """
    
    # 关联本地用户
    user_id = fields.BigIntField(description="本地用户ID", index=True)
    
    # 关联身份提供商
    provider = fields.ForeignKeyField(
        "models.IdentityProvider",
        related_name="external_identities",
        on_delete=fields.CASCADE
    )
    
    # 外部身份信息
    external_id = fields.CharField(max_length=255, description="外部用户ID")
    external_username = fields.CharField(max_length=100, null=True, description="外部用户名")
    
    # 登录信息
    last_login_at = fields.DatetimeField(null=True, description="最后登录时间")
    
    class Meta:
        table = "t_user_external_identities"
        table_description = "用户外部身份关联表"
        unique_together = [("provider_id", "external_id")]
        indexes = [
            ("user_id",),
            ("external_id",)
        ]
        app = "models"
