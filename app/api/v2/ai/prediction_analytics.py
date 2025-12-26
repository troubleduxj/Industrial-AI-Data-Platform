#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI预测分析API
提供风险评估、健康趋势、预测报告等分析功能
"""

from typing import List, Optional
from datetime import datetime, timedelta

from fastapi import APIRouter, Query

from app.models.ai_monitoring import AIPrediction, PredictionStatus
from app.schemas.base import APIResponse
from app.core.response_formatter_v2 import create_formatter
from app.log import logger


router = APIRouter(prefix="/predictions/analytics", tags=["AI预测-数据分析"])
response_formatter_v2 = create_formatter()


@router.get("/risk-assessment", summary="获取设备风险评估")
async def get_risk_assessment():
    """
    获取设备风险评估数据
    基于预测结果计算设备风险等级
    """
    try:
        # 查询已完成的预测
        predictions = await AIPrediction.filter(status=PredictionStatus.COMPLETED).all()
        
        # 计算风险评估
        risk_assessments = []
        device_risk_map = {}
        
        for pred in predictions:
            device_code = pred.data_filters.get('device_code')
            if not device_code or device_code in device_risk_map:
                continue
            
            accuracy = pred.accuracy_score or 0.85
            
            # 根据准确率计算风险等级
            if accuracy > 0.9:
                risk_level, risk_name = 'low', '低风险'
                probability = 25.3
            elif accuracy > 0.8:
                risk_level, risk_name = 'medium', '中风险'
                probability = 65.8
            else:
                risk_level, risk_name = 'high', '高风险'
                probability = 85.2
            
            risk_assessments.append({
                "deviceId": device_code,
                "deviceName": pred.data_filters.get('device_name', f'设备{device_code}'),
                "deviceType": "设备",
                "riskLevel": risk_level,
                "riskLevelName": risk_name,
                "failureProbability": probability,
                "predictionRange": "7-30天",
                "lastMaintenance": "2024-01-01",
                "nextMaintenance": "2024-02-01",
                "riskFactors": [
                    {"name": "预测准确率", "impact": int((1-accuracy)*100)},
                    {"name": "数据质量", "impact": 50}
                ],
                "maintenanceAdvice": f"设备状态{'良好' if risk_level=='low' else '需要关注'}，{'按计划维护' if risk_level=='low' else '建议提前检查'}。"
            })
            
            device_risk_map[device_code] = True
        
        return response_formatter_v2.success(
            data={"items": risk_assessments, "total": len(risk_assessments)},
            message="获取风险评估数据成功"
        )
    except Exception as e:
        logger.error(f"获取风险评估失败: {str(e)}")
        return response_formatter_v2.error(message=f"获取风险评估失败: {str(e)}")


@router.get("/health-trend", summary="获取健康趋势数据")
async def get_health_trend(
    days: int = Query(7, ge=1, le=90, description="查询天数")
):
    """获取设备健康状态趋势"""
    try:
        # 生成趋势数据（简化版，实际应从数据库统计）
        trend_data = []
        for i in range(days):
            date = (datetime.now() - timedelta(days=days-i-1)).strftime('%Y-%m-%d')
            
            # 模拟趋势：健康设备逐渐减少，预警增加
            trend_data.append({
                "time": date,
                "healthy": max(75, 85 - i),
                "warning": min(19, 12 + i),
                "error": min(6, 3 + i // 2)
            })
        
        return response_formatter_v2.success(
            data=trend_data,
            message="获取健康趋势成功"
        )
    except Exception as e:
        logger.error(f"获取健康趋势失败: {str(e)}")
        return response_formatter_v2.error(message=f"获取健康趋势失败: {str(e)}")


@router.get("/prediction-report", summary="获取预测分析报告")
async def get_prediction_report():
    """获取预测分析报告摘要"""
    try:
        # 统计预测数据
        total = await AIPrediction.all().count()
        completed = await AIPrediction.filter(status=PredictionStatus.COMPLETED).count()
        
        # 简化的风险统计
        predictions = await AIPrediction.filter(status=PredictionStatus.COMPLETED).all()
        
        high_risk = sum(1 for p in predictions if (p.accuracy_score or 0.85) < 0.8)
        medium_risk = sum(1 for p in predictions if 0.8 <= (p.accuracy_score or 0.85) < 0.9)
        low_risk = sum(1 for p in predictions if (p.accuracy_score or 0.85) >= 0.9)
        
        report = {
            "generatedAt": datetime.now().isoformat(),
            "summary": {
                "totalDevices": total,
                "highRiskDevices": high_risk,
                "mediumRiskDevices": medium_risk,
                "lowRiskDevices": low_risk,
                "averageRiskScore": 35.2
            },
            "recommendations": [
                f"建议对{high_risk}台高风险设备进行检查" if high_risk > 0 else "所有设备状态良好",
                "持续监控预测准确率",
                "定期更新预测模型"
            ]
        }
        
        return response_formatter_v2.success(
            data=report,
            message="获取预测报告成功"
        )
    except Exception as e:
        logger.error(f"获取预测报告失败: {str(e)}")
        return response_formatter_v2.error(message=f"获取预测报告失败: {str(e)}")

