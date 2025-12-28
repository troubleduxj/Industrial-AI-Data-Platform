"""
企业身份集成模块

提供多种身份提供商的抽象和实现，支持LDAP、OAuth2等企业身份系统集成。
"""

from .identity_provider import (
    IdentityProvider,
    UserInfo,
    AuthenticationResult,
    IdentityProviderConfig,
    IdentityProviderType,
)

__all__ = [
    "IdentityProvider",
    "UserInfo",
    "AuthenticationResult",
    "IdentityProviderConfig",
    "IdentityProviderType",
]

# 延迟导入以避免循环依赖
def __getattr__(name):
    if name == "LDAPProvider":
        from .ldap_provider import LDAPProvider
        return LDAPProvider
    elif name == "OAuth2Provider":
        from .oauth2_provider import OAuth2Provider
        return OAuth2Provider
    elif name == "IdentityManager":
        from .identity_manager import IdentityManager
        return IdentityManager
    elif name == "identity_manager":
        from .identity_manager import identity_manager
        return identity_manager
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
