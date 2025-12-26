#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI数据标注API v2
提供数据标注项目的CRUD操作、数据导入导出功能
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
import os
import json
import csv

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, BackgroundTasks
from fastapi.responses import FileResponse

from app.models.ai_monitoring import AIAnnotationProject, AnnotationStatus
from app.schemas.ai_monitoring import (
    AnnotationProjectCreate, AnnotationProjectUpdate, AnnotationProjectResponse,
    AnnotationImportRequest, AnnotationExportRequest,
    AIMonitoringQuery, BatchDeleteRequest, BatchOperationResponse
)
from app.schemas.base import APIResponse, PaginatedResponse
from app.core.response_formatter_v2 import create_formatter
from app.core.pagination import get_pagination_params, create_pagination_response
from app.log import logger


router = APIRouter(prefix="/annotations", tags=["AI数据标注"])


@router.get("", response_model=APIResponse[PaginatedResponse[AnnotationProjectResponse]])
async def get_annotation_projects(
    query: AIMonitoringQuery = Depends(),
    pagination: dict = Depends(get_pagination_params),
    annotation_type: Optional[str] = Query(None, description="标注类型过滤"),
    data_type: Optional[str] = Query(None, description="数据类型过滤")
):
    """
    获取标注项目列表
    
    支持按标注类型、数据类型、状态、创建人等条件过滤，支持关键词搜索
    """
    try:
        # 构建查询条件
        filters = {}
        
        if query.status:
            filters["status"] = query.status
        
        if annotation_type:
            filters["annotation_type"] = annotation_type
        
        if data_type:
            filters["data_type"] = data_type
        
        if query.created_by:
            filters["created_by"] = query.created_by
        
        if query.date_from:
            filters["created_at__gte"] = query.date_from
        
        if query.date_to:
            filters["created_at__lte"] = query.date_to
        
        # 基础查询
        queryset = AIAnnotationProject.filter(**filters)
        
        # 关键词搜索
        if query.search:
            queryset = queryset.filter(
                project_name__icontains=query.search
            )
        
        # 排序
        queryset = queryset.order_by("-created_at")
        
        # 分页查询
        total = await queryset.count()
        projects = await queryset.offset(pagination["offset"]).limit(pagination["limit"])
        
        # 转换为响应模式
        project_responses = []
        for project in projects:
            project_responses.append(AnnotationProjectResponse(
                id=project.id,
                project_name=project.project_name,
                description=project.description,
                annotation_type=project.annotation_type,
                data_type=project.data_type,
                label_schema=project.label_schema,
                total_samples=project.total_samples,
                annotated_samples=project.annotated_samples,
                reviewed_samples=project.reviewed_samples,
                status=project.status,
                progress=project.progress,
                quality_threshold=project.quality_threshold,
                inter_annotator_agreement=project.inter_annotator_agreement,
                import_config=project.import_config,
                export_config=project.export_config,
                created_at=project.created_at,
                updated_at=project.updated_at,
                created_by=project.created_by,
                updated_by=project.updated_by
            ))
        
        # 创建分页响应
        paginated_response = create_pagination_response(
            items=project_responses,
            total=total,
            page=pagination["page"],
            page_size=pagination["page_size"]
        )
        
        return response_formatter_v2.success(
            data=paginated_response,
            message="获取标注项目列表成功"
        )
        
    except Exception as e:
        logger.error(f"获取标注项目列表失败: {str(e)}")
        return response_formatter_v2.error(
            message="获取标注项目列表失败",
            details={"error": str(e)}
        )


@router.get("/{project_id}", response_model=APIResponse[AnnotationProjectResponse])
async def get_annotation_project(project_id: int):
    """获取标注项目详情"""
    try:
        project = await AIAnnotationProject.get_or_none(id=project_id)
        if not project:
            return response_formatter_v2.error(
                message="标注项目不存在",
                code=404
            )
        
        project_response = AnnotationProjectResponse(
            id=project.id,
            project_name=project.project_name,
            description=project.description,
            annotation_type=project.annotation_type,
            data_type=project.data_type,
            label_schema=project.label_schema,
            total_samples=project.total_samples,
            annotated_samples=project.annotated_samples,
            reviewed_samples=project.reviewed_samples,
            status=project.status,
            progress=project.progress,
            quality_threshold=project.quality_threshold,
            inter_annotator_agreement=project.inter_annotator_agreement,
            import_config=project.import_config,
            export_config=project.export_config,
            created_at=project.created_at,
            updated_at=project.updated_at,
            created_by=project.created_by,
            updated_by=project.updated_by
        )
        
        return response_formatter_v2.success(
            data=project_response,
            message="获取标注项目详情成功"
        )
        
    except Exception as e:
        logger.error(f"获取标注项目详情失败: project_id={project_id}, 错误: {str(e)}")
        return response_formatter_v2.error(
            message="获取标注项目详情失败",
            details={"error": str(e)}
        )


