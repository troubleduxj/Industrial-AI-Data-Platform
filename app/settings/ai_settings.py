#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AI监测模块配置"""

from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings
import os
from app.settings.config import get_env_file


class AIModuleSettings(BaseSettings):
    """AI模块配置"""
    
    # 全局开关
    ai_module_enabled: bool = Field(
        default=True,
        env='AI_MODULE_ENABLED',
        description='是否启用AI监测模块'
    )
    
    # 功能开关
    ai_feature_extraction_enabled: bool = Field(default=True, env='AI_FEATURE_EXTRACTION_ENABLED')
    ai_anomaly_detection_enabled: bool = Field(default=True, env='AI_ANOMALY_DETECTION_ENABLED')
    ai_trend_prediction_enabled: bool = Field(default=True, env='AI_TREND_PREDICTION_ENABLED')
    ai_health_scoring_enabled: bool = Field(default=True, env='AI_HEALTH_SCORING_ENABLED')
    ai_smart_analysis_enabled: bool = Field(default=True, env='AI_SMART_ANALYSIS_ENABLED')
    
    # 资源限制
    ai_max_memory_mb: int = Field(default=1024, env='AI_MAX_MEMORY_MB')
    ai_max_cpu_percent: int = Field(default=50, ge=1, le=100, env='AI_MAX_CPU_PERCENT')
    ai_worker_threads: int = Field(default=2, ge=1, env='AI_WORKER_THREADS')
    
    # 路径配置
    ai_models_path: str = Field(default='./data/ai_models', env='AI_MODELS_PATH')
    
    # 后台任务
    ai_background_tasks_enabled: bool = Field(default=True, env='AI_BACKGROUND_TASKS_ENABLED')
    
    def is_feature_enabled(self, feature_name: str) -> bool:
        """检查特定功能是否启用"""
        if not self.ai_module_enabled:
            return False
        
        feature_map = {
            'feature_extraction': self.ai_feature_extraction_enabled,
            'anomaly_detection': self.ai_anomaly_detection_enabled,
            'trend_prediction': self.ai_trend_prediction_enabled,
            'health_scoring': self.ai_health_scoring_enabled,
            'smart_analysis': self.ai_smart_analysis_enabled,
        }
        
        return feature_map.get(feature_name, False)
    
    class Config:
        env_file = get_env_file()
        env_file_encoding = 'utf-8'
        extra = 'ignore'  # 忽略额外的环境变量字段


# 全局实例
ai_settings = AIModuleSettings()

