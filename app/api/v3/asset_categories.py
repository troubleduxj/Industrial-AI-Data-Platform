"""
资产类别管理API v3
实现资产类别CRUD操作、信号定义管理、Schema引擎自动同步

需求：5.1, 5.2
"""
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from datetime import datetime

from app.core.auth_dependencies import get_current_user, get_current_active_user
from app.core.unified_logger import get_logger
from app.schemas.base import Success, Fail, SuccessExtra
from app.models.admin import User

from .schemas import (
    AssetCategoryCreate,
    AssetCategoryUpdate,
    AssetCategoryResponse,
    SignalDefinitionCreate,
    SignalDefinitionUpdate,
    SignalDefinitionResponse
)

logger = get_logger(__name__)
router = APIRouter()


# =====================================================
# 辅助函数
# =====================================================

async def get_category_model():
    """延迟导入AssetCategory模型"""
    from app.models.platform_upgrade import AssetCategory
    return AssetCategory


async def get_signal_model():
    """延迟导入SignalDefinition模型"""
    from app.models.platform_upgrade import SignalDefinition
    return SignalDefinition


async def get_schema_manager():
    """延迟导入Schema管理器"""
    from app.services.schema_engine import schema_manager
    return schema_manager


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
# 资产类别CRUD API
# =====================================================

@router.post("", summary="创建资产类别")
async def create_asset_category(
    category_data: AssetCategoryCreate,
    current_user: User = Depends(get_current_active_user)
):
    """
    创建新的资产类别
    
    - 自动生成TDengine超级表前缀
    - 初始化TDengine Schema（如果有信号定义）
    
    需求：5.1
    """
    try:
        AssetCategory = await get_category_model()
        schema_manager = await get_schema_manager()
        
        # 1. 检查编码唯一性
        existing = await AssetCategory.filter(code=category_data.code).first()
        if existing:
            return Fail(
                code=400,
                msg=f"类别编码 '{category_data.code}' 已存在"
            )
        
        # 2. 创建类别
        tdengine_db = category_data.tdengine_database or "devicemonitor"
        
        # 处理颜色字段，存入config
        config = category_data.config or {}
        if category_data.color:
            config["color"] = category_data.color
            
        category = AssetCategory(
            code=category_data.code,
            name=category_data.name,
            description=category_data.description,
            industry=category_data.industry,
            icon=category_data.icon,
            tdengine_database=tdengine_db,
            tdengine_stable_prefix=f"raw_{category_data.code}",
            config=config,
            is_active=True,
            asset_count=0
        )
        await category.save()
        
        logger.info(f"资产类别创建成功: {category_data.code}, 用户: {current_user.username}")
        
        # 3. 尝试初始化TDengine Schema（可能没有信号定义）
        try:
            await schema_manager.sync_category_schema(category_data.code)
        except Exception as e:
            logger.warning(f"Schema初始化跳过（无信号定义）: {e}")
        
        return Success(
            code=200,
            msg="资产类别创建成功",
            data=await category_to_dict(category)
        )
        
    except Exception as e:
        logger.error(f"创建资产类别失败: {e}")
        return Fail(code=500, msg=f"创建失败: {str(e)}")


