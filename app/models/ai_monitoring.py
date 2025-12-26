#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI监控模块数据模型
包含趋势预测、模型管理、数据标注、健康评分等功能的数据模型

⚠️ 模块归属: AI监测模块 (ai_module)
注意: 这些模型属于AI模块，但保留在 models/ 目录下便于 Tortoise-ORM 管理。
当 AI_MODULE_ENABLED=false 时，这些表可选不创建。
参见: app/settings/ai_settings.py
"""

from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum

from tortoise import fields
from tortoise.models import Model

from app.models.base import BaseModel, TimestampMixin


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
# 趋势预测模型
# =====================================================

class AIPrediction(BaseModel):
    """AI趋势预测模型"""
    
    class Meta:
        table = "t_ai_predictions"
        table_description = "AI趋势预测表"
    
    # 基本信息
    prediction_name = fields.CharField(max_length=200, description="预测名称")
    description = fields.TextField(null=True, description="预测描述")
    
    # 预测配置
    target_variable = fields.CharField(max_length=100, description="目标变量")
    prediction_horizon = fields.IntField(description="预测时间范围(小时)")
    model_type = fields.CharField(max_length=50, description="模型类型")
    parameters = fields.JSONField(default=dict, description="预测参数(JSON)")
    
    # 数据源配置
    data_source = fields.CharField(max_length=100, description="数据源")
    data_filters = fields.JSONField(default=dict, description="数据过滤条件(JSON)")
    
    # 状态和结果
    status = fields.CharEnumField(PredictionStatus, default=PredictionStatus.PENDING, description="预测状态")
    progress = fields.IntField(default=0, description="执行进度(0-100)")
    
    # 结果数据
    result_data = fields.JSONField(null=True, description="预测结果数据(JSON)")
    accuracy_score = fields.FloatField(null=True, description="准确率分数")
    confidence_interval = fields.JSONField(null=True, description="置信区间(JSON)")
    
    # 执行信息
    started_at = fields.DatetimeField(null=True, description="开始时间")
    completed_at = fields.DatetimeField(null=True, description="完成时间")
    error_message = fields.TextField(null=True, description="错误信息")
    
    # 定时分析
    is_scheduled = fields.BooleanField(default=False, description="是否定时分析")
    schedule_config = fields.JSONField(null=True, description="定时配置(JSON)")
    next_run_at = fields.DatetimeField(null=True, description="下次运行时间")
    
    # 审计字段
    created_at = fields.DatetimeField(auto_now_add=True, description="创建时间")
    updated_at = fields.DatetimeField(auto_now=True, description="更新时间")
    created_by = fields.BigIntField(null=True, description="创建人ID")
    updated_by = fields.BigIntField(null=True, description="更新人ID")


# =====================================================
# 异常检测记录模型
# =====================================================

class AIAnomalyRecord(BaseModel):
    """AI异常检测记录模型"""
    
    class Meta:
        table = "t_ai_anomaly_records"
        table_description = "AI异常检测记录表"
    
    # 基本信息
    device_code = fields.CharField(max_length=50, description="设备编码", index=True)
    device_name = fields.CharField(max_length=100, null=True, description="设备名称")
    
    # 异常信息
    anomaly_type = fields.CharField(max_length=50, description="异常类型/检测方法")
    severity = fields.CharField(max_length=20, default="低", description="严重程度")
    anomaly_score = fields.FloatField(default=0.0, description="异常分数")
    
    # 详细数据
    anomaly_data = fields.JSONField(default=dict, description="异常详情数据(JSON)")
    
    # 时间信息
    detection_time = fields.DatetimeField(auto_now_add=True, description="检测时间", index=True)
    
    # 处理状态
    is_handled = fields.BooleanField(default=False, description="是否已处理", index=True)
    handle_time = fields.DatetimeField(null=True, description="处理时间")
    handle_by = fields.CharField(max_length=100, null=True, description="处理人")
    handle_note = fields.TextField(null=True, description="处理备注")
    
    # 审计字段
    created_at = fields.DatetimeField(auto_now_add=True, description="创建时间")


class AIAnomalyConfig(BaseModel):
    """AI异常检测配置模型"""
    
    class Meta:
        table = "t_ai_anomaly_configs"
        table_description = "AI异常检测配置表"
    
    device_code = fields.CharField(max_length=50, unique=True, description="设备编码", index=True)
    config_data = fields.JSONField(default=dict, description="配置数据(JSON)")
    is_active = fields.BooleanField(default=True, description="是否启用")
    
    # 审计字段
    created_at = fields.DatetimeField(auto_now_add=True, description="创建时间")
    updated_at = fields.DatetimeField(auto_now=True, description="更新时间")
    updated_by = fields.CharField(max_length=100, null=True, description="更新人")


# =====================================================
# AI模型管理模型
# =====================================================

class AIModel(BaseModel):
    """AI模型管理模型"""
    
    class Meta:
        table = "t_ai_models"
        table_description = "AI模型管理表"
    
    # 基本信息
    model_name = fields.CharField(max_length=100, description="模型名称")
    model_version = fields.CharField(max_length=50, description="模型版本")
    model_type = fields.CharField(max_length=50, description="模型类型(anomaly_detection/trend_prediction/etc)")
    description = fields.TextField(null=True, description="模型描述")
    
    # 文件和路径
    file_path = fields.CharField(max_length=255, null=True, description="模型文件路径")
    
    # 配置信息
    parameters = fields.JSONField(default=dict, description="模型参数(JSON)")
    metrics = fields.JSONField(default=dict, description="评估指标(JSON)")
    
    # 状态
    status = fields.CharEnumField(ModelStatus, default=ModelStatus.DRAFT, description="模型状态")
    is_active = fields.BooleanField(default=False, description="是否激活(当前使用的模型)")
    
    # 训练信息
    training_data_info = fields.JSONField(null=True, description="训练数据信息")
    trained_at = fields.DatetimeField(null=True, description="训练完成时间")
    
    # 审计字段
    created_at = fields.DatetimeField(auto_now_add=True, description="创建时间")
    updated_at = fields.DatetimeField(auto_now=True, description="更新时间")
    created_by = fields.BigIntField(null=True, description="创建人ID")
