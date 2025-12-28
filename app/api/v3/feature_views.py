"""
特征工程API v3
实现特征视图管理、特征数据查询、特征引擎服务集成

需求：3.2, 3.5
"""
from typing import Optional, List
from fastapi import APIRouter, Depends, Query
from datetime import datetime, timedelta

from app.core.auth_dependencies import get_current_active_user
from app.core.unified_logger import get_logger
from app.schemas.base import Success, Fail, SuccessExtra
from app.models.admin import User

from .schemas import FeatureViewCreate, FeatureViewUpdate, FeatureConfig

logger = get_logger(__name__)
router = APIRouter()


# =====================================================
# 辅助函数
# =====================================================

async def get_feature_view_model():
    """延迟导入FeatureView模型"""
    from app.models.platform_upgrade import FeatureView
    return FeatureView


async def get_feature_definition_model():
    """延迟导入FeatureDefinition模型"""
    from app.models.platform_upgrade import FeatureDefinition
    return FeatureDefinition


async def get_category_model():
    """延迟导入AssetCategory模型"""
    from app.models.platform_upgrade import AssetCategory
    return AssetCategory


async def get_feature_engine():
    """延迟导入特征引擎"""
    try:
        from app.services.feature_engine import FeatureManager
        return FeatureManager()
    except ImportError:
        logger.warning("特征引擎未配置")
        return None


async def feature_view_to_dict(view) -> dict:
    """将特征视图转换为字典"""
    return {
        "id": view.id,
        "category_id": view.category_id,
        "name": view.name,
        "code": view.code,
        "description": view.description,
        "feature_codes": view.feature_codes or [],
        "stream_name": view.stream_name,
        "target_stable": view.target_stable,
        "status": view.status,
        "is_active": view.is_active,
        "last_quality_check": view.last_quality_check.isoformat() if view.last_quality_check else None,
        "quality_score": view.quality_score,
        "created_at": view.created_at.isoformat() if view.created_at else None,
        "updated_at": view.updated_at.isoformat() if view.updated_at else None
    }


async def feature_definition_to_dict(feature) -> dict:
    """将特征定义转换为字典"""
    return {
        "id": feature.id,
        "category_id": feature.category_id,
        "name": feature.name,
        "code": feature.code,
        "description": feature.description,
        "calculation_config": feature.calculation_config,
        "output_type": feature.output_type,
        "output_unit": feature.output_unit,
        "stream_name": feature.stream_name,
        "target_table": feature.target_table,
        "is_active": feature.is_active,
        "created_at": feature.created_at.isoformat() if feature.created_at else None,
        "updated_at": feature.updated_at.isoformat() if feature.updated_at else None
    }


# =====================================================
# 特征视图CRUD API
# =====================================================

@router.post("", summary="创建特征视图")
async def create_feature_view(
    view_data: FeatureViewCreate,
    current_user: User = Depends(get_current_active_user)
):
    """
    创建特征视图
    
    - 验证资产类别存在
    - 创建特征定义
    - 生成TDengine流计算SQL
    
    需求：3.2
    """
    try:
        FeatureView = await get_feature_view_model()
        FeatureDefinition = await get_feature_definition_model()
        AssetCategory = await get_category_model()
        
        # 1. 验证资产类别存在
        category = await AssetCategory.get_or_none(id=view_data.category_id)
        if not category:
            return Fail(code=404, msg=f"资产类别不存在: {view_data.category_id}")
        
        # 2. 检查视图编码唯一性
        existing = await FeatureView.filter(
            category_id=view_data.category_id,
            code=view_data.code
        ).first()
        if existing:
            return Fail(code=400, msg=f"特征视图编码 '{view_data.code}' 在该类别下已存在")
        
        # 3. 验证聚合函数
        valid_functions = ["avg", "sum", "max", "min", "count", "stddev", "percentile", "first", "last"]
        for config in view_data.feature_configs:
            if config.function.lower() not in valid_functions:
                return Fail(
                    code=400,
                    msg=f"无效的聚合函数: {config.function}，支持: {', '.join(valid_functions)}"
                )
        
        # 4. 创建特征定义
        feature_codes = []
        for config in view_data.feature_configs:
            feature_code = f"{config.name}_{config.function}_{config.window}".replace("-", "_")
            
            feature = FeatureDefinition(
                category_id=view_data.category_id,
                name=config.name,
                code=feature_code,
                calculation_config={
                    "source_signal": config.source_signal,
                    "function": config.function.lower(),
                    "window": config.window,
                    "slide_interval": config.slide_interval,
                    "filters": config.filters,
                    "group_by": config.group_by
                },
                output_type="double",
                is_active=True
            )
            await feature.save()
            feature_codes.append(feature_code)
        
        # 5. 创建特征视图
        stream_name = f"stream_{category.code}_{view_data.code}"
        target_stable = f"feat_{category.code}_{view_data.code}"
        
        view = FeatureView(
            category_id=view_data.category_id,
            name=view_data.name,
            code=view_data.code,
            description=view_data.description,
            feature_codes=feature_codes,
            stream_name=stream_name,
            target_stable=target_stable,
            status="draft",
            is_active=True
        )
        await view.save()
        
        logger.info(f"特征视图创建成功: {category.code}.{view_data.code}, 用户: {current_user.username}")
        
        # 6. 尝试生成流计算SQL（可选）
        try:
            feature_engine = await get_feature_engine()
            if feature_engine:
                sql = await feature_engine.generate_stream_sql(
                    category_code=category.code,
                    view_code=view_data.code,
                    feature_configs=[c.model_dump() for c in view_data.feature_configs]
                )
                logger.info(f"流计算SQL生成成功: {stream_name}")
        except Exception as e:
            logger.warning(f"流计算SQL生成失败: {e}")
        
        return Success(
            code=200,
            msg="特征视图创建成功",
            data=await feature_view_to_dict(view)
        )
        
    except Exception as e:
        logger.error(f"创建特征视图失败: {e}")
        return Fail(code=500, msg=f"创建失败: {str(e)}")


