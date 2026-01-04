"""
资产管理模块

提供资产和资产类别的管理功能，包括：
- 数据传输对象 (DTO)
- 数据访问层 (Repository)
- 业务服务层 (Service)

使用示例:
    from platform_core.asset import AssetService, AssetDTO
    
    service = AssetService()
    asset = await service.get_asset(1)
"""

from .models import AssetDTO, AssetCategoryDTO
from .repository import AssetRepository, AssetCategoryRepository
from .service import AssetService, AssetCategoryService

__all__ = [
    # 数据传输对象
    "AssetDTO",
    "AssetCategoryDTO",
    # 数据访问层
    "AssetRepository",
    "AssetCategoryRepository",
    # 业务服务层
    "AssetService",
    "AssetCategoryService",
]
