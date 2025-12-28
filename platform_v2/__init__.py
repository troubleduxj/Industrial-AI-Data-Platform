"""
Platform Layer - 平台核心层

工业AI数据平台的核心平台层，提供以下功能模块：

- metadata: 元数据管理（资产类别、信号定义）
- timeseries: 时序数据服务（TDengine操作）
- ingestion: 数据采集层（协议适配器、数据验证）
- realtime: 实时推送服务（WebSocket）

注意: 
- 为避免与Python内置 platform 模块冲突，部分实现位于 platform_core
- 此模块提供统一的导入接口，内部会代理到 platform_core

使用示例:
    from platform.metadata import AssetCategoryService
    from platform.timeseries import TDengineClient
    from platform.ingestion import DataValidator
    from platform.realtime import ConnectionManager
"""

__version__ = "2.0.0"

# 直接导入子模块
from . import metadata
from . import timeseries
from . import ingestion

# realtime 模块位于 platform_core，创建别名
try:
    from platform_core import realtime
except ImportError:
    realtime = None

__all__ = [
    "metadata",
    "timeseries",
    "ingestion",
    "realtime",
]
