"""
API v3 Pydantic模型定义
工业AI数据平台 - 请求和响应模型
"""
from typing import Optional, Dict, Any, List
from datetime import datetime, date
from pydantic import BaseModel, Field


# =====================================================
# 资产类别相关模型
# =====================================================

class AssetCategoryCreate(BaseModel):
    """资产类别创建模型"""
    code: str = Field(..., min_length=1, max_length=50, description="类别编码")
    name: str = Field(..., min_length=1, max_length=100, description="类别名称")
    description: Optional[str] = Field(None, max_length=500, description="描述")
    industry: Optional[str] = Field(None, max_length=50, description="所属行业")
    icon: Optional[str] = Field(None, max_length=100, description="图标")
    tdengine_database: Optional[str] = Field("devicemonitor", max_length=100, description="TDengine数据库名")
    config: Optional[Dict[str, Any]] = Field(None, description="扩展配置")


class AssetCategoryUpdate(BaseModel):
    """资产类别更新模型"""
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="类别名称")
    description: Optional[str] = Field(None, max_length=500, description="描述")
    industry: Optional[str] = Field(None, max_length=50, description="所属行业")
    icon: Optional[str] = Field(None, max_length=100, description="图标")
    is_active: Optional[bool] = Field(None, description="是否激活")
    config: Optional[Dict[str, Any]] = Field(None, description="扩展配置")


class AssetCategoryResponse(BaseModel):
    """资产类别响应模型"""
    id: int
    code: str
    name: str
    description: Optional[str] = None
    industry: Optional[str] = None
    icon: Optional[str] = None
    color: Optional[str] = None
    tdengine_database: str
    tdengine_stable_prefix: str
    is_active: bool
    asset_count: int
    config: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# =====================================================
# 信号定义相关模型
# =====================================================

class SignalDefinitionCreate(BaseModel):
    """信号定义创建模型"""
    code: str = Field(..., min_length=1, max_length=50, description="信号编码")
    name: str = Field(..., min_length=1, max_length=100, description="信号名称")
    data_type: str = Field(..., description="数据类型: float/int/bool/string/double/bigint")
    unit: Optional[str] = Field(None, max_length=20, description="单位")
    is_stored: bool = Field(True, description="是否存储到时序数据库")
    is_realtime: bool = Field(True, description="是否实时监控")
    is_feature: bool = Field(False, description="是否用于特征工程")
    is_alarm_enabled: bool = Field(False, description="是否启用报警")
    value_range: Optional[Dict[str, Any]] = Field(None, description='值范围: {"min": 0, "max": 100}')
    validation_rules: Optional[Dict[str, Any]] = Field(None, description="验证规则")
    alarm_threshold: Optional[Dict[str, Any]] = Field(None, description='报警阈值: {"warning": 80, "critical": 90}')
    aggregation_method: Optional[str] = Field(None, max_length=20, description="聚合方法: avg/sum/max/min/count")
    display_config: Optional[Dict[str, Any]] = Field(None, description="前端显示配置")
    sort_order: int = Field(0, description="排序")
    field_group: str = Field("default", max_length=50, description="字段分组")
    is_default_visible: bool = Field(True, description="是否默认显示")


class SignalDefinitionUpdate(BaseModel):
    """信号定义更新模型"""
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="信号名称")
    unit: Optional[str] = Field(None, max_length=20, description="单位")
    is_stored: Optional[bool] = Field(None, description="是否存储到时序数据库")
    is_realtime: Optional[bool] = Field(None, description="是否实时监控")
    is_feature: Optional[bool] = Field(None, description="是否用于特征工程")
    is_alarm_enabled: Optional[bool] = Field(None, description="是否启用报警")
    value_range: Optional[Dict[str, Any]] = Field(None, description="值范围")
    validation_rules: Optional[Dict[str, Any]] = Field(None, description="验证规则")
    alarm_threshold: Optional[Dict[str, Any]] = Field(None, description="报警阈值")
    aggregation_method: Optional[str] = Field(None, max_length=20, description="聚合方法")
    display_config: Optional[Dict[str, Any]] = Field(None, description="前端显示配置")
    sort_order: Optional[int] = Field(None, description="排序")
    field_group: Optional[str] = Field(None, max_length=50, description="字段分组")
    is_default_visible: Optional[bool] = Field(None, description="是否默认显示")
    is_active: Optional[bool] = Field(None, description="是否激活")


class SignalDefinitionResponse(BaseModel):
    """信号定义响应模型"""
    id: int
    category_id: int
    code: str
    name: str
    data_type: str
    unit: Optional[str] = None
    is_stored: bool
    is_realtime: bool
    is_feature: bool
    is_alarm_enabled: bool
    value_range: Optional[Dict[str, Any]] = None
    validation_rules: Optional[Dict[str, Any]] = None
    alarm_threshold: Optional[Dict[str, Any]] = None
    aggregation_method: Optional[str] = None
    display_config: Optional[Dict[str, Any]] = None
    sort_order: int
    field_group: str
    is_default_visible: bool
    is_active: bool
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# =====================================================
# 资产相关模型
# =====================================================

