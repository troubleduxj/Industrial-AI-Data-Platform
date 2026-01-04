"""
Platform Compatibility Module - 向后兼容导入

此模块提供从旧路径到新路径的兼容性映射。
允许现有代码继续使用旧的导入路径。

警告: platform_v2 模块已弃用，请使用 platform_core 代替。

使用示例:
    # 旧路径 (已弃用)
    from platform_v2.metadata import AssetCategoryService, SignalDefinitionService
    from platform_v2.timeseries import TDengineClient, SchemaManager
    
    # 新路径 (推荐)
    from platform_core.metadata import AssetCategoryService, SignalDefinitionService
    from platform_core.timeseries import TDengineClient, SchemaManager
    from platform_core.ingestion import DataValidator, DualWriter
"""

import warnings
from typing import Any


def deprecated_import(old_path: str, new_path: str, obj: Any) -> Any:
    """
    发出弃用警告并返回对象
    
    Args:
        old_path: 旧导入路径
        new_path: 新导入路径
        obj: 要返回的对象
        
    Returns:
        传入的对象
    """
    warnings.warn(
        f"从 '{old_path}' 导入已弃用，请使用 '{new_path}'",
        DeprecationWarning,
        stacklevel=3
    )
    return obj


# 路径映射表 - 从旧路径到新的 platform_core 路径
PATH_MAPPINGS = {
    # 元数据服务
    "platform_v2.metadata.AssetCategoryService": "platform_core.metadata.AssetCategoryService",
    "platform_v2.metadata.SignalDefinitionService": "platform_core.metadata.SignalDefinitionService",
    "platform_v2.metadata.MetadataRegistry": "platform_core.metadata.MetadataRegistry",
    "platform_v2.metadata.metadata_registry": "platform_core.metadata.metadata_registry",
    
    # TDengine服务
    "platform_v2.timeseries.TDengineClient": "platform_core.timeseries.TDengineClient",
    "platform_v2.timeseries.get_tdengine_client": "platform_core.timeseries.get_tdengine_client",
    
    # Schema管理
    "platform_v2.timeseries.SchemaManager": "platform_core.timeseries.SchemaManager",
    "platform_v2.timeseries.SchemaVersionManager": "platform_core.timeseries.SchemaVersionManager",
    "platform_v2.timeseries.schema_manager": "platform_core.timeseries.schema_manager",
    "platform_v2.timeseries.schema_version_manager": "platform_core.timeseries.schema_version_manager",
    
    # 查询构建器
    "platform_v2.timeseries.QueryBuilder": "platform_core.timeseries.QueryBuilder",
    "platform_v2.timeseries.AggregateFunction": "platform_core.timeseries.AggregateFunction",
    "platform_v2.timeseries.TimeInterval": "platform_core.timeseries.TimeInterval",
    "platform_v2.timeseries.query": "platform_core.timeseries.query",
    
    # 数据采集
    "platform_v2.ingestion": "platform_core.ingestion",
    "platform_v2.realtime": "platform_core.realtime",
    
    # 旧的 app.services 路径
    "app.services.metadata_service.MetadataService": "platform_core.metadata.AssetCategoryService",
    "app.services.tdengine_service.TDengineService": "platform_core.timeseries.TDengineClient",
    "app.services.tdengine_service.TDengineServiceManager": "platform_core.timeseries.TDengineClient",
    "app.services.schema_engine.TDengineSchemaManager": "platform_core.timeseries.SchemaManager",
    "app.services.schema_engine.SchemaVersionManager": "platform_core.timeseries.SchemaVersionManager",
    "app.services.schema_engine.schema_manager": "platform_core.timeseries.schema_manager",
}


def get_new_path(old_path: str) -> str:
    """
    获取新的导入路径
    
    Args:
        old_path: 旧导入路径
        
    Returns:
        新导入路径，如果没有映射则返回原路径
    """
    return PATH_MAPPINGS.get(old_path, old_path)