@router.post("", response_model=APIResponse[AnnotationProjectResponse])
async def create_annotation_project(
    project_data: AnnotationProjectCreate,
    current_user_id: int = 1  # TODO: 从认证中获取
):
    """创建标注项目"""
    try:
        # 检查项目名称是否已存在
        existing_project = await AIAnnotationProject.get_or_none(
            project_name=project_data.project_name
        )
        if existing_project:
            return response_formatter_v2.error(
                message="项目名称已存在",
                code=400
            )
        
        # 创建标注项目
        project = await AIAnnotationProject.create(
            project_name=project_data.project_name,
            description=project_data.description,
            annotation_type=project_data.annotation_type,
            data_type=project_data.data_type,
            label_schema=project_data.label_schema,
            quality_threshold=project_data.quality_threshold,
            status=AnnotationStatus.CREATED,
            progress=0.0,
            created_by=current_user_id,
            updated_by=current_user_id
        )
        
        project_response = AnnotationProjectResponse(
            id=project.id,
            project_name=project.project_name,
            description=project.description,
            annotation_type=project.annotation_type,
            data_type=project.data_type,
            label_schema=project.label_schema,
            total_samples=project.total_samples,
            annotated_samples=project.annotated_samples,
            reviewed_samples=project.reviewed_samples,
            status=project.status,
            progress=project.progress,
            quality_threshold=project.quality_threshold,
            inter_annotator_agreement=project.inter_annotator_agreement,
            import_config=project.import_config,
            export_config=project.export_config,
            created_at=project.created_at,
            updated_at=project.updated_at,
            created_by=project.created_by,
            updated_by=project.updated_by
        )
        
        return response_formatter_v2.success(
            data=project_response,
            message="创建标注项目成功",
            code=201
        )
        
    except Exception as e:
        logger.error(f"创建标注项目失败: {str(e)}")
        return response_formatter_v2.error(
            message="创建标注项目失败",
            details={"error": str(e)}
        )


@router.put("/{project_id}", response_model=APIResponse[AnnotationProjectResponse])
async def update_annotation_project(
    project_id: int,
    project_data: AnnotationProjectUpdate,
    current_user_id: int = 1  # TODO: 从认证中获取
):
    """更新标注项目"""
    try:
        project = await AIAnnotationProject.get_or_none(id=project_id)
        if not project:
            return response_formatter_v2.error(
                message="标注项目不存在",
                code=404
            )
        
        # 检查是否可以更新（已完成的项目不能更新某些字段）
        if project.status == AnnotationStatus.COMPLETED:
            restricted_fields = {"annotation_type", "data_type", "label_schema"}
            update_fields = set(project_data.dict(exclude_unset=True).keys())
            if restricted_fields.intersection(update_fields):
                return response_formatter_v2.error(
                    message="已完成的项目不能更新核心配置",
                    code=400
                )
        
        # 更新字段
        update_data = project_data.dict(exclude_unset=True)
        if update_data:
            update_data["updated_by"] = current_user_id
            await project.update_from_dict(update_data)
            await project.save()
        
        project_response = AnnotationProjectResponse(
            id=project.id,
            project_name=project.project_name,
            description=project.description,
            annotation_type=project.annotation_type,
            data_type=project.data_type,
            label_schema=project.label_schema,
            total_samples=project.total_samples,
            annotated_samples=project.annotated_samples,
            reviewed_samples=project.reviewed_samples,
            status=project.status,
            progress=project.progress,
            quality_threshold=project.quality_threshold,
            inter_annotator_agreement=project.inter_annotator_agreement,
            import_config=project.import_config,
            export_config=project.export_config,
            created_at=project.created_at,
            updated_at=project.updated_at,
            created_by=project.created_by,
            updated_by=project.updated_by
        )
        
        return response_formatter_v2.success(
            data=project_response,
            message="更新标注项目成功"
        )
        
    except Exception as e:
        logger.error(f"更新标注项目失败: project_id={project_id}, 错误: {str(e)}")
        return response_formatter_v2.error(
            message="更新标注项目失败",
            details={"error": str(e)}
        )


