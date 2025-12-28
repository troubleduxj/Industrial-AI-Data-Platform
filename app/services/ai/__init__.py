#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI服务包
包含所有AI相关的服务实现

核心组件：
- ModelRegistry: AI模型注册中心
- InferenceService: 统一推理服务
- BasePredictor: 预测器基类
"""

__version__ = "0.2.0"
__author__ = "DeviceMonitor Team"

# 导入各个服务
from app.services.ai.trainer import BaseTrainer
from app.services.ai.data_loader import TDengineLoader

# 导入新的AI引擎组件
from app.services.ai.model_registry import (
    ModelRegistry,
    ModelRegistryError,
    model_registry
)
from app.services.ai.inference_service import (
    InferenceService,
    InferenceError,
    BasePredictor,
    IsolationForestPredictor,
    ARIMAPredictor,
    XGBoostPredictor,
    inference_service
)

__all__ = [
    # 原有组件
    "BaseTrainer",
    "TDengineLoader",
    # 新AI引擎组件
    "ModelRegistry",
    "ModelRegistryError",
    "model_registry",
    "InferenceService",
    "InferenceError",
    "BasePredictor",
    "IsolationForestPredictor",
    "ARIMAPredictor",
    "XGBoostPredictor",
    "inference_service"
]
