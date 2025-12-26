"""
元数据管理相关的Pydantic Schema
用于数据模型配置、字段映射等功能的数据验证和序列化
"""

from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field, validator, root_validator
from datetime import datetime


# =====================================================
# DeviceField Schema（扩展）
# =====================================================

class DeviceFieldBase(BaseModel):
    """设备字段基础Schema"""
    device_type_code: str = Field(..., max_length=50, description="设备类型代码")
    field_name: str = Field(..., max_length=100, description="字段名称")
    field_code: str = Field(..., max_length=50, description="字段代码")
    field_type: str = Field(..., max_length=20, description="字段类型")
    field_category: str = Field(default="data_collection", max_length=50, description="字段分类")
    unit: Optional[str] = Field(None, max_length=20, description="单位")
    description: Optional[str] = Field(None, description="字段描述")
    is_required: bool = Field(default=False, description="是否必填")
    default_value: Optional[str] = Field(None, max_length=255, description="默认值")
    validation_rule: Optional[str] = Field(None, description="验证规则")
    sort_order: int = Field(default=0, description="排序顺序")
    is_active: bool = Field(default=True, description="是否激活")
    
    # ⭐ 新增字段：元数据驱动支持
    is_monitoring_key: bool = Field(default=False, description="是否为实时监控关键字段")
    is_alarm_enabled: bool = Field(default=False, description="是否允许配置报警规则")
    is_ai_feature: bool = Field(default=False, description="是否为AI分析特征字段")
    aggregation_method: Optional[str] = Field(None, max_length=20, description="聚合方法")
    data_range: Optional[Dict[str, Any]] = Field(None, description="正常数据范围")
    alarm_threshold: Optional[Dict[str, Any]] = Field(None, description="报警阈值配置")
    display_config: Optional[Dict[str, Any]] = Field(None, description="前端显示配置")
    
    # ⭐ 字段分组功能
    field_group: str = Field(default="default", max_length=50, description="字段分组")
    is_default_visible: bool = Field(default=True, description="是否默认显示（卡片上直接可见）")
    group_order: int = Field(default=0, description="分组内排序顺序")

    @validator('aggregation_method')
    def validate_aggregation_method(cls, v):
        if v and v not in ['avg', 'sum', 'max', 'min', 'count', 'first', 'last']:
            raise ValueError('聚合方法必须是: avg/sum/max/min/count/first/last')
        return v


class DeviceFieldCreate(DeviceFieldBase):
    """创建设备字段"""
    pass


class DeviceFieldUpdate(BaseModel):
    """更新设备字段（所有字段可选）"""
    field_name: Optional[str] = Field(None, max_length=100)
    field_type: Optional[str] = Field(None, max_length=20)
    field_category: Optional[str] = Field(None, max_length=50)
    unit: Optional[str] = Field(None, max_length=20)
    description: Optional[str] = None
    is_required: Optional[bool] = None
    default_value: Optional[str] = Field(None, max_length=255)
    validation_rule: Optional[str] = None
    sort_order: Optional[int] = None
    is_active: Optional[bool] = None
    is_monitoring_key: Optional[bool] = None
    is_alarm_enabled: Optional[bool] = None
    is_ai_feature: Optional[bool] = None
    aggregation_method: Optional[str] = Field(None, max_length=20)
    data_range: Optional[Dict[str, Any]] = None
    alarm_threshold: Optional[Dict[str, Any]] = None
    display_config: Optional[Dict[str, Any]] = None
    field_group: Optional[str] = Field(None, max_length=50)
    is_default_visible: Optional[bool] = None
    group_order: Optional[int] = None


class DeviceFieldResponse(DeviceFieldBase):
    """设备字段响应"""
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# =====================================================
# DeviceDataModel Schema
# =====================================================

