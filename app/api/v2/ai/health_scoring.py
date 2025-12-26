#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI健康评分API

提供设备健康状态综合评分功能，集成Week 2的HealthScorer服务。
支持多维度评分、健康等级划分和历史趋势分析。
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel, Field
import logging

from app.core.response_formatter_v2 import create_formatter
from app.core.dependency import DependAuth
from app.services.ai.health_scoring import HealthScorer
from app.models.ai_monitoring import AIHealthScore
from app.core.exceptions import APIException
from app.schemas.base import APIResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/health-scores/calculate", tags=["AI健康-评分计算"])
formatter = create_formatter()


# ==================== 请求/响应模型 ====================

class HealthScoringRequest(BaseModel):
    """健康评分请求"""
    device_code: str = Field(..., description="设备编码")
    device_name: Optional[str] = Field(None, description="设备名称")
    performance_data: Dict[str, float] = Field(
        ...,
        description="性能指标数据，如：{'cpu_usage': 75.5, 'memory_usage': 60.2, 'response_time': 120.0}"
    )
    anomaly_count: int = Field(default=0, description="异常次数（最近一段时间）", ge=0)
    uptime_days: float = Field(default=0.0, description="运行天数", ge=0)
    historical_data: Optional[List[float]] = Field(None, description="历史数据（用于趋势评分）")
    weights: Optional[Dict[str, float]] = Field(
        None,
        description="自定义权重，如：{'performance': 0.3, 'anomaly': 0.3, 'trend': 0.2, 'uptime': 0.2}"
    )
    save_to_db: bool = Field(default=False, description="是否保存评分记录到数据库")


class DimensionScore(BaseModel):
    """维度评分"""
    dimension: str = Field(..., description="评分维度")
    score: float = Field(..., description="得分（0-100）")
    weight: float = Field(..., description="权重（0-1）")
    grade: str = Field(..., description="等级（A/B/C/D/F）")
    description: str = Field(..., description="评分说明")


class HealthScoringResponse(BaseModel):
    """健康评分响应"""
    total_score: float = Field(..., description="总分（0-100）")
    health_grade: str = Field(..., description="健康等级（A/B/C/D/F）")
    health_status: str = Field(..., description="健康状态描述")
    dimension_scores: List[DimensionScore] = Field(..., description="各维度评分详情")
    recommendations: List[str] = Field(..., description="改进建议")
    risk_level: str = Field(..., description="风险等级：低/中/高")


class BatchHealthScoringRequest(BaseModel):
    """批量健康评分请求"""
    devices: Dict[str, dict] = Field(
        ...,
        description="设备数据集，key为设备编码，value为评分数据"
    )
    weights: Optional[Dict[str, float]] = Field(None, description="统一权重配置")


class BatchHealthScoringResponse(BaseModel):
    """批量健康评分响应"""
    results: Dict[str, dict] = Field(..., description="批量评分结果")
    total_devices: int = Field(..., description="处理的设备总数")
    success_count: int = Field(..., description="成功评分的设备数")
    failed_devices: List[str] = Field(default_factory=list, description="失败的设备ID列表")
    statistics: Dict[str, Any] = Field(..., description="统计信息")


class HealthTrendRequest(BaseModel):
    """健康趋势请求"""
    device_code: str = Field(..., description="设备编码")
    days: int = Field(default=30, description="查询天数", ge=1, le=365)


class HealthTrendResponse(BaseModel):
    """健康趋势响应"""
    device_code: str = Field(..., description="设备编码")
    device_name: str = Field(..., description="设备名称")
    trend_data: List[Dict[str, Any]] = Field(..., description="趋势数据")
    average_score: float = Field(..., description="平均得分")
    trend_direction: str = Field(..., description="趋势方向：改善/恶化/稳定")


# ==================== API端点 ====================

