"""
资产管理API v4
实现资产CRUD操作，使用统一响应格式

Requirements: 6.1, 7.4 - 服务调用路径统一
"""
from typing import Optional, List
from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from datetime import datetime

from app.core.auth_dependencies import get_current_active_user
from app.core.unified_logger import get_logger
from app.models.admin import User
from app.services.platform_services import (
    asset_service,
    asset_category_service,
    tdengine_service
)

from .schemas import (
    AssetCreate,
    AssetUpdate,
    AssetResponse,
    ErrorCodes,
    PageMeta,
    create_response,
    create_error_response,
    create_paginated_response
)

logger = get_logger(__name__)
router = APIRouter()


# =====================================================
# 辅助函数
# =====================================================

async def get_asset_model():
    """延迟导入Asset模型（仅用于直接数据库操作）"""
    from app.models.platform_upgrade import Asset
    return Asset


async def get_category_model():
    """延迟导入AssetCategory模型（仅用于直接数据库操作）"""
    from app.models.platform_upgrade import AssetCategory
    return AssetCategory


async def asset_to_dict(asset, include_category: bool = False) -> dict:
    """将资产转换为字典"""
    result = {
        "id": asset.id,
        "code": asset.code,
        "name": asset.name,
        "category_id": asset.category_id,
        "location": asset.location,
        "status": asset.status,
        "attributes": asset.attributes or {},
        "manufacturer": asset.manufacturer,
        "model": asset.model,
        "serial_number": asset.serial_number,
        "install_date": asset.install_date.isoformat() if asset.install_date else None,
        "department": asset.department,
        "team": asset.team,
        "ip_address": asset.ip_address,
        "mac_address": asset.mac_address,
        "is_locked": asset.is_locked,
        "is_active": asset.is_active,
        "created_at": asset.created_at.isoformat() if asset.created_at else None,
        "updated_at": asset.updated_at.isoformat() if asset.updated_at else None
    }
    
    if include_category and hasattr(asset, 'category') and asset.category:
        result["category"] = {
            "id": asset.category.id,
            "code": asset.category.code,
            "name": asset.category.name,
            "industry": asset.category.industry,
            "icon": asset.category.icon,
            "tdengine_database": asset.category.tdengine_database,
            "tdengine_stable_prefix": asset.category.tdengine_stable_prefix,
            "is_active": asset.category.is_active,
            "asset_count": asset.category.asset_count
        }
    
    return result


# =====================================================
# 资产CRUD API
# =====================================================

@router.post("", summary="创建资产")
async def create_asset(
    asset_data: AssetCreate,
    current_user: User = Depends(get_current_active_user)
) -> JSONResponse:
    """
    创建新资产
    
    - 自动创建TDengine子表
    - 更新资产类别的资产计数
    """
    try:
        Asset = await get_asset_model()
        AssetCategory = await get_category_model()
        
        # 1. 验证资产类别存在
        category = await AssetCategory.get_or_none(id=asset_data.category_id)
        if not category:
            return JSONResponse(
                status_code=404,
                content=create_error_response(
                    code=ErrorCodes.CATEGORY_NOT_FOUND,
                    message=f"资产类别不存在: {asset_data.category_id}"
                )
            )
        
        if not category.is_active:
            return JSONResponse(
                status_code=400,
                content=create_error_response(
                    code=ErrorCodes.INVALID_STATUS,
                    message=f"资产类别已禁用: {category.name}"
                )
            )
        
        # 2. 检查资产编号唯一性
        existing = await Asset.filter(code=asset_data.code).first()
        if existing:
            return JSONResponse(
                status_code=409,
                content=create_error_response(
                    code=ErrorCodes.DUPLICATE_CODE,
                    message=f"资产编号 '{asset_data.code}' 已存在"
                )
            )
        
        # 3. 创建资产
        asset = Asset(
            code=asset_data.code,
            name=asset_data.name,
            category_id=asset_data.category_id,
            location=asset_data.location,
            attributes=asset_data.attributes or {},
            manufacturer=asset_data.manufacturer,
            model=asset_data.model,
            serial_number=asset_data.serial_number,
            install_date=asset_data.install_date,
            department=asset_data.department,
            team=asset_data.team,
            ip_address=asset_data.ip_address,
            mac_address=asset_data.mac_address,
            status="offline",
            is_locked=False,
            is_active=True
        )
        await asset.save()
        
        # 4. 更新资产类别计数
        category.asset_count = await Asset.filter(category_id=category.id, is_active=True).count()
        await category.save()
        
        logger.info(f"资产创建成功: {asset_data.code}, 类别: {category.code}, 用户: {current_user.username}")
        
        # 5. 创建TDengine子表（使用platform_services适配器）
        try:
            stable_name = f"raw_{category.code}"
            await tdengine_service.create_child_table(
                stable_name=stable_name,
                asset_code=asset_data.code,
                asset_id=asset.id,
                database=category.tdengine_database
            )
            logger.info(f"TDengine子表创建成功: {stable_name}_{asset_data.code}")
        except Exception as e:
            logger.warning(f"TDengine子表创建失败: {e}")
        
        # 6. 返回完整资产信息
        asset.category = category
        return JSONResponse(
            status_code=201,
            content=create_response(
                data=await asset_to_dict(asset, include_category=True),
                message="资产创建成功"
            )
        )
        
    except Exception as e:
        logger.error(f"创建资产失败: {e}")
        return JSONResponse(
            status_code=500,
            content=create_error_response(
                code=ErrorCodes.INTERNAL_ERROR,
                message=f"创建失败: {str(e)}"
            )
        )


