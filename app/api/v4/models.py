"""
AI模型管理API v4
整合v3 AI模型API功能，使用统一响应格式

Requirements: 6.1
"""
from typing import Optional, List
from fastapi import APIRouter, Depends, Query, UploadFile, File
from fastapi.responses import JSONResponse, StreamingResponse
from datetime import datetime
import io

from app.core.auth_dependencies import get_current_active_user
from app.core.unified_logger import get_logger
from app.models.admin import User

from .schemas import (
    AIModelCreate,
    AIModelUpdate,
    ErrorCodes,
    create_response,
    create_error_response,
    create_paginated_response
)

logger = get_logger(__name__)
router = APIRouter()


# =====================================================
# 辅助函数
# =====================================================

async def get_model_class():
    """延迟导入AIModel模型"""
    from app.models.platform_upgrade import AIModel
    return AIModel


async def get_version_class():
    """延迟导入AIModelVersion模型"""
    from app.models.platform_upgrade import AIModelVersion
    return AIModelVersion


async def get_category_model():
    """延迟导入AssetCategory模型"""
    from app.models.platform_upgrade import AssetCategory
    return AssetCategory


async def model_to_dict(model, include_versions: bool = False) -> dict:
    """将AI模型转换为字典"""
    result = {
        "id": model.id,
        "code": model.code,
        "name": model.name,
        "description": model.description,
        "algorithm": model.algorithm,
        "target_signal": model.target_signal,
        "category_id": model.category_id,
        "hyperparameters": model.hyperparameters,
        "feature_config": model.feature_config,
        "training_config": model.training_config,
        "status": model.status,
        "is_active": model.is_active,
        "created_by": model.created_by,
        "updated_by": model.updated_by,
        "created_at": model.created_at.isoformat() if model.created_at else None,
        "updated_at": model.updated_at.isoformat() if model.updated_at else None
    }
    
    if include_versions and hasattr(model, 'versions'):
        versions = await model.versions.all()
        result["versions"] = [await version_to_dict(v) for v in versions]
    
    return result


async def version_to_dict(version) -> dict:
    """将模型版本转换为字典"""
    return {
        "id": version.id,
        "model_id": version.model_id,
        "version": version.version,
        "file_path": version.file_path,
        "file_size": version.file_size,
        "file_hash": version.file_hash,
        "training_start_time": version.training_start_time.isoformat() if version.training_start_time else None,
        "training_end_time": version.training_end_time.isoformat() if version.training_end_time else None,
        "training_data_range": version.training_data_range,
        "training_samples": version.training_samples,
        "metrics": version.metrics,
        "status": version.status,
        "deployed_at": version.deployed_at.isoformat() if version.deployed_at else None,
        "deployed_by": version.deployed_by,
        "release_notes": version.release_notes,
        "created_at": version.created_at.isoformat() if version.created_at else None,
        "updated_at": version.updated_at.isoformat() if version.updated_at else None
    }


# =====================================================
# AI模型CRUD API
# =====================================================

@router.post("", summary="创建AI模型")
async def create_model(
    model_data: AIModelCreate,
    current_user: User = Depends(get_current_active_user)
) -> JSONResponse:
    """
    创建新的AI模型
    """
    try:
        AIModel = await get_model_class()
        AssetCategory = await get_category_model()
        
        # 1. 检查编码唯一性
        existing = await AIModel.filter(code=model_data.code).first()
        if existing:
            return JSONResponse(
                status_code=409,
                content=create_error_response(
                    code=ErrorCodes.DUPLICATE_CODE,
                    message=f"模型编码 '{model_data.code}' 已存在"
                )
            )
        
        # 2. 验证资产类别（如果指定）
        if model_data.category_id:
            category = await AssetCategory.get_or_none(id=model_data.category_id)
            if not category:
                return JSONResponse(
                    status_code=404,
                    content=create_error_response(
                        code=ErrorCodes.CATEGORY_NOT_FOUND,
                        message=f"资产类别不存在: {model_data.category_id}"
                    )
                )
        
        # 3. 创建模型
        model = AIModel(
            code=model_data.code,
            name=model_data.name,
            description=model_data.description,
            algorithm=model_data.algorithm or "unknown",
            target_signal=model_data.output_features[0] if model_data.output_features else "",
            category_id=model_data.category_id,
            hyperparameters=model_data.hyperparameters or {},
            feature_config={"input_features": model_data.input_features} if model_data.input_features else {},
            training_config=model_data.training_config,
            status="draft",
            is_active=True,
            created_by=current_user.id,
            updated_by=current_user.id
        )
        await model.save()
        
        logger.info(f"AI模型创建成功: {model_data.code}, 用户: {current_user.username}")
        
        return JSONResponse(
            status_code=201,
            content=create_response(
                data=await model_to_dict(model),
                message="AI模型创建成功"
            )
        )
        
    except Exception as e:
        logger.error(f"创建AI模型失败: {e}")
        return JSONResponse(
            status_code=500,
            content=create_error_response(
                code=ErrorCodes.INTERNAL_ERROR,
                message=f"创建失败: {str(e)}"
            )
        )