@router.get("", summary="获取特征视图列表")
async def list_feature_views(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    category_id: Optional[int] = Query(None, description="资产类别ID"),
    status: Optional[str] = Query(None, description="状态: draft/active/paused/archived"),
    is_active: Optional[bool] = Query(None, description="是否激活"),
    current_user: User = Depends(get_current_active_user)
):
    """
    获取特征视图列表
    
    需求：3.2
    """
    try:
        FeatureView = await get_feature_view_model()
        
        # 1. 构建查询条件
        query = FeatureView.all()
        
        if category_id:
            query = query.filter(category_id=category_id)
        if status:
            query = query.filter(status=status)
        if is_active is not None:
            query = query.filter(is_active=is_active)
        
        # 2. 分页查询
        total = await query.count()
        offset = (page - 1) * page_size
        views = await query.order_by("-created_at").offset(offset).limit(page_size)
        
        # 3. 转换为字典列表
        view_list = [await feature_view_to_dict(v) for v in views]
        
        return SuccessExtra(
            code=200,
            msg="获取成功",
            data=view_list,
            total=total,
            page=page,
            page_size=page_size
        )
        
    except Exception as e:
        logger.error(f"获取特征视图列表失败: {e}")
        return Fail(code=500, msg=f"查询失败: {str(e)}")


@router.get("/categories/{category_id}", summary="获取资产类别的特征视图")
async def get_category_feature_views(
    category_id: int,
    current_user: User = Depends(get_current_active_user)
):
    """
    获取指定资产类别的所有特征视图
    
    需求：3.2
    """
    try:
        FeatureView = await get_feature_view_model()
        AssetCategory = await get_category_model()
        
        # 1. 验证类别存在
        category = await AssetCategory.get_or_none(id=category_id)
        if not category:
            return Fail(code=404, msg=f"资产类别不存在: {category_id}")
        
        # 2. 查询特征视图
        views = await FeatureView.filter(
            category_id=category_id,
            is_active=True
        ).order_by("name")
        
        # 3. 转换为字典列表
        view_list = [await feature_view_to_dict(v) for v in views]
        
        return Success(
            code=200,
            msg="获取成功",
            data={
                "category_id": category_id,
                "category_code": category.code,
                "feature_views": view_list,
                "total": len(view_list)
            }
        )
        
    except Exception as e:
        logger.error(f"获取类别特征视图失败: {e}")
        return Fail(code=500, msg=f"查询失败: {str(e)}")


@router.get("/{view_id}", summary="获取特征视图详情")
async def get_feature_view(
    view_id: int,
    current_user: User = Depends(get_current_active_user)
):
    """
    获取特征视图详情
    
    需求：3.2
    """
    try:
        FeatureView = await get_feature_view_model()
        FeatureDefinition = await get_feature_definition_model()
        
        view = await FeatureView.get_or_none(id=view_id)
        if not view:
            return Fail(code=404, msg=f"特征视图不存在: {view_id}")
        
        # 获取关联的特征定义
        features = await FeatureDefinition.filter(
            category_id=view.category_id,
            code__in=view.feature_codes or []
        ).all()
        
        result = await feature_view_to_dict(view)
        result["features"] = [await feature_definition_to_dict(f) for f in features]
        
        return Success(
            code=200,
            msg="获取成功",
            data=result
        )
        
    except Exception as e:
        logger.error(f"获取特征视图详情失败: {e}")
        return Fail(code=500, msg=f"查询失败: {str(e)}")


