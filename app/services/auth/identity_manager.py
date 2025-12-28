"""
身份管理服务

提供多身份提供商管理、用户自动创建和角色同步功能。
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from .identity_provider import (
    IdentityProvider,
    IdentityProviderConfig,
    IdentityProviderType,
    UserInfo,
    AuthenticationResult,
)

logger = logging.getLogger(__name__)


class IdentityManager:
    """
    身份管理服务
    
    管理多个身份提供商，处理外部认证、本地用户创建和角色同步。
    """
    
    def __init__(self):
        self._providers: Dict[str, IdentityProvider] = {}
        self._provider_configs: Dict[str, IdentityProviderConfig] = {}
    
    def register_provider(self, name: str, provider: IdentityProvider) -> None:
        """
        注册身份提供商
        
        Args:
            name: 提供商名称
            provider: 身份提供商实例
        """
        self._providers[name] = provider
        self._provider_configs[name] = provider.config
        logger.info(f"注册身份提供商: {name} ({provider.provider_type.value})")
    
    def unregister_provider(self, name: str) -> bool:
        """
        注销身份提供商
        
        Args:
            name: 提供商名称
            
        Returns:
            bool: 是否成功注销
        """
        if name in self._providers:
            del self._providers[name]
            del self._provider_configs[name]
            logger.info(f"注销身份提供商: {name}")
            return True
        return False
    
    def get_provider(self, name: str) -> Optional[IdentityProvider]:
        """
        获取身份提供商
        
        Args:
            name: 提供商名称
            
        Returns:
            IdentityProvider: 身份提供商实例
        """
        return self._providers.get(name)
    
    def list_providers(self) -> List[Dict[str, Any]]:
        """
        列出所有身份提供商
        
        Returns:
            List[Dict]: 提供商信息列表
        """
        return [
            {
                "name": name,
                "type": provider.provider_type.value,
                "enabled": provider.config.enabled,
                "priority": provider.config.priority,
                "initialized": provider.is_initialized,
            }
            for name, provider in self._providers.items()
        ]
    
    async def initialize_all(self) -> Dict[str, bool]:
        """
        初始化所有身份提供商
        
        Returns:
            Dict[str, bool]: 各提供商初始化结果
        """
        results = {}
        for name, provider in self._providers.items():
            try:
                results[name] = await provider.initialize()
            except Exception as e:
                logger.error(f"初始化提供商 {name} 失败: {e}")
                results[name] = False
        return results
    
    async def close_all(self) -> None:
        """关闭所有身份提供商"""
        for name, provider in self._providers.items():
            try:
                await provider.close()
            except Exception as e:
                logger.error(f"关闭提供商 {name} 失败: {e}")
    
    async def authenticate(
        self,
        provider_name: str,
        credentials: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        通过指定提供商认证
        
        Args:
            provider_name: 提供商名称
            credentials: 用户凭据
            
        Returns:
            Dict: 包含用户信息和本地用户的字典，认证失败返回None
        """
        provider = self._providers.get(provider_name)
        if not provider:
            logger.error(f"未知的身份提供商: {provider_name}")
            return None
        
        if not provider.config.enabled:
            logger.warning(f"身份提供商已禁用: {provider_name}")
            return None
        
        # 执行认证
        result = await provider.authenticate(credentials)
        if not result.success or not result.user_info:
            logger.warning(f"认证失败: {result.error_message}")
            return None
        
        user_info = result.user_info
        
        # 确保本地用户存在
        local_user = await self._ensure_local_user(user_info, provider_name)
        
        # 同步角色
        synced_roles = await self._sync_user_roles(local_user, user_info, provider)
        
        # 更新最后登录时间
        await self._update_last_login(local_user, provider_name)
        
        return {
            "user_info": user_info,
            "local_user": local_user,
            "synced_roles": synced_roles,
            "provider": provider_name,
            "authenticated_at": result.authenticated_at.isoformat(),
        }
    
    async def _ensure_local_user(
        self,
        user_info: UserInfo,
        provider_name: str
    ) -> Any:
        """
        确保本地用户记录存在
        
        如果用户不存在，则自动创建。
        
        Args:
            user_info: 外部用户信息
            provider_name: 提供商名称
            
        Returns:
            User: 本地用户对象
        """
        try:
            from app.models.admin import User
            
            # 首先尝试通过用户名查找
            user = await User.filter(username=user_info.username).first()
            
            if not user and user_info.email:
                # 尝试通过邮箱查找
                user = await User.filter(email=user_info.email).first()
            
            if user:
                # 用户已存在，更新信息
                updated = False
                
                if user_info.email and user.email != user_info.email:
                    user.email = user_info.email
                    updated = True
                
                if user_info.display_name and user.nick_name != user_info.display_name:
                    user.nick_name = user_info.display_name
                    updated = True
                
                if updated:
                    await user.save()
                    logger.info(f"更新本地用户信息: {user_info.username}")
                
                return user
            
            # 创建新用户
            user = User(
                username=user_info.username,
                email=user_info.email or f"{user_info.username}@external.local",
                nick_name=user_info.display_name,
                user_type="02",  # 外部用户类型
                status="0",  # 正常状态
                del_flag="0",
            )
            await user.save()
            
            logger.info(f"创建本地用户: {user_info.username} (来自 {provider_name})")
            
            # 记录外部身份关联
            await self._create_external_identity(user, user_info, provider_name)
            
            return user
            
        except ImportError:
            logger.warning("无法导入User模型，跳过本地用户创建")
            return None
        except Exception as e:
            logger.error(f"确保本地用户存在时发生错误: {e}")
            return None
    
    async def _create_external_identity(
        self,
        user: Any,
        user_info: UserInfo,
        provider_name: str
    ) -> None:
        """
        创建外部身份关联记录
        
        Args:
            user: 本地用户对象
            user_info: 外部用户信息
            provider_name: 提供商名称
        """
        try:
            from app.models.platform_upgrade import UserExternalIdentity, IdentityProvider as IdentityProviderModel
            
            # 获取提供商记录
            provider_record = await IdentityProviderModel.filter(name=provider_name).first()
            if not provider_record:
                logger.warning(f"未找到提供商记录: {provider_name}")
                return
            
            # 创建或更新外部身份关联
            external_identity, created = await UserExternalIdentity.get_or_create(
                user_id=user.id,
                provider_id=provider_record.id,
                defaults={
                    "external_id": user_info.external_id or user_info.username,
                    "external_username": user_info.username,
                    "last_login_at": datetime.now(),
                }
            )
            
            if not created:
                external_identity.last_login_at = datetime.now()
                await external_identity.save()
                
        except ImportError:
            logger.debug("外部身份模型不可用，跳过关联创建")
        except Exception as e:
            logger.error(f"创建外部身份关联时发生错误: {e}")
    
    async def _sync_user_roles(
        self,
        user: Any,
        user_info: UserInfo,
        provider: IdentityProvider
    ) -> List[int]:
        """
        同步用户角色
        
        根据外部用户的组成员关系，同步本地角色。
        
        Args:
            user: 本地用户对象
            user_info: 外部用户信息
            provider: 身份提供商
            
        Returns:
            List[int]: 同步的角色ID列表
        """
        if not user:
            return []
        
        try:
            from app.models.admin import Role, UserRole
            
            # 获取应该拥有的角色
            target_role_ids = await provider.sync_roles(user_info.username)
            
            if not target_role_ids:
                return []
            
            # 获取当前角色
            current_roles = await UserRole.filter(user_id=user.id).all()
            current_role_ids = {r.role_id for r in current_roles}
            
            # 添加新角色
            new_role_ids = set(target_role_ids) - current_role_ids
            for role_id in new_role_ids:
                # 验证角色存在
                role = await Role.filter(id=role_id).first()
                if role:
                    await UserRole.create(user_id=user.id, role_id=role_id)
                    logger.info(f"为用户 {user.username} 添加角色: {role.role_name}")
            
            return list(target_role_ids)
            
        except ImportError:
            logger.debug("角色模型不可用，跳过角色同步")
            return []
        except Exception as e:
            logger.error(f"同步用户角色时发生错误: {e}")
            return []
    
    async def _update_last_login(self, user: Any, provider_name: str) -> None:
        """
        更新用户最后登录时间
        
        Args:
            user: 本地用户对象
            provider_name: 提供商名称
        """
        if not user:
            return
        
        try:
            user.login_date = datetime.now()
            await user.save()
        except Exception as e:
            logger.error(f"更新最后登录时间失败: {e}")
    
    async def load_providers_from_db(self) -> int:
        """
        从数据库加载身份提供商配置
        
        Returns:
            int: 加载的提供商数量
        """
        try:
            from app.models.platform_upgrade import IdentityProvider as IdentityProviderModel
            
            providers = await IdentityProviderModel.filter(enabled=True).all()
            count = 0
            
            for provider_record in providers:
                try:
                    config = IdentityProviderConfig(
                        name=provider_record.name,
                        provider_type=IdentityProviderType(provider_record.type),
                        enabled=provider_record.enabled,
                        priority=provider_record.priority or 0,
                        config=provider_record.config or {},
                        role_mapping=provider_record.role_mapping or {},
                    )
                    
                    # 根据类型创建提供商实例
                    provider = self._create_provider(config)
                    if provider:
                        self.register_provider(provider_record.name, provider)
                        count += 1
                        
                except Exception as e:
                    logger.error(f"加载提供商 {provider_record.name} 失败: {e}")
            
            logger.info(f"从数据库加载了 {count} 个身份提供商")
            return count
            
        except ImportError:
            logger.warning("身份提供商模型不可用")
            return 0
        except Exception as e:
            logger.error(f"从数据库加载提供商失败: {e}")
            return 0
    
    def _create_provider(self, config: IdentityProviderConfig) -> Optional[IdentityProvider]:
        """
        根据配置创建提供商实例
        
        Args:
            config: 提供商配置
            
        Returns:
            IdentityProvider: 提供商实例
        """
        from .ldap_provider import LDAPProvider
        from .oauth2_provider import OAuth2Provider
        
        provider_classes = {
            IdentityProviderType.LDAP: LDAPProvider,
            IdentityProviderType.OAUTH2: OAuth2Provider,
        }
        
        provider_class = provider_classes.get(config.provider_type)
        if provider_class:
            return provider_class(config)
        
        logger.warning(f"不支持的提供商类型: {config.provider_type}")
        return None


# 全局身份管理器实例
identity_manager = IdentityManager()