@router.get("", summary="获取资产列表")
async def list_assets(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    category_id: Optional[int] = Query(None, description="资产类别ID"),
    category_code: Optional[str] = Query(None, description="资产类别编码"),
    status: Optional[str] = Query(None, description="状态: online/offline/error/maintenance"),
    location: Optional[str] = Query(None, description="位置"),
    department: Optional[str] = Query(None, description="部门"),
    is_active: Optional[bool] = Query(None, description="是否激活"),
    keyword: Optional[str] = Query(None, description="搜索关键词"),
    current_user: User = Depends(get_current_active_user)
) -> JSONResponse:
    """
    获取资产列表（分页）
    
    支持多种筛选条件
    """
    try:
        Asset = await get_asset_model()
        AssetCategory = await get_category_model()
        
        # 1. 构建查询条件
        query = Asset.all()
        
        if category_id:
            query = query.filter(category_id=category_id)
        if category_code:
            category = await AssetCategory.get_or_none(code=category_code)
            if category:
                query = query.filter(category_id=category.id)
        if status:
            query = query.filter(status=status)
        if location:
            query = query.filter(location__icontains=location)
        if department:
            query = query.filter(department=department)
        if is_active is not None:
            query = query.filter(is_active=is_active)
        if keyword:
            query = query.filter(name__icontains=keyword) | query.filter(code__icontains=keyword)
        
        # 2. 分页查询
        total = await query.count()
        offset = (page - 1) * page_size
        assets = await query.prefetch_related("category").order_by("-created_at").offset(offset).limit(page_size)
        
        # 3. 转换为字典列表
        asset_list = [await asset_to_dict(asset, include_category=True) for asset in assets]
        
        return JSONResponse(
            status_code=200,
            content=create_paginated_response(
                data=asset_list,
                total=total,
                page=page,
                page_size=page_size,
                message="获取成功"
            )
        )
        
    except Exception as e:
        logger.error(f"获取资产列表失败: {e}")
        return JSONResponse(
            status_code=500,
            content=create_error_response(
                code=ErrorCodes.INTERNAL_ERROR,
                message=f"查询失败: {str(e)}"
            )
        )


@router.get("/{asset_id}", summary="获取资产详情")
async def get_asset(
    asset_id: int,
    current_user: User = Depends(get_current_active_user)
) -> JSONResponse:
    """
    获取单个资产详情
    """
    try:
        Asset = await get_asset_model()
        
        asset = await Asset.get_or_none(id=asset_id).prefetch_related("category")
        if not asset:
            return JSONResponse(
                status_code=404,
                content=create_error_response(
                    code=ErrorCodes.ASSET_NOT_FOUND,
                    message=f"资产不存在: {asset_id}"
                )
            )
        
        return JSONResponse(
            status_code=200,
            content=create_response(
                data=await asset_to_dict(asset, include_category=True),
                message="获取成功"
            )
        )
        
    except Exception as e:
        logger.error(f"获取资产详情失败: {e}")
        return JSONResponse(
            status_code=500,
            content=create_error_response(
                code=ErrorCodes.INTERNAL_ERROR,
                message=f"查询失败: {str(e)}"
            )
        )


