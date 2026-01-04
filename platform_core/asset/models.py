"""
资产模型定义

从app/models/platform_upgrade.py迁移Asset和AssetCategory模型的业务逻辑封装。
提供数据传输对象(DTO)用于服务层和API层之间的数据交换。
"""
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from datetime import datetime, date


@dataclass
class AssetDTO:
    """
    资产数据传输对象
    
    用于在服务层和API层之间传递资产数据，
    与数据库模型解耦，便于数据验证和转换。
    """
    id: Optional[int] = None
    code: str = ""
    name: str = ""
    category_id: int = 0
    category_code: str = ""
    attributes: Dict[str, Any] = field(default_factory=dict)
    location: Optional[str] = None
    status: str = "offline"
    is_active: bool = True
    
    # 扩展字段
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    serial_number: Optional[str] = None
    install_date: Optional[date] = None
    
    # 组织归属
    department: Optional[str] = None
    team: Optional[str] = None
    
    # 网络配置
    ip_address: Optional[str] = None
    mac_address: Optional[str] = None
    
    # 状态标记
    is_locked: bool = False
    
    # 时间戳
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    @classmethod
    def from_orm(cls, asset) -> "AssetDTO":
        """从ORM模型创建DTO"""
        return cls(
            id=asset.id,
            code=asset.code,
            name=asset.name,
            category_id=asset.category_id,
            category_code=getattr(asset.category, 'code', '') if hasattr(asset, 'category') and asset.category else '',
            attributes=asset.attributes or {},
            location=asset.location,
            status=asset.status,
            is_active=asset.is_active,
            manufacturer=asset.manufacturer,
            model=asset.model,
            serial_number=asset.serial_number,
            install_date=asset.install_date,
            department=asset.department,
            team=asset.team,
            ip_address=asset.ip_address,
            mac_address=asset.mac_address,
            is_locked=asset.is_locked,
            created_at=asset.created_at,
            updated_at=asset.updated_at
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "code": self.code,
            "name": self.name,
            "category_id": self.category_id,
            "category_code": self.category_code,
            "attributes": self.attributes,
            "location": self.location,
            "status": self.status,
            "is_active": self.is_active,
            "manufacturer": self.manufacturer,
            "model": self.model,
            "serial_number": self.serial_number,
            "install_date": self.install_date.isoformat() if self.install_date else None,
            "department": self.department,
            "team": self.team,
            "ip_address": self.ip_address,
            "mac_address": self.mac_address,
            "is_locked": self.is_locked,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


@dataclass
class AssetCategoryDTO:
    """
    资产类别数据传输对象
    
    用于在服务层和API层之间传递资产类别数据，
    包含TDengine配置和行业分类信息。
    """
    id: Optional[int] = None
    code: str = ""
    name: str = ""
    description: Optional[str] = None
    
    # 平台化字段
    icon: Optional[str] = None
    industry: Optional[str] = None
    
    # TDengine配置
    tdengine_database: str = ""
    tdengine_stable_prefix: str = ""
    
    # 状态字段
    is_active: bool = True
    asset_count: int = 0
    
    # 扩展配置
    config: Dict[str, Any] = field(default_factory=dict)
    
    # 时间戳
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    @classmethod
    def from_orm(cls, category) -> "AssetCategoryDTO":
        """从ORM模型创建DTO"""
        return cls(
            id=category.id,
            code=category.code,
            name=category.name,
            description=category.description,
            icon=category.icon,
            industry=category.industry,
            tdengine_database=category.tdengine_database,
            tdengine_stable_prefix=category.tdengine_stable_prefix,
            is_active=category.is_active,
            asset_count=category.asset_count,
            config=category.config or {},
            created_at=category.created_at,
            updated_at=category.updated_at
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "code": self.code,
            "name": self.name,
            "description": self.description,
            "icon": self.icon,
            "industry": self.industry,
            "tdengine_database": self.tdengine_database,
            "tdengine_stable_prefix": self.tdengine_stable_prefix,
            "is_active": self.is_active,
            "asset_count": self.asset_count,
            "config": self.config,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
