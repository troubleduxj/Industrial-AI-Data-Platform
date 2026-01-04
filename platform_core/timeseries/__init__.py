"""
Platform Core Timeseries Module - 时序数据服务

提供TDengine时序数据库的操作服务。

包含以下组件:
- tdengine_client: TDengine客户端封装
- schema_manager: Schema动态管理器
- query_builder: 查询构建器

迁移说明:
- 从 platform_v2.timeseries 迁移到 platform_core.timeseries
- 保持所有API接口不变
"""

__version__ = "3.0.0"

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
