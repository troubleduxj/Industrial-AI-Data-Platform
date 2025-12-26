#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""系统健康检查API"""

from datetime import datetime
from fastapi import APIRouter, HTTPException
from app.settings.ai_settings import ai_settings
from app.ai_module.loader import ai_loader
from app.core.response_formatter_v2 import create_formatter

router = APIRouter(prefix="/system", tags=["系统健康 v2"])


@router.get("/health")
async def get_system_health():
    """获取系统健康状态"""
    formatter = create_formatter()
    
    return formatter.success(
        data={
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "ai_module_status": {
                "module_enabled": ai_settings.ai_module_enabled,
                "module_loaded": ai_loader._loaded,
                "features": {
                    "feature_extraction": ai_settings.ai_feature_extraction_enabled,
                    "anomaly_detection": ai_settings.ai_anomaly_detection_enabled,
                    "trend_prediction": ai_settings.ai_trend_prediction_enabled,
                    "health_scoring": ai_settings.ai_health_scoring_enabled,
                    "smart_analysis": ai_settings.ai_smart_analysis_enabled,
                } if ai_settings.ai_module_enabled else {}
            }
        },
        message="系统运行正常"
    )


@router.get("/modules/ai/config")
async def get_ai_module_config():
    """获取AI模块配置（仅超级管理员）"""
    return {
        "enabled": ai_settings.ai_module_enabled,
        "features": {
            "feature_extraction": ai_settings.ai_feature_extraction_enabled,
            "anomaly_detection": ai_settings.ai_anomaly_detection_enabled,
            "trend_prediction": ai_settings.ai_trend_prediction_enabled,
            "health_scoring": ai_settings.ai_health_scoring_enabled,
            "smart_analysis": ai_settings.ai_smart_analysis_enabled,
        },
        "resources": {
            "max_memory_mb": ai_settings.ai_max_memory_mb,
            "max_cpu_percent": ai_settings.ai_max_cpu_percent,
            "worker_threads": ai_settings.ai_worker_threads,
        }
    }


@router.get("/modules/ai/resources")
async def get_ai_module_resources():
    """获取AI模块资源使用情况"""
    # 检查AI模块是否启用
    if not ai_settings.ai_module_enabled:
        raise HTTPException(
            status_code=503,
            detail="AI模块未启用"
        )
    
    try:
        from app.ai_module.monitor import AIResourceMonitor
        
        # 获取资源统计
        stats = AIResourceMonitor.get_resource_stats()
        
        formatter = create_formatter()
        # 转换为前端期望的格式
        return formatter.success(
            data={
                "cpu_usage": stats.get("usage", {}).get("cpu_percent", 0),
                "memory_usage": stats.get("system_memory", {}).get("percent", 0),
                "qps": None,  # 暂无实时QPS监控
                "avg_latency": None,  # 暂无实时延迟监控
                "timestamp": datetime.now().isoformat(),
                "details": stats
            }
        )
    
    except ImportError:
        raise HTTPException(
            status_code=500,
            detail="AI资源监控器不可用"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"获取资源信息失败: {str(e)}"
        )