@router.put("/{asset_id}", summary="更新资产")
async def update_asset(
    asset_id: int,
    asset_data: AssetUpdate,
    current_user: User = Depends(get_current_active_user)
) -> JSONResponse:
    """
    更新资产信息
    
    注意：code和category_id字段不可修改
    """
    try:
        Asset = await get_asset_model()
        
        asset = await Asset.get_or_none(id=asset_id).prefetch_related("category")
        if not asset:
            return JSONResponse(
                status_code=404,
                content=create_error_response(
                    code=ErrorCodes.ASSET_NOT_FOUND,
                    message=f"资产不存在: {asset_id}"
                )
            )
        
        if asset.is_locked:
            return JSONResponse(
                status_code=400,
                content=create_error_response(
                    code=ErrorCodes.RESOURCE_LOCKED,
                    message="资产已锁定，无法修改"
                )
            )
        
        # 更新字段
        update_data = asset_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(asset, field, value)
        
        asset.updated_at = datetime.now()
        await asset.save()
        
        logger.info(f"资产更新成功: {asset.code}, 用户: {current_user.username}")
        
        return JSONResponse(
            status_code=200,
            content=create_response(
                data=await asset_to_dict(asset, include_category=True),
                message="更新成功"
            )
        )
        
    except Exception as e:
        logger.error(f"更新资产失败: {e}")
        return JSONResponse(
            status_code=500,
            content=create_error_response(
                code=ErrorCodes.INTERNAL_ERROR,
                message=f"更新失败: {str(e)}"
            )
        )


@router.delete("/{asset_id}", summary="删除资产")
async def delete_asset(
    asset_id: int,
    force: bool = Query(False, description="是否强制删除"),
    current_user: User = Depends(get_current_active_user)
) -> JSONResponse:
    """
    删除资产
    
    - 默认软删除（设置is_active=False）
    - force=True时物理删除
    """
    try:
        Asset = await get_asset_model()
        AssetCategory = await get_category_model()
        
        asset = await Asset.get_or_none(id=asset_id)
        if not asset:
            return JSONResponse(
                status_code=404,
                content=create_error_response(
                    code=ErrorCodes.ASSET_NOT_FOUND,
                    message=f"资产不存在: {asset_id}"
                )
            )
        
        if asset.is_locked:
            return JSONResponse(
                status_code=400,
                content=create_error_response(
                    code=ErrorCodes.RESOURCE_LOCKED,
                    message="资产已锁定，无法删除"
                )
            )
        
        category_id = asset.category_id
        
        if force:
            await asset.delete()
            logger.info(f"资产物理删除: {asset.code}, 用户: {current_user.username}")
            message = "删除成功"
        else:
            asset.is_active = False
            asset.updated_at = datetime.now()
            await asset.save()
            logger.info(f"资产软删除: {asset.code}, 用户: {current_user.username}")
            message = "已禁用"
        
        # 更新资产类别计数
        category = await AssetCategory.get_or_none(id=category_id)
        if category:
            category.asset_count = await Asset.filter(category_id=category_id, is_active=True).count()
            await category.save()
        
        return JSONResponse(
            status_code=200,
            content=create_response(
                data={"asset_id": asset_id},
                message=message
            )
        )
        
    except Exception as e:
        logger.error(f"删除资产失败: {e}")
        return JSONResponse(
            status_code=500,
            content=create_error_response(
                code=ErrorCodes.INTERNAL_ERROR,
                message=f"删除失败: {str(e)}"
            )
        )


