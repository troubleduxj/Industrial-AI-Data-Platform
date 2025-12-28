"""
Platform Metadata Module - 元数据管理

提供资产类别、信号定义等元数据的管理服务。

包含以下组件:
- asset_category_service: 资产类别管理服务
- signal_definition_service: 信号定义管理服务
- metadata_registry: 元数据注册表

向后兼容:
- 原 app/services/metadata_service.py 中的功能已迁移到此模块
- 可以通过 platform.metadata 访问所有元数据管理功能
"""

__version__ = "2.0.0"

from .asset_category_service import AssetCategoryService
from .signal_definition_service import SignalDefinitionService
from .metadata_registry import MetadataRegistry, metadata_registry

__all__ = [
    "AssetCategoryService",
    "SignalDefinitionService",
    "MetadataRegistry",
    "metadata_registry",
]
