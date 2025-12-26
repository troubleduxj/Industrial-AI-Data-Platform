#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI智能分析API v2
提供智能分析的CRUD操作、执行分析、定时分析和结果管理功能
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from fastapi.responses import FileResponse

from app.models.ai_monitoring import AIAnalysis, AnalysisStatus
from app.schemas.ai_monitoring import (
    AnalysisCreate, AnalysisUpdate, AnalysisResponse,
    AnalysisScheduleRequest, AnalysisResultsResponse,
    AIMonitoringQuery, BatchDeleteRequest, BatchOperationResponse
)
from app.schemas.base import APIResponse, PaginatedResponse
from app.core.response_formatter_v2 import create_formatter
from app.core.pagination import get_pagination_params, create_pagination_response
from app.log import logger


router = APIRouter(prefix="/analysis", tags=["AI智能分析"])


@router.get("", response_model=APIResponse[PaginatedResponse[AnalysisResponse]])
async def get_analysis_list(
    query: AIMonitoringQuery = Depends(),
    pagination: dict = Depends(get_pagination_params),
    analysis_type: Optional[str] = Query(None, description="分析类型过滤"),
    algorithm: Optional[str] = Query(None, description="算法过滤"),
    is_scheduled: Optional[bool] = Query(None, description="是否定时分析过滤")
):
    """
    获取智能分析列表
    
    支持按分析类型、算法、状态、是否定时等条件过滤，支持关键词搜索
    """
    try:
        # 构建查询条件
        filters = {}
        
        if query.status:
            filters["status"] = query.status
        
        if analysis_type:
            filters["analysis_type"] = analysis_type
        
        if algorithm:
            filters["algorithm"] = algorithm
        
        if is_scheduled is not None:
            filters["is_scheduled"] = is_scheduled
        
        if query.created_by:
            filters["created_by"] = query.created_by
        
        if query.date_from:
            filters["created_at__gte"] = query.date_from
        
        if query.date_to:
            filters["created_at__lte"] = query.date_to
        
        # 基础查询
        queryset = AIAnalysis.filter(**filters)
        
        # 关键词搜索
        if query.search:
            queryset = queryset.filter(
                analysis_name__icontains=query.search
            )
        
        # 排序
        queryset = queryset.order_by("-created_at")
        
        # 分页查询
        total = await queryset.count()
        analyses = await queryset.offset(pagination["offset"]).limit(pagination["limit"])
        
        # 转换为响应模式
        analysis_responses = []
        for analysis in analyses:
            analysis_responses.append(AnalysisResponse(
                id=analysis.id,
                analysis_name=analysis.analysis_name,
                description=analysis.description,
                analysis_type=analysis.analysis_type,
                algorithm=analysis.algorithm,
                parameters=analysis.parameters,
                data_sources=analysis.data_sources,
                data_filters=analysis.data_filters,
                status=analysis.status,
                progress=analysis.progress,
                result_data=analysis.result_data,
                insights=analysis.insights,
                recommendations=analysis.recommendations,
                started_at=analysis.started_at,
                completed_at=analysis.completed_at,
                error_message=analysis.error_message,
                is_scheduled=analysis.is_scheduled,
                schedule_config=analysis.schedule_config,
                next_run_at=analysis.next_run_at,
                created_at=analysis.created_at,
                updated_at=analysis.updated_at,
                created_by=analysis.created_by,
                updated_by=analysis.updated_by
            ))
        
        # 创建分页响应
        paginated_response = create_pagination_response(
            items=analysis_responses,
            total=total,
            page=pagination["page"],
            page_size=pagination["page_size"]
        )
        
        return response_formatter_v2.success(
            data=paginated_response,
            message="获取智能分析列表成功"
        )
        
    except Exception as e:
        logger.error(f"获取智能分析列表失败: {str(e)}")
        return response_formatter_v2.error(
            message="获取智能分析列表失败",
            details={"error": str(e)}
        )


