"""
资产类别管理API v4
实现资产类别CRUD操作，使用统一响应格式

Requirements: 6.1, 7.4 - 服务调用路径统一
"""
from typing import Optional
from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from datetime import datetime

from app.core.auth_dependencies import get_current_active_user
from app.core.unified_logger import get_logger
from app.models.admin import User
from app.services.platform_services import (
    asset_category_service,
    tdengine_service
)

from .schemas import (
    AssetCategoryCreate,
    AssetCategoryUpdate,
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

async def get_category_model():
    """延迟导入AssetCategory模型（仅用于直接数据库操作）"""
    from app.models.platform_upgrade import AssetCategory
    return AssetCategory


async def get_asset_model():
    """延迟导入Asset模型（仅用于直接数据库操作）"""
    from app.models.platform_upgrade import Asset
    return Asset


async def category_to_dict(category) -> dict:
    """将资产类别转换为字典"""
    return {
        "id": category.id,
        "code": category.code,
        "name": category.name,
        "description": category.description,
        "industry": category.industry,
        "icon": category.icon,
        "tdengine_database": category.tdengine_database,
        "tdengine_stable_prefix": category.tdengine_stable_prefix,
        "is_active": category.is_active,
        "asset_count": category.asset_count,
        "config": category.config,
        "created_at": category.created_at.isoformat() if category.created_at else None,
        "updated_at": category.updated_at.isoformat() if category.updated_at else None
    }


# =====================================================
# 资产类别CRUD API
# =====================================================

@router.post("", summary="创建资产类别")
async def create_category(
    category_data: AssetCategoryCreate,
    current_user: User = Depends(get_current_active_user)
) -> JSONResponse:
    """
    创建新的资产类别
    
    - 自动生成TDengine超级表前缀
    - 初始化TDengine Schema（如果有信号定义）
    """
    try:
        AssetCategory = await get_category_model()
        
        # 1. 检查编码唯一性
        existing = await AssetCategory.filter(code=category_data.code).first()
        if existing:
            return JSONResponse(
                status_code=409,
                content=create_error_response(
                    code=ErrorCodes.DUPLICATE_CODE,
                    message=f"类别编码 '{category_data.code}' 已存在"
                )
            )
        
        # 2. 创建类别
        tdengine_db = category_data.tdengine_database or "devicemonitor"
        category = AssetCategory(
            code=category_data.code,
            name=category_data.name,
            description=category_data.description,
            industry=category_data.industry,
            icon=category_data.icon,
            tdengine_database=tdengine_db,
            tdengine_stable_prefix=f"raw_{category_data.code}",
            config=category_data.config,
            is_active=True,
            asset_count=0
        )
        await category.save()
        
        logger.info(f"资产类别创建成功: {category_data.code}, 用户: {current_user.username}")
        
        # 3. 尝试初始化TDengine Schema（使用platform_services适配器）
        try:
            await tdengine_service.sync_category_schema(category_data.code)
        except Exception as e:
            logger.warning(f"Schema初始化跳过（无信号定义）: {e}")
        
        return JSONResponse(
            status_code=201,
            content=create_response(
                data=await category_to_dict(category),
                message="资产类别创建成功"
            )
        )
        
    except Exception as e:
        logger.error(f"创建资产类别失败: {e}")
        return JSONResponse(
            status_code=500,
            content=create_error_response(
                code=ErrorCodes.INTERNAL_ERROR,
                message=f"创建失败: {str(e)}"
            )
        )


@router.get("", summary="获取资产类别列表")
async def list_categories(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    is_active: Optional[bool] = Query(None, description="是否激活"),
    industry: Optional[str] = Query(None, description="所属行业"),
    keyword: Optional[str] = Query(None, description="搜索关键词"),
    current_user: User = Depends(get_current_active_user)
) -> JSONResponse:
    """
    获取资产类别列表（分页）
    
    支持按激活状态、行业、关键词筛选
    """
    try:
        AssetCategory = await get_category_model()
        
        # 1. 构建查询条件
        query = AssetCategory.all()
        
        if is_active is not None:
            query = query.filter(is_active=is_active)
        if industry:
            query = query.filter(industry=industry)
        if keyword:
            query = query.filter(name__icontains=keyword) | query.filter(code__icontains=keyword)
        
        # 2. 分页查询
        total = await query.count()
        offset = (page - 1) * page_size
        categories = await query.order_by("-created_at").offset(offset).limit(page_size)
        
        # 3. 转换为字典列表
        category_list = [await category_to_dict(cat) for cat in categories]
        
        return JSONResponse(
            status_code=200,
            content=create_paginated_response(
                data=category_list,
                total=total,
                page=page,
                page_size=page_size,
                message="获取成功"
            )
        )
        
    except Exception as e:
        logger.error(f"获取资产类别列表失败: {e}")
        return JSONResponse(
            status_code=500,
            content=create_error_response(
                code=ErrorCodes.INTERNAL_ERROR,
                message=f"查询失败: {str(e)}"
            )
        )


@router.get("/{category_id}", summary="获取资产类别详情")
async def get_category(
    category_id: int,
    current_user: User = Depends(get_current_active_user)
) -> JSONResponse:
    """
    获取单个资产类别详情
    """
    try:
        AssetCategory = await get_category_model()
        
        category = await AssetCategory.get_or_none(id=category_id)
        if not category:
            return JSONResponse(
                status_code=404,
                content=create_error_response(
                    code=ErrorCodes.CATEGORY_NOT_FOUND,
                    message=f"资产类别不存在: {category_id}"
                )
            )
        
        return JSONResponse(
            status_code=200,
            content=create_response(
                data=await category_to_dict(category),
                message="获取成功"
            )
        )
        
    except Exception as e:
        logger.error(f"获取资产类别详情失败: {e}")
        return JSONResponse(
            status_code=500,
            content=create_error_response(
                code=ErrorCodes.INTERNAL_ERROR,
                message=f"查询失败: {str(e)}"
            )
        )


@router.put("/{category_id}", summary="更新资产类别")
async def update_category(
    category_id: int,
    category_data: AssetCategoryUpdate,
    current_user: User = Depends(get_current_active_user)
) -> JSONResponse:
    """
    更新资产类别信息
    
    注意：code字段不可修改
    """
    try:
        AssetCategory = await get_category_model()
        
        category = await AssetCategory.get_or_none(id=category_id)
        if not category:
            return JSONResponse(
                status_code=404,
                content=create_error_response(
                    code=ErrorCodes.CATEGORY_NOT_FOUND,
                    message=f"资产类别不存在: {category_id}"
                )
            )
        
        # 更新字段
        update_data = category_data.model_dump(exclude_unset=True)
        
        # 处理颜色字段
        if "color" in update_data:
            color = update_data.pop("color")
            if color:
                category.config = category.config or {}
                category.config["color"] = color
        
        for field, value in update_data.items():
            setattr(category, field, value)
        
        category.updated_at = datetime.now()
        await category.save()
        
        logger.info(f"资产类别更新成功: {category.code}, 用户: {current_user.username}")
        
        return JSONResponse(
            status_code=200,
            content=create_response(
                data=await category_to_dict(category),
                message="更新成功"
            )
        )
        
    except Exception as e:
        logger.error(f"更新资产类别失败: {e}")
        return JSONResponse(
            status_code=500,
            content=create_error_response(
                code=ErrorCodes.INTERNAL_ERROR,
                message=f"更新失败: {str(e)}"
            )
        )


@router.delete("/{category_id}", summary="删除资产类别")
async def delete_category(
    category_id: int,
    force: bool = Query(False, description="是否强制删除"),
    current_user: User = Depends(get_current_active_user)
) -> JSONResponse:
    """
    删除资产类别
    
    - 默认软删除（设置is_active=False）
    - force=True时物理删除（需要无关联资产）
    """
    try:
        AssetCategory = await get_category_model()
        Asset = await get_asset_model()
        
        category = await AssetCategory.get_or_none(id=category_id)
        if not category:
            return JSONResponse(
                status_code=404,
                content=create_error_response(
                    code=ErrorCodes.CATEGORY_NOT_FOUND,
                    message=f"资产类别不存在: {category_id}"
                )
            )
        
        # 检查是否有关联资产
        asset_count = await Asset.filter(category_id=category_id).count()
        
        if force:
            if asset_count > 0:
                return JSONResponse(
                    status_code=400,
                    content=create_error_response(
                        code=ErrorCodes.DEPENDENCY_EXISTS,
                        message=f"无法删除：该类别下有 {asset_count} 个资产"
                    )
                )
            await category.delete()
            logger.info(f"资产类别物理删除: {category.code}, 用户: {current_user.username}")
            message = "删除成功"
        else:
            # 软删除
            category.is_active = False
            category.updated_at = datetime.now()
            await category.save()
            logger.info(f"资产类别软删除: {category.code}, 用户: {current_user.username}")
            message = "已禁用"
        
        return JSONResponse(
            status_code=200,
            content=create_response(
                data={"category_id": category_id},
                message=message
            )
        )
        
    except Exception as e:
        logger.error(f"删除资产类别失败: {e}")
        return JSONResponse(
            status_code=500,
            content=create_error_response(
                code=ErrorCodes.INTERNAL_ERROR,
                message=f"删除失败: {str(e)}"
            )
        )


# =====================================================
# Schema同步API
# =====================================================

@router.post("/{category_id}/sync-schema", summary="同步TDengine Schema")
async def sync_category_schema(
    category_id: int,
    current_user: User = Depends(get_current_active_user)
) -> JSONResponse:
    """
    手动同步资产类别的TDengine Schema
    
    - 根据信号定义创建/更新超级表结构
    - 记录Schema版本变更
    """
    try:
        AssetCategory = await get_category_model()
        
        # 1. 验证类别存在
        category = await AssetCategory.get_or_none(id=category_id)
        if not category:
            return JSONResponse(
                status_code=404,
                content=create_error_response(
                    code=ErrorCodes.CATEGORY_NOT_FOUND,
                    message=f"资产类别不存在: {category_id}"
                )
            )
        
        # 2. 同步Schema（使用platform_services适配器）
        try:
            success = await tdengine_service.sync_category_schema(category.code)
            
            if success:
                logger.info(f"Schema同步成功: {category.code}, 用户: {current_user.username}")
                return JSONResponse(
                    status_code=200,
                    content=create_response(
                        data={
                            "category_code": category.code,
                            "stable_name": f"raw_{category.code}",
                            "database": category.tdengine_database
                        },
                        message="Schema同步成功"
                    )
                )
            else:
                return JSONResponse(
                    status_code=500,
                    content=create_error_response(
                        code=ErrorCodes.TDENGINE_ERROR,
                        message="Schema同步失败"
                    )
                )
        except Exception as e:
            return JSONResponse(
                status_code=500,
                content=create_error_response(
                    code=ErrorCodes.TDENGINE_ERROR,
                    message=f"Schema同步失败: {str(e)}"
                )
            )
        
    except Exception as e:
        logger.error(f"Schema同步失败: {e}")
        return JSONResponse(
            status_code=500,
            content=create_error_response(
                code=ErrorCodes.INTERNAL_ERROR,
                message=f"同步失败: {str(e)}"
            )
        )
