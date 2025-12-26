#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI模型管理API v2
提供模型的CRUD操作、上传、训练、部署和指标查看功能
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
import os
import hashlib

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form, BackgroundTasks, Request
from fastapi.responses import FileResponse

from app.models.ai_monitoring import AIModel, ModelStatus
from app.schemas.ai_monitoring import (
    ModelCreate, ModelUpdate, ModelResponse, ModelTrainRequest, ModelMetricsResponse,
    AIMonitoringQuery, BatchDeleteRequest, BatchOperationResponse
)
from app.schemas.base import APIResponse, PaginatedResponse
from app.core.response_formatter_v2 import create_formatter
from app.core.pagination import get_pagination_params, create_pagination_response
from app.log import logger
from app.services.ai.tasks import train_model as train_model_task_celery

response_formatter_v2 = create_formatter()

router = APIRouter(prefix="/models", tags=["AI模型管理"])


@router.get("")
async def get_models(
    status: Optional[str] = Query(None, description="模型状态"),
    model_type: Optional[str] = Query(None, description="模型类型"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    created_by: Optional[int] = Query(None, description="创建人ID"),
    pagination: Dict[str, int] = Depends(get_pagination_params)
):
    """
    获取模型列表
    """
    try:
        logger.info(f"获取模型列表请求: status={status}, model_type={model_type}, search={search}")
        
        # 构建查询条件
        filters = {}
        
        if status:
            filters["status"] = status
        
        if model_type:
            filters["model_type"] = model_type
        
        if created_by:
            filters["created_by"] = created_by
            
        # 基础查询
        queryset = AIModel.filter(**filters)
        
        # 关键词搜索
        if search:
            queryset = queryset.filter(
                model_name__icontains=search
            )
        
        # 排序
        queryset = queryset.order_by("-created_at")
        
        # 分页查询
        total = await queryset.count()
        models = await queryset.offset(pagination["offset"]).limit(pagination["limit"])
        
        logger.info(f"查询到 {total} 个模型")
        
        # 转换为响应数据（使用字典而非 Pydantic 模型）
        model_list = []
        for model in models:
            params = model.parameters or {}
            metrics_data = model.metrics or {}
            
            model_list.append({
                "id": model.id,
                "model_name": model.model_name,
                "model_version": model.model_version,
                "description": model.description,
                "model_type": model.model_type,
                "algorithm": params.get("algorithm", ""),
                "framework": params.get("framework", ""),
                "model_file_path": model.file_path,
                "model_file_size": params.get("file_size"),
                "model_file_hash": params.get("file_hash"),
                "training_dataset": model.training_data_info,
                "training_parameters": params,
                "training_metrics": metrics_data,
                "status": model.status.value if hasattr(model.status, 'value') else str(model.status),
                "progress": params.get("progress", 0.0),
                "accuracy": metrics_data.get("accuracy"),
                "precision": metrics_data.get("precision"),
                "recall": metrics_data.get("recall"),
                "f1_score": metrics_data.get("f1_score"),
                "deployment_config": params.get("deployment_config"),
                "deployed_at": model.trained_at.isoformat() if model.trained_at else None,
                "created_at": model.created_at.isoformat() if model.created_at else None,
                "updated_at": model.updated_at.isoformat() if model.updated_at else None,
                "created_by": model.created_by,
                "updated_by": model.created_by
            })
        
        # 创建分页响应
        paginated_response = create_pagination_response(
            data=model_list,
            total=total,
            page=pagination["page"],
            page_size=pagination["page_size"]
        )
        
        return response_formatter_v2.success(
            data=paginated_response,
            message="获取模型列表成功"
        )
        
    except Exception as e:
        logger.error(f"获取模型列表失败: {str(e)}")
        import traceback
        traceback.print_exc()
        # 返回 500 错误而不是 400
        return response_formatter_v2.error(
            message=f"获取模型列表失败: {str(e)}",
            code=500
        )


@router.get("/{model_id}")
async def get_model(model_id: int):
    """获取模型详情"""
    try:
        model = await AIModel.get_or_none(id=model_id)
        if not model:
            return response_formatter_v2.error(
                message="模型不存在",
                code=404
            )
        
        params = model.parameters or {}
        metrics_data = model.metrics or {}
        
        model_data = {
            "id": model.id,
            "model_name": model.model_name,
            "model_version": model.model_version,
            "description": model.description,
            "model_type": model.model_type,
            "algorithm": params.get("algorithm", ""),
            "framework": params.get("framework", ""),
            "model_file_path": model.file_path,
            "model_file_size": params.get("file_size"),
            "model_file_hash": params.get("file_hash"),
            "training_dataset": model.training_data_info,
            "training_parameters": params,
            "training_metrics": metrics_data,
            "status": model.status.value if hasattr(model.status, 'value') else str(model.status),
            "progress": params.get("progress", 0.0),
            "accuracy": metrics_data.get("accuracy"),
            "precision": metrics_data.get("precision"),
            "recall": metrics_data.get("recall"),
            "f1_score": metrics_data.get("f1_score"),
            "deployment_config": params.get("deployment_config"),
            "deployed_at": model.trained_at.isoformat() if model.trained_at else None,
            "created_at": model.created_at.isoformat() if model.created_at else None,
            "updated_at": model.updated_at.isoformat() if model.updated_at else None,
            "created_by": model.created_by,
            "updated_by": model.created_by
        }
        
        return response_formatter_v2.success(
            data=model_data,
            message="获取模型详情成功"
        )
        
    except Exception as e:
        logger.error(f"获取模型详情失败: model_id={model_id}, 错误: {str(e)}")
        return response_formatter_v2.error(
            message="获取模型详情失败",
            details={"error": str(e)}
        )


@router.post("", response_model=APIResponse[ModelResponse])
async def create_model(
    model_data: ModelCreate,
    current_user_id: int = 1  # TODO: 从认证中获取
):
    """创建模型"""
    try:
        # 检查模型名称和版本是否已存在
        existing_model = await AIModel.get_or_none(
            model_name=model_data.model_name,
            model_version=model_data.model_version
        )
        if existing_model:
            return response_formatter_v2.error(
                message="模型名称和版本已存在",
                code=400
            )
        
        # 创建模型记录
        model = await AIModel.create(
            model_name=model_data.model_name,
            model_version=model_data.model_version,
            description=model_data.description,
            model_type=model_data.model_type,
            algorithm=model_data.algorithm,
            framework=model_data.framework,
            training_dataset=model_data.training_dataset,
            training_parameters=model_data.training_parameters,
            status=ModelStatus.DRAFT,
            created_by=current_user_id,
            updated_by=current_user_id
        )
        
        model_response = ModelResponse(
            id=model.id,
            model_name=model.model_name,
            model_version=model.model_version,
            description=model.description,
            model_type=model.model_type,
            algorithm=model.algorithm,
            framework=model.framework,
            model_file_path=model.model_file_path,
            model_file_size=model.model_file_size,
            model_file_hash=model.model_file_hash,
            training_dataset=model.training_dataset,
            training_parameters=model.training_parameters,
            training_metrics=model.training_metrics,
            status=model.status,
            progress=model.progress,
            accuracy=model.accuracy,
            precision=model.precision,
            recall=model.recall,
            f1_score=model.f1_score,
            deployment_config=model.deployment_config,
            deployed_at=model.deployed_at,
            created_at=model.created_at,
            updated_at=model.updated_at,
            created_by=model.created_by,
            updated_by=model.updated_by
        )
        
        return response_formatter_v2.success(
            data=model_response,
            message="创建模型成功",
            code=201
        )
        
    except Exception as e:
        logger.error(f"创建模型失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return response_formatter_v2.error(
            message=f"创建模型失败: {str(e)}",
            details=[{
                "code": "CREATION_FAILED",
                "message": str(e),
                "field": "general"
            }]
        )


@router.post("/upload", response_model=APIResponse[ModelResponse])
async def upload_model(
    file: UploadFile = File(...),
    model_name: str = Form(..., description="模型名称"),
    model_version: str = Form(..., description="模型版本"),
    model_type: str = Form(..., description="模型类型"),
    algorithm: str = Form(..., description="算法名称"),
    framework: str = Form(..., description="框架名称"),
    description: Optional[str] = Form(None, description="模型描述"),
    current_user_id: int = 1  # TODO: 从认证中获取
):
    """上传模型文件"""
    try:
        # 检查文件类型
        allowed_extensions = {'.pkl', '.joblib', '.h5', '.pb', '.onnx', '.pt', '.pth'}
        file_extension = os.path.splitext(file.filename)[1].lower()
        if file_extension not in allowed_extensions:
            return response_formatter_v2.error(
                message=f"不支持的文件类型: {file_extension}",
                code=400
            )
        
        # 检查模型名称和版本是否已存在
        existing_model = await AIModel.get_or_none(
            model_name=model_name,
            model_version=model_version
        )
        if existing_model:
            return response_formatter_v2.error(
                message="模型名称和版本已存在",
                code=400
            )
        
        # 创建上传目录
        upload_dir = f"uploads/models/{model_name}/{model_version}"
        os.makedirs(upload_dir, exist_ok=True)
        
        # 保存文件
        file_path = os.path.join(upload_dir, file.filename)
        content = await file.read()
        
        with open(file_path, "wb") as f:
            f.write(content)
        
        # 计算文件哈希
        file_hash = hashlib.sha256(content).hexdigest()
        
        # 创建模型记录
        model = await AIModel.create(
            model_name=model_name,
            model_version=model_version,
            description=description,
            model_type=model_type,
            algorithm=algorithm,
            framework=framework,
            model_file_path=file_path,
            model_file_size=len(content),
            model_file_hash=file_hash,
            status=ModelStatus.TRAINED,
            created_by=current_user_id,
            updated_by=current_user_id
        )
        
        model_response = ModelResponse(
            id=model.id,
            model_name=model.model_name,
            model_version=model.model_version,
            description=model.description,
            model_type=model.model_type,
            algorithm=model.algorithm,
            framework=model.framework,
            model_file_path=model.model_file_path,
            model_file_size=model.model_file_size,
            model_file_hash=model.model_file_hash,
            training_dataset=model.training_dataset,
            training_parameters=model.training_parameters,
            training_metrics=model.training_metrics,
            status=model.status,
            progress=model.progress,
            accuracy=model.accuracy,
            precision=model.precision,
            recall=model.recall,
            f1_score=model.f1_score,
            deployment_config=model.deployment_config,
            deployed_at=model.deployed_at,
            created_at=model.created_at,
            updated_at=model.updated_at,
            created_by=model.created_by,
            updated_by=model.updated_by
        )
        
        return response_formatter_v2.success(
            data=model_response,
            message="上传模型成功",
            code=201
        )
        
    except Exception as e:
        logger.error(f"上传模型失败: {str(e)}")
        return response_formatter_v2.error(
            message="上传模型失败",
            details={"error": str(e)}
        )


@router.put("/{model_id}", response_model=APIResponse[ModelResponse])
async def update_model(
    model_id: int,
    model_data: ModelUpdate,
    current_user_id: int = 1  # TODO: 从认证中获取
):
    """更新模型"""
    try:
        model = await AIModel.get_or_none(id=model_id)
        if not model:
            return response_formatter_v2.error(
                message="模型不存在",
                code=404
            )
        
        # 检查是否可以更新（训练中的模型不能更新某些字段）
        if model.status == ModelStatus.TRAINING:
            restricted_fields = {"model_name", "model_version", "model_type", "algorithm", "framework"}
            update_fields = set(model_data.dict(exclude_unset=True).keys())
            if restricted_fields.intersection(update_fields):
                return response_formatter_v2.error(
                    message="训练中的模型不能更新基本信息",
                    code=400
                )
        
        # 更新字段
        update_data = model_data.dict(exclude_unset=True)
        if update_data:
            update_data["updated_by"] = current_user_id
            await model.update_from_dict(update_data)
            await model.save()
        
        model_response = ModelResponse(
            id=model.id,
            model_name=model.model_name,
            model_version=model.model_version,
            description=model.description,
            model_type=model.model_type,
            algorithm=model.algorithm,
            framework=model.framework,
            model_file_path=model.model_file_path,
            model_file_size=model.model_file_size,
            model_file_hash=model.model_file_hash,
            training_dataset=model.training_dataset,
            training_parameters=model.training_parameters,
            training_metrics=model.training_metrics,
            status=model.status,
            progress=model.progress,
            accuracy=model.accuracy,
            precision=model.precision,
            recall=model.recall,
            f1_score=model.f1_score,
            deployment_config=model.deployment_config,
            deployed_at=model.deployed_at,
            created_at=model.created_at,
            updated_at=model.updated_at,
            created_by=model.created_by,
            updated_by=model.updated_by
        )
        
        return response_formatter_v2.success(
            data=model_response,
            message="更新模型成功"
        )
        
    except Exception as e:
        logger.error(f"更新模型失败: model_id={model_id}, 错误: {str(e)}")
        return response_formatter_v2.error(
            message="更新模型失败",
            details={"error": str(e)}
        )


@router.delete("/{model_id}", response_model=APIResponse[dict])
async def delete_model(model_id: int):
    """删除模型"""
    try:
        model = await AIModel.get_or_none(id=model_id)
        if not model:
            return response_formatter_v2.error(
                message="模型不存在",
                code=404
            )
        
        # 检查是否可以删除（已部署的模型需要先下线）
        if model.status == ModelStatus.DEPLOYED:
            return response_formatter_v2.error(
                message="请先下线已部署的模型",
                code=400
            )
        
        # 删除模型文件
        if model.model_file_path and os.path.exists(model.model_file_path):
            try:
                os.remove(model.model_file_path)
            except Exception as e:
                logger.warning(f"删除模型文件失败: {str(e)}")
        
        await model.delete()
        
        return response_formatter_v2.success(
            data={"deleted_id": model_id},
            message="删除模型成功"
        )
        
    except Exception as e:
        logger.error(f"删除模型失败: model_id={model_id}, 错误: {str(e)}")
        return response_formatter_v2.error(
            message="删除模型失败",
            details={"error": str(e)}
        )


@router.post("/{model_id}/train", response_model=APIResponse[dict])
async def train_model(
    model_id: int,
    train_data: ModelTrainRequest,
    background_tasks: BackgroundTasks,
    current_user_id: int = 1  # TODO: 从认证中获取
):
    """训练模型"""
    try:
        model = await AIModel.get_or_none(id=model_id)
        if not model:
            return response_formatter_v2.error(
                message="模型不存在",
                code=404
            )
        
        # 检查模型状态
        if model.status not in [ModelStatus.DRAFT, ModelStatus.TRAINED]:
            return response_formatter_v2.error(
                message="模型状态不允许训练",
                code=400
            )
        
        # 更新训练参数
        model.training_dataset = train_data.training_dataset
        model.training_parameters = train_data.training_parameters
        model.status = ModelStatus.TRAINING
        model.progress = 0.0
        model.updated_by = current_user_id
        await model.save()
        
        # 添加后台训练任务
        # background_tasks.add_task(train_model_task, model_id, train_data.dict())
        # 使用 Celery 异步任务
        task = train_model_task_celery.delay(model_id, train_data.dict())
        
        # 更新 task_id
        model.task_id = task.id
        await model.save()
        
        return response_formatter_v2.success(
            data={
                "model_id": model_id,
                "task_id": task.id,
                "status": "training_started",
                "training_dataset": train_data.training_dataset
            },
            message="开始训练模型"
        )
        
    except Exception as e:
        logger.error(f"训练模型失败: model_id={model_id}, 错误: {str(e)}")
        return response_formatter_v2.error(
            message="训练模型失败",
            details={"error": str(e)}
        )


@router.get("/{model_id}/metrics", response_model=APIResponse[ModelMetricsResponse])
async def get_model_metrics(model_id: int):
    """获取模型指标"""
    try:
        model = await AIModel.get_or_none(id=model_id)
        if not model:
            return response_formatter_v2.error(
                message="模型不存在",
                code=404
            )
        
        metrics_response = ModelMetricsResponse(
            accuracy=model.accuracy,
            precision=model.precision,
            recall=model.recall,
            f1_score=model.f1_score,
            training_metrics=model.training_metrics,
            validation_metrics=model.training_metrics.get("validation", {}) if model.training_metrics else {},
            confusion_matrix=model.training_metrics.get("confusion_matrix") if model.training_metrics else None
        )
        
        return response_formatter_v2.success(
            data=metrics_response,
            message="获取模型指标成功"
        )
        
    except Exception as e:
        logger.error(f"获取模型指标失败: model_id={model_id}, 错误: {str(e)}")
        return response_formatter_v2.error(
            message="获取模型指标失败",
            details={"error": str(e)}
        )


@router.get("/{model_id}/logs", response_model=APIResponse[dict])
async def get_model_logs(model_id: int):
    """获取模型训练日志"""
    try:
        model = await AIModel.get_or_none(id=model_id)
        if not model:
            return response_formatter_v2.error(
                message="模型不存在",
                code=404
            )
        
        # 目前我们使用 error_log 字段存储训练日志
        # 在实际生产环境中，建议使用专门的日志存储或表
        logs = model.error_log if model.error_log else "暂无日志"
        
        return response_formatter_v2.success(
            data={
                "model_id": model_id,
                "logs": logs,
                "status": model.status,
                "progress": model.progress
            },
            message="获取模型日志成功"
        )
        
    except Exception as e:
        logger.error(f"获取模型日志失败: model_id={model_id}, 错误: {str(e)}")
        return response_formatter_v2.error(
            message="获取模型日志失败",
            details={"error": str(e)}
        )


@router.post("/{model_id}/deploy", response_model=APIResponse[dict])
async def deploy_model(
    model_id: int,
    deployment_config: Dict[str, Any],
    current_user_id: int = 1  # TODO: 从认证中获取
):
    """部署模型"""
    try:
        model = await AIModel.get_or_none(id=model_id)
        if not model:
            return response_formatter_v2.error(
                message="模型不存在",
                code=404
            )
        
        if model.status != ModelStatus.TRAINED:
            return response_formatter_v2.error(
                message="只有已训练的模型可以部署",
                code=400
            )
        
        # 更新部署配置
        model.deployment_config = deployment_config
        model.status = ModelStatus.DEPLOYED
        model.deployed_at = datetime.now()
        model.updated_by = current_user_id
        await model.save()
        
        return response_formatter_v2.success(
            data={
                "model_id": model_id,
                "status": "deployed",
                "deployed_at": model.deployed_at.isoformat()
            },
            message="部署模型成功"
        )
        
    except Exception as e:
        logger.error(f"部署模型失败: model_id={model_id}, 错误: {str(e)}")
        return response_formatter_v2.error(
            message="部署模型失败",
            details={"error": str(e)}
        )


@router.post("/batch-delete", response_model=APIResponse[BatchOperationResponse])
async def batch_delete_models(batch_data: BatchDeleteRequest):
    """批量删除模型"""
    try:
        success_count = 0
        failed_count = 0
        failed_ids = []
        errors = []
        
        for model_id in batch_data.ids:
            try:
                model = await AIModel.get_or_none(id=model_id)
                if not model:
                    failed_count += 1
                    failed_ids.append(model_id)
                    errors.append(f"模型 {model_id} 不存在")
                    continue
                
                if model.status == ModelStatus.DEPLOYED:
                    failed_count += 1
                    failed_ids.append(model_id)
                    errors.append(f"模型 {model_id} 已部署，无法删除")
                    continue
                
                # 删除模型文件
                if model.model_file_path and os.path.exists(model.model_file_path):
                    try:
                        os.remove(model.model_file_path)
                    except Exception as e:
                        logger.warning(f"删除模型文件失败: {str(e)}")
                
                await model.delete()
                success_count += 1
                
            except Exception as e:
                failed_count += 1
                failed_ids.append(model_id)
                errors.append(f"删除模型 {model_id} 失败: {str(e)}")
        
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
        logger.error(f"批量删除模型失败: {str(e)}")
        return response_formatter_v2.error(
            message="批量删除模型失败",
            details={"error": str(e)}
        )


# =====================================================
# 后台任务和辅助函数
# =====================================================

async def train_model_task(model_id: int, train_config: Dict[str, Any]):
    """训练模型任务（后台任务）"""
    try:
        model = await AIModel.get(id=model_id)
        
        # TODO: 实现具体的模型训练逻辑
        # 这里应该根据model_type、algorithm和training_parameters执行相应的训练算法
        
        # 模拟训练过程
        import asyncio
        # 模拟进度更新
        for progress in range(0, 101, 10):
            model.progress = float(progress)
            await model.save()
            await asyncio.sleep(1)  # 模拟每步1秒，共10秒
        
        # 模拟训练结果
        training_metrics = {
            "epochs": 100,
            "loss": 0.15,
            "val_loss": 0.18,
            "training_time": 600,
            "validation": {
                "accuracy": 0.92,
                "precision": 0.89,
                "recall": 0.94,
                "f1_score": 0.91
            },
            "confusion_matrix": [[85, 5], [3, 87]]
        }
        
        # 更新模型
        model.status = ModelStatus.TRAINED
        model.training_metrics = training_metrics
        model.accuracy = training_metrics["validation"]["accuracy"]
        model.precision = training_metrics["validation"]["precision"]
        model.recall = training_metrics["validation"]["recall"]
        model.f1_score = training_metrics["validation"]["f1_score"]
        await model.save()
        
        logger.info(f"模型训练完成: model_id={model_id}")
        
    except Exception as e:
        # 更新状态为草稿（训练失败）
        try:
            model = await AIModel.get(id=model_id)
            model.status = ModelStatus.DRAFT
            await model.save()
        except:
            pass
        
        logger.error(f"模型训练失败: model_id={model_id}, 错误: {str(e)}")