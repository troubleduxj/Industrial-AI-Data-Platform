"""
Platform Compatibility Module - 向后兼容导入

此模块提供从旧路径到新路径的兼容性映射。
允许现有代码继续使用旧的导入路径。

使用示例:
    # 旧路径 (仍然有效)
    from app.services.metadata_service import MetadataService
    from app.services.tdengine_service import TDengineService
    from app.services.schema_engine import schema_manager
    
    # 新路径 (推荐)
    from platform.metadata import AssetCategoryService, SignalDefinitionService
    from platform.timeseries import TDengineClient, SchemaManager
    from platform.ingestion import DataValidator, DualWriter
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


# 路径映射表
PATH_MAPPINGS = {
    # 元数据服务
    "app.services.metadata_service.MetadataService": "platform.metadata.AssetCategoryService",
    
    # TDengine服务
    "app.services.tdengine_service.TDengineService": "platform.timeseries.TDengineClient",
    "app.services.tdengine_service.TDengineServiceManager": "platform.timeseries.TDengineClient",
    
    # Schema引擎
    "app.services.schema_engine.TDengineSchemaManager": "platform.timeseries.SchemaManager",
    "app.services.schema_engine.SchemaVersionManager": "platform.timeseries.SchemaVersionManager",
    "app.services.schema_engine.schema_manager": "platform.timeseries.schema_manager",
    
    # 数据采集
    "platform_core.ingestion": "platform.ingestion",
    "platform_core.realtime": "platform.realtime",
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
