#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI健康评分API v2
提供健康评分的CRUD操作、计算评分、配置管理和趋势分析功能
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from fastapi.responses import FileResponse

from app.models.ai_monitoring import AIHealthScore, HealthScoreStatus
from app.schemas.ai_monitoring import (
    HealthScoreCreate, HealthScoreUpdate, HealthScoreResponse,
    HealthScoreConfigUpdate, HealthScoreTrendsResponse,
    AIMonitoringQuery, BatchDeleteRequest, BatchOperationResponse
)
from app.schemas.base import APIResponse, PaginatedResponse
from app.core.response_formatter_v2 import create_formatter
from app.core.pagination import get_pagination_params, create_pagination_response
from app.log import logger


router = APIRouter(prefix="/health-scores/records", tags=["AI健康-记录管理"])


@router.get("", response_model=APIResponse[PaginatedResponse[HealthScoreResponse]])
async def get_health_scores(
    query: AIMonitoringQuery = Depends(),
    pagination: dict = Depends(get_pagination_params),
    target_type: Optional[str] = Query(None, description="评分对象类型过滤"),
    target_id: Optional[int] = Query(None, description="评分对象ID过滤"),
    risk_level: Optional[str] = Query(None, description="风险等级过滤")
):
    """
    获取健康评分列表
    
    支持按评分对象类型、对象ID、风险等级、状态等条件过滤，支持关键词搜索
    """
    try:
        # 构建查询条件
        filters = {}
        
        if query.status:
            filters["status"] = query.status
        
        if target_type:
            filters["target_type"] = target_type
        
        if target_id:
            filters["target_id"] = target_id
        
        if risk_level:
            filters["risk_level"] = risk_level
        
        if query.created_by:
            filters["created_by"] = query.created_by
        
        if query.date_from:
            filters["created_at__gte"] = query.date_from
        
        if query.date_to:
            filters["created_at__lte"] = query.date_to
        
        # 基础查询
        queryset = AIHealthScore.filter(**filters)
        
        # 关键词搜索
        if query.search:
            queryset = queryset.filter(
                score_name__icontains=query.search
            )
        
        # 排序
        queryset = queryset.order_by("-calculated_at", "-created_at")
        
        # 分页查询
        total = await queryset.count()
        scores = await queryset.offset(pagination["offset"]).limit(pagination["limit"])
        
        # 转换为响应模式
        score_responses = []
        for score in scores:
            score_responses.append(HealthScoreResponse(
                id=score.id,
                score_name=score.score_name,
                description=score.description,
                target_type=score.target_type,
                target_id=score.target_id,
                scoring_algorithm=score.scoring_algorithm,
                weight_config=score.weight_config,
                threshold_config=score.threshold_config,
                overall_score=score.overall_score,
                dimension_scores=score.dimension_scores,
                risk_level=score.risk_level,
                status=score.status,
                calculated_at=score.calculated_at,
                data_period_start=score.data_period_start,
                data_period_end=score.data_period_end,
                trend_direction=score.trend_direction,
                trend_confidence=score.trend_confidence,
                created_at=score.created_at,
                updated_at=score.updated_at,
                created_by=score.created_by,
                updated_by=score.updated_by
    
          ))
        
        # 创建分页响应
        paginated_response = create_pagination_response(
            items=score_responses,
            total=total,
            page=pagination["page"],
            page_size=pagination["page_size"]
        )
        
        return response_formatter_v2.success(
            data=paginated_response,
            message="获取健康评分列表成功"
        )
        
    except Exception as e:
        logger.error(f"获取健康评分列表失败: {str(e)}")
        return response_formatter_v2.error(
            message="获取健康评分列表失败",
            details={"error": str(e)}
        )