@router.get("", summary="获取AI模型列表")
async def list_models(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    category_id: Optional[int] = Query(None, description="资产类别ID"),
    algorithm: Optional[str] = Query(None, description="算法类型"),
    status: Optional[str] = Query(None, description="状态: draft/training/trained/deployed/archived"),
    is_active: Optional[bool] = Query(None, description="是否激活"),
    keyword: Optional[str] = Query(None, description="搜索关键词"),
    current_user: User = Depends(get_current_active_user)
) -> JSONResponse:
    """
    获取AI模型列表（分页）
    """
    try:
        AIModel = await get_model_class()
        
        # 1. 构建查询条件
        query = AIModel.all()
        
        if category_id:
            query = query.filter(category_id=category_id)
        if algorithm:
            query = query.filter(algorithm=algorithm)
        if status:
            query = query.filter(status=status)
        if is_active is not None:
            query = query.filter(is_active=is_active)
        if keyword:
            query = query.filter(name__icontains=keyword) | query.filter(code__icontains=keyword)
        
        # 2. 分页查询
        total = await query.count()
        offset = (page - 1) * page_size
        models = await query.order_by("-created_at").offset(offset).limit(page_size)
        
        # 3. 转换为字典列表
        model_list = [await model_to_dict(m) for m in models]
        
        return JSONResponse(
            status_code=200,
            content=create_paginated_response(
                data=model_list,
                total=total,
                page=page,
                page_size=page_size,
                message="获取成功"
            )
        )
        
    except Exception as e:
        logger.error(f"获取AI模型列表失败: {e}")
        return JSONResponse(
            status_code=500,
            content=create_error_response(
                code=ErrorCodes.INTERNAL_ERROR,
                message=f"查询失败: {str(e)}"
            )
        )


@router.get("/{model_id}", summary="获取AI模型详情")
async def get_model(
    model_id: int,
    include_versions: bool = Query(False, description="是否包含版本列表"),
    current_user: User = Depends(get_current_active_user)
) -> JSONResponse:
    """
    获取单个AI模型详情
    """
    try:
        AIModel = await get_model_class()
        
        model = await AIModel.get_or_none(id=model_id)
        if not model:
            return JSONResponse(
                status_code=404,
                content=create_error_response(
                    code=ErrorCodes.MODEL_NOT_FOUND,
                    message=f"AI模型不存在: {model_id}"
                )
            )
        
        result = await model_to_dict(model, include_versions=include_versions)
        
        # 获取关联的类别信息
        if model.category_id:
            AssetCategory = await get_category_model()
            category = await AssetCategory.get_or_none(id=model.category_id)
            if category:
                result["category"] = {
                    "id": category.id,
                    "code": category.code,
                    "name": category.name
                }
        
        return JSONResponse(
            status_code=200,
            content=create_response(
                data=result,
                message="获取成功"
            )
        )
        
    except Exception as e:
        logger.error(f"获取AI模型详情失败: {e}")
        return JSONResponse(
            status_code=500,
            content=create_error_response(
                code=ErrorCodes.INTERNAL_ERROR,
                message=f"查询失败: {str(e)}"
            )
        )


