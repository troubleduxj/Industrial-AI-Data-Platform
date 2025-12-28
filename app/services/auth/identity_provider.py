"""
身份提供商抽象基类

定义身份提供商的通用接口和数据结构，支持LDAP、OAuth2等多种身份验证方式。
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class IdentityProviderType(str, Enum):
    """身份提供商类型"""
    LDAP = "ldap"
    OAUTH2 = "oauth2"
    SAML = "saml"
    LOCAL = "local"


@dataclass
class UserInfo:
    """
    用户信息数据类
    
    存储从外部身份提供商获取的用户信息。
    """
    username: str
    email: Optional[str] = None
    display_name: Optional[str] = None
    groups: List[str] = field(default_factory=list)
    attributes: Dict[str, Any] = field(default_factory=dict)
    external_id: Optional[str] = None
    provider_name: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "UserInfo":
        """从字典创建实例"""
        return cls(
            username=data.get("username", ""),
            email=data.get("email"),
            display_name=data.get("display_name"),
            groups=data.get("groups", []),
            attributes=data.get("attributes", {}),
            external_id=data.get("external_id"),
            provider_name=data.get("provider_name"),
        )


@dataclass
class AuthenticationResult:
    """
    认证结果数据类
    
    存储认证操作的结果信息。
    """
    success: bool
    user_info: Optional[UserInfo] = None
    error_message: Optional[str] = None
    error_code: Optional[str] = None
    authenticated_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        result = {
            "success": self.success,
            "error_message": self.error_message,
            "error_code": self.error_code,
            "authenticated_at": self.authenticated_at.isoformat(),
        }
        if self.user_info:
            result["user_info"] = self.user_info.to_dict()
        return result


@dataclass
class IdentityProviderConfig:
    """
    身份提供商配置数据类
    
    存储身份提供商的配置信息。
    """
    name: str
    provider_type: IdentityProviderType
    enabled: bool = True
    priority: int = 0
    config: Dict[str, Any] = field(default_factory=dict)
    role_mapping: Dict[str, int] = field(default_factory=dict)  # 外部组 -> 本地角色ID
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "name": self.name,
            "provider_type": self.provider_type.value,
            "enabled": self.enabled,
            "priority": self.priority,
            "config": self.config,
            "role_mapping": self.role_mapping,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "IdentityProviderConfig":
        """从字典创建实例"""
        return cls(
            name=data.get("name", ""),
            provider_type=IdentityProviderType(data.get("provider_type", "local")),
            enabled=data.get("enabled", True),
            priority=data.get("priority", 0),
            config=data.get("config", {}),
            role_mapping=data.get("role_mapping", {}),
        )


class IdentityProvider(ABC):
    """
    身份提供商抽象基类
    
    定义身份提供商必须实现的接口方法。
    """
    
    def __init__(self, config: IdentityProviderConfig):
        """
        初始化身份提供商
        
        Args:
            config: 身份提供商配置
        """
        self.config = config
        self.name = config.name
        self.provider_type = config.provider_type
        self._initialized = False
    
    @abstractmethod
    async def initialize(self) -> bool:
        """
        初始化身份提供商连接
        
        Returns:
            bool: 初始化是否成功
        """
        pass
    
    @abstractmethod
    async def authenticate(self, credentials: Dict[str, Any]) -> AuthenticationResult:
        """
        验证用户凭据
        
        Args:
            credentials: 用户凭据字典，包含用户名、密码或其他认证信息
            
        Returns:
            AuthenticationResult: 认证结果
        """
        pass
    
    @abstractmethod
    async def get_user_info(self, user_id: str) -> Optional[UserInfo]:
        """
        获取用户信息
        
        Args:
            user_id: 用户标识符
            
        Returns:
            UserInfo: 用户信息，如果用户不存在返回None
        """
        pass
    
    @abstractmethod
    async def get_user_groups(self, user_id: str) -> List[str]:
        """
        获取用户所属的组
        
        Args:
            user_id: 用户标识符
            
        Returns:
            List[str]: 用户所属的组列表
        """
        pass
    
    async def sync_roles(self, user_id: str) -> List[int]:
        """
        同步用户角色
        
        根据用户在外部系统中的组成员关系，返回对应的本地角色ID列表。
        
        Args:
            user_id: 用户标识符
            
        Returns:
            List[int]: 本地角色ID列表
        """
        groups = await self.get_user_groups(user_id)
        role_ids = []
        
        for group in groups:
            if group in self.config.role_mapping:
                role_ids.append(self.config.role_mapping[group])
        
        return list(set(role_ids))  # 去重
    
    async def close(self) -> None:
        """
        关闭身份提供商连接
        
        子类可以重写此方法以清理资源。
        """
        self._initialized = False
    
    @property
    def is_initialized(self) -> bool:
        """检查是否已初始化"""
        return self._initialized
    
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(name={self.name}, type={self.provider_type.value})>"