@router.get("/{analysis_id}", response_model=APIResponse[AnalysisResponse])
async def get_analysis(analysis_id: int):
    """获取智能分析详情"""
    try:
        analysis = await AIAnalysis.get_or_none(id=analysis_id)
        if not analysis:
            return response_formatter_v2.error(
                message="智能分析不存在",
                code=404
            )
        
        analysis_response = AnalysisResponse(
            id=analysis.id,
            analysis_name=analysis.analysis_name,
            description=analysis.description,
            analysis_type=analysis.analysis_type,
            algorithm=analysis.algorithm,
            parameters=analysis.parameters,
            data_sources=analysis.data_sources,
            data_filters=analysis.data_filters,
            status=analysis.status,
            progress=analysis.progress,
            result_data=analysis.result_data,
            insights=analysis.insights,
            recommendations=analysis.recommendations,
            started_at=analysis.started_at,
            completed_at=analysis.completed_at,
            error_message=analysis.error_message,
            is_scheduled=analysis.is_scheduled,
            schedule_config=analysis.schedule_config,
            next_run_at=analysis.next_run_at,
            created_at=analysis.created_at,
            updated_at=analysis.updated_at,
            created_by=analysis.created_by,
            updated_by=analysis.updated_by
        )
        
        return response_formatter_v2.success(
            data=analysis_response,
            message="获取智能分析详情成功"
        )
        
    except Exception as e:
        logger.error(f"获取智能分析详情失败: analysis_id={analysis_id}, 错误: {str(e)}")
        return response_formatter_v2.error(
            message="获取智能分析详情失败",
            details={"error": str(e)}
        )


@router.post("", response_model=APIResponse[AnalysisResponse])
async def create_analysis(
    analysis_data: AnalysisCreate,
    background_tasks: BackgroundTasks,
    current_user_id: int = 1  # TODO: 从认证中获取
):
    """
    创建智能分析
    
    创建后会在后台自动开始执行分析
    """
    try:
        # 创建智能分析记录
        analysis = await AIAnalysis.create(
            analysis_name=analysis_data.analysis_name,
            description=analysis_data.description,
            analysis_type=analysis_data.analysis_type,
            algorithm=analysis_data.algorithm,
            parameters=analysis_data.parameters,
            data_sources=analysis_data.data_sources,
            data_filters=analysis_data.data_filters,
            status=AnalysisStatus.PENDING,
            progress=0,
            created_by=current_user_id,
            updated_by=current_user_id
        )
        
        # 添加后台任务执行分析
        background_tasks.add_task(execute_analysis_task, analysis.id)
        
        analysis_response = AnalysisResponse(
            id=analysis.id,
            analysis_name=analysis.analysis_name,
            description=analysis.description,
            analysis_type=analysis.analysis_type,
            algorithm=analysis.algorithm,
            parameters=analysis.parameters,
            data_sources=analysis.data_sources,
            data_filters=analysis.data_filters,
            status=analysis.status,
            progress=analysis.progress,
            result_data=analysis.result_data,
            insights=analysis.insights,
            recommendations=analysis.recommendations,
            started_at=analysis.started_at,
            completed_at=analysis.completed_at,
            error_message=analysis.error_message,
            is_scheduled=analysis.is_scheduled,
            schedule_config=analysis.schedule_config,
            next_run_at=analysis.next_run_at,
            created_at=analysis.created_at,
            updated_at=analysis.updated_at,
            created_by=analysis.created_by,
            updated_by=analysis.updated_by
        )
        
        return response_formatter_v2.success(
            data=analysis_response,
            message="创建智能分析成功",
            code=201
        )
        
    except Exception as e:
        logger.error(f"创建智能分析失败: {str(e)}")
        return response_formatter_v2.error(
            message="创建智能分析失败",
            details={"error": str(e)}
        )


