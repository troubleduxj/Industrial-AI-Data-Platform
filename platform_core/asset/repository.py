"""
资产数据访问层

提供资产和资产类别的数据库操作，封装ORM查询逻辑。
"""
from typing import Optional, List, Tuple, Dict, Any


class AssetRepository:
    """
    资产数据仓库
    
    提供资产的CRUD操作和查询方法。
    """
    
    @staticmethod
    async def get_by_id(asset_id: int) -> Optional["Asset"]:
        """
        根据ID获取资产
        
        Args:
            asset_id: 资产ID
            
        Returns:
            Asset对象或None
        """
        from app.models.platform_upgrade import Asset
        return await Asset.get_or_none(id=asset_id).prefetch_related("category")
    
    @staticmethod
    async def get_by_code(code: str) -> Optional["Asset"]:
        """
        根据编码获取资产
        
        Args:
            code: 资产编码
            
        Returns:
            Asset对象或None
        """
        from app.models.platform_upgrade import Asset
        return await Asset.get_or_none(code=code).prefetch_related("category")
    
    @staticmethod
    async def list_assets(
        category_id: Optional[int] = None,
        status: Optional[str] = None,
        is_active: Optional[bool] = None,
        location: Optional[str] = None,
        department: Optional[str] = None,
        search: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List["Asset"], int]:
        """
        分页查询资产列表
        
        Args:
            category_id: 资产类别ID筛选
            status: 状态筛选
            is_active: 激活状态筛选
            location: 位置筛选
            department: 部门筛选
            search: 搜索关键词（匹配code或name）
            page: 页码
            page_size: 每页数量
            
        Returns:
            (资产列表, 总数)
        """
        from app.models.platform_upgrade import Asset
        
        query = Asset.all()
        
        if category_id is not None:
            query = query.filter(category_id=category_id)
        if status is not None:
            query = query.filter(status=status)
        if is_active is not None:
            query = query.filter(is_active=is_active)
        if location is not None:
            query = query.filter(location__icontains=location)
        if department is not None:
            query = query.filter(department=department)
        if search:
            query = query.filter(
                code__icontains=search
            ) | query.filter(
                name__icontains=search
            )
        
        total = await query.count()
        offset = (page - 1) * page_size
        assets = await query.prefetch_related("category").offset(offset).limit(page_size)
        
        return list(assets), total
    
    @staticmethod
    async def get_by_category(category_id: int, is_active: bool = True) -> List["Asset"]:
        """
        获取指定类别下的所有资产
        
        Args:
            category_id: 资产类别ID
            is_active: 是否只获取激活的资产
            
        Returns:
            资产列表
        """
        from app.models.platform_upgrade import Asset
        
        query = Asset.filter(category_id=category_id)
        if is_active:
            query = query.filter(is_active=True)
        
        return await query.prefetch_related("category").all()
    
    @staticmethod
    async def create(data: Dict[str, Any]) -> "Asset":
        """
        创建资产
        
        Args:
            data: 资产数据字典
            
        Returns:
            创建的Asset对象
        """
        from app.models.platform_upgrade import Asset
        
        asset = await Asset.create(**data)
        return await Asset.get(id=asset.id).prefetch_related("category")
    
    @staticmethod
    async def update(asset_id: int, data: Dict[str, Any]) -> Optional["Asset"]:
        """
        更新资产
        
        Args:
            asset_id: 资产ID
            data: 更新数据字典
            
        Returns:
            更新后的Asset对象或None
        """
        from app.models.platform_upgrade import Asset
        
        asset = await Asset.get_or_none(id=asset_id)
        if not asset:
            return None
        
        await asset.update_from_dict(data).save()
        return await Asset.get(id=asset_id).prefetch_related("category")
    
    @staticmethod
    async def delete(asset_id: int) -> bool:
        """
        删除资产
        
        Args:
            asset_id: 资产ID
            
        Returns:
            是否删除成功
        """
        from app.models.platform_upgrade import Asset
        
        deleted_count = await Asset.filter(id=asset_id).delete()
        return deleted_count > 0
    
    @staticmethod
    async def count_by_category(category_id: int) -> int:
        """
        统计指定类别下的资产数量
        
        Args:
            category_id: 资产类别ID
            
        Returns:
            资产数量
        """
        from app.models.platform_upgrade import Asset
        
        return await Asset.filter(category_id=category_id, is_active=True).count()
    
    @staticmethod
    async def get_status_statistics(category_id: Optional[int] = None) -> Dict[str, int]:
        """
        获取资产状态统计
        
        Args:
            category_id: 可选的资产类别ID筛选
            
        Returns:
            状态统计字典 {"online": 10, "offline": 5, ...}
        """
        from app.models.platform_upgrade import Asset
        from tortoise.functions import Count
        
        query = Asset.filter(is_active=True)
        if category_id is not None:
            query = query.filter(category_id=category_id)
        
        results = await query.annotate(count=Count("id")).group_by("status").values("status", "count")
        
        return {r["status"]: r["count"] for r in results}


