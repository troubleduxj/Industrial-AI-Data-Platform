"""
资产管理API v3
实现资产CRUD操作、实时数据查询、历史数据查询

需求：5.3, 6.1
"""
from typing import Optional, List
from fastapi import APIRouter, Depends, Query
from datetime import datetime, timedelta

from app.core.auth_dependencies import get_current_active_user
from app.core.unified_logger import get_logger
from app.schemas.base import Success, Fail, SuccessExtra
from app.models.admin import User

from .schemas import AssetCreate, AssetUpdate

logger = get_logger(__name__)
router = APIRouter()


# =====================================================
# 辅助函数
# =====================================================

async def get_asset_model():
    """延迟导入Asset模型"""
    from app.models.platform_upgrade import Asset
    return Asset


async def get_category_model():
    """延迟导入AssetCategory模型"""
    from app.models.platform_upgrade import AssetCategory
    return AssetCategory


async def get_schema_manager():
    """延迟导入Schema管理器"""
    from app.services.schema_engine import schema_manager
    return schema_manager


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
            "icon": asset.category.icon
        }
    
    return result


# =====================================================
# 资产CRUD API
# =====================================================

@router.post("", summary="创建资产")
async def create_asset(
    asset_data: AssetCreate,
    current_user: User = Depends(get_current_active_user)
):
    """
    创建新资产
    
    - 自动创建TDengine子表
    - 更新资产类别的资产计数
    
    需求：5.3
    """
    try:
        Asset = await get_asset_model()
        AssetCategory = await get_category_model()
        schema_manager = await get_schema_manager()
        
        # 1. 验证资产类别存在
        category = await AssetCategory.get_or_none(id=asset_data.category_id)
        if not category:
            return Fail(code=404, msg=f"资产类别不存在: {asset_data.category_id}")
        
        if not category.is_active:
            return Fail(code=400, msg=f"资产类别已禁用: {category.name}")
        
        # 2. 检查资产编号唯一性
        existing = await Asset.filter(code=asset_data.code).first()
        if existing:
            return Fail(code=400, msg=f"资产编号 '{asset_data.code}' 已存在")
        
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
        
        # 5. 创建TDengine子表
        try:
            stable_name = f"raw_{category.code}"
            await schema_manager.create_child_table(
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
        return Success(
            code=200,
            msg="资产创建成功",
            data=await asset_to_dict(asset, include_category=True)
        )
        
    except Exception as e:
        logger.error(f"创建资产失败: {e}")
        return Fail(code=500, msg=f"创建失败: {str(e)}")


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
):
    """
    获取资产列表（分页）
    
    支持多种筛选条件
    
    需求：5.3
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
        
        return SuccessExtra(
            code=200,
            msg="获取成功",
            data=asset_list,
            total=total,
            page=page,
            page_size=page_size
        )
        
    except Exception as e:
        logger.error(f"获取资产列表失败: {e}")
        return Fail(code=500, msg=f"查询失败: {str(e)}")


@router.get("/{asset_id}", summary="获取资产详情")
async def get_asset(
    asset_id: int,
    current_user: User = Depends(get_current_active_user)
):
    """
    获取单个资产详情
    
    需求：5.3
    """
    try:
        Asset = await get_asset_model()
        
        asset = await Asset.get_or_none(id=asset_id).prefetch_related("category")
        if not asset:
            return Fail(code=404, msg=f"资产不存在: {asset_id}")
        
        return Success(
            code=200,
            msg="获取成功",
            data=await asset_to_dict(asset, include_category=True)
        )
        
    except Exception as e:
        logger.error(f"获取资产详情失败: {e}")
        return Fail(code=500, msg=f"查询失败: {str(e)}")


@router.put("/{asset_id}", summary="更新资产")
async def update_asset(
    asset_id: int,
    asset_data: AssetUpdate,
    current_user: User = Depends(get_current_active_user)
):
    """
    更新资产信息
    
    注意：code和category_id字段不可修改
    
    需求：5.3
    """
    try:
        Asset = await get_asset_model()
        
        asset = await Asset.get_or_none(id=asset_id).prefetch_related("category")
        if not asset:
            return Fail(code=404, msg=f"资产不存在: {asset_id}")
        
        if asset.is_locked:
            return Fail(code=400, msg="资产已锁定，无法修改")
        
        # 更新字段
        update_data = asset_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(asset, field, value)
        
        asset.updated_at = datetime.now()
        await asset.save()
        
        logger.info(f"资产更新成功: {asset.code}, 用户: {current_user.username}")
        
        return Success(
            code=200,
            msg="更新成功",
            data=await asset_to_dict(asset, include_category=True)
        )
        
    except Exception as e:
        logger.error(f"更新资产失败: {e}")
        return Fail(code=500, msg=f"更新失败: {str(e)}")


@router.delete("/{asset_id}", summary="删除资产")
async def delete_asset(
    asset_id: int,
    force: bool = Query(False, description="是否强制删除"),
    current_user: User = Depends(get_current_active_user)
):
    """
    删除资产
    
    - 默认软删除（设置is_active=False）
    - force=True时物理删除
    
    需求：5.3
    """
    try:
        Asset = await get_asset_model()
        AssetCategory = await get_category_model()
        
        asset = await Asset.get_or_none(id=asset_id)
        if not asset:
            return Fail(code=404, msg=f"资产不存在: {asset_id}")
        
        if asset.is_locked:
            return Fail(code=400, msg="资产已锁定，无法删除")
        
        category_id = asset.category_id
        
        if force:
            await asset.delete()
            logger.info(f"资产物理删除: {asset.code}, 用户: {current_user.username}")
        else:
            asset.is_active = False
            asset.updated_at = datetime.now()
            await asset.save()
            logger.info(f"资产软删除: {asset.code}, 用户: {current_user.username}")
        
        # 更新资产类别计数
        category = await AssetCategory.get_or_none(id=category_id)
        if category:
            category.asset_count = await Asset.filter(category_id=category_id, is_active=True).count()
            await category.save()
        
        return Success(code=200, msg="删除成功" if force else "已禁用")
        
    except Exception as e:
        logger.error(f"删除资产失败: {e}")
        return Fail(code=500, msg=f"删除失败: {str(e)}")


# =====================================================
# 实时数据查询API
# =====================================================

@router.get("/{asset_id}/realtime-data", summary="获取资产实时数据")
async def get_asset_realtime_data(
    asset_id: int,
    current_user: User = Depends(get_current_active_user)
):
    """
    获取资产的最新实时数据
    
    从TDengine查询最新一条数据记录
    
    需求：6.1
    """
    try:
        Asset = await get_asset_model()
        
        # 1. 获取资产信息
        asset = await Asset.get_or_none(id=asset_id).prefetch_related("category")
        if not asset:
            return Fail(code=404, msg=f"资产不存在: {asset_id}")
        
        # 2. 构建表名
        safe_code = asset.code.replace("-", "_").replace(" ", "_")
        table_name = f"{asset.category.tdengine_database}.raw_{asset.category.code}_{safe_code}"
        
        # 3. 查询最新数据
        try:
            from app.core.tdengine_connector import td_client
            
            sql = f"""
            SELECT * FROM {table_name}
            ORDER BY ts DESC
            LIMIT 1
            """
            
            result = await td_client.query(sql)
            realtime_data = result[0] if result else None
            
        except Exception as e:
            logger.warning(f"TDengine查询失败: {e}")
            realtime_data = None
        
        return Success(
            code=200,
            msg="获取成功",
            data={
                "asset": await asset_to_dict(asset, include_category=True),
                "realtime_data": realtime_data,
                "timestamp": datetime.now().isoformat()
            }
        )
        
    except Exception as e:
        logger.error(f"获取实时数据失败: {e}")
        return Fail(code=500, msg=f"查询失败: {str(e)}")


# =====================================================
# 历史数据查询API
# =====================================================

@router.get("/{asset_id}/historical-data", summary="获取资产历史数据")
async def get_asset_historical_data(
    asset_id: int,
    start_time: Optional[datetime] = Query(None, description="开始时间"),
    end_time: Optional[datetime] = Query(None, description="结束时间"),
    hours: int = Query(24, ge=1, le=168, description="查询最近N小时（默认24小时）"),
    signals: Optional[str] = Query(None, description="信号列表，逗号分隔"),
    interval: Optional[str] = Query(None, description="聚合间隔: 1m/5m/10m/30m/1h"),
    limit: int = Query(1000, ge=1, le=10000, description="最大返回条数"),
    current_user: User = Depends(get_current_active_user)
):
    """
    获取资产的历史数据
    
    支持时间范围、信号筛选、聚合间隔
    
    需求：6.1
    """
    try:
        Asset = await get_asset_model()
        from app.models.platform_upgrade import SignalDefinition
        
        # 1. 获取资产信息
        asset = await Asset.get_or_none(id=asset_id).prefetch_related("category")
        if not asset:
            return Fail(code=404, msg=f"资产不存在: {asset_id}")
        
        # 2. 计算时间范围
        if not end_time:
            end_time = datetime.now()
        if not start_time:
            start_time = end_time - timedelta(hours=hours)
        
        # 3. 构建表名
        safe_code = asset.code.replace("-", "_").replace(" ", "_")
        table_name = f"{asset.category.tdengine_database}.raw_{asset.category.code}_{safe_code}"
        
        # 4. 构建查询字段
        if signals:
            signal_list = [s.strip() for s in signals.split(",")]
            select_fields = "ts, " + ", ".join(signal_list)
        else:
            select_fields = "*"
        
        # 5. 构建SQL
        try:
            from app.core.tdengine_connector import td_client
            
            if interval:
                # 聚合查询
                # 获取信号定义以确定聚合方法
                signal_defs = await SignalDefinition.filter(
                    category_id=asset.category_id,
                    is_stored=True,
                    is_active=True
                ).all()
                
                agg_fields = []
                for sig in signal_defs:
                    if signals and sig.code not in signal_list:
                        continue
                    method = sig.aggregation_method or "avg"
                    agg_fields.append(f"{method}({sig.code}) as {sig.code}")
                
                if agg_fields:
                    select_fields = "_wstart as ts, " + ", ".join(agg_fields)
                    sql = f"""
                    SELECT {select_fields}
                    FROM {table_name}
                    WHERE ts >= '{start_time.strftime('%Y-%m-%d %H:%M:%S')}'
                      AND ts <= '{end_time.strftime('%Y-%m-%d %H:%M:%S')}'
                    INTERVAL({interval})
                    ORDER BY ts
                    LIMIT {limit}
                    """
                else:
                    sql = f"""
                    SELECT {select_fields}
                    FROM {table_name}
                    WHERE ts >= '{start_time.strftime('%Y-%m-%d %H:%M:%S')}'
                      AND ts <= '{end_time.strftime('%Y-%m-%d %H:%M:%S')}'
                    ORDER BY ts
                    LIMIT {limit}
                    """
            else:
                # 原始数据查询
                sql = f"""
                SELECT {select_fields}
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
                "asset_id": asset_id,
                "asset_code": asset.code,
                "time_range": {
                    "start_time": start_time.isoformat(),
                    "end_time": end_time.isoformat()
                },
                "interval": interval,
                "data": result,
                "count": len(result)
            }
        )
        
    except Exception as e:
        logger.error(f"获取历史数据失败: {e}")
        return Fail(code=500, msg=f"查询失败: {str(e)}")


# =====================================================
# 批量操作API
# =====================================================

@router.post("/batch-status", summary="批量更新资产状态")
async def batch_update_status(
    asset_ids: List[int] = Query(..., description="资产ID列表"),
    status: str = Query(..., description="目标状态"),
    current_user: User = Depends(get_current_active_user)
):
    """
    批量更新资产状态
    
    需求：5.3
    """
    try:
        Asset = await get_asset_model()
        
        valid_statuses = ["online", "offline", "error", "maintenance"]
        if status not in valid_statuses:
            return Fail(code=400, msg=f"无效状态: {status}，支持: {', '.join(valid_statuses)}")
        
        updated_count = await Asset.filter(id__in=asset_ids, is_locked=False).update(
            status=status,
            updated_at=datetime.now()
        )
        
        logger.info(f"批量更新资产状态: {updated_count}个, 状态: {status}, 用户: {current_user.username}")
        
        return Success(
            code=200,
            msg=f"成功更新 {updated_count} 个资产状态",
            data={"updated_count": updated_count}
        )
        
    except Exception as e:
        logger.error(f"批量更新状态失败: {e}")
        return Fail(code=500, msg=f"更新失败: {str(e)}")