@router.post(
    "/score",
    summary="计算设备健康评分",
    description="基于多维度指标计算设备健康状态综合评分",
    response_model=APIResponse[HealthScoringResponse],
    dependencies=[DependAuth]
)
async def calculate_health_score(
    request: HealthScoringRequest,
    current_user=DependAuth
):
    """
    计算设备健康评分
    
    **评分维度**:
    1. **性能指标** (30%): CPU、内存、响应时间等
    2. **异常频率** (30%): 最近的异常次数
    3. **趋势健康** (20%): 数据趋势是否良好
    4. **运行时长** (20%): 连续稳定运行时间
    
    **健康等级**:
    - A (90-100): 优秀，设备运行健康
    - B (80-89): 良好，设备运行正常
    - C (70-79): 一般，需要关注
    - D (60-69): 较差，需要维护
    - F (0-59): 故障，需要紧急处理
    
    **使用场景**:
    - 设备健康状态监控
    - 维护优先级排序
    - 预防性维护决策
    - 设备生命周期管理
    
    **示例**:
    ```json
    {
      "device_code": "WD001",
      "performance_data": {
        "cpu_usage": 75.5,
        "memory_usage": 60.2,
        "response_time": 120.0
      },
      "anomaly_count": 3,
      "uptime_days": 45.5,
      "save_to_db": true
    }
    ```
    """
    try:
        logger.info(
            f"用户 {current_user.username} 请求健康评分，"
            f"设备: {request.device_code}"
        )
        
        # 验证性能数据
        if not request.performance_data:
            raise APIException(
                status_code=400,
                code="INVALID_PERFORMANCE_DATA",
                message="性能数据不能为空"
            )
        
        # 创建健康评分器
        scorer = HealthScorer(weights=request.weights)
        
        # 计算评分
        result = scorer.score(
            performance_data=request.performance_data,
            anomaly_count=request.anomaly_count,
            uptime_days=request.uptime_days,
            historical_data=request.historical_data
        )
        
        # 构建维度评分
        dimension_scores = []
        for dim_name, dim_data in result["dimension_scores"].items():
            dimension_scores.append(DimensionScore(
                dimension=dim_name,
                score=dim_data["score"],
                weight=dim_data["weight"],
                grade=dim_data["grade"],
                description=dim_data.get("description", "")
            ))
        
        # 构建响应
        response = HealthScoringResponse(
            total_score=result["total_score"],
            health_grade=result["health_grade"],
            health_status=result["health_status"],
            dimension_scores=dimension_scores,
            recommendations=result["recommendations"],
            risk_level=result["risk_level"]
        )
        
        # 保存到数据库
        if request.save_to_db:
            try:
                await AIHealthScore.create(
                    device_code=request.device_code,
                    device_name=request.device_name or request.device_code,
                    total_score=result["total_score"],
                    health_grade=result["health_grade"],
                    dimension_scores=result["dimension_scores"],
                    performance_data=request.performance_data,
                    anomaly_count=request.anomaly_count,
                    uptime_days=request.uptime_days,
                    score_time=datetime.now(),
                    recommendations=result["recommendations"]
                )
                logger.info(f"健康评分已保存到数据库，设备: {request.device_code}")
            except Exception as e:
                logger.error(f"保存健康评分失败: {str(e)}", exc_info=True)
                # 不阻止响应，只记录错误
        
        logger.info(
            f"健康评分完成，设备: {request.device_code}, "
            f"总分: {result['total_score']:.2f}, 等级: {result['health_grade']}"
        )
        
        return formatter.success(
            data=response,
            message=f"健康评分完成，等级: {result['health_grade']}, 总分: {result['total_score']:.2f}"
        )
    
    except APIException:
        raise
    except Exception as e:
        logger.error(f"健康评分失败: {str(e)}", exc_info=True)
        raise APIException(
            status_code=500,
            code="HEALTH_SCORING_ERROR",
            message=f"健康评分失败: {str(e)}"
        )