@router.put("/{model_id}", summary="更新AI模型")
async def update_model(
    model_id: int,
    model_data: AIModelUpdate,
    current_user: User = Depends(get_current_active_user)
) -> JSONResponse:
    """
    更新AI模型信息
    
    注意：code字段不可修改
    """
    try:
        AIModel = await get_model_class()
        AssetCategory = await get_category_model()
        
        model = await AIModel.get_or_none(id=model_id)
        if not model:
            return JSONResponse(
                status_code=404,
                content=create_error_response(
                    code=ErrorCodes.MODEL_NOT_FOUND,
                    message=f"AI模型不存在: {model_id}"
                )
            )
        
        # 验证资产类别（如果更新）
        update_data = model_data.model_dump(exclude_unset=True)
        if "category_id" in update_data and update_data["category_id"]:
            category = await AssetCategory.get_or_none(id=update_data["category_id"])
            if not category:
                return JSONResponse(
                    status_code=404,
                    content=create_error_response(
                        code=ErrorCodes.CATEGORY_NOT_FOUND,
                        message=f"资产类别不存在: {update_data['category_id']}"
                    )
                )
        
        # 更新字段
        for field, value in update_data.items():
            if field == "input_features":
                model.feature_config = {"input_features": value}
            elif field == "output_features":
                if value:
                    model.target_signal = value[0]
            else:
                setattr(model, field, value)
        
        model.updated_by = current_user.id
        model.updated_at = datetime.now()
        await model.save()
        
        logger.info(f"AI模型更新成功: {model.code}, 用户: {current_user.username}")
        
        return JSONResponse(
            status_code=200,
            content=create_response(
                data=await model_to_dict(model),
                message="更新成功"
            )
        )
        
    except Exception as e:
        logger.error(f"更新AI模型失败: {e}")
        return JSONResponse(
            status_code=500,
            content=create_error_response(
                code=ErrorCodes.INTERNAL_ERROR,
                message=f"更新失败: {str(e)}"
            )
        )


@router.delete("/{model_id}", summary="删除AI模型")
async def delete_model(
    model_id: int,
    force: bool = Query(False, description="是否强制删除"),
    current_user: User = Depends(get_current_active_user)
) -> JSONResponse:
    """
    删除AI模型
    
    - 默认软删除（设置is_active=False）
    - force=True时物理删除
    """
    try:
        AIModel = await get_model_class()
        
        model = await AIModel.get_or_none(id=model_id)
        if not model:
            return JSONResponse(
                status_code=404,
                content=create_error_response(
                    code=ErrorCodes.MODEL_NOT_FOUND,
                    message=f"AI模型不存在: {model_id}"
                )
            )
        
        if force:
            # 检查是否有关联版本
            AIModelVersion = await get_version_class()
            version_count = await AIModelVersion.filter(model_id=model_id).count()
            if version_count > 0:
                return JSONResponse(
                    status_code=400,
                    content=create_error_response(
                        code=ErrorCodes.DEPENDENCY_EXISTS,
                        message=f"无法删除：该模型有 {version_count} 个版本"
                    )
                )
            await model.delete()
            logger.info(f"AI模型物理删除: {model.code}, 用户: {current_user.username}")
            message = "删除成功"
        else:
            model.is_active = False
            model.updated_by = current_user.id
            model.updated_at = datetime.now()
            await model.save()
            logger.info(f"AI模型软删除: {model.code}, 用户: {current_user.username}")
            message = "已禁用"
        
        return JSONResponse(
            status_code=200,
            content=create_response(
                data={"model_id": model_id},
                message=message
            )
        )
        
    except Exception as e:
        logger.error(f"删除AI模型失败: {e}")
        return JSONResponse(
            status_code=500,
            content=create_error_response(
                code=ErrorCodes.INTERNAL_ERROR,
                message=f"删除失败: {str(e)}"
            )
        )


# =====================================================
# 模型版本API
# =====================================================