class SelectedField(BaseModel):
    """选中的字段配置"""
    field_code: str = Field(..., description="字段代码")
    alias: Optional[str] = Field(None, description="字段别名")
    weight: float = Field(default=1.0, ge=0, le=10, description="权重（0-10）")
    is_required: bool = Field(default=False, description="是否必填")
    transform: Optional[str] = Field(None, description="转换方法：normalize/standardize/log等")

    @validator('alias', always=True)
    def set_default_alias(cls, v, values):
        if v is None and 'field_code' in values:
            return values['field_code']
        return v


class AggregationConfig(BaseModel):
    """聚合配置"""
    time_window: str = Field(..., description="时间窗口：1h/1d/1w等")
    interval: Optional[str] = Field(None, description="时间间隔：5m/1h等")
    methods: List[str] = Field(..., description="聚合方法列表：avg/max/min/sum/count")
    group_by: Optional[List[str]] = Field(default_factory=list, description="分组字段")
    custom_expressions: Optional[Dict[str, str]] = Field(None, description="自定义表达式")
    filters: Optional[Dict[str, Any]] = Field(None, description="过滤条件")

    @validator('methods')
    def validate_methods(cls, v):
        valid_methods = ['avg', 'sum', 'max', 'min', 'count', 'first', 'last']
        for method in v:
            if method not in valid_methods:
                raise ValueError(f'无效的聚合方法: {method}，必须是: {"/".join(valid_methods)}')
        return v

    @validator('time_window', 'interval')
    def validate_time_format(cls, v):
        if v and not any(v.endswith(unit) for unit in ['s', 'm', 'h', 'd', 'w']):
            raise ValueError('时间格式无效，必须以 s/m/h/d/w 结尾 (例如: 1h, 5m)')
        return v


class AIConfig(BaseModel):
    """AI配置"""
    algorithm: str = Field(..., description="算法名称：isolation_forest/one_class_svm等")
    purpose: str = Field(default="anomaly_detection", description="用途：anomaly_detection/prediction/classification")
    features: List[str] = Field(..., min_items=1, description="特征字段列表")
    normalization: str = Field(default="min-max", description="归一化方法：min-max/z-score/robust")
    window_size: int = Field(default=100, ge=10, le=10000, description="滑动窗口大小")
    missing_value_strategy: str = Field(default="interpolate", description="缺失值处理：interpolate/drop/fill_zero/fill_mean")
    outlier_threshold: float = Field(default=3.0, ge=0, description="异常值阈值（标准差倍数）")
    training_params: Optional[Dict[str, Any]] = Field(None, description="训练参数")
    feature_engineering: Optional[Dict[str, str]] = Field(None, description="特征工程配置")

    @validator('normalization')
    def validate_normalization(cls, v):
        if v not in ['min-max', 'z-score', 'robust', 'none']:
            raise ValueError('归一化方法必须是: min-max/z-score/robust/none')
        return v


class DeviceDataModelBase(BaseModel):
    """数据模型基础Schema"""
    model_name: str = Field(..., max_length=100, description="模型名称")
    model_code: str = Field(..., max_length=50, description="模型编码")
    device_type_code: str = Field(..., max_length=50, description="设备类型代码")
    model_type: Literal["realtime", "statistics", "ai_analysis"] = Field(..., description="模型类型")
    selected_fields: List[SelectedField] = Field(..., min_items=1, description="选中的字段列表")
    aggregation_config: Optional[AggregationConfig] = Field(None, description="聚合配置（statistics类型）")
    ai_config: Optional[AIConfig] = Field(None, description="AI配置（ai_analysis类型）")
    version: str = Field(default="1.0", max_length=20, description="模型版本")
    is_active: bool = Field(default=True, description="是否激活")
    is_default: bool = Field(default=False, description="是否为默认模型")
    description: Optional[str] = Field(None, description="模型说明")

    @root_validator(pre=True)
    def cleanup_configs(cls, values):
        """清理不匹配模型类型的配置"""
        # 如果是ORM对象，直接返回（避免 AttributeError: 'DeviceDataModel' object has no attribute 'get'）
        if not isinstance(values, dict):
            return values

        model_type = values.get('model_type')
        # 如果不是统计类型，清除聚合配置
        if model_type != 'statistics':
            values['aggregation_config'] = None
        # 如果不是AI类型，清除AI配置
        if model_type != 'ai_analysis':
            values['ai_config'] = None
        return values

    @validator('aggregation_config')
    def validate_aggregation_config(cls, v, values):
        if values.get('model_type') == 'statistics' and v is None:
            raise ValueError('统计分析类型的模型必须提供聚合配置')
        return v

    @validator('ai_config')
    def validate_ai_config(cls, v, values):
        if values.get('model_type') == 'ai_analysis' and v is None:
            raise ValueError('AI分析类型的模型必须提供AI配置')
        return v