@router.get("", summary="获取资产类别列表")
async def list_asset_categories(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    is_active: Optional[bool] = Query(None, description="是否激活"),
    industry: Optional[str] = Query(None, description="所属行业"),
    keyword: Optional[str] = Query(None, description="搜索关键词"),
    current_user: User = Depends(get_current_active_user)
):
    """
    获取资产类别列表（分页）
    
    支持按激活状态、行业、关键词筛选
    
    需求：5.1
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
        
        return SuccessExtra(
            code=200,
            msg="获取成功",
            data=category_list,
            total=total,
            page=page,
            page_size=page_size
        )
        
    except Exception as e:
        logger.error(f"获取资产类别列表失败: {e}")
        return Fail(code=500, msg=f"查询失败: {str(e)}")


@router.get("/{category_id}", summary="获取资产类别详情")
async def get_asset_category(
    category_id: int,
    current_user: User = Depends(get_current_active_user)
):
    """
    获取单个资产类别详情
    
    需求：5.2
    """
    try:
        AssetCategory = await get_category_model()
        
        category = await AssetCategory.get_or_none(id=category_id)
        if not category:
            return Fail(code=404, msg=f"资产类别不存在: {category_id}")
        
        return Success(
            code=200,
            msg="获取成功",
            data=await category_to_dict(category)
        )
        
    except Exception as e:
        logger.error(f"获取资产类别详情失败: {e}")
        return Fail(code=500, msg=f"查询失败: {str(e)}")


@router.put("/{category_id}", summary="更新资产类别")
async def update_asset_category(
    category_id: int,
    category_data: AssetCategoryUpdate,
    current_user: User = Depends(get_current_active_user)
):
    """
    更新资产类别信息
    
    注意：code字段不可修改
    
    需求：5.1
    """
    try:
        AssetCategory = await get_category_model()
        
        category = await AssetCategory.get_or_none(id=category_id)
        if not category:
            return Fail(code=404, msg=f"资产类别不存在: {category_id}")
        
        # 更新字段
        update_data = category_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(category, field, value)
        
        category.updated_at = datetime.now()
        await category.save()
        
        logger.info(f"资产类别更新成功: {category.code}, 用户: {current_user.username}")
        
        return Success(
            code=200,
            msg="更新成功",
            data=await category_to_dict(category)
        )
        
    except Exception as e:
        logger.error(f"更新资产类别失败: {e}")
        return Fail(code=500, msg=f"更新失败: {str(e)}")


@router.delete("/{category_id}", summary="删除资产类别")
async def delete_asset_category(
    category_id: int,
    force: bool = Query(False, description="是否强制删除"),
    current_user: User = Depends(get_current_active_user)
):
    """
    删除资产类别
    
    - 默认软删除（设置is_active=False）
    - force=True时物理删除（需要无关联资产）
    
    需求：5.1
    """
    try:
        AssetCategory = await get_category_model()
        from app.models.platform_upgrade import Asset
        
        category = await AssetCategory.get_or_none(id=category_id)
        if not category:
            return Fail(code=404, msg=f"资产类别不存在: {category_id}")
        
        # 检查是否有关联资产
        asset_count = await Asset.filter(category_id=category_id).count()
        
        if force:
            if asset_count > 0:
                return Fail(
                    code=400,
                    msg=f"无法删除：该类别下有 {asset_count} 个资产"
                )
            await category.delete()
            logger.info(f"资产类别物理删除: {category.code}, 用户: {current_user.username}")
            return Success(code=200, msg="删除成功")
        else:
            # 软删除
            category.is_active = False
            category.updated_at = datetime.now()
            await category.save()
            logger.info(f"资产类别软删除: {category.code}, 用户: {current_user.username}")
            return Success(code=200, msg="已禁用")
        
    except Exception as e:
        logger.error(f"删除资产类别失败: {e}")
        return Fail(code=500, msg=f"删除失败: {str(e)}")


# =====================================================
# 信号定义管理API
# =====================================================

@router.get("/{category_id}/signals", summary="获取资产类别的信号定义")
async def get_category_signals(
    category_id: int,
    is_active: Optional[bool] = Query(None, description="是否激活"),
    is_stored: Optional[bool] = Query(None, description="是否存储"),
    is_realtime: Optional[bool] = Query(None, description="是否实时"),
    field_group: Optional[str] = Query(None, description="字段分组"),
    current_user: User = Depends(get_current_active_user)
):
    """
    获取资产类别的信号定义列表
    
    支持按激活状态、存储状态、实时状态、分组筛选
    
    需求：5.2
    """
    try:
        AssetCategory = await get_category_model()
        SignalDefinition = await get_signal_model()
        
        # 1. 验证类别存在
        category = await AssetCategory.get_or_none(id=category_id)
        if not category:
            return Fail(code=404, msg=f"资产类别不存在: {category_id}")
        
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
        
        return Success(
            code=200,
            msg="获取成功",
            data={
                "category": await category_to_dict(category),
                "signals": signal_list,
                "total": len(signal_list)
            }
        )
        
    except Exception as e:
        logger.error(f"获取信号定义列表失败: {e}")
        return Fail(code=500, msg=f"查询失败: {str(e)}")


@router.post("/{category_id}/signals", summary="创建信号定义")
async def create_signal_definition(
    category_id: int,
    signal_data: SignalDefinitionCreate,
    current_user: User = Depends(get_current_active_user)
):
    """
    为资产类别创建信号定义
    
    - 自动同步TDengine Schema
    - 验证数据类型有效性
    
    需求：5.2
    """
    try:
        AssetCategory = await get_category_model()
        SignalDefinition = await get_signal_model()
        schema_manager = await get_schema_manager()
        
        # 1. 验证类别存在
        category = await AssetCategory.get_or_none(id=category_id)
        if not category:
            return Fail(code=404, msg=f"资产类别不存在: {category_id}")
        
        # 2. 验证数据类型
        valid_types = ["float", "int", "bool", "string", "double", "bigint", "timestamp"]
        if signal_data.data_type.lower() not in valid_types:
            return Fail(
                code=400,
                msg=f"无效的数据类型: {signal_data.data_type}，支持: {', '.join(valid_types)}"
            )
        
        # 3. 检查信号编码唯一性
        existing = await SignalDefinition.filter(
            category_id=category_id,
            code=signal_data.code
        ).first()
        if existing:
            return Fail(
                code=400,
                msg=f"信号编码 '{signal_data.code}' 在该类别下已存在"
            )
        
        # 4. 创建信号定义
        signal = SignalDefinition(
            category_id=category_id,
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
        
        # 5. 同步TDengine Schema
        if signal_data.is_stored:
            try:
                await schema_manager.sync_category_schema(category.code)
                logger.info(f"TDengine Schema同步成功: {category.code}")
            except Exception as e:
                logger.warning(f"TDengine Schema同步失败: {e}")
        
        return Success(
            code=200,
            msg="信号定义创建成功",
            data=await signal_to_dict(signal)
        )
        
    except Exception as e:
        logger.error(f"创建信号定义失败: {e}")
        return Fail(code=500, msg=f"创建失败: {str(e)}")


@router.put("/{category_id}/signals/{signal_id}", summary="更新信号定义")
async def update_signal_definition(
    category_id: int,
    signal_id: int,
    signal_data: SignalDefinitionUpdate,
    current_user: User = Depends(get_current_active_user)
):
    """
    更新信号定义
    
    注意：code和data_type字段不可修改
    
    需求：5.2
    """
    try:
        AssetCategory = await get_category_model()
        SignalDefinition = await get_signal_model()
        schema_manager = await get_schema_manager()
        
        # 1. 验证类别存在
        category = await AssetCategory.get_or_none(id=category_id)
        if not category:
            return Fail(code=404, msg=f"资产类别不存在: {category_id}")
        
        # 2. 验证信号存在
        signal = await SignalDefinition.get_or_none(id=signal_id, category_id=category_id)
        if not signal:
            return Fail(code=404, msg=f"信号定义不存在: {signal_id}")
        
        # 3. 更新字段
        update_data = signal_data.model_dump(exclude_unset=True)
        old_is_stored = signal.is_stored
        
        for field, value in update_data.items():
            setattr(signal, field, value)
        
        signal.updated_at = datetime.now()
        await signal.save()
        
        logger.info(f"信号定义更新成功: {category.code}.{signal.code}, 用户: {current_user.username}")
        
        # 4. 如果is_stored状态变化，同步Schema
        new_is_stored = signal.is_stored
        if old_is_stored != new_is_stored:
            try:
                await schema_manager.sync_category_schema(category.code)
                logger.info(f"TDengine Schema同步成功: {category.code}")
            except Exception as e:
                logger.warning(f"TDengine Schema同步失败: {e}")
        
        return Success(
            code=200,
            msg="更新成功",
            data=await signal_to_dict(signal)
        )
        
    except Exception as e:
        logger.error(f"更新信号定义失败: {e}")
        return Fail(code=500, msg=f"更新失败: {str(e)}")


@router.delete("/{category_id}/signals/{signal_id}", summary="删除信号定义")
async def delete_signal_definition(
    category_id: int,
    signal_id: int,
    force: bool = Query(False, description="是否强制删除"),
    current_user: User = Depends(get_current_active_user)
):
    """
    删除信号定义
    
    - 默认软删除（设置is_active=False）
    - force=True时物理删除
    - 注意：TDengine不支持删除列，物理删除后列仍存在
    
    需求：5.2
    """
    try:
        AssetCategory = await get_category_model()
        SignalDefinition = await get_signal_model()
        
        # 1. 验证类别存在
        category = await AssetCategory.get_or_none(id=category_id)
        if not category:
            return Fail(code=404, msg=f"资产类别不存在: {category_id}")
        
        # 2. 验证信号存在
        signal = await SignalDefinition.get_or_none(id=signal_id, category_id=category_id)
        if not signal:
            return Fail(code=404, msg=f"信号定义不存在: {signal_id}")
        
        if force:
            await signal.delete()
            logger.info(f"信号定义物理删除: {category.code}.{signal.code}, 用户: {current_user.username}")
            return Success(
                code=200,
                msg="删除成功（注意：TDengine中的列不会被删除）"
            )
        else:
            # 软删除
            signal.is_active = False
            signal.updated_at = datetime.now()
            await signal.save()
            logger.info(f"信号定义软删除: {category.code}.{signal.code}, 用户: {current_user.username}")
            return Success(code=200, msg="已禁用")
        
    except Exception as e:
        logger.error(f"删除信号定义失败: {e}")
        return Fail(code=500, msg=f"删除失败: {str(e)}")


# =====================================================
# Schema同步API
# =====================================================

@router.post("/{category_id}/sync-schema", summary="同步TDengine Schema")
async def sync_category_schema(
    category_id: int,
    current_user: User = Depends(get_current_active_user)
):
    """
    手动同步资产类别的TDengine Schema
    
    - 根据信号定义创建/更新超级表结构
    - 记录Schema版本变更
    
    需求：1.1, 1.2
    """
    try:
        AssetCategory = await get_category_model()
        schema_manager = await get_schema_manager()
        
        # 1. 验证类别存在
        category = await AssetCategory.get_or_none(id=category_id)
        if not category:
            return Fail(code=404, msg=f"资产类别不存在: {category_id}")
        
        # 2. 同步Schema
        success = await schema_manager.sync_category_schema(category.code)
        
        if success:
            logger.info(f"Schema同步成功: {category.code}, 用户: {current_user.username}")
            return Success(
                code=200,
                msg="Schema同步成功",
                data={
                    "category_code": category.code,
                    "stable_name": f"raw_{category.code}",
                    "database": category.tdengine_database
                }
            )
        else:
            return Fail(code=500, msg="Schema同步失败")
        
    except Exception as e:
        logger.error(f"Schema同步失败: {e}")
        return Fail(code=500, msg=f"同步失败: {str(e)}")


@router.get("/{category_id}/schema-history", summary="获取Schema变更历史")
async def get_schema_history(
    category_id: int,
    current_user: User = Depends(get_current_active_user)
):
    """
    获取资产类别的Schema变更历史
    
    需求：1.1
    """
    try:
        AssetCategory = await get_category_model()
        from app.models.platform_upgrade import SchemaVersion
        
        # 1. 验证类别存在
        category = await AssetCategory.get_or_none(id=category_id)
        if not category:
            return Fail(code=404, msg=f"资产类别不存在: {category_id}")
        
        # 2. 查询Schema版本历史
        versions = await SchemaVersion.filter(
            category_id=category_id
        ).order_by("-execution_time").limit(50)
        
        # 3. 转换为字典列表
        version_list = []
        for v in versions:
            version_list.append({
                "id": v.id,
                "version": v.version,
                "change_type": v.change_type,
                "change_details": v.change_details,
                "execution_status": v.execution_status,
                "execution_time": v.execution_time.isoformat() if v.execution_time else None,
                "execution_duration_ms": v.execution_duration_ms,
                "error_message": v.error_message
            })
        
        return Success(
            code=200,
            msg="获取成功",
            data={
                "category": await category_to_dict(category),
                "schema_versions": version_list,
                "total": len(version_list)
            }
        )
        
    except Exception as e:
        logger.error(f"获取Schema历史失败: {e}")
        return Fail(code=500, msg=f"查询失败: {str(e)}")