@router.put("/{analysis_id}", response_model=APIResponse[AnalysisResponse])
async def update_analysis(
    analysis_id: int,
    analysis_data: AnalysisUpdate,
    current_user_id: int = 1  # TODO: 从认证中获取
):
    """更新智能分析配置"""
    try:
        analysis = await AIAnalysis.get_or_none(id=analysis_id)
        if not analysis:
            return response_formatter_v2.error(
                message="智能分析不存在",
                code=404
            )
        
        # 检查是否可以更新（运行中的分析不能更新配置）
        if analysis.status == AnalysisStatus.RUNNING:
            return response_formatter_v2.error(
                message="运行中的分析不能更新配置",
                code=400
            )
        
        # 更新字段
        update_data = analysis_data.dict(exclude_unset=True)
        if update_data:
            update_data["updated_by"] = current_user_id
            await analysis.update_from_dict(update_data)
            await analysis.save()
        
        analysis_response = AnalysisResponse(
            id=analysis.id,
            analysis_name=analysis.analysis_name,
            description=analysis.description,
            analysis_type=analysis.analysis_type,
            algorithm=analysis.algorithm,
            parameters=analysis.parameters,
            data_sources=analysis.data_sources,
            data_filters=analysis.data_filters,
            status=analysis.status,
            progress=analysis.progress,
            result_data=analysis.result_data,
            insights=analysis.insights,
            recommendations=analysis.recommendations,
            started_at=analysis.started_at,
            completed_at=analysis.completed_at,
            error_message=analysis.error_message,
            is_scheduled=analysis.is_scheduled,
            schedule_config=analysis.schedule_config,
            next_run_at=analysis.next_run_at,
            created_at=analysis.created_at,
            updated_at=analysis.updated_at,
            created_by=analysis.created_by,
            updated_by=analysis.updated_by
        )
        
        return response_formatter_v2.success(
            data=analysis_response,
            message="更新智能分析配置成功"
        )
        
    except Exception as e:
        logger.error(f"更新智能分析配置失败: analysis_id={analysis_id}, 错误: {str(e)}")
        return response_formatter_v2.error(
            message="更新智能分析配置失败",
            details={"error": str(e)}
        )


@router.delete("/{analysis_id}", response_model=APIResponse[dict])
async def delete_analysis(analysis_id: int):
    """删除智能分析"""
    try:
        analysis = await AIAnalysis.get_or_none(id=analysis_id)
        if not analysis:
            return response_formatter_v2.error(
                message="智能分析不存在",
                code=404
            )
        
        # 检查是否可以删除（运行中的分析需要先取消）
        if analysis.status == AnalysisStatus.RUNNING:
            return response_formatter_v2.error(
                message="请先取消运行中的分析",
                code=400
            )
        
        await analysis.delete()
        
        return response_formatter_v2.success(
            data={"deleted_id": analysis_id},
            message="删除智能分析成功"
        )
        
    except Exception as e:
        logger.error(f"删除智能分析失败: analysis_id={analysis_id}, 错误: {str(e)}")
        return response_formatter_v2.error(
            message="删除智能分析失败",
            details={"error": str(e)}
        )


@router.get("/{analysis_id}/results", response_model=APIResponse[AnalysisResultsResponse])
async def get_analysis_results(analysis_id: int):
    """获取分析结果"""
    try:
        analysis = await AIAnalysis.get_or_none(id=analysis_id)
        if not analysis:
            return response_formatter_v2.error(
                message="智能分析不存在",
                code=404
            )
        
        if analysis.status != AnalysisStatus.COMPLETED:
            return response_formatter_v2.error(
                message="分析未完成，无法获取结果",
                code=400
            )
        
        if not analysis.result_data:
            return response_formatter_v2.error(
                message="分析结果为空",
                code=400
            )
        
        results_response = AnalysisResultsResponse(
            analysis_id=analysis.id,
            analysis_name=analysis.analysis_name,
            result_data=analysis.result_data,
            insights=analysis.insights or {},
            recommendations=analysis.recommendations or {},
            completed_at=analysis.completed_at
        )
        
        return response_formatter_v2.success(
            data=results_response,
            message="获取分析结果成功"
        )
        
    except Exception as e:
        logger.error(f"获取分析结果失败: analysis_id={analysis_id}, 错误: {str(e)}")
        return response_formatter_v2.error(
            message="获取分析结果失败",
            details={"error": str(e)}
        )