@router.delete("/{project_id}", response_model=APIResponse[dict])
async def delete_annotation_project(project_id: int):
    """删除标注项目"""
    try:
        project = await AIAnnotationProject.get_or_none(id=project_id)
        if not project:
            return response_formatter_v2.error(
                message="标注项目不存在",
                code=404
            )
        
        # 检查是否可以删除（进行中的项目需要先停止）
        if project.status == AnnotationStatus.IN_PROGRESS:
            return response_formatter_v2.error(
                message="请先停止进行中的标注项目",
                code=400
            )
        
        await project.delete()
        
        return response_formatter_v2.success(
            data={"deleted_id": project_id},
            message="删除标注项目成功"
        )
        
    except Exception as e:
        logger.error(f"删除标注项目失败: project_id={project_id}, 错误: {str(e)}")
        return response_formatter_v2.error(
            message="删除标注项目失败",
            details={"error": str(e)}
        )


@router.post("/{project_id}/import", response_model=APIResponse[dict])
async def import_annotation_data(
    project_id: int,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    import_format: str = Query(..., description="导入格式: json, csv, coco"),
    current_user_id: int = 1  # TODO: 从认证中获取
):
    """导入标注数据"""
    try:
        project = await AIAnnotationProject.get_or_none(id=project_id)
        if not project:
            return response_formatter_v2.error(
                message="标注项目不存在",
                code=404
            )
        
        # 检查文件格式
        allowed_formats = {"json", "csv", "coco"}
        if import_format not in allowed_formats:
            return response_formatter_v2.error(
                message=f"不支持的导入格式: {import_format}",
                code=400
            )
        
        # 保存上传文件
        upload_dir = f"uploads/annotations/{project_id}"
        os.makedirs(upload_dir, exist_ok=True)
        
        file_path = os.path.join(upload_dir, f"import_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename}")
        content = await file.read()
        
        with open(file_path, "wb") as f:
            f.write(content)
        
        # 更新导入配置
        import_config = {
            "file_path": file_path,
            "format": import_format,
            "imported_at": datetime.now().isoformat(),
            "imported_by": current_user_id
        }
        
        project.import_config = import_config
        project.status = AnnotationStatus.IN_PROGRESS
        project.updated_by = current_user_id
        await project.save()
        
        # 添加后台任务处理导入
        background_tasks.add_task(process_annotation_import, project_id, file_path, import_format)
        
        return response_formatter_v2.success(
            data={
                "project_id": project_id,
                "file_name": file.filename,
                "import_format": import_format,
                "status": "importing"
            },
            message="开始导入标注数据"
        )
        
    except Exception as e:
        logger.error(f"导入标注数据失败: project_id={project_id}, 错误: {str(e)}")
        return response_formatter_v2.error(
            message="导入标注数据失败",
            details={"error": str(e)}
        )


@router.get("/{project_id}/export")
async def export_annotation_data(
    project_id: int,
    export_format: str = Query("json", description="导出格式: json, csv, coco"),
    include_reviewed_only: bool = Query(False, description="仅包含已审核数据")
):
    """导出标注数据"""
    try:
        project = await AIAnnotationProject.get_or_none(id=project_id)
        if not project:
            raise HTTPException(status_code=404, detail="标注项目不存在")
        
        if project.total_samples == 0:
            raise HTTPException(status_code=400, detail="项目无数据可导出")
        
        # 生成导出文件
        file_path = await generate_annotation_export_file(project, export_format, include_reviewed_only)
        
        # 返回文件
        filename = f"annotation_{project_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{export_format}"
        return FileResponse(
            path=file_path,
            filename=filename,
            media_type="application/octet-stream"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"导出标注数据失败: project_id={project_id}, 错误: {str(e)}")
        raise HTTPException(status_code=500, detail="导出标注数据失败")