@router.get("/{model_id}/versions", summary="获取模型版本列表")
async def list_model_versions(
    model_id: int,
    status: Optional[str] = Query(None, description="状态: staging/prod/archived"),
    current_user: User = Depends(get_current_active_user)
) -> JSONResponse:
    """
    获取指定模型的版本列表
    """
    try:
        AIModel = await get_model_class()
        AIModelVersion = await get_version_class()
        
        # 验证模型存在
        model = await AIModel.get_or_none(id=model_id)
        if not model:
            return JSONResponse(
                status_code=404,
                content=create_error_response(
                    code=ErrorCodes.MODEL_NOT_FOUND,
                    message=f"AI模型不存在: {model_id}"
                )
            )
        
        # 查询版本
        query = AIModelVersion.filter(model_id=model_id)
        if status:
            query = query.filter(status=status)
        
        versions = await query.order_by("-created_at")
        version_list = [await version_to_dict(v) for v in versions]
        
        return JSONResponse(
            status_code=200,
            content=create_response(
                data={
                    "model": await model_to_dict(model),
                    "versions": version_list,
                    "total": len(version_list)
                },
                message="获取成功"
            )
        )
        
    except Exception as e:
        logger.error(f"获取模型版本列表失败: {e}")
        return JSONResponse(
            status_code=500,
            content=create_error_response(
                code=ErrorCodes.INTERNAL_ERROR,
                message=f"查询失败: {str(e)}"
            )
        )


@router.post("/{model_id}/versions/{version}/deploy", summary="部署模型版本")
async def deploy_model_version(
    model_id: int,
    version: str,
    current_user: User = Depends(get_current_active_user)
) -> JSONResponse:
    """
    部署指定版本的模型到生产环境
    """
    try:
        AIModel = await get_model_class()
        AIModelVersion = await get_version_class()
        
        # 验证模型存在
        model = await AIModel.get_or_none(id=model_id)
        if not model:
            return JSONResponse(
                status_code=404,
                content=create_error_response(
                    code=ErrorCodes.MODEL_NOT_FOUND,
                    message=f"AI模型不存在: {model_id}"
                )
            )
        
        # 验证版本存在
        model_version = await AIModelVersion.get_or_none(model_id=model_id, version=version)
        if not model_version:
            return JSONResponse(
                status_code=404,
                content=create_error_response(
                    code=ErrorCodes.NOT_FOUND,
                    message=f"模型版本不存在: {version}"
                )
            )
        
        # 将其他版本设为archived
        await AIModelVersion.filter(model_id=model_id, status="prod").update(status="archived")
        
        # 部署当前版本
        model_version.status = "prod"
        model_version.deployed_at = datetime.now()
        model_version.deployed_by = current_user.id
        await model_version.save()
        
        # 更新模型状态
        model.status = "deployed"
        model.is_active = True
        model.updated_by = current_user.id
        await model.save()
        
        logger.info(f"模型版本部署成功: {model.code} v{version}, 用户: {current_user.username}")
        
        return JSONResponse(
            status_code=200,
            content=create_response(
                data=await version_to_dict(model_version),
                message="部署成功"
            )
        )
        
    except Exception as e:
        logger.error(f"部署模型版本失败: {e}")
        return JSONResponse(
            status_code=500,
            content=create_error_response(
                code=ErrorCodes.INTERNAL_ERROR,
                message=f"部署失败: {str(e)}"
            )
        )


# =====================================================
# 模型存储API
# =====================================================

