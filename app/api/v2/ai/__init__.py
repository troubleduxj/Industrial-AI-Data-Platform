#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI监测模块API

此模块包含AI监测功能的所有API端点，仅在AI模块启用时加载。
参见: app/settings/ai_settings.py, app/ai_module/loader.py
"""

from fastapi import APIRouter
from app.settings.ai_settings import ai_settings

# 创建AI模块总路由
ai_router = APIRouter()

# 条件导入各个子路由
# 这些路由只在对应功能启用时注册

# 特征提取
if ai_settings.ai_feature_extraction_enabled:
    try:
        from app.api.v2.ai.feature_extraction import router as feature_extraction_router
        ai_router.include_router(feature_extraction_router)
    except ImportError as e:
        import logging
        logging.warning(f"无法加载 AI 特征提取路由: {e}")

# 异常检测
if ai_settings.ai_anomaly_detection_enabled:
    try:
        from app.api.v2.ai.anomaly_detection import router as anomaly_detection_router
        ai_router.include_router(anomaly_detection_router)
    except ImportError as e:
        import logging
        logging.warning(f"无法加载 AI 异常检测路由: {e}")

# 智能分析
if ai_settings.ai_smart_analysis_enabled:
    try:
        from app.api.v2.ai.analysis import router as analysis_router
        ai_router.include_router(analysis_router)
    except ImportError as e:
        import logging
        logging.warning(f"无法加载 AI 智能分析路由: {e}")

# 趋势预测 - 执行API
if ai_settings.ai_trend_prediction_enabled:
    try:
        from app.api.v2.ai.trend_prediction import router as trend_prediction_router
        ai_router.include_router(trend_prediction_router)
    except ImportError as e:
        import logging
        logging.warning(f"无法加载 AI 趋势预测执行路由: {e}")

# 趋势预测 - 管理API
if ai_settings.ai_trend_prediction_enabled:
    try:
        from app.api.v2.ai.predictions import router as predictions_router
        ai_router.include_router(predictions_router)
    except ImportError as e:
        import logging
        logging.warning(f"无法加载 AI 趋势预测管理路由: {e}")

# 模型管理
if ai_settings.ai_module_enabled:  # 模型管理属于基础功能
    try:
        from app.api.v2.ai.models import router as models_router
        ai_router.include_router(models_router)
    except ImportError as e:
        import logging
        logging.warning(f"无法加载 AI 模型管理路由: {e}")

# 健康评分 - 执行API
if ai_settings.ai_health_scoring_enabled:
    try:
        from app.api.v2.ai.health_scoring import router as health_scoring_router
        ai_router.include_router(health_scoring_router)
    except ImportError as e:
        import logging
        logging.warning(f"无法加载 AI 健康评分执行路由: {e}")

# 健康评分 - 管理API
if ai_settings.ai_health_scoring_enabled:
    try:
        from app.api.v2.ai.health_scores import router as health_scores_router
        ai_router.include_router(health_scores_router)
    except ImportError as e:
        import logging
        logging.warning(f"无法加载 AI 健康评分管理路由: {e}")

# 数据标注
if ai_settings.ai_module_enabled:  # 数据标注属于基础功能
    try:
        from app.api.v2.ai.annotations import router as annotations_router
        ai_router.include_router(annotations_router)
    except ImportError as e:
        import logging
        logging.warning(f"无法加载 AI 数据标注路由: {e}")

__all__ = ['ai_router']