@router.post("/batch-delete", response_model=APIResponse[BatchOperationResponse])
async def batch_delete_annotation_projects(batch_data: BatchDeleteRequest):
    """批量删除标注项目"""
    try:
        success_count = 0
        failed_count = 0
        failed_ids = []
        errors = []
        
        for project_id in batch_data.ids:
            try:
                project = await AIAnnotationProject.get_or_none(id=project_id)
                if not project:
                    failed_count += 1
                    failed_ids.append(project_id)
                    errors.append(f"标注项目 {project_id} 不存在")
                    continue
                
                if project.status == AnnotationStatus.IN_PROGRESS:
                    failed_count += 1
                    failed_ids.append(project_id)
                    errors.append(f"标注项目 {project_id} 正在进行中，无法删除")
                    continue
                
                await project.delete()
                success_count += 1
                
            except Exception as e:
                failed_count += 1
                failed_ids.append(project_id)
                errors.append(f"删除标注项目 {project_id} 失败: {str(e)}")
        
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
        logger.error(f"批量删除标注项目失败: {str(e)}")
        return response_formatter_v2.error(
            message="批量删除标注项目失败",
            details={"error": str(e)}
        )


# =====================================================
# 后台任务和辅助函数
# =====================================================

async def process_annotation_import(project_id: int, file_path: str, import_format: str):
    """处理标注数据导入（后台任务）"""
    try:
        project = await AIAnnotationProject.get(id=project_id)
        
        # TODO: 实现具体的数据导入逻辑
        # 这里应该根据import_format解析文件并导入数据
        
        # 模拟导入过程
        import asyncio
        await asyncio.sleep(5)  # 模拟处理时间
        
        # 模拟导入结果
        if import_format == "json":
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                total_samples = len(data.get("samples", []))
        elif import_format == "csv":
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                total_samples = sum(1 for row in reader) - 1  # 减去标题行
        else:
            total_samples = 100  # 模拟数据
        
        # 更新项目统计
        project.total_samples = total_samples
        project.annotated_samples = 0
        project.reviewed_samples = 0
        project.progress = 0.0
        project.status = AnnotationStatus.IN_PROGRESS
        await project.save()
        
        logger.info(f"标注数据导入完成: project_id={project_id}, total_samples={total_samples}")
        
    except Exception as e:
        # 更新状态为创建（导入失败）
        try:
            project = await AIAnnotationProject.get(id=project_id)
            project.status = AnnotationStatus.CREATED
            await project.save()
        except:
            pass
        
        logger.error(f"标注数据导入失败: project_id={project_id}, 错误: {str(e)}")


async def generate_annotation_export_file(
    project: AIAnnotationProject, 
    export_format: str, 
    include_reviewed_only: bool
) -> str:
    """生成标注数据导出文件"""
    from pathlib import Path
    
    # 创建导出目录
    export_dir = Path("exports/annotations")
    export_dir.mkdir(parents=True, exist_ok=True)
    
    filename = f"annotation_{project.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    if export_format == "json":
        file_path = export_dir / f"{filename}.json"
        
        # TODO: 从数据库获取实际的标注数据
        export_data = {
            "project_info": {
                "id": project.id,
                "name": project.project_name,
                "description": project.description,
                "annotation_type": project.annotation_type,
                "data_type": project.data_type,
                "label_schema": project.label_schema
            },
            "statistics": {
                "total_samples": project.total_samples,
                "annotated_samples": project.annotated_samples,
                "reviewed_samples": project.reviewed_samples,
                "progress": project.progress
            },
            "samples": [
                # 这里应该是实际的标注数据
                {
                    "id": 1,
                    "data": "sample_data_1",
                    "labels": ["label1", "label2"],
                    "annotated_by": 1,
                    "reviewed": True,
                    "created_at": "2024-01-01T00:00:00Z"
                }
            ],
            "export_info": {
                "exported_at": datetime.now().isoformat(),
                "include_reviewed_only": include_reviewed_only,
                "format": export_format
            }
        }
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)
    
    elif export_format == "csv":
        file_path = export_dir / f"{filename}.csv"
        
        with open(file_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # 写入头部
            writer.writerow(["样本ID", "数据", "标签", "标注人", "是否审核", "创建时间"])
            
            # TODO: 写入实际的标注数据
            writer.writerow([1, "sample_data_1", "label1,label2", 1, True, "2024-01-01T00:00:00Z"])
    
    elif export_format == "coco":
        file_path = export_dir / f"{filename}.json"
        
        # TODO: 实现COCO格式导出
        coco_data = {
            "info": {
                "description": project.project_name,
                "version": "1.0",
                "year": datetime.now().year,
                "contributor": "AI Annotation System",
                "date_created": datetime.now().isoformat()
            },
            "licenses": [],
            "images": [],
            "annotations": [],
            "categories": []
        }
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(coco_data, f, ensure_ascii=False, indent=2)
    
    return str(file_path)