"""
资产业务服务层

提供资产管理的核心业务逻辑，封装Repository操作并添加业务规则。
"""
from typing import Optional, List, Tuple, Dict, Any

from .models import AssetDTO, AssetCategoryDTO
from .repository import AssetRepository, AssetCategoryRepository


class AssetService:
    """
    资产管理服务
    
    提供资产的业务逻辑处理，包括CRUD操作、状态管理和统计功能。
    """
    
    def __init__(self):
        self.asset_repo = AssetRepository()
        self.category_repo = AssetCategoryRepository()
    
    async def get_asset(self, asset_id: int) -> Optional[AssetDTO]:
        """
        获取单个资产
        
        Args:
            asset_id: 资产ID
            
        Returns:
            AssetDTO对象或None
        """
        asset = await self.asset_repo.get_by_id(asset_id)
        if not asset:
            return None
        return AssetDTO.from_orm(asset)
    
    async def get_asset_by_code(self, code: str) -> Optional[AssetDTO]:
        """
        根据编码获取资产
        
        Args:
            code: 资产编码
            
        Returns:
            AssetDTO对象或None
        """
        asset = await self.asset_repo.get_by_code(code)
        if not asset:
            return None
        return AssetDTO.from_orm(asset)
    
    async def list_assets(
        self,
        category_id: Optional[int] = None,
        status: Optional[str] = None,
        is_active: Optional[bool] = None,
        location: Optional[str] = None,
        department: Optional[str] = None,
        search: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[AssetDTO], int]:
        """
        分页查询资产列表
        
        Args:
            category_id: 资产类别ID筛选
            status: 状态筛选
            is_active: 激活状态筛选
            location: 位置筛选
            department: 部门筛选
            search: 搜索关键词
            page: 页码
            page_size: 每页数量
            
        Returns:
            (AssetDTO列表, 总数)
        """
        assets, total = await self.asset_repo.list_assets(
            category_id=category_id,
            status=status,
            is_active=is_active,
            location=location,
            department=department,
            search=search,
            page=page,
            page_size=page_size
        )
        return [AssetDTO.from_orm(a) for a in assets], total
    
    async def get_assets_by_category(
        self,
        category_id: int,
        is_active: bool = True
    ) -> List[AssetDTO]:
        """
        获取指定类别下的所有资产
        
        Args:
            category_id: 资产类别ID
            is_active: 是否只获取激活的资产
            
        Returns:
            AssetDTO列表
        """
        assets = await self.asset_repo.get_by_category(category_id, is_active)
        return [AssetDTO.from_orm(a) for a in assets]
    
    async def create_asset(self, data: Dict[str, Any]) -> AssetDTO:
        """
        创建资产
        
        Args:
            data: 资产数据字典
            
        Returns:
            创建的AssetDTO对象
            
        Raises:
            ValueError: 如果资产编码已存在或类别不存在
        """
        # 验证编码唯一性
        existing = await self.asset_repo.get_by_code(data.get("code", ""))
        if existing:
            raise ValueError(f"资产编码 '{data.get('code')}' 已存在")
        
        # 验证类别存在
        category_id = data.get("category_id")
        if category_id:
            category = await self.category_repo.get_by_id(category_id)
            if not category:
                raise ValueError(f"资产类别ID '{category_id}' 不存在")
        
        asset = await self.asset_repo.create(data)
        
        # 更新类别的资产数量
        if category_id:
            await self.category_repo.update_asset_count(category_id)
        
        return AssetDTO.from_orm(asset)
    
    async def update_asset(self, asset_id: int, data: Dict[str, Any]) -> Optional[AssetDTO]:
        """
        更新资产
        
        Args:
            asset_id: 资产ID
            data: 更新数据字典
            
        Returns:
            更新后的AssetDTO对象或None
            
        Raises:
            ValueError: 如果新编码已被其他资产使用
        """
        # 如果更新编码，验证唯一性
        if "code" in data:
            existing = await self.asset_repo.get_by_code(data["code"])
            if existing and existing.id != asset_id:
                raise ValueError(f"资产编码 '{data['code']}' 已被其他资产使用")
        
        # 获取原资产信息（用于更新类别统计）
        original = await self.asset_repo.get_by_id(asset_id)
        original_category_id = original.category_id if original else None
        
        asset = await self.asset_repo.update(asset_id, data)
        if not asset:
            return None
        
        # 如果类别变更，更新两个类别的资产数量
        new_category_id = data.get("category_id")
        if new_category_id and new_category_id != original_category_id:
            if original_category_id:
                await self.category_repo.update_asset_count(original_category_id)
            await self.category_repo.update_asset_count(new_category_id)
        
        return AssetDTO.from_orm(asset)
    
    async def delete_asset(self, asset_id: int) -> bool:
        """
        删除资产
        
        Args:
            asset_id: 资产ID
            
        Returns:
            是否删除成功
        """
        # 获取资产信息（用于更新类别统计）
        asset = await self.asset_repo.get_by_id(asset_id)
        category_id = asset.category_id if asset else None
        
        result = await self.asset_repo.delete(asset_id)
        
        # 更新类别的资产数量
        if result and category_id:
            await self.category_repo.update_asset_count(category_id)
        
        return result
    
    async def update_asset_status(self, asset_id: int, status: str) -> Optional[AssetDTO]:
        """
        更新资产状态
        
        Args:
            asset_id: 资产ID
            status: 新状态 (online/offline/error/maintenance)
            
        Returns:
            更新后的AssetDTO对象或None
            
        Raises:
            ValueError: 如果状态值无效
        """
        valid_statuses = ["online", "offline", "error", "maintenance"]
        if status not in valid_statuses:
            raise ValueError(f"无效的状态值 '{status}'，有效值为: {valid_statuses}")
        
        return await self.update_asset(asset_id, {"status": status})
    
    async def get_status_statistics(
        self,
        category_id: Optional[int] = None
    ) -> Dict[str, int]:
        """
        获取资产状态统计
        
        Args:
            category_id: 可选的资产类别ID筛选
            
        Returns:
            状态统计字典
        """
        return await self.asset_repo.get_status_statistics(category_id)