@router.post("/{model_id}/upload", summary="上传模型文件")
async def upload_model_file(
    model_id: int,
    file: UploadFile = File(..., description="模型文件"),
    version: Optional[str] = Query(None, description="版本号"),
    current_user: User = Depends(get_current_active_user)
) -> JSONResponse:
    """
    上传模型文件
    """
    try:
        AIModel = await get_model_class()
        
        # 验证模型存在
        model = await AIModel.get_or_none(id=model_id)
        if not model:
            return JSONResponse(
                status_code=404,
                content=create_error_response(
                    code=ErrorCodes.MODEL_NOT_FOUND,
                    message=f"AI模型不存在: {model_id}"
                )
            )
        
        # 获取存储服务
        try:
            from ai_engine.model import get_model_storage_service
            storage_service = get_model_storage_service()
        except ImportError:
            return JSONResponse(
                status_code=500,
                content=create_error_response(
                    code=ErrorCodes.AI_ENGINE_ERROR,
                    message="模型存储模块未安装"
                )
            )
        
        # 验证文件格式
        if not file.filename:
            return JSONResponse(
                status_code=400,
                content=create_error_response(
                    code=ErrorCodes.BAD_REQUEST,
                    message="文件名不能为空"
                )
            )
        
        is_valid, ext = storage_service.backend.validate_format(file.filename)
        if not is_valid:
            return JSONResponse(
                status_code=400,
                content=create_error_response(
                    code=ErrorCodes.BAD_REQUEST,
                    message=f"不支持的文件格式: {file.filename}"
                )
            )
        
        # 读取并上传文件
        content = await file.read()
        file_obj = io.BytesIO(content)
        
        result = await storage_service.upload_model(
            file=file_obj,
            filename=file.filename,
            model_id=model_id,
            version=version
        )
        
        if result.success:
            return JSONResponse(
                status_code=200,
                content=create_response(
                    data={
                        "file_path": result.file_path,
                        "checksum": result.checksum,
                        "size_bytes": result.size_bytes
                    },
                    message="上传成功"
                )
            )
        else:
            return JSONResponse(
                status_code=500,
                content=create_error_response(
                    code=ErrorCodes.STORAGE_ERROR,
                    message=f"上传失败: {result.error}"
                )
            )
        
    except Exception as e:
        logger.error(f"上传模型文件失败: {e}")
        return JSONResponse(
            status_code=500,
            content=create_error_response(
                code=ErrorCodes.INTERNAL_ERROR,
                message=f"上传失败: {str(e)}"
            )
        )


@router.get("/{model_id}/download", summary="下载模型文件")
async def download_model_file(
    model_id: int,
    version: Optional[str] = Query(None, description="版本号"),
    current_user: User = Depends(get_current_active_user)
):
    """
    下载模型文件
    """
    try:
        AIModel = await get_model_class()
        AIModelVersion = await get_version_class()
        
        # 验证模型存在
        model = await AIModel.get_or_none(id=model_id)
        if not model:
            return JSONResponse(
                status_code=404,
                content=create_error_response(
                    code=ErrorCodes.MODEL_NOT_FOUND,
                    message=f"AI模型不存在: {model_id}"
                )
            )
        
        # 获取版本
        if version:
            model_version = await AIModelVersion.get_or_none(model_id=model_id, version=version)
        else:
            # 获取最新的prod版本
            model_version = await AIModelVersion.filter(model_id=model_id, status="prod").first()
            if not model_version:
                model_version = await AIModelVersion.filter(model_id=model_id).order_by("-created_at").first()
        
        if not model_version or not model_version.file_path:
            return JSONResponse(
                status_code=404,
                content=create_error_response(
                    code=ErrorCodes.NOT_FOUND,
                    message="模型文件不存在"
                )
            )
        
        # 获取存储服务
        try:
            from ai_engine.model import get_model_storage_service
            storage_service = get_model_storage_service()
        except ImportError:
            return JSONResponse(
                status_code=500,
                content=create_error_response(
                    code=ErrorCodes.AI_ENGINE_ERROR,
                    message="模型存储模块未安装"
                )
            )
        
        # 下载文件
        file_obj = await storage_service.download_model(model_version.file_path)
        content = file_obj.read()
        
        filename = model_version.file_path.split("/")[-1]
        
        return StreamingResponse(
            io.BytesIO(content),
            media_type="application/octet-stream",
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "Content-Length": str(len(content))
            }
        )
        
    except Exception as e:
        logger.error(f"下载模型文件失败: {e}")
        return JSONResponse(
            status_code=500,
            content=create_error_response(
                code=ErrorCodes.INTERNAL_ERROR,
                message=f"下载失败: {str(e)}"
            )
        )