@router.get("/{score_id}", response_model=APIResponse[HealthScoreResponse])
async def get_health_score(score_id: int):
    """获取健康评分详情"""
    try:
        score = await AIHealthScore.get_or_none(id=score_id)
        if not score:
            return response_formatter_v2.error(
                message="健康评分不存在",
                code=404
            )
        
        score_response = HealthScoreResponse(
            id=score.id,
            score_name=score.score_name,
            description=score.description,
            target_type=score.target_type,
            target_id=score.target_id,
            scoring_algorithm=score.scoring_algorithm,
            weight_config=score.weight_config,
            threshold_config=score.threshold_config,
            overall_score=score.overall_score,
            dimension_scores=score.dimension_scores,
            risk_level=score.risk_level,
            status=score.status,
            calculated_at=score.calculated_at,
            data_period_start=score.data_period_start,
            data_period_end=score.data_period_end,
            trend_direction=score.trend_direction,
            trend_confidence=score.trend_confidence,
            created_at=score.created_at,
            updated_at=score.updated_at,
            created_by=score.created_by,
            updated_by=score.updated_by
        )
        
        return response_formatter_v2.success(
            data=score_response,
            message="获取健康评分详情成功"
        )
        
    except Exception as e:
        logger.error(f"获取健康评分详情失败: score_id={score_id}, 错误: {str(e)}")
        return response_formatter_v2.error(
            message="获取健康评分详情失败",
            details={"error": str(e)}
        )


@router.post("", response_model=APIResponse[HealthScoreResponse])
async def create_health_score(
    score_data: HealthScoreCreate,
    background_tasks: BackgroundTasks,
    current_user_id: int = 1  # TODO: 从认证中获取
):
    """
    创建健康评分
    
    创建后会在后台自动开始计算评分
    """
    try:
        # 创建健康评分记录
        score = await AIHealthScore.create(
            score_name=score_data.score_name,
            description=score_data.description,
            target_type=score_data.target_type,
            target_id=score_data.target_id,
            scoring_algorithm=score_data.scoring_algorithm,
            weight_config=score_data.weight_config,
            threshold_config=score_data.threshold_config,
            data_period_start=score_data.data_period_start,
            data_period_end=score_data.data_period_end,
            status=HealthScoreStatus.CALCULATING,
            created_by=current_user_id,
            updated_by=current_user_id
        )
        
        # 添加后台任务计算评分
        background_tasks.add_task(calculate_health_score_task, score.id)
        
        score_response = HealthScoreResponse(
            id=score.id,
            score_name=score.score_name,
            description=score.description,
            target_type=score.target_type,
            target_id=score.target_id,
            scoring_algorithm=score.scoring_algorithm,
            weight_config=score.weight_config,
            threshold_config=score.threshold_config,
            overall_score=score.overall_score,
            dimension_scores=score.dimension_scores,
            risk_level=score.risk_level,
            status=score.status,
            calculated_at=score.calculated_at,
            data_period_start=score.data_period_start,
            data_period_end=score.data_period_end,
            trend_direction=score.trend_direction,
            trend_confidence=score.trend_confidence,
            created_at=score.created_at,
            updated_at=score.updated_at,
            created_by=score.created_by,
            updated_by=score.updated_by
        )
        
        return response_formatter_v2.success(
            data=score_response,
            message="创建健康评分成功",
            code=201
        )
        
    except Exception as e:
        logger.error(f"创建健康评分失败: {str(e)}")
        return response_formatter_v2.error(
            message="创建健康评分失败",
            details={"error": str(e)}
        )


@router.put("/{score_id}", response_model=APIResponse[HealthScoreResponse])
async def update_health_score(
    score_id: int,
    score_data: HealthScoreUpdate,
    current_user_id: int = 1  # TODO: 从认证中获取
):
    """更新健康评分"""
    try:
        score = await AIHealthScore.get_or_none(id=score_id)
        if not score:
            return response_formatter_v2.error(
                message="健康评分不存在",
                code=404
            )
        
        # 检查是否可以更新（计算中的评分不能更新配置）
        if score.status == HealthScoreStatus.CALCULATING:
            return response_formatter_v2.error(
                message="计算中的评分不能更新配置",
                code=400
            )
        
        # 更新字段
        update_data = score_data.dict(exclude_unset=True)
        if update_data:
            update_data["updated_by"] = current_user_id
            await score.update_from_dict(update_data)
            await score.save()
        
        score_response = HealthScoreResponse(
            id=score.id,
            score_name=score.score_name,
            description=score.description,
            target_type=score.target_type,
            target_id=score.target_id,
            scoring_algorithm=score.scoring_algorithm,
            weight_config=score.weight_config,
            threshold_config=score.threshold_config,
            overall_score=score.overall_score,
            dimension_scores=score.dimension_scores,
            risk_level=score.risk_level,
            status=score.status,
            calculated_at=score.calculated_at,
            data_period_start=score.data_period_start,
            data_period_end=score.data_period_end,
            trend_direction=score.trend_direction,
            trend_confidence=score.trend_confidence,
            created_at=score.created_at,
            updated_at=score.updated_at,
            created_by=score.created_by,
            updated_by=score.updated_by
        )
        
        return response_formatter_v2.success(
            data=score_response,
            message="更新健康评分成功"
        )
        
    except Exception as e:
        logger.error(f"更新健康评分失败: score_id={score_id}, 错误: {str(e)}")
        return response_formatter_v2.error(
            message="更新健康评分失败",
            details={"error": str(e)}
        )


