"""
Platform Core Layer - 平台核心层 (platform_core)

注意：使用 platform_core 而非 platform 以避免与Python内置模块冲突

包含以下模块：
- asset: 资产管理模块
- signal: 信号管理模块
- metadata: 元数据管理模块
- timeseries: 时序数据服务模块
- ingestion: 数据采集层模块
- realtime: 实时WebSocket推送服务模块

迁移说明:
- V3版本整合了platform_v2的所有功能到platform_core
- metadata和timeseries模块从platform_v2迁移而来
- asset和signal模块为新增模块
"""

__version__ = "3.0.0"

# 导出所有子模块
from . import asset
from . import signal
from . import metadata
from . import timeseries
from . import ingestion
from . import realtime

__all__ = [
    "asset",
    "signal",
    "metadata",
    "timeseries",
    "ingestion",
    "realtime",
]
