"""
统一API v4响应格式

定义统一的响应格式、错误码和分页规范。

Requirements: 6.2, 6.3, 6.4
"""
from typing import TypeVar, Generic, Optional, Any, List, Dict
from pydantic import BaseModel, Field
from datetime import datetime, date
from enum import IntEnum


# =====================================================
# 错误码定义
# =====================================================

class ErrorCodes(IntEnum):
    """统一错误码定义"""
    # 成功
    SUCCESS = 0
    
    # 客户端错误 (4xx)
    BAD_REQUEST = 400
    UNAUTHORIZED = 401
    FORBIDDEN = 403
    NOT_FOUND = 404
    METHOD_NOT_ALLOWED = 405
    CONFLICT = 409
    VALIDATION_ERROR = 422
    TOO_MANY_REQUESTS = 429
    
    # 服务端错误 (5xx)
    INTERNAL_ERROR = 500
    NOT_IMPLEMENTED = 501
    SERVICE_UNAVAILABLE = 503
    
    # 业务错误 (1xxx)
    ASSET_NOT_FOUND = 1001
    CATEGORY_NOT_FOUND = 1002
    SIGNAL_NOT_FOUND = 1003
    MODEL_NOT_FOUND = 1004
    DUPLICATE_CODE = 1010
    INVALID_STATUS = 1011
    RESOURCE_LOCKED = 1012
    DEPENDENCY_EXISTS = 1013
    
    # 数据库错误 (2xxx)
    DB_CONNECTION_ERROR = 2001
    DB_QUERY_ERROR = 2002
    DB_TRANSACTION_ERROR = 2003
    
    # 外部服务错误 (3xxx)
    TDENGINE_ERROR = 3001
    STORAGE_ERROR = 3002
    AI_ENGINE_ERROR = 3003


# =====================================================
# 分页元数据
# =====================================================

class PageMeta(BaseModel):
    """分页元数据"""
    page: int = Field(1, ge=1, description="当前页码")
    page_size: int = Field(20, ge=1, le=100, description="每页数量")
    total: int = Field(0, ge=0, description="总记录数")
    total_pages: int = Field(0, ge=0, description="总页数")
    timestamp: datetime = Field(default_factory=datetime.now, description="响应时间戳")
    
    def __init__(self, **data):
        # 自动计算总页数
        if "total_pages" not in data and data.get("total", 0) > 0 and data.get("page_size", 20) > 0:
            data["total_pages"] = (data["total"] + data["page_size"] - 1) // data["page_size"]
        if "timestamp" not in data:
            data["timestamp"] = datetime.now()
        super().__init__(**data)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


# =====================================================
# 统一响应格式
# =====================================================

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    """
    统一API响应格式
    
    所有v4 API端点都应使用此格式返回数据。
    
    Attributes:
        code: 响应码，0表示成功，其他表示错误
        message: 响应消息
        data: 响应数据
        meta: 分页元数据（仅列表响应）
    """
    code: int = Field(ErrorCodes.SUCCESS, description="响应码，0表示成功")
    message: str = Field("success", description="响应消息")
    data: Optional[T] = Field(None, description="响应数据")
    meta: Optional[PageMeta] = Field(None, description="分页元数据")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            date: lambda v: v.isoformat()
        }


class ErrorDetail(BaseModel):
    """错误详情"""
    field: Optional[str] = Field(None, description="错误字段")
    message: str = Field(..., description="错误消息")
    code: Optional[str] = Field(None, description="错误代码")


class ErrorResponse(BaseModel):
    """
    错误响应格式
    
    用于返回错误信息。
    """
    code: int = Field(..., description="错误码")
    message: str = Field(..., description="错误消息")
    details: Optional[List[ErrorDetail]] = Field(None, description="错误详情列表")
    timestamp: datetime = Field(default_factory=datetime.now, description="错误发生时间")
    path: Optional[str] = Field(None, description="请求路径")
    request_id: Optional[str] = Field(None, description="请求ID")
    
    def __init__(self, **data):
        if "timestamp" not in data:
            data["timestamp"] = datetime.now()
        super().__init__(**data)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


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
    category_id: int = Field(..., description="资产类别ID")
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
# AI模型相关模型
# =====================================================

