"""
信号管理模块

提供信号定义的管理功能，包括：
- 数据传输对象 (DTO)
- 数据访问层 (Repository)
- 业务服务层 (Service)

使用示例:
    from platform_core.signal import SignalService, SignalDefinitionDTO
    
    service = SignalService()
    signals = await service.get_signals_by_category(1)
"""

from .models import SignalDefinitionDTO
from .repository import SignalRepository
from .service import SignalService

__all__ = [
    # 数据传输对象
    "SignalDefinitionDTO",
    # 数据访问层
    "SignalRepository",
    # 业务服务层
    "SignalService",
]
