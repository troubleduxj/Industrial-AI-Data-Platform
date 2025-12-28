"""
资产类别管理服务

提供资产类别的CRUD操作和业务逻辑。
"""

from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class AssetCategoryService:
    """
    资产类别管理服务
    
    提供资产类别的创建、查询、更新、删除等操作。
    """
    
    @staticmethod
    async def create_category(
        code: str,
        name: str,
        tdengine_database: str,
        tdengine_stable_prefix: str,
        description: Optional[str] = None,
        icon: Optional[str] = None,
        industry: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None
    ) -> "AssetCategory":
        """
        创建资产类别
        
        Args:
            code: 类别编码（唯一）
            name: 类别名称
            tdengine_database: TDengine数据库名
            tdengine_stable_prefix: 超级表前缀
            description: 类别描述
            icon: 图标
            industry: 所属行业
            config: 扩展配置
            
        Returns:
            AssetCategory: 创建的资产类别对象
        """
        from app.models.platform_upgrade import AssetCategory
        
        try:
            category = await AssetCategory.create(
                code=code,
                name=name,
                tdengine_database=tdengine_database,
                tdengine_stable_prefix=tdengine_stable_prefix,
                description=description,
                icon=icon,
                industry=industry,
                config=config or {},
                is_active=True,
                asset_count=0
            )
            logger.info(f"创建资产类别成功: {code} ({name})")
            return category
        except Exception as e:
            logger.error(f"创建资产类别失败: {e}")
            raise
    
    @staticmethod
    async def get_category_by_id(category_id: int) -> Optional["AssetCategory"]:
        """根据ID获取资产类别"""
        from app.models.platform_upgrade import AssetCategory
        return await AssetCategory.get_or_none(id=category_id)
    
    @staticmethod
    async def get_category_by_code(code: str) -> Optional["AssetCategory"]:
        """根据编码获取资产类别"""
        from app.models.platform_upgrade import AssetCategory
        return await AssetCategory.get_or_none(code=code)
    
    @staticmethod
    async def get_categories(
        industry: Optional[str] = None,
        is_active: Optional[bool] = None,
        search: Optional[str] = None,
        page: int = 1,
        page_size: int = 10
    ) -> Tuple[List["AssetCategory"], int]:
        """
        获取资产类别列表（分页）
        
        Args:
            industry: 按行业筛选
            is_active: 按激活状态筛选
            search: 搜索关键词
            page: 页码
            page_size: 每页数量
            
        Returns:
            Tuple[List[AssetCategory], int]: (类别列表, 总数)
        """
        from app.models.platform_upgrade import AssetCategory
        from tortoise.expressions import Q
        
        query = AssetCategory.all()
        
        if industry:
            query = query.filter(industry=industry)
        if is_active is not None:
            query = query.filter(is_active=is_active)
        if search:
            query = query.filter(
                Q(code__icontains=search) |
                Q(name__icontains=search) |
                Q(description__icontains=search)
            )
        
        total = await query.count()
        offset = (page - 1) * page_size
        categories = await query.order_by("code").offset(offset).limit(page_size)
        
        return categories, total
    
    @staticmethod
    async def update_category(
        category_id: int,
        **kwargs
    ) -> Optional["AssetCategory"]:
        """
        更新资产类别
        
        Args:
            category_id: 类别ID
            **kwargs: 要更新的字段
            
        Returns:
            AssetCategory: 更新后的类别对象，如果不存在返回None
        """
        from app.models.platform_upgrade import AssetCategory
        
        category = await AssetCategory.get_or_none(id=category_id)
        if not category:
            return None
        
        # 过滤掉None值和不允许更新的字段
        update_data = {k: v for k, v in kwargs.items() if v is not None and k != "id"}
        
        if update_data:
            await category.update_from_dict(update_data).save()
            logger.info(f"更新资产类别成功: {category.code}")
        
        return category
    
    @staticmethod
    async def delete_category(category_id: int, soft_delete: bool = True) -> bool:
        """
        删除资产类别
        
        Args:
            category_id: 类别ID
            soft_delete: 是否软删除（默认True）
            
        Returns:
            bool: 删除是否成功
        """
        from app.models.platform_upgrade import AssetCategory, Asset
        
        category = await AssetCategory.get_or_none(id=category_id)
        if not category:
            return False
        
        # 检查是否有关联的资产
        asset_count = await Asset.filter(category_id=category_id, is_active=True).count()
        if asset_count > 0:
            raise ValueError(f"类别 {category.code} 下有 {asset_count} 个资产，无法删除")
        
        if soft_delete:
            category.is_active = False
            await category.save()
        else:
            await category.delete()
        
        logger.info(f"删除资产类别成功: {category.code}")
        return True
    
    @staticmethod
    async def get_category_statistics(category_id: int) -> Dict[str, Any]:
        """
        获取资产类别统计信息
        
        Args:
            category_id: 类别ID
            
        Returns:
            Dict: 统计信息
        """
        from app.models.platform_upgrade import AssetCategory, Asset, SignalDefinition
        
        category = await AssetCategory.get_or_none(id=category_id)
        if not category:
            return {}
        
        asset_count = await Asset.filter(category_id=category_id, is_active=True).count()
        signal_count = await SignalDefinition.filter(category_id=category_id, is_active=True).count()
        
        return {
            "category_id": category_id,
            "category_code": category.code,
            "category_name": category.name,
            "asset_count": asset_count,
            "signal_count": signal_count,
            "is_active": category.is_active,
            "tdengine_database": category.tdengine_database,
            "tdengine_stable_prefix": category.tdengine_stable_prefix
        }