class DeviceDataModelCreate(DeviceDataModelBase):
    """创建数据模型"""
    created_by: Optional[int] = Field(None, description="创建人ID")


class DeviceDataModelUpdate(BaseModel):
    """更新数据模型（所有字段可选）"""
    model_name: Optional[str] = Field(None, max_length=100)
    selected_fields: Optional[List[SelectedField]] = Field(None, min_items=1)
    aggregation_config: Optional[AggregationConfig] = None
    ai_config: Optional[AIConfig] = None
    version: Optional[str] = Field(None, max_length=20)
    is_active: Optional[bool] = None
    is_default: Optional[bool] = None
    description: Optional[str] = None
    updated_by: Optional[int] = Field(None, description="更新人ID")


class DeviceDataModelResponse(DeviceDataModelBase):
    """数据模型响应"""
    id: int
    created_by: Optional[int]
    updated_by: Optional[int]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# =====================================================
# DeviceFieldMapping Schema
# =====================================================

class TransformRule(BaseModel):
    """数据转换规则"""
    type: str = Field(..., description="转换类型：expression/unit_conversion/range_limit/composite等")
    expression: Optional[str] = Field(None, description="表达式（type=expression时）")
    from_unit: Optional[str] = Field(None, alias="from", description="源单位（type=unit_conversion时）")
    to_unit: Optional[str] = Field(None, alias="to", description="目标单位（type=unit_conversion时）")
    factor: Optional[float] = Field(None, description="转换因子")
    min: Optional[float] = Field(None, description="最小值（type=range_limit时）")
    max: Optional[float] = Field(None, description="最大值（type=range_limit时）")
    conditions: Optional[List[Dict[str, Any]]] = Field(None, description="条件列表")
    rules: Optional[List[Dict[str, Any]]] = Field(None, description="规则列表（type=composite时）")

    class Config:
        populate_by_name = True


class DeviceFieldMappingBase(BaseModel):
    """字段映射基础Schema"""
    device_type_code: str = Field(..., max_length=50, description="设备类型代码")
    tdengine_database: str = Field(..., max_length=100, description="TDengine数据库名")
    tdengine_stable: str = Field(..., max_length=100, description="TDengine超级表名")
    tdengine_column: str = Field(..., max_length=100, description="TDengine列名")
    device_field_id: int = Field(..., description="关联的字段定义ID")
    transform_rule: Optional[TransformRule] = Field(None, description="数据转换规则")
    is_tag: bool = Field(default=False, description="是否为TAG列")
    is_active: bool = Field(default=True, description="是否激活")


class DeviceFieldMappingCreate(DeviceFieldMappingBase):
    """创建字段映射"""
    pass


class DeviceFieldMappingUpdate(BaseModel):
    """更新字段映射（所有字段可选）"""
    tdengine_database: Optional[str] = Field(None, max_length=100)
    tdengine_stable: Optional[str] = Field(None, max_length=100)
    tdengine_column: Optional[str] = Field(None, max_length=100)
    device_field_id: Optional[int] = None
    transform_rule: Optional[TransformRule] = None
    is_tag: Optional[bool] = None
    is_active: Optional[bool] = None