class AIModelCreate(BaseModel):
    """AI模型创建模型"""
    code: str = Field(..., min_length=1, max_length=50, description="模型编码")
    name: str = Field(..., min_length=1, max_length=100, description="模型名称")
    description: Optional[str] = Field(None, max_length=500, description="模型描述")
    model_type: str = Field(..., description="模型类型: classification/regression/anomaly_detection/forecasting")
    category_id: Optional[int] = Field(None, description="关联资产类别ID")
    algorithm: Optional[str] = Field(None, max_length=50, description="算法名称")
    framework: Optional[str] = Field(None, max_length=50, description="框架: sklearn/pytorch/tensorflow/onnx")
    input_features: Optional[List[str]] = Field(None, description="输入特征列表")
    output_features: Optional[List[str]] = Field(None, description="输出特征列表")
    hyperparameters: Optional[Dict[str, Any]] = Field(None, description="超参数配置")
    training_config: Optional[Dict[str, Any]] = Field(None, description="训练配置")


class AIModelUpdate(BaseModel):
    """AI模型更新模型"""
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="模型名称")
    description: Optional[str] = Field(None, max_length=500, description="模型描述")
    category_id: Optional[int] = Field(None, description="关联资产类别ID")
    algorithm: Optional[str] = Field(None, max_length=50, description="算法名称")
    input_features: Optional[List[str]] = Field(None, description="输入特征列表")
    output_features: Optional[List[str]] = Field(None, description="输出特征列表")
    hyperparameters: Optional[Dict[str, Any]] = Field(None, description="超参数配置")
    training_config: Optional[Dict[str, Any]] = Field(None, description="训练配置")
    is_active: Optional[bool] = Field(None, description="是否激活")


class AIModelResponse(BaseModel):
    """AI模型响应模型"""
    id: int
    code: str
    name: str
    description: Optional[str] = None
    model_type: str
    category_id: Optional[int] = None
    algorithm: Optional[str] = None
    framework: Optional[str] = None
    input_features: Optional[List[str]] = None
    output_features: Optional[List[str]] = None
    hyperparameters: Optional[Dict[str, Any]] = None
    training_config: Optional[Dict[str, Any]] = None
    current_version: Optional[str] = None
    is_active: bool
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# =====================================================
# 系统相关模型
# =====================================================

class HealthCheckResponse(BaseModel):
    """健康检查响应"""
    status: str = Field(..., description="服务状态: healthy/unhealthy/degraded")
    version: str = Field(..., description="API版本")
    uptime: float = Field(..., description="运行时间（秒）")
    timestamp: datetime = Field(default_factory=datetime.now, description="检查时间")
    services: Dict[str, str] = Field(default_factory=dict, description="依赖服务状态")


class SystemConfigResponse(BaseModel):
    """系统配置响应"""
    api_version: str = Field(..., description="API版本")
    environment: str = Field(..., description="运行环境")
    features: Dict[str, bool] = Field(default_factory=dict, description="功能开关")
    limits: Dict[str, int] = Field(default_factory=dict, description="限制配置")


# =====================================================
# 辅助函数
# =====================================================

def create_response(
    data: Any = None,
    message: str = "success",
    code: int = ErrorCodes.SUCCESS,
    meta: Optional[PageMeta] = None
) -> Dict[str, Any]:
    """创建统一响应"""
    response = {
        "code": code,
        "message": message,
        "data": data
    }
    if meta:
        response["meta"] = meta.model_dump()
    return response


def create_error_response(
    code: int,
    message: str,
    details: Optional[List[Dict[str, Any]]] = None,
    path: Optional[str] = None
) -> Dict[str, Any]:
    """创建错误响应"""
    return {
        "code": code,
        "message": message,
        "details": details,
        "timestamp": datetime.now().isoformat(),
        "path": path
    }


def create_paginated_response(
    data: List[Any],
    total: int,
    page: int = 1,
    page_size: int = 20,
    message: str = "success"
) -> Dict[str, Any]:
    """创建分页响应"""
    meta = PageMeta(
        page=page,
        page_size=page_size,
        total=total
    )
    return create_response(data=data, message=message, meta=meta)