@router.post(
    "/score/batch",
    summary="批量健康评分",
    description="批量计算多个设备的健康评分",
    response_model=APIResponse[BatchHealthScoringResponse],
    dependencies=[DependAuth]
)
async def batch_calculate_health_score(
    request: BatchHealthScoringRequest,
    current_user=DependAuth
):
    """
    批量健康评分
    
    **功能**:
    - 同时处理多个设备的健康评分
    - 自动跳过异常数据
    - 返回统计信息
    
    **使用场景**:
    - 设备群组健康监控
    - 批量设备评估
    - 健康排名统计
    """
    try:
        logger.info(f"用户 {current_user.username} 请求批量健康评分，设备数: {len(request.devices)}")
        
        if not request.devices:
            raise APIException(
                status_code=400,
                code="EMPTY_DATASET",
                message="设备数据集不能为空"
            )
        
        # 创建健康评分器
        scorer = HealthScorer(weights=request.weights)
        
        # 批量评分
        results = {}
        failed_devices = []
        success_count = 0
        grade_distribution = {"A": 0, "B": 0, "C": 0, "D": 0, "F": 0}
        total_scores = []
        
        for device_code, device_data in request.devices.items():
            try:
                # 提取数据
                performance_data = device_data.get("performance_data", {})
                if not performance_data:
                    logger.warning(f"设备 {device_code} 缺少性能数据，跳过")
                    failed_devices.append(device_code)
                    continue
                
                # 计算评分
                result = scorer.score(
                    performance_data=performance_data,
                    anomaly_count=device_data.get("anomaly_count", 0),
                    uptime_days=device_data.get("uptime_days", 0.0),
                    historical_data=device_data.get("historical_data")
                )
                
                results[device_code] = {
                    "total_score": result["total_score"],
                    "health_grade": result["health_grade"],
                    "health_status": result["health_status"],
                    "risk_level": result["risk_level"]
                }
                
                # 统计
                success_count += 1
                grade_distribution[result["health_grade"]] += 1
                total_scores.append(result["total_score"])
                
            except Exception as e:
                logger.error(f"设备 {device_code} 健康评分失败: {str(e)}")
                failed_devices.append(device_code)
                continue
        
        # 计算统计信息
        statistics = {
            "grade_distribution": grade_distribution,
            "average_score": sum(total_scores) / len(total_scores) if total_scores else 0.0,
            "max_score": max(total_scores) if total_scores else 0.0,
            "min_score": min(total_scores) if total_scores else 0.0,
            "healthy_count": grade_distribution["A"] + grade_distribution["B"],  # A和B等级
            "unhealthy_count": grade_distribution["D"] + grade_distribution["F"]  # D和F等级
        }
        
        response = BatchHealthScoringResponse(
            results=results,
            total_devices=len(request.devices),
            success_count=success_count,
            failed_devices=failed_devices,
            statistics=statistics
        )
        
        logger.info(
            f"批量健康评分完成，成功: {success_count}/{len(request.devices)}, "
            f"平均分: {statistics['average_score']:.2f}"
        )
        
        return formatter.success(
            data=response,
            message=f"批量评分完成，成功: {success_count}/{len(request.devices)}"
        )
    
    except APIException:
        raise
    except Exception as e:
        logger.error(f"批量健康评分失败: {str(e)}", exc_info=True)
        raise APIException(
            status_code=500,
            code="BATCH_HEALTH_SCORING_ERROR",
            message=f"批量健康评分失败: {str(e)}"
        )