@router.put("/{view_id}", summary="更新特征视图")
async def update_feature_view(
    view_id: int,
    view_data: FeatureViewUpdate,
    current_user: User = Depends(get_current_active_user)
):
    """
    更新特征视图
    
    需求：3.2
    """
    try:
        FeatureView = await get_feature_view_model()
        
        view = await FeatureView.get_or_none(id=view_id)
        if not view:
            return Fail(code=404, msg=f"特征视图不存在: {view_id}")
        
        # 更新字段
        update_data = view_data.model_dump(exclude_unset=True, exclude={"feature_configs"})
        for field, value in update_data.items():
            setattr(view, field, value)
        
        view.updated_at = datetime.now()
        await view.save()
        
        logger.info(f"特征视图更新成功: {view.code}, 用户: {current_user.username}")
        
        return Success(
            code=200,
            msg="更新成功",
            data=await feature_view_to_dict(view)
        )
        
    except Exception as e:
        logger.error(f"更新特征视图失败: {e}")
        return Fail(code=500, msg=f"更新失败: {str(e)}")


@router.delete("/{view_id}", summary="删除特征视图")
async def delete_feature_view(
    view_id: int,
    force: bool = Query(False, description="是否强制删除"),
    current_user: User = Depends(get_current_active_user)
):
    """
    删除特征视图
    
    需求：3.2
    """
    try:
        FeatureView = await get_feature_view_model()
        
        view = await FeatureView.get_or_none(id=view_id)
        if not view:
            return Fail(code=404, msg=f"特征视图不存在: {view_id}")
        
        if force:
            await view.delete()
            logger.info(f"特征视图物理删除: {view.code}, 用户: {current_user.username}")
            return Success(code=200, msg="删除成功")
        else:
            view.is_active = False
            view.status = "archived"
            view.updated_at = datetime.now()
            await view.save()
            logger.info(f"特征视图软删除: {view.code}, 用户: {current_user.username}")
            return Success(code=200, msg="已归档")
        
    except Exception as e:
        logger.error(f"删除特征视图失败: {e}")
        return Fail(code=500, msg=f"删除失败: {str(e)}")


# =====================================================
# 特征视图操作API
# =====================================================

@router.post("/{view_id}/activate", summary="激活特征视图")
async def activate_feature_view(
    view_id: int,
    current_user: User = Depends(get_current_active_user)
):
    """
    激活特征视图
    
    - 创建TDengine流计算任务
    - 更新视图状态为active
    
    需求：3.2
    """
    try:
        FeatureView = await get_feature_view_model()
        AssetCategory = await get_category_model()
        
        view = await FeatureView.get_or_none(id=view_id)
        if not view:
            return Fail(code=404, msg=f"特征视图不存在: {view_id}")
        
        if view.status == "active":
            return Fail(code=400, msg="特征视图已经是激活状态")
        
        category = await AssetCategory.get_or_none(id=view.category_id)
        
        # 尝试创建流计算任务
        try:
            feature_engine = await get_feature_engine()
            if feature_engine:
                await feature_engine.create_stream(
                    stream_name=view.stream_name,
                    target_table=view.target_stable,
                    category_code=category.code
                )
        except Exception as e:
            logger.warning(f"创建流计算任务失败: {e}")
        
        # 更新状态
        view.status = "active"
        view.updated_at = datetime.now()
        await view.save()
        
        logger.info(f"特征视图激活成功: {view.code}, 用户: {current_user.username}")
        
        return Success(
            code=200,
            msg="激活成功",
            data=await feature_view_to_dict(view)
        )
        
    except Exception as e:
        logger.error(f"激活特征视图失败: {e}")
        return Fail(code=500, msg=f"激活失败: {str(e)}")


@router.post("/{view_id}/pause", summary="暂停特征视图")
async def pause_feature_view(
    view_id: int,
    current_user: User = Depends(get_current_active_user)
):
    """
    暂停特征视图
    
    需求：3.2
    """
    try:
        FeatureView = await get_feature_view_model()
        
        view = await FeatureView.get_or_none(id=view_id)
        if not view:
            return Fail(code=404, msg=f"特征视图不存在: {view_id}")
        
        if view.status != "active":
            return Fail(code=400, msg="只能暂停激活状态的特征视图")
        
        view.status = "paused"
        view.updated_at = datetime.now()
        await view.save()
        
        logger.info(f"特征视图暂停成功: {view.code}, 用户: {current_user.username}")
        
        return Success(
            code=200,
            msg="暂停成功",
            data=await feature_view_to_dict(view)
        )
        
    except Exception as e:
        logger.error(f"暂停特征视图失败: {e}")
        return Fail(code=500, msg=f"暂停失败: {str(e)}")