@router.delete("/{score_id}", response_model=APIResponse[dict])
async def delete_health_score(score_id: int):
    """删除健康评分"""
    try:
        score = await AIHealthScore.get_or_none(id=score_id)
        if not score:
            return response_formatter_v2.error(
                message="健康评分不存在",
                code=404
            )
        
        # 检查是否可以删除（计算中的评分需要先取消）
        if score.status == HealthScoreStatus.CALCULATING:
            return response_formatter_v2.error(
                message="请先取消计算中的评分",
                code=400
            )
        
        await score.delete()
        
        return response_formatter_v2.success(
            data={"deleted_id": score_id},
            message="删除健康评分成功"
        )
        
    except Exception as e:
        logger.error(f"删除健康评分失败: score_id={score_id}, 错误: {str(e)}")
        return response_formatter_v2.error(
            message="删除健康评分失败",
            details={"error": str(e)}
        )


@router.get("/export")
async def export_health_report(
    target_type: Optional[str] = Query(None, description="评分对象类型"),
    target_id: Optional[int] = Query(None, description="评分对象ID"),
    date_from: Optional[datetime] = Query(None, description="开始日期"),
    date_to: Optional[datetime] = Query(None, description="结束日期"),
    format: str = Query("excel", description="导出格式: excel, pdf, json")
):
    """导出健康报告"""
    try:
        # 构建查询条件
        filters = {"status": HealthScoreStatus.COMPLETED}
        
        if target_type:
            filters["target_type"] = target_type
        
        if target_id:
            filters["target_id"] = target_id
        
        if date_from:
            filters["calculated_at__gte"] = date_from
        
        if date_to:
            filters["calculated_at__lte"] = date_to
        
        # 查询健康评分数据
        scores = await AIHealthScore.filter(**filters).order_by("-calculated_at")
        
        if not scores:
            raise HTTPException(status_code=400, detail="没有符合条件的健康评分数据")
        
        # 生成导出文件
        file_path = await generate_health_report_file(scores, format)
        
        # 返回文件
        filename = f"health_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{format}"
        return FileResponse(
            path=file_path,
            filename=filename,
            media_type="application/octet-stream"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"导出健康报告失败: {str(e)}")
        raise HTTPException(status_code=500, detail="导出健康报告失败")


@router.put("/config", response_model=APIResponse[dict])
async def update_health_score_config(
    config_data: HealthScoreConfigUpdate,
    current_user_id: int = 1  # TODO: 从认证中获取
):
    """更新健康评分配置"""
    try:
        # TODO: 实现全局健康评分配置更新
        # 这里应该更新系统级别的健康评分配置
        
        return response_formatter_v2.success(
            data={
                "weight_config": config_data.weight_config,
                "threshold_config": config_data.threshold_config,
                "updated_by": current_user_id,
                "updated_at": datetime.now().isoformat()
            },
            message="更新健康评分配置成功"
        )
        
    except Exception as e:
        logger.error(f"更新健康评分配置失败: {str(e)}")
        return response_formatter_v2.error(
            message="更新健康评分配置失败",
            details={"error": str(e)}
        )


