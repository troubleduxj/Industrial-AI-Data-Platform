"""
信号模型定义

从app/models/platform_upgrade.py迁移SignalDefinition模型的业务逻辑封装。
提供数据传输对象(DTO)用于服务层和API层之间的数据交换。
"""
from typing import Optional, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class SignalDefinitionDTO:
    """
    信号定义数据传输对象
    
    用于在服务层和API层之间传递信号定义数据，
    与数据库模型解耦，便于数据验证和转换。
    """
    id: Optional[int] = None
    category_id: int = 0
    code: str = ""
    name: str = ""
    data_type: str = "float"
    unit: Optional[str] = None
    
    # 平台化配置
    is_stored: bool = True
    is_realtime: bool = True
    is_feature: bool = False
    is_alarm_enabled: bool = False
    
    # 数据范围和验证
    value_range: Optional[Dict[str, Any]] = None
    validation_rules: Optional[Dict[str, Any]] = None
    alarm_threshold: Optional[Dict[str, Any]] = None
    
    # 聚合配置
    aggregation_method: Optional[str] = None
    
    # 显示配置
    display_config: Optional[Dict[str, Any]] = None
    sort_order: int = 0
    
    # 分组配置
    field_group: str = "default"
    is_default_visible: bool = True
    
    # 状态
    is_active: bool = True
    
    # 时间戳
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    @classmethod
    def from_orm(cls, signal) -> "SignalDefinitionDTO":
        """从ORM模型创建DTO"""
        return cls(
            id=signal.id,
            category_id=signal.category_id,
            code=signal.code,
            name=signal.name,
            data_type=signal.data_type,
            unit=signal.unit,
            is_stored=signal.is_stored,
            is_realtime=signal.is_realtime,
            is_feature=signal.is_feature,
            is_alarm_enabled=signal.is_alarm_enabled,
            value_range=signal.value_range,
            validation_rules=signal.validation_rules,
            alarm_threshold=signal.alarm_threshold,
            aggregation_method=signal.aggregation_method,
            display_config=signal.display_config,
            sort_order=signal.sort_order,
            field_group=signal.field_group,
            is_default_visible=signal.is_default_visible,
            is_active=signal.is_active,
            created_at=signal.created_at,
            updated_at=signal.updated_at
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "category_id": self.category_id,
            "code": self.code,
            "name": self.name,
            "data_type": self.data_type,
            "unit": self.unit,
            "is_stored": self.is_stored,
            "is_realtime": self.is_realtime,
            "is_feature": self.is_feature,
            "is_alarm_enabled": self.is_alarm_enabled,
            "value_range": self.value_range,
            "validation_rules": self.validation_rules,
            "alarm_threshold": self.alarm_threshold,
            "aggregation_method": self.aggregation_method,
            "display_config": self.display_config,
            "sort_order": self.sort_order,
            "field_group": self.field_group,
            "is_default_visible": self.is_default_visible,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