class AssetCreate(BaseModel):
    """资产创建模型"""
    code: str = Field(..., min_length=1, max_length=100, description="资产编号")
    name: str = Field(..., min_length=1, max_length=100, description="资产名称")
    category_id: int = Field(..., description="资产类别ID")
    location: Optional[str] = Field(None, max_length=255, description="位置")
    attributes: Optional[Dict[str, Any]] = Field(default_factory=dict, description="静态属性")
    manufacturer: Optional[str] = Field(None, max_length=100, description="制造商")
    model: Optional[str] = Field(None, max_length=50, description="型号")
    serial_number: Optional[str] = Field(None, max_length=100, description="序列号")
    install_date: Optional[date] = Field(None, description="安装日期")
    department: Optional[str] = Field(None, max_length=100, description="所属部门")
    team: Optional[str] = Field(None, max_length=100, description="所属班组")
    ip_address: Optional[str] = Field(None, max_length=50, description="IP地址")
    mac_address: Optional[str] = Field(None, max_length=50, description="MAC地址")


class AssetUpdate(BaseModel):
    """资产更新模型"""
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="资产名称")
    location: Optional[str] = Field(None, max_length=255, description="位置")
    status: Optional[str] = Field(None, description="状态: online/offline/error/maintenance")
    attributes: Optional[Dict[str, Any]] = Field(None, description="静态属性")
    manufacturer: Optional[str] = Field(None, max_length=100, description="制造商")
    model: Optional[str] = Field(None, max_length=50, description="型号")
    serial_number: Optional[str] = Field(None, max_length=100, description="序列号")
    install_date: Optional[date] = Field(None, description="安装日期")
    department: Optional[str] = Field(None, max_length=100, description="所属部门")
    team: Optional[str] = Field(None, max_length=100, description="所属班组")
    ip_address: Optional[str] = Field(None, max_length=50, description="IP地址")
    mac_address: Optional[str] = Field(None, max_length=50, description="MAC地址")
    is_locked: Optional[bool] = Field(None, description="是否锁定")
    is_active: Optional[bool] = Field(None, description="是否激活")


class AssetResponse(BaseModel):
    """资产响应模型"""
    id: int
    code: str
    name: str
    category_id: int
    category: Optional[AssetCategoryResponse] = None
    location: Optional[str] = None
    status: str
    attributes: Dict[str, Any]
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    serial_number: Optional[str] = None
    install_date: Optional[date] = None
    department: Optional[str] = None
    team: Optional[str] = None
    ip_address: Optional[str] = None
    mac_address: Optional[str] = None
    is_locked: bool
    is_active: bool
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# =====================================================
# AI预测相关模型
# =====================================================

class PredictionRequest(BaseModel):
    """预测请求模型"""
    model_id: int = Field(..., description="模型ID")
    asset_id: int = Field(..., description="资产ID")
    input_data: Dict[str, Any] = Field(..., description="输入数据")


class PredictionResponse(BaseModel):
    """预测响应模型"""
    id: int
    model_version_id: int
    asset_id: int
    input_data: Dict[str, Any]
    predicted_value: float
    confidence: Optional[float] = None
    prediction_details: Optional[Dict[str, Any]] = None
    prediction_time: datetime
    target_time: datetime
    is_anomaly: Optional[bool] = None
    anomaly_score: Optional[float] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# =====================================================
# 特征工程相关模型
# =====================================================

class FeatureConfig(BaseModel):
    """特征配置模型"""
    name: str = Field(..., description="特征名称")
    source_signal: str = Field(..., description="源信号")
    function: str = Field(..., description="聚合函数: avg/sum/max/min/count/stddev/percentile")
    window: str = Field(..., description="时间窗口: 1h/30m/1d等")
    slide_interval: Optional[str] = Field(None, description="滑动间隔")
    filters: Optional[Dict[str, Any]] = Field(None, description="过滤条件")
    group_by: Optional[List[str]] = Field(None, description="分组字段")


class FeatureViewCreate(BaseModel):
    """特征视图创建模型"""
    name: str = Field(..., min_length=1, max_length=100, description="视图名称")
    code: str = Field(..., min_length=1, max_length=50, description="视图编码")
    category_id: int = Field(..., description="资产类别ID")
    description: Optional[str] = Field(None, max_length=500, description="视图描述")
    feature_configs: List[FeatureConfig] = Field(..., description="特征配置列表")


class FeatureViewUpdate(BaseModel):
    """特征视图更新模型"""
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="视图名称")
    description: Optional[str] = Field(None, max_length=500, description="视图描述")
    feature_configs: Optional[List[FeatureConfig]] = Field(None, description="特征配置列表")
    is_active: Optional[bool] = Field(None, description="是否激活")


class FeatureViewResponse(BaseModel):
    """特征视图响应模型"""
    id: int
    category_id: int
    name: str
    code: str
    description: Optional[str] = None
    feature_codes: List[str]
    stream_name: Optional[str] = None
    target_stable: Optional[str] = None
    status: str
    is_active: bool
    last_quality_check: Optional[datetime] = None
    quality_score: Optional[float] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
