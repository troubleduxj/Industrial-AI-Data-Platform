"""
Platform Core Layer - 平台核心层 (platform_core)

注意：使用 platform_core 而非 platform 以避免与Python内置模块冲突

包含以下模块：
- realtime: 实时WebSocket推送服务
- ingestion: 数据采集层
- metadata: 元数据管理 (通过 platform.metadata 访问)
- timeseries: 时序数据服务 (通过 platform.timeseries 访问)

向后兼容说明:
- platform_core.ingestion 和 platform_core.realtime 保持不变
- 新增的 platform.metadata 和 platform.timeseries 提供更清晰的API
- 可以通过 platform 模块统一访问所有功能
"""

__version__ = "2.0.0"

# 导出子模块
from . import ingestion
from . import realtime

__all__ = [
    "ingestion",
    "realtime",
]
