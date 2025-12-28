# 工业AI数据平台 - 核心模型升级
# 基于现有 app/models/device.py 进行扩展

from tortoise import fields
from app.models.base import BaseModel, TimestampMixin

# =====================================================
# 阶段1：元数据驱动核心表
# =====================================================

class AssetCategory(TimestampMixin, BaseModel):
    """资产类别表 - 替代 DeviceType"""
    
    # 基础字段
    code = fields.CharField(max_length=50, unique=True, description="类别编码", index=True)
    name = fields.CharField(max_length=100, description="类别名称")
    description = fields.TextField(null=True, description="类别描述")
    
    # 平台化字段
    icon = fields.CharField(max_length=100, null=True, description="图标")
    industry = fields.CharField(max_length=50, null=True, description="所属行业")
    
    # TDengine配置
    tdengine_database = fields.CharField(max_length=100, description="TDengine数据库名")
    tdengine_stable_prefix = fields.CharField(max_length=50, description="超级表前缀")
    
    # 状态字段
    is_active = fields.BooleanField(default=True, description="是否激活")
    asset_count = fields.IntField(default=0, description="资产数量")
    
    class Meta:
        table = "t_asset_category"
        table_description = "资产类别表"


class SignalDefinition(TimestampMixin, BaseModel):
    """信号定义表 - 升级版 DeviceField"""
    
    # 关联资产类别
    category = fields.ForeignKeyField("models.AssetCategory", related_name="signals")
    
    # 基础字段
    code = fields.CharField(max_length=50, description="信号编码")
    name = fields.CharField(max_length=100, description="信号名称")
    data_type = fields.CharField(max_length=20, description="数据类型: float/int/bool/string")
    unit = fields.CharField(max_length=20, null=True, description="单位")
    
    # 平台化配置
    is_stored = fields.BooleanField(default=True, description="是否存储到时序数据库")
    is_realtime = fields.BooleanField(default=True, description="是否实时监控")
    is_feature = fields.BooleanField(default=False, description="是否用于特征工程")
    
    # 数据范围和验证
    value_range = fields.JSONField(null=True, description='值范围: {"min": 0, "max": 100}')
    validation_rules = fields.JSONField(null=True, description="验证规则")
    
    # 显示配置
    display_config = fields.JSONField(null=True, description="前端显示配置")
    sort_order = fields.IntField(default=0, description="排序")
    
    class Meta:
        table = "t_signal_definition"
        table_description = "信号定义表"
        unique_together = [("category_id", "code")]


class Asset(TimestampMixin, BaseModel):
    """资产表 - 升级版 DeviceInfo"""
    
    # 关联资产类别
    category = fields.ForeignKeyField("models.AssetCategory", related_name="assets")
    
    # 基础字段
    code = fields.CharField(max_length=100, unique=True, description="资产编号")
    name = fields.CharField(max_length=100, description="资产名称")
    
    # 静态属性 (JSONB存储)
    attributes = fields.JSONField(default=dict, description="静态属性")
    
    # 位置和状态
    location = fields.CharField(max_length=255, null=True, description="位置")
    status = fields.CharField(max_length=20, default="offline", description="状态")
    
    # 扩展字段
    manufacturer = fields.CharField(max_length=100, null=True, description="制造商")
    model = fields.CharField(max_length=50, null=True, description="型号")
    install_date = fields.DateField(null=True, description="安装日期")
    
    class Meta:
        table = "t_asset"
        table_description = "资产表"


# =====================================================
# 阶段2：AI引擎核心表
# =====================================================

class AIModel(TimestampMixin, BaseModel):
    """AI模型注册表"""
    
    # 基础信息
    name = fields.CharField(max_length=100, description="模型名称")
    algorithm = fields.CharField(max_length=50, description="算法类型")
    target_signal = fields.CharField(max_length=50, description="目标信号")
    
    # 关联资产类别
    category = fields.ForeignKeyField("models.AssetCategory", related_name="ai_models")
    
    # 模型配置
    hyperparameters = fields.JSONField(default=dict, description="超参数")
    feature_config = fields.JSONField(default=dict, description="特征配置")
    
    # 状态
    status = fields.CharField(max_length=20, default="draft", description="状态")
    is_active = fields.BooleanField(default=False, description="是否激活")
    
    class Meta:
        table = "t_ai_models"
        table_description = "AI模型表"


class AIModelVersion(TimestampMixin, BaseModel):
    """AI模型版本表"""
    
    # 关联模型
    model = fields.ForeignKeyField("models.AIModel", related_name="versions")
    
    # 版本信息
    version = fields.CharField(max_length=20, description="版本号")
    file_path = fields.CharField(max_length=255, description="模型文件路径")
    
    # 评估指标
    metrics = fields.JSONField(default=dict, description="评估指标")
    
    # 状态
    status = fields.CharField(max_length=20, default="staging", description="状态: staging/prod")
    
    class Meta:
        table = "t_ai_model_versions"
        table_description = "AI模型版本表"


class AIPrediction(TimestampMixin, BaseModel):
    """AI预测结果表"""
    
    # 关联
    model_version = fields.ForeignKeyField("models.AIModelVersion", related_name="predictions")
    asset = fields.ForeignKeyField("models.Asset", related_name="predictions")
    
    # 预测数据
    input_data = fields.JSONField(description="输入数据快照")
    predicted_value = fields.FloatField(description="预测值")
    confidence = fields.FloatField(null=True, description="置信度")
    
    # 时间
    prediction_time = fields.DatetimeField(description="预测时间")
    target_time = fields.DatetimeField(description="目标时间")
    
    class Meta:
        table = "t_ai_predictions"
        table_description = "AI预测结果表"


# =====================================================
# 阶段3：特征工程表
# =====================================================

class FeatureDefinition(TimestampMixin, BaseModel):
    """特征定义表"""
    
    # 关联资产类别
    category = fields.ForeignKeyField("models.AssetCategory", related_name="features")
    
    # 基础信息
    name = fields.CharField(max_length=100, description="特征名称")
    code = fields.CharField(max_length=50, description="特征编码")
    
    # 计算配置 (JSON DSL)
    calculation_config = fields.JSONField(description="计算配置")
    
    # 示例: {"source_signal": "current", "function": "avg", "window": "1h"}
    
    # 状态
    is_active = fields.BooleanField(default=True, description="是否激活")
    
    class Meta:
        table = "t_feature_definition"
        table_description = "特征定义表"
        unique_together = [("category_id", "code")]