class AssetCategoryService:
    """
    资产类别管理服务
    
    提供资产类别的业务逻辑处理。
    """
    
    def __init__(self):
        self.repo = AssetCategoryRepository()
        self.asset_repo = AssetRepository()
    
    async def get_category(self, category_id: int) -> Optional[AssetCategoryDTO]:
        """
        获取单个资产类别
        
        Args:
            category_id: 资产类别ID
            
        Returns:
            AssetCategoryDTO对象或None
        """
        category = await self.repo.get_by_id(category_id)
        if not category:
            return None
        return AssetCategoryDTO.from_orm(category)
    
    async def get_category_by_code(self, code: str) -> Optional[AssetCategoryDTO]:
        """
        根据编码获取资产类别
        
        Args:
            code: 资产类别编码
            
        Returns:
            AssetCategoryDTO对象或None
        """
        category = await self.repo.get_by_code(code)
        if not category:
            return None
        return AssetCategoryDTO.from_orm(category)
    
    async def list_categories(
        self,
        industry: Optional[str] = None,
        is_active: Optional[bool] = None,
        search: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[AssetCategoryDTO], int]:
        """
        分页查询资产类别列表
        
        Args:
            industry: 行业筛选
            is_active: 激活状态筛选
            search: 搜索关键词
            page: 页码
            page_size: 每页数量
            
        Returns:
            (AssetCategoryDTO列表, 总数)
        """
        categories, total = await self.repo.list_categories(
            industry=industry,
            is_active=is_active,
            search=search,
            page=page,
            page_size=page_size
        )
        return [AssetCategoryDTO.from_orm(c) for c in categories], total
    
    async def get_all_active_categories(self) -> List[AssetCategoryDTO]:
        """
        获取所有激活的资产类别
        
        Returns:
            AssetCategoryDTO列表
        """
        categories = await self.repo.get_all_active()
        return [AssetCategoryDTO.from_orm(c) for c in categories]
    
    async def get_categories_by_industry(
        self,
        industry: str,
        is_active: bool = True
    ) -> List[AssetCategoryDTO]:
        """
        获取指定行业的资产类别
        
        Args:
            industry: 行业名称
            is_active: 是否只获取激活的类别
            
        Returns:
            AssetCategoryDTO列表
        """
        categories = await self.repo.get_by_industry(industry, is_active)
        return [AssetCategoryDTO.from_orm(c) for c in categories]
    
    async def create_category(self, data: Dict[str, Any]) -> AssetCategoryDTO:
        """
        创建资产类别
        
        Args:
            data: 资产类别数据字典
            
        Returns:
            创建的AssetCategoryDTO对象
            
        Raises:
            ValueError: 如果类别编码已存在
        """
        # 验证编码唯一性
        existing = await self.repo.get_by_code(data.get("code", ""))
        if existing:
            raise ValueError(f"资产类别编码 '{data.get('code')}' 已存在")
        
        category = await self.repo.create(data)
        return AssetCategoryDTO.from_orm(category)
    
    async def update_category(
        self,
        category_id: int,
        data: Dict[str, Any]
    ) -> Optional[AssetCategoryDTO]:
        """
        更新资产类别
        
        Args:
            category_id: 资产类别ID
            data: 更新数据字典
            
        Returns:
            更新后的AssetCategoryDTO对象或None
            
        Raises:
            ValueError: 如果新编码已被其他类别使用
        """
        # 如果更新编码，验证唯一性
        if "code" in data:
            existing = await self.repo.get_by_code(data["code"])
            if existing and existing.id != category_id:
                raise ValueError(f"资产类别编码 '{data['code']}' 已被其他类别使用")
        
        category = await self.repo.update(category_id, data)
        if not category:
            return None
        return AssetCategoryDTO.from_orm(category)
    
    async def delete_category(self, category_id: int) -> bool:
        """
        删除资产类别
        
        Args:
            category_id: 资产类别ID
            
        Returns:
            是否删除成功
            
        Raises:
            ValueError: 如果类别下还有资产
        """
        # 检查是否有关联的资产
        asset_count = await self.asset_repo.count_by_category(category_id)
        if asset_count > 0:
            raise ValueError(f"无法删除：该类别下还有 {asset_count} 个资产")
        
        return await self.repo.delete(category_id)
    
    async def get_industries(self) -> List[str]:
        """
        获取所有行业列表
        
        Returns:
            行业名称列表
        """
        return await self.repo.get_industries()
    
    async def refresh_asset_count(self, category_id: int) -> int:
        """
        刷新资产类别的资产数量统计
        
        Args:
            category_id: 资产类别ID
            
        Returns:
            更新后的资产数量
        """
        return await self.repo.update_asset_count(category_id)