@router.get("/trends", response_model=APIResponse[List[HealthScoreTrendsResponse]])
async def get_health_score_trends(
    target_type: str = Query(..., description="评分对象类型"),
    target_ids: Optional[str] = Query(None, description="评分对象ID列表，逗号分隔"),
    period_days: int = Query(30, description="趋势周期天数", ge=1, le=365)
):
    """获取健康评分趋势"""
    try:
        # 解析目标ID列表
        if target_ids:
            target_id_list = [int(id.strip()) for id in target_ids.split(",")]
        else:
            # 获取该类型的所有对象
            target_id_list = await get_target_ids_by_type(target_type)
        
        # 计算时间范围
        end_date = datetime.now()
        start_date = end_date - timedelta(days=period_days)
        
        trends_responses = []
        
        for target_id in target_id_list:
            # 查询该对象的健康评分历史
            scores = await AIHealthScore.filter(
                target_type=target_type,
                target_id=target_id,
                status=HealthScoreStatus.COMPLETED,
                calculated_at__gte=start_date,
                calculated_at__lte=end_date
            ).order_by("calculated_at")
            
            if scores:
                # 构建趋势数据
                trend_data = []
                for score in scores:
                    trend_data.append({
                        "date": score.calculated_at.isoformat(),
                        "overall_score": score.overall_score,
                        "risk_level": score.risk_level,
                        "dimension_scores": score.dimension_scores
                    })
                
                # 计算趋势方向和置信度
                trend_direction, trend_confidence = calculate_trend_direction(
                    [score.overall_score for score in scores]
                )
                
                trends_response = HealthScoreTrendsResponse(
                    target_type=target_type,
                    target_id=target_id,
                    trend_data=trend_data,
                    trend_direction=trend_direction,
                    trend_confidence=trend_confidence,
                    period_start=start_date,
                    period_end=end_date
                )
                
                trends_responses.append(trends_response)
        
        return response_formatter_v2.success(
            data=trends_responses,
            message="获取健康评分趋势成功"
        )
        
    except Exception as e:
        logger.error(f"获取健康评分趋势失败: {str(e)}")
        return response_formatter_v2.error(
            message="获取健康评分趋势失败",
            details={"error": str(e)}
        )


@router.post("/batch-delete", response_model=APIResponse[BatchOperationResponse])
async def batch_delete_health_scores(batch_data: BatchDeleteRequest):
    """批量删除健康评分"""
    try:
        success_count = 0
        failed_count = 0
        failed_ids = []
        errors = []
        
        for score_id in batch_data.ids:
            try:
                score = await AIHealthScore.get_or_none(id=score_id)
                if not score:
                    failed_count += 1
                    failed_ids.append(score_id)
                    errors.append(f"健康评分 {score_id} 不存在")
                    continue
                
                if score.status == HealthScoreStatus.CALCULATING:
                    failed_count += 1
                    failed_ids.append(score_id)
                    errors.append(f"健康评分 {score_id} 正在计算中，无法删除")
                    continue
                
                await score.delete()
                success_count += 1
                
            except Exception as e:
                failed_count += 1
                failed_ids.append(score_id)
                errors.append(f"删除健康评分 {score_id} 失败: {str(e)}")
        
        batch_response = BatchOperationResponse(
            success_count=success_count,
            failed_count=failed_count,
            failed_ids=failed_ids,
            errors=errors
        )
        
        return response_formatter_v2.success(
            data=batch_response,
            message=f"批量删除完成，成功 {success_count} 个，失败 {failed_count} 个"
        )
        
    except Exception as e:
        logger.error(f"批量删除健康评分失败: {str(e)}")
        return response_formatter_v2.error(
            message="批量删除健康评分失败",
            details={"error": str(e)}
        )


# =====================================================
# 后台任务和辅助函数
# =====================================================