class AssetCategoryRepository:
    """
    资产类别数据仓库
    
    提供资产类别的CRUD操作和查询方法。
    """
    
    @staticmethod
    async def get_by_id(category_id: int) -> Optional["AssetCategory"]:
        """
        根据ID获取资产类别
        
        Args:
            category_id: 资产类别ID
            
        Returns:
            AssetCategory对象或None
        """
        from app.models.platform_upgrade import AssetCategory
        return await AssetCategory.get_or_none(id=category_id)
    
    @staticmethod
    async def get_by_code(code: str) -> Optional["AssetCategory"]:
        """
        根据编码获取资产类别
        
        Args:
            code: 资产类别编码
            
        Returns:
            AssetCategory对象或None
        """
        from app.models.platform_upgrade import AssetCategory
        return await AssetCategory.get_or_none(code=code)
    
    @staticmethod
    async def list_categories(
        industry: Optional[str] = None,
        is_active: Optional[bool] = None,
        search: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List["AssetCategory"], int]:
        """
        分页查询资产类别列表
        
        Args:
            industry: 行业筛选
            is_active: 激活状态筛选
            search: 搜索关键词
            page: 页码
            page_size: 每页数量
            
        Returns:
            (资产类别列表, 总数)
        """
        from app.models.platform_upgrade import AssetCategory
        
        query = AssetCategory.all()
        
        if industry is not None:
            query = query.filter(industry=industry)
        if is_active is not None:
            query = query.filter(is_active=is_active)
        if search:
            query = query.filter(
                code__icontains=search
            ) | query.filter(
                name__icontains=search
            )
        
        total = await query.count()
        offset = (page - 1) * page_size
        categories = await query.offset(offset).limit(page_size)
        
        return list(categories), total
    
    @staticmethod
    async def get_all_active() -> List["AssetCategory"]:
        """
        获取所有激活的资产类别
        
        Returns:
            资产类别列表
        """
        from app.models.platform_upgrade import AssetCategory
        return await AssetCategory.filter(is_active=True).all()
    
    @staticmethod
    async def get_by_industry(industry: str, is_active: bool = True) -> List["AssetCategory"]:
        """
        获取指定行业的资产类别
        
        Args:
            industry: 行业名称
            is_active: 是否只获取激活的类别
            
        Returns:
            资产类别列表
        """
        from app.models.platform_upgrade import AssetCategory
        
        query = AssetCategory.filter(industry=industry)
        if is_active:
            query = query.filter(is_active=True)
        
        return await query.all()
    
    @staticmethod
    async def create(data: Dict[str, Any]) -> "AssetCategory":
        """
        创建资产类别
        
        Args:
            data: 资产类别数据字典
            
        Returns:
            创建的AssetCategory对象
        """
        from app.models.platform_upgrade import AssetCategory
        return await AssetCategory.create(**data)
    
    @staticmethod
    async def update(category_id: int, data: Dict[str, Any]) -> Optional["AssetCategory"]:
        """
        更新资产类别
        
        Args:
            category_id: 资产类别ID
            data: 更新数据字典
            
        Returns:
            更新后的AssetCategory对象或None
        """
        from app.models.platform_upgrade import AssetCategory
        
        category = await AssetCategory.get_or_none(id=category_id)
        if not category:
            return None
        
        await category.update_from_dict(data).save()
        return await AssetCategory.get(id=category_id)
    
    @staticmethod
    async def delete(category_id: int) -> bool:
        """
        删除资产类别
        
        Args:
            category_id: 资产类别ID
            
        Returns:
            是否删除成功
        """
        from app.models.platform_upgrade import AssetCategory
        
        deleted_count = await AssetCategory.filter(id=category_id).delete()
        return deleted_count > 0
    
    @staticmethod
    async def update_asset_count(category_id: int) -> int:
        """
        更新资产类别的资产数量统计
        
        Args:
            category_id: 资产类别ID
            
        Returns:
            更新后的资产数量
        """
        from app.models.platform_upgrade import AssetCategory, Asset
        
        count = await Asset.filter(category_id=category_id, is_active=True).count()
        await AssetCategory.filter(id=category_id).update(asset_count=count)
        
        return count
    
    @staticmethod
    async def get_industries() -> List[str]:
        """
        获取所有行业列表
        
        Returns:
            行业名称列表
        """
        from app.models.platform_upgrade import AssetCategory
        
        results = await AssetCategory.filter(
            is_active=True,
            industry__not_isnull=True
        ).distinct().values_list("industry", flat=True)
        
        return [r for r in results if r]