@router.get("/{asset_id}/history", summary="获取资产历史数据")
async def get_history_data(
    asset_id: int,
    start_time: str = Query(..., description="开始时间"),
    end_time: str = Query(..., description="结束时间"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(100, ge=1, le=2000, description="每页数量"),
    current_user: User = Depends(get_current_active_user)
) -> JSONResponse:
    """
    获取资产历史数据 (从TDengine)
    """
    try:
        Asset = await get_asset_model()
        asset = await Asset.get_or_none(id=asset_id).prefetch_related("category")
        
        if not asset:
            return JSONResponse(
                status_code=404, 
                content=create_error_response(code=ErrorCodes.ASSET_NOT_FOUND, message="资产不存在")
            )
            
        if not asset.category:
             return JSONResponse(
                 status_code=400, 
                 content=create_error_response(code=ErrorCodes.INVALID_PARAMS, message="资产未关联类别")
             )
        
        database = asset.category.tdengine_database
        stable = asset.category.tdengine_stable_prefix
        
        if not database or not stable:
            return JSONResponse(
                status_code=200,
                content=create_paginated_response(
                    data=[],
                    total=0,
                    page=page,
                    page_size=page_size,
                    message="该资产类别未配置TDengine存储"
                )
            )
        
        offset = (page - 1) * page_size
        
        # 查询数据
        # 注意：假设STable中有 device_code 标签
        sql = f"SELECT * FROM {database}.{stable} WHERE device_code='{asset.code}' AND ts >= '{start_time}' AND ts <= '{end_time}' ORDER BY ts DESC LIMIT {page_size} OFFSET {offset}"
        
        result = await tdengine_service.execute_query(sql, database)
        data = result.get("data", [])
        
        # 获取总数 (可选，为了性能可能需要优化)
        count_sql = f"SELECT count(*) FROM {database}.{stable} WHERE device_code='{asset.code}' AND ts >= '{start_time}' AND ts <= '{end_time}'"
        count_res = await tdengine_service.execute_query(count_sql, database)
        total = 0
        if count_res and count_res.get("data"):
            # TDengine count result format depends on driver, usually [{"count(*)": 123}] or [[123]]
            # Assuming list of dicts or list of lists
            rows = count_res.get("data")
            if isinstance(rows, list) and len(rows) > 0:
                first_row = rows[0]
                if isinstance(first_row, dict):
                    total = list(first_row.values())[0]
                elif isinstance(first_row, (list, tuple)):
                    total = first_row[0]
        
        return JSONResponse(
            status_code=200,
            content=create_paginated_response(
                data=data,
                total=total,
                page=page,
                page_size=page_size,
                message="获取成功"
            )
        )
        
    except Exception as e:
        logger.error(f"获取历史数据失败: {e}")
        return JSONResponse(
            status_code=500,
            content=create_error_response(
                code=ErrorCodes.INTERNAL_ERROR,
                message=f"查询失败: {str(e)}"
            )
        )


# =====================================================
# 批量操作API
# =====================================================

@router.post("/batch/status", summary="批量更新资产状态")
async def batch_update_status(
    asset_ids: List[int] = Query(..., description="资产ID列表"),
    status: str = Query(..., description="目标状态"),
    current_user: User = Depends(get_current_active_user)
) -> JSONResponse:
    """
    批量更新资产状态
    """
    try:
        Asset = await get_asset_model()
        
        valid_statuses = ["online", "offline", "error", "maintenance"]
        if status not in valid_statuses:
            return JSONResponse(
                status_code=400,
                content=create_error_response(
                    code=ErrorCodes.INVALID_STATUS,
                    message=f"无效状态: {status}，支持: {', '.join(valid_statuses)}"
                )
            )
        
        updated_count = await Asset.filter(id__in=asset_ids, is_locked=False).update(
            status=status,
            updated_at=datetime.now()
        )
        
        logger.info(f"批量更新资产状态: {updated_count}个, 状态: {status}, 用户: {current_user.username}")
        
        return JSONResponse(
            status_code=200,
            content=create_response(
                data={"updated_count": updated_count},
                message=f"成功更新 {updated_count} 个资产状态"
            )
        )
        
    except Exception as e:
        logger.error(f"批量更新状态失败: {e}")
        return JSONResponse(
            status_code=500,
            content=create_error_response(
                code=ErrorCodes.INTERNAL_ERROR,
                message=f"更新失败: {str(e)}"
            )
        )