async def calculate_health_score_task(score_id: int):
    """计算健康评分任务（后台任务）"""
    try:
        score = await AIHealthScore.get(id=score_id)
        
        # TODO: 实现具体的健康评分计算逻辑
        # 这里应该根据scoring_algorithm、weight_config和threshold_config计算评分
        
        # 模拟计算过程
        import asyncio
        await asyncio.sleep(3)  # 模拟计算时间
        
        # 模拟计算结果
        dimension_scores = {
            "performance": 85.2,
            "reliability": 92.1,
            "efficiency": 78.5,
            "maintenance": 88.9
        }
        
        # 计算总体评分（加权平均）
        weights = score.weight_config
        overall_score = sum(
            dimension_scores[dim] * weights.get(dim, 0.25) 
            for dim in dimension_scores
        )
        
        # 确定风险等级
        thresholds = score.threshold_config
        if overall_score >= thresholds.get("excellent", 90):
            risk_level = "low"
        elif overall_score >= thresholds.get("good", 80):
            risk_level = "medium"
        elif overall_score >= thresholds.get("fair", 70):
            risk_level = "high"
        else:
            risk_level = "critical"
        
        # 更新评分结果
        score.status = HealthScoreStatus.COMPLETED
        score.calculated_at = datetime.now()
        score.overall_score = round(overall_score, 2)
        score.dimension_scores = dimension_scores
        score.risk_level = risk_level
        score.trend_direction = "stable"
        score.trend_confidence = 0.85
        await score.save()
        
        logger.info(f"健康评分计算完成: score_id={score_id}, overall_score={overall_score}")
        
    except Exception as e:
        # 更新状态为失败
        try:
            score = await AIHealthScore.get(id=score_id)
            score.status = HealthScoreStatus.FAILED
            await score.save()
        except:
            pass
        
        logger.error(f"健康评分计算失败: score_id={score_id}, 错误: {str(e)}")


async def generate_health_report_file(scores: list, format: str) -> str:
    """生成健康报告导出文件"""
    import json
    from pathlib import Path
    
    # 创建导出目录
    export_dir = Path("exports/health_reports")
    export_dir.mkdir(parents=True, exist_ok=True)
    
    filename = f"health_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    if format == "json":
        file_path = export_dir / f"{filename}.json"
        
        export_data = {
            "report_info": {
                "title": "健康评分报告",
                "generated_at": datetime.now().isoformat(),
                "total_scores": len(scores)
            },
            "scores": [
                {
                    "id": score.id,
                    "score_name": score.score_name,
                    "target_type": score.target_type,
                    "target_id": score.target_id,
                    "overall_score": score.overall_score,
                    "dimension_scores": score.dimension_scores,
                    "risk_level": score.risk_level,
                    "calculated_at": score.calculated_at.isoformat() if score.calculated_at else None
                }
                for score in scores
            ]
        }
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)
    
    elif format == "excel":
        # TODO: 实现Excel导出
        file_path = export_dir / f"{filename}.xlsx"
        # 这里应该使用openpyxl或pandas实现Excel导出
        pass
    
    elif format == "pdf":
        # TODO: 实现PDF导出
        file_path = export_dir / f"{filename}.pdf"
        # 这里应该使用reportlab或其他PDF库实现PDF导出
        pass
    
    return str(file_path)


async def get_target_ids_by_type(target_type: str) -> List[int]:
    """根据目标类型获取目标ID列表"""
    # TODO: 实现根据目标类型查询目标ID的逻辑
    # 这里应该根据target_type查询相应的数据表
    
    if target_type == "device":
        # 从设备表查询
        return [1, 2, 3, 4, 5]  # 模拟数据
    elif target_type == "system":
        # 从系统表查询
        return [1]  # 模拟数据
    else:
        return []


def calculate_trend_direction(scores: List[float]) -> tuple:
    """计算趋势方向和置信度"""
    if len(scores) < 2:
        return "stable", 0.0
    
    # 简单的线性趋势计算
    n = len(scores)
    x = list(range(n))
    
    # 计算斜率
    x_mean = sum(x) / n
    y_mean = sum(scores) / n
    
    numerator = sum((x[i] - x_mean) * (scores[i] - y_mean) for i in range(n))
    denominator = sum((x[i] - x_mean) ** 2 for i in range(n))
    
    if denominator == 0:
        return "stable", 0.0
    
    slope = numerator / denominator
    
    # 确定趋势方向
    if slope > 0.5:
        direction = "increasing"
    elif slope < -0.5:
        direction = "decreasing"
    else:
        direction = "stable"
    
    # 计算置信度（基于R²）
    y_pred = [x_mean + slope * (x[i] - x_mean) for i in range(n)]
    ss_res = sum((scores[i] - y_pred[i]) ** 2 for i in range(n))
    ss_tot = sum((scores[i] - y_mean) ** 2 for i in range(n))
    
    if ss_tot == 0:
        confidence = 1.0
    else:
        r_squared = 1 - (ss_res / ss_tot)
        confidence = max(0.0, min(1.0, r_squared))
    
    return direction, confidence