@router.post("/{analysis_id}/schedule", response_model=APIResponse[dict])
async def schedule_analysis(
    analysis_id: int,
    schedule_data: AnalysisScheduleRequest,
    current_user_id: int = 1  # TODO: 从认证中获取
):
    """设置定时分析"""
    try:
        analysis = await AIAnalysis.get_or_none(id=analysis_id)
        if not analysis:
            return response_formatter_v2.error(
                message="智能分析不存在",
                code=404
            )
        
        # 计算下次运行时间
        next_run_at = calculate_next_run_time(schedule_data.schedule_config)
        
        # 更新定时配置
        analysis.is_scheduled = schedule_data.is_enabled
        analysis.schedule_config = schedule_data.schedule_config
        analysis.next_run_at = next_run_at if schedule_data.is_enabled else None
        analysis.updated_by = current_user_id
        await analysis.save()
        
        # TODO: 注册到定时任务调度器
        
        return response_formatter_v2.success(
            data={
                "analysis_id": analysis_id,
                "is_scheduled": schedule_data.is_enabled,
                "schedule_config": schedule_data.schedule_config,
                "next_run_at": next_run_at.isoformat() if next_run_at else None
            },
            message="设置定时分析成功"
        )
        
    except Exception as e:
        logger.error(f"设置定时分析失败: analysis_id={analysis_id}, 错误: {str(e)}")
        return response_formatter_v2.error(
            message="设置定时分析失败",
            details={"error": str(e)}
        )


@router.post("/batch-delete", response_model=APIResponse[BatchOperationResponse])
async def batch_delete_analyses(batch_data: BatchDeleteRequest):
    """批量删除智能分析"""
    try:
        success_count = 0
        failed_count = 0
        failed_ids = []
        errors = []
        
        for analysis_id in batch_data.ids:
            try:
                analysis = await AIAnalysis.get_or_none(id=analysis_id)
                if not analysis:
                    failed_count += 1
                    failed_ids.append(analysis_id)
                    errors.append(f"智能分析 {analysis_id} 不存在")
                    continue
                
                if analysis.status == AnalysisStatus.RUNNING:
                    failed_count += 1
                    failed_ids.append(analysis_id)
                    errors.append(f"智能分析 {analysis_id} 正在运行中，无法删除")
                    continue
                
                await analysis.delete()
                success_count += 1
                
            except Exception as e:
                failed_count += 1
                failed_ids.append(analysis_id)
                errors.append(f"删除智能分析 {analysis_id} 失败: {str(e)}")
        
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
        logger.error(f"批量删除智能分析失败: {str(e)}")
        return response_formatter_v2.error(
            message="批量删除智能分析失败",
            details={"error": str(e)}
        )


# =====================================================
# 后台任务和辅助函数
# =====================================================

