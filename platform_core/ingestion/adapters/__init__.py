"""
协议适配器模块

提供多种协议的数据采集适配器实现。
"""

from platform_core.ingestion.adapters.base_adapter import (
    BaseAdapter,
    DataPoint,
    AdapterStatus,
    AdapterStatistics,
)
from platform_core.ingestion.adapters.mqtt_adapter import MQTTAdapter
from platform_core.ingestion.adapters.http_adapter import HTTPAdapter

__all__ = [
    "BaseAdapter",
    "DataPoint",
    "AdapterStatus",
    "AdapterStatistics",
    "MQTTAdapter",
    "HTTPAdapter",
]
