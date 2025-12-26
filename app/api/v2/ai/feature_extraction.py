#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI特征提取API

提供设备数据特征提取功能，包括统计特征、时间序列特征和频域特征。
"""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel, Field
import logging

from app.core.response_formatter_v2 import create_formatter
from app.core.dependency import DependAuth
from app.services.ai.feature_extraction import FeatureExtractor
from app.core.exceptions import APIException
from app.schemas.base import APIResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ai/features", tags=["AI特征提取"])
formatter = create_formatter()


# ==================== 请求/响应模型 ====================

class FeatureExtractionRequest(BaseModel):
    """特征提取请求"""
    data: List[float] = Field(..., description="设备数据时间序列", min_items=1)
    feature_types: List[str] = Field(
        default=["statistical", "time_series", "frequency"],
        description="要提取的特征类型：statistical（统计）、time_series（时序）、frequency（频域）"
    )


class BatchFeatureExtractionRequest(BaseModel):
    """批量特征提取请求"""
    dataset: Dict[str, List[float]] = Field(..., description="设备数据集，key为设备ID，value为数据时间序列")
    feature_types: List[str] = Field(
        default=["statistical", "time_series", "frequency"],
        description="要提取的特征类型"
    )


class FeatureExtractionResponse(BaseModel):
    """特征提取响应"""
    features: Dict[str, Any] = Field(..., description="提取的特征字典")
    feature_count: int = Field(..., description="提取的特征数量")
    data_points: int = Field(..., description="输入数据点数")


class BatchFeatureExtractionResponse(BaseModel):
    """批量特征提取响应"""
    results: Dict[str, Dict[str, Any]] = Field(..., description="批量提取结果，key为设备ID")
    total_devices: int = Field(..., description="处理的设备总数")
    success_count: int = Field(..., description="成功提取的设备数")
    failed_devices: List[str] = Field(default_factory=list, description="失败的设备ID列表")


# ==================== API端点 ====================

@router.post(
    "/extract",
    summary="提取数据特征",
    description="从设备数据时间序列中提取统计特征、时间序列特征和频域特征",
    response_model=APIResponse[FeatureExtractionResponse],
    dependencies=[DependAuth]
)
async def extract_features(
    request: FeatureExtractionRequest,
    current_user=DependAuth
):
    """
    提取数据特征
    
    **功能**:
    - 统计特征：均值、标准差、最大值、最小值、分位数、峰度、偏度等
    - 时间序列特征：趋势、周期性、自相关、变化率等
    - 频域特征：主频、频谱能量、谱熵等
    
    **使用场景**:
    - AI模型训练前的特征工程
    - 实时数据分析与监控
    - 异常检测前的数据预处理
    
    **示例**:
    ```json
    {
      "data": [100.5, 102.3, 98.7, 101.2, 99.8],
      "feature_types": ["statistical", "time_series"]
    }
    ```
    """
    try:
        logger.info(f"用户 {current_user.username} 请求提取特征，数据点数: {len(request.data)}")
        
        # 验证数据
        if len(request.data) < 2:
            raise APIException(
                status_code=400,
                code="INSUFFICIENT_DATA",
                message="数据点数至少需要2个才能提取特征"
            )
        
        # 验证特征类型
        valid_types = {"statistical", "time_series", "frequency"}
        invalid_types = set(request.feature_types) - valid_types
        if invalid_types:
            raise APIException(
                status_code=400,
                code="INVALID_FEATURE_TYPE",
                message=f"无效的特征类型: {', '.join(invalid_types)}。有效类型: {', '.join(valid_types)}"
            )
        
        # 创建特征提取器
        extractor = FeatureExtractor()
        
        # 提取特征
        features = {}
        
        if "statistical" in request.feature_types:
            stat_features = extractor.statistical.extract(request.data)
            features["statistical"] = stat_features
        
        if "time_series" in request.feature_types:
            ts_features = extractor.time_series.extract(request.data)
            features["time_series"] = ts_features
        
        if "frequency" in request.feature_types:
            freq_features = extractor.frequency.extract(request.data)
            features["frequency"] = freq_features
        
        # 统计特征数量
        feature_count = sum(len(v) if isinstance(v, dict) else 1 for v in features.values())
        
        result = FeatureExtractionResponse(
            features=features,
            feature_count=feature_count,
            data_points=len(request.data)
        )
        
        logger.info(f"特征提取成功，共提取 {feature_count} 个特征")
        
        return formatter.success(
            data=result,
            message=f"成功提取 {feature_count} 个特征"
        )
    
    except APIException:
        raise
    except Exception as e:
        logger.error(f"特征提取失败: {str(e)}", exc_info=True)
        raise APIException(
            status_code=500,
            code="FEATURE_EXTRACTION_ERROR",
            message=f"特征提取失败: {str(e)}"
        )


@router.post(
    "/extract/batch",
    summary="批量提取特征",
    description="批量提取多个设备的数据特征，适用于大规模数据处理",
    response_model=APIResponse[BatchFeatureExtractionResponse],
    dependencies=[DependAuth]
)
async def batch_extract_features(
    request: BatchFeatureExtractionRequest,
    current_user=DependAuth
):
    """
    批量提取特征
    
    **功能**:
    - 支持同时处理多个设备的数据
    - 自动跳过异常数据
    - 返回成功/失败统计
    
    **使用场景**:
    - 周期性特征提取任务
    - AI模型批量训练
    - 设备群组分析
    
    **示例**:
    ```json
    {
      "dataset": {
        "device_001": [100.5, 102.3, 98.7],
        "device_002": [55.2, 56.1, 54.8]
      },
      "feature_types": ["statistical"]
    }
    ```
    """
    try:
        logger.info(f"用户 {current_user.username} 请求批量提取特征，设备数: {len(request.dataset)}")
        
        if not request.dataset:
            raise APIException(
                status_code=400,
                code="EMPTY_DATASET",
                message="数据集不能为空"
            )
        
        # 创建特征提取器
        extractor = FeatureExtractor()
        
        # 批量提取
        results = {}
        failed_devices = []
        success_count = 0
        
        for device_id, data in request.dataset.items():
            try:
                # 验证数据
                if len(data) < 2:
                    logger.warning(f"设备 {device_id} 数据点数不足，跳过")
                    failed_devices.append(device_id)
                    continue
                
                # 提取特征
                device_features = {}
                
                if "statistical" in request.feature_types:
                    device_features["statistical"] = extractor.statistical.extract(data)
                
                if "time_series" in request.feature_types:
                    device_features["time_series"] = extractor.time_series.extract(data)
                
                if "frequency" in request.feature_types:
                    device_features["frequency"] = extractor.frequency.extract(data)
                
                results[device_id] = device_features
                success_count += 1
                
            except Exception as e:
                logger.error(f"设备 {device_id} 特征提取失败: {str(e)}")
                failed_devices.append(device_id)
                continue
        
        result = BatchFeatureExtractionResponse(
            results=results,
            total_devices=len(request.dataset),
            success_count=success_count,
            failed_devices=failed_devices
        )
        
        logger.info(f"批量特征提取完成，成功: {success_count}/{len(request.dataset)}")
        
        return formatter.success(
            data=result,
            message=f"批量提取完成，成功: {success_count}/{len(request.dataset)}"
        )
    
    except APIException:
        raise
    except Exception as e:
        logger.error(f"批量特征提取失败: {str(e)}", exc_info=True)
        raise APIException(
            status_code=500,
            code="BATCH_FEATURE_EXTRACTION_ERROR",
            message=f"批量特征提取失败: {str(e)}"
        )


@router.get(
    "/types",
    summary="获取支持的特征类型",
    description="获取系统支持的所有特征类型及其说明",
    dependencies=[DependAuth]
)
async def get_feature_types(current_user=DependAuth):
    """
    获取支持的特征类型
    
    **返回**:
    - 特征类型列表
    - 每个类型的说明和包含的特征项
    """
    try:
        feature_types = {
            "statistical": {
                "name": "统计特征",
                "description": "基本统计量，如均值、标准差、最大值等",
                "features": [
                    "mean", "std", "max", "min", "median",
                    "q25", "q75", "range", "iqr",
                    "skewness", "kurtosis", "cv"
                ],
                "count": 12
            },
            "time_series": {
                "name": "时间序列特征",
                "description": "时序相关特征，如趋势、周期性、自相关等",
                "features": [
                    "trend", "slope", "intercept",
                    "autocorr_lag1", "autocorr_lag2",
                    "mean_change", "abs_mean_change",
                    "variance_change", "zero_crossing_rate",
                    "mean_abs_diff"
                ],
                "count": 10
            },
            "frequency": {
                "name": "频域特征",
                "description": "频谱分析特征，如主频、频谱能量等",
                "features": [
                    "dominant_frequency", "spectral_energy",
                    "spectral_entropy", "spectral_centroid",
                    "spectral_rolloff", "spectral_flatness",
                    "peak_frequency", "frequency_std",
                    "high_freq_power", "low_freq_power"
                ],
                "count": 10
            }
        }
        
        return formatter.success(
            data=feature_types,
            message="成功获取特征类型列表"
        )
    
    except Exception as e:
        logger.error(f"获取特征类型失败: {str(e)}", exc_info=True)
        raise APIException(
            status_code=500,
            code="GET_FEATURE_TYPES_ERROR",
            message=f"获取特征类型失败: {str(e)}"
        )

