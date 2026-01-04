"""
信号定义管理API v4
实现信号定义CRUD操作，使用统一响应格式

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
    signal_service,
    tdengine_service
)

from .schemas import (
    SignalDefinitionCreate,
    SignalDefinitionUpdate,
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

async def get_signal_model():
    """延迟导入SignalDefinition模型（仅用于直接数据库操作）"""
    from app.models.platform_upgrade import SignalDefinition
    return SignalDefinition


async def get_category_model():
    """延迟导入AssetCategory模型（仅用于直接数据库操作）"""
    from app.models.platform_upgrade import AssetCategory
    return AssetCategory


async def signal_to_dict(signal) -> dict:
    """将信号定义转换为字典"""
    return {
        "id": signal.id,
        "category_id": signal.category_id,
        "code": signal.code,
        "name": signal.name,
        "data_type": signal.data_type,
        "unit": signal.unit,
        "is_stored": signal.is_stored,
        "is_realtime": signal.is_realtime,
        "is_feature": signal.is_feature,
        "is_alarm_enabled": signal.is_alarm_enabled,
        "value_range": signal.value_range,
        "validation_rules": signal.validation_rules,
        "alarm_threshold": signal.alarm_threshold,
        "aggregation_method": signal.aggregation_method,
        "display_config": signal.display_config,
        "sort_order": signal.sort_order,
        "field_group": signal.field_group,
        "is_default_visible": signal.is_default_visible,
        "is_active": signal.is_active,
        "created_at": signal.created_at.isoformat() if signal.created_at else None,
        "updated_at": signal.updated_at.isoformat() if signal.updated_at else None
    }


# =====================================================
# 信号定义CRUD API
# =====================================================

@router.post("", summary="创建信号定义")
async def create_signal(
    signal_data: SignalDefinitionCreate,
    current_user: User = Depends(get_current_active_user)
) -> JSONResponse:
    """
    创建信号定义
    
    - 自动同步TDengine Schema
    - 验证数据类型有效性
    """
    try:
        SignalDefinition = await get_signal_model()
        AssetCategory = await get_category_model()
        
        # 1. 验证类别存在
        category = await AssetCategory.get_or_none(id=signal_data.category_id)
        if not category:
            return JSONResponse(
                status_code=404,
                content=create_error_response(
                    code=ErrorCodes.CATEGORY_NOT_FOUND,
                    message=f"资产类别不存在: {signal_data.category_id}"
                )
            )
        
        # 2. 验证数据类型
        valid_types = ["float", "int", "bool", "string", "double", "bigint", "timestamp"]
        if signal_data.data_type.lower() not in valid_types:
            return JSONResponse(
                status_code=400,
                content=create_error_response(
                    code=ErrorCodes.BAD_REQUEST,
                    message=f"无效的数据类型: {signal_data.data_type}，支持: {', '.join(valid_types)}"
                )
            )
        
        # 3. 检查信号编码唯一性
        existing = await SignalDefinition.filter(
            category_id=signal_data.category_id,
            code=signal_data.code
        ).first()
        if existing:
            return JSONResponse(
                status_code=409,
                content=create_error_response(
                    code=ErrorCodes.DUPLICATE_CODE,
                    message=f"信号编码 '{signal_data.code}' 在该类别下已存在"
                )
            )
        
        # 4. 创建信号定义
        signal = SignalDefinition(
            category_id=signal_data.category_id,
            code=signal_data.code,
            name=signal_data.name,
            data_type=signal_data.data_type.lower(),
            unit=signal_data.unit,
            is_stored=signal_data.is_stored,
            is_realtime=signal_data.is_realtime,
            is_feature=signal_data.is_feature,
            is_alarm_enabled=signal_data.is_alarm_enabled,
            value_range=signal_data.value_range,
            validation_rules=signal_data.validation_rules,
            alarm_threshold=signal_data.alarm_threshold,
            aggregation_method=signal_data.aggregation_method,
            display_config=signal_data.display_config,
            sort_order=signal_data.sort_order,
            field_group=signal_data.field_group,
            is_default_visible=signal_data.is_default_visible,
            is_active=True
        )
        await signal.save()
        
        logger.info(f"信号定义创建成功: {category.code}.{signal_data.code}, 用户: {current_user.username}")
        
        # 5. 同步TDengine Schema（使用platform_services适配器）
        if signal_data.is_stored:
            try:
                await tdengine_service.sync_category_schema(category.code)
                logger.info(f"TDengine Schema同步成功: {category.code}")
            except Exception as e:
                logger.warning(f"TDengine Schema同步失败: {e}")
        
        return JSONResponse(
            status_code=201,
            content=create_response(
                data=await signal_to_dict(signal),
                message="信号定义创建成功"
            )
        )
        
    except Exception as e:
        logger.error(f"创建信号定义失败: {e}")
        return JSONResponse(
            status_code=500,
            content=create_error_response(
                code=ErrorCodes.INTERNAL_ERROR,
                message=f"创建失败: {str(e)}"
            )
        )


@router.get("", summary="获取信号定义列表")
async def list_signals(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    category_id: Optional[int] = Query(None, description="资产类别ID"),
    is_active: Optional[bool] = Query(None, description="是否激活"),
    is_stored: Optional[bool] = Query(None, description="是否存储"),
    is_realtime: Optional[bool] = Query(None, description="是否实时"),
    is_feature: Optional[bool] = Query(None, description="是否特征"),
    field_group: Optional[str] = Query(None, description="字段分组"),
    keyword: Optional[str] = Query(None, description="搜索关键词"),
    current_user: User = Depends(get_current_active_user)
) -> JSONResponse:
    """
    获取信号定义列表（分页）
    
    支持多种筛选条件
    """
    try:
        SignalDefinition = await get_signal_model()
        
        # 1. 构建查询条件
        query = SignalDefinition.all()
        
        if category_id:
            query = query.filter(category_id=category_id)
        if is_active is not None:
            query = query.filter(is_active=is_active)
        if is_stored is not None:
            query = query.filter(is_stored=is_stored)
        if is_realtime is not None:
            query = query.filter(is_realtime=is_realtime)
        if is_feature is not None:
            query = query.filter(is_feature=is_feature)
        if field_group:
            query = query.filter(field_group=field_group)
        if keyword:
            query = query.filter(name__icontains=keyword) | query.filter(code__icontains=keyword)
        
        # 2. 分页查询
        total = await query.count()
        offset = (page - 1) * page_size
        signals = await query.order_by("sort_order", "id").offset(offset).limit(page_size)
        
        # 3. 转换为字典列表
        signal_list = [await signal_to_dict(sig) for sig in signals]
        
        return JSONResponse(
            status_code=200,
            content=create_paginated_response(
                data=signal_list,
                total=total,
                page=page,
                page_size=page_size,
                message="获取成功"
            )
        )
        
    except Exception as e:
        logger.error(f"获取信号定义列表失败: {e}")
        return JSONResponse(
            status_code=500,
            content=create_error_response(
                code=ErrorCodes.INTERNAL_ERROR,
                message=f"查询失败: {str(e)}"
            )
        )


@router.get("/{signal_id}", summary="获取信号定义详情")
async def get_signal(
    signal_id: int,
    current_user: User = Depends(get_current_active_user)
) -> JSONResponse:
    """
    获取单个信号定义详情
    """
    try:
        SignalDefinition = await get_signal_model()
        
        signal = await SignalDefinition.get_or_none(id=signal_id)
        if not signal:
            return JSONResponse(
                status_code=404,
                content=create_error_response(
                    code=ErrorCodes.SIGNAL_NOT_FOUND,
                    message=f"信号定义不存在: {signal_id}"
                )
            )
        
        result = await signal_to_dict(signal)
        
        # 获取关联的类别信息
        AssetCategory = await get_category_model()
        category = await AssetCategory.get_or_none(id=signal.category_id)
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
        logger.error(f"获取信号定义详情失败: {e}")
        return JSONResponse(
            status_code=500,
            content=create_error_response(
                code=ErrorCodes.INTERNAL_ERROR,
                message=f"查询失败: {str(e)}"
            )
        )


@router.put("/{signal_id}", summary="更新信号定义")
async def update_signal(
    signal_id: int,
    signal_data: SignalDefinitionUpdate,
    current_user: User = Depends(get_current_active_user)
) -> JSONResponse:
    """
    更新信号定义
    
    注意：code和data_type字段不可修改
    """
    try:
        SignalDefinition = await get_signal_model()
        AssetCategory = await get_category_model()
        
        # 1. 验证信号存在
        signal = await SignalDefinition.get_or_none(id=signal_id)
        if not signal:
            return JSONResponse(
                status_code=404,
                content=create_error_response(
                    code=ErrorCodes.SIGNAL_NOT_FOUND,
                    message=f"信号定义不存在: {signal_id}"
                )
            )
        
        # 2. 获取类别信息
        category = await AssetCategory.get_or_none(id=signal.category_id)
        
        # 3. 更新字段
        update_data = signal_data.model_dump(exclude_unset=True)
        old_is_stored = signal.is_stored
        
        for field, value in update_data.items():
            setattr(signal, field, value)
        
        signal.updated_at = datetime.now()
        await signal.save()
        
        logger.info(f"信号定义更新成功: {category.code if category else 'unknown'}.{signal.code}, 用户: {current_user.username}")
        
        # 4. 如果is_stored状态变化，同步Schema（使用platform_services适配器）
        new_is_stored = signal.is_stored
        if old_is_stored != new_is_stored and category:
            try:
                await tdengine_service.sync_category_schema(category.code)
                logger.info(f"TDengine Schema同步成功: {category.code}")
            except Exception as e:
                logger.warning(f"TDengine Schema同步失败: {e}")
        
        return JSONResponse(
            status_code=200,
            content=create_response(
                data=await signal_to_dict(signal),
                message="更新成功"
            )
        )
        
    except Exception as e:
        logger.error(f"更新信号定义失败: {e}")
        return JSONResponse(
            status_code=500,
            content=create_error_response(
                code=ErrorCodes.INTERNAL_ERROR,
                message=f"更新失败: {str(e)}"
            )
        )


@router.delete("/{signal_id}", summary="删除信号定义")
async def delete_signal(
    signal_id: int,
    force: bool = Query(False, description="是否强制删除"),
    current_user: User = Depends(get_current_active_user)
) -> JSONResponse:
    """
    删除信号定义
    
    - 默认软删除（设置is_active=False）
    - force=True时物理删除
    - 注意：TDengine不支持删除列，物理删除后列仍存在
    """
    try:
        SignalDefinition = await get_signal_model()
        AssetCategory = await get_category_model()
        
        # 1. 验证信号存在
        signal = await SignalDefinition.get_or_none(id=signal_id)
        if not signal:
            return JSONResponse(
                status_code=404,
                content=create_error_response(
                    code=ErrorCodes.SIGNAL_NOT_FOUND,
                    message=f"信号定义不存在: {signal_id}"
                )
            )
        
        # 获取类别信息用于日志
        category = await AssetCategory.get_or_none(id=signal.category_id)
        category_code = category.code if category else "unknown"
        
        if force:
            await signal.delete()
            logger.info(f"信号定义物理删除: {category_code}.{signal.code}, 用户: {current_user.username}")
            message = "删除成功（注意：TDengine中的列不会被删除）"
        else:
            # 软删除
            signal.is_active = False
            signal.updated_at = datetime.now()
            await signal.save()
            logger.info(f"信号定义软删除: {category_code}.{signal.code}, 用户: {current_user.username}")
            message = "已禁用"
        
        return JSONResponse(
            status_code=200,
            content=create_response(
                data={"signal_id": signal_id},
                message=message
            )
        )
        
    except Exception as e:
        logger.error(f"删除信号定义失败: {e}")
        return JSONResponse(
            status_code=500,
            content=create_error_response(
                code=ErrorCodes.INTERNAL_ERROR,
                message=f"删除失败: {str(e)}"
            )
        )


# =====================================================
# 按类别获取信号API
# =====================================================

@router.get("/category/{category_id}", summary="获取类别下的信号定义")
async def get_signals_by_category(
    category_id: int,
    is_active: Optional[bool] = Query(None, description="是否激活"),
    is_stored: Optional[bool] = Query(None, description="是否存储"),
    is_realtime: Optional[bool] = Query(None, description="是否实时"),
    field_group: Optional[str] = Query(None, description="字段分组"),
    current_user: User = Depends(get_current_active_user)
) -> JSONResponse:
    """
    获取指定资产类别的所有信号定义
    """
    try:
        SignalDefinition = await get_signal_model()
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
        
        # 2. 构建查询条件
        query = SignalDefinition.filter(category_id=category_id)
        
        if is_active is not None:
            query = query.filter(is_active=is_active)
        if is_stored is not None:
            query = query.filter(is_stored=is_stored)
        if is_realtime is not None:
            query = query.filter(is_realtime=is_realtime)
        if field_group:
            query = query.filter(field_group=field_group)
        
        # 3. 查询并排序
        signals = await query.order_by("sort_order", "id")
        
        # 4. 转换为字典列表
        signal_list = [await signal_to_dict(sig) for sig in signals]
        
        return JSONResponse(
            status_code=200,
            content=create_response(
                data={
                    "category": {
                        "id": category.id,
                        "code": category.code,
                        "name": category.name
                    },
                    "signals": signal_list,
                    "total": len(signal_list)
                },
                message="获取成功"
            )
        )
        
    except Exception as e:
        logger.error(f"获取类别信号定义失败: {e}")
        return JSONResponse(
            status_code=500,
            content=create_error_response(
                code=ErrorCodes.INTERNAL_ERROR,
                message=f"查询失败: {str(e)}"
            )
        )
