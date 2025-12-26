#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI趋势预测执行API

提供设备数据趋势预测功能，集成Week 2的TrendPredictor服务。
支持ARIMA、移动平均、指数平滑和线性回归等多种预测方法。
"""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel, Field
import logging

from app.core.response_formatter_v2 import create_formatter
from app.core.dependency import DependAuth
from app.services.ai.prediction import TrendPredictor
from app.core.exceptions import APIException
from app.schemas.base import APIResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/predictions/execute", tags=["AI预测-实时计算"])
formatter = create_formatter()


# ==================== 请求/响应模型 ====================

class TrendPredictionRequest(BaseModel):
    """趋势预测请求"""
    data: List[float] = Field(..., description="历史数据时间序列", min_items=10)
    steps: int = Field(..., description="预测步数（未来多少个时间点）", ge=1, le=100)
    method: str = Field(
        default="arima",
        description="预测方法：arima（ARIMA）、ma（移动平均）、ema（指数平滑）、lr（线性回归）、auto（自动选择）"
    )
    confidence_level: float = Field(
        default=0.95,
        description="置信水平（0.9, 0.95, 0.99）",
        ge=0.8,
        le=0.99
    )


class PredictionPoint(BaseModel):
    """预测点信息"""
    step: int = Field(..., description="预测步数（从1开始）")
    predicted_value: float = Field(..., description="预测值")
    lower_bound: Optional[float] = Field(None, description="置信区间下界")
    upper_bound: Optional[float] = Field(None, description="置信区间上界")


class TrendPredictionResponse(BaseModel):
    """趋势预测响应"""
    predictions: List[PredictionPoint] = Field(..., description="预测结果列表")
    method_used: str = Field(..., description="使用的预测方法")
    data_points: int = Field(..., description="输入数据点数")
    prediction_steps: int = Field(..., description="预测步数")
    trend_direction: str = Field(..., description="趋势方向：上升、下降、平稳")
    evaluation: Optional[Dict[str, float]] = Field(None, description="模型评估指标（如有）")


class BatchTrendPredictionRequest(BaseModel):
    """批量趋势预测请求"""
    dataset: Dict[str, List[float]] = Field(..., description="设备数据集")
    steps: int = Field(..., description="预测步数", ge=1, le=100)
    method: str = Field(default="auto", description="预测方法")
    confidence_level: float = Field(default=0.95, description="置信水平")


class BatchTrendPredictionResponse(BaseModel):
    """批量趋势预测响应"""
    results: Dict[str, dict] = Field(..., description="批量预测结果")
    total_devices: int = Field(..., description="处理的设备总数")
    success_count: int = Field(..., description="成功预测的设备数")
    failed_devices: List[str] = Field(default_factory=list, description="失败的设备ID列表")


class ModelComparisonRequest(BaseModel):
    """模型对比请求"""
    data: List[float] = Field(..., description="历史数据", min_items=10)
    steps: int = Field(..., description="预测步数", ge=1, le=50)
    methods: List[str] = Field(
        default=["arima", "ma", "ema", "lr"],
        description="要对比的方法列表"
    )


class ModelComparisonResponse(BaseModel):
    """模型对比响应"""
    comparisons: List[Dict[str, Any]] = Field(..., description="各方法的预测结果和评估")
    best_method: str = Field(..., description="推荐的最佳方法")
    data_points: int = Field(..., description="输入数据点数")


# ==================== API端点 ====================

@router.post(
    "/predict",
    summary="执行趋势预测",
    description="基于历史数据预测未来趋势，支持多种预测算法",
    response_model=APIResponse[TrendPredictionResponse],
    dependencies=[DependAuth]
)
async def predict_trend(
    request: TrendPredictionRequest,
    current_user=DependAuth
):
    """
    执行趋势预测
    
    **预测方法**:
    - `arima`: ARIMA时间序列模型（适用于有趋势和季节性的数据）
    - `ma`: 简单移动平均（适用于短期预测）
    - `ema`: 指数平滑（对最近数据赋予更高权重）
    - `lr`: 线性回归（适用于线性趋势）
    - `auto`: 自动选择最佳方法
    
    **置信区间**:
    - 0.90: 90%置信水平
    - 0.95: 95%置信水平（推荐）
    - 0.99: 99%置信水平
    
    **使用场景**:
    - 设备状态趋势预测
    - 故障预测
    - 维护计划制定
    - 资源需求预测
    
    **示例**:
    ```json
    {
      "data": [100, 102, 98, 101, 99, 103, 97, 100, 102, 104],
      "steps": 5,
      "method": "arima",
      "confidence_level": 0.95
    }
    ```
    """
    try:
        logger.info(
            f"用户 {current_user.username} 请求趋势预测，"
            f"数据点数: {len(request.data)}, 预测步数: {request.steps}, 方法: {request.method}"
        )
        
        # 验证数据
        if len(request.data) < 10:
            raise APIException(
                status_code=400,
                code="INSUFFICIENT_DATA",
                message="数据点数至少需要10个才能进行趋势预测"
            )
        
        # 验证预测方法
        valid_methods = {"arima", "ma", "ema", "lr", "auto"}
        if request.method not in valid_methods:
            raise APIException(
                status_code=400,
                code="INVALID_METHOD",
                message=f"无效的预测方法。有效方法: {', '.join(valid_methods)}"
            )
        
        # 创建趋势预测器
        predictor = TrendPredictor()
        
        # 执行预测
        result = predictor.predict(
            data=request.data,
            steps=request.steps,
            method=request.method,
            confidence_level=request.confidence_level
        )
        
        # 构建响应
        predictions = []
        for i, pred in enumerate(result["predictions"], start=1):
            predictions.append(PredictionPoint(
                step=i,
                predicted_value=pred["value"],
                lower_bound=pred.get("lower_bound"),
                upper_bound=pred.get("upper_bound")
            ))
        
        response = TrendPredictionResponse(
            predictions=predictions,
            method_used=result["method"],
            data_points=len(request.data),
            prediction_steps=request.steps,
            trend_direction=result["trend"],
            evaluation=result.get("evaluation")
        )
        
        logger.info(f"趋势预测完成，方法: {result['method']}, 趋势: {result['trend']}")
        
        return formatter.success(
            data=response,
            message=f"成功预测 {request.steps} 步，趋势: {result['trend']}"
        )
    
    except APIException:
        raise
    except Exception as e:
        logger.error(f"趋势预测失败: {str(e)}", exc_info=True)
        raise APIException(
            status_code=500,
            code="TREND_PREDICTION_ERROR",
            message=f"趋势预测失败: {str(e)}"
        )


@router.post(
    "/predict/batch",
    summary="批量趋势预测",
    description="批量预测多个设备的未来趋势",
    response_model=APIResponse[BatchTrendPredictionResponse],
    dependencies=[DependAuth]
)
async def batch_predict_trend(
    request: BatchTrendPredictionRequest,
    current_user=DependAuth
):
    """
    批量趋势预测
    
    **功能**:
    - 同时处理多个设备的数据
    - 自动跳过异常数据
    - 返回成功/失败统计
    
    **使用场景**:
    - 设备群组趋势分析
    - 批量故障预测
    - 资源规划
    """
    try:
        logger.info(f"用户 {current_user.username} 请求批量趋势预测，设备数: {len(request.dataset)}")
        
        if not request.dataset:
            raise APIException(
                status_code=400,
                code="EMPTY_DATASET",
                message="数据集不能为空"
            )
        
        # 创建趋势预测器
        predictor = TrendPredictor()
        
        # 批量预测
        results = {}
        failed_devices = []
        success_count = 0
        
        for device_id, data in request.dataset.items():
            try:
                if len(data) < 10:
                    logger.warning(f"设备 {device_id} 数据点数不足，跳过")
                    failed_devices.append(device_id)
                    continue
                
                # 执行预测
                result = predictor.predict(
                    data=data,
                    steps=request.steps,
                    method=request.method,
                    confidence_level=request.confidence_level
                )
                
                results[device_id] = {
                    "predictions": result["predictions"],
                    "method": result["method"],
                    "trend": result["trend"],
                    "evaluation": result.get("evaluation")
                }
                
                success_count += 1
                
            except Exception as e:
                logger.error(f"设备 {device_id} 趋势预测失败: {str(e)}")
                failed_devices.append(device_id)
                continue
        
        response = BatchTrendPredictionResponse(
            results=results,
            total_devices=len(request.dataset),
            success_count=success_count,
            failed_devices=failed_devices
        )
        
        logger.info(f"批量趋势预测完成，成功: {success_count}/{len(request.dataset)}")
        
        return formatter.success(
            data=response,
            message=f"批量预测完成，成功: {success_count}/{len(request.dataset)}"
        )
    
    except APIException:
        raise
    except Exception as e:
        logger.error(f"批量趋势预测失败: {str(e)}", exc_info=True)
        raise APIException(
            status_code=500,
            code="BATCH_TREND_PREDICTION_ERROR",
            message=f"批量趋势预测失败: {str(e)}"
        )


@router.post(
    "/compare",
    summary="预测方法对比",
    description="对比多种预测方法的效果，自动选择最佳方法",
    response_model=APIResponse[ModelComparisonResponse],
    dependencies=[DependAuth]
)
async def compare_prediction_methods(
    request: ModelComparisonRequest,
    current_user=DependAuth
):
    """
    预测方法对比
    
    **功能**:
    - 同时使用多种方法进行预测
    - 计算每种方法的评估指标（MAE、RMSE、MAPE）
    - 自动推荐最佳方法
    
    **使用场景**:
    - 选择最适合当前数据的预测方法
    - 模型性能评估
    - 预测结果可信度分析
    
    **返回**:
    - 每种方法的预测结果
    - 评估指标对比
    - 推荐的最佳方法
    """
    try:
        logger.info(
            f"用户 {current_user.username} 请求预测方法对比，"
            f"数据点数: {len(request.data)}, 对比方法: {request.methods}"
        )
        
        # 验证数据
        if len(request.data) < 10:
            raise APIException(
                status_code=400,
                code="INSUFFICIENT_DATA",
                message="数据点数至少需要10个才能进行方法对比"
            )
        
        # 验证方法
        valid_methods = {"arima", "ma", "ema", "lr"}
        invalid_methods = set(request.methods) - valid_methods
        if invalid_methods:
            raise APIException(
                status_code=400,
                code="INVALID_METHOD",
                message=f"无效的预测方法: {', '.join(invalid_methods)}"
            )
        
        # 创建趋势预测器
        predictor = TrendPredictor()
        
        # 对比方法
        comparisons = []
        best_method = None
        best_score = float('inf')
        
        for method in request.methods:
            try:
                # 执行预测
                result = predictor.predict(
                    data=request.data,
                    steps=request.steps,
                    method=method
                )
                
                # 获取评估指标
                evaluation = result.get("evaluation", {})
                mae = evaluation.get("mae", float('inf'))
                
                comparisons.append({
                    "method": method,
                    "predictions": result["predictions"],
                    "trend": result["trend"],
                    "evaluation": evaluation
                })
                
                # 更新最佳方法（基于MAE）
                if mae < best_score:
                    best_score = mae
                    best_method = method
                
            except Exception as e:
                logger.warning(f"方法 {method} 预测失败: {str(e)}")
                comparisons.append({
                    "method": method,
                    "error": str(e)
                })
                continue
        
        if not best_method:
            raise APIException(
                status_code=500,
                code="ALL_METHODS_FAILED",
                message="所有预测方法均失败"
            )
        
        response = ModelComparisonResponse(
            comparisons=comparisons,
            best_method=best_method,
            data_points=len(request.data)
        )
        
        logger.info(f"预测方法对比完成，推荐方法: {best_method}")
        
        return formatter.success(
            data=response,
            message=f"方法对比完成，推荐使用: {best_method}"
        )
    
    except APIException:
        raise
    except Exception as e:
        logger.error(f"预测方法对比失败: {str(e)}", exc_info=True)
        raise APIException(
            status_code=500,
            code="METHOD_COMPARISON_ERROR",
            message=f"预测方法对比失败: {str(e)}"
        )


@router.get(
    "/methods",
    summary="获取支持的预测方法",
    description="获取系统支持的所有预测方法及其说明",
    dependencies=[DependAuth]
)
async def get_prediction_methods(current_user=DependAuth):
    """
    获取支持的预测方法
    
    **返回**:
    - 预测方法列表
    - 每个方法的说明和适用场景
    """
    try:
        methods = {
            "arima": {
                "name": "ARIMA时间序列模型",
                "description": "自回归移动平均模型，适用于有趋势和季节性的数据",
                "适用场景": ["中长期预测", "复杂趋势", "季节性数据"],
                "优点": ["准确度高", "理论基础扎实", "可解释性强"],
                "缺点": ["计算复杂", "需要较多历史数据", "参数调优困难"],
                "min_data_points": 20
            },
            "ma": {
                "name": "简单移动平均",
                "description": "计算固定窗口的平均值进行预测",
                "适用场景": ["短期预测", "平稳数据", "快速分析"],
                "优点": ["计算简单", "易于理解", "实时性好"],
                "缺点": ["对趋势变化不敏感", "滞后性强"],
                "min_data_points": 5
            },
            "ema": {
                "name": "指数平滑",
                "description": "对最近的数据赋予更高权重的平滑方法",
                "适用场景": ["短中期预测", "趋势变化", "噪声数据"],
                "优点": ["对最新数据敏感", "适应性强", "计算高效"],
                "缺点": ["需要调参", "对异常值敏感"],
                "min_data_points": 10
            },
            "lr": {
                "name": "线性回归",
                "description": "拟合线性趋势进行预测",
                "适用场景": ["线性趋势", "长期预测", "趋势分析"],
                "优点": ["简单直观", "可解释性强", "计算快速"],
                "缺点": ["仅适用于线性趋势", "对非线性变化无效"],
                "min_data_points": 10
            },
            "auto": {
                "name": "自动选择",
                "description": "自动选择最适合当前数据的预测方法",
                "适用场景": ["不确定数据特征", "通用预测", "快速分析"],
                "优点": ["无需人工选择", "适应性强", "准确度高"],
                "缺点": ["计算时间较长"],
                "min_data_points": 10
            }
        }
        
        return formatter.success(
            data=methods,
            message="成功获取预测方法列表"
        )
    
    except Exception as e:
        logger.error(f"获取预测方法失败: {str(e)}", exc_info=True)
        raise APIException(
            status_code=500,
            code="GET_METHODS_ERROR",
            message=f"获取预测方法失败: {str(e)}"
        )

