#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI趋势预测API v2
提供趋势预测的CRUD操作、执行预测、导出报告和分享功能
"""

from typing import List, Optional, Dict, Any
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from fastapi.responses import FileResponse

from app.models.ai_monitoring import AIPrediction, PredictionStatus
from app.schemas.ai_monitoring import (
    PredictionCreate, PredictionUpdate, PredictionResponse,
    PredictionShareRequest, AIMonitoringQuery, BatchDeleteRequest, BatchOperationResponse,
    BatchPredictionCreate, BatchPredictionResponse, PredictionHistoryQuery
)
from app.schemas.base import APIResponse, PaginatedResponse
from app.core.response_formatter_v2 import create_formatter
from app.core.pagination import get_pagination_params, create_pagination_response
from app.log import logger


router = APIRouter(prefix="/predictions/tasks", tags=["AI预测-任务管理"])
response_formatter_v2 = create_formatter()


@router.get("", response_model=APIResponse[PaginatedResponse[PredictionResponse]])
async def get_predictions(
    query: AIMonitoringQuery = Depends(),
    pagination: dict = Depends(get_pagination_params)
):
    """
    获取预测列表
    
    支持按状态、创建人、日期范围等条件过滤，支持关键词搜索
    """
    try:
        # 构建查询条件
        filters = {}
        
        if query.status:
            filters["status"] = query.status
        
        if query.created_by:
            filters["created_by"] = query.created_by
        
        if query.date_from:
            filters["created_at__gte"] = query.date_from
        
        if query.date_to:
            filters["created_at__lte"] = query.date_to
        
        # 基础查询
        queryset = AIPrediction.filter(**filters)
        
        # 关键词搜索
        if query.search:
            queryset = queryset.filter(
                prediction_name__icontains=query.search
            )
        
        # 排序
        queryset = queryset.order_by("-created_at")
        
        # 分页查询
        total = await queryset.count()
        predictions = await queryset.offset(pagination["offset"]).limit(pagination["limit"])
        
        # 转换为响应模式
        prediction_responses = []
        for prediction in predictions:
            prediction_responses.append(PredictionResponse(
                id=prediction.id,
                prediction_name=prediction.prediction_name,
                description=prediction.description,
                target_variable=prediction.target_variable,
                prediction_horizon=prediction.prediction_horizon,
                model_type=prediction.model_type,
                parameters=prediction.parameters,
                data_source=prediction.data_source,
                data_filters=prediction.data_filters,
                status=prediction.status,
                progress=prediction.progress,
                result_data=prediction.result_data,
                accuracy_score=prediction.accuracy_score,
                confidence_interval=prediction.confidence_interval,
                started_at=prediction.started_at,
                completed_at=prediction.completed_at,
                error_message=prediction.error_message,
                export_formats=prediction.export_formats,
                shared_with=prediction.shared_with,
                is_public=prediction.is_public,
                created_at=prediction.created_at,
                updated_at=prediction.updated_at,
                created_by=prediction.created_by,
                updated_by=prediction.updated_by
            ))
        
        # 创建分页响应
        paginated_response = create_pagination_response(
            items=prediction_responses,
            total=total,
            page=pagination["page"],
            page_size=pagination["page_size"]
        )
        
        return response_formatter_v2.success(
            data=paginated_response,
            message="获取预测列表成功"
        )
        
    except Exception as e:
        logger.error(f"获取预测列表失败: {str(e)}")
        return response_formatter_v2.error(
            message="获取预测列表失败",
            details={"error": str(e)}
        )


@router.get("/{prediction_id}", response_model=APIResponse[PredictionResponse])
async def get_prediction(prediction_id: int):
    """获取预测详情"""
    try:
        prediction = await AIPrediction.get_or_none(id=prediction_id)
        if not prediction:
            return response_formatter_v2.error(
                message="预测不存在",
                code=404
            )
        
        prediction_response = PredictionResponse(
            id=prediction.id,
            prediction_name=prediction.prediction_name,
            description=prediction.description,
            target_variable=prediction.target_variable,
            prediction_horizon=prediction.prediction_horizon,
            model_type=prediction.model_type,
            parameters=prediction.parameters,
            data_source=prediction.data_source,
            data_filters=prediction.data_filters,
            status=prediction.status,
            progress=prediction.progress,
            result_data=prediction.result_data,
            accuracy_score=prediction.accuracy_score,
            confidence_interval=prediction.confidence_interval,
            started_at=prediction.started_at,
            completed_at=prediction.completed_at,
            error_message=prediction.error_message,
            export_formats=prediction.export_formats,
            shared_with=prediction.shared_with,
            is_public=prediction.is_public,
            created_at=prediction.created_at,
            updated_at=prediction.updated_at,
            created_by=prediction.created_by,
            updated_by=prediction.updated_by
        )
        
        return response_formatter_v2.success(
            data=prediction_response,
            message="获取预测详情成功"
        )
        
    except Exception as e:
        logger.error(f"获取预测详情失败: prediction_id={prediction_id}, 错误: {str(e)}")
        return response_formatter_v2.error(
            message="获取预测详情失败",
            details={"error": str(e)}
        )


@router.post("", response_model=APIResponse[PredictionResponse])
async def create_prediction(
    prediction_data: PredictionCreate,
    background_tasks: BackgroundTasks,
    current_user_id: int = 1  # TODO: 从认证中获取
):
    """
    创建预测任务
    
    创建后会在后台自动开始执行预测
    """
    try:
        # 创建预测记录
        prediction = await AIPrediction.create(
            prediction_name=prediction_data.prediction_name,
            description=prediction_data.description,
            target_variable=prediction_data.target_variable,
            prediction_horizon=prediction_data.prediction_horizon,
            model_type=prediction_data.model_type,
            parameters=prediction_data.parameters,
            data_source=prediction_data.data_source,
            data_filters=prediction_data.data_filters,
            status=PredictionStatus.PENDING,
            progress=0,
            export_formats=["json", "csv", "excel"],
            created_by=current_user_id,
            updated_by=current_user_id
        )
        
        # 添加后台任务执行预测
        background_tasks.add_task(execute_prediction_task, prediction.id)
        
        prediction_response = PredictionResponse(
            id=prediction.id,
            prediction_name=prediction.prediction_name,
            description=prediction.description,
            target_variable=prediction.target_variable,
            prediction_horizon=prediction.prediction_horizon,
            model_type=prediction.model_type,
            parameters=prediction.parameters,
            data_source=prediction.data_source,
            data_filters=prediction.data_filters,
            status=prediction.status,
            progress=prediction.progress,
            result_data=prediction.result_data,
            accuracy_score=prediction.accuracy_score,
            confidence_interval=prediction.confidence_interval,
            started_at=prediction.started_at,
            completed_at=prediction.completed_at,
            error_message=prediction.error_message,
            export_formats=prediction.export_formats,
            shared_with=prediction.shared_with,
            is_public=prediction.is_public,
            created_at=prediction.created_at,
            updated_at=prediction.updated_at,
            created_by=prediction.created_by,
            updated_by=prediction.updated_by
        )
        
        return response_formatter_v2.success(
            data=prediction_response,
            message="创建预测任务成功",
            code=201
        )
        
    except Exception as e:
        logger.error(f"创建预测任务失败: {str(e)}")
        return response_formatter_v2.error(
            message="创建预测任务失败",
            details={"error": str(e)}
        )


@router.put("/{prediction_id}", response_model=APIResponse[PredictionResponse])
async def update_prediction(
    prediction_id: int,
    prediction_data: PredictionUpdate,
    current_user_id: int = 1  # TODO: 从认证中获取
):
    """更新预测配置"""
    try:
        prediction = await AIPrediction.get_or_none(id=prediction_id)
        if not prediction:
            return response_formatter_v2.error(
                message="预测不存在",
                code=404
            )
        
        # 检查是否可以更新（运行中的预测不能更新配置）
        if prediction.status == PredictionStatus.RUNNING:
            return response_formatter_v2.error(
                message="运行中的预测不能更新配置",
                code=400
            )
        
        # 更新字段
        update_data = prediction_data.dict(exclude_unset=True)
        if update_data:
            update_data["updated_by"] = current_user_id
            await prediction.update_from_dict(update_data)
            await prediction.save()
        
        prediction_response = PredictionResponse(
            id=prediction.id,
            prediction_name=prediction.prediction_name,
            description=prediction.description,
            target_variable=prediction.target_variable,
            prediction_horizon=prediction.prediction_horizon,
            model_type=prediction.model_type,
            parameters=prediction.parameters,
            data_source=prediction.data_source,
            data_filters=prediction.data_filters,
            status=prediction.status,
            progress=prediction.progress,
            result_data=prediction.result_data,
            accuracy_score=prediction.accuracy_score,
            confidence_interval=prediction.confidence_interval,
            started_at=prediction.started_at,
            completed_at=prediction.completed_at,
            error_message=prediction.error_message,
            export_formats=prediction.export_formats,
            shared_with=prediction.shared_with,
            is_public=prediction.is_public,
            created_at=prediction.created_at,
            updated_at=prediction.updated_at,
            created_by=prediction.created_by,
            updated_by=prediction.updated_by
        )
        
        return response_formatter_v2.success(
            data=prediction_response,
            message="更新预测配置成功"
        )
        
    except Exception as e:
        logger.error(f"更新预测配置失败: prediction_id={prediction_id}, 错误: {str(e)}")
        return response_formatter_v2.error(
            message="更新预测配置失败",
            details={"error": str(e)}
        )


@router.delete("/{prediction_id}", response_model=APIResponse[dict])
async def delete_prediction(prediction_id: int):
    """删除预测"""
    try:
        prediction = await AIPrediction.get_or_none(id=prediction_id)
        if not prediction:
            return response_formatter_v2.error(
                message="预测不存在",
                code=404
            )
        
        # 检查是否可以删除（运行中的预测需要先取消）
        if prediction.status == PredictionStatus.RUNNING:
            return response_formatter_v2.error(
                message="请先取消运行中的预测",
                code=400
            )
        
        await prediction.delete()
        
        return response_formatter_v2.success(
            data={"deleted_id": prediction_id},
            message="删除预测成功"
        )
        
    except Exception as e:
        logger.error(f"删除预测失败: prediction_id={prediction_id}, 错误: {str(e)}")
        return response_formatter_v2.error(
            message="删除预测失败",
            details={"error": str(e)}
        )


@router.get("/{prediction_id}/export")
async def export_prediction_report(
    prediction_id: int,
    format: str = Query("json", description="导出格式: json, csv, excel")
):
    """导出预测报告"""
    try:
        prediction = await AIPrediction.get_or_none(id=prediction_id)
        if not prediction:
            raise HTTPException(status_code=404, detail="预测不存在")
        
        if prediction.status != PredictionStatus.COMPLETED:
            raise HTTPException(status_code=400, detail="预测未完成，无法导出")
        
        if not prediction.result_data:
            raise HTTPException(status_code=400, detail="预测结果为空，无法导出")
        
        # 生成导出文件
        file_path = await generate_prediction_export_file(prediction, format)
        
        # 返回文件
        filename = f"prediction_{prediction_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{format}"
        return FileResponse(
            path=file_path,
            filename=filename,
            media_type="application/octet-stream"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"导出预测报告失败: prediction_id={prediction_id}, 错误: {str(e)}")
        raise HTTPException(status_code=500, detail="导出预测报告失败")


@router.post("/{prediction_id}/share", response_model=APIResponse[dict])
async def share_prediction(
    prediction_id: int,
    share_data: PredictionShareRequest,
    current_user_id: int = 1  # TODO: 从认证中获取
):
    """分享预测结果"""
    try:
        prediction = await AIPrediction.get_or_none(id=prediction_id)
        if not prediction:
            return response_formatter_v2.error(
                message="预测不存在",
                code=404
            )
        
        if prediction.status != PredictionStatus.COMPLETED:
            return response_formatter_v2.error(
                message="预测未完成，无法分享",
                code=400
            )
        
        # 更新分享设置
        prediction.shared_with = share_data.user_ids
        prediction.is_public = share_data.is_public
        prediction.updated_by = current_user_id
        await prediction.save()
        
        # TODO: 发送分享通知给相关用户
        
        return response_formatter_v2.success(
            data={
                "shared_with": share_data.user_ids,
                "is_public": share_data.is_public,
                "message": share_data.message
            },
            message="分享预测结果成功"
        )
        
    except Exception as e:
        logger.error(f"分享预测结果失败: prediction_id={prediction_id}, 错误: {str(e)}")
        return response_formatter_v2.error(
            message="分享预测结果失败",
            details={"error": str(e)}
        )


@router.post("/batch", response_model=APIResponse[BatchPredictionResponse])
async def create_batch_predictions(
    batch_data: BatchPredictionCreate,
    background_tasks: BackgroundTasks,
    current_user_id: int = 1  # TODO: 从认证中获取
):
    """
    批量创建预测任务并执行
    
    为多个设备批量创建预测任务，自动在后台执行预测
    
    Args:
        batch_data: 批量预测请求数据
            - device_codes: 设备代码列表
            - metric_name: 指标名称（如temperature）
            - prediction_horizon: 预测时间范围（小时）
            - model_type: 预测模型类型
    """
    try:
        predictions = []
        failed_devices = []
        
        for device_code in batch_data.device_codes:
            try:
                # 创建预测记录
                prediction = await AIPrediction.create(
                    prediction_name=f"{device_code}-{batch_data.metric_name}-预测-{batch_data.prediction_horizon}h",
                    description=f"设备{device_code}的{batch_data.metric_name}指标{batch_data.prediction_horizon}小时预测",
                    target_variable=batch_data.metric_name,
                    prediction_horizon=batch_data.prediction_horizon,
                    model_type=batch_data.model_type,
                    parameters=batch_data.parameters or {},
                    data_source="t_device_realtime_data",
                    data_filters={
                        "device_code": device_code,
                        "metric_name": batch_data.metric_name,
                        "time_range": f"{batch_data.prediction_horizon}h"
                    },
                    status=PredictionStatus.PENDING,
                    progress=0,
                    export_formats=["json", "csv", "excel"],
                    created_by=current_user_id,
                    updated_by=current_user_id
                )
                
                # 添加后台任务执行预测
                background_tasks.add_task(execute_prediction_task, prediction.id)
                
                # 转换为响应格式
                prediction_response = PredictionResponse.from_orm_with_filters(prediction)
                predictions.append(prediction_response)
                
            except Exception as e:
                logger.error(f"创建设备 {device_code} 的预测任务失败: {str(e)}")
                failed_devices.append(device_code)
                continue
        
        batch_response = BatchPredictionResponse(
            predictions=predictions,
            total=len(batch_data.device_codes),
            successful=len(predictions),
            failed=len(failed_devices),
            failed_devices=failed_devices
        )
        
        return response_formatter_v2.success(
            data=batch_response,
            message=f"批量预测任务创建完成，成功 {len(predictions)} 个，失败 {len(failed_devices)} 个",
            code=201
        )
        
    except Exception as e:
        logger.error(f"批量创建预测任务失败: {str(e)}")
        return response_formatter_v2.error(
            message="批量创建预测任务失败",
            details={"error": str(e)}
        )


@router.get("/history", response_model=APIResponse[PaginatedResponse[PredictionResponse]])
async def get_prediction_history(
    device_code: str = Query(..., description="设备代码"),
    metric_name: Optional[str] = Query(None, description="指标名称"),
    status: Optional[str] = Query(None, description="状态筛选"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页大小")
):
    """
    查询设备的预测历史记录
    
    支持按设备代码、指标名称、状态筛选，返回分页结果
    
    使用JSONB查询优化性能，基于data_filters字段查询
    
    Args:
        device_code: 设备代码（必填）
        metric_name: 指标名称（可选）
        status: 状态筛选（可选）
        page: 页码
        page_size: 每页大小
    """
    try:
        # 使用 JSONB 包含查询（利用GIN索引）
        query = AIPrediction.filter(
            data_filters__contains={"device_code": device_code}
        )
        
        # 如果指定了指标名称，添加额外过滤
        if metric_name:
            query = query.filter(
                data_filters__contains={"metric_name": metric_name}
            )
        
        # 状态筛选
        if status:
            query = query.filter(status=status)
        
        # 查询总数
        total = await query.count()
        
        # 分页查询（按创建时间倒序）
        offset = (page - 1) * page_size
        predictions = await query.order_by('-created_at').offset(offset).limit(page_size)
        
        # 转换为响应格式（使用增强的from_orm_with_filters方法）
        prediction_responses = [
            PredictionResponse.from_orm_with_filters(p)
            for p in predictions
        ]
        
        # 创建分页响应
        paginated_response = create_pagination_response(
            items=prediction_responses,
            total=total,
            page=page,
            page_size=page_size
        )
        
        return response_formatter_v2.success(
            data=paginated_response,
            message=f"成功查询到 {total} 条预测历史记录"
        )
        
    except Exception as e:
        logger.error(f"查询预测历史失败: device_code={device_code}, 错误: {str(e)}")
        return response_formatter_v2.error(
            message="查询预测历史失败",
            details={"error": str(e)}
        )


@router.post("/batch-delete", response_model=APIResponse[BatchOperationResponse])
async def batch_delete_predictions(batch_data: BatchDeleteRequest):
    """批量删除预测"""
    try:
        success_count = 0
        failed_count = 0
        failed_ids = []
        errors = []
        
        for prediction_id in batch_data.ids:
            try:
                prediction = await AIPrediction.get_or_none(id=prediction_id)
                if not prediction:
                    failed_count += 1
                    failed_ids.append(prediction_id)
                    errors.append(f"预测 {prediction_id} 不存在")
                    continue
                
                if prediction.status == PredictionStatus.RUNNING:
                    failed_count += 1
                    failed_ids.append(prediction_id)
                    errors.append(f"预测 {prediction_id} 正在运行中，无法删除")
                    continue
                
                await prediction.delete()
                success_count += 1
                
            except Exception as e:
                failed_count += 1
                failed_ids.append(prediction_id)
                errors.append(f"删除预测 {prediction_id} 失败: {str(e)}")
        
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
        logger.error(f"批量删除预测失败: {str(e)}")
        return response_formatter_v2.error(
            message="批量删除预测失败",
            details={"error": str(e)}
        )


# =====================================================
# 后台任务和辅助函数
# =====================================================

async def execute_prediction_task(prediction_id: int):
    """执行预测任务（后台任务）"""
    try:
        prediction = await AIPrediction.get(id=prediction_id)
        
        # 更新状态为运行中
        prediction.status = PredictionStatus.RUNNING
        prediction.started_at = datetime.now()
        prediction.progress = 0
        await prediction.save()
        
        # TODO: 实现具体的预测算法
        # 这里应该根据model_type和parameters执行相应的预测算法
        
        # 模拟预测过程
        import asyncio
        for progress in range(0, 101, 10):
            prediction.progress = progress
            await prediction.save()
            await asyncio.sleep(1)  # 模拟计算时间
        
        # 模拟预测结果
        result_data = {
            "predictions": [
                {"timestamp": "2024-01-01T00:00:00Z", "value": 85.2, "confidence": 0.92},
                {"timestamp": "2024-01-01T01:00:00Z", "value": 87.1, "confidence": 0.89},
                {"timestamp": "2024-01-01T02:00:00Z", "value": 89.3, "confidence": 0.87}
            ],
            "summary": {
                "avg_value": 87.2,
                "trend": "increasing",
                "volatility": "low"
            }
        }
        
        confidence_interval = {
            "lower_bound": 82.5,
            "upper_bound": 91.8,
            "confidence_level": 0.95
        }
        
        # 更新预测结果
        prediction.status = PredictionStatus.COMPLETED
        prediction.completed_at = datetime.now()
        prediction.progress = 100
        prediction.result_data = result_data
        prediction.accuracy_score = 0.89
        prediction.confidence_interval = confidence_interval
        await prediction.save()
        
        logger.info(f"预测任务完成: prediction_id={prediction_id}")
        
    except Exception as e:
        # 更新状态为失败
        try:
            prediction = await AIPrediction.get(id=prediction_id)
            prediction.status = PredictionStatus.FAILED
            prediction.error_message = str(e)
            await prediction.save()
        except:
            pass
        
        logger.error(f"预测任务失败: prediction_id={prediction_id}, 错误: {str(e)}")


async def generate_prediction_export_file(prediction: AIPrediction, format: str) -> str:
    """生成预测导出文件"""
    import json
    import csv
    import os
    from pathlib import Path
    
    # 创建导出目录
    export_dir = Path("exports/predictions")
    export_dir.mkdir(parents=True, exist_ok=True)
    
    filename = f"prediction_{prediction.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    if format == "json":
        file_path = export_dir / f"{filename}.json"
        export_data = {
            "prediction_info": {
                "id": prediction.id,
                "name": prediction.prediction_name,
                "description": prediction.description,
                "target_variable": prediction.target_variable,
                "prediction_horizon": prediction.prediction_horizon,
                "model_type": prediction.model_type
            },
            "results": prediction.result_data,
            "accuracy_score": prediction.accuracy_score,
            "confidence_interval": prediction.confidence_interval,
            "export_time": datetime.now().isoformat()
        }
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)
    
    elif format == "csv":
        file_path = export_dir / f"{filename}.csv"
        
        with open(file_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # 写入头部信息
            writer.writerow(["预测信息"])
            writer.writerow(["预测ID", prediction.id])
            writer.writerow(["预测名称", prediction.prediction_name])
            writer.writerow(["目标变量", prediction.target_variable])
            writer.writerow(["准确率", prediction.accuracy_score])
            writer.writerow([])
            
            # 写入预测结果
            if prediction.result_data and "predictions" in prediction.result_data:
                writer.writerow(["时间戳", "预测值", "置信度"])
                for pred in prediction.result_data["predictions"]:
                    writer.writerow([pred["timestamp"], pred["value"], pred["confidence"]])
    
    elif format == "excel":
        # TODO: 实现Excel导出
        file_path = export_dir / f"{filename}.xlsx"
        # 这里应该使用openpyxl或pandas实现Excel导出
        pass
    
    return str(file_path)