"""
OAuth2身份提供商实现

提供OAuth2/OpenID Connect身份验证功能，支持授权码流程。
"""

import logging
from typing import Any, Dict, List, Optional
from urllib.parse import urlencode

from .identity_provider import (
    IdentityProvider,
    IdentityProviderConfig,
    UserInfo,
    AuthenticationResult,
)

logger = logging.getLogger(__name__)


class OAuth2Provider(IdentityProvider):
    """
    OAuth2身份提供商
    
    支持OAuth2授权码流程和OpenID Connect。
    
    配置示例:
    {
        "client_id": "your_client_id",
        "client_secret": "your_client_secret",
        "authorization_url": "https://provider.com/oauth2/authorize",
        "token_url": "https://provider.com/oauth2/token",
        "userinfo_url": "https://provider.com/oauth2/userinfo",
        "redirect_uri": "https://your-app.com/callback",
        "scopes": ["openid", "profile", "email"],
        "timeout": 10
    }
    """
    
    def __init__(self, config: IdentityProviderConfig):
        super().__init__(config)
        self._oauth_config = config.config
    
    @property
    def client_id(self) -> str:
        """获取客户端ID"""
        return self._oauth_config.get("client_id", "")
    
    @property
    def client_secret(self) -> str:
        """获取客户端密钥"""
        return self._oauth_config.get("client_secret", "")
    
    @property
    def authorization_url(self) -> str:
        """获取授权URL"""
        return self._oauth_config.get("authorization_url", "")
    
    @property
    def token_url(self) -> str:
        """获取令牌URL"""
        return self._oauth_config.get("token_url", "")
    
    @property
    def userinfo_url(self) -> str:
        """获取用户信息URL"""
        return self._oauth_config.get("userinfo_url", "")
    
    @property
    def redirect_uri(self) -> str:
        """获取重定向URI"""
        return self._oauth_config.get("redirect_uri", "")
    
    @property
    def scopes(self) -> List[str]:
        """获取请求的作用域"""
        return self._oauth_config.get("scopes", ["openid", "profile", "email"])
    
    @property
    def timeout(self) -> int:
        """请求超时时间（秒）"""
        return self._oauth_config.get("timeout", 10)
    
    async def initialize(self) -> bool:
        """
        初始化OAuth2提供商
        
        验证配置是否完整。
        
        Returns:
            bool: 初始化是否成功
        """
        try:
            # 验证必要配置
            required_fields = ["client_id", "client_secret", "authorization_url", "token_url"]
            missing_fields = [f for f in required_fields if not self._oauth_config.get(f)]
            
            if missing_fields:
                logger.error(f"OAuth2提供商 {self.name} 缺少必要配置: {missing_fields}")
                return False
            
            self._initialized = True
            logger.info(f"OAuth2提供商 {self.name} 初始化成功")
            return True
            
        except Exception as e:
            logger.error(f"OAuth2提供商 {self.name} 初始化失败: {e}")
            self._initialized = False
            return False
    
    def get_authorization_url(self, state: Optional[str] = None) -> str:
        """
        获取授权URL
        
        用于重定向用户到身份提供商进行认证。
        
        Args:
            state: 可选的状态参数，用于防止CSRF攻击
            
        Returns:
            str: 完整的授权URL
        """
        params = {
            "client_id": self.client_id,
            "response_type": "code",
            "redirect_uri": self.redirect_uri,
            "scope": " ".join(self.scopes),
        }
        
        if state:
            params["state"] = state
        
        return f"{self.authorization_url}?{urlencode(params)}"
    
    async def authenticate(self, credentials: Dict[str, Any]) -> AuthenticationResult:
        """
        OAuth2认证（使用授权码）
        
        Args:
            credentials: 包含code和redirect_uri的字典
            
        Returns:
            AuthenticationResult: 认证结果
        """
        code = credentials.get("code")
        redirect_uri = credentials.get("redirect_uri", self.redirect_uri)
        
        if not code:
            return AuthenticationResult(
                success=False,
                error_message="缺少授权码",
                error_code="MISSING_CODE"
            )
        
        try:
            import httpx
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # 1. 交换授权码获取访问令牌
                token_response = await client.post(
                    self.token_url,
                    data={
                        "grant_type": "authorization_code",
                        "code": code,
                        "redirect_uri": redirect_uri,
                        "client_id": self.client_id,
                        "client_secret": self.client_secret,
                    },
                    headers={"Accept": "application/json"}
                )
                
                if token_response.status_code != 200:
                    logger.warning(f"OAuth2令牌交换失败: {token_response.status_code}")
                    return AuthenticationResult(
                        success=False,
                        error_message="令牌交换失败",
                        error_code="TOKEN_EXCHANGE_FAILED"
                    )
                
                tokens = token_response.json()
                access_token = tokens.get("access_token")
                
                if not access_token:
                    return AuthenticationResult(
                        success=False,
                        error_message="未获取到访问令牌",
                        error_code="NO_ACCESS_TOKEN"
                    )
                
                # 2. 使用访问令牌获取用户信息
                if self.userinfo_url:
                    userinfo_response = await client.get(
                        self.userinfo_url,
                        headers={
                            "Authorization": f"Bearer {access_token}",
                            "Accept": "application/json"
                        }
                    )
                    
                    if userinfo_response.status_code == 200:
                        userinfo = userinfo_response.json()
                        user_info = self._parse_userinfo(userinfo)
                        user_info.provider_name = self.name
                        
                        logger.info(f"OAuth2用户认证成功: {user_info.username}")
                        return AuthenticationResult(
                            success=True,
                            user_info=user_info
                        )
                    else:
                        logger.warning(f"获取用户信息失败: {userinfo_response.status_code}")
                
                # 如果没有userinfo_url或获取失败，尝试从ID令牌解析
                id_token = tokens.get("id_token")
                if id_token:
                    user_info = self._parse_id_token(id_token)
                    if user_info:
                        user_info.provider_name = self.name
                        logger.info(f"OAuth2用户认证成功（从ID令牌）: {user_info.username}")
                        return AuthenticationResult(
                            success=True,
                            user_info=user_info
                        )
                
                return AuthenticationResult(
                    success=False,
                    error_message="无法获取用户信息",
                    error_code="USERINFO_FAILED"
                )
                
        except httpx.TimeoutException:
            logger.error("OAuth2认证超时")
            return AuthenticationResult(
                success=False,
                error_message="认证服务超时",
                error_code="TIMEOUT"
            )
        except Exception as e:
            logger.error(f"OAuth2认证过程中发生错误: {e}")
            return AuthenticationResult(
                success=False,
                error_message=f"认证服务错误: {str(e)}",
                error_code="AUTH_SERVICE_ERROR"
            )
    
    def _parse_userinfo(self, userinfo: Dict[str, Any]) -> UserInfo:
        """
        解析用户信息响应
        
        Args:
            userinfo: 用户信息字典
            
        Returns:
            UserInfo: 用户信息对象
        """
        # 尝试多种常见的字段名
        username = (
            userinfo.get("preferred_username") or
            userinfo.get("username") or
            userinfo.get("sub") or
            userinfo.get("email", "").split("@")[0]
        )
        
        email = userinfo.get("email")
        
        display_name = (
            userinfo.get("name") or
            userinfo.get("display_name") or
            userinfo.get("nickname")
        )
        
        # 提取组信息
        groups = userinfo.get("groups", [])
        if isinstance(groups, str):
            groups = [groups]
        
        # 也检查roles字段
        roles = userinfo.get("roles", [])
        if isinstance(roles, str):
            roles = [roles]
        groups.extend(roles)
        
        return UserInfo(
            username=username,
            email=email,
            display_name=display_name,
            groups=list(set(groups)),  # 去重
            attributes=userinfo,
            external_id=userinfo.get("sub"),
        )
    
    def _parse_id_token(self, id_token: str) -> Optional[UserInfo]:
        """
        解析ID令牌（JWT）
        
        Args:
            id_token: JWT格式的ID令牌
            
        Returns:
            UserInfo: 用户信息对象，解析失败返回None
        """
        try:
            import jwt
            
            # 不验证签名，仅解析载荷
            # 在生产环境中应该验证签名
            payload = jwt.decode(
                id_token,
                options={"verify_signature": False}
            )
            
            return self._parse_userinfo(payload)
            
        except Exception as e:
            logger.warning(f"解析ID令牌失败: {e}")
            return None
    
    async def get_user_info(self, user_id: str) -> Optional[UserInfo]:
        """
        获取用户信息
        
        注意：OAuth2通常不支持直接通过用户ID获取信息，
        需要有效的访问令牌。
        
        Args:
            user_id: 用户标识符
            
        Returns:
            UserInfo: 用户信息，通常返回None
        """
        logger.warning("OAuth2提供商不支持直接通过用户ID获取信息")
        return None
    
    async def get_user_groups(self, user_id: str) -> List[str]:
        """
        获取用户所属的组
        
        注意：OAuth2通常不支持直接获取用户组，
        组信息通常在认证时通过userinfo或ID令牌获取。
        
        Args:
            user_id: 用户标识符
            
        Returns:
            List[str]: 空列表
        """
        logger.warning("OAuth2提供商不支持直接获取用户组")
        return []
    
    async def refresh_access_token(self, refresh_token: str) -> Optional[Dict[str, Any]]:
        """
        刷新访问令牌
        
        Args:
            refresh_token: 刷新令牌
            
        Returns:
            Dict: 新的令牌信息，失败返回None
        """
        try:
            import httpx
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    self.token_url,
                    data={
                        "grant_type": "refresh_token",
                        "refresh_token": refresh_token,
                        "client_id": self.client_id,
                        "client_secret": self.client_secret,
                    },
                    headers={"Accept": "application/json"}
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    logger.warning(f"刷新令牌失败: {response.status_code}")
                    return None
                    
        except Exception as e:
            logger.error(f"刷新令牌过程中发生错误: {e}")
            return None
    
    async def close(self) -> None:
        """关闭OAuth2提供商"""
        self._initialized = False
        logger.info(f"OAuth2提供商 {self.name} 已关闭")