async def execute_analysis_task(analysis_id: int):
    """执行智能分析任务（后台任务）"""
    try:
        analysis = await AIAnalysis.get(id=analysis_id)
        
        # 更新状态为运行中
        analysis.status = AnalysisStatus.RUNNING
        analysis.started_at = datetime.now()
        analysis.progress = 0
        await analysis.save()
        
        # TODO: 实现具体的智能分析算法
        # 这里应该根据analysis_type和algorithm执行相应的分析算法
        
        # 模拟分析过程
        import asyncio
        for progress in range(0, 101, 20):
            analysis.progress = progress
            await analysis.save()
            await asyncio.sleep(1)  # 模拟计算时间
        
        # 模拟分析结果
        result_data = {
            "summary": {
                "total_data_points": 10000,
                "analysis_duration": "5 minutes",
                "confidence_score": 0.87
            },
            "patterns": [
                {
                    "pattern_type": "trend",
                    "description": "设备温度呈上升趋势",
                    "confidence": 0.92,
                    "time_range": "2024-01-01 to 2024-01-07"
                },
                {
                    "pattern_type": "anomaly",
                    "description": "检测到3个异常数据点",
                    "confidence": 0.85,
                    "locations": ["2024-01-03 14:30", "2024-01-05 09:15", "2024-01-06 16:45"]
                }
            ],
            "metrics": {
                "accuracy": 0.89,
                "precision": 0.91,
                "recall": 0.87,
                "f1_score": 0.89
            }
        }
        
        insights = {
            "key_findings": [
                "设备运行温度在过去一周内平均上升了5.2°C",
                "异常事件主要集中在下午时段",
                "设备效率与温度变化呈负相关关系"
            ],
            "risk_assessment": {
                "overall_risk": "medium",
                "risk_factors": [
                    {"factor": "温度上升", "impact": "high", "probability": 0.8},
                    {"factor": "异常频率", "impact": "medium", "probability": 0.6}
                ]
            }
        }
        
        recommendations = {
            "immediate_actions": [
                "检查设备冷却系统",
                "调整运行参数以降低温度",
                "增加异常时段的监控频率"
            ],
            "long_term_strategies": [
                "制定预防性维护计划",
                "考虑设备升级或更换",
                "建立温度预警机制"
            ],
            "priority_level": "high"
        }
        
        # 更新分析结果
        analysis.status = AnalysisStatus.COMPLETED
        analysis.completed_at = datetime.now()
        analysis.progress = 100
        analysis.result_data = result_data
        analysis.insights = insights
        analysis.recommendations = recommendations
        await analysis.save()
        
        logger.info(f"智能分析任务完成: analysis_id={analysis_id}")
        
    except Exception as e:
        # 更新状态为失败
        try:
            analysis = await AIAnalysis.get(id=analysis_id)
            analysis.status = AnalysisStatus.FAILED
            analysis.error_message = str(e)
            await analysis.save()
        except:
            pass
        
        logger.error(f"智能分析任务失败: analysis_id={analysis_id}, 错误: {str(e)}")


def calculate_next_run_time(schedule_config: Dict[str, Any]) -> Optional[datetime]:
    """计算下次运行时间"""
    try:
        schedule_type = schedule_config.get("type", "once")
        
        if schedule_type == "once":
            # 一次性任务
            run_time = schedule_config.get("run_time")
            if run_time:
                return datetime.fromisoformat(run_time)
        
        elif schedule_type == "daily":
            # 每日任务
            hour = schedule_config.get("hour", 0)
            minute = schedule_config.get("minute", 0)
            
            now = datetime.now()
            next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            
            # 如果今天的时间已过，则安排到明天
            if next_run <= now:
                next_run += timedelta(days=1)
            
            return next_run
        
        elif schedule_type == "weekly":
            # 每周任务
            weekday = schedule_config.get("weekday", 0)  # 0=Monday
            hour = schedule_config.get("hour", 0)
            minute = schedule_config.get("minute", 0)
            
            now = datetime.now()
            days_ahead = weekday - now.weekday()
            
            if days_ahead <= 0:  # 目标日期已过或是今天
                days_ahead += 7
            
            next_run = now + timedelta(days=days_ahead)
            next_run = next_run.replace(hour=hour, minute=minute, second=0, microsecond=0)
            
            return next_run
        
        elif schedule_type == "monthly":
            # 每月任务
            day = schedule_config.get("day", 1)
            hour = schedule_config.get("hour", 0)
            minute = schedule_config.get("minute", 0)
            
            now = datetime.now()
            
            # 尝试当月
            try:
                next_run = now.replace(day=day, hour=hour, minute=minute, second=0, microsecond=0)
                if next_run <= now:
                    # 当月时间已过，安排到下月
                    if now.month == 12:
                        next_run = next_run.replace(year=now.year + 1, month=1)
                    else:
                        next_run = next_run.replace(month=now.month + 1)
            except ValueError:
                # 日期无效（如2月30日），安排到下月1日
                if now.month == 12:
                    next_run = datetime(now.year + 1, 1, day, hour, minute)
                else:
                    next_run = datetime(now.year, now.month + 1, day, hour, minute)
            
            return next_run
        
        return None
        
    except Exception as e:
        logger.error(f"计算下次运行时间失败: {str(e)}")
        return None