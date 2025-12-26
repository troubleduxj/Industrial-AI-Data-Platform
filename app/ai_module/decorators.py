#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AI模块装饰器"""

from functools import wraps
from typing import Optional
from fastapi import HTTPException
from loguru import logger

from app.settings.ai_settings import ai_settings


def require_ai_module(feature_name: Optional[str] = None):
    """
    要求AI模块启用的装饰器
    
    Args:
        feature_name: 可选的具体功能名称
            - 'feature_extraction': 特征提取
            - 'anomaly_detection': 异常检测
            - 'trend_prediction': 趋势预测
            - 'health_scoring': 健康评分
            - 'smart_analysis': 智能分析
    
    Example:
        @router.post("/analysis")
        @require_ai_module('smart_analysis')
        async def create_analysis(...):
            pass
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 检查AI模块是否启用
            if not ai_settings.ai_module_enabled:
                logger.warning(f"API {func.__name__} 访问被拒绝: AI模块未启用")
                raise HTTPException(
                    status_code=503,
                    detail={
                        "error": "service_unavailable",
                        "message": "AI监测模块未启用",
                        "hint": "请联系管理员启用AI模块或在.env中设置 AI_MODULE_ENABLED=true"
                    }
                )
            
            # 检查特定功能是否启用
            if feature_name:
                if not ai_settings.is_feature_enabled(feature_name):
                    logger.warning(
                        f"API {func.__name__} 访问被拒绝: "
                        f"AI功能 '{feature_name}' 未启用"
                    )
                    raise HTTPException(
                        status_code=503,
                        detail={
                            "error": "feature_disabled",
                            "message": f"AI功能 '{feature_name}' 未启用",
                            "feature": feature_name,
                            "hint": f"请在.env中设置 AI_{feature_name.upper()}_ENABLED=true"
                        }
                    )
            
            # 功能检查通过，执行原函数
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


def require_ai_feature(feature_name: str):
    """
    要求特定AI功能启用的装饰器（简化版本）
    
    Args:
        feature_name: 功能名称
            - 'feature_extraction': 特征提取
            - 'anomaly_detection': 异常检测
            - 'trend_prediction': 趋势预测
            - 'health_scoring': 健康评分
            - 'smart_analysis': 智能分析
    
    Example:
        @router.post("/analysis")
        @require_ai_feature('anomaly_detection')
        async def detect_anomalies(...):
            pass
    """
    return require_ai_module(feature_name)


def check_ai_resources():
    """
    检查AI资源限制的装饰器
    用于资源密集型AI操作
    
    Example:
        @router.post("/heavy-analysis")
        @require_ai_module('smart_analysis')
        @check_ai_resources()
        async def heavy_analysis(...):
            pass
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                # 导入资源监控器
                from app.ai_module.monitor import AIResourceMonitor
                
                # 检查资源使用情况
                stats = AIResourceMonitor.get_resource_stats()
                
                # 检查内存
                memory_mb = stats['memory_mb']
                max_memory = stats['limits']['max_memory_mb']
                if memory_mb > max_memory * 0.9:  # 超过90%警告
                    logger.warning(
                        f"AI模块内存接近限制: {memory_mb:.2f}MB / {max_memory}MB"
                    )
                
                # 检查CPU
                cpu_percent = stats['cpu_percent']
                max_cpu = stats['limits']['max_cpu_percent']
                if cpu_percent > max_cpu * 0.9:  # 超过90%警告
                    logger.warning(
                        f"AI模块CPU接近限制: {cpu_percent:.2f}% / {max_cpu}%"
                    )
                
                # 如果资源严重不足，拒绝请求
                if memory_mb > max_memory or cpu_percent > max_cpu:
                    raise HTTPException(
                        status_code=503,
                        detail={
                            "error": "resource_exhausted",
                            "message": "AI模块资源不足，请稍后重试",
                            "resources": stats
                        }
                    )
                
            except ImportError:
                # 资源监控器不可用，记录警告但不阻止请求
                logger.warning("资源监控器不可用，跳过资源检查")
            
            # 资源检查通过，执行原函数
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


def log_ai_operation(operation_type: str = "unknown"):
    """
    记录AI操作日志的装饰器
    
    Args:
        operation_type: 操作类型
    
    Example:
        @router.post("/predict")
        @require_ai_module('trend_prediction')
        @log_ai_operation('trend_prediction')
        async def predict(...):
            pass
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            logger.info(f"AI操作开始: {operation_type} (function: {func.__name__})")
            
            try:
                result = await func(*args, **kwargs)
                logger.info(f"AI操作成功: {operation_type}")
                return result
            except Exception as e:
                logger.error(f"AI操作失败: {operation_type}, 错误: {str(e)}")
                raise
        
        return wrapper
    return decorator