@router.get(
    "/history",
    summary="获取健康评分历史",
    description="查询设备的历史健康评分记录",
    dependencies=[DependAuth]
)
async def get_health_score_history(
    device_code: Optional[str] = Query(None, description="设备编码"),
    health_grade: Optional[str] = Query(None, description="健康等级（A/B/C/D/F）"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    current_user=DependAuth
):
    """
    获取健康评分历史
    
    **查询条件**:
    - device_code: 按设备编码筛选
    - health_grade: 按健康等级筛选
    
    **返回**: 分页的健康评分记录列表
    """
    try:
        # 构建查询
        query = AIHealthScore.all()
        
        if device_code:
            query = query.filter(device_code=device_code)
        
        if health_grade:
            query = query.filter(health_grade=health_grade)
        
        # 总数
        total = await query.count()
        
        # 分页
        offset = (page - 1) * page_size
        records = await query.offset(offset).limit(page_size).order_by("-score_time")
        
        # 转换为字典
        records_data = []
        for record in records:
            records_data.append({
                "id": record.id,
                "device_code": record.device_code,
                "device_name": record.device_name,
                "total_score": record.total_score,
                "health_grade": record.health_grade,
                "dimension_scores": record.dimension_scores,
                "performance_data": record.performance_data,
                "anomaly_count": record.anomaly_count,
                "uptime_days": record.uptime_days,
                "score_time": record.score_time.isoformat() if record.score_time else None,
                "recommendations": record.recommendations
            })
        
        return formatter.success(
            data={
                "records": records_data,
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": (total + page_size - 1) // page_size
            },
            message=f"成功获取 {len(records_data)} 条健康评分记录"
        )
    
    except Exception as e:
        logger.error(f"获取健康评分历史失败: {str(e)}", exc_info=True)
        raise APIException(
            status_code=500,
            code="GET_HEALTH_HISTORY_ERROR",
            message=f"获取健康评分历史失败: {str(e)}"
        )


@router.get(
    "/trend/{device_code}",
    summary="获取设备健康趋势",
    description="分析设备的健康评分趋势",
    response_model=APIResponse[HealthTrendResponse],
    dependencies=[DependAuth]
)
async def get_health_trend(
    device_code: str,
    days: int = Query(30, description="查询天数", ge=1, le=365),
    current_user=DependAuth
):
    """
    获取设备健康趋势
    
    **功能**:
    - 查询指定天数内的健康评分记录
    - 计算平均得分
    - 分析趋势方向（改善/恶化/稳定）
    
    **使用场景**:
    - 设备健康趋势监控
    - 维护效果评估
    - 长期健康分析
    """
    try:
        # 查询最近N天的评分记录
        from datetime import timedelta
        start_date = datetime.now() - timedelta(days=days)
        
        records = await AIHealthScore.filter(
            device_code=device_code,
            score_time__gte=start_date
        ).order_by("score_time")
        
        if not records:
            raise APIException(
                status_code=404,
                code="NO_RECORDS_FOUND",
                message=f"未找到设备 {device_code} 的健康评分记录"
            )
        
        # 构建趋势数据
        trend_data = []
        scores = []
        for record in records:
            trend_data.append({
                "score_time": record.score_time.isoformat(),
                "total_score": record.total_score,
                "health_grade": record.health_grade
            })
            scores.append(record.total_score)
        
        # 计算平均分
        average_score = sum(scores) / len(scores)
        
        # 分析趋势方向（比较前半段和后半段的平均分）
        mid_point = len(scores) // 2
        first_half_avg = sum(scores[:mid_point]) / mid_point if mid_point > 0 else average_score
        second_half_avg = sum(scores[mid_point:]) / (len(scores) - mid_point) if len(scores) > mid_point else average_score
        
        if second_half_avg > first_half_avg + 5:
            trend_direction = "改善"
        elif second_half_avg < first_half_avg - 5:
            trend_direction = "恶化"
        else:
            trend_direction = "稳定"
        
        response = HealthTrendResponse(
            device_code=device_code,
            device_name=records[0].device_name if records else device_code,
            trend_data=trend_data,
            average_score=round(average_score, 2),
            trend_direction=trend_direction
        )
        
        logger.info(
            f"设备 {device_code} 健康趋势分析完成，"
            f"平均分: {average_score:.2f}, 趋势: {trend_direction}"
        )
        
        return formatter.success(
            data=response,
            message=f"健康趋势分析完成，趋势: {trend_direction}"
        )
    
    except APIException:
        raise
    except Exception as e:
        logger.error(f"获取健康趋势失败: {str(e)}", exc_info=True)
        raise APIException(
            status_code=500,
            code="GET_HEALTH_TREND_ERROR",
            message=f"获取健康趋势失败: {str(e)}"
        )


@router.get(
    "/weights",
    summary="获取默认评分权重",
    description="获取健康评分的默认权重配置",
    dependencies=[DependAuth]
)
async def get_default_weights(current_user=DependAuth):
    """
    获取默认评分权重
    
    **返回**: 各维度的默认权重配置
    """
    try:
        default_weights = {
            "performance": {
                "weight": 0.3,
                "description": "性能指标权重（CPU、内存、响应时间等）"
            },
            "anomaly": {
                "weight": 0.3,
                "description": "异常频率权重（最近的异常次数）"
            },
            "trend": {
                "weight": 0.2,
                "description": "趋势健康权重（数据趋势是否良好）"
            },
            "uptime": {
                "weight": 0.2,
                "description": "运行时长权重（连续稳定运行时间）"
            }
        }
        
        return formatter.success(
            data=default_weights,
            message="成功获取默认权重配置"
        )
    
    except Exception as e:
        logger.error(f"获取默认权重失败: {str(e)}", exc_info=True)
        raise APIException(
            status_code=500,
            code="GET_WEIGHTS_ERROR",
            message=f"获取默认权重失败: {str(e)}"
        )