# =====================================================
# 特征数据查询API
# =====================================================

@router.get("/{view_id}/data", summary="获取特征数据")
async def get_feature_data(
    view_id: int,
    asset_id: int = Query(..., description="资产ID"),
    hours: int = Query(24, ge=1, le=168, description="查询最近N小时"),
    limit: int = Query(1000, ge=1, le=10000, description="最大返回条数"),
    current_user: User = Depends(get_current_active_user)
):
    """
    获取特征数据
    
    从TDengine查询计算后的特征数据
    
    需求：3.5
    """
    try:
        FeatureView = await get_feature_view_model()
        AssetCategory = await get_category_model()
        from app.models.platform_upgrade import Asset
        
        # 1. 验证特征视图存在
        view = await FeatureView.get_or_none(id=view_id)
        if not view:
            return Fail(code=404, msg=f"特征视图不存在: {view_id}")
        
        # 2. 验证资产存在
        asset = await Asset.get_or_none(id=asset_id)
        if not asset:
            return Fail(code=404, msg=f"资产不存在: {asset_id}")
        
        # 3. 获取类别信息
        category = await AssetCategory.get_or_none(id=view.category_id)
        
        # 4. 计算时间范围
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours)
        
        # 5. 查询特征数据
        try:
            from app.core.tdengine_connector import td_client
            
            table_name = f"{category.tdengine_database}.{view.target_stable}_{asset.code}"
            
            sql = f"""
            SELECT *
            FROM {table_name}
            WHERE ts >= '{start_time.strftime('%Y-%m-%d %H:%M:%S')}'
              AND ts <= '{end_time.strftime('%Y-%m-%d %H:%M:%S')}'
            ORDER BY ts
            LIMIT {limit}
            """
            
            result = await td_client.query(sql)
            
        except Exception as e:
            logger.warning(f"TDengine查询失败: {e}")
            result = []
        
        return Success(
            code=200,
            msg="获取成功",
            data={
                "view_id": view_id,
                "view_code": view.code,
                "asset_id": asset_id,
                "asset_code": asset.code,
                "time_range": {
                    "start_time": start_time.isoformat(),
                    "end_time": end_time.isoformat()
                },
                "data": result,
                "count": len(result)
            }
        )
        
    except Exception as e:
        logger.error(f"获取特征数据失败: {e}")
        return Fail(code=500, msg=f"查询失败: {str(e)}")


# =====================================================
# 特征质量监控API
# =====================================================

@router.get("/{view_id}/quality", summary="获取特征质量报告")
async def get_feature_quality(
    view_id: int,
    current_user: User = Depends(get_current_active_user)
):
    """
    获取特征视图的质量报告
    
    包括数据完整性、新鲜度、分布指标
    
    需求：3.5
    """
    try:
        FeatureView = await get_feature_view_model()
        
        view = await FeatureView.get_or_none(id=view_id)
        if not view:
            return Fail(code=404, msg=f"特征视图不存在: {view_id}")
        
        # 尝试获取质量指标
        try:
            feature_engine = await get_feature_engine()
            if feature_engine:
                quality_report = await feature_engine.check_feature_quality(
                    view_code=view.code,
                    category_id=view.category_id
                )
            else:
                quality_report = {
                    "completeness": None,
                    "freshness": None,
                    "distribution": None,
                    "message": "特征引擎未配置"
                }
        except Exception as e:
            logger.warning(f"获取质量报告失败: {e}")
            quality_report = {
                "completeness": None,
                "freshness": None,
                "distribution": None,
                "error": str(e)
            }
        
        # 更新最后检查时间
        view.last_quality_check = datetime.now()
        if quality_report.get("completeness"):
            view.quality_score = quality_report["completeness"]
        await view.save()
        
        return Success(
            code=200,
            msg="获取成功",
            data={
                "view_id": view_id,
                "view_code": view.code,
                "quality_report": quality_report,
                "last_check": view.last_quality_check.isoformat()
            }
        )
        
    except Exception as e:
        logger.error(f"获取特征质量报告失败: {e}")
        return Fail(code=500, msg=f"查询失败: {str(e)}")
