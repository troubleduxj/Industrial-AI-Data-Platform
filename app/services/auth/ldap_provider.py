"""
LDAP身份提供商实现

提供LDAP/Active Directory身份验证功能。
"""

import asyncio
from typing import Any, Dict, List, Optional
import logging

from .identity_provider import (
    IdentityProvider,
    IdentityProviderConfig,
    UserInfo,
    AuthenticationResult,
)

logger = logging.getLogger(__name__)


class LDAPProvider(IdentityProvider):
    """
    LDAP身份提供商
    
    支持LDAP和Active Directory的用户认证和信息获取。
    
    配置示例:
    {
        "server": "ldap://ldap.example.com:389",
        "base_dn": "dc=example,dc=com",
        "bind_dn": "cn=admin,dc=example,dc=com",
        "bind_password": "admin_password",
        "user_search_base": "ou=users,dc=example,dc=com",
        "user_search_filter": "(uid={username})",
        "group_search_base": "ou=groups,dc=example,dc=com",
        "group_search_filter": "(member={user_dn})",
        "use_ssl": false,
        "timeout": 10
    }
    """
    
    def __init__(self, config: IdentityProviderConfig):
        super().__init__(config)
        self._ldap_config = config.config
        self._connection = None
        self._server = None
    
    @property
    def server_url(self) -> str:
        """获取LDAP服务器URL"""
        return self._ldap_config.get("server", "ldap://localhost:389")
    
    @property
    def base_dn(self) -> str:
        """获取基础DN"""
        return self._ldap_config.get("base_dn", "")
    
    @property
    def bind_dn(self) -> Optional[str]:
        """获取绑定DN"""
        return self._ldap_config.get("bind_dn")
    
    @property
    def bind_password(self) -> Optional[str]:
        """获取绑定密码"""
        return self._ldap_config.get("bind_password")
    
    @property
    def user_search_base(self) -> str:
        """获取用户搜索基础DN"""
        return self._ldap_config.get("user_search_base", self.base_dn)
    
    @property
    def user_search_filter(self) -> str:
        """获取用户搜索过滤器"""
        return self._ldap_config.get("user_search_filter", "(uid={username})")
    
    @property
    def group_search_base(self) -> str:
        """获取组搜索基础DN"""
        return self._ldap_config.get("group_search_base", self.base_dn)
    
    @property
    def group_search_filter(self) -> str:
        """获取组搜索过滤器"""
        return self._ldap_config.get("group_search_filter", "(member={user_dn})")
    
    @property
    def use_ssl(self) -> bool:
        """是否使用SSL"""
        return self._ldap_config.get("use_ssl", False)
    
    @property
    def timeout(self) -> int:
        """连接超时时间（秒）"""
        return self._ldap_config.get("timeout", 10)
    
    async def initialize(self) -> bool:
        """
        初始化LDAP连接
        
        Returns:
            bool: 初始化是否成功
        """
        try:
            # 尝试导入ldap3库
            try:
                import ldap3
                from ldap3 import Server, Connection, ALL
            except ImportError:
                logger.error("ldap3库未安装，请运行: pip install ldap3")
                return False
            
            # 创建服务器对象
            self._server = Server(
                self.server_url,
                use_ssl=self.use_ssl,
                get_info=ALL,
                connect_timeout=self.timeout
            )
            
            # 如果配置了绑定DN，测试连接
            if self.bind_dn and self.bind_password:
                test_conn = Connection(
                    self._server,
                    user=self.bind_dn,
                    password=self.bind_password,
                    auto_bind=True
                )
                test_conn.unbind()
            
            self._initialized = True
            logger.info(f"LDAP提供商 {self.name} 初始化成功")
            return True
            
        except Exception as e:
            logger.error(f"LDAP提供商 {self.name} 初始化失败: {e}")
            self._initialized = False
            return False
    
    async def authenticate(self, credentials: Dict[str, Any]) -> AuthenticationResult:
        """
        LDAP用户认证
        
        Args:
            credentials: 包含username和password的字典
            
        Returns:
            AuthenticationResult: 认证结果
        """
        username = credentials.get("username")
        password = credentials.get("password")
        
        if not username or not password:
            return AuthenticationResult(
                success=False,
                error_message="用户名和密码不能为空",
                error_code="MISSING_CREDENTIALS"
            )
        
        try:
            import ldap3
            from ldap3 import Connection, SUBTREE
            
            # 首先使用管理员账号搜索用户DN
            user_dn = await self._find_user_dn(username)
            if not user_dn:
                logger.warning(f"LDAP用户不存在: {username}")
                return AuthenticationResult(
                    success=False,
                    error_message="用户名或密码错误",
                    error_code="INVALID_CREDENTIALS"
                )
            
            # 使用用户DN和密码进行绑定认证
            try:
                user_conn = Connection(
                    self._server,
                    user=user_dn,
                    password=password,
                    auto_bind=True
                )
                
                # 认证成功，获取用户信息
                user_info = await self._get_user_info_by_dn(user_dn, username)
                user_conn.unbind()
                
                if user_info:
                    user_info.provider_name = self.name
                    user_info.external_id = user_dn
                    
                    logger.info(f"LDAP用户认证成功: {username}")
                    return AuthenticationResult(
                        success=True,
                        user_info=user_info
                    )
                else:
                    return AuthenticationResult(
                        success=False,
                        error_message="无法获取用户信息",
                        error_code="USER_INFO_ERROR"
                    )
                    
            except ldap3.core.exceptions.LDAPBindError:
                logger.warning(f"LDAP用户密码错误: {username}")
                return AuthenticationResult(
                    success=False,
                    error_message="用户名或密码错误",
                    error_code="INVALID_CREDENTIALS"
                )
                
        except Exception as e:
            logger.error(f"LDAP认证过程中发生错误: {e}")
            return AuthenticationResult(
                success=False,
                error_message=f"认证服务错误: {str(e)}",
                error_code="AUTH_SERVICE_ERROR"
            )
    
    async def _find_user_dn(self, username: str) -> Optional[str]:
        """
        查找用户DN
        
        Args:
            username: 用户名
            
        Returns:
            str: 用户DN，如果未找到返回None
        """
        try:
            import ldap3
            from ldap3 import Connection, SUBTREE
            
            # 使用管理员账号连接
            conn = Connection(
                self._server,
                user=self.bind_dn,
                password=self.bind_password,
                auto_bind=True
            )
            
            # 构建搜索过滤器
            search_filter = self.user_search_filter.format(username=username)
            
            # 搜索用户
            conn.search(
                search_base=self.user_search_base,
                search_filter=search_filter,
                search_scope=SUBTREE,
                attributes=["dn"]
            )
            
            if conn.entries:
                user_dn = str(conn.entries[0].entry_dn)
                conn.unbind()
                return user_dn
            
            conn.unbind()
            return None
            
        except Exception as e:
            logger.error(f"查找用户DN失败: {e}")
            return None
    
    async def _get_user_info_by_dn(self, user_dn: str, username: str) -> Optional[UserInfo]:
        """
        通过DN获取用户信息
        
        Args:
            user_dn: 用户DN
            username: 用户名
            
        Returns:
            UserInfo: 用户信息
        """
        try:
            import ldap3
            from ldap3 import Connection, SUBTREE
            
            conn = Connection(
                self._server,
                user=self.bind_dn,
                password=self.bind_password,
                auto_bind=True
            )
            
            # 获取用户属性
            conn.search(
                search_base=user_dn,
                search_filter="(objectClass=*)",
                search_scope=ldap3.BASE,
                attributes=["cn", "mail", "displayName", "memberOf", "uid", "sn", "givenName"]
            )
            
            if not conn.entries:
                conn.unbind()
                return None
            
            entry = conn.entries[0]
            
            # 提取用户信息
            email = str(entry.mail) if hasattr(entry, "mail") and entry.mail else None
            display_name = None
            if hasattr(entry, "displayName") and entry.displayName:
                display_name = str(entry.displayName)
            elif hasattr(entry, "cn") and entry.cn:
                display_name = str(entry.cn)
            
            # 提取组成员关系
            groups = []
            if hasattr(entry, "memberOf") and entry.memberOf:
                for group_dn in entry.memberOf:
                    # 从DN中提取组名
                    group_name = self._extract_cn_from_dn(str(group_dn))
                    if group_name:
                        groups.append(group_name)
            
            # 收集其他属性
            attributes = {}
            for attr_name in ["uid", "sn", "givenName"]:
                if hasattr(entry, attr_name) and getattr(entry, attr_name):
                    attributes[attr_name] = str(getattr(entry, attr_name))
            
            conn.unbind()
            
            return UserInfo(
                username=username,
                email=email,
                display_name=display_name,
                groups=groups,
                attributes=attributes,
                external_id=user_dn
            )
            
        except Exception as e:
            logger.error(f"获取用户信息失败: {e}")
            return None
    
    def _extract_cn_from_dn(self, dn: str) -> Optional[str]:
        """
        从DN中提取CN值
        
        Args:
            dn: Distinguished Name
            
        Returns:
            str: CN值
        """
        try:
            parts = dn.split(",")
            for part in parts:
                if part.strip().lower().startswith("cn="):
                    return part.strip()[3:]
            return None
        except Exception:
            return None
    
    async def get_user_info(self, user_id: str) -> Optional[UserInfo]:
        """
        获取用户信息
        
        Args:
            user_id: 用户名或用户DN
            
        Returns:
            UserInfo: 用户信息
        """
        try:
            # 如果user_id是DN格式，直接使用
            if "=" in user_id:
                user_dn = user_id
                username = self._extract_cn_from_dn(user_dn) or user_id
            else:
                # 否则搜索用户DN
                user_dn = await self._find_user_dn(user_id)
                username = user_id
                
            if not user_dn:
                return None
            
            user_info = await self._get_user_info_by_dn(user_dn, username)
            if user_info:
                user_info.provider_name = self.name
            
            return user_info
            
        except Exception as e:
            logger.error(f"获取用户信息失败: {e}")
            return None
    
    async def get_user_groups(self, user_id: str) -> List[str]:
        """
        获取用户所属的组
        
        Args:
            user_id: 用户名或用户DN
            
        Returns:
            List[str]: 组名列表
        """
        user_info = await self.get_user_info(user_id)
        if user_info:
            return user_info.groups
        return []
    
    async def close(self) -> None:
        """关闭LDAP连接"""
        self._server = None
        self._initialized = False
        logger.info(f"LDAP提供商 {self.name} 已关闭")
