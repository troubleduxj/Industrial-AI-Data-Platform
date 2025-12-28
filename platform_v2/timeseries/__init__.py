"""
Platform Timeseries Module - 时序数据服务

提供TDengine时序数据库的操作服务。

包含以下组件:
- tdengine_client: TDengine客户端封装
- schema_manager: Schema动态管理器
- query_builder: 查询构建器

向后兼容:
- 原 app/services/tdengine_service.py 中的功能已迁移到此模块
- 原 app/services/schema_engine.py 中的功能已迁移到此模块
- 可以通过 platform.timeseries 访问所有时序数据服务
"""

__version__ = "2.0.0"

from .tdengine_client import TDengineClient, get_tdengine_client
from .schema_manager import SchemaManager, SchemaVersionManager, schema_manager, schema_version_manager
from .query_builder import QueryBuilder, AggregateFunction, TimeInterval, query

__all__ = [
    # TDengine Client
    "TDengineClient",
    "get_tdengine_client",
    # Schema Manager
    "SchemaManager",
    "SchemaVersionManager",
    "schema_manager",
    "schema_version_manager",
    # Query Builder
    "QueryBuilder",
    "AggregateFunction",
    "TimeInterval",
    "query",
]
