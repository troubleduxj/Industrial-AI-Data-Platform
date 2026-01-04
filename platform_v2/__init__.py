"""
Platform V2 Layer - 平台核心层 (已弃用)

警告: 此模块已弃用，请使用 platform_core 代替。

所有功能已迁移到 platform_core 模块：
- platform_core.metadata: 元数据管理（资产类别、信号定义）
- platform_core.timeseries: 时序数据服务（TDengine操作）
- platform_core.ingestion: 数据采集层（协议适配器、数据验证）
- platform_core.realtime: 实时推送服务（WebSocket）
- platform_core.asset: 资产管理
- platform_core.signal: 信号管理

迁移指南:
    # 旧路径 (已弃用)
    from platform_v2.metadata import AssetCategoryService
    from platform_v2.timeseries import TDengineClient
    
    # 新路径 (推荐)
    from platform_core.metadata import AssetCategoryService
    from platform_core.timeseries import TDengineClient
"""

import warnings

__version__ = "2.0.0"

# 发出弃用警告
warnings.warn(
    "platform_v2 模块已弃用，请使用 platform_core 代替。"
    "所有功能已迁移到 platform_core 模块。",
    DeprecationWarning,
    stacklevel=2
)

# 为向后兼容，从 platform_core 导入所有子模块
from platform_core import metadata
from platform_core import timeseries
from platform_core import ingestion
from platform_core import realtime

__all__ = [
    "metadata",
    "timeseries",
    "ingestion",
    "realtime",
]