class DeviceFieldMappingResponse(DeviceFieldMappingBase):
    """字段映射响应"""
    id: int
    created_at: datetime
    updated_at: datetime
    device_field: Optional[DeviceFieldResponse] = None

    class Config:
        from_attributes = True


# =====================================================
# ModelExecutionLog Schema
# =====================================================

class ModelExecutionLogBase(BaseModel):
    """模型执行日志基础Schema"""
    model_id: int = Field(..., description="数据模型ID")
    execution_type: Literal["query", "feature_extract", "training", "validation"] = Field(..., description="执行类型")
    input_params: Optional[Dict[str, Any]] = Field(None, description="输入参数")
    status: Literal["success", "failed", "timeout", "cancelled"] = Field(..., description="执行状态")
    result_summary: Optional[Dict[str, Any]] = Field(None, description="结果摘要")
    error_message: Optional[str] = Field(None, description="错误信息")
    execution_time_ms: Optional[int] = Field(None, ge=0, description="执行时间（毫秒）")
    data_volume: Optional[int] = Field(None, ge=0, description="数据量（行数）")
    memory_usage_mb: Optional[int] = Field(None, ge=0, description="内存使用（MB）")
    generated_sql: Optional[str] = Field(None, description="生成的SQL")
    executed_by: Optional[int] = Field(None, description="执行人ID")


class ModelExecutionLogCreate(ModelExecutionLogBase):
    """创建执行日志"""
    pass


class ModelExecutionLogResponse(ModelExecutionLogBase):
    """执行日志响应"""
    id: int
    executed_at: datetime

    class Config:
        from_attributes = True


# =====================================================
# 查询和统计Schema
# =====================================================

class ModelListQuery(BaseModel):
    """模型列表查询参数"""
    device_type_code: Optional[str] = Field(None, description="设备类型代码")
    model_type: Optional[Literal["realtime", "statistics", "ai_analysis"]] = Field(None, description="模型类型")
    is_active: Optional[bool] = Field(None, description="是否激活")
    search: Optional[str] = Field(None, description="搜索关键词（模型名称或编码）")
    page: int = Field(default=1, ge=1, description="页码")
    page_size: int = Field(default=10, ge=1, le=100, description="每页数量")


class FieldMappingQuery(BaseModel):
    """字段映射查询参数"""
    device_type_code: Optional[str] = Field(None, description="设备类型代码")
    tdengine_stable: Optional[str] = Field(None, description="TDengine超级表名")
    is_tag: Optional[bool] = Field(None, description="是否为TAG列")
    is_active: Optional[bool] = Field(None, description="是否激活")
    page: int = Field(default=1, ge=1, description="页码")
    page_size: int = Field(default=10, ge=1, le=100, description="每页数量")


class ExecutionLogQuery(BaseModel):
    """执行日志查询参数"""
    model_id: Optional[int] = Field(None, description="模型ID")
    execution_type: Optional[Literal["query", "feature_extract", "training", "validation"]] = Field(None, description="执行类型")
    status: Optional[Literal["success", "failed", "timeout", "cancelled"]] = Field(None, description="执行状态")
    start_time: Optional[datetime] = Field(None, description="开始时间")
    end_time: Optional[datetime] = Field(None, description="结束时间")
    page: int = Field(default=1, ge=1, description="页码")
    page_size: int = Field(default=10, ge=1, le=100, description="每页数量")


class ModelStatistics(BaseModel):
    """模型统计信息"""
    total_models: int = Field(..., description="模型总数")
    active_models: int = Field(..., description="激活的模型数")
    realtime_models: int = Field(..., description="实时监控模型数")
    statistics_models: int = Field(..., description="统计分析模型数")
    ai_models: int = Field(..., description="AI模型数")
    total_executions: int = Field(..., description="总执行次数")
    success_rate: float = Field(..., ge=0, le=100, description="成功率（%）")
    avg_execution_time_ms: float = Field(..., ge=0, description="平均执行时间（毫秒）")

