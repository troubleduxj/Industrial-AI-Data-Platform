#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI监控模块数据模式
包含趋势预测、模型管理、数据标注、健康评分等功能的数据模式
"""

from datetime import datetime
from typing import Optional, Dict, Any, List, Union
from enum import Enum

from pydantic import BaseModel, Field, validator

from app.schemas.base import APIResponse, PaginatedResponse


# =====================================================
# 枚举定义
# =====================================================

class PredictionStatus(str, Enum):
    """预测状态枚举"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ModelStatus(str, Enum):
    """模型状态枚举"""
    DRAFT = "draft"
    TRAINING = "training"
    TRAINED = "trained"
    DEPLOYED = "deployed"
    ARCHIVED = "archived"
    FAILED = "failed"
    ERROR = "error"


class AnnotationStatus(str, Enum):
    """标注状态枚举"""
    CREATED = "created"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    REVIEWED = "reviewed"
    ARCHIVED = "archived"


class HealthScoreStatus(str, Enum):
    """健康评分状态枚举"""
    CALCULATING = "calculating"
    COMPLETED = "completed"
    FAILED = "failed"


class AnalysisStatus(str, Enum):
    """分析状态枚举"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


# =====================================================
# 趋势预测相关模式
# =====================================================

# ----- 详细预测结果结构 -----

class PredictionPoint(BaseModel):
    """单个预测点"""
    time: datetime = Field(..., description="预测时间点")
    value: float = Field(..., description="预测值")
    confidence: float = Field(..., description="置信度 (0-1)")
    lower_bound: Optional[float] = Field(None, description="置信区间下界")
    upper_bound: Optional[float] = Field(None, description="置信区间上界")


class PredictionMetadata(BaseModel):
    """预测元数据"""
    device_code: str = Field(..., description="设备代码")
    device_name: Optional[str] = Field(None, description="设备名称")
    metric_name: str = Field(..., description="指标名称")
    prediction_method: str = Field(..., description="预测方法")
    total_points: int = Field(..., description="预测点数量")
    avg_confidence: float = Field(..., description="平均置信度")
    data_period_start: datetime = Field(..., description="数据周期开始时间")
    data_period_end: datetime = Field(..., description="数据周期结束时间")


class ActualValue(BaseModel):
    """实际值（用于验证）"""
    time: datetime = Field(..., description="时间点")
    value: float = Field(..., description="实际值")
    error: Optional[float] = Field(None, description="预测误差")


class PredictionResultData(BaseModel):
    """预测结果数据结构"""
    predictions: List[PredictionPoint] = Field(..., description="预测点列表")
    metadata: PredictionMetadata = Field(..., description="预测元数据")
    actual_values: Optional[List[ActualValue]] = Field(default_factory=list, description="实际值列表（用于验证）")


# ----- 创建和更新请求 -----

class PredictionCreate(BaseModel):
    """创建预测请求模式"""
    prediction_name: str = Field(..., description="预测名称", max_length=200)
    description: Optional[str] = Field(None, description="预测描述")
    target_variable: str = Field(..., description="目标变量", max_length=100)
    prediction_horizon: int = Field(..., description="预测时间范围(小时)", ge=1, le=8760)
    model_type: str = Field(..., description="模型类型", max_length=50)
    parameters: Dict[str, Any] = Field(default_factory=dict, description="预测参数")
    data_source: str = Field(..., description="数据源", max_length=100)
    data_filters: Dict[str, Any] = Field(default_factory=dict, description="数据过滤条件")


class BatchPredictionCreate(BaseModel):
    """批量创建预测请求模式"""
    device_codes: List[str] = Field(..., description="设备代码列表", min_items=1)
    metric_name: str = Field(..., description="指标名称（如temperature）")
    prediction_horizon: int = Field(24, description="预测时间范围（小时）", ge=1, le=8760)
    model_type: str = Field("ARIMA", description="预测模型类型（ARIMA/MA/ES/LR）")
    parameters: Optional[Dict[str, Any]] = Field(default_factory=dict, description="预测参数")


class PredictionUpdate(BaseModel):
    """更新预测请求模式"""
    prediction_name: Optional[str] = Field(None, description="预测名称", max_length=200)
    description: Optional[str] = Field(None, description="预测描述")
    target_variable: Optional[str] = Field(None, description="目标变量", max_length=100)
    prediction_horizon: Optional[int] = Field(None, description="预测时间范围(小时)", ge=1, le=8760)
    model_type: Optional[str] = Field(None, description="模型类型", max_length=50)
    parameters: Optional[Dict[str, Any]] = Field(None, description="预测参数")
    data_source: Optional[str] = Field(None, description="数据源", max_length=100)
    data_filters: Optional[Dict[str, Any]] = Field(None, description="数据过滤条件")


class PredictionResponse(BaseModel):
    """预测响应模式（增强版）"""
    id: int = Field(..., description="预测ID")
    prediction_name: str = Field(..., description="预测名称")
    description: Optional[str] = Field(None, description="预测描述")
    target_variable: str = Field(..., description="目标变量")
    prediction_horizon: int = Field(..., description="预测时间范围(小时)")
    model_type: str = Field(..., description="模型类型")
    parameters: Dict[str, Any] = Field(..., description="预测参数")
    data_source: str = Field(..., description="数据源")
    data_filters: Dict[str, Any] = Field(..., description="数据过滤条件")
    status: PredictionStatus = Field(..., description="预测状态")
    progress: int = Field(..., description="执行进度(0-100)")
    result_data: Optional[Union[Dict[str, Any], PredictionResultData]] = Field(None, description="预测结果数据")
    accuracy_score: Optional[float] = Field(None, description="准确率分数")
    confidence_interval: Optional[Dict[str, Any]] = Field(None, description="置信区间")
    started_at: Optional[datetime] = Field(None, description="开始时间")
    completed_at: Optional[datetime] = Field(None, description="完成时间")
    error_message: Optional[str] = Field(None, description="错误信息")
    export_formats: List[str] = Field(default_factory=list, description="支持的导出格式")
    shared_with: List[int] = Field(default_factory=list, description="分享给的用户列表")
    is_public: bool = Field(False, description="是否公开")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    created_by: Optional[int] = Field(None, description="创建人ID")
    updated_by: Optional[int] = Field(None, description="更新人ID")
    
    # 从data_filters提取的字段（便于前端使用）
    device_code: Optional[str] = Field(None, description="设备代码（从data_filters提取）")
    device_name: Optional[str] = Field(None, description="设备名称（从data_filters提取）")
    metric_name: Optional[str] = Field(None, description="指标名称（从data_filters提取）")
    
    class Config:
        from_attributes = True
    
    @classmethod
    def from_orm_with_filters(cls, obj):
        """从ORM对象创建，并自动提取data_filters中的常用字段"""
        # 转换基础字段
        data = {
            "id": obj.id,
            "prediction_name": obj.prediction_name,
            "description": obj.description,
            "target_variable": obj.target_variable,
            "prediction_horizon": obj.prediction_horizon,
            "model_type": obj.model_type,
            "parameters": obj.parameters,
            "data_source": obj.data_source,
            "data_filters": obj.data_filters,
            "status": obj.status,
            "progress": obj.progress,
            "result_data": obj.result_data,
            "accuracy_score": obj.accuracy_score,
            "confidence_interval": obj.confidence_interval,
            "started_at": obj.started_at,
            "completed_at": obj.completed_at,
            "error_message": obj.error_message,
            "export_formats": obj.export_formats,
            "shared_with": obj.shared_with,
            "is_public": obj.is_public,
            "created_at": obj.created_at,
            "updated_at": obj.updated_at,
            "created_by": obj.created_by,
            "updated_by": obj.updated_by,
        }
        
        # 从data_filters提取常用字段
        if obj.data_filters:
            data["device_code"] = obj.data_filters.get("device_code")
            data["device_name"] = obj.data_filters.get("device_name")
            data["metric_name"] = obj.data_filters.get("metric_name")
        
        return cls(**data)


class BatchPredictionResponse(BaseModel):
    """批量预测响应模式"""
    predictions: List[PredictionResponse] = Field(..., description="预测结果列表")
    total: int = Field(..., description="总数")
    successful: int = Field(..., description="成功数量")
    failed: int = Field(0, description="失败数量")
    failed_devices: List[str] = Field(default_factory=list, description="失败的设备列表")


class PredictionHistoryQuery(BaseModel):
    """预测历史查询参数"""
    device_code: str = Field(..., description="设备代码")
    metric_name: Optional[str] = Field(None, description="指标名称")
    status: Optional[str] = Field(None, description="状态筛选")
    page: int = Field(1, ge=1, description="页码")
    page_size: int = Field(20, ge=1, le=100, description="每页大小")


class PredictionShareRequest(BaseModel):
    """预测分享请求模式"""
    user_ids: List[int] = Field(..., description="分享给的用户ID列表")
    is_public: bool = Field(False, description="是否公开")
    message: Optional[str] = Field(None, description="分享消息")


# =====================================================
# 模型管理相关模式
# =====================================================

class ModelCreate(BaseModel):
    """创建模型请求模式"""
    model_name: str = Field(..., description="模型名称", max_length=200)
    model_version: str = Field(..., description="模型版本", max_length=50)
    description: Optional[str] = Field(None, description="模型描述")
    model_type: str = Field(..., description="模型类型", max_length=50)
    algorithm: str = Field(..., description="算法名称", max_length=100)
    framework: str = Field(..., description="框架名称", max_length=50)
    training_dataset: Optional[str] = Field(None, description="训练数据集", max_length=2000)
    training_parameters: Dict[str, Any] = Field(default_factory=dict, description="训练参数")


class ModelUpdate(BaseModel):
    """更新模型请求模式"""
    model_name: Optional[str] = Field(None, description="模型名称", max_length=200)
    model_version: Optional[str] = Field(None, description="模型版本", max_length=50)
    description: Optional[str] = Field(None, description="模型描述")
    model_type: Optional[str] = Field(None, description="模型类型", max_length=50)
    algorithm: Optional[str] = Field(None, description="算法名称", max_length=100)
    framework: Optional[str] = Field(None, description="框架名称", max_length=50)
    training_dataset: Optional[str] = Field(None, description="训练数据集", max_length=2000)
    training_parameters: Optional[Dict[str, Any]] = Field(None, description="训练参数")
    deployment_config: Optional[Dict[str, Any]] = Field(None, description="部署配置")


class ModelResponse(BaseModel):
    """模型响应模式"""
    id: int = Field(..., description="模型ID")
    model_name: str = Field(..., description="模型名称")
    model_version: str = Field(..., description="模型版本")
    description: Optional[str] = Field(None, description="模型描述")
    model_type: str = Field(..., description="模型类型")
    algorithm: Optional[str] = Field(None, description="算法名称")
    framework: Optional[str] = Field(None, description="框架名称")
    model_file_path: Optional[str] = Field(None, description="模型文件路径")
    model_file_size: Optional[int] = Field(None, description="模型文件大小(字节)")
    model_file_hash: Optional[str] = Field(None, description="模型文件哈希")
    training_dataset: Optional[Any] = Field(None, description="训练数据集")
    training_parameters: Optional[Dict[str, Any]] = Field(None, description="训练参数")
    training_metrics: Optional[Dict[str, Any]] = Field(None, description="训练指标")
    status: ModelStatus = Field(..., description="模型状态")
    progress: Optional[float] = Field(0.0, description="训练进度(0-100)")
    accuracy: Optional[float] = Field(None, description="准确率")
    precision: Optional[float] = Field(None, description="精确率")
    recall: Optional[float] = Field(None, description="召回率")
    f1_score: Optional[float] = Field(None, description="F1分数")
    deployment_config: Optional[Dict[str, Any]] = Field(None, description="部署配置")
    deployed_at: Optional[datetime] = Field(None, description="部署时间")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    created_by: Optional[int] = Field(None, description="创建人ID")
    updated_by: Optional[int] = Field(None, description="更新人ID")


class ModelTrainRequest(BaseModel):
    """模型训练请求模式"""
    training_dataset: str = Field(..., description="训练数据集")
    training_parameters: Dict[str, Any] = Field(..., description="训练参数")
    validation_split: float = Field(0.2, description="验证集比例", ge=0.1, le=0.5)


class ModelMetricsResponse(BaseModel):
    """模型指标响应模式"""
    accuracy: Optional[float] = Field(None, description="准确率")
    precision: Optional[float] = Field(None, description="精确率")
    recall: Optional[float] = Field(None, description="召回率")
    f1_score: Optional[float] = Field(None, description="F1分数")
    training_metrics: Optional[Dict[str, Any]] = Field(None, description="训练指标")
    validation_metrics: Optional[Dict[str, Any]] = Field(None, description="验证指标")
    confusion_matrix: Optional[List[List[int]]] = Field(None, description="混淆矩阵")


# =====================================================
# 数据标注相关模式
# =====================================================

class AnnotationProjectCreate(BaseModel):
    """创建标注项目请求模式"""
    project_name: str = Field(..., description="项目名称", max_length=200)
    description: Optional[str] = Field(None, description="项目描述")
    annotation_type: str = Field(..., description="标注类型", max_length=50)
    data_type: str = Field(..., description="数据类型", max_length=50)
    label_schema: Dict[str, Any] = Field(..., description="标签模式")
    quality_threshold: float = Field(0.8, description="质量阈值", ge=0.0, le=1.0)


class AnnotationProjectUpdate(BaseModel):
    """更新标注项目请求模式"""
    project_name: Optional[str] = Field(None, description="项目名称", max_length=200)
    description: Optional[str] = Field(None, description="项目描述")
    annotation_type: Optional[str] = Field(None, description="标注类型", max_length=50)
    data_type: Optional[str] = Field(None, description="数据类型", max_length=50)
    label_schema: Optional[Dict[str, Any]] = Field(None, description="标签模式")
    quality_threshold: Optional[float] = Field(None, description="质量阈值", ge=0.0, le=1.0)


class AnnotationProjectResponse(BaseModel):
    """标注项目响应模式"""
    id: int = Field(..., description="项目ID")
    project_name: str = Field(..., description="项目名称")
    description: Optional[str] = Field(None, description="项目描述")
    annotation_type: str = Field(..., description="标注类型")
    data_type: str = Field(..., description="数据类型")
    label_schema: Dict[str, Any] = Field(..., description="标签模式")
    total_samples: int = Field(..., description="总样本数")
    annotated_samples: int = Field(..., description="已标注样本数")
    reviewed_samples: int = Field(..., description="已审核样本数")
    status: AnnotationStatus = Field(..., description="项目状态")
    progress: float = Field(..., description="完成进度(0-100)")
    quality_threshold: float = Field(..., description="质量阈值")
    inter_annotator_agreement: Optional[float] = Field(None, description="标注者间一致性")
    import_config: Optional[Dict[str, Any]] = Field(None, description="导入配置")
    export_config: Optional[Dict[str, Any]] = Field(None, description="导出配置")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    created_by: Optional[int] = Field(None, description="创建人ID")
    updated_by: Optional[int] = Field(None, description="更新人ID")


class AnnotationImportRequest(BaseModel):
    """标注数据导入请求模式"""
    data_source: str = Field(..., description="数据源")
    import_format: str = Field(..., description="导入格式")
    import_config: Dict[str, Any] = Field(..., description="导入配置")


class AnnotationExportRequest(BaseModel):
    """标注数据导出请求模式"""
    export_format: str = Field(..., description="导出格式")
    export_config: Dict[str, Any] = Field(default_factory=dict, description="导出配置")
    include_reviewed_only: bool = Field(False, description="仅包含已审核数据")


# =====================================================
# 健康评分相关模式
# =====================================================

class HealthScoreCreate(BaseModel):
    """创建健康评分请求模式"""
    score_name: str = Field(..., description="评分名称", max_length=200)
    description: Optional[str] = Field(None, description="评分描述")
    target_type: str = Field(..., description="评分对象类型", max_length=50)
    target_id: int = Field(..., description="评分对象ID")
    scoring_algorithm: str = Field(..., description="评分算法", max_length=100)
    weight_config: Dict[str, Any] = Field(..., description="权重配置")
    threshold_config: Dict[str, Any] = Field(..., description="阈值配置")
    data_period_start: Optional[datetime] = Field(None, description="数据周期开始")
    data_period_end: Optional[datetime] = Field(None, description="数据周期结束")


class HealthScoreUpdate(BaseModel):
    """更新健康评分请求模式"""
    score_name: Optional[str] = Field(None, description="评分名称", max_length=200)
    description: Optional[str] = Field(None, description="评分描述")
    scoring_algorithm: Optional[str] = Field(None, description="评分算法", max_length=100)
    weight_config: Optional[Dict[str, Any]] = Field(None, description="权重配置")
    threshold_config: Optional[Dict[str, Any]] = Field(None, description="阈值配置")


class HealthScoreResponse(BaseModel):
    """健康评分响应模式"""
    id: int = Field(..., description="评分ID")
    score_name: str = Field(..., description="评分名称")
    description: Optional[str] = Field(None, description="评分描述")
    target_type: str = Field(..., description="评分对象类型")
    target_id: int = Field(..., description="评分对象ID")
    scoring_algorithm: str = Field(..., description="评分算法")
    weight_config: Dict[str, Any] = Field(..., description="权重配置")
    threshold_config: Dict[str, Any] = Field(..., description="阈值配置")
    overall_score: Optional[float] = Field(None, description="总体评分(0-100)")
    dimension_scores: Optional[Dict[str, Any]] = Field(None, description="维度评分")
    risk_level: Optional[str] = Field(None, description="风险等级")
    status: HealthScoreStatus = Field(..., description="评分状态")
    calculated_at: Optional[datetime] = Field(None, description="计算时间")
    data_period_start: Optional[datetime] = Field(None, description="数据周期开始")
    data_period_end: Optional[datetime] = Field(None, description="数据周期结束")
    trend_direction: Optional[str] = Field(None, description="趋势方向")
    trend_confidence: Optional[float] = Field(None, description="趋势置信度")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    created_by: Optional[int] = Field(None, description="创建人ID")
    updated_by: Optional[int] = Field(None, description="更新人ID")


class HealthScoreConfigUpdate(BaseModel):
    """健康评分配置更新模式"""
    weight_config: Dict[str, Any] = Field(..., description="权重配置")
    threshold_config: Dict[str, Any] = Field(..., description="阈值配置")


class HealthScoreTrendsResponse(BaseModel):
    """健康评分趋势响应模式"""
    target_type: str = Field(..., description="评分对象类型")
    target_id: int = Field(..., description="评分对象ID")
    trend_data: List[Dict[str, Any]] = Field(..., description="趋势数据")
    trend_direction: str = Field(..., description="趋势方向")
    trend_confidence: float = Field(..., description="趋势置信度")
    period_start: datetime = Field(..., description="周期开始")
    period_end: datetime = Field(..., description="周期结束")


# =====================================================
# 智能分析相关模式
# =====================================================

class AnalysisCreate(BaseModel):
    """创建分析请求模式"""
    analysis_name: str = Field(..., description="分析名称", max_length=200)
    description: Optional[str] = Field(None, description="分析描述")
    analysis_type: str = Field(..., description="分析类型", max_length=50)
    algorithm: str = Field(..., description="分析算法", max_length=100)
    parameters: Dict[str, Any] = Field(..., description="分析参数")
    data_sources: List[str] = Field(..., description="数据源列表")
    data_filters: Dict[str, Any] = Field(default_factory=dict, description="数据过滤条件")


class AnalysisUpdate(BaseModel):
    """更新分析请求模式"""
    analysis_name: Optional[str] = Field(None, description="分析名称", max_length=200)
    description: Optional[str] = Field(None, description="分析描述")
    analysis_type: Optional[str] = Field(None, description="分析类型", max_length=50)
    algorithm: Optional[str] = Field(None, description="分析算法", max_length=100)
    parameters: Optional[Dict[str, Any]] = Field(None, description="分析参数")
    data_sources: Optional[List[str]] = Field(None, description="数据源列表")
    data_filters: Optional[Dict[str, Any]] = Field(None, description="数据过滤条件")


class AnalysisResponse(BaseModel):
    """分析响应模式"""
    id: int = Field(..., description="分析ID")
    analysis_name: str = Field(..., description="分析名称")
    description: Optional[str] = Field(None, description="分析描述")
    analysis_type: str = Field(..., description="分析类型")
    algorithm: str = Field(..., description="分析算法")
    parameters: Dict[str, Any] = Field(..., description="分析参数")
    data_sources: List[str] = Field(..., description="数据源列表")
    data_filters: Dict[str, Any] = Field(..., description="数据过滤条件")
    status: AnalysisStatus = Field(..., description="分析状态")
    progress: int = Field(..., description="执行进度(0-100)")
    result_data: Optional[Dict[str, Any]] = Field(None, description="分析结果")
    insights: Optional[Dict[str, Any]] = Field(None, description="洞察信息")
    recommendations: Optional[Dict[str, Any]] = Field(None, description="建议信息")
    started_at: Optional[datetime] = Field(None, description="开始时间")
    completed_at: Optional[datetime] = Field(None, description="完成时间")
    error_message: Optional[str] = Field(None, description="错误信息")
    is_scheduled: bool = Field(False, description="是否定时分析")
    schedule_config: Optional[Dict[str, Any]] = Field(None, description="定时配置")
    next_run_at: Optional[datetime] = Field(None, description="下次运行时间")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    created_by: Optional[int] = Field(None, description="创建人ID")
    updated_by: Optional[int] = Field(None, description="更新人ID")


class AnalysisScheduleRequest(BaseModel):
    """分析定时请求模式"""
    schedule_config: Dict[str, Any] = Field(..., description="定时配置")
    is_enabled: bool = Field(True, description="是否启用")


class AnalysisResultsResponse(BaseModel):
    """分析结果响应模式"""
    analysis_id: int = Field(..., description="分析ID")
    analysis_name: str = Field(..., description="分析名称")
    result_data: Dict[str, Any] = Field(..., description="分析结果")
    insights: Dict[str, Any] = Field(..., description="洞察信息")
    recommendations: Dict[str, Any] = Field(..., description="建议信息")
    completed_at: datetime = Field(..., description="完成时间")


# =====================================================
# 查询参数模式
# =====================================================

class AIMonitoringQuery(BaseModel):
    """AI监控查询参数"""
    status: Optional[str] = Field(None, description="状态过滤")
    model_type: Optional[str] = Field(None, description="模型类型过滤")
    created_by: Optional[int] = Field(None, description="创建人过滤")
    date_from: Optional[datetime] = Field(None, description="开始日期")
    date_to: Optional[datetime] = Field(None, description="结束日期")
    search: Optional[str] = Field(None, description="搜索关键词")


# =====================================================
# 批量操作模式
# =====================================================

class BatchDeleteRequest(BaseModel):
    """批量删除请求模式"""
    ids: List[int] = Field(..., description="要删除的ID列表")


class BatchOperationResponse(BaseModel):
    """批量操作响应模式"""
    success_count: int = Field(..., description="成功数量")
    failed_count: int = Field(..., description="失败数量")
    failed_ids: List[int] = Field(default_factory=list, description="失败的ID列表")
    errors: List[str] = Field(default_factory=list, description="错误信息列